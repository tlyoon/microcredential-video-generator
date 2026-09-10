# Project Status — v0.6.0

## Project identity

**Microcredential Video Generator** is a generic topic-neutral DOCX-to-narrated-video pipeline. Physics Laboratory 101 remains the bundled reference profile and sample document.

## Implemented

- Generic DOCX semantic extraction with paragraphs, tables, heading hierarchy, and Office Math provenance.
- Pagination-independent extraction and semantic heading paths.
- Whole-document Gemini global planning before any production lesson/slide segmentation.
- Global concept map, pedagogical strategy, video sequence, source-block assignments, prerequisites, already-taught concepts, and forward links.
- Second Gemini pass reviewing/revising the global course plan against the complete structured source.
- Deterministic local validation of global plan source IDs and coverage warnings.
- SHA-256 source signature protection preventing silent reuse of a global plan after DOCX changes.
- Per-video Gemini generation using both the global course context and assigned authoritative/reference source blocks.
- Per-video grounded Gemini review/revision plus local manifest QA.
- Whole-course Gemini consistency review after all lessons are generated.
- Targeted lesson revision from whole-course review instructions followed by final course verification.
- Slide-production gate when unresolved global blocking issues remain.
- `microvid plan` command for explicit global planning.
- `microvid all` production default: extract -> global plan/review -> lesson generation/review -> whole-course review/revision -> slides -> validation.
- Legacy instructor-presegmented profile mode retained explicitly via `--design-mode profile`.
- Deterministic generation restricted to the explicit legacy path because it has no global semantic reasoning.
- New-topic scaffolding changed from local Heading-1 packing to a course/parser/LLM constraint shell with `videos: []`.
- Google Gemini provider through the official `google-genai` SDK with structured outputs.
- Version-controlled prompts for global planning, global plan review, lesson generation, lesson review, and whole-course consistency review.
- Per-slide manifest containing on-screen content, narration, lecturer notes, visual direction, source provenance, optional LaTeX, timing, and TTS overrides.
- PowerPoint generation with narration and production guidance embedded in speaker notes.
- Standalone narration, lecturer-note, and SRT subtitle assets.
- Pluggable TTS provider layer.
- Google Cloud Chirp 3 HD production TTS with configurable voice/locale/rate/location.
- Default female British-English Chirp voice `en-GB-Chirp3-HD-Leda`.
- Windows SAPI fallback/offline TTS option.
- Scientific speech normalization plus `tts_text` and `tts_replacements` overrides.
- Voice audition workflow and TTS provenance logging.
- PowerPoint PNG rendering and FFmpeg segment/final MP4 assembly.
- Human editorial approval gate before final media rendering.
- Corrected Lab 101 DOCX tracked under `examples/sample_docs/` as reference/sample data only; all real builds require explicit `--source`.
- Comprehensive README, user manual, global design guide, architecture document, configuration reference, Chirp guide, pilot workflow, and changelog.

## Automated validation

The v0.6.0 branch adds regression coverage specifically for the global-first concern:

- verifies the first planning prompt contains source content from both the beginning and end of a synthetic DOCX;
- verifies the global course plan carries the source signature and explicit source-block assignments;
- verifies per-lesson generation receives `global_course_context` rather than only isolated lesson text;
- verifies the whole-course consistency review runs before the course index is marked ready.

Existing tests continue to cover generic parsing, semantic selection, manifest QA, PowerPoint speaker-note persistence, media capability reporting, Chirp/SAPI TTS behavior, and scientific speech normalization.

No live Gemini or Cloud TTS credentials are stored in the repository. Automated tests use fake/mock LLM responses and must remain independent of private credentials.

## Production boundary

The global-first architecture is implemented end-to-end at the software level. A real production course still requires:

1. a live Gemini run with the chosen model/account;
2. inspection of `plans/course_plan.yaml` to confirm that the model genuinely understood the full source;
3. inspection of whole-course consistency reports;
4. human scientific/editorial approval of lesson manifests and representative slide decks;
5. a live Chirp voice/media pilot before batch production.

## Known boundary

v0.6.0 sends the complete prompt-facing structured extraction during global planning and refuses silent truncation. The default upper limit is 800,000 source characters. Very large textbooks should eventually use a hierarchical major-unit/chapter planner rather than arbitrary truncation.

Embedded DOCX figures/images are not yet extracted as multimodal Gemini inputs. Paragraphs, tables, headings, and Office Math are supported; source figures remain a future enhancement.
