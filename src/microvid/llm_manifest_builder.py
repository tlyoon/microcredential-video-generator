from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

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
        packet.append({
            "id": block.get("id"), "kind": block.get("kind"),
            "section": block.get("section"), "heading_level": block.get("heading_level"),
            "heading_path": meta.get("heading_path", []), "text": block.get("text", ""),
            "math_text": meta.get("math_text", []), "contains_office_math": bool(block.get("omml")),
        })
    return packet


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
        "required": ["slide_type", "title", "onscreen", "narration", "lecturer_notes", "visual_direction", "equation_latex", "source_block_ids", "estimated_seconds"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "lesson_title": {"type": "string"},
            "learning_outcomes": {"type": "array", "items": {"type": "string"}},
            "slides": {"type": "array", "minItems": 4, "maxItems": max_slides, "items": slide_schema},
            "editorial_flags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["lesson_title", "learning_outcomes", "slides", "editorial_flags"],
        "additionalProperties": False,
    }


def _prompt_context(course: dict, lesson: dict, core: list[dict], refs: list[dict]) -> dict[str, Any]:
    return {
        "course": {
            "title": course.get("title"), "audience": course.get("audience"),
            "design_principle": course.get("design_principle"),
            "narration_wpm": course.get("narration_wpm", 130),
            "target_video_minutes": lesson.get("target_minutes", course.get("target_video_minutes", 6)),
            "max_slides": lesson.get("max_slides", course.get("max_slides", 7)),
        },
        "lesson": {
            "id": lesson.get("id"), "title": lesson.get("title"), "focus": lesson.get("focus"),
            "learning_outcomes": lesson.get("learning_outcomes", []),
            "check_question": lesson.get("check_question"), "takeaways": lesson.get("takeaways", []),
        },
        "authoritative_core_blocks": _source_packet(core),
        "reference_blocks": _source_packet(refs),
    }


def _compose_generation_prompt(context: dict[str, Any]) -> str:
    return "\n\n".join([
        _read_prompt("system_microcredential_architect.md"),
        _read_prompt("lesson_generation.md"),
        "## CURRENT LESSON INPUT (machine-readable)\n```json\n" + json.dumps(context, ensure_ascii=False, indent=2) + "\n```",
    ])


def _compose_revision_prompt(context: dict[str, Any], draft: dict[str, Any], issues: list[dict]) -> str:
    return "\n\n".join([
        _read_prompt("system_microcredential_architect.md"), _read_prompt("lesson_review.md"),
        "## CURRENT LESSON INPUT\n```json\n" + json.dumps(context, ensure_ascii=False, indent=2) + "\n```",
        "## FIRST-PASS MANIFEST\n```json\n" + json.dumps(draft, ensure_ascii=False, indent=2) + "\n```",
        "## DETERMINISTIC QA FINDINGS\n```json\n" + json.dumps(issues, ensure_ascii=False, indent=2) + "\n```",
    ])


def _normalize_manifest(generated, extraction, course, lesson, core, refs, provider, *, generation_passes):
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
            raise LLMError(f"LLM returned source block IDs not supplied to the lesson: {invalid}. Generation rejected.")
        source_blocks = [block_by_id[x] for x in ids if x in block_by_id]
        normalized.append({
            "id": f"{lesson['id']}S{i:02d}", "slide_type": slide.get("slide_type"),
            "title": slide.get("title", ""), "onscreen": slide.get("onscreen", []),
            "narration": slide.get("narration", ""), "lecturer_notes": slide.get("lecturer_notes", []),
            "visual_direction": slide.get("visual_direction", ""), "source_block_ids": ids,
            "source_sections": sorted({str(b.get("section")) for b in source_blocks if b.get("section")}),
            "source_heading_paths": [b.get("metadata", {}).get("heading_path", []) for b in source_blocks],
            "estimated_seconds": int(slide.get("estimated_seconds", 30)),
            "equation_latex": slide.get("equation_latex"),
        })
    return {
        "schema_version": 3, "video_id": lesson["id"],
        "title": generated.get("lesson_title") or lesson["title"], "focus": lesson["focus"],
        "learning_outcomes": generated.get("learning_outcomes") or lesson.get("learning_outcomes", []),
        "target_minutes": lesson.get("target_minutes", course.get("target_video_minutes", 6)),
        "source_core_block_count": len(core), "source_reference_block_count": len(refs),
        "source_reference_blocks": [b["id"] for b in refs],
        "editorial_status": "llm_draft_requires_review",
        "editorial_flags": generated.get("editorial_flags", []),
        "generation": {"mode": "llm", "provider": provider.provider_name, "model": provider.model, "passes": generation_passes, "prompt_set": "microcredential_v2"},
        "slides": normalized,
    }


def build_lesson_manifest_with_llm(extraction, course, lesson, provider: JSONLLMProvider, *, review_pass=True):
    core, refs = lesson_blocks(extraction, lesson)
    if not core:
        raise LLMError(f"{lesson.get('id', 'Lesson')} selectors matched zero authoritative source blocks. Review the course profile before invoking the LLM.")
    max_chars = int(course.get("llm", {}).get("max_source_characters_per_lesson", 220_000))
    source_chars = sum(len(str(b.get("text", ""))) for b in core + refs)
    if source_chars > max_chars:
        raise LLMError(f"Lesson source packet is {source_chars:,} characters, above configured limit {max_chars:,}; it will not be truncated silently.")
    max_slides = int(lesson.get("max_slides", course.get("max_slides", 7)))
    schema = lesson_manifest_schema(max_slides)
    context = _prompt_context(course, lesson, core, refs)
    generated = provider.generate_json(_compose_generation_prompt(context), schema)
    first = _normalize_manifest(generated, extraction, course, lesson, core, refs, provider, generation_passes=1)
    if not review_pass:
        return first
    issues = validate_manifest(first)
    revised = provider.generate_json(_compose_revision_prompt(context, first, issues), schema)
    return _normalize_manifest(revised, extraction, course, lesson, core, refs, provider, generation_passes=2)


def build_all_manifests_with_llm(extraction, profile, out_dir: str | Path, provider: JSONLLMProvider, *, review_pass=True):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    course = profile["course"]; written = []; course_index = {"course": course, "videos": []}
    for n, lesson in enumerate(profile["videos"], start=1):
        manifest = build_lesson_manifest_with_llm(extraction, course, lesson, provider, review_pass=review_pass)
        digits = "".join(ch for ch in str(lesson.get("id", f"V{n:02d}")) if ch.isdigit())
        video_number = int(digits) if digits else n
        path = out / f"video_{video_number:02d}.yaml"
        path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        written.append(path)
        course_index["videos"].append({"id": lesson.get("id", f"V{n:02d}"), "title": manifest["title"], "manifest": path.name, "target_minutes": manifest["target_minutes"], "generator": manifest["generation"]})
    (out / "course.yaml").write_text(yaml.safe_dump(course_index, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return written
