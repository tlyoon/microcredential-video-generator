from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from .office_math import latex_to_omml


def _visible_slide_strings(slide: dict) -> list[str]:
    values = [str(slide.get("title", ""))]
    values.extend(str(value) for value in slide.get("onscreen", []) or [])
    for panel in slide.get("visual_panels", []) or []:
        values.append(str(panel.get("heading", "")))
        values.extend(str(value) for value in panel.get("body", []) or [])
    values.extend(str(value) for value in slide.get("table_headers", []) or [])
    for row in slide.get("table_rows", []) or []:
        values.extend(str(value) for value in row)
    return [value.strip() for value in values if value.strip()]


def validate_slide_surface(slide: dict) -> list[dict]:
    """Return blocking issues that could make a rendered slide unreadable."""
    slide_id = slide.get("id")
    issues: list[dict] = []
    visual_type = str(slide.get("visual_type", "auto") or "auto")
    onscreen = [
        str(value).strip()
        for value in slide.get("onscreen", []) or []
        if str(value).strip()
    ]
    onscreen_chars = len(" ".join(onscreen))
    has_rich_visual = bool(
        slide.get("visual_panels")
        or slide.get("table_rows")
        or slide.get("figure_ids")
        or slide.get("equation_latex")
        or visual_type in {"process", "comparison", "diagram", "table", "figure", "equation_focus"}
    )
    line_limit, char_limit = (2, 140) if has_rich_visual else (4, 260)
    if len(onscreen) > line_limit or onscreen_chars > char_limit:
        issues.append({
            "severity": "error",
            "slide": slide_id,
            "message": (
                "On-screen lead text exceeds the safe layout budget "
                f"({len(onscreen)}/{line_limit} entries, {onscreen_chars}/{char_limit} characters)."
            ),
        })
    equation = str(slide.get("equation_latex") or "").strip()
    if equation:
        try:
            latex_to_omml(equation)
        except Exception as exc:
            issues.append({"severity": "error", "slide": slide_id, "message": f"equation_latex cannot be converted to native Office Math: {exc}"})
    visible_text = " ".join(_visible_slide_strings(slide))
    if re.search(r"\$[^$]+\$|\\(?:frac|sqrt|sum|begin|mathrm|left|right)\b", visible_text):
        issues.append({
            "severity": "error",
            "slide": slide_id,
            "message": "Visible text contains raw TeX/LaTeX; use equation_latex or compact renderer-convertible notation.",
        })
    for panel_index, panel in enumerate(slide.get("visual_panels", []) or [], start=1):
        heading = str(panel.get("heading", "")).strip()
        body = [
            str(value).strip()
            for value in panel.get("body", []) or []
            if str(value).strip()
        ]
        body_chars = len(" ".join(body))
        if len(heading.split()) > 7 or len(body) > 3 or body_chars > 160:
            issues.append({
                "severity": "error",
                "slide": slide_id,
                "message": (
                    f"Visual panel {panel_index} exceeds the safe layout budget "
                    f"({len(heading.split())}/7 heading words, {len(body)}/3 body entries, "
                    f"{body_chars}/160 body characters)."
                ),
            })
    table_headers = slide.get("table_headers", []) or []
    table_rows = slide.get("table_rows", []) or []
    longest_cell = max((len(str(value)) for row in table_rows for value in row), default=0)
    if len(table_headers) > 5 or len(table_rows) > 8 or longest_cell > 100:
        issues.append({
            "severity": "error",
            "slide": slide_id,
            "message": (
                "Table exceeds the safe layout budget "
                f"({len(table_headers)}/5 columns, {len(table_rows)}/8 rows, "
                f"{longest_cell}/100 characters in the longest cell)."
            ),
        })
    return issues


