# Microcredential Video Generator

A reusable Python pipeline for converting a structured `.docx` teaching document into short microcredential-style learning assets:

- semantic DOCX extraction with source provenance;
- course/lesson sectioning driven by YAML profiles;
- semantic heading-path selectors that are independent of page numbers and resilient to section renumbering;
- automatic starter-profile scaffolding for a new document/topic;
- slide-level lesson manifests;
- lecture notes and per-slide narration drafts;
- PowerPoint decks;
- subtitle (`.srt`) files;
- validation reports and profile-drift detection;
- optional local slide rendering, TTS and MP4 assembly hooks.

The bundled course profile is **Physics Laboratory 101**, designed for nine approximately 5–8 minute videos.

## Important distinction: sample source vs runtime source

The repository intentionally contains a sample copy of the corrected Lab 101 manual at:

```text
examples/sample_docs/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

That file is **reference/sample data only**. The Python package never locates it automatically and never uses it as a fallback. Every build requires an explicit runtime source:

```powershell
microvid all --source "C:\path\to\your\actual.docx" --workspace ".\workspace\course"
```

Production source documents may be placed under the local `source/` directory, which remains ignored by Git.

## Design principle

```text
Explicit DOCX source -> extracted semantic structure -> course profile -> lesson manifests
                    -> slides / notes / narration -> media
```

The DOCX is the authoritative content source. The intermediate YAML lesson manifest is the production source of truth for media generation.

## What is soft-coded in v0.2

The engine does **not** depend on Word page numbers. Page count and pagination can change freely.

Document structure is represented by:

- heading level;
- optional numeric section identifier;
- semantic heading breadcrumb (`heading_path`);
- block type (heading, paragraph, equation, table, worked-example marker, etc.);
- source order and provenance.

Profiles can select source material semantically, for example:

```yaml
core_selectors:
  - heading_contains: "Propagation of uncertainty"
```

rather than by a fixed section number such as `8.*`. Therefore renumbering the same topic does not break the Lab 101 profile.

Supported selector fields include:

```yaml
section: "8.*"                  # backward compatible
heading: "Exact heading"
heading_contains: "partial heading"
heading_regex: "regex"
path_regex: "regex over breadcrumb"
kind: [equation, table]
text_regex: "regex over block text"
```

Domain-specific ranking terms are profile data. Physics-specific terms are not hard-coded in the generic manifest engine.

## Using a completely different DOCX/topic

For a new topic with a similar Word structure (headings, paragraphs, tables, equations), no Python changes should be required. First scaffold an editable profile:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

Review/edit the generated YAML, then build:

```powershell
microvid all `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --profile ".\profiles\heat_transfer.yaml"
```

## Installation

Windows PowerShell:

```powershell
.\scripts\setup-local.ps1
```

Or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Lab 101 build

```powershell
microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101"
```

To build one lesson:

```powershell
microvid build `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101" `
  --video V05
```

## Editorial safety gate

Generated lesson manifests start as:

```yaml
editorial_status: draft_requires_review
```

Media rendering refuses draft manifests unless explicitly overridden. After scientific and narration review, change the manifest to:

```yaml
editorial_status: approved
```

This keeps automation from silently converting a draft into a publication-ready teaching video.

## Expected outputs

A course build creates a workspace with extracted structure, manifests, lecture-note/narration assets, PowerPoint decks, subtitles, and QA reports. Optional local media hooks can render slides, synthesize narration, and assemble MP4 files when the relevant desktop software is available.

## Version

Current package version: **0.2.0**.
