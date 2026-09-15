from __future__ import annotations

import json
from pathlib import Path

from .docx_parser import extract_docx
from .pdf_parser import extract_pdf

_SUPPORTED_SUFFIXES = {".docx", ".pdf"}


def extract_source(path: str | Path, parser_config: dict | None = None) -> dict:
    """Extract a supported source document into the common semantic block schema."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Source document not found: {source}")
    suffix = source.suffix.lower()
    if suffix == ".docx":
        payload = extract_docx(source, parser_config=parser_config)
        payload.setdefault("source_format", "docx")
        return payload
    if suffix == ".pdf":
        return extract_pdf(source, parser_config=parser_config)
    supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
    raise ValueError(f"Unsupported source format '{source.suffix or '<none>'}'. Supported formats: {supported}")


def write_extraction(
    path: str | Path,
    output: str | Path,
    parser_config: dict | None = None,
) -> dict:
    payload = extract_source(path, parser_config=parser_config)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