def validate_manifest(m: dict) -> list[dict]:
    issues: list[dict] = []
    slides = m.get("slides", [])
    if not slides:
        issues.append({"severity": "error", "message": "Manifest contains no slides."})
        return issues

    if int(m.get("source_core_block_count", 1)) == 0:
        issues.append(
            {
                "severity": "error",
                "message": "Lesson matched zero authoritative source blocks. The global plan or legacy profile is incompatible with this source document.",
            }
        )

    source_slides = [
        s
        for s in slides
        if s.get("slide_type") in {"concept", "worked_example", "method", "interpretation"}
    ]
    if not source_slides:
        issues.append(
            {
                "severity": "error",
                "message": "Lesson contains no source-derived concept/worked-example slides.",
            }
        )

    target = float(m.get("target_minutes", 6)) * 60
    actual = sum(float(s.get("estimated_seconds", 0)) for s in slides)
    if actual < target * 0.55:
        issues.append(
            {
                "severity": "warning",
                "message": f"Draft is short: {actual/60:.1f} min vs target {target/60:.1f} min.",
            }
        )
    if actual > target * 1.35:
        issues.append(
            {
                "severity": "warning",
                "message": f"Draft is long: {actual/60:.1f} min vs target {target/60:.1f} min.",
            }
        )
    if not any(s.get("slide_type") == "check" for s in slides):
        issues.append({"severity": "error", "message": "No check-your-understanding slide."})

    textbook = m.get("source_document_type") == "textbook_subchapter"
    is_llm = (m.get("generation") or {}).get("mode") == "llm"
    if is_llm and not textbook:
        if len(slides) < 5:
            issues.append({"severity": "error", "message": "Self-learning LLM lesson requires at least five slides."})
        if slides and slides[0].get("slide_type") != "introduction":
            issues.append({"severity": "error", "message": "Self-learning LLM lesson must begin with an introduction slide."})
        if slides and slides[-1].get("slide_type") != "conclusion":
            issues.append({"severity": "error", "message": "Self-learning LLM lesson must end with a conclusion slide."})

    if textbook:
        if len(slides) < 5:
            issues.append({"severity": "error", "message": "Textbook subchapter requires at least five slides."})
        if not slides or slides[0].get("slide_type") != "title":
            issues.append({"severity": "error", "message": "Textbook subchapter must begin with a title slide."})
        if slides and str(slides[0].get("title", "")).strip() != str(m.get("title", "")).strip():
            issues.append({"severity": "error", "message": "Textbook title slide must use the exact lesson title."})
        if slides and (
            slides[0].get("onscreen")
            or slides[0].get("figure_ids")
            or slides[0].get("visual_panels")
            or slides[0].get("table_headers")
            or slides[0].get("table_rows")
        ):
            issues.append({"severity": "error", "message": "Textbook title slide must contain only the exact title."})
        if len(slides) < 2 or slides[1].get("slide_type") != "introduction":
            issues.append({"severity": "error", "message": "Textbook subchapter must include an introduction slide immediately after the title."})
        if any(str(slide.get("title", "")).strip() for slide in slides[1:]):
            issues.append({"severity": "error", "message": "Textbook slides after Slide 1 must not contain visible slide titles."})
        if not slides or slides[-1].get("slide_type") != "conclusion":
            issues.append({"severity": "error", "message": "Textbook subchapter must end with a conclusion slide."})
        if m.get("figure_assets") and not any(slide.get("figure_ids") for slide in slides):
            issues.append({"severity": "error", "message": "Relevant textbook figure assets are available but none are used in the lesson."})
    if len(slides) > 9:
        issues.append({"severity": "warning", "message": f"High slide count: {len(slides)}."})
    valid_figure_ids = {str(item.get("id")) for item in m.get("figure_assets", []) or []}
    for s in slides:
        if not s.get("narration"):
            issues.append(
                {"severity": "error", "slide": s.get("id"), "message": "Missing narration."}
            )
        if s.get("slide_type") in {"concept", "worked_example", "method", "interpretation"} and not s.get(
            "source_block_ids"
        ):
            issues.append(
                {
                    "severity": "error",
                    "slide": s.get("id"),
                    "message": "Source-derived slide lacks provenance.",
                }
            )
        if len(" ".join(s.get("onscreen", []))) > 320:
            issues.append(
                {
                    "severity": "warning",
                    "slide": s.get("id"),
                    "message": "On-screen text is dense.",
                }
            )
        visual_type = str(s.get("visual_type", "auto") or "auto")
        issues.extend(validate_slide_surface(s))
        if visual_type in {"process", "comparison", "diagram"} and not s.get("visual_panels"):
            issues.append({"severity": "warning", "slide": s.get("id"), "message": f"Visual type '{visual_type}' has no visual panels."})
        if visual_type == "table" and (not s.get("table_headers") or not s.get("table_rows")):
            issues.append({"severity": "warning", "slide": s.get("id"), "message": "Table visual lacks table headers or rows."})
        narration = str(s.get("narration", ""))
        if is_llm and re.search(r"\\[A-Za-z]+|\$|\b[A-Za-z][A-Za-z0-9_]*\s*=\s*[^,.!?;]+", narration):
            issues.append({"severity": "error", "slide": s.get("id"), "message": "Narration contains symbolic/TeX mathematics instead of plain spoken English."})
        if textbook:
            visible = " ".join(str(x) for x in s.get("onscreen", []))
            narration = str(s.get("narration", ""))
            invalid_figures = [str(x) for x in s.get("figure_ids", []) if str(x) not in valid_figure_ids]
            if invalid_figures:
                issues.append({"severity": "error", "slide": s.get("id"), "message": f"Unknown textbook figure IDs: {invalid_figures}."})
            if s.get("figure_ids") and len(visible) > 300:
                issues.append({"severity": "warning", "slide": s.get("id"), "message": "Figure-bearing textbook slide has dense on-screen text; reduce text for visual readability."})
            if re.search(r"\b(?:page|slide)\s+\d+(?:\s+of\s+\d+)?\b|(?:cite|filecite)|\bsource[_ ]block\b", visible + " " + narration, flags=re.IGNORECASE):
                issues.append({"severity": "error", "slide": s.get("id"), "message": "Textbook slide exposes a counter, citation marker, or source artefact."})
            if re.search(r"\\[A-Za-z]+|\$|[₀-₉]|[⁰¹²³⁴⁵⁶⁷⁸⁹]|[±×÷√∑Σ]|\b[A-Za-z][A-Za-z0-9_]*\s*=\s*[^,.!?;]+", narration):
                issues.append({"severity": "error", "slide": s.get("id"), "message": "Textbook narration contains symbolic/TeX mathematics instead of plain spoken English."})
    if is_llm and len(slides) >= 5:
        middle = slides[1:-1] if len(slides) > 2 else slides
        plain = [
            slide
            for slide in middle
            if str(slide.get("visual_type", "auto") or "auto") in {"auto", "text"}
            and not slide.get("visual_panels")
            and not slide.get("table_rows")
            and not slide.get("figure_ids")
            and not slide.get("equation_latex")
        ]
        if middle and len(plain) >= max(3, int(len(middle) * 0.75)):
            issues.append({"severity": "warning", "message": "Most substantive slides use plain text; consider source-grounded process/comparison/table/diagram/equation/figure visuals."})
    return issues


