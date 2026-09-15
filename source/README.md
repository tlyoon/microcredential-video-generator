# Local runtime source directory

Place working or private source documents here if convenient. `microvid --source` accepts `.docx` and text-readable `.pdf` files. Files such as `source/*.docx` and `source/*.pdf` are ignored by Git.

Do not place `.env` or Google Cloud credential JSON files here. Store reusable local credentials in `%LOCALAPPDATA%\Microvid`; the CLI discovers them automatically. The recommended filenames are `.env` and `google_cloud_credentials.json`.

The repository's tracked demonstration document is intentionally separate at:

```text
examples/sample_docs/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

That tracked file is a sample/reference only. The package never uses it implicitly. Every build requires an explicit `--source` path.

PDF notes:

- PDFs are parsed locally with PyMuPDF; they are not converted to DOCX first.
- Repeated page headers/footers and page-number labels are filtered where possible.
- Page numbers are preserved as source provenance, but lesson selection remains semantic.
- Image-only/scanned PDFs fail visibly; OCR is not invoked automatically.
- Embedded figures/images are not yet sent to Gemini as multimodal source material.
