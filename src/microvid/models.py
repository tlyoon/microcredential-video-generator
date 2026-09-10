from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Block:
    id: str
    kind: str
    text: str
    section: str | None = None
    heading_level: int | None = None
    style: str | None = None
    source_index: int | None = None
    omml: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SlideDraft:
    id: str
    slide_type: str
    title: str
    onscreen: list[str]
    narration: str
    lecturer_notes: list[str]
    source_block_ids: list[str]
    source_sections: list[str]
    estimated_seconds: int
    equation_latex: str | None = None
    source_heading_paths: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
