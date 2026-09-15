from __future__ import annotations

import json
from pathlib import Path

from .docx_parser import extract_docx
from .pdf_parser import extract_pdf
from .source_selection import resolve_source_path
from .textbook_figures import extract_textbook_figure_assets
from .textbook_ingestion import prepare_pdf_extraction

_SUPPORTED_SUFFIXES = {".docx", ".pdf"}


def _extract_source_with_raw(
    path: str | Path, parser_config: dict | None = None
) -> tuple[dict, dict | None]:
    source = resolve_source_path(path)
    suffix = source.suffix.lower()
    if suffix == ".docx":
        payload = extract_docx(source, parser_config=parser_config)
        payload.setdefault("source_format", "docx")
        payload["source_classification"] = {
            "kind": "structured_document",
            "confidence": 1.0,
            "reasons": ["DOCX sources use the structured-document ingestion path."],
            "automatic": True,
        }
        return payload, None
    if suffix == ".pdf":
        raw = extract_pdf(source, parser_config=parser_config)
        payload = prepare_pdf_extraction(raw)
        scope = payload.get("textbook_subchapter_ingestion") or {}
        if (payload.get("source_classification") or {}).get("kind") == "textbook_subchapter" and scope.get("requires_review"):
            raise ValueError(
                "Textbook-like PDF detected, but the intended subchapter boundary could not be determined safely: "
                f"{scope.get('reason')}. Provide a cleaner subchapter cut before video generation."
            )
        return payload, raw
    supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
    raise ValueError(
        f"Unsupported source format '{source.suffix or '<none>'}'. Supported formats: {supported}"
    )


def extract_source(path: str | Path, parser_config: dict | None = None) -> dict:
    """Extract a supported source document into the common semantic block schema."""
    payload, _ = _extract_source_with_raw(path, parser_config=parser_config)
    return payload


def write_extraction(
    path: str | Path,
    output: str | Path,
    parser_config: dict | None = None,
) -> dict:
    payload, raw = _extract_source_with_raw(path, parser_config=parser_config)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)

    scope = payload.get("textbook_subchapter_ingestion")
    if raw is not None and isinstance(scope, dict) and scope.get("applied"):
        figures_dir = destination.parent / "figures"
        payload["figure_assets"] = extract_textbook_figure_assets(
            payload.get("source", path), payload, figures_dir
        )
    else:
        payload.setdefault("figure_assets", [])

    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if raw is not None and isinstance(scope, dict) and scope.get("applied"):
        raw_path = destination.parent / "document_structure_raw.json"
        raw_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        scope_path = destination.parent / "source_scope.json"
        scope_payload = {
            "source": payload.get("source"),
            "source_classification": payload.get("source_classification"),
            "textbook_subchapter_ingestion": scope,
        }
        scope_path.write_text(
            json.dumps(scope_payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return payload
