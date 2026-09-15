from __future__ import annotations

import copy
import re
from collections import Counter

_SUBSTANTIVE_KINDS = {
    "paragraph",
    "equation",
    "table",
    "key_idea",
    "worked_example_heading",
}

_MANUAL_MARKERS = (
    "student reference manual",
    "physics laboratory 101",
    "laboratory manual",
)

_TEXTBOOK_MARKER_PATTERNS = (
    re.compile(r"\bchapter\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bfigure\s+\d+\.\d+\b", re.IGNORECASE),
    re.compile(r"\bconceptual\s+example\s+\d+\.\d+\b", re.IGNORECASE),
    re.compile(r"\bquick\s+quiz\s+\d+\.\d+\b", re.IGNORECASE),
    re.compile(r"copyright\s+\d{4}", re.IGNORECASE),
)


def _section_parts(section: str | None) -> tuple[str, ...]:
    if not section:
        return ()
    return tuple(part for part in str(section).split(".") if part)


def _is_numbered_subsection(section: str | None) -> bool:
    parts = _section_parts(section)
    return len(parts) >= 2 and all(part.isdigit() for part in parts)


def _heading_declares_numbered_section(block: dict) -> bool:
    section = str(block.get("section") or "").strip()
    text = str(block.get("text") or "").strip()
    parts = _section_parts(section)
    if not parts or not all(part.isdigit() for part in parts):
        return False
    return bool(re.match(rf"^{re.escape(section)}(?:\.|\s)", text))


def _heading_declares_section(block: dict) -> bool:
    return _is_numbered_subsection(block.get("section")) and _heading_declares_numbered_section(block)


def _substantive_chars(blocks: list[dict]) -> int:
    return sum(
        len(str(block.get("text", "")).strip())
        for block in blocks
        if block.get("kind") in _SUBSTANTIVE_KINDS
    )


def classify_pdf_extraction(extraction: dict) -> dict:
    """Classify a PDF as a textbook subchapter excerpt or a structured document."""
    blocks = list(extraction.get("blocks", []))
    text = "\n".join(str(block.get("text", "")) for block in blocks)
    lower = text.casefold()
    page_count = int(extraction.get("page_count", 0) or 0)

    subsection_headings = [
        block
        for block in blocks
        if block.get("kind") == "heading" and _heading_declares_section(block)
    ]
    distinct_sections = {
        str(block.get("section")) for block in blocks if block.get("section")
    }

    score = 0
    reasons: list[str] = []
    if 0 < page_count <= 20:
        score += 1
        reasons.append("short PDF consistent with a chapter/subchapter excerpt")
    if subsection_headings:
        score += 2
        reasons.append("numbered subsection headings detected")
    marker_hits = sum(1 for pattern in _TEXTBOOK_MARKER_PATTERNS if pattern.search(text))
    if marker_hits:
        score += min(marker_hits, 3)
        reasons.append(f"{marker_hits} textbook-style chapter/figure/publisher markers detected")

    parents = Counter(
        _section_parts(block.get("section"))[:-1]
        for block in subsection_headings
        if _section_parts(block.get("section"))
    )
    if any(count >= 2 for count in parents.values()):
        score += 2
        reasons.append("adjacent peer subsection headings detected")

    manual_hits = [marker for marker in _MANUAL_MARKERS if marker in lower]
    if manual_hits:
        score -= 6
        reasons.append("manual/reference-document markers detected")
    if page_count >= 24 and len(distinct_sections) >= 8:
        score -= 4
        reasons.append("many sections across a long document indicate a full manual/course document")

    kind = (
        "textbook_subchapter"
        if score >= 5 and marker_hits >= 1 and not manual_hits
        else "structured_document"
    )
    confidence = min(0.99, 0.55 + 0.05 * abs(score - 4))
    return {
        "kind": kind,
        "score": score,
        "confidence": round(confidence, 2),
        "reasons": reasons,
        "automatic": True,
    }


def _candidate_spans(blocks: list[dict]) -> list[dict]:
    headings: list[tuple[int, dict, tuple[str, ...]]] = []
    boundaries: list[tuple[int, tuple[str, ...]]] = []
    for index, block in enumerate(blocks):
        if block.get("kind") != "heading" or not _heading_declares_numbered_section(block):
            continue
        parts = _section_parts(block.get("section"))
        boundaries.append((index, parts))
        if len(parts) >= 2:
            headings.append((index, block, parts))
    if not headings:
        return []

    minimum_depth = min(len(parts) for _, _, parts in headings)
    peers = [(index, block, parts) for index, block, parts in headings if len(parts) == minimum_depth]
    spans: list[dict] = []
    for start, block, parts in peers:
        end = len(blocks)
        for next_index, next_parts in boundaries:
            if next_index <= start:
                continue
            if len(next_parts) <= minimum_depth and next_parts[:minimum_depth] != parts:
                end = next_index
                break
        span_blocks = blocks[start:end]
        spans.append({
            "start": start, "end": end, "section": str(block.get("section")),
            "title": str(block.get("text", "")).strip(), "parts": parts,
            "chars": _substantive_chars(span_blocks),
        })
    return spans


def scope_textbook_subchapter(extraction: dict) -> dict:
    """Scope a textbook-like PDF to its dominant intended numbered subchapter."""
    result = copy.deepcopy(extraction)
    blocks = list(extraction.get("blocks", []))
    classification = classify_pdf_extraction(extraction)
    result["source_classification"] = classification
    if classification["kind"] != "textbook_subchapter":
        result["textbook_subchapter_ingestion"] = {
            "applied": False,
            "reason": "PDF classified as a structured/manual-like document.",
        }
        return result

    spans = _candidate_spans(blocks)
    if not spans:
        result["textbook_subchapter_ingestion"] = {
            "applied": False,
            "reason": "Textbook-like PDF detected, but no reliable numbered subchapter boundary was found.",
            "requires_review": True,
        }
        return result

    total_chars = sum(max(0, int(span["chars"])) for span in spans) or 1
    target = max(spans, key=lambda span: (span["chars"], -span["start"]))
    if len(spans) == 1 and int(target["start"]) > 0:
        before_chars = _substantive_chars(blocks[: int(target["start"])])
        if before_chars > max(200, int(target["chars"]) * 2):
            result["textbook_subchapter_ingestion"] = {
                "applied": False,
                "reason": "Only one numbered subsection heading was found near the end of a larger preceding text region; the intended boundary is ambiguous.",
                "requires_review": True,
            }
            return result
    target_ratio = float(target["chars"]) / total_chars
    start, end = int(target["start"]), int(target["end"])
    included = blocks[start:end]
    excluded_before = blocks[:start]
    excluded_after = blocks[end:]

    result["raw_block_count"] = len(blocks)
    result["blocks"] = included
    result["block_count"] = len(included)
    result["textbook_subchapter_ingestion"] = {
        "applied": True,
        "target_section": target["section"],
        "target_title": target["title"],
        "target_substantive_character_fraction": round(target_ratio, 3),
        "included_block_ids": [str(block.get("id")) for block in included],
        "excluded_before_block_ids": [str(block.get("id")) for block in excluded_before],
        "excluded_after_block_ids": [str(block.get("id")) for block in excluded_after],
        "boundary_confidence": (
            "high" if target_ratio >= 0.70 else "medium" if target_ratio >= 0.50 else "low"
        ),
    }
    return result


def prepare_pdf_extraction(extraction: dict) -> dict:
    """Apply automatic PDF classification and textbook subchapter scoping when warranted."""
    return scope_textbook_subchapter(extraction)
