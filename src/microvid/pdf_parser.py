from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import fitz

from .models import Block

_DEFAULT_SECTION_RE = r"^(\d+(?:\.\d+)*)\.?\s+"
_DEFAULT_PAGE_NUMBER_RE = r"^(?:page\s+)?\d+\s*$"


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ").replace("\u2005", " ")).strip()


def _compiled_patterns(parser_config: dict | None, key: str, default: list[str]) -> list[re.Pattern]:
    values = (parser_config or {}).get(key, default)
    return [re.compile(str(value), re.IGNORECASE) for value in values]


def _section_from_heading(text: str, parser_config: dict | None = None) -> str | None:
    pattern = str((parser_config or {}).get("section_number_regex", _DEFAULT_SECTION_RE))
    match = re.match(pattern, text.strip())
    return match.group(1) if match and match.groups() else None


def _classify_text(text: str, heading_level: int | None, math_fraction: float, parser_config: dict | None) -> str:
    if heading_level is not None:
        return "heading"

    cfg = parser_config or {}
    key_patterns = _compiled_patterns(cfg, "key_idea_patterns", [r"^key\s+idea\b"])
    worked_patterns = _compiled_patterns(
        cfg,
        "worked_example_patterns",
        [r"^worked\s+example\b", r"^example\b"],
    )
    contrast_patterns = _compiled_patterns(
        cfg,
        "contrast_label_patterns",
        [r"^poor:?$", r"^better:?$", r"^weak:?$", r"^incorrect\s+treatment:?$"],
    )

    if any(pattern.search(text) for pattern in key_patterns):
        return "key_idea"
    if any(pattern.search(text) for pattern in worked_patterns):
        return "worked_example_heading"
    if any(pattern.search(text) for pattern in contrast_patterns):
        return "contrast_label"
    if math_fraction >= float(cfg.get("pdf_equation_math_font_fraction", 0.65)) and len(text) <= int(
        cfg.get("pdf_equation_max_chars", 500)
    ):
        return "equation"
    return "paragraph"


def _span_metrics(block: dict[str, Any]) -> tuple[str, float, bool, float, list[str]]:
    text_lines: list[str] = []
    weighted_sizes: list[tuple[float, int]] = []
    fonts: list[str] = []
    bold_chars = 0
    math_chars = 0
    total_chars = 0

    for line in block.get("lines", []):
        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
        line_text = _normalize_ws(line_text)
        if line_text:
            text_lines.append(line_text)
        for span in line.get("spans", []):
            span_text = span.get("text", "")
            n = len(span_text.strip())
            if not n:
                continue
            size = float(span.get("size", 0.0))
            font = str(span.get("font", ""))
            fonts.append(font)
            weighted_sizes.append((size, n))
            total_chars += n
            lower_font = font.lower()
            if "bold" in lower_font or "semibold" in lower_font:
                bold_chars += n
            if "math" in lower_font:
                math_chars += n

    text = "\n".join(text_lines).strip()
    if weighted_sizes:
        font_size = sum(size * weight for size, weight in weighted_sizes) / sum(weight for _, weight in weighted_sizes)
    else:
        font_size = 0.0
    bold = total_chars > 0 and bold_chars / total_chars >= 0.5
    math_fraction = (math_chars / total_chars) if total_chars else 0.0
    return text, font_size, bold, math_fraction, sorted(set(fonts))


