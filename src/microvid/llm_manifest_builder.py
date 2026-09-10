from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from .course_consistency import blocking_findings, review_course_consistency
from .llm import JSONLLMProvider, LLMError
from .qa import validate_manifest
from .segmenter import lesson_blocks

_ALLOWED_SLIDE_TYPES = [
    "hook", "concept", "worked_example", "method", "interpretation", "check", "takeaway"
]


def _read_prompt(name: str) -> str:
    return files("microvid").joinpath("prompts", name).read_text(encoding="utf-8")


def _source_packet(blocks: list[dict]) -> list[dict[str, Any]]:
    packet = []
    for block in blocks:
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


def _blocks_from_ids(extraction: dict, block_ids: list[str]) -> list[dict]:
    wanted = {str(x) for x in block_ids}
    return [b for b in extraction.get("blocks", []) if str(b.get("id")) in wanted]


def _lesson_source_blocks(extraction: dict, lesson: dict) -> tuple[list[dict], list[dict]]:
    """Use global-plan block assignments when available; otherwise use legacy selectors."""
    if "core_block_ids" in lesson:
        core = _blocks_from_ids(extraction, [str(x) for x in lesson.get("core_block_ids", [])])
        core_ids = {str(b.get("id")) for b in core}
        refs = [
            b
            for b in _blocks_from_ids(
                extraction, [str(x) for x in lesson.get("reference_block_ids", [])]
            )
            if str(b.get("id")) not in core_ids
        ]
        return core, refs
    return lesson_blocks(extraction, lesson)


