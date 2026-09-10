# Project status — v0.3.0

## Implemented

- Generic DOCX semantic extraction with paragraphs, tables and Office Math provenance.
- Pagination-independent semantic heading-path selection.
- Generic YAML course profiles and automatic profile scaffolding for unrelated topics.
- LLM-first content authoring pipeline; deterministic authoring is explicit offline/debug fallback only.
- Google Gemini provider using the official `google-genai` SDK and structured outputs.
- Default model selector `gemini-flash-latest`, with high reasoning and CLI/profile model overrides.
- Two-pass LLM workflow: lesson generation followed by independent grounded review/revision.
- Comprehensive version-controlled prompt set for source fidelity, pedagogical abstraction, slide design, narration, technical integrity, provenance and assessment.
- Per-slide manifest containing on-screen content, full narration, lecturer notes, visual direction, source provenance, optional LaTeX and timing.
- Narration and production guidance embedded into PowerPoint speaker notes as well as separate text/SRT assets.
- TTS and FFmpeg MP4 assembly hooks.
- Editorial approval gate before final video rendering.
- Corrected Lab 101 DOCX tracked under `examples/sample_docs/` as sample/reference data only; all actual builds require explicit `--source`.

## Validation

- 12 local unit/regression tests pass, including mocked two-pass LLM generation and PowerPoint speaker-note persistence.
- Semantic section renumbering regression passes.
- Unrelated-topic scaffold/build regression passes.
- Stale-profile detection remains fail-visible.
- No external Gemini call is performed by the automated unit tests; API integration requires the user's local `GEMINI_API_KEY`.

## Current production boundary

The source extraction, LLM prompt packet, structured manifest, PPTX/narration and media stages are implemented. The quality of an actual Gemini-generated lesson must still be validated with a live API key and human scientific/editorial review before a lesson is marked `approved`.
