from __future__ import annotations

from pathlib import Path
from typing import Iterable
import yaml

from .models import SlideDraft
from .segmenter import lesson_blocks
from .text import clean_text, sentences, shorten, word_count

def _content_blocks(blocks: Iterable[dict], course: dict) -> list[dict]:
    skip_headings = {str(x).casefold() for x in _selection_config(course).get("skip_headings", ["table of contents"])}
    out = []
    for b in blocks:
        text = clean_text(b.get("text", ""))
        if not text:
            continue
        if b.get("kind") == "heading" and text.casefold() in skip_headings:
            continue
        out.append(b)
    return out


def _selection_config(course: dict) -> dict:
    return course.get("content_selection", {}) or {}


def _score_block(block: dict, course: dict) -> int:
    text = block.get("text", "").lower()
    kind = block.get("kind")
    cfg = _selection_config(course)
    kind_scores = {
        "key_idea": 7,
        "worked_example_heading": 7,
        "table": 7,
        "equation": 5,
        "heading": 1,
    }
    kind_scores.update({str(k): int(v) for k, v in (cfg.get("kind_scores") or {}).items()})
    score = int(kind_scores.get(kind, 0))

    # Domain terms are profile data, not engine code. A generic profile can leave this empty.
    for term in cfg.get("priority_terms", []):
        if str(term).lower() in text:
            score += int(cfg.get("priority_term_score", 2))

    min_len = int(cfg.get("preferred_min_chars", 40))
    max_len = int(cfg.get("preferred_max_chars", 500))
    if min_len <= len(text) <= max_len:
        score += int(cfg.get("preferred_length_score", 2))
    return score


def _pick_source_groups(blocks: list[dict], desired: int, course: dict) -> list[list[dict]]:
    ordered = _content_blocks(blocks, course)
    if not ordered:
        return []
    candidates = [b for b in ordered if b.get("kind") != "contrast_label"]
    ranked = sorted(candidates, key=lambda b: (-_score_block(b, course), b.get("source_index") or 0))
    selected = sorted(ranked[: max(1, desired)], key=lambda b: b.get("source_index") or 0)

    cfg = _selection_config(course)
    context_blocks = int(cfg.get("max_context_blocks", 6))
    source_words = int(cfg.get("source_words_per_slide", 110))

    groups: list[list[dict]] = []
    used: set[str] = set()
    for anchor in selected:
        if anchor["id"] in used:
            continue
        anchor_pos = ordered.index(anchor)
        group = [anchor]
        used.add(anchor["id"])
        approx_words = word_count(anchor.get("text", ""))
        anchor_path = anchor.get("metadata", {}).get("heading_path", [])
        # Give a slide enough contiguous source context while remaining inside the same
        # semantic subsection whenever the source document exposes one.
        for nxt in ordered[anchor_pos + 1 : anchor_pos + 1 + context_blocks]:
            if nxt["id"] in used:
                continue
            next_path = nxt.get("metadata", {}).get("heading_path", [])
            if anchor_path and next_path != anchor_path:
                break
            if nxt.get("kind") == "heading" and group:
                break
            group.append(nxt)
            used.add(nxt["id"])
            approx_words += word_count(nxt.get("text", ""))
            if approx_words >= source_words:
                break
        groups.append(group)
        if len(groups) >= desired:
            break
    return groups


def _group_text(group: list[dict]) -> str:
    return " ".join(clean_text(b.get("text", "")) for b in group if clean_text(b.get("text", "")))


def _draft_narration(title: str, group: list[dict], slide_type: str, course: dict) -> str:
    if slide_type == "hook":
        framing = course.get(
            "hook_narration_template",
            "In this micro-lesson, we focus on {title}. The aim is to understand the reasoning well enough to apply it, while the source document remains available for technical detail.",
        )
        return str(framing).format(title=title.lower())
    text = _group_text(group)
    ss = sentences(text)
    max_words = int(course.get("max_draft_narration_words_per_slide", 135))
    if ss:
        draft = " ".join(ss[:6])
        words = draft.split()
        if len(words) > max_words:
            draft = " ".join(words[:max_words]) + "…"
        return draft
    return text


def _onscreen_for(block: dict) -> list[str]:
    text = clean_text(block.get("text", ""))
    if block.get("kind") == "table":
        rows = block.get("metadata", {}).get("rows", [])
        return [" | ".join(r) for r in rows[:4]]
    if block.get("kind") == "equation":
        return [shorten(text, 180)]
    ss = sentences(text)
    if len(ss) >= 2:
        return [shorten(ss[0], 120), shorten(ss[1], 120)]
    return [shorten(text, 180)] if text else []


def _slide_title(block: dict, fallback: str) -> str:
    text = clean_text(block.get("text", ""))
    if block.get("kind") in {"heading", "worked_example_heading"} and text:
        return shorten(text, 78)
    if block.get("kind") == "equation":
        return "Use the relationship from the source"
    ss = sentences(text)
    if ss and len(ss[0]) <= 78:
        return ss[0]
    return fallback


def _estimate_seconds(narration: str, wpm: int, floor: int = 18) -> int:
    words = word_count(narration)
    return max(floor, round(words / max(wpm, 1) * 60 + 6))


def _selector_summary(lesson: dict, key: str, legacy_key: str) -> list:
    if key in lesson:
        return lesson.get(key, [])
    return [str(x) for x in lesson.get(legacy_key, [])]


