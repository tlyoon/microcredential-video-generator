# Microcredential Video Generator

A reusable Python pipeline that converts a structured teaching `.docx` into short narrated microcredential videos using whole-document Gemini course design, LLM-authored slide content, dedicated narration polishing, PowerPoint, configurable TTS, and FFmpeg assembly.

**Repository:** `tlyoon/microcredential-video-generator`  
**Current package version:** `0.7.0`  
**CLI command:** `microvid`

Physics Laboratory 101 is the bundled reference implementation and sample course profile. The engine itself is topic-neutral.

## Start here

- [Complete user manual](docs/USER_MANUAL.md)
- [Global-first design](docs/GLOBAL_DESIGN.md)
- [Narration quality and dedicated script polishing](docs/NARRATION_QUALITY.md)
- [Architecture and genericity contract](docs/ARCHITECTURE.md)
- [Configuration reference](docs/CONFIGURATION_REFERENCE.md)
- [Google Cloud Chirp 3 HD TTS guide](docs/CHIRP_TTS.md)
- [Physics Lab 101 pilot workflow](docs/PILOT_WORKFLOW.md)
- [Changelog](CHANGELOG.md)

## Production architecture

The production default is **global-first**. Gemini sees the complete structured source document before any video boundaries or slide decks are created. Narration is subsequently treated as a separate editorial artifact rather than accepting the first script produced during slide design.

```text
Explicit runtime DOCX
   -> LOCAL semantic extraction + provenance
   -> GEMINI whole-document comprehension + course segmentation
   -> LOCAL validation of global plan/source IDs
   -> GEMINI global-plan review/revision
   -> global course map + video block assignments
   -> for each video:
        global map + sequence context + assigned source blocks
        -> GEMINI slide stack + first narration
        -> LOCAL deterministic lesson QA
        -> GEMINI grounded scientific/pedagogical lesson review
        -> GEMINI dedicated narration-only polish
        -> LOCAL narration speech/timing QA
   -> GEMINI whole-course consistency review
        -> targeted lesson revisions if needed
        -> narration is polished again for any revised lesson
        -> final consistency verification
   -> LOCAL YAML manifests
   -> LOCAL PowerPoint decks + speaker notes
   -> LOCAL narration / notes / subtitle assets
   -> LOCAL scientific-speech normalization
   -> Google Cloud Chirp 3 HD TTS by default
   -> LOCAL PowerPoint rendering + FFmpeg
   -> MP4
```

The old workflow, in which a YAML profile predefines video boundaries before Gemini sees the content, remains only as an explicit compatibility/debug path:

```powershell
--design-mode profile
```

## What Gemini receives

The DOCX file itself is parsed locally. For global planning, Gemini receives the **complete structured extraction**: block IDs, headings, heading paths, paragraph/table text, readable Office Math tokens, course constraints, and the global planning prompt. Raw OMML XML stays local.

For an individual video, Gemini receives:

- the global course summary and concept map;
- the complete planned video sequence;
- prerequisite/already-taught/forward-link context;
- only that video's authoritative core blocks and supporting reference blocks;
- the lesson-generation/review prompts and JSON schema.

For the dedicated narration-polish call, Gemini additionally receives the now-fixed lesson manifest, including slide titles, on-screen content, visual directions, equations, source provenance, timing and the current narration. Its response schema allows it to return only `slide_id`, polished `narration`, and optional `tts_text`. It cannot use that pass to redesign slides or silently change the science.

## Narration is a first-class production artifact

The dedicated narration prompt asks Gemini to write for the ear rather than the page: continuous lecturer-like speech, natural transitions, explanation rather than bullet recitation, restrained conversational tone, visual synchronization, TTS-ready mathematical language, and realistic pacing.

For most explanatory slides, the editor targets roughly 70–85% of theoretical speaking capacity:

```text
estimated_seconds * narration_wpm / 60
```

This leaves room for visual attention and pauses. The final manifest records `narration_word_count`, `narration_estimated_spoken_seconds`, optional `tts_text`, and narration-quality findings. See [NARRATION_QUALITY.md](docs/NARRATION_QUALITY.md).

## Normal first run

```powershell
microvid all `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile my_course
```

`microvid all` performs extraction, fresh whole-document planning, lesson generation/review, dedicated narration polishing, whole-course consistency review, PowerPoint generation, and validation.

For a staged workflow:

```powershell
microvid extract `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile my_course

microvid plan `
  --workspace ".\workspace\my_course" `
  --profile my_course

microvid draft `
  --workspace ".\workspace\my_course" `
  --profile my_course

microvid slides `
  --workspace ".\workspace\my_course"
```

The global plan is saved to:

```text
workspace/my_course/plans/course_plan.yaml
```

It carries a source signature. If the extracted DOCX changes, a stale plan is rejected/rebuilt rather than reused silently.

## New topic

`scaffold-profile` creates **course/parser/LLM constraints only**. It intentionally does not guess video boundaries from Heading 1 sections.

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

Review the generated course constraints and audience, then run `microvid all` with that profile. Gemini will read the complete structured document and decide the video boundaries.

## LLM configuration

The bundled provider is Google Gemini through `google-genai`:

```yaml
course:
  llm:
    provider: gemini
    model: gemini-flash-latest
    thinking_level: high
    api_key_env: GEMINI_API_KEY
    review_pass: true
    narration_polish_pass: true
    max_source_characters_per_lesson: 220000
    global_design:
      max_source_characters: 800000
      max_videos: 30
```

The narration polish is enabled by default even for older profiles that omit the field. Set `narration_polish_pass: false` only for deliberate cost/diagnostic comparisons.

Set the key locally:

```powershell
$env:GEMINI_API_KEY = "your-key"
```

No source packet is silently truncated. If the complete global source exceeds the configured global limit, planning fails visibly so a future hierarchical/chapter-level strategy can be chosen deliberately.

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

Voice audition:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

Windows SAPI remains a configurable fallback. The local media layer records the actual provider/voice/text used for every slide in `tts_manifest.yaml`.

## Editorial gates

Global Gemini consistency review happens before slide production. If blocking cross-course issues remain after the allowed targeted revision pass, draft manifests and review files are saved but slide generation is blocked.

Individual lesson manifests still begin with:

```yaml
editorial_status: llm_draft_requires_review
```

Human scientific/editorial approval remains required before final media production:

```yaml
editorial_status: approved
```

For narration specifically, audition representative lessons with the actual TTS voice before approving the full course. A polished LLM script remains subject to human judgment about scientific nuance, pace and teaching style.

## Installation

Windows PowerShell:

```powershell
.\scripts\setup-local.ps1
```

or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,windows]"
```

Run regression tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Compatibility/debug path

The legacy local profile segmentation remains available deliberately, not silently:

```powershell
microvid draft `
  --workspace ".\workspace\course" `
  --profile my_profile `
  --design-mode profile
```

Deterministic generation has no whole-document reasoning and therefore requires:

```powershell
--generator deterministic --design-mode profile
```
