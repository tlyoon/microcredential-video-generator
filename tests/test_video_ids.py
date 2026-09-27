import pytest

from microvid.global_planner import _canonicalize_generated_video_ids, validate_global_plan
from microvid.video_ids import canonical_video_id, parse_canonical_video_id


def test_video_id_helpers_enforce_canonical_format():
    assert canonical_video_id(1) == "V01"
    assert canonical_video_id(12) == "V12"
    assert parse_canonical_video_id("V01") == 1
    with pytest.raises(ValueError, match="canonical sequential form"):
        parse_canonical_video_id("vid_7_8_conservative_forces_potential_energy")


def test_global_plan_canonicalizes_semantic_ids_and_prerequisites():
    generated = {
        "videos": [
            {"id": "intro_energy", "prerequisite_video_ids": []},
            {"id": "force_from_energy", "prerequisite_video_ids": ["intro_energy"]},
        ]
    }
    normalized, findings = _canonicalize_generated_video_ids(generated)
    assert [v["id"] for v in normalized["videos"]] == ["V01", "V02"]
    assert normalized["videos"][1]["prerequisite_video_ids"] == ["V01"]
    assert findings and findings[0]["severity"] == "warning"


def test_global_plan_validation_rejects_noncanonical_id():
    extraction = {"blocks": [{"id": "b1", "kind": "paragraph", "text": "x"}]}
    plan = {
        "videos": [
            {
                "id": "semantic_slug",
                "core_block_ids": ["b1"],
                "reference_block_ids": [],
                "prerequisite_video_ids": [],
            }
        ]
    }
    issues = validate_global_plan(plan, extraction)
    assert any("not canonical" in issue["message"] for issue in issues)
