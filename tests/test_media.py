import subprocess
from pathlib import Path

import pytest
import yaml

from microvid import media
from microvid.media import media_capabilities


def test_media_capabilities_shape():
    caps = media_capabilities()
    assert "ffmpeg" in caps
    assert "powerpoint_automation_possible" in caps
    assert "sapi_tts_possible" in caps
    assert "google_cloud_tts_package" in caps


def test_make_segment_stages_inputs_and_output_locally(monkeypatch, tmp_path):
    image = tmp_path / "cloud" / "slide.png"
    audio = tmp_path / "cloud" / "slide.wav"
    output = tmp_path / "cloud" / "segment.mp4"
    image.parent.mkdir()
    image.write_bytes(b"png")
    audio.write_bytes(b"wav")
    captured = {}

    monkeypatch.setattr(media, "ffmpeg_executable", lambda: "ffmpeg-test")

    def fake_run(command, **kwargs):
        inputs = [Path(command[index + 1]) for index, item in enumerate(command) if item == "-i"]
        captured["inputs"] = inputs
        captured["timeout"] = kwargs["timeout"]
        assert [path.read_bytes() for path in inputs] == [b"png", b"wav"]
        staged_output = Path(command[-1])
        assert staged_output.parent == inputs[0].parent
        staged_output.write_bytes(b"mp4")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(media.subprocess, "run", fake_run)

    media._make_segment(image, audio, output)

    assert output.read_bytes() == b"mp4"
    assert all(path.parent != image.parent for path in captured["inputs"])
    assert captured["timeout"] == media.DEFAULT_FFMPEG_TIMEOUT_SECONDS


def test_concat_segments_stages_every_input_locally(monkeypatch, tmp_path):
    segments = [tmp_path / "cloud" / f"segment_{index}.mp4" for index in range(2)]
    segments[0].parent.mkdir()
    for index, segment in enumerate(segments):
        segment.write_bytes(f"segment-{index}".encode())
    output = tmp_path / "cloud" / "video.mp4"

    monkeypatch.setattr(media, "ffmpeg_executable", lambda: "ffmpeg-test")

    def fake_run(command, **kwargs):
        listing = Path(command[command.index("-i") + 1])
        entries = [
            listing.parent / line.removeprefix("file '").removesuffix("'")
            for line in listing.read_text(encoding="utf-8").splitlines()
        ]
        assert [entry.read_bytes() for entry in entries] == [b"segment-0", b"segment-1"]
        Path(command[-1]).write_bytes(b"video")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(media.subprocess, "run", fake_run)

    media.concat_segments(segments, output)

    assert output.read_bytes() == b"video"


def test_ffmpeg_timeout_reports_the_operation(monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_executable", lambda: "ffmpeg-test")
    monkeypatch.setenv(media.FFMPEG_TIMEOUT_ENV, "1")

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"], stderr="encoder stalled")

    monkeypatch.setattr(media.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Encoding test timed out after 1 seconds"):
        media._run_ffmpeg(["-version"], operation="Encoding test")


def test_media_build_uses_automated_qa_not_human_approval(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    manifests = workspace / "manifests"
    slides_dir = workspace / "slides"
    manifests.mkdir(parents=True)
    slides_dir.mkdir(parents=True)
    manifest = {
        "video_id": "V01",
        "title": "Measurement",
        "target_minutes": 2,
        "source_core_block_count": 1,
        "source_document_type": "structured_document",
        "editorial_status": "automated_ready",
        "generation": {"mode": "llm"},
        "slides": [
            {"id":"V01S01", "slide_type":"introduction", "narration":"Why does a number need a unit?", "onscreen":["12.4 — what does it mean?"], "source_block_ids":["b1"], "estimated_seconds":20},
            {"id":"V01S02", "slide_type":"concept", "narration":"A unit gives the value physical meaning.", "onscreen":["value + unit"], "source_block_ids":["b1"], "estimated_seconds":25},
            {"id":"V01S03", "slide_type":"interpretation", "narration":"That makes the result interpretable.", "onscreen":["physical quantity"], "source_block_ids":["b1"], "estimated_seconds":20},
            {"id":"V01S04", "slide_type":"check", "narration":"What is missing from twelve point four?", "onscreen":["What is missing?"], "source_block_ids":[], "estimated_seconds":20},
            {"id":"V01S05", "slide_type":"conclusion", "narration":"Keep the value and unit together.", "onscreen":["value + unit"], "source_block_ids":["b1"], "estimated_seconds":20},
        ],
    }
    (manifests / "video_01.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (slides_dir / "video_01.pptx").write_bytes(b"pptx")

    images = workspace / "fake-images"
    images.mkdir()
    for i in range(1, 6):
        (images / f"slide_{i:02d}.png").write_bytes(b"png")
    monkeypatch.setattr(media, "render_powerpoint", lambda deck, out: sorted(images.glob("*.png")))

    class FakeTTS:
        def synthesize(self, text, output_path):
            from microvid.tts import SynthesisResult
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"wav")
            return SynthesisResult(output_path, "fake")

    monkeypatch.setattr(media, "provider_from_tts_config", lambda cfg: FakeTTS())

    def fake_segment(image, audio, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"segment")

    monkeypatch.setattr(media, "_make_segment", fake_segment)

    def fake_concat(segments, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"video")
        return output

    monkeypatch.setattr(media, "concat_segments", fake_concat)

    output = media.build_windows_video(workspace, "V01", tts_config={"provider":"sapi"})
    assert output.read_bytes() == b"video"


def test_media_build_blocks_automated_qa_errors(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "manifests").mkdir(parents=True)
    (workspace / "slides").mkdir(parents=True)
    manifest = {
        "video_id": "V01",
        "target_minutes": 2,
        "source_core_block_count": 1,
        "source_document_type": "structured_document",
        "generation": {"mode": "llm"},
        "slides": [{"id":"V01S01", "slide_type":"concept", "narration":"Incomplete lesson.", "onscreen":["x"], "source_block_ids":["b1"], "estimated_seconds":20}],
    }
    (workspace / "manifests" / "video_01.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (workspace / "slides" / "video_01.pptx").write_bytes(b"pptx")
    with pytest.raises(RuntimeError, match="automated lesson QA"):
        media.build_windows_video(workspace, "V01", tts_config={"provider":"sapi"})

def test_media_capabilities_requires_win32com_for_powerpoint(monkeypatch):
    monkeypatch.setattr(media.os, "name", "nt")
    real = media._module_available
    monkeypatch.setattr(media, "_module_available", lambda name: False if name == "win32com.client" else real(name))
    assert media.media_capabilities()["powerpoint_automation_possible"] is False
