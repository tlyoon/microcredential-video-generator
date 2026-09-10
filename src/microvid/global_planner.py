from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from .llm import JSONLLMProvider, LLMError


def _read_prompt(name: str) -> str:
    return files("microvid").joinpath("prompts", name).read_text(encoding="utf-8")


def whole_document_packet(extraction: dict) -> list[dict[str, Any]]:
    """Return the complete structured DOCX extraction in prompt-friendly form.

    The global planning pass deliberately receives every extracted semantic block. Raw OMML
    XML is retained locally in the extraction JSON, but readable math tokens are sent instead.
    """
    packet: list[dict[str, Any]] = []
    for block in extraction.get("blocks", []):
        meta = block.get("metadata", {}) or {}
        packet.append(
            {
                "id": block.get("id"),
                "kind": block.get("kind"),
                "section": block.get("section"),
                "heading_level": block.get("heading_level"),
                "heading_path": meta.get("heading_path", []),
                "text": block.get("text", ""),
                "math_text": meta.get("math_text", []),
                "contains_office_math": bool(block.get("omml")),
            }
        )
    return packet


def extraction_signature(extraction: dict) -> str:
    """Stable digest used to reject a stale global plan after the DOCX changes."""
    payload = whole_document_packet(extraction)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def global_course_plan_schema(max_videos: int = 30) -> dict[str, Any]:
    concept = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "source_block_ids": {"type": "array", "items": {"type": "string"}},
            "prerequisite_concepts": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "description", "source_block_ids", "prerequisite_concepts"],
        "additionalProperties": False,
    }
    video = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "focus": {"type": "string"},
            "target_minutes": {"type": "number", "minimum": 2, "maximum": 20},
            "max_slides": {"type": "integer", "minimum": 4, "maximum": 12},
            "learning_outcomes": {"type": "array", "items": {"type": "string"}},
            "check_question": {"type": "string"},
            "takeaways": {"type": "array", "items": {"type": "string"}},
            "core_block_ids": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "reference_block_ids": {"type": "array", "items": {"type": "string"}},
            "prerequisite_video_ids": {"type": "array", "items": {"type": "string"}},
            "already_taught": {"type": "array", "items": {"type": "string"}},
            "forward_links": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "id",
            "title",
            "focus",
            "target_minutes",
            "max_slides",
            "learning_outcomes",
            "check_question",
            "takeaways",
            "core_block_ids",
            "reference_block_ids",
            "prerequisite_video_ids",
            "already_taught",
            "forward_links",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "course_summary": {"type": "string"},
            "pedagogical_strategy": {"type": "string"},
            "concept_map": {"type": "array", "items": concept},
            "videos": {"type": "array", "minItems": 1, "maxItems": max_videos, "items": video},
            "coverage_notes": {"type": "array", "items": {"type": "string"}},
            "editorial_flags": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "course_summary",
            "pedagogical_strategy",
            "concept_map",
            "videos",
            "coverage_notes",
            "editorial_flags",
        ],
        "additionalProperties": False,
    }


def _planning_context(extraction: dict, profile: dict) -> dict[str, Any]:
    course = profile.get("course", {})
    llm_cfg = course.get("llm", {}) or {}
    global_cfg = llm_cfg.get("global_design", {}) or {}
    packet = whole_document_packet(extraction)
    source_chars = sum(len(str(b.get("text", ""))) for b in packet)
    max_chars = int(global_cfg.get("max_source_characters", 800_000))
    if source_chars > max_chars:
        raise LLMError(
            f"Whole-document planning packet is {source_chars:,} characters, above configured "
            f"global-design limit {max_chars:,}. The package will not silently truncate the source."
        )
    return {
        "course_constraints": {
            "id": course.get("id"),
            "title": course.get("title"),
            "audience": course.get("audience"),
            "source_role": course.get("source_role"),
            "design_principle": course.get("design_principle"),
            "narration_wpm": course.get("narration_wpm", 130),
            "target_video_minutes": course.get("target_video_minutes", 6),
            "target_total_minutes": course.get("target_total_minutes"),
            "max_slides": course.get("max_slides", 7),
            "editorial_policy": course.get("editorial_policy", []),
        },
        "planning_policy": {
            "max_videos": int(global_cfg.get("max_videos", 30)),
            "prefer_semantic_boundaries_over_document_section_boundaries": True,
            "allow_noncontiguous_supporting_blocks": True,
            "preserve_worked_examples_as_reasoning_units": True,
            "avoid_redundant_reteaching": True,
            "require_source_provenance": True,
        },
        "whole_document_blocks": packet,
    }


