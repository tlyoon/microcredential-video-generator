from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from .llm import JSONLLMProvider, LLMError


def _read_prompt(name: str) -> str:
    return files("microvid").joinpath("prompts", name).read_text(encoding="utf-8")


def course_consistency_schema() -> dict[str, Any]:
    finding = {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["blocking", "advisory"]},
            "video_id": {"type": ["string", "null"]},
            "issue": {"type": "string"},
            "recommendation": {"type": "string"},
        },
        "required": ["severity", "video_id", "issue", "recommendation"],
        "additionalProperties": False,
    }
    revision = {
        "type": "object",
        "properties": {
            "video_id": {"type": "string"},
            "instructions": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        },
        "required": ["video_id", "instructions"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["ready", "revision_required"]},
            "summary": {"type": "string"},
            "findings": {"type": "array", "items": finding},
            "lesson_revision_instructions": {"type": "array", "items": revision},
        },
        "required": ["status", "summary", "findings", "lesson_revision_instructions"],
        "additionalProperties": False,
    }


def _compact_manifest(manifest: dict) -> dict[str, Any]:
    return {
        "video_id": manifest.get("video_id"),
        "title": manifest.get("title"),
        "focus": manifest.get("focus"),
        "learning_outcomes": manifest.get("learning_outcomes", []),
        "target_minutes": manifest.get("target_minutes"),
        "slides": [
            {
                "id": slide.get("id"),
                "slide_type": slide.get("slide_type"),
                "title": slide.get("title"),
                "onscreen": slide.get("onscreen", []),
                "narration": slide.get("narration", ""),
                "equation_latex": slide.get("equation_latex"),
                "source_block_ids": slide.get("source_block_ids", []),
                "estimated_seconds": slide.get("estimated_seconds"),
            }
            for slide in manifest.get("slides", [])
        ],
    }


def review_course_consistency(
    global_plan: dict,
    manifests: list[dict],
    provider: JSONLLMProvider,
    *,
    verification: bool = False,
) -> dict:
    prompt = "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("global_course_consistency_review.md"),
            "## REVIEW PHASE\n" + ("FINAL VERIFICATION AFTER TARGETED REVISIONS" if verification else "INITIAL WHOLE-COURSE REVIEW"),
            "## APPROVED GLOBAL COURSE PLAN\n```json\n"
            + json.dumps(global_plan, ensure_ascii=False, indent=2)
            + "\n```",
            "## GENERATED LESSON MANIFESTS\n```json\n"
            + json.dumps([_compact_manifest(m) for m in manifests], ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )
    report = provider.generate_json(prompt, course_consistency_schema())
    video_ids = {str(m.get("video_id")) for m in manifests}
    bad = [
        str(x.get("video_id"))
        for x in report.get("lesson_revision_instructions", [])
        if str(x.get("video_id")) not in video_ids
    ]
    if bad:
        raise LLMError(f"Whole-course review requested revisions for unknown video IDs: {bad}")
    if report.get("status") == "ready" and any(
        x.get("severity") == "blocking" for x in report.get("findings", [])
    ):
        raise LLMError("Whole-course review returned status=ready while also reporting blocking findings.")
    return report


def blocking_findings(report: dict) -> list[dict]:
    return [x for x in report.get("findings", []) if x.get("severity") == "blocking"]
