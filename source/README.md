# Local runtime source directory

Place working or private source documents here if convenient. Files such as `source/*.docx` and `source/*.pdf` are ignored by Git.

Do not place `.env` or Google Cloud credential JSON files here. Store reusable local credentials in `%LOCALAPPDATA%\Microvid`; the CLI discovers them automatically. The recommended filenames are `.env` and `google_cloud_credentials.json`.

The repository's tracked demonstration document is intentionally separate at:

```text
examples/sample_docs/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

That tracked file is a sample/reference only. The package never uses it implicitly. Every build requires an explicit `--source` path.
