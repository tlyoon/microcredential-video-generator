import fitz

from microvid.global_planner import extraction_signature, whole_document_packet
from microvid.source_parser import extract_source


def test_pdf_extraction_is_compatible_with_global_packet(tmp_path):
    path = tmp_path / "course.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "1. Measurement", fontsize=16, fontname="hebo")
    page.insert_text(
        (72, 110),
        "Measurement uncertainty belongs with the reported value.",
        fontsize=11,
    )
    doc.save(path)
    doc.close()

    extraction = extract_source(
        path,
        parser_config={
            "pdf_repeated_margin_min_pages": 1,
            "pdf_min_extractable_characters": 10,
        },
    )
    packet = whole_document_packet(extraction)

    assert packet
    assert extraction["source_format"] == "pdf"
    assert any(item["section"] == "1" for item in packet)
    assert len(extraction_signature(extraction)) == 64