def lesson_manifest_schema(max_slides: int) -> dict[str, Any]:
    slide_schema = {
        "type": "object",
        "properties": {
            "slide_type": {"type": "string", "enum": _ALLOWED_SLIDE_TYPES},
            "title": {"type": "string"},
            "onscreen": {"type": "array", "items": {"type": "string"}},
            "narration": {"type": "string"},
            "lecturer_notes": {"type": "array", "items": {"type": "string"}},
            "visual_direction": {"type": "string"},
            "equation_latex": {"type": ["string", "null"]},
            "source_block_ids": {"type": "array", "items": {"type": "string"}},
            "estimated_seconds": {"type": "integer", "minimum": 10, "maximum": 180},
        },
        "required": [
            "slide_type",
            "title",
            "onscreen",
            "narration",
            "lecturer_notes",
            "visual_direction",
            "equation_latex",
            "source_block_ids",
            "estimated_seconds",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "lesson_title": {"type": "string"},
            "learning_outcomes": {"type": "array", "items": {"type": "string"}},
            "slides": {
                "type": "array",
                "minItems": 4,
                "maxItems": max_slides,
                "items": slide_schema,
            },
            "editorial_flags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["lesson_title", "learning_outcomes", "slides", "editorial_flags"],
        "additionalProperties": False,
    }


def _global_course_context(global_plan: dict | None, lesson_id: str | None) -> dict[str, Any] | None:
    if not global_plan:
        return None
    sequence = []
    current_index = None
    for i, video in enumerate(global_plan.get("videos", [])):
        if str(video.get("id")) == str(lesson_id):
            current_index = i
        sequence.append(
            {
                "id": video.get("id"),
                "title": video.get("title"),
                "focus": video.get("focus"),
                "prerequisite_video_ids": video.get("prerequisite_video_ids", []),
                "already_taught": video.get("already_taught", []),
                "forward_links": video.get("forward_links", []),
            }
        )
    return {
        "course_summary": global_plan.get("course_summary"),
        "pedagogical_strategy": global_plan.get("pedagogical_strategy"),
        "concept_map": global_plan.get("concept_map", []),
        "lesson_sequence": sequence,
        "current_lesson_index_zero_based": current_index,
    }


def _prompt_context(
    course: dict,
    lesson: dict,
    core: list[dict],
    refs: list[dict],
    global_plan: dict | None = None,
) -> dict[str, Any]:
    return {
        "course": {
            "title": course.get("title"),
            "audience": course.get("audience"),
            "design_principle": course.get("design_principle"),
            "narration_wpm": course.get("narration_wpm", 130),
            "target_video_minutes": lesson.get(
                "target_minutes", course.get("target_video_minutes", 6)
            ),
            "max_slides": lesson.get("max_slides", course.get("max_slides", 7)),
        },
        "global_course_context": _global_course_context(global_plan, lesson.get("id")),
        "lesson": {
            "id": lesson.get("id"),
            "title": lesson.get("title"),
            "focus": lesson.get("focus"),
            "learning_outcomes": lesson.get("learning_outcomes", []),
            "check_question": lesson.get("check_question"),
            "takeaways": lesson.get("takeaways", []),
            "prerequisite_video_ids": lesson.get("prerequisite_video_ids", []),
            "already_taught": lesson.get("already_taught", []),
            "forward_links": lesson.get("forward_links", []),
        },
        "authoritative_core_blocks": _source_packet(core),
        "reference_blocks": _source_packet(refs),
    }


def _compose_generation_prompt(context: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("lesson_generation.md"),
            "## CURRENT LESSON INPUT (machine-readable)\n```json\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )


def _compose_revision_prompt(
    context: dict[str, Any], draft: dict[str, Any], issues: list[dict]
) -> str:
    return "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("lesson_review.md"),
            "## CURRENT LESSON INPUT\n```json\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
            + "\n```",
            "## DRAFT MANIFEST\n```json\n"
            + json.dumps(draft, ensure_ascii=False, indent=2)
            + "\n```",
            "## DETERMINISTIC QA FINDINGS\n```json\n"
            + json.dumps(issues, ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )


def _compose_consistency_revision_prompt(
    context: dict[str, Any], draft: dict[str, Any], instructions: list[str]
) -> str:
    return "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("lesson_review.md"),
            "Revise this lesson specifically to satisfy the whole-course consistency review. "
            "Preserve source fidelity and the assigned lesson scope.",
            "## CURRENT LESSON INPUT\n```json\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
            + "\n```",
            "## CURRENT LESSON MANIFEST\n```json\n"
            + json.dumps(draft, ensure_ascii=False, indent=2)
            + "\n```",
            "## WHOLE-COURSE REVISION INSTRUCTIONS\n```json\n"
            + json.dumps(instructions, ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )


def _normalize_manifest(
    generated,
    extraction,
    course,
    lesson,
    core,
    refs,
    provider,
    *,
    generation_passes,
    design_mode: str,
):
    valid_ids = {b["id"] for b in core + refs}
    block_by_id = {b["id"]: b for b in extraction.get("blocks", [])}
    slides = generated.get("slides", [])
    if not isinstance(slides, list):
        raise LLMError("LLM manifest 'slides' must be a list.")
    normalized = []
    for i, slide in enumerate(slides, start=1):
        ids = [str(x) for x in slide.get("source_block_ids", [])]
        invalid = [x for x in ids if x not in valid_ids]
        if invalid:
            raise LLMError(
                f"LLM returned source block IDs not supplied to the lesson: {invalid}. Generation rejected."
            )
        source_blocks = [block_by_id[x] for x in ids if x in block_by_id]
        normalized.append(
            {
                "id": f"{lesson['id']}S{i:02d}",
                "slide_type": slide.get("slide_type"),
                "title": slide.get("title", ""),
                "onscreen": slide.get("onscreen", []),
                "narration": slide.get("narration", ""),
                "lecturer_notes": slide.get("lecturer_notes", []),
                "visual_direction": slide.get("visual_direction", ""),
                "source_block_ids": ids,
                "source_sections": sorted(
                    {str(b.get("section")) for b in source_blocks if b.get("section")}
                ),
                "source_heading_paths": [
                    b.get("metadata", {}).get("heading_path", []) for b in source_blocks
                ],
                "estimated_seconds": int(slide.get("estimated_seconds", 30)),
                "equation_latex": slide.get("equation_latex"),
            }
        )
    return {
        "schema_version": 4,
        "video_id": lesson["id"],
        "title": generated.get("lesson_title") or lesson["title"],
        "focus": lesson["focus"],
        "learning_outcomes": generated.get("learning_outcomes")
        or lesson.get("learning_outcomes", []),
        "target_minutes": lesson.get(
            "target_minutes", course.get("target_video_minutes", 6)
        ),
        "source_core_block_count": len(core),
        "source_reference_block_count": len(refs),
        "source_core_blocks": [b["id"] for b in core],
        "source_reference_blocks": [b["id"] for b in refs],
        "editorial_status": "llm_draft_requires_review",
        "editorial_flags": generated.get("editorial_flags", []),
        "generation": {
            "mode": "llm",
            "design_mode": design_mode,
            "provider": provider.provider_name,
            "model": provider.model,
            "passes": generation_passes,
            "prompt_set": "global_design_v1+microcredential_v2"
            if design_mode == "global_llm"
            else "microcredential_v2",
        },
        "slides": normalized,
    }


def build_lesson_manifest_with_llm(
    extraction,
    course,
    lesson,
    provider: JSONLLMProvider,
    *,
    review_pass=True,
    global_plan: dict | None = None,
):
    core, refs = _lesson_source_blocks(extraction, lesson)
    if not core:
        raise LLMError(
            f"{lesson.get('id', 'Lesson')} matched zero authoritative source blocks. "
            "Review the global course plan or legacy profile before invoking the LLM."
        )
    max_chars = int(course.get("llm", {}).get("max_source_characters_per_lesson", 220_000))
    source_chars = sum(len(str(b.get("text", ""))) for b in core + refs)
    if source_chars > max_chars:
        raise LLMError(
            f"Lesson source packet is {source_chars:,} characters, above configured limit "
            f"{max_chars:,}; it will not be truncated silently."
        )
    max_slides = int(lesson.get("max_slides", course.get("max_slides", 7)))
    schema = lesson_manifest_schema(max_slides)
    context = _prompt_context(course, lesson, core, refs, global_plan)
    design_mode = "global_llm" if global_plan else "profile"
    generated = provider.generate_json(_compose_generation_prompt(context), schema)
    first = _normalize_manifest(
        generated,
        extraction,
        course,
        lesson,
        core,
        refs,
        provider,
        generation_passes=1,
        design_mode=design_mode,
    )
    if not review_pass:
        return first
    issues = validate_manifest(first)
    revised = provider.generate_json(_compose_revision_prompt(context, first, issues), schema)
    return _normalize_manifest(
        revised,
        extraction,
        course,
        lesson,
        core,
        refs,
        provider,
        generation_passes=2,
        design_mode=design_mode,
    )


def _revise_for_course_consistency(
    extraction: dict,
    course: dict,
    lesson: dict,
    manifest: dict,
    provider: JSONLLMProvider,
    global_plan: dict,
    instructions: list[str],
) -> dict:
    core, refs = _lesson_source_blocks(extraction, lesson)
    context = _prompt_context(course, lesson, core, refs, global_plan)
    schema = lesson_manifest_schema(int(lesson.get("max_slides", course.get("max_slides", 7))))
    revised = provider.generate_json(
        _compose_consistency_revision_prompt(context, manifest, instructions), schema
    )
    previous_passes = int(manifest.get("generation", {}).get("passes", 2))
    return _normalize_manifest(
        revised,
        extraction,
        course,
        lesson,
        core,
        refs,
        provider,
        generation_passes=previous_passes + 1,
        design_mode="global_llm",
    )


def _video_number(lesson: dict, n: int) -> int:
    digits = "".join(ch for ch in str(lesson.get("id", f"V{n:02d}")) if ch.isdigit())
    return int(digits) if digits else n


def _write_manifests(out: Path, lessons: list[dict], manifests: list[dict]) -> list[Path]:
    written: list[Path] = []
    for n, (lesson, manifest) in enumerate(zip(lessons, manifests), start=1):
        path = out / f"video_{_video_number(lesson, n):02d}.yaml"
        path.write_text(
            yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        written.append(path)
    return written


def build_all_manifests_with_llm(
    extraction,
    profile,
    out_dir: str | Path,
    provider: JSONLLMProvider,
    *,
    review_pass=True,
    global_plan: dict | None = None,
    course_consistency_review: bool = True,
):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    course = profile["course"]
    lessons = list(global_plan.get("videos", [])) if global_plan else list(profile["videos"])
    manifests = [
        build_lesson_manifest_with_llm(
            extraction,
            course,
            lesson,
            provider,
            review_pass=review_pass,
            global_plan=global_plan,
        )
        for lesson in lessons
    ]

    consistency_status = "not_applicable"
    consistency_report: dict | None = None
    if global_plan and course_consistency_review:
        consistency_report = review_course_consistency(global_plan, manifests, provider)
        (out / "global_consistency_initial.yaml").write_text(
            yaml.safe_dump(consistency_report, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        instructions = {
            str(item.get("video_id")): list(item.get("instructions", []))
            for item in consistency_report.get("lesson_revision_instructions", [])
        }
        if instructions:
            revised_manifests = []
            for lesson, manifest in zip(lessons, manifests):
                video_id = str(lesson.get("id"))
                if video_id in instructions:
                    manifest = _revise_for_course_consistency(
                        extraction,
                        course,
                        lesson,
                        manifest,
                        provider,
                        global_plan,
                        instructions[video_id],
                    )
                revised_manifests.append(manifest)
            manifests = revised_manifests
            consistency_report = review_course_consistency(
                global_plan, manifests, provider, verification=True
            )
        (out / "global_consistency_final.yaml").write_text(
            yaml.safe_dump(consistency_report, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        consistency_status = str(consistency_report.get("status", "revision_required"))

    written = _write_manifests(out, lessons, manifests)
    course_index = {
        "course": course,
        "design_mode": "global_llm" if global_plan else "profile",
        "global_course_summary": global_plan.get("course_summary") if global_plan else None,
        "global_consistency_status": consistency_status,
        "videos": [],
    }
    for lesson, manifest, path in zip(lessons, manifests, written):
        course_index["videos"].append(
            {
                "id": lesson.get("id"),
                "title": manifest["title"],
                "manifest": path.name,
                "target_minutes": manifest["target_minutes"],
                "generator": manifest["generation"],
            }
        )
    (out / "course.yaml").write_text(
        yaml.safe_dump(course_index, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    if global_plan and course_consistency_review and (
        consistency_status != "ready" or blocking_findings(consistency_report or {})
    ):
        raise LLMError(
            "Whole-course consistency review still has blocking issues after the allowed targeted "
            "revision pass. Draft manifests and the review report were saved; resolve the findings "
            "before slide/media production."
        )
    return written
