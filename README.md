# Microcredential Video Generator

A reusable Python pipeline that converts a structured teaching `.docx` into short narrated microcredential videos using LLM-authored slide abstraction, PowerPoint generation, configurable text-to-speech, and FFmpeg assembly.

**Recommended GitHub repository name:** `microcredential-video-generator`  
**Current package version:** `0.5.0`  
**CLI command:** `microvid`

Physics Laboratory 101 is the bundled reference implementation and sample course profile. The engine itself is topic-neutral.

## Start here

- [Complete user manual](docs/USER_MANUAL.md)
- [Architecture and genericity contract](docs/ARCHITECTURE.md)
- [Configuration reference](docs/CONFIGURATION_REFERENCE.md)
- [Google Cloud Chirp 3 HD TTS guide](docs/CHIRP_TTS.md)
- [Physics Lab 101 pilot workflow](docs/PILOT_WORKFLOW.md)
- [Repository rename migration](docs/REPOSITORY_RENAME.md)
- [Changelog](CHANGELOG.md)

## Production architecture

```text
Explicit runtime DOCX
   -> semantic extraction + source provenance
   -> profile-driven lesson source packets
   -> Google Gemini lesson abstraction by default
   -> grounded LLM review/revision
   -> structured slide manifests
      - concise on-screen content
      - full narration per slide
      - lecturer notes
      - visual/build directions
      - equations and source block IDs
   -> PowerPoint decks with speaker notes
   -> narration / notes / subtitle assets
   -> scientific-speech normalization
   -> Google Cloud Chirp 3 HD TTS by default
   -> rendered slide + audio segments
   -> FFmpeg
   -> MP4
```

## Source document policy

The runtime source is always explicit:

```powershell
microvid all `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile my_course
```

The tracked Lab 101 document under `examples/sample_docs/` is sample/reference data only. It is never selected automatically and is never a hidden fallback.

The parser is pagination-independent. It works from Word structure, heading paths, block type, source order, tables, paragraphs, and Office Math provenance rather than rendered page numbers.

## LLM authoring

LLM generation is the normal content-authoring path. The bundled provider is Google Gemini through the official `google-genai` SDK. Provider/model settings are profile data rather than hard-coded into the engine.

```yaml
course:
  llm:
    provider: gemini
    model: gemini-flash-latest
    thinking_level: high
    api_key_env: GEMINI_API_KEY
    review_pass: true
```

Set the API key locally:

```powershell
$env:GEMINI_API_KEY = "your-key"
```

A deterministic builder remains available only for offline/debugging work:

```powershell
microvid all ... --generator deterministic
```

## Slide/narration production record

Each slide is represented as one production unit in YAML:

```yaml
id: V05S03
slide_type: worked_example
title: Which measurement dominates?
onscreen:
  - concise visible teaching content
narration: >
  Natural spoken explanation for this exact slide.
lecturer_notes:
  - teaching emphasis
visual_direction: >
  Show the two contributions sequentially.
equation_latex: null
source_block_ids: [b0214, b0215]
estimated_seconds: 70
```

The same narration and production guidance are also written into PowerPoint speaker notes. Standalone narration, lecturer-note, and `.srt` subtitle assets are generated alongside the deck.

## TTS

The production default is Google Cloud Chirp 3 HD with a configurable female British-English voice:

```yaml
tts:
  provider: google_cloud_chirp3
  language_code: en-GB
  voice_name: en-GB-Chirp3-HD-Leda
  audio_encoding: LINEAR16
  speaking_rate: 1.0
  location: global
  normalize_scientific_speech: true
  fallback_provider: sapi
  fallback_on_error: true
```

Windows SAPI is retained as a fallback. Scientific notation is normalized conservatively before synthesis, and slides may provide `tts_text` or local `tts_replacements` when a specific spoken form is required.

Voice audition:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

## Installation

On Windows PowerShell:

```powershell
.\scripts\setup-local.ps1
```

or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,windows]"
```

Run the regression tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Generic use with another topic

For a different structured DOCX, scaffold a profile first:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

Review the generated YAML, then run the same extraction, LLM, PowerPoint, TTS, and MP4 pipeline. Python source changes should not be required for a similarly structured teaching document.

## Editorial gate

Generated manifests are not treated as publication-ready automatically. LLM output begins with a review-required status. Final media generation is blocked until the manifest is explicitly marked:

```yaml
editorial_status: approved
```

This keeps automatic generation separate from scientific/editorial acceptance.

## Repository naming

The software is generic, so the preferred repository slug is `microcredential-video-generator`. Internal documentation uses relative links and the Python package/CLI do not depend on the GitHub repository slug, so renaming the GitHub repository does not change runtime behavior. See [REPOSITORY_RENAME.md](docs/REPOSITORY_RENAME.md) for migration steps.
