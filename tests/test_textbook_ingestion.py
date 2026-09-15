from pathlib import Path

import fitz
import pytest

from microvid.qa import validate_manifest
from microvid.source_parser import extract_source, write_extraction
from microvid.source_selection import resolve_source_path
from microvid.textbook_ingestion import prepare_pdf_extraction


def _write_textbook_excerpt(path: Path) -> None:
    doc = fitz.open()
    p1 = doc.new_page(width=612, height=792)
    p1.insert_text((72, 45), "182 Chapter 8 Conservation of Energy", fontsize=9)
    p1.insert_text((72, 90), "continued sentence from the previous section.", fontsize=11)
    p1.insert_text((72, 130), "8.1 Target Subchapter", fontsize=16, fontname="hebo")
    p1.insert_text((72, 165), "The target concept begins here and is explained in detail.", fontsize=11)
    p1.insert_text((72, 200), "Figure 8.1 illustrates the central transfer mechanism.", fontsize=11)

    p2 = doc.new_page(width=612, height=792)
    p2.insert_text((72, 45), "184 Chapter 8 Conservation of Energy", fontsize=9)
    p2.insert_text((72, 100), "The target explanation continues with a useful example and interpretation.", fontsize=11)
    p2.insert_text((72, 140), "Copyright 2019 Example Publisher", fontsize=8)

    p3 = doc.new_page(width=612, height=792)
    p3.insert_text((72, 90), "The target section finishes with its main conclusion.", fontsize=11)
    p3.insert_text((72, 145), "8.2 Next Subchapter", fontsize=16, fontname="hebo")
    p3.insert_text((72, 180), "This sentence belongs to the following subchapter.", fontsize=11)
    doc.save(path)
    doc.close()


def test_directory_selection_warns_and_prefers_source_pdf(tmp_path):
    folder = tmp_path / "source"
    folder.mkdir()
    (folder / "z_other.pdf").write_bytes(b"x")
    (folder / "source.pdf").write_bytes(b"x")
    (folder / "course.docx").write_bytes(b"x")

    with pytest.warns(UserWarning) as caught:
        chosen = resolve_source_path(folder)
    assert chosen.name == "source.pdf"
    messages = " ".join(str(item.message) for item in caught)
    assert "Multiple PDF source files" in messages
    assert "PDF selection takes precedence" in messages


def test_textbook_excerpt_is_detected_and_scoped(tmp_path):
    path = tmp_path / "source.pdf"
    _write_textbook_excerpt(path)
    payload = extract_source(path)

    assert payload["source_classification"]["kind"] == "textbook_subchapter"
    scope = payload["textbook_subchapter_ingestion"]
    assert scope["applied"] is True
    assert scope["target_section"] == "8.1"
    texts = [block["text"] for block in payload["blocks"]]
    assert texts[0].startswith("8.1 Target Subchapter")
    assert not any("previous section" in text for text in texts)
    assert not any("8.2 Next Subchapter" in text for text in texts)
    assert not any("following subchapter" in text for text in texts)


def test_textbook_write_extraction_keeps_raw_and_scope_sidecars(tmp_path):
    path = tmp_path / "source.pdf"
    _write_textbook_excerpt(path)
    output = tmp_path / "workspace" / "extracted" / "document_structure.json"
    payload = write_extraction(path, output)

    assert payload["block_count"] < payload["raw_block_count"]
    assert (output.parent / "document_structure_raw.json").is_file()
    assert (output.parent / "source_scope.json").is_file()


def test_manual_like_pdf_classification_is_not_scoped():
    blocks = [
        {
            "id": "b0001",
            "kind": "paragraph",
            "text": "Physics Laboratory 101 Student Reference Manual",
            "section": None,
        }
    ]
    for i in range(1, 13):
        blocks.append(
            {
                "id": f"b{i+1:04d}",
                "kind": "heading",
                "text": f"{i}. Laboratory topic {i}",
                "section": str(i),
            }
        )
    blocks.append(
        {"id": "b0099", "kind": "heading", "text": "8.1 General case", "section": "8.1"}
    )
    raw = {"source_format": "pdf", "page_count": 31, "blocks": blocks, "block_count": len(blocks)}
    payload = prepare_pdf_extraction(raw)
    assert payload["source_classification"]["kind"] == "structured_document"
    assert payload["textbook_subchapter_ingestion"]["applied"] is False
    assert payload["block_count"] == len(blocks)


def _textbook_manifest(slide_types):
    lesson_title = "8.1 Analysis Model: Nonisolated System (Energy)"
    slides = []
    for i, slide_type in enumerate(slide_types, start=1):
        slides.append(
            {
                "id": f"V01S{i:02d}",
                "slide_type": slide_type,
                "title": lesson_title if i == 1 else "",
                "narration": "Explain the concept clearly.",
                "onscreen": [] if i == 1 else ["Concise content"],
                "source_block_ids": ["b0003"] if slide_type == "concept" else [],
                "estimated_seconds": 30,
            }
        )
    return {
        "title": lesson_title,
        "source_document_type": "textbook_subchapter",
        "source_core_block_count": 1,
        "target_minutes": 3,
        "slides": slides,
    }


def test_textbook_manifest_requires_title_intro_check_and_conclusion():
    good = _textbook_manifest(["title", "introduction", "concept", "check", "conclusion"])
    assert not [item for item in validate_manifest(good) if item["severity"] == "error"]

    bad = _textbook_manifest(["hook", "concept", "concept", "check", "takeaway"])
    messages = " ".join(item["message"] for item in validate_manifest(bad))
    assert "title slide" in messages
    assert "introduction slide" in messages
    assert "conclusion slide" in messages
