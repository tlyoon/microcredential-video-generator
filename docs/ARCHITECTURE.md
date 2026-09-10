# Architecture and Genericity Contract

## Project identity

**Microcredential Video Generator** is a topic-neutral Python framework. Physics Laboratory 101 is the bundled reference profile and sample dataset; it is not a hard-coded domain restriction.

The Python package name is `microcredential-video-generator` and the CLI command is `microvid`.

## Production graph — v0.7.0 global-first default

```text
explicit runtime DOCX
  -> LOCAL semantic extraction + provenance
  -> COMPLETE structured extraction
  -> GEMINI global course planning
       -> course summary
       -> concept map
       -> pedagogical strategy
       -> video boundaries
       -> source block assignments
       -> prerequisites / already-taught / forward links
  -> LOCAL plan validation + source-signature protection
  -> GEMINI global-plan review/revision
  -> global course plan YAML
  -> for each planned video:
       global course context + assigned source blocks
       -> GEMINI slide + first-narration generation
       -> LOCAL deterministic lesson QA
       -> GEMINI grounded scientific/pedagogical lesson review/revision
       -> GEMINI dedicated narration-only polish
       -> LOCAL narration speech/timing QA
  -> GEMINI whole-course consistency review
       -> targeted lesson revisions where requested
       -> re-polish narration for any revised lesson
       -> final consistency verification
  -> LOCAL structured lesson manifests
  -> LOCAL PPTX + speaker notes + narration + lecturer notes + SRT
  -> LOCAL scientific-speech normalization
  -> configurable TTS provider
       -> Google Cloud Chirp 3 HD by default
       -> Windows SAPI fallback
  -> LOCAL PowerPoint slide rendering
  -> LOCAL FFmpeg segment/MP4 assembly
```

## Source-of-truth layers

1. **Explicit runtime DOCX** — authoritative subject source selected with `--source`.
2. **Extraction JSON** — ordered semantic blocks with provenance and semantic heading paths.
3. **Course constraint profile YAML** — audience, parser rules, LLM/TTS configuration, timing limits, and editorial policy. In global mode it does not dictate lesson boundaries.
4. **Global course plan YAML** — Gemini's reviewed whole-document concept map, lesson segmentation, source block assignments, prerequisites, and sequence. This becomes the design contract for lesson generation.
5. **Prompt set** — version-controlled global-planning, lesson-generation, lesson-review, narration-polish, and course-consistency policies.
6. **Lesson manifest YAML** — production source of truth for one video; every slide owns visible content, polished narration, notes, visual direction, timing, source provenance, and optional TTS-specific wording.
7. **TTS configuration** — voice/provider settings independent of lesson content.
8. **Generated assets** — PPTX, notes, narration, subtitles, rendered slides, audio, segment files, and final MP4.

The tracked DOCX under `examples/sample_docs/` is sample data only and is never automatically selected.

## Global LLM boundary

Lesson boundaries are not chosen locally before Gemini understands the source.

During global planning, the local parser sends Gemini the complete prompt-facing extraction: block ID, block kind, optional section, heading level/path, text, readable math tokens, and a flag indicating Office Math. Raw OMML XML stays local.

Gemini receives the complete document once for planning and again for plan review. The planner may group non-contiguous source blocks into one lesson where that better reflects the conceptual structure.

The global-plan schema requires explicit `core_block_ids` and optional `reference_block_ids` for every video. Unknown source IDs are rejected locally.

## Global plan source signature

A SHA-256 signature is calculated from the complete prompt-facing extraction and stored in `plans/course_plan.yaml`. This prevents a plan from one DOCX revision being silently reused after the source changes.

`microvid draft` may reuse a plan only when its signature matches the current extraction. `microvid all` replans by default after a fresh extraction; `--reuse-plan` only reuses a source-matched plan.

## Per-lesson LLM boundary

After global planning, each lesson-generation call receives:

- the global course summary;
- pedagogical strategy;
- concept map;
- the compact full lesson sequence;
- current lesson prerequisites;
- concepts marked `already_taught`;
- `forward_links` to later lessons;
- authoritative core blocks assigned by the global plan;
- optional reference blocks assigned by the global plan.

The entire DOCX is therefore not resent for every lesson, but the lesson is never generated without awareness of its role in the whole course.

Each lesson receives a generation pass followed by a grounded scientific/pedagogical review/revision pass by default. Every source-derived slide must cite block IDs supplied in that lesson packet. Invented provenance is rejected.

## Dedicated narration editorial layer

Narration is deliberately separated from the general lesson-review task because spoken-script quality has different optimization goals from scientific correctness and slide architecture.

After lesson content and structure are settled, Gemini receives:

