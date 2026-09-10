# Project Status — v0.5.0

## Project identity

The software is **Microcredential Video Generator**, a generic topic-neutral DOCX-to-narrated-video pipeline. The preferred GitHub repository slug is `microcredential-video-generator`. Physics Laboratory 101 is the bundled reference profile and sample document, not a hard-coded software scope.

## Implemented

- Generic DOCX semantic extraction with paragraphs, tables, heading hierarchy, and Office Math provenance.
- Pagination-independent semantic heading-path selection.
- Generic YAML course profiles and automatic profile scaffolding for unrelated topics.
- Fail-visible stale-profile detection when required source material no longer matches.
- LLM-first content authoring; deterministic authoring remains an explicit offline/debugging fallback.
- Google Gemini provider through the official `google-genai` SDK with structured output.
- Soft-coded Gemini model and reasoning configuration.
- Default two-pass lesson workflow: generation followed by independent grounded review/revision.
- Version-controlled prompts covering source fidelity, pedagogical compression, slide architecture, narration, technical integrity, provenance, assessment, and TTS-ready speech.
- Per-slide production manifest containing on-screen content, full narration, lecturer notes, visual direction, source provenance, optional LaTeX, timing, and optional TTS-specific overrides.
- PowerPoint generation with narration and production guidance embedded in speaker notes.
- Standalone narration, lecturer-note, and SRT subtitle assets.
- Pluggable TTS provider layer.
- Google Cloud Chirp 3 HD production TTS with configurable voice/locale/rate/location.
- Default female British-English Chirp voice `en-GB-Chirp3-HD-Leda`.
- Windows SAPI fallback/offline TTS option.
- Scientific speech normalization plus per-slide `tts_text` and `tts_replacements` overrides.
- Voice audition workflow.
- TTS provenance logging in `tts_manifest.yaml`.
- PowerPoint PNG rendering and FFmpeg per-slide/final MP4 assembly.
- Editorial approval gate before final media rendering.
- Corrected Lab 101 DOCX tracked under `examples/sample_docs/` as reference/sample data only; actual builds always require explicit `--source`.
- Comprehensive user manual, architecture document, configuration reference, Chirp guide, pilot workflow, and changelog.
- Repository publication script now defaults to the generic name `microcredential-video-generator`.

## Validation

The Chirp/TTS change was integrated through PR #1 after the GitHub Actions test job completed successfully. The test suite covers generic parsing/selection, unrelated-topic handling, LLM builder behavior, manifest generation, slide-note persistence, media capabilities, and TTS/speech behavior.

No live Gemini or Cloud TTS credentials are stored in the repository. Automated tests must not depend on private credentials.

## Current production boundary

The end-to-end architecture from DOCX through manifests, PowerPoint, narration, TTS, and MP4 assembly is implemented. Publication-quality instructional output still requires a live pilot with real Gemini and Chirp calls plus human scientific/editorial review before lessons are marked `approved`.

## Repository rename status

Code and documentation have been prepared for the generic repository name `microcredential-video-generator`. Runtime code is repository-name independent. The GitHub connector available in this environment does not expose the repository rename operation itself, so the GitHub slug must be renamed once in repository Settings. After that, existing clones should update `origin` to the new URL for clarity.
