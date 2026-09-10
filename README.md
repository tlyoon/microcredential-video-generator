# Microcredential Video Generator

A reusable Python pipeline for converting a structured `.docx` teaching document into short microcredential-style narrated videos.

## Production architecture

```text
Explicit source DOCX
   -> semantic extraction + lesson source packets
   -> capable LLM content abstraction (Google Gemini by default)
   -> slide-stack manifest
      - slide title and concise on-screen content
      - full narration script for that slide
      - lecturer notes
      - visual/build directions
      - equations and source provenance
   -> PowerPoint deck with narration embedded in speaker notes
   -> TTS per slide
   -> slide/audio segments
   -> MP4 video
```

The bundled course profile is **Physics Laboratory 101**, designed for nine approximately 5–8 minute videos. The full manual remains the technical reference; the videos teach the reasoning students need to act correctly in the laboratory.

## LLM content generation is the default

Normal `microvid draft` and `microvid all` runs use an LLM. The packaged default provider is Google Gemini and the default model selector is:

```yaml
provider: gemini
model: gemini-flash-latest
thinking_level: high
```

As of September 2026, Google's current generally available latest Flash model is Gemini 3.8 Flash. Using the `gemini-flash-latest` alias allows Google to move the alias to a later Flash generation without requiring a Python-code change. For controlled production runs you may instead pin an exact model in the YAML profile or with `--model`.

The Gemini integration uses the official `google-genai` SDK and structured JSON output. Set the API key locally before generation:

```powershell
$env:GEMINI_API_KEY = "your-key"
```

Then:

```powershell
microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101"
```

By default, each lesson receives **two LLM passes**:

1. lesson architecture/content generation;
2. independent grounded review and complete revision.

Use `--no-review-pass` only when a cheaper/faster first-pass draft is deliberately desired.

A deterministic source-extractive builder is retained only for offline/debug work:

```powershell
microvid all ... --generator deterministic
```

It is not the normal content-authoring mode and is never selected silently when Gemini credentials are missing.

## Carefully separated prompt set

The LLM workflow is governed by version-controlled prompts under `src/microvid/prompts/`:

- `system_microcredential_architect.md` — evidence discipline, micro-learning pedagogy, slide abstraction, narration, visuals, technical integrity and assessment;
- `lesson_generation.md` — first-pass conceptual-spine and slide-stack generation;
- `lesson_review.md` — second-pass scientific grounding, provenance, cognitive-load, narration, duration and assessment revision.

The prompt packet supplies only the source blocks assigned to the lesson plus course/lesson design metadata. Every source-derived slide must return valid `source_block_ids`; invented provenance causes generation to fail rather than being accepted silently.

## Sample source vs runtime source

The repository intentionally contains a sample copy of the corrected Lab 101 manual at:

```text
examples/sample_docs/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

That file is **reference/sample data only**. The package never locates it automatically and never uses it as a fallback. Every build requires an explicit runtime source:

```powershell
microvid all --source "C:\path\to\your\actual.docx" --workspace ".\workspace\course"
```

Production source documents may be placed under the local `source/` directory, which remains ignored by Git.

## Soft-coded document handling

The engine does **not** depend on Word page numbers. Page count and pagination can change freely.

Document structure is represented by heading level, optional numeric section identifier, semantic heading breadcrumb (`heading_path`), block type, source order and provenance. Profiles can select source material semantically, for example:

```yaml
core_selectors:
  - heading_contains: "Propagation of uncertainty"
```

rather than by a fixed section number. Thus ordinary renumbering does not break the profile. Materially renamed/reorganized content is reported as profile drift rather than guessed silently.

Physics-specific ranking terms and all model/provider settings live in YAML profile data rather than in the generic Python engine.

## Completely different DOCX/topic

For a new topic with a similar Word structure, first scaffold a profile:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

Review/edit the generated YAML, then build with that profile. No Python modification should be required.

## Installation

Windows PowerShell:

```powershell
.\scripts\setup-local.ps1
```

Or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,windows]"
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Generated lesson representation

Each slide in the YAML manifest contains a tightly coupled production record such as:

```yaml
id: V05S03
slide_type: worked_example
title: Which measurement dominates?
onscreen:
  - concise visible teaching content
narration: >
  Full natural spoken script for this exact slide.
lecturer_notes:
  - teaching emphasis
  - likely misconception
visual_direction: >
  Show the contributions sequentially and highlight the largest one.
equation_latex: null
source_block_ids: [b0214, b0215]
estimated_seconds: 70
```

The PowerPoint generator also writes the narration, lecturer notes, visual direction and source provenance into the slide's **speaker notes**, while standalone narration/notes/SRT files are generated for media automation and editing.

## Video rendering

The current local media path uses PowerPoint for 16:9 slide rendering, Windows SAPI for TTS, and FFmpeg for MP4 assembly. TTS is downstream from LLM authoring: changing a voice does not regenerate lesson content.

Final media rendering is blocked until the lesson manifest is explicitly approved. LLM output begins as:

```yaml
editorial_status: llm_draft_requires_review
```

After scientific and editorial review, change it to:

```yaml
editorial_status: approved
```

This prevents automatically generated teaching material from being mistaken for a reviewed final lesson.

## Version

Current package version: **0.3.0**.