def _merge_same_row(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge PDF text fragments that occupy the same visual row.

    PDF writers frequently emit an equation or a table row as several independent text
    blocks.  Keeping those fragments separate makes the LLM source packet difficult to
    read.  This conservative merge joins only blocks whose vertical centres are almost
    identical or whose vertical spans substantially overlap.
    """

    if not blocks:
        return []
    ordered = sorted(blocks, key=lambda item: (item["bbox"][1], item["bbox"][0]))
    rows: list[list[dict[str, Any]]] = []

    for block in ordered:
        _, y0, _, y1 = block["bbox"]
        cy = (y0 + y1) / 2.0
        placed = False
        for row in reversed(rows[-4:]):
            ry0 = min(part["bbox"][1] for part in row)
            ry1 = max(part["bbox"][3] for part in row)
            rcy = (ry0 + ry1) / 2.0
            overlap = min(y1, ry1) - max(y0, ry0)
            min_height = max(1.0, min(y1 - y0, ry1 - ry0))
            if abs(cy - rcy) <= 3.0 or overlap / min_height >= 0.65:
                row.append(block)
                placed = True
                break
        if not placed:
            rows.append([block])

    merged: list[dict[str, Any]] = []
    for row in rows:
        row.sort(key=lambda item: item["bbox"][0])
        if len(row) == 1:
            merged.append(row[0])
            continue
        text_parts = [item["text"] for item in row if item["text"]]
        char_weights = [max(1, len(item["text"])) for item in row]
        total_weight = sum(char_weights)
        merged.append(
            {
                "text": _normalize_ws(" ".join(text_parts)),
                "bbox": (
                    min(item["bbox"][0] for item in row),
                    min(item["bbox"][1] for item in row),
                    max(item["bbox"][2] for item in row),
                    max(item["bbox"][3] for item in row),
                ),
                "font_size": sum(item["font_size"] * weight for item, weight in zip(row, char_weights))
                / total_weight,
                "bold": any(item["bold"] for item in row),
                "math_fraction": sum(item["math_fraction"] * weight for item, weight in zip(row, char_weights))
                / total_weight,
                "fonts": sorted({font for item in row for font in item["fonts"]}),
            }
        )
    return sorted(merged, key=lambda item: (item["bbox"][1], item["bbox"][0]))


def _page_blocks(page: fitz.Page) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for block in page.get_text("dict", sort=True).get("blocks", []):
        if block.get("type") != 0:
            continue
        text, font_size, bold, math_fraction, fonts = _span_metrics(block)
        if not text:
            continue
        blocks.append(
            {
                "text": text,
                "bbox": tuple(float(value) for value in block["bbox"]),
                "font_size": font_size,
                "bold": bold,
                "math_fraction": math_fraction,
                "fonts": fonts,
            }
        )
    return _merge_same_row(blocks)


def _body_font_size(pages: list[tuple[float, list[dict[str, Any]]]], margin_ratio: float) -> float:
    weighted: Counter[float] = Counter()
    for height, blocks in pages:
        top = height * margin_ratio
        bottom = height * (1.0 - margin_ratio)
        for block in blocks:
            y0, y1 = block["bbox"][1], block["bbox"][3]
            if y1 < top or y0 > bottom:
                continue
            size = round(float(block["font_size"]) * 2.0) / 2.0
            if size <= 0:
                continue
            weighted[size] += max(1, len(block["text"]))
    if not weighted:
        return 10.0
    return float(weighted.most_common(1)[0][0])


def _repeated_margin_texts(
    pages: list[tuple[float, list[dict[str, Any]]]],
    margin_ratio: float,
    min_pages: int,
    fraction: float,
) -> set[str]:
    counts: Counter[str] = Counter()
    for height, blocks in pages:
        seen: set[str] = set()
        top = height * margin_ratio
        bottom = height * (1.0 - margin_ratio)
        for block in blocks:
            y0, y1 = block["bbox"][1], block["bbox"][3]
            if y1 <= top or y0 >= bottom:
                normalized = _normalize_ws(block["text"]).lower()
                if normalized:
                    seen.add(normalized)
        counts.update(seen)
    threshold = max(min_pages, round(len(pages) * fraction))
    return {text for text, count in counts.items() if count >= threshold}


def _semantic_label(text: str, parser_config: dict | None) -> bool:
    cfg = parser_config or {}
    patterns = (
        _compiled_patterns(cfg, "key_idea_patterns", [r"^key\s+idea\b"])
        + _compiled_patterns(cfg, "worked_example_patterns", [r"^worked\s+example\b", r"^example\b"])
        + _compiled_patterns(
            cfg,
            "contrast_label_patterns",
            [r"^poor:?$", r"^better:?$", r"^weak:?$", r"^incorrect\s+treatment:?$"],
        )
    )
    return any(pattern.search(text) for pattern in patterns)


def _heading_level(
    block: dict[str, Any],
    body_size: float,
    parser_config: dict | None,
) -> int | None:
    cfg = parser_config or {}
    text = _normalize_ws(block["text"])
    section = _section_from_heading(text, parser_config)
    rounded_size = round(float(block["font_size"]) * 2.0) / 2.0
    delta = float(cfg.get("pdf_heading_min_size_delta", 1.5))
    max_chars = int(cfg.get("pdf_heading_max_chars", 180))

    if section and len(text) <= max_chars and (block["bold"] or rounded_size >= body_size + 0.5):
        return min(section.count(".") + 1, 6)
    if _semantic_label(text, parser_config):
        return None
    if len(text) <= max_chars and rounded_size >= body_size + delta:
        if rounded_size >= body_size + 5.0:
            return 1
        if rounded_size >= body_size + 3.0:
            return 2
        return 3
    return None


def extract_pdf(path: str | Path, parser_config: dict | None = None) -> dict:
    """Extract semantic text blocks from a text-readable PDF.

    The parser preserves page provenance but does not use page numbers to segment lessons.
    Repeated page headers/footers are removed, numbered/font-prominent headings are mapped
    to the same heading-path model used by the DOCX parser, and PDF equation fragments on
    the same row are merged where possible.  OCR is intentionally not implicit: scanned
    PDFs with no extractable text fail visibly.
    """

    source = Path(path)
    cfg = parser_config or {}
    try:
        document = fitz.open(source)
    except Exception as exc:  # pragma: no cover - PyMuPDF supplies format-specific details
        raise ValueError(f"Unable to open PDF source '{source}': {exc}") from exc

    try:
        pages: list[tuple[float, list[dict[str, Any]]]] = [
            (float(page.rect.height), _page_blocks(page)) for page in document
        ]
        text_chars = sum(len(block["text"]) for _, blocks in pages for block in blocks)
        if text_chars < int(cfg.get("pdf_min_extractable_characters", 100)):
            raise ValueError(
                "PDF contains too little extractable text. Scanned/image-only PDFs are not "
                "silently OCRed; provide a text-readable PDF or a DOCX source."
            )

        margin_ratio = float(cfg.get("pdf_header_footer_margin_ratio", 0.09))
        repeated = _repeated_margin_texts(
            pages,
            margin_ratio,
            min_pages=int(cfg.get("pdf_repeated_margin_min_pages", 3)),
            fraction=float(cfg.get("pdf_repeated_margin_fraction", 0.40)),
        )
        page_number_re = re.compile(
            str(cfg.get("pdf_page_number_regex", _DEFAULT_PAGE_NUMBER_RE)), re.IGNORECASE
        )
        body_size = _body_font_size(pages, margin_ratio)
        blocks: list[Block] = []
        current_section: str | None = None
        heading_stack: dict[int, str] = {}
        source_index = 0

        for page_index, (page_height, page_blocks) in enumerate(pages, start=1):
            top = page_height * margin_ratio
            bottom = page_height * (1.0 - margin_ratio)
            for raw in page_blocks:
                text = _normalize_ws(raw["text"])
                if not text:
                    continue
                normalized = text.lower()
                y0, y1 = raw["bbox"][1], raw["bbox"][3]
                in_margin = y1 <= top or y0 >= bottom
                if normalized in repeated or (in_margin and page_number_re.match(text)):
                    continue

                source_index += 1
                level = _heading_level(raw, body_size, parser_config)
                if level is not None:
                    heading_stack[level] = text
                    for key in list(heading_stack):
                        if key > level:
                            del heading_stack[key]
                    section = _section_from_heading(text, parser_config)
                    if section:
                        current_section = section
                    elif level == 1:
                        current_section = None

                kind = _classify_text(text, level, float(raw["math_fraction"]), parser_config)
                metadata = {
                    "heading_path": [heading_stack[key] for key in sorted(heading_stack)],
                    "page_number": page_index,
                    "bbox": [round(float(value), 2) for value in raw["bbox"]],
                    "font_size": round(float(raw["font_size"]), 2),
                    "fonts": raw["fonts"],
                }
                if kind == "equation":
                    metadata["math_text"] = [text]
                blocks.append(
                    Block(
                        id=f"b{len(blocks)+1:04d}",
                        kind=kind,
                        text=text,
                        section=current_section,
                        heading_level=level,
                        style="pdf",
                        source_index=source_index,
                        metadata=metadata,
                    )
                )

        return {
            "schema_version": 2,
            "source": str(source),
            "source_format": "pdf",
            "page_count": len(pages),
            "block_count": len(blocks),
            # Kept false for compatibility: lesson selection is semantic, not page-number based.
            "pagination_used": False,
            "blocks": [block.to_dict() for block in blocks],
        }
    finally:
        document.close()


def write_pdf_extraction(
    path: str | Path,
    output: str | Path,
    parser_config: dict | None = None,
) -> dict:
    payload = extract_pdf(path, parser_config=parser_config)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
