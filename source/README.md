# Local runtime source directory

Place working or private source documents here if convenient. Files such as `source/*.docx` and `source/*.pdf` are ignored by Git.

The repository's tracked demonstration document is intentionally separate at:

```text
examples/sample_docs/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

That tracked file is a sample/reference only. The package never uses it implicitly. Every build requires an explicit `--source` path.
