from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
import yaml

from .speech import normalize_scientific_speech
from .tts import TTSConfig, provider_from_tts_config


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def media_capabilities() -> dict[str, bool]:
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "libreoffice": shutil.which("libreoffice") is not None or shutil.which("soffice") is not None,
        "windows": os.name == "nt",
        "powerpoint_automation_possible": os.name == "nt",
        "sapi_tts_possible": os.name == "nt",
        "google_cloud_tts_package": _module_available("google.cloud.texttospeech"),
    }


def render_powerpoint(pptx: Path, out_dir: Path, width: int = 1920, height: int = 1080) -> list[Path]:
    if os.name != "nt":
        raise RuntimeError("PowerPoint rendering requires Windows.")
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install the package with the [windows] extra to use PowerPoint automation.") from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = 1
    presentation = app.Presentations.Open(str(pptx.resolve()), WithWindow=False)
    files: list[Path] = []
    try:
        for i in range(1, presentation.Slides.Count + 1):
            target = out_dir / f"slide_{i:02d}.png"
            presentation.Slides(i).Export(str(target.resolve()), "PNG", width, height)
            files.append(target)
    finally:
        presentation.Close()
        app.Quit()
    return files


def _make_segment(image: Path, audio: Path, output: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not available on PATH.")
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
        "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", str(output)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concat_segments(segments: list[Path], output: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not available on PATH.")
    output.parent.mkdir(parents=True, exist_ok=True)
    listing = output.with_suffix(".concat.txt")
    listing.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in segments), encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(output)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _tts_text(slide: dict, config: TTSConfig) -> str:
    text = slide.get("tts_text") or slide.get("narration", "")
    if not str(text).strip():
        raise RuntimeError(f"Slide {slide.get('id', '<unknown>')} has no narration/tts_text.")
    if config.normalize_scientific_speech:
        return normalize_scientific_speech(str(text), slide.get("tts_replacements") or {})
    return str(text).strip()


def build_windows_video(
    workspace: str | Path,
    video_id: str,
    allow_draft: bool = False,
    tts_config: dict | TTSConfig | None = None,
) -> Path:
    workspace = Path(workspace)
    num = int(video_id.upper().lstrip("V"))
    manifest_path = workspace / "manifests" / f"video_{num:02d}.yaml"
    deck = workspace / "slides" / f"video_{num:02d}.pptx"
    if not manifest_path.exists() or not deck.exists():
        raise RuntimeError("Manifest/deck missing. Run extract, draft and slides first.")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("editorial_status") != "approved" and not allow_draft:
        raise RuntimeError(
            "Media generation is blocked because the lesson manifest is not editorial_status: approved. "
            "Review source provenance, equations, narration and timing first, or use --allow-draft only for a private preview."
        )

    cfg = tts_config if isinstance(tts_config, TTSConfig) else TTSConfig.from_mapping(tts_config)
    tts_provider = provider_from_tts_config(cfg)

    image_dir = workspace / "rendered_slides" / f"video_{num:02d}"
    audio_dir = workspace / "audio" / f"video_{num:02d}"
    segment_dir = workspace / "segments" / f"video_{num:02d}"
    images = render_powerpoint(deck, image_dir)
    if len(images) != len(manifest["slides"]):
        raise RuntimeError("Rendered slide count does not match manifest.")

    segments: list[Path] = []
    synthesis_log: list[dict] = []
    for i, slide in enumerate(manifest["slides"], start=1):
        spoken = _tts_text(slide, cfg)
        requested_path = audio_dir / f"slide_{i:02d}{cfg.output_suffix}"
        result = tts_provider.synthesize(spoken, requested_path)
        segment = segment_dir / f"slide_{i:02d}.mp4"
        _make_segment(images[i - 1], result.path, segment)
        segments.append(segment)
        synthesis_log.append({
            "slide": slide.get("id", f"slide_{i:02d}"),
            "provider": result.provider,
            "voice_name": result.voice_name,
            "language_code": result.language_code,
            "audio_file": str(result.path),
            "tts_text": spoken,
        })

    audio_dir.mkdir(parents=True, exist_ok=True)
    (audio_dir / "tts_manifest.yaml").write_text(
        yaml.safe_dump(
            {"requested_config": cfg.__dict__, "slides": synthesis_log},
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    output = workspace / "videos" / f"video_{num:02d}.mp4"
    concat_segments(segments, output)
    return output


def audition_voices(
    output_dir: str | Path,
    text: str,
    tts_config: dict | TTSConfig | None = None,
    voices: list[str] | tuple[str, ...] | None = None,
) -> list[Path]:
    """Render the same narration with several voices for direct comparison."""
    cfg = tts_config if isinstance(tts_config, TTSConfig) else TTSConfig.from_mapping(tts_config)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    spoken = normalize_scientific_speech(text) if cfg.normalize_scientific_speech else text.strip()
    selected = tuple(voices or cfg.audition_voices)
    if not selected:
        raise ValueError("No audition voices configured.")

    outputs: list[Path] = []
    for voice_name in selected:
        voice_cfg = cfg.with_overrides(voice_name=voice_name, fallback_on_error=False)
        provider = provider_from_tts_config(voice_cfg)
        safe_name = voice_name.replace("/", "_").replace("\\", "_")
        result = provider.synthesize(spoken, output_dir / f"{safe_name}{voice_cfg.output_suffix}")
        outputs.append(result.path)
    return outputs