- the fixed lesson manifest;
- current narration;
- title and on-screen text for every slide;
- `visual_direction`;
- equations;
- slide timing;
- narration words-per-minute target;
- global course context;
- the same authoritative/reference source blocks.

The narration-polish schema only permits:

```text
slide_id
narration
tts_text (optional)
```

It cannot return new titles, bullets, equations, source IDs, visual directions, or lesson structure. Local code verifies that every existing slide ID is returned exactly once.

The dedicated prompt treats the lesson as continuous speech rather than independent slide captions. It asks for natural university-lecturer delivery, smooth transitions, visual synchronization, explanation rather than bullet recitation, controlled sentence rhythm, TTS-ready mathematical speech, and restraint from generic filler or AI-like phrasing.

Local speech-hygiene QA rejects obvious raw LaTeX/markup and internal production/meta language in the final narration. It records per-slide word count and estimated spoken duration and warns when the script is too dense for the allocated slide time.

If whole-course consistency review later requires a targeted revision of a lesson, that revised lesson is sent through narration polishing again before final course verification.

See `docs/NARRATION_QUALITY.md` for the detailed narration contract.

## Whole-course consistency layer

Once every lesson has been generated and polished, Gemini reviews the complete course plan and compact versions of all generated lesson manifests together.

The review checks for concept gaps, accidental repetition, prerequisite violations, inconsistent terminology/notation/units/definitions, premature introduction of later material, poor hand-offs between videos, duplicated or weak checks/takeaways, and drift from the globally planned scope.

The review can return targeted revision instructions for specific videos. Those lessons are regenerated using their original authoritative source packets plus global context and the consistency instructions, and their narration is polished again. Gemini then performs a final whole-course verification.

If blocking issues remain, normal slide production is blocked. Draft lesson manifests and review reports remain available for diagnosis.

## Prompt architecture

The version-controlled prompt set separates distinct responsibilities:

- `system_microcredential_architect.md` — invariant source-fidelity, pedagogy, narration, and production rules;
- `global_course_planning.md` — whole-document comprehension, concept mapping, and video segmentation;
- `global_course_plan_review.md` — independent review/revision of the global plan against the full source;
- `lesson_generation.md` — slide/first-narration design using both global context and local authoritative blocks;
- `lesson_review.md` — grounded scientific/pedagogical per-lesson review/revision;
- `narration_polish.md` — dedicated spoken-script editing with frozen lesson structure;
- `global_course_consistency_review.md` — final cross-lesson coherence and targeted revision instructions.

The LLM provider interface remains separate from extraction, PowerPoint, TTS, and media rendering.

## Pagination independence

The parser does not use rendered Word pages. Changes to margins, page breaks, font size, or pagination do not alter the semantic extraction.

Document structure is represented using heading level, semantic breadcrumb path, source order, block type, optional section identifiers, tables, paragraphs, and Office Math provenance.

## Generic-course boundary

For a new topic, `microvid scaffold-profile` creates a **constraint profile**, not a locally guessed set of lesson boundaries. The scaffold provides course/audience placeholders, parser conventions, Gemini settings, global-design limits, narration-polish policy, and generic TTS configuration. Its `videos` list is intentionally empty.

Gemini then reads the whole extracted source and decides the course segmentation.

The legacy pre-segmented profile workflow remains available only with `--design-mode profile`. It exists for compatibility, testing, or deliberate instructor-controlled segmentation, not as the normal production path.

Deterministic generation has no whole-document semantic reasoning and therefore requires `--generator deterministic --design-mode profile`.

## Slide as the atomic production unit

Each generated slide binds together:

- concise on-screen content;
- polished natural narration;
- lecturer notes;
- visual/build direction;
- optional exact LaTeX;
- source block IDs;
- estimated timing;
- optional `tts_text` and `tts_replacements`;
- narration word-count and estimated spoken-duration metrics after polishing.

The PPTX embeds narration and production guidance in speaker notes while standalone text assets are also written.

## TTS and media boundary

TTS is downstream from instructional authoring. Changing voice should not regenerate the course content.

The provider layer currently supports Google Cloud Chirp 3 HD as the production default and Windows SAPI as fallback/offline option. Scientific speech normalization converts common notation conservatively before synthesis.

The final Windows media path is:

```text
PPTX -> PowerPoint PNG export
polished manifest narration/tts_text -> normalized text -> TTS audio
PNG + audio -> FFmpeg segment
segments -> final MP4
```

Human scientific/editorial approval remains a separate gate. Final media rendering is blocked unless the lesson manifest is `editorial_status: approved`, except when `--allow-draft` is deliberately used for a private preview.

## Large-document boundary

The global planning pass intentionally sends the complete structured source and refuses silent truncation. The default global limit is 800,000 prompt-facing source characters. Very large books should eventually use a hierarchical planner rather than relying on arbitrary truncation or blind context-limit increases.