def build_lesson_manifest(extraction: dict, course: dict, lesson: dict) -> dict:
    core, refs = lesson_blocks(extraction, lesson)
    max_slides = int(lesson.get("max_slides", course.get("max_slides", 7)))
    wpm = int(course.get("narration_wpm", 130))
    content_slots = max(2, max_slides - 3)
    groups = _pick_source_groups(core, content_slots, course)
    slides: list[SlideDraft] = []

    hook_text = {"id": "hook", "kind": "paragraph", "text": lesson.get("hook", lesson["focus"]), "section": None}
    narration = _draft_narration(lesson["title"], [hook_text], "hook", course)
    slides.append(SlideDraft(
        id=f"{lesson['id']}S01", slide_type="hook", title=lesson["title"],
        onscreen=[lesson["focus"]], narration=narration,
        lecturer_notes=["Open with a question, decision or practical motivation; do not read the slide verbatim."],
        source_block_ids=[], source_sections=[], estimated_seconds=_estimate_seconds(narration, wpm, 30)
    ))

    target_seconds = float(lesson.get("target_minutes", course.get("target_video_minutes", 6))) * 60
    fixed_seconds = 30 + 35 + 30
    content_floor = max(45, int((target_seconds - fixed_seconds) / max(len(groups), 1)))

    for idx, group in enumerate(groups, start=2):
        b = group[0]
        stype = "worked_example" if b.get("kind") in {"worked_example_heading", "table"} else "concept"
        title = _slide_title(b, lesson["focus"])
        narration = _draft_narration(title, group, stype, course)
        source_ids = [x["id"] for x in group]
        sections = sorted({str(x.get("section")) for x in group if x.get("section")})
        heading_paths = [x.get("metadata", {}).get("heading_path", []) for x in group]
        notes = [
            "Explain meaning rather than reading equations or bullets word-for-word.",
            "Verify equations, units, names and numerical values against the authoritative source before publication.",
        ]
        if any(x.get("omml") for x in group):
            notes.append("This source group contains Office Math (OMML). Enter/review the production equation in equation_latex before final rendering.")
        slides.append(SlideDraft(
            id=f"{lesson['id']}S{idx:02d}", slide_type=stype, title=title,
            onscreen=_onscreen_for(b), narration=narration,
            lecturer_notes=notes,
            source_block_ids=source_ids,
            source_sections=sections,
            estimated_seconds=_estimate_seconds(narration, wpm, content_floor),
            source_heading_paths=heading_paths,
        ))

    q_num = len(slides) + 1
    q_narr = "Pause here and answer the check before continuing. Explain your choice from the principle developed in this lesson rather than guessing."
    slides.append(SlideDraft(
        id=f"{lesson['id']}S{q_num:02d}", slide_type="check", title="Check your understanding",
        onscreen=[lesson.get("check_question", "What decision or conclusion follows from the ideas in this lesson?")],
        narration=q_narr,
        lecturer_notes=["Allow a short pause before revealing or discussing the answer."],
        source_block_ids=[], source_sections=[], estimated_seconds=35,
    ))

    t_num = len(slides) + 1
    takeaways = lesson.get("takeaways") or [lesson["focus"], "Use the source document for full technical detail."]
    t_narr = "Carry this reasoning into the relevant task. Use the source document as the detailed reference when you need definitions, equations, examples or procedures."
    slides.append(SlideDraft(
        id=f"{lesson['id']}S{t_num:02d}", slide_type="takeaway", title="Takeaway",
        onscreen=takeaways[:3], narration=t_narr,
        lecturer_notes=["End with no more than three memorable points."],
        source_block_ids=[], source_sections=[], estimated_seconds=_estimate_seconds(t_narr, wpm, 30),
    ))

    return {
        "schema_version": 2,
        "video_id": lesson["id"],
        "title": lesson["title"],
        "focus": lesson["focus"],
        "learning_outcomes": lesson.get("learning_outcomes", []),
        "target_minutes": lesson.get("target_minutes", course.get("target_video_minutes", 6)),
        "core_selectors": _selector_summary(lesson, "core_selectors", "core_sections"),
        "reference_selectors": _selector_summary(lesson, "reference_selectors", "reference_sections"),
        "source_core_block_count": len(core),
        "source_reference_block_count": len(refs),
        "source_reference_blocks": [b["id"] for b in refs],
        "editorial_status": "draft_requires_review",
        "slides": [s.to_dict() for s in slides],
    }


def build_all_manifests(extraction: dict, profile: dict, out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    course = profile["course"]
    written = []
    course_index = {"course": course, "videos": []}
    for n, lesson in enumerate(profile["videos"], start=1):
        manifest = build_lesson_manifest(extraction, course, lesson)
        video_number = n
        lesson_id = str(lesson.get("id", f"V{n:02d}"))
        digits = "".join(ch for ch in lesson_id if ch.isdigit())
        if digits:
            video_number = int(digits)
        path = out / f"video_{video_number:02d}.yaml"
        path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        written.append(path)
        course_index["videos"].append({
            "id": lesson_id, "title": lesson["title"], "manifest": path.name,
            "target_minutes": lesson.get("target_minutes", course.get("target_video_minutes", 6)),
        })
    (out / "course.yaml").write_text(yaml.safe_dump(course_index, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return written
