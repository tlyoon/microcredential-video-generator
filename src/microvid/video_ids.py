from __future__ import annotations

import re

_CANONICAL_VIDEO_ID_RE = re.compile(r"^V(?:0[1-9]|[1-9]\d*)$")


def canonical_video_id(number: int) -> str:
    number = int(number)
    if number < 1:
        raise ValueError("Video numbers must start at 1.")
    return f"V{number:02d}"


def is_canonical_video_id(value: object) -> bool:
    return bool(_CANONICAL_VIDEO_ID_RE.fullmatch(str(value or "").strip().upper()))


def parse_canonical_video_id(value: object) -> int:
    text = str(value or "").strip().upper()
    if not is_canonical_video_id(text):
        raise ValueError(
            f"Invalid video id {value!r}; expected canonical sequential form such as V01, V02, or V10."
        )
    return int(text[1:])