def validate_global_plan(plan: dict, extraction: dict) -> list[dict[str, Any]]:
    valid_ids = {str(b.get("id")) for b in extraction.get("blocks", [])}
    issues: list[dict[str, Any]] = []
    videos = plan.get("videos", [])
    seen_video_ids: set[str] = set()
    assigned_core: list[str] = []

    if not videos:
        issues.append({"severity": "error", "message": "Global plan contains no videos."})
        return issues

    for video in videos:
        video_id = str(video.get("id", ""))
        if not video_id:
            issues.append({"severity": "error", "message": "A planned video has no id."})
        elif video_id in seen_video_ids:
            issues.append({"severity": "error", "video_id": video_id, "message": "Duplicate video id."})
        seen_video_ids.add(video_id)

        core = [str(x) for x in video.get("core_block_ids", [])]
        refs = [str(x) for x in video.get("reference_block_ids", [])]
        if not core:
            issues.append({"severity": "error", "video_id": video_id, "message": "Video has no authoritative core blocks."})
        invalid = [x for x in core + refs if x not in valid_ids]
        if invalid:
            issues.append(
                {
                    "severity": "error",
                    "video_id": video_id,
                    "message": f"Plan cites source block IDs absent from the extraction: {invalid}",
                }
            )
        assigned_core.extend(core)

    duplicates = sorted({x for x in assigned_core if assigned_core.count(x) > 1})
    if duplicates:
        issues.append(
            {
                "severity": "warning",
                "message": "Some blocks are assigned as core to multiple videos; verify that repetition is pedagogically intentional.",
                "block_ids": duplicates,
            }
        )

    substantive_kinds = {"paragraph", "equation", "table", "key_idea", "worked_example_heading"}
    substantive = {
        str(b.get("id"))
        for b in extraction.get("blocks", [])
        if b.get("kind") in substantive_kinds and str(b.get("text", "")).strip()
    }
    all_assigned = {
        str(x)
        for v in videos
        for key in ("core_block_ids", "reference_block_ids")
        for x in v.get(key, [])
    }
    unassigned = sorted(substantive - all_assigned)
    if unassigned:
        issues.append(
            {
                "severity": "warning",
                "message": "Substantive source blocks remain unassigned; this may be deliberate reference-only detail, but must be reviewed.",
                "block_ids": unassigned,
            }
        )
    return issues


def _normalize_plan(
    generated: dict,
    extraction: dict,
    profile: dict,
    provider: JSONLLMProvider,
    passes: int,
) -> dict:
    issues = validate_global_plan(generated, extraction)
    errors = [x for x in issues if x.get("severity") == "error"]
    if errors:
        raise LLMError(f"Gemini global course plan failed deterministic validation: {errors}")

    course = profile.get("course", {})
    normalized = dict(generated)
    normalized.update(
        {
            "schema_version": 1,
            "design_mode": "global_llm",
            "course_id": course.get("id"),
            "course_title": course.get("title"),
            "source_signature": extraction_signature(extraction),
            "generation": {
                "provider": provider.provider_name,
                "model": provider.model,
                "passes": passes,
                "prompt_set": "global_design_v1",
            },
            "deterministic_findings": issues,
        }
    )
    return normalized


def build_global_course_plan(
    extraction: dict,
    profile: dict,
    provider: JSONLLMProvider,
    *,
    review_pass: bool = True,
) -> dict:
    context = _planning_context(extraction, profile)
    max_videos = int(context["planning_policy"]["max_videos"])
    schema = global_course_plan_schema(max_videos=max_videos)
    prompt = "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("global_course_planning.md"),
            "## COMPLETE STRUCTURED SOURCE DOCUMENT\n```json\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )
    first_raw = provider.generate_json(prompt, schema)
    first = _normalize_plan(first_raw, extraction, profile, provider, passes=1)
    if not review_pass:
        return first

    review_prompt = "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("global_course_plan_review.md"),
            "## COMPLETE STRUCTURED SOURCE DOCUMENT\n```json\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
            + "\n```",
            "## FIRST GLOBAL COURSE PLAN\n```json\n"
            + json.dumps(first_raw, ensure_ascii=False, indent=2)
            + "\n```",
            "## LOCAL PLAN QA FINDINGS\n```json\n"
            + json.dumps(first.get("deterministic_findings", []), ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )
    revised_raw = provider.generate_json(review_prompt, schema)
    return _normalize_plan(revised_raw, extraction, profile, provider, passes=2)


def write_global_course_plan(plan: dict, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output
