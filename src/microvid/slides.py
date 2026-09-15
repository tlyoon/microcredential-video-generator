from __future__ import annotations

import math
from pathlib import Path

import yaml
from PIL import Image
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from .office_math import looks_like_math, set_native_math_paragraph, visible_math_to_latex


def _add_footer(slide, slide_id: str, sources: list[str]) -> None:
    box = slide.shapes.add_textbox(Inches(0.6), Inches(7.08), Inches(12.0), Inches(0.25))
    p = box.text_frame.paragraphs[0]
    source_text = ", ".join(sources) if sources else "course framing"
    p.text = f"{slide_id}  •  source sections: {source_text}"
    p.font.size = Pt(9)
    p.alignment = PP_ALIGN.RIGHT


def _body_font_size(lines: list[str], *, has_figure: bool) -> int:
    chars = len(" ".join(str(x) for x in lines))
    if chars <= 90:
        return 28 if not has_figure else 25
    if chars <= 190:
        return 25 if not has_figure else 22
    if chars <= 300:
        return 22 if not has_figure else 19
    return 18

def _add_body(slide, item: dict, x: float, y: float, w: float, h: float, *, has_figure: bool) -> None:
    body = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    btf = body.text_frame
    btf.clear()
    lines = [str(line) for line in item.get("onscreen", [])]
    font_size = _body_font_size(lines, has_figure=has_figure)
    for j, line in enumerate(lines):
        p = btf.paragraphs[0] if j == 0 else btf.add_paragraph()
        if looks_like_math(line):
            set_native_math_paragraph(
                p, visible_math_to_latex(line), font_size_pt=font_size, alignment="left"
            )
        else:
            p.text = line
            p.font.size = Pt(font_size)
        p.space_after = Pt(12)

    equation = item.get("equation_latex")
    if equation:
        p = btf.add_paragraph()
        set_native_math_paragraph(
            p, str(equation), font_size_pt=max(18, font_size), alignment="centerGroup"
        )


def _fit_picture(slide, image_path: Path, x: float, y: float, w: float, h: float) -> None:
    with Image.open(image_path) as image:
        px_w, px_h = image.size
    aspect = px_w / max(1, px_h)
    box_aspect = w / max(0.01, h)
    if aspect >= box_aspect:
        draw_w = w
        draw_h = w / aspect
    else:
        draw_h = h
        draw_w = h * aspect
    draw_x = x + (w - draw_w) / 2
    draw_y = y + (h - draw_h) / 2
    slide.shapes.add_picture(
        str(image_path), Inches(draw_x), Inches(draw_y), Inches(draw_w), Inches(draw_h)
    )

def _resolve_figure_paths(manifest_path: Path, item: dict) -> list[Path]:
    workspace = manifest_path.parent.parent
    paths: list[Path] = []
    for asset in item.get("figure_assets", []) or []:
        rel = str(asset.get("asset_path", "")).strip()
        if not rel:
            continue
        path = workspace / rel
        if path.is_file():
            paths.append(path)
    return paths


def _add_picture_grid(slide, paths: list[Path], x: float, y: float, w: float, h: float) -> None:
    if not paths:
        return
    count = len(paths)
    cols = 1 if count == 1 else 2 if count <= 4 else 3
    rows = math.ceil(count / cols)
    gap = 0.12
    cell_w = (w - gap * (cols - 1)) / cols
    cell_h = (h - gap * (rows - 1)) / rows
    for index, path in enumerate(paths):
        row, col = divmod(index, cols)
        _fit_picture(
            slide,
            path,
            x + col * (cell_w + gap),
            y + row * (cell_h + gap),
            cell_w,
            cell_h,
        )


def _add_notes(slide, item: dict) -> None:
    notes_tf = slide.notes_slide.notes_text_frame
    notes_tf.text = item.get("narration", "")
    guidance: list[str] = []
    if item.get("lecturer_notes"):
        guidance.append("LECTURER NOTES:\n" + "\n".join(f"- {x}" for x in item.get("lecturer_notes", [])))
    if item.get("visual_direction"):
        guidance.append("VISUAL DIRECTION:\n" + str(item.get("visual_direction")))
    if item.get("source_block_ids"):
        guidance.append("SOURCE BLOCKS: " + ", ".join(item.get("source_block_ids", [])))
    if item.get("figure_ids"):
        guidance.append("TEXTBOOK FIGURES: " + ", ".join(item.get("figure_ids", [])))
    if guidance:
        p_notes = notes_tf.add_paragraph()
        p_notes.text = "\n\n".join(guidance)

def _build_standard_slide(prs: Presentation, item: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title_box = slide.shapes.add_textbox(Inches(0.75), Inches(0.55), Inches(11.85), Inches(0.8))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = item["title"]
    p.font.size = Pt(28)
    p.font.bold = True

    _add_body(slide, item, 1.0, 1.7, 11.3, 4.7, has_figure=False)
    _add_footer(slide, item["id"], item.get("source_sections", []))
    _add_notes(slide, item)
    return slide


def _build_textbook_title_slide(prs: Presentation, lesson_title: str, item: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    box = slide.shapes.add_textbox(Inches(0.85), Inches(2.35), Inches(11.65), Inches(2.0))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = lesson_title
    p.font.size = Pt(36)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER
    _add_notes(slide, item)
    return slide

def _build_textbook_content_slide(prs: Presentation, manifest_path: Path, item: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    figure_paths = _resolve_figure_paths(manifest_path, item)
    hint = str(item.get("figure_layout_hint", "auto"))
    lines = [str(x) for x in item.get("onscreen", [])]

    if not figure_paths:
        _add_body(slide, item, 0.95, 0.85, 11.45, 5.95, has_figure=False)
    elif len(figure_paths) == 1 and (hint == "image_large" or len(" ".join(lines)) <= 90):
        _add_picture_grid(slide, figure_paths, 1.0, 0.55, 11.3, 4.75)
        _add_body(slide, item, 1.1, 5.35, 11.1, 1.35, has_figure=True)
    elif hint == "image_left":
        _add_picture_grid(slide, figure_paths, 0.65, 0.75, 6.4, 5.95)
        _add_body(slide, item, 7.3, 0.95, 5.15, 5.6, has_figure=True)
    elif len(figure_paths) >= 2 or hint == "grid":
        _add_body(slide, item, 0.65, 0.9, 4.35, 5.7, has_figure=True)
        _add_picture_grid(slide, figure_paths, 5.2, 0.65, 7.45, 6.0)
    else:
        _add_body(slide, item, 0.65, 0.95, 5.15, 5.55, has_figure=True)
        _add_picture_grid(slide, figure_paths, 6.05, 0.75, 6.55, 5.95)

    _add_notes(slide, item)
    return slide


def build_pptx(manifest_path: str | Path, output_path: str | Path) -> Path:
    manifest_path = Path(manifest_path)
    m = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    textbook = m.get("source_document_type") == "textbook_subchapter"

    for index, item in enumerate(m["slides"]):
        if textbook and index == 0:
            _build_textbook_title_slide(prs, str(m.get("title", "")), item)
        elif textbook:
            _build_textbook_content_slide(prs, manifest_path, item)
        else:
            _build_standard_slide(prs, item)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    return output_path
