from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz

_FIGURE_CAPTION_RE = re.compile(r"\b(?:Figure|Fig\.)\s+\d+(?:\.\d+)+\b", re.IGNORECASE)


def _is_textbook(extraction: dict) -> bool:
    return (extraction.get("source_classification") or {}).get("kind") == "textbook_subchapter"


def _page_blocks(extraction: dict, page_number: int) -> list[dict]:
    return [
        block
        for block in extraction.get("blocks", [])
        if int((block.get("metadata") or {}).get("page_number", 0) or 0) == page_number
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
    # Textbook captions are often below multi-panel artwork. Give the crop enough
    # room above the actual caption to retain graphs/diagrams, and enough horizontal
    # room for side-by-side panels without swallowing the entire neighbouring page.
    return fitz.Rect(
        max(36, caption_rect.x0 - 340),
        max(0, caption_rect.y0 - 450),
        min(page.rect.width - 36, caption_rect.x1 + 220),
        min(page.rect.height, caption_rect.y1 + 135),
    )


def _nearby_drawing_rects(page: fitz.Page, caption_rect: fitz.Rect) -> list[fitz.Rect]:
    """Return vector drawing groups geometrically associated with a caption label."""
    candidates: list[tuple[float, fitz.Rect]] = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if not rect:
            continue
        rect = fitz.Rect(rect)
        # Ignore tiny glyph/decorative fragments; retain meaningful plot/diagram groups.
        if rect.get_area() < 100 and not (rect.width >= 18 and rect.height >= 18):
            continue
        # Figure artwork normally sits above or level with its caption. Exclude lower
        # pitfall/callout panels that are nearby on the page but not part of the figure.
        if rect.y0 > caption_rect.y1 + 20:
            continue
        dx = max(caption_rect.x0 - rect.x1, rect.x0 - caption_rect.x1, 0.0)
        dy = max(caption_rect.y0 - rect.y1, rect.y0 - caption_rect.y1, 0.0)
        distance = (dx * dx + dy * dy) ** 0.5
        candidates.append((distance, rect))
    if not candidates:
        return []
    nearest = min(distance for distance, _ in candidates)
    # Multi-panel figures can place a companion graph well above the caption.
    # Keep drawing groups in the same geometric neighborhood, but reject more distant
    # boxes such as adjacent pitfall panels or page ornaments.
    cutoff = nearest + 165.0
    selected = [rect for distance, rect in candidates if distance <= cutoff]
    return selected


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


def _nearby_context(page_blocks: list[dict], source_block_id: str, limit: int = 1100) -> tuple[str, list[str]]:
    try:
        index = next(i for i, block in enumerate(page_blocks) if str(block.get("id")) == source_block_id)
    except StopIteration:
        index = 0
    selected = page_blocks[max(0, index - 1): min(len(page_blocks), index + 2)]
    text = " ".join(str(block.get("text", "")).strip() for block in selected if block.get("text"))
    return text[:limit], [str(block.get("id")) for block in selected if block.get("id")]


def _caption_candidates(extraction: dict, page: fitz.Page, page_number: int) -> list[dict[str, Any]]:
    """Locate actual figure captions rather than earlier in-prose references.

    Textbook pages often mention a figure several times before the printed caption.
    Prefer the occurrence with the shortest trailing text inside its source block, and
    map it to a page-search hit that lies inside that block's bounding box.
    """
    best: dict[str, tuple[tuple[int, int], dict[str, Any]]] = {}
    for block in _page_blocks(extraction, page_number):
        text = str(block.get("text", ""))
        bbox_values = (block.get("metadata") or {}).get("bbox")
        block_rect = fitz.Rect(bbox_values) if bbox_values else None
        matches = list(_FIGURE_CAPTION_RE.finditer(text))
        for match in matches:
            label = match.group(0)
            key = label.lower()
            next_match = _FIGURE_CAPTION_RE.search(text, match.end())
            end = next_match.start() if next_match else len(text)
            trailing = text[match.end():end].strip()
            caption_text = text[match.start():end].strip()
            hits = [fitz.Rect(hit) for hit in page.search_for(label)]
            in_block = []
            if block_rect is not None:
                padded = fitz.Rect(block_rect.x0 - 3, block_rect.y0 - 3, block_rect.x1 + 3, block_rect.y1 + 3)
                in_block = [hit for hit in hits if hit.intersects(padded)]
            if in_block:
                caption_rect = in_block[-1]
            elif hits and block_rect is not None:
                cx, cy = (block_rect.x0 + block_rect.x1) / 2, (block_rect.y0 + block_rect.y1) / 2
                caption_rect = min(
                    hits,
                    key=lambda hit: ((hit.x0 + hit.x1) / 2 - cx) ** 2 + ((hit.y0 + hit.y1) / 2 - cy) ** 2,
                )
            elif hits:
                caption_rect = hits[-1]
            elif block_rect is not None:
                caption_rect = block_rect
            else:
                continue

            # Actual captions are usually compact; prose references typically have
            # much more explanatory text after the figure number.
            cleaned_trailing = trailing.lstrip("\u200b\ufeff ")
            caption_like = bool(re.match(r"^(?:\([a-zA-Z]\)|[A-Z])", cleaned_trailing))
            score = (0 if caption_like else 1, len(trailing))
            candidate = {
                "label": label,
                "caption": caption_text[:1000],
                "rect": caption_rect,
                "source_block_id": str(block.get("id", "")),
                "section": block.get("section"),
            }
            if key not in best or score < best[key][0]:
                best[key] = (score, candidate)
    return [item[1] for item in best.values()]


def _scope_position(raw_extraction: dict, scoped_extraction: dict, source_block_id: str) -> tuple[str, int]:
    raw_ids = [str(block.get("id")) for block in raw_extraction.get("blocks", [])]
    position = {block_id: i for i, block_id in enumerate(raw_ids)}
    included = [
        str(x)
        for x in (scoped_extraction.get("textbook_subchapter_ingestion") or {}).get("included_block_ids", [])
    ]
    included_positions = [position[x] for x in included if x in position]
    if source_block_id in included:
        return "within_target", 0
    if not included_positions or source_block_id not in position:
        return "same_page_adjacent", 0
    p = position[source_block_id]
    low, high = min(included_positions), max(included_positions)
    if p < low:
        return "before_target", low - p
    if p > high:
        return "after_target", p - high
    return "within_target_span", 0


def _layout_metadata(width_px: int, height_px: int) -> dict[str, Any]:
    ratio = width_px / max(1, height_px)
    if ratio > 1.6:
        orientation = "wide"
        hint = "image_large"
        columns = "single_column"
    elif ratio < 0.8:
        orientation = "portrait"
        hint = "image_right"
        columns = "two_columns"
    elif ratio < 1.1:
        orientation = "near_square"
        hint = "image_right"
        columns = "two_columns"
    else:
        orientation = "landscape"
        hint = "image_large"
        columns = "single_column"
    return {
        "width_px": width_px,
        "height_px": height_px,
        "aspect_ratio": round(ratio, 3),
        "orientation": orientation,
        "recommended_layout_hint": hint,
        "recommended_columns_layout": columns,
        "fit_policy": "bounded_box_keep_aspect_ratio",
    }


def _save_clip(page: fitz.Page, clip: fitz.Rect, path: Path) -> tuple[int, int]:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=clip, alpha=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(path)
    return int(pixmap.width), int(pixmap.height)


def extract_textbook_figure_assets(
    pdf_path: str | Path,
    extraction: dict,
    output_dir: str | Path,
    *,
    raw_extraction: dict | None = None,
) -> list[dict[str, Any]]:
    """Inventory/crop figures before slide selection, including same-page spillover.

    Discovery uses the raw extraction so a caption just outside the target subsection
    is not silently discarded. Cropping remains limited to pages touched by the target.
    Each asset records its relation to the target boundary for safe LLM selection.
    """
    if not _is_textbook(extraction):
        return []

    source = Path(pdf_path)
    out_dir = Path(output_dir)
    raw_source = raw_extraction or extraction
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
            captions = _caption_candidates(raw_source, page, page_number)
            raw_page_blocks = _page_blocks(raw_source, page_number)
            used: set[int] = set()
            asset_index = 0

            for caption in captions:
                caption_rect = caption["rect"]
                region = _expanded_caption_region(page, caption_rect)
                matched = [
                    (idx, image)
                    for idx, image in enumerate(images)
                    if image["bbox"].intersects(region)
                ]
                drawing_rects = _nearby_drawing_rects(page, caption_rect)
                rects = [caption_rect] + [image["bbox"] for _, image in matched] + drawing_rects
                if len(rects) == 1:
                    clip = region
                    source_type = "caption_region"
                else:
                    clip = _union_rect(rects, page, margin=14.0)
                    source_type = "captioned_graphic_group"

                asset_index += 1
                asset_id = f"fig_p{page_number:03d}_{asset_index:02d}"
                filename = f"{asset_id}.png"
                asset_path = out_dir / filename
                width_px, height_px = _save_clip(page, clip, asset_path)
                for idx, _ in matched:
                    used.add(idx)

                context, source_ids = _nearby_context(
                    raw_page_blocks, caption["source_block_id"]
                )
                relation, distance = _scope_position(
                    raw_source, extraction, caption["source_block_id"]
                )
                assets.append(
                    {
                        "id": asset_id,
                        "page_number": page_number,
                        "section": caption.get("section"),
                        "caption": caption.get("caption", ""),
                        "context": context,
                        "group_label": caption.get("label"),
                        "source_block_ids": source_ids,
                        "caption_source_block_id": caption["source_block_id"],
                        "scope_relation": relation,
                        "scope_distance_blocks": distance,
                        "asset_path": f"extracted/figures/{filename}",
                        "source_type": source_type,
                        "bbox": [round(float(value), 2) for value in clip],
                        **_layout_metadata(width_px, height_px),
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
                width_px, height_px = _save_clip(page, clip, asset_path)
                nearby_text = " ".join(
                    str(block.get("text", "")).strip()
                    for block in raw_page_blocks
                    if block.get("text")
                )[:900]
                assets.append(
                    {
                        "id": asset_id,
                        "page_number": page_number,
                        "section": next(
                            (block.get("section") for block in raw_page_blocks if block.get("section")),
                            None,
                        ),
                        "caption": "",
                        "context": nearby_text,
                        "group_label": None,
                        "source_block_ids": [str(block.get("id")) for block in raw_page_blocks[:3]],
                        "caption_source_block_id": None,
                        "scope_relation": "same_page_unlabelled",
                        "scope_distance_blocks": 0,
                        "asset_path": f"extracted/figures/{filename}",
                        "source_type": "embedded_image",
                        "bbox": [round(float(value), 2) for value in clip],
                        **_layout_metadata(width_px, height_px),
                    }
                )
    finally:
        document.close()
    return assets
