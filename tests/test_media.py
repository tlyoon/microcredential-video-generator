import subprocess
from pathlib import Path

import pytest

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