def _course_level_issues(workspace: Path) -> list[dict]:
    course_index = workspace / "manifests" / "course.yaml"
    if not course_index.exists():
        return []
    payload = yaml.safe_load(course_index.read_text(encoding="utf-8")) or {}
    if payload.get("design_mode") != "global_llm":
        return []

    status = str(payload.get("global_consistency_status", "revision_required"))
    if status == "ready":
        return []
    if status == "not_applicable":
        return [
            {
                "severity": "warning",
                "message": "Whole-course consistency review was skipped for this global-design build.",
            }
        ]
    return [
        {
            "severity": "error",
            "message": f"Whole-course consistency status is '{status}', not ready for normal slide/media production.",
        }
    ]


def validate_workspace(workspace: str | Path) -> dict:
    workspace = Path(workspace)
    result = {"course": [], "videos": {}, "errors": 0, "warnings": 0}

    course_issues = _course_level_issues(workspace)
    result["course"] = course_issues
    result["errors"] += sum(i["severity"] == "error" for i in course_issues)
    result["warnings"] += sum(i["severity"] == "warning" for i in course_issues)

    for path in sorted((workspace / "manifests").glob("video_*.yaml")):
        m = yaml.safe_load(path.read_text(encoding="utf-8"))
        issues = validate_manifest(m)
        result["videos"][m["video_id"]] = issues
        result["errors"] += sum(i["severity"] == "error" for i in issues)
        result["warnings"] += sum(i["severity"] == "warning" for i in issues)

    out = workspace / "qa" / "validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
