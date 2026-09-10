# Changelog

All notable project changes are summarized here.

## 0.7.0 — Dedicated Gemini narration polishing

- Promoted narration to a first-class production artifact rather than accepting the script directly from the general slide-generation/review pass.
- Added `src/microvid/prompts/narration_polish.md`, a detailed spoken-script editorial contract covering natural lecturer voice, continuity, visual synchronization, timing, TTS readiness, equation verbalization, assessment pauses, and anti-patterns.
- Added a separate narration-only Gemini call after lesson generation and grounded scientific/pedagogical review.
- Restricted the narration-polish response schema to existing `slide_id`, polished `narration`, and optional `tts_text`, preventing that pass from redesigning slides, changing equations, or altering source provenance.
- Added local enforcement that every existing slide is returned exactly once and in the same lesson structure.
- Added narration speech-hygiene checks for raw LaTeX/markup and internal production/meta language.
- Added timing-density warnings based on `estimated_seconds` and configured narration words per minute.
- Added `narration_word_count` and `narration_estimated_spoken_seconds` to polished slide records.
- Added generation provenance under `generation.narration_polish`.
- If whole-course consistency review requires a targeted lesson revision, narration polishing is run again for that revised lesson before final verification.
- Strengthened the upstream system narration contract so first-pass scripts are already coherent, speech-oriented, visually synchronized, and free of common filler.
- Added `course.llm.narration_polish_pass`, enabled by default for bundled and newly scaffolded profiles. Older profiles that omit the setting also default to enabled.
- Added `docs/NARRATION_QUALITY.md` and updated README/configuration/manual documentation.
- Added regression coverage proving that the dedicated narration pass runs and preserves slide/source provenance.

## 0.6.0 — Global-first Gemini course design

- Replaced the production default in which YAML lesson boundaries were chosen before Gemini saw the source.
- Added a whole-document Gemini planning pass that receives the complete structured DOCX extraction before any video/slide segmentation.
- Added a second whole-document Gemini plan-review/revision pass.
- Added a global course plan containing course summary, pedagogical strategy, concept map, video boundaries, source-block assignments, prerequisites, already-taught concepts, forward links, checks, and takeaways.
- Added local deterministic validation of global-plan source block IDs, duplicate core assignments, and unassigned substantive blocks.
- Added SHA-256 source signatures so a global plan cannot be silently reused after the extracted DOCX changes.
- Changed per-video Gemini generation so every lesson receives the global course map and full sequence context plus its assigned authoritative/reference source blocks.
- Added final whole-course Gemini consistency review across all generated lesson manifests.
- Added targeted per-lesson revision calls from whole-course review instructions and a final course verification pass.
- Added a slide-production gate when unresolved blocking whole-course issues remain.
- Added `microvid plan` for explicit whole-document planning.
- Changed `microvid all` to extract -> globally plan -> generate/review lessons -> globally review -> build slides -> validate.
- Added `--design-mode profile` only as an explicit legacy/instructor-presegmented compatibility mode.
- Restricted deterministic generation to `--generator deterministic --design-mode profile` because deterministic code has no whole-document semantic reasoning.
- Changed new-topic `scaffold-profile` behavior so it creates global-design constraints and leaves `videos: []` instead of locally guessing lesson boundaries from Heading 1 sections.
- Added global planning, global plan review, and whole-course consistency prompt files.
- Updated lesson generation/review prompts to honor prerequisites, already-taught concepts, forward links, and the global concept map.
- Added `docs/GLOBAL_DESIGN.md` and comprehensively updated README, user manual, architecture, configuration reference, status, and pilot documentation.
- Added regression tests verifying that the planning prompt contains both early and late source content and that per-lesson generation receives global context before whole-course review.

## 0.5.0 — Generic project identity and documentation consolidation

- Standardized the project identity as **Microcredential Video Generator**.
- Recommended GitHub repository slug changed from `physics-lab-microcredential-video-generator` to `microcredential-video-generator`.
- Clarified that Physics Laboratory 101 is the bundled reference profile/sample, not the software's domain boundary.
- Updated Python package description to describe the generic DOCX-to-video workflow.
- Updated the repository publication script to default to `microcredential-video-generator`.
- Added `docs/CONFIGURATION_REFERENCE.md`.
- Reworked README, user manual, architecture, project status, Chirp guide, and pilot documentation to describe the Gemini-first, Chirp-enabled pipeline consistently.
- Documented repository-name independence and rename migration behavior.

## 0.4.0 — Configurable Google Cloud Chirp 3 HD TTS

- Added pluggable TTS provider architecture.
- Added Google Cloud Chirp 3 HD as the production default.
- Added configurable female British-English default voice `en-GB-Chirp3-HD-Leda`.
- Retained Windows SAPI as a configurable fallback.
- Added scientific speech normalization.
- Added per-slide `tts_text` and `tts_replacements` support.
- Added voice-audition workflow.
- Added TTS provenance logging in `tts_manifest.yaml`.
- Updated LLM prompting so narration is written as TTS-ready spoken prose.
- Added Google Cloud Text-to-Speech dependency and regression tests.

## 0.3.0 — Gemini-first lesson authoring

- Added Google Gemini LLM provider through the official `google-genai` SDK.
- Made LLM slide/narration generation the normal content-authoring path.
- Added two-pass lesson generation plus grounded review/revision.
- Added version-controlled prompt architecture for source fidelity, pedagogy, slide design, narration, visuals, technical integrity, provenance, and assessment.
- Added structured per-slide narration, lecturer notes, visual direction, equations, source block IDs, and timing.
- Embedded narration and production guidance into PowerPoint speaker notes.

## 0.2.0 — Generic document/profile handling

- Removed Physics-specific ranking behavior from the generic engine.
- Added semantic heading selectors and pagination-independent source handling.
- Added profile scaffolding for unrelated structured DOCX topics.
- Added stale-profile detection so missing source material fails visibly.
- Included the corrected Physics Laboratory 101 DOCX under `examples/sample_docs/` as reference/sample data only.

## 0.1.0 — Initial pipeline

- Added DOCX semantic extraction.
- Added Lab 101 nine-video profile.
- Added YAML lesson manifests, PowerPoint generation, narration assets, subtitles, QA, and initial media hooks.
