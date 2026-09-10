from __future__ import annotations

from pathlib import Path

import yaml


def scaffold_profile(
    extraction: dict,
    course_id: str,
    title: str,
    *,
    target_video_minutes: float = 6.0,
    narration_wpm: int = 130,
    source_compression_ratio: float = 1.9,
    max_slides: int = 7,
) -> dict:
    """Create a topic-neutral constraint profile for global Gemini course design.

    Earlier releases locally pre-segmented Heading-1 units into tentative videos. That is no
    longer the production default: the whole extracted document is now given to Gemini first,
    and Gemini decides the video boundaries after global comprehension. The
    source_compression_ratio argument is retained for CLI/API compatibility but is not used by
    the global-first scaffold.
    """
    _ = extraction, source_compression_ratio
    return {
        "course": {
            "id": course_id,
            "title": title,
            "audience": "Configure for the intended learners.",
            "source_role": "The explicitly supplied DOCX is the authoritative content source.",
            "design_principle": "Video teaches the reasoning; the source document carries the detail.",
            "narration_wpm": narration_wpm,
            "max_slides": max_slides,
            "target_video_minutes": target_video_minutes,
            "target_total_minutes": None,
            "profile_status": "global_design_constraints_require_editorial_review",
            "llm": {
                "provider": "gemini",
                "model": "gemini-flash-latest",
                "thinking_level": "high",
                "api_key_env": "GEMINI_API_KEY",
                "review_pass": True,
                "narration_polish_pass": True,
                "max_source_characters_per_lesson": 220000,
                "prompt_set": "global_design_v1+microcredential_v3+narration_polish_v1",
                "global_design": {
                    "enabled": True,
                    "max_source_characters": 800000,
                    "max_videos": 30,
                    "plan_review_pass": True,
                    "course_consistency_review": True,
                },
            },
            "content_selection": {
                "priority_terms": [],
                "kind_scores": {
                    "key_idea": 7,
                    "worked_example_heading": 7,
                    "table": 6,
                    "equation": 5,
                    "heading": 1,
                },
                "source_words_per_slide": 110,
                "max_context_blocks": 6,
            },
        },
        "parser": {
            "heading_style_patterns": [r"^Heading\s*(\d+)$"],
            "use_outline_level": True,
            "infer_numbered_headings": False,
            "section_number_regex": r"^(\d+(?:\.\d+)*)\.?\s+",
            "key_idea_patterns": [r"^key\s+idea\b"],
            "worked_example_patterns": [r"^worked\s+example\b", r"^example\b"],
            "contrast_label_patterns": [r"^poor:?$", r"^better:?$", r"^weak:?$"],
        },
        "videos": [],
    }


def write_scaffold_profile(extraction: dict, output: str | Path, **kwargs) -> Path:
    profile = scaffold_profile(extraction, **kwargs)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return output
