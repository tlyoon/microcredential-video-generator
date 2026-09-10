from __future__ import annotations

from pathlib import Path
import yaml
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN


def _add_footer(slide, slide_id: str, sources: list[str]) -> None:
    box = slide.shapes.add_textbox(Inches(0.6), Inches(7.08), Inches(12.0), Inches(0.25))
    p = box.text_frame.paragraphs[0]
    source_text = ", ".join(sources) if sources else "course framing"
    p.text = f"{slide_id}  •  source sections: {source_text}"
    p.font.size = Pt(9)
    p.alignment = PP_ALIGN.RIGHT


def build_pptx(manifest_path: str | Path, output_path: str | Path) -> Path:
    manifest_path = Path(manifest_path)
    m = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    for item in m["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        title_box = slide.shapes.add_textbox(Inches(0.75), Inches(0.55), Inches(11.85), Inches(0.8))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = item["title"]
        p.font.size = Pt(28)
        p.font.bold = True

        body = slide.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(11.3), Inches(4.7))
        btf = body.text_frame
        btf.clear()
        for j, line in enumerate(item.get("onscreen", [])):
            p = btf.paragraphs[0] if j == 0 else btf.add_paragraph()
            p.text = str(line)
            p.font.size = Pt(24 if item.get("slide_type") != "check" else 28)
            p.space_after = Pt(15)

        equation = item.get("equation_latex")
        if equation:
            p = btf.add_paragraph()
            p.text = f"Equation (LaTeX source): {equation}"
            p.font.size = Pt(18)

        _add_footer(slide, item["id"], item.get("source_sections", []))

        notes_tf = slide.notes_slide.notes_text_frame
        notes_tf.text = item.get("narration", "")
        guidance = []
        if item.get("lecturer_notes"):
            guidance.append("LECTURER NOTES:\n" + "\n".join(f"- {x}" for x in item.get("lecturer_notes", [])))
        if item.get("visual_direction"):
            guidance.append("VISUAL DIRECTION:\n" + str(item.get("visual_direction")))
        if item.get("source_block_ids"):
            guidance.append("SOURCE BLOCKS: " + ", ".join(item.get("source_block_ids", [])))
        if guidance:
            p_notes = notes_tf.add_paragraph()
            p_notes.text = "\n\n".join(guidance)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    return output_path
