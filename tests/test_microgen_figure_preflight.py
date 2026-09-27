from pathlib import Path

import fitz

from microvid.qa import validate_manifest
from microvid.llm_manifest_builder import _normalize_manifest
from microvid.textbook_figures import extract_textbook_figure_assets


def _synthetic_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 90), "7.8 Target Section", fontsize=16)
    page.insert_text((72, 135), "Target content explains the slope-force relationship.", fontsize=11)
    page.insert_text((72, 190), "7.9 Adjacent Section", fontsize=16)
    # Vector artwork intentionally has no embedded raster image.
    page.draw_line((110, 390), (420, 390), width=2)
    page.draw_line((260, 300), (260, 470), width=2)
    page.draw_bezier((120, 350), (190, 260), (340, 260), (410, 350), width=3)
    page.insert_text((300, 510), "Figure 7.21 Potential-energy curve illustrating slope.", fontsize=11)
    doc.save(path)
    doc.close()


def _raw_and_scoped():
    raw = {
        "blocks": [
            {"id": "b1", "text": "7.8 Target Section", "section": "7.8", "metadata": {"page_number": 1, "bbox": [72, 75, 220, 95]}},
            {"id": "b2", "text": "Target content explains the slope-force relationship.", "section": "7.8", "metadata": {"page_number": 1, "bbox": [72, 120, 400, 145]}},
            {"id": "b3", "text": "7.9 Adjacent Section. As shown in Quick Quiz 7.8, the slope gives the force direction.", "section": "7.9", "metadata": {"page_number": 1, "bbox": [72, 175, 520, 205]}},
            {"id": "b4", "text": "Figure 7.21 Potential-energy curve illustrating slope.", "section": "7.9", "metadata": {"page_number": 1, "bbox": [300, 495, 560, 520]}},
        ]
    }
    scoped = {
        "source_classification": {"kind": "textbook_subchapter"},
        "blocks": raw["blocks"][:2],
        "textbook_subchapter_ingestion": {"applied": True, "target_section": "7.8", "included_block_ids": ["b1", "b2"]},
    }
    return raw, scoped


def test_figure_inventory_runs_before_scope_and_keeps_adjacent_same_page_candidate(tmp_path):
    pdf = tmp_path / "source.pdf"
    _synthetic_pdf(pdf)
    raw, scoped = _raw_and_scoped()
    assets = extract_textbook_figure_assets(pdf, scoped, tmp_path / "figures", raw_extraction=raw)
    assert len(assets) == 1
    asset = assets[0]
    assert asset["group_label"] == "Figure 7.21"
    assert asset["scope_relation"] == "after_target"
    assert asset["scope_distance_blocks"] == 2
    assert asset["width_px"] > 0 and asset["height_px"] > 0
    assert asset["aspect_ratio"] > 0
    assert asset["fit_policy"] == "bounded_box_keep_aspect_ratio"
    assert asset["recommended_layout_hint"] in {"image_large", "image_right"}
    assert asset["explicit_target_cross_reference"] is True
    assert asset["recommended_for_target"] is True
    assert (tmp_path / asset["asset_path"].replace("extracted/figures/", "figures/")).is_file()


def _manifest_with_figure_candidate(reason=""):
    return {
        "video_id": "V01",
        "title": "7.8 Target Section",
        "source_document_type": "textbook_subchapter",
        "source_core_block_count": 1,
        "target_minutes": 3,
        "figure_assets": [{"id": "fig1"}],
        "figure_omission_reason": reason,
        "slides": [
            {"id":"V01S01", "slide_type":"title", "title":"7.8 Target Section", "narration":"", "onscreen":[], "source_block_ids":[], "estimated_seconds":10},
            {"id":"V01S02", "slide_type":"introduction", "title":"", "narration":"Orient the learner.", "onscreen":["Big picture"], "source_block_ids":[], "estimated_seconds":30},
            {"id":"V01S03", "slide_type":"concept", "title":"", "narration":"Explain the target concept.", "onscreen":["Core idea"], "source_block_ids":["b1"], "estimated_seconds":40},
            {"id":"V01S04", "slide_type":"check", "title":"", "narration":"Predict the sign.", "onscreen":["Check"], "source_block_ids":[], "estimated_seconds":25},
            {"id":"V01S05", "slide_type":"conclusion", "title":"Conclusion", "narration":"Close the loop.", "onscreen":["Key takeaway"], "source_block_ids":[], "estimated_seconds":25},
        ],
    }


def test_figure_candidates_cannot_be_silently_omitted():
    issues = validate_manifest(_manifest_with_figure_candidate())
    assert any(i["severity"] == "error" and "figure candidates" in i["message"] for i in issues)


def test_specific_figure_omission_reason_is_auditable_warning_not_silent_pass():
    issues = validate_manifest(_manifest_with_figure_candidate("Candidate belongs to adjacent theory and would introduce out-of-scope content."))
    assert not [i for i in issues if i["severity"] == "error" and "figure" in i["message"].lower()]
    assert any(i["severity"] == "warning" and "omitted" in i["message"] for i in issues)


def test_textbook_conclusion_requires_visible_conclusion_title():
    m = _manifest_with_figure_candidate("Figure is not relevant to the target concept.")
    m["figure_assets"] = []
    m["slides"][-1]["title"] = ""
    issues = validate_manifest(m)
    assert any(i["severity"] == "error" and "visible title 'Conclusion'" in i["message"] for i in issues)


def test_recommended_target_figure_cannot_be_waived_by_omission_reason():
    m = _manifest_with_figure_candidate("Adjacent caption would otherwise be omitted.")
    m["figure_assets"][0].update({
        "group_label": "Figure 7.21",
        "recommended_for_target": True,
        "explicit_target_cross_reference": True,
    })
    issues = validate_manifest(m)
    assert any(
        i["severity"] == "error" and "explicitly relevant to the target subsection" in i["message"]
        for i in issues
    )


def test_adjacent_figure_context_ids_are_not_academic_slide_provenance():
    class Provider:
        provider_name = "gemini"
        model = "fake"

    extraction = {
        "source_classification": {"kind": "textbook_subchapter"},
        "blocks": [{"id": "b1", "text": "Target slope-force relation", "section": "7.8", "metadata": {}}],
        "figure_assets": [{
            "id": "fig1", "source_block_ids": ["b46", "b47"],
            "recommended_for_target": True, "group_label": "Figure 7.21",
        }],
    }
    generated = {
        "lesson_title": "Target", "learning_outcomes": [], "editorial_flags": [],
        "slides": [{
            "slide_type": "concept", "title": "", "onscreen": ["Slope determines force"],
            "narration": "Use the curve to inspect the slope.", "lecturer_notes": [],
            "visual_direction": "Inspect the curve.", "visual_type": "figure",
            "visual_panels": [], "table_headers": [], "table_rows": [],
            "equation_latex": None, "figure_ids": ["fig1"],
            "source_block_ids": ["b1", "b46", "b47"], "estimated_seconds": 30,
        }],
    }
    manifest = _normalize_manifest(
        generated, extraction, {"target_video_minutes": 3},
        {"id": "V01", "title": "Target", "focus": "Target", "target_minutes": 3},
        extraction["blocks"], [], Provider(), generation_passes=1, design_mode="global_llm",
    )
    slide = manifest["slides"][0]
    assert slide["source_block_ids"] == ["b1"]
    assert slide["figure_context_block_ids"] == ["b46", "b47"]
    assert slide["figure_ids"] == ["fig1"]
