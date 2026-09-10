from __future__ import annotations

import re
from pathlib import Path
import yaml

from .text import clean_text, word_count


def _strip_numbering(text: str) -> str:
    return re.sub(r"^\s*\d+(?:\.\d+)*\.?\s+", "", clean_text(text)).strip()


def _top_level_units(extraction: dict) -> list[dict]:
    units = []; current = None
    for block in extraction.get("blocks", []):
        if block.get("kind") == "heading" and block.get("heading_level") == 1:
            if current: units.append(current)
            current = {"heading": block.get("text", "Untitled section"), "block_ids": [block.get("id")], "words": word_count(block.get("text", ""))}
            continue
        if current is not None:
            current["block_ids"].append(block.get("id")); current["words"] += word_count(block.get("text", ""))
    if current: units.append(current)
    return units


def _pack_units(units, target_source_words, max_source_words):
    if not units: return []
    groups=[]; current=[]; words=0
    for unit in units:
        unit_words=max(1,int(unit.get("words",0)))
        if current and words+unit_words>max_source_words and words>=target_source_words*0.55:
            groups.append(current); current=[]; words=0
        current.append(unit); words+=unit_words
        if words>=target_source_words and words>=max_source_words*0.80:
            groups.append(current); current=[]; words=0
    if current:
        if groups and sum(u["words"] for u in current)<target_source_words*0.35: groups[-1].extend(current)
        else: groups.append(current)
    return groups


def scaffold_profile(extraction: dict, course_id: str, title: str, *, target_video_minutes: float=6.0, narration_wpm: int=130, source_compression_ratio: float=1.9, max_slides: int=7) -> dict:
    units=_top_level_units(extraction)
    target_source_words=max(350,round(target_video_minutes*narration_wpm*source_compression_ratio))
    groups=_pack_units(units,target_source_words,round(target_source_words*1.35))
    videos=[]
    for i,group in enumerate(groups,start=1):
        headings=[u["heading"] for u in group]; clean=[_strip_numbering(h) or h for h in headings]
        lesson_title=clean[0] if len(clean)==1 else f"{clean[0]} + {clean[-1]}"
        videos.append({"id":f"V{i:02d}","title":lesson_title,"focus":f"Core reasoning and applications from: {'; '.join(clean)}.","target_minutes":target_video_minutes,"max_slides":max_slides,"core_selectors":[{"heading_contains":_strip_numbering(h) or h} for h in headings],"reference_selectors":[],"learning_outcomes":["Explain the central ideas in this lesson using the source document.","Apply the relevant reasoning to an appropriate example or decision."],"check_question":"What is the most important conclusion or decision supported by this lesson?"})
    return {"course":{"id":course_id,"title":title,"audience":"Configure for the intended learners.","source_role":"The explicitly supplied DOCX is the authoritative content source.","design_principle":"Video teaches the reasoning; the source document carries the detail.","narration_wpm":narration_wpm,"max_slides":max_slides,"target_video_minutes":target_video_minutes,"target_total_minutes":round(len(videos)*target_video_minutes,1),"profile_status":"scaffold_requires_editorial_review","llm":{"provider":"gemini","model":"gemini-flash-latest","thinking_level":"high","api_key_env":"GEMINI_API_KEY","review_pass":True,"max_source_characters_per_lesson":220000,"prompt_set":"microcredential_v2"},"content_selection":{"priority_terms":[],"kind_scores":{"key_idea":7,"worked_example_heading":7,"table":6,"equation":5,"heading":1},"source_words_per_slide":110,"max_context_blocks":6}},"parser":{"heading_style_patterns":[r"^Heading\s*(\d+)$"],"section_number_regex":r"^(\d+(?:\.\d+)*)\.?\s+","key_idea_patterns":[r"^key\s+idea\b"],"worked_example_patterns":[r"^worked\s+example\b",r"^example\b"],"contrast_label_patterns":[r"^poor:?$",r"^better:?$",r"^weak:?$"]},"videos":videos}


def write_scaffold_profile(extraction: dict, output: str | Path, **kwargs) -> Path:
    profile=scaffold_profile(extraction,**kwargs); output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(yaml.safe_dump(profile,sort_keys=False,allow_unicode=True),encoding="utf-8"); return output
