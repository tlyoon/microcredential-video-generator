from __future__ import annotations

import json
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
                "message": "Lesson matched zero authoritative source blocks. The global plan or legacy profile is incompatible with this DOCX.",
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
    if len(slides) > 9:
        issues.append({"severity": "warning", "message": f"High slide count: {len(slides)}."})
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
