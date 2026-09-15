from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz

_FIGURE_CAPTION_RE = re.compile(r"\b(?:Figure|Fig\.)\s+\d+(?:\.\d+)+\b", re.IGNORECASE)
_FIGURE_CAPTION_START_RE = re.compile(r"^\s*(?:Figure|Fig\.)\s+\d+(?:\.\d+)+\b", re.IGNORECASE)


def _is_textbook(extraction: dict) -> bool:
    return (extraction.get("source_classification") or {}).get("kind") == "textbook_subchapter"


def _page_blocks(extraction: dict, page_number: int) -> list[dict]:
    return [
        block
        for block in extraction.get("blocks", [])
        if int((block.get("metadata") or {}).get("page_number", 0) or 0) == page_number
    ]


def _caption_blocks(extraction: dict, page_number: int) -> list[dict]:
    return [
        block
        for block in _page_blocks(extraction, page_number)
        if _FIGURE_CAPTION_START_RE.search(str(block.get("text", "")))
    ]


def _eligible_image_blocks(page: fitz.Page) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    for block in page.get_text("dict", sort=True).get("blocks", []):
        if block.get("type") != 1:
            continue
        bbox = fitz.Rect(block.get("bbox", (0, 0, 0, 0)))
        width_px = int(block.get("width", 0) or 0)
        height_px = int(block.get("height", 0) or 0)
        image_bytes = block.get("image", b"") or b""
        if width_px < 60 or height_px < 45:
            continue
        if bbox.width < 30 or bbox.height < 25 or bbox.get_area() < 1200:
            continue
        if len(image_bytes) < 1500:
            continue
        images.append({"bbox": bbox, "width_px": width_px, "height_px": height_px})
    return images

def _expanded_caption_region(page: fitz.Page, caption_rect: fitz.Rect) -> fitz.Rect:
    region = fitz.Rect(
        max(0, caption_rect.x0 - 100),
        max(0, caption_rect.y0 - 240),
        min(page.rect.width, caption_rect.x1 + 100),
        min(page.rect.height, caption_rect.y1 + 120),
    )
    return region


def _union_rect(rects: list[fitz.Rect], page: fitz.Page, margin: float = 8.0) -> fitz.Rect:
    rect = fitz.Rect(rects[0])
    for item in rects[1:]:
        rect |= item
    return fitz.Rect(
        max(0, rect.x0 - margin),
        max(0, rect.y0 - margin),
        min(page.rect.width, rect.x1 + margin),
        min(page.rect.height, rect.y1 + margin),
    )


def _nearby_context(page_blocks: list[dict], caption: dict, limit: int = 900) -> tuple[str, list[str]]:
    caption_id = str(caption.get("id"))
    try:
        index = next(i for i, block in enumerate(page_blocks) if str(block.get("id")) == caption_id)
    except StopIteration:
        index = 0
    selected = page_blocks[max(0, index - 1) : min(len(page_blocks), index + 2)]
    text = " ".join(str(block.get("text", "")).strip() for block in selected if block.get("text"))
    return text[:limit], [str(block.get("id")) for block in selected if block.get("id")]

def _save_clip(page: fitz.Page, clip: fitz.Rect, path: Path) -> None:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=clip, alpha=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(path)


def extract_textbook_figure_assets(
    pdf_path: str | Path,
    extraction: dict,
    output_dir: str | Path,
) -> list[dict[str, Any]]:
    """Materialize relevant textbook figures as slide-ready PNG assets.

    Structured/manual-like PDFs deliberately return no assets so their proven
    rendering behavior is unchanged. Caption-associated image groups are rendered
    as a single page crop; this also preserves labels, arrows, and vector artwork.
    """
    if not _is_textbook(extraction):
        return []

    source = Path(pdf_path)
    out_dir = Path(output_dir)
    scoped_pages = sorted(
        {
            int((block.get("metadata") or {}).get("page_number", 0) or 0)
            for block in extraction.get("blocks", [])
            if int((block.get("metadata") or {}).get("page_number", 0) or 0) > 0
        }
    )
    assets: list[dict[str, Any]] = []
    document = fitz.open(source)
    try:
        for page_number in scoped_pages:
            if page_number < 1 or page_number > len(document):
                continue
            page = document[page_number - 1]
            images = _eligible_image_blocks(page)
            captions = _caption_blocks(extraction, page_number)
            used: set[int] = set()
            page_blocks = _page_blocks(extraction, page_number)
            asset_index = 0

            for caption in captions:
                caption_bbox = (caption.get("metadata") or {}).get("bbox")
                if not caption_bbox:
                    continue
                caption_rect = fitz.Rect(caption_bbox)
                region = _expanded_caption_region(page, caption_rect)
                matched = [
                    (idx, image)
                    for idx, image in enumerate(images)
                    if image["bbox"].intersects(region)
                ]
                rects = [caption_rect] + [image["bbox"] for _, image in matched]
                if len(rects) == 1:
                    clip = region
                    source_type = "caption_region"
                else:
                    clip = _union_rect(rects, page)
                    source_type = "captioned_image_group"
                asset_index += 1
                asset_id = f"fig_p{page_number:03d}_{asset_index:02d}"
                filename = f"{asset_id}.png"
                asset_path = out_dir / filename
                _save_clip(page, clip, asset_path)
                for idx, _ in matched:
                    used.add(idx)

                caption_text = str(caption.get("text", "")).strip()
                group_match = _FIGURE_CAPTION_RE.search(caption_text)
                context, source_ids = _nearby_context(page_blocks, caption)
                assets.append(
                    {
                        "id": asset_id,
                        "page_number": page_number,
                        "section": caption.get("section"),
                        "caption": caption_text[:1000],
                        "context": context,
                        "group_label": group_match.group(0) if group_match else None,
                        "source_block_ids": source_ids,
                        "asset_path": f"extracted/figures/{filename}",
                        "source_type": source_type,
                        "aspect_ratio": round(clip.width / max(1.0, clip.height), 3),
                        "bbox": [round(float(value), 2) for value in clip],
                    }
                )
            for idx, image in enumerate(images):
                if idx in used:
                    continue
                asset_index += 1
                asset_id = f"fig_p{page_number:03d}_{asset_index:02d}"
                filename = f"{asset_id}.png"
                clip = _union_rect([image["bbox"]], page, margin=4.0)
                asset_path = out_dir / filename
                _save_clip(page, clip, asset_path)
                section = next(
                    (block.get("section") for block in page_blocks if block.get("section")),
                    None,
                )
                nearby_text = " ".join(
                    str(block.get("text", "")).strip()
                    for block in page_blocks
                    if block.get("text")
                )[:900]
                assets.append(
                    {
                        "id": asset_id,
                        "page_number": page_number,
                        "section": section,
                        "caption": "",
                        "context": nearby_text,
                        "group_label": None,
                        "source_block_ids": [str(block.get("id")) for block in page_blocks[:3]],
                        "asset_path": f"extracted/figures/{filename}",
                        "source_type": "embedded_image",
                        "aspect_ratio": round(clip.width / max(1.0, clip.height), 3),
                        "bbox": [round(float(value), 2) for value in clip],
                    }
                )
    finally:
        document.close()
    return assets
