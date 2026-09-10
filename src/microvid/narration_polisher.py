from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any

from .llm import JSONLLMProvider, LLMError


def _read_prompt(name: str) -> str:
    return files("microvid").joinpath("prompts", name).read_text(encoding="utf-8")


def narration_polish_schema(slide_ids: list[str]) -> dict[str, Any]:
    if not slide_ids:
        raise LLMError("Cannot polish narration for a lesson with no slides.")
    item = {
        "type": "object",
        "properties": {
            "slide_id": {"type": "string", "enum": slide_ids},
            "narration": {"type": "string"},
            "tts_text": {"type": ["string", "null"]},
        },
        "required": ["slide_id", "narration", "tts_text"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "slides": {
                "type": "array",
                "minItems": len(slide_ids),
                "maxItems": len(slide_ids),
                "items": item,
            }
        },
        "required": ["slides"],
        "additionalProperties": False,
    }


def _prompt_payload(context: dict[str, Any], manifest: dict) -> dict[str, Any]:
    return {
        "narration_wpm": context.get("course", {}).get("narration_wpm", 130),
        "global_course_context": context.get("global_course_context"),
        "lesson": context.get("lesson"),
        "authoritative_core_blocks": context.get("authoritative_core_blocks", []),
        "reference_blocks": context.get("reference_blocks", []),
        "fixed_lesson_manifest": {
            "video_id": manifest.get("video_id"),
            "title": manifest.get("title"),
            "focus": manifest.get("focus"),
            "learning_outcomes": manifest.get("learning_outcomes", []),
            "slides": [
                {
                    "id": slide.get("id"),
                    "slide_type": slide.get("slide_type"),
                    "title": slide.get("title"),
                    "onscreen": slide.get("onscreen", []),
                    "narration": slide.get("narration", ""),
                    "visual_direction": slide.get("visual_direction", ""),
                    "equation_latex": slide.get("equation_latex"),
                    "source_block_ids": slide.get("source_block_ids", []),
                    "estimated_seconds": slide.get("estimated_seconds", 30),
                }
                for slide in manifest.get("slides", [])
            ],
        },
    }


def _compose_prompt(context: dict[str, Any], manifest: dict) -> str:
    payload = _prompt_payload(context, manifest)
    return "\n\n".join(
        [
            _read_prompt("system_microcredential_architect.md"),
            _read_prompt("narration_polish.md"),
            "## FIXED LESSON AND SOURCE CONTEXT\n```json\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n```",
        ]
    )


def narration_quality_findings(manifest: dict, narration_wpm: int = 130) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    raw_math_patterns = [r"\\frac\b", r"\\begin\b", r"\\mathrm\b", r"```", r"\$[^$]+\$"]
    meta_patterns = [r"\bsource[_ ]block", r"\bjson schema\b", r"\binternal prompt\b"]

    for slide in manifest.get("slides", []):
        slide_id = str(slide.get("id", ""))
        narration = str(slide.get("narration", "")).strip()
        words = len(re.findall(r"\b[\w’'-]+\b", narration))
        seconds = max(1, int(slide.get("estimated_seconds", 30)))
        theoretical_capacity = seconds * max(1, narration_wpm) / 60.0

        slide["narration_word_count"] = words
        slide["narration_estimated_spoken_seconds"] = round(words * 60 / max(1, narration_wpm), 1)

        if any(re.search(pattern, narration, flags=re.IGNORECASE) for pattern in raw_math_patterns):
            findings.append(
                {
                    "severity": "error",
                    "slide": slide_id,
                    "message": "Narration contains raw markup/LaTeX unsuitable for polished TTS speech.",
                }
            )
        if any(re.search(pattern, narration, flags=re.IGNORECASE) for pattern in meta_patterns):
            findings.append(
                {
                    "severity": "error",
                    "slide": slide_id,
                    "message": "Narration exposes internal production/provenance language.",
                }
            )
        if words > theoretical_capacity * 0.95:
            findings.append(
                {
                    "severity": "warning",
                    "slide": slide_id,
                    "message": (
                        f"Narration is dense for its timing allocation: {words} words for "
                        f"{seconds} s at {narration_wpm} wpm."
                    ),
                }
            )
    return findings


def polish_lesson_narration(
    manifest: dict,
    context: dict[str, Any],
    provider: JSONLLMProvider,
) -> dict:
    """Run a narration-only Gemini edit while freezing scientific/slide structure."""

    slides = list(manifest.get("slides", []))
    slide_ids = [str(slide.get("id")) for slide in slides]
    if any(not x for x in slide_ids) or len(set(slide_ids)) != len(slide_ids):
        raise LLMError("Narration polish requires unique non-empty slide IDs.")

    response = provider.generate_json(_compose_prompt(context, manifest), narration_polish_schema(slide_ids))
    polished_items = response.get("slides", [])
    by_id: dict[str, dict[str, Any]] = {}
    for item in polished_items:
        slide_id = str(item.get("slide_id", ""))
        if slide_id in by_id:
            raise LLMError(f"Narration polish returned duplicate slide ID {slide_id}.")
        by_id[slide_id] = item

    if set(by_id) != set(slide_ids):
        missing = sorted(set(slide_ids) - set(by_id))
        extra = sorted(set(by_id) - set(slide_ids))
        raise LLMError(
            f"Narration polish must return every existing slide exactly once. Missing={missing}; extra={extra}."
        )

    for slide in slides:
        slide_id = str(slide["id"])
        narration = str(by_id[slide_id].get("narration", "")).strip()
        if not narration:
            raise LLMError(f"Narration polish returned empty narration for {slide_id}.")
        slide["narration"] = narration
        tts_text = by_id[slide_id].get("tts_text")
        if tts_text is None or not str(tts_text).strip():
            slide.pop("tts_text", None)
        else:
            slide["tts_text"] = str(tts_text).strip()

    narration_wpm = int(context.get("course", {}).get("narration_wpm", 130))
    findings = narration_quality_findings(manifest, narration_wpm=narration_wpm)
    errors = [x for x in findings if x.get("severity") == "error"]
    if errors:
        raise LLMError(f"Polished narration failed hard speech-hygiene checks: {errors}")

    manifest["narration_quality_findings"] = findings
    generation = manifest.setdefault("generation", {})
    generation["passes"] = int(generation.get("passes", 0)) + 1
    generation["narration_polish"] = {
        "enabled": True,
        "provider": provider.provider_name,
        "model": provider.model,
        "prompt_set": "narration_polish_v1",
    }
    return manifest
