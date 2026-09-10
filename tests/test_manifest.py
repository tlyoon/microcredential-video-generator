from microvid.manifest_builder import build_lesson_manifest


def test_manifest_has_provenance_and_check():
    extraction = {"blocks": [
        {"id":"b1", "kind":"heading", "text":"1. Measurement", "section":"1", "source_index":1},
        {"id":"b2", "kind":"paragraph", "text":"A measurement includes a numerical estimate and a unit. Uncertainty describes how well it is known.", "section":"1", "source_index":2},
    ]}
    course = {"narration_wpm":130, "max_slides":7}
    lesson = {"id":"V01", "title":"Measurement", "focus":"Understand measurements.", "core_sections":["1"], "target_minutes":5}
    m = build_lesson_manifest(extraction, course, lesson)
    assert m["slides"][0]["slide_type"] == "hook"
    assert any(s["slide_type"] == "check" for s in m["slides"])
    derived = [s for s in m["slides"] if s["slide_type"] in {"concept", "worked_example"}]
    assert derived and all(s["source_block_ids"] for s in derived)
