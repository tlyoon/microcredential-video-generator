from __future__ import annotations

from pathlib import Path
import yaml


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def seconds_to_srt(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_text_assets(manifest_path: str | Path, workspace: str | Path) -> None:
    manifest_path = Path(manifest_path)
    workspace = Path(workspace)
    m = _load(manifest_path)
    num = int(m["video_id"][1:])
    notes_dir = workspace / "notes"
    narr_dir = workspace / "narration"
    srt_dir = workspace / "subtitles"
    for d in (notes_dir, narr_dir, srt_dir):
        d.mkdir(parents=True, exist_ok=True)

    notes = [f"# {m['video_id']} — {m['title']}", ""]
    narration = [f"# {m['video_id']} — {m['title']}", ""]
    srt_lines = []
    cursor = 0.0
    for i, slide in enumerate(m["slides"], start=1):
        notes += [f"## {slide['id']} — {slide['title']}", *[f"- {x}" for x in slide.get("lecturer_notes", [])], ""]
        narration += [f"## {slide['id']} — {slide['title']}", slide.get("narration", ""), ""]
        dur = float(slide.get("estimated_seconds", 30))
        srt_lines += [
            str(i),
            f"{seconds_to_srt(cursor)} --> {seconds_to_srt(cursor + dur)}",
            slide.get("narration", ""),
            "",
        ]
        cursor += dur
    (notes_dir / f"video_{num:02d}_notes.md").write_text("\n".join(notes), encoding="utf-8")
    (narr_dir / f"video_{num:02d}.md").write_text("\n".join(narration), encoding="utf-8")
    (srt_dir / f"video_{num:02d}.srt").write_text("\n".join(srt_lines), encoding="utf-8")
