from types import SimpleNamespace

import pytest
import yaml

from microvid import cli
from microvid.qa import validate_manifest


def test_validation_flags_missing_check():
    m = {"target_minutes":1, "slides":[{"id":"S1", "slide_type":"concept", "narration":"x", "onscreen":["x"], "source_block_ids":["b1"]}]}
    issues = validate_manifest(m)
    assert any(i["severity"] == "error" and "check" in i["message"].lower() for i in issues)


def test_llm_self_learning_manifest_requires_introduction_and_conclusion():
    slides = [
        {"id":"S1", "slide_type":"hook", "narration":"Start.", "onscreen":["Start"], "source_block_ids":[]},
        {"id":"S2", "slide_type":"concept", "narration":"Explain.", "onscreen":["Concept"], "source_block_ids":["b1"]},
        {"id":"S3", "slide_type":"interpretation", "narration":"Interpret.", "onscreen":["Meaning"], "source_block_ids":["b1"]},
        {"id":"S4", "slide_type":"check", "narration":"Think.", "onscreen":["Question"], "source_block_ids":[]},
        {"id":"S5", "slide_type":"takeaway", "narration":"End.", "onscreen":["End"], "source_block_ids":[]},
    ]
    m = {
        "target_minutes": 2,
        "source_core_block_count": 1,
        "source_document_type": "structured_document",
        "generation": {"mode": "llm"},
        "slides": slides,
    }
    messages = " ".join(i["message"] for i in validate_manifest(m))
    assert "begin with an introduction" in messages
    assert "end with a conclusion" in messages


def test_validation_blocks_visual_slide_content_that_exceeds_layout_budget():
    slide = {
        "id": "S1",
        "slide_type": "concept",
        "narration": "Explain the comparison.",
        "source_block_ids": ["b1"],
        "visual_type": "comparison",
        "onscreen": ["First line", "Second line", "Third line"],
        "visual_panels": [
            {
                "heading": "An excessively long panel heading that cannot scan quickly",
                "body": ["one", "two", "three", "four"],
            }
        ],
    }
    issues = validate_manifest({"target_minutes": 1, "slides": [slide]})
    messages = " ".join(issue["message"] for issue in issues)
    assert "lead text exceeds the safe layout budget" in messages
    assert "Visual panel 1 exceeds the safe layout budget" in messages


def test_validation_blocks_raw_latex_on_the_visible_slide_surface():
    slide = {
        "id": "S1",
        "slide_type": "concept",
        "narration": "Explain the ratio in words.",
        "source_block_ids": ["b1"],
        "onscreen": [r"Density is $\rho = \frac{m}{V}$"],
    }
    issues = validate_manifest({"target_minutes": 1, "slides": [slide]})
    assert any("raw TeX/LaTeX" in issue["message"] for issue in issues)


def test_slide_command_does_not_emit_a_deck_when_manifest_has_blocking_qa(tmp_path, monkeypatch):
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    manifest = {
        "video_id": "V01",
        "target_minutes": 1,
        "slides": [
            {
                "id": "V01S01",
                "slide_type": "concept",
                "narration": "Explain it.",
                "source_block_ids": ["b1"],
                "visual_type": "comparison",
                "onscreen": ["one", "two", "three"],
                "visual_panels": [{"heading": "A", "body": ["B"]}],
            }
        ],
    }
    (manifest_dir / "video_01.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    called = False

    def fake_build(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(cli, "build_pptx", fake_build)
    args = SimpleNamespace(workspace=str(tmp_path), video=None, allow_unreviewed_course=False)
    with pytest.raises(SystemExit, match="Slide production is blocked"):
        cli.cmd_slides(args)
    assert not called
