from __future__ import annotations

import re


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    t = clean_text(text)
    if not t:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]


def shorten(text: str, limit: int = 150) -> str:
    t = clean_text(text)
    if len(t) <= limit:
        return t
    cut = t[: limit - 1].rsplit(" ", 1)[0]
    return cut + "…"


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+[\w'’-]*\b", text))
