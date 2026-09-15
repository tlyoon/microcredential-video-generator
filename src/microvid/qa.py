from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


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
        s for s in slides if s.get("slide_type") in {"concept", "worked_example"}
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

    if m.get("source_document_type") == "textbook_subchapter":
        if len(slides) < 5:
            issues.append({"severity": "error", "message": "Textbook subchapter requires at least five slides."})
        if not slides or slides[0].get("slide_type") != "title":
            issues.append({"severity": "error", "message": "Textbook subchapter must begin with a title slide."})
        if slides and str(slides[0].get("title", "")).strip() != str(m.get("title", "")).strip():
            issues.append({"severity": "error", "message": "Textbook title slide must use the exact lesson title."})
        if slides and (slides[0].get("onscreen") or slides[0].get("figure_ids")):
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
    textbook = m.get("source_document_type") == "textbook_subchapter"
    valid_figure_ids = {str(item.get("id")) for item in m.get("figure_assets", []) or []}
    for s in slides:
        if not s.get("narration"):
            issues.append(
                {"severity": "error", "slide": s.get("id"), "message": "Missing narration."}
            )
        if s.get("slide_type") in {"concept", "worked_example"} and not s.get(
            "source_block_ids"
        ):
            issues.append(
                {
                    "severity": "error",
                    "slide": s.get("id"),
                    "message": "Source-derived slide lacks provenance.",
                }
            )
        if len(" ".join(s.get("onscreen", []))) > 420:
            issues.append(
                {
                    "severity": "warning",
                    "slide": s.get("id"),
                    "message": "On-screen text is dense.",
                }
            )
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
