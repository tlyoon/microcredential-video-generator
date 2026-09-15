from __future__ import annotations

import warnings
from pathlib import Path

_SUPPORTED_SUFFIXES = {".docx", ".pdf"}


def _source_sort_key(path: Path) -> tuple[int, str]:
    """Prefer the conventional source.pdf name, then deterministic filename order."""
    return (0 if path.name.casefold() == "source.pdf" else 1, path.name.casefold())


def resolve_source_path(path: str | Path) -> Path:
    """Resolve an explicit source file or choose a source from a directory.

    Directory mode is intentionally conservative. PDFs take precedence because the
    textbook-subchapter workflow is PDF-specific. If more than one PDF is present,
    a visible warning is emitted and the first PDF in deterministic order is used.
    """
    source = Path(path)
    if source.is_file():
        if source.suffix.lower() not in _SUPPORTED_SUFFIXES:
            supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
            raise ValueError(
                f"Unsupported source format '{source.suffix or '<none>'}'. Supported formats: {supported}"
            )
        return source
    if not source.is_dir():
        raise FileNotFoundError(f"Source document or directory not found: {source}")

    pdfs = sorted(
        (p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
        key=_source_sort_key,
    )
    docxs = sorted(
        (p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".docx"),
        key=_source_sort_key,
    )

    if pdfs:
        chosen = pdfs[0]
        if len(pdfs) > 1:
            warnings.warn(
                "Multiple PDF source files were found in "
                f"'{source}'. Choosing '{chosen.name}' by default. "
                "Pass an explicit --source file path to select another PDF.",
                UserWarning,
                stacklevel=2,
            )
        if docxs:
            warnings.warn(
                f"Both PDF and DOCX source files were found in '{source}'. "
                f"PDF selection takes precedence; using '{chosen.name}'.",
                UserWarning,
                stacklevel=2,
            )
        return chosen

    if docxs:
        chosen = docxs[0]
        if len(docxs) > 1:
            warnings.warn(
                "Multiple DOCX source files were found in "
                f"'{source}'. Choosing '{chosen.name}' by default. "
                "Pass an explicit --source file path to select another DOCX.",
                UserWarning,
                stacklevel=2,
            )
        return chosen

    raise FileNotFoundError(
        f"No supported .pdf or .docx source files were found in directory: {source}"
    )
