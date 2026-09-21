# Project Status — v0.8.0

## Project identity

**Microcredential Video Generator** is a generic topic-neutral DOCX/PDF-to-narrated-video pipeline. Physics Laboratory 101 remains the bundled reference profile and sample course.

## Implemented

- Generic source dispatch for explicit `.docx` and text-readable `.pdf` inputs.
- DOCX semantic extraction with paragraphs, tables, heading hierarchy, source order, semantic heading paths, and Office Math provenance.
- Native PDF extraction through PyMuPDF with ordered text blocks, font/heading cues, equation-like text where identifiable, page provenance, and repeated margin boilerplate filtering.
- Image-only/scanned PDFs fail visibly when too little extractable text is available; OCR is not invoked automatically.
- PDF page numbers are retained only as provenance metadata; lesson segmentation remains semantic rather than page-based.
- DOCX and PDF are normalized into the same common semantic block schema before downstream planning.
- Whole-document Gemini global planning before any production lesson/slide segmentation.
- Global concept map, pedagogical strategy, video sequence, source-block assignments, prerequisites, already-taught concepts, and forward links.
- Second Gemini pass reviewing/revising the global course plan against the complete structured source.
- Deterministic local validation of global plan source IDs and coverage warnings.
- SHA-256 source signature protection preventing silent reuse of a global plan after source-document changes.
- Per-video Gemini generation using both the global course context and assigned authoritative/reference source blocks.
- Per-video grounded Gemini scientific/pedagogical review/revision plus local manifest QA.
- Dedicated Gemini narration-only polishing pass after lesson content/structure has been settled.
- Narration-polish response constrained to existing slide IDs, polished narration, and optional TTS text; slide structure/science/provenance are frozen during this pass.
- Narration-specific local speech-hygiene checks and timing-density warnings.
- Per-slide narration word counts and estimated spoken duration recorded in the manifest.
- Targeted whole-course lesson revisions are re-polished before final course verification.
- Feynman-inspired narration contract for concrete motivation, intuitive reasoning, physical interpretation of equations, restrained analogies, misconception handling, continuity, and concise TTS-ready speech.
- Self-learning lesson architecture for ordinary LLM lessons: introduction -> concept development -> reasoning check -> conclusion; textbook subchapters retain title -> introduction -> development -> check -> conclusion.
- Structured visual grammar (`process`, `comparison`, `table`, `diagram`, `equation_focus`, `figure`) carried in the lesson manifest and rendered natively in PowerPoint.
- Source-grounded visual panels and compact tables allow concepts to be visualized without inventing external data or facts.
- Learner-facing provenance footers removed; source traceability remains in manifests and speaker notes.
- Whole-course Gemini consistency review after all lessons are generated.
- Targeted lesson revision from whole-course review instructions followed by final course verification.
- Slide-production gate when unresolved global blocking issues remain.
- `microvid plan` command for explicit global planning.
- `microvid all` production default: extract -> global plan/review -> lesson generation/review -> narration polish -> whole-course review/revision -> slides -> validation.
- Legacy instructor-presegmented profile mode retained explicitly via `--design-mode profile`.
- Deterministic generation restricted to the explicit legacy path because it has no global semantic reasoning.
- New-topic scaffolding produces a course/parser/LLM constraint shell with `videos: []` and narration polish enabled.
- Google Gemini provider through the official `google-genai` SDK with structured outputs.
- Version-controlled prompts for global planning, global plan review, lesson generation, lesson review, dedicated narration polishing, and whole-course consistency review.
- Per-slide manifest containing on-screen content, polished narration, lecturer notes, structured visual type/panels/tables, visual direction, source provenance, optional LaTeX, timing, optional `tts_text`, and narration quality metrics.
- PowerPoint generation with narration and production guidance embedded in speaker notes.
- Standalone narration, lecturer-note, and SRT subtitle assets.
- Pluggable TTS provider layer.
- Google Cloud Chirp 3 HD production TTS with configurable voice/locale/rate/location.
- Default Google Cloud Chirp 3 HD voice `en-US-Chirp-HD-F`, with default speaking rate 0.8 on this development branch.
- Windows SAPI fallback/offline TTS option.
- Scientific speech normalization plus `tts_text` and `tts_replacements` overrides.
- Voice audition workflow and TTS provenance logging.
- PowerPoint PNG rendering and FFmpeg segment/final MP4 assembly.
- Automated production gating: grounded revision, narration polish, whole-course consistency review, and deterministic QA; no human approval status is required for media rendering.
- Corrected Lab 101 DOCX tracked under `examples/sample_docs/` as reference/sample data only; all real builds require explicit `--source`.
- Comprehensive README, user manual, global design guide, narration-quality guide, architecture document, configuration reference, Chirp guide, pilot workflow, and changelog.

## Automated validation

The regression suite covers the global-first, narration-quality, and PDF-ingestion concerns, including:

- the initial planning prompt contains source content from both the beginning and end of a synthetic DOCX;
- the global course plan carries the source signature and explicit source-block assignments;
- per-lesson generation receives `global_course_context` rather than only isolated lesson text;
- the dedicated narration editor is called after lesson review;
- narration polishing preserves slide/source provenance and can add TTS-specific wording without redesigning slides;
- narration timing metadata is produced;
- whole-course consistency review runs before the course index is marked ready;
- PDF extraction preserves semantic headings and page provenance while filtering repeated page headers/footers and page-number labels;
- the generic source dispatcher retains DOCX support, accepts PDFs, and rejects unsupported file types visibly;
- image-only PDFs fail visibly rather than entering the planning pipeline with empty content;
- PDF extraction serializes into the same common schema and is compatible with the global course packet/signature layer;
- generic parsing/selection, manifest QA, PowerPoint speaker-note persistence, media capabilities, Chirp/SAPI behavior, and scientific speech normalization remain covered.

The v0.8.0 feature was additionally validated against the shared Physics Laboratory 101 PDF: 31 pages, 715 semantic blocks, 190 equation-classified blocks, repeated page boilerplate removed, key numbered sections detected, and the complete source packet remained within the configured global source limit.

No live Gemini or Cloud TTS credentials are stored in the repository. Automated tests use fake/mock LLM responses and must remain independent of private credentials.

## Production boundary

The software-level workflow is designed for automated production. A real build requires valid Gemini/TTS credentials and successful runtime calls, but it does not require a human approval flag. Blocking whole-course or deterministic QA findings stop the normal path automatically. Optional inspection or TTS audition can still be used while tuning the package.

## Known boundaries

The global planning pass sends the complete prompt-facing structured extraction and refuses silent truncation. The default upper limit is 800,000 source characters. Very large textbooks should eventually use a hierarchical major-unit/chapter planner rather than arbitrary truncation.

DOCX paragraphs, tables, headings, and Office Math are supported; PDF text/font/layout cues and page provenance are supported. For detected textbook-subchapter PDFs, captioned figure regions are extracted as source assets and can be selected for slide placement using their caption/context metadata. Full multimodal interpretation of arbitrary embedded figures is not yet implemented.

Narration timing metrics are estimates based on word count and configured words per minute. Actual Chirp audio duration should eventually be fed back into subtitle/timing validation for production-grade synchronization.
