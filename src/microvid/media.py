from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
import yaml


def media_capabilities() -> dict[str, bool]:
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "libreoffice": shutil.which("libreoffice") is not None or shutil.which("soffice") is not None,
        "windows": os.name == "nt",
        "powerpoint_automation_possible": os.name == "nt",
        "sapi_tts_possible": os.name == "nt",
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


def sapi_tts(text: str, wav_path: Path) -> Path:
    if os.name != "nt":
        raise RuntimeError("SAPI TTS requires Windows.")
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install the package with the [windows] extra to use SAPI TTS.") from exc

    wav_path.parent.mkdir(parents=True, exist_ok=True)
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    # SSFMCreateForWrite = 3
    stream.Open(str(wav_path.resolve()), 3, False)
    try:
        voice.AudioOutputStream = stream
        voice.Speak(text)
    finally:
        stream.Close()
    return wav_path


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


def build_windows_video(workspace: str | Path, video_id: str, allow_draft: bool = False) -> Path:
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

    image_dir = workspace / "rendered_slides" / f"video_{num:02d}"
    audio_dir = workspace / "audio" / f"video_{num:02d}"
    segment_dir = workspace / "segments" / f"video_{num:02d}"
    images = render_powerpoint(deck, image_dir)
    if len(images) != len(manifest["slides"]):
        raise RuntimeError("Rendered slide count does not match manifest.")

    segments = []
    for i, slide in enumerate(manifest["slides"], start=1):
        wav = sapi_tts(slide.get("narration", ""), audio_dir / f"slide_{i:02d}.wav")
        segment = segment_dir / f"slide_{i:02d}.mp4"
        _make_segment(images[i - 1], wav, segment)
        segments.append(segment)

    output = workspace / "videos" / f"video_{num:02d}.mp4"
    concat_segments(segments, output)
    return output
