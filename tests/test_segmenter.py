from microvid.segmenter import section_matches


def test_section_matching():
    assert section_matches("8.2", ["8.*"])
    assert section_matches("8", ["8.*"])
    assert not section_matches("9.1", ["8.*"])
    assert section_matches("12.1", ["12.1"])
