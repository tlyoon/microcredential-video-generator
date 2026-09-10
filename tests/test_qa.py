from microvid.qa import validate_manifest


def test_validation_flags_missing_check():
    m = {"target_minutes":1, "slides":[{"id":"S1", "slide_type":"concept", "narration":"x", "onscreen":["x"], "source_block_ids":["b1"]}]}
    issues = validate_manifest(m)
    assert any(i["severity"] == "error" and "check" in i["message"].lower() for i in issues)
