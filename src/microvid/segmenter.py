from __future__ import annotations

import re
from typing import Any


def section_matches(section: str | None, selectors: list[str]) -> bool:
    if not section:
        return False
    for selector in selectors:
        selector = str(selector)
        if selector.endswith(".*"):
            root = selector[:-2]
            if section == root or section.startswith(root + "."):
                return True
        elif section == selector:
            return True
    return False


def _heading_path(block: dict) -> list[str]:
    return [str(x) for x in block.get("metadata", {}).get("heading_path", [])]


def selector_matches(block: dict, selector: Any) -> bool:
    """Match a block using a backward-compatible string or a semantic selector dict.

    Supported dict keys are ANDed together. Useful keys:
      section: "8.*"
      heading: exact current/ancestor heading text
      heading_contains: substring in any heading in the path
      heading_regex: regex against any heading in the path
      path_regex: regex against the complete ' > '-joined heading breadcrumb
      kind: block kind, or a list of kinds
      text_regex: regex against block text
    """
    if isinstance(selector, str):
        return section_matches(block.get("section"), [selector])
    if not isinstance(selector, dict):
        return False

    path = _heading_path(block)
    path_joined = " > ".join(path)

    if "section" in selector and not section_matches(block.get("section"), [str(selector["section"])]):
        return False
    if "heading" in selector:
        target = str(selector["heading"]).casefold()
        if not any(h.casefold() == target for h in path):
            return False
    if "heading_contains" in selector:
        target = str(selector["heading_contains"]).casefold()
        if not any(target in h.casefold() for h in path):
            return False
    if "heading_regex" in selector:
        pattern = re.compile(str(selector["heading_regex"]), re.IGNORECASE)
        if not any(pattern.search(h) for h in path):
            return False
    if "path_regex" in selector:
        if not re.search(str(selector["path_regex"]), path_joined, flags=re.IGNORECASE):
            return False
    if "kind" in selector:
        kinds = selector["kind"] if isinstance(selector["kind"], list) else [selector["kind"]]
        if block.get("kind") not in {str(x) for x in kinds}:
            return False
    if "text_regex" in selector:
        if not re.search(str(selector["text_regex"]), block.get("text", ""), flags=re.IGNORECASE):
            return False
    return True


def any_selector_matches(block: dict, selectors: list[Any]) -> bool:
    return any(selector_matches(block, s) for s in selectors)


def _lesson_selectors(lesson: dict, key: str, legacy_key: str) -> list[Any]:
    if key in lesson:
        return list(lesson.get(key) or [])
    return [str(x) for x in lesson.get(legacy_key, [])]


def lesson_blocks(extraction: dict, lesson: dict) -> tuple[list[dict], list[dict]]:
    core_selectors = _lesson_selectors(lesson, "core_selectors", "core_sections")
    ref_selectors = _lesson_selectors(lesson, "reference_selectors", "reference_sections")
    core, reference = [], []
    for block in extraction["blocks"]:
        if any_selector_matches(block, core_selectors):
            core.append(block)
        elif any_selector_matches(block, ref_selectors):
            reference.append(block)
    return core, reference
