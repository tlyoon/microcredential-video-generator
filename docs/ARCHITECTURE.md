# Architecture and Genericity Contract

## Project identity

**Microcredential Video Generator** is a topic-neutral Python framework. The preferred repository slug is `microcredential-video-generator`. Physics Laboratory 101 is the bundled reference profile and sample dataset; it is not a hard-coded domain restriction.

The Python package name is `microcredential-video-generator` and the CLI command is `microvid`. Neither depends on the GitHub repository slug.

## Production graph

```text
explicit runtime DOCX
  -> semantic extraction + provenance
  -> profile-driven lesson source packet
  -> Gemini lesson architecture + slide/narration generation by default
  -> grounded LLM review/revision
  -> structured slide manifest
  -> PPTX + speaker notes + narration + lecturer notes + SRT
  -> scientific-speech normalization
  -> configurable TTS provider
       -> Google Cloud Chirp 3 HD by default
       -> Windows SAPI fallback
  -> one audio file per slide
  -> PowerPoint slide rendering
  -> slide/audio video segments
  -> FFmpeg concatenation
  -> MP4
```

## Source-of-truth layers

1. **Explicit runtime DOCX** — authoritative subject source selected with `--source`.
2. **Extraction JSON** — ordered semantic blocks with provenance and semantic heading paths.
3. **Course profile YAML** — pedagogical boundaries, LLM settings, duration targets, source selectors, ranking terms, and optional TTS defaults.
4. **Prompt set** — version-controlled content-generation and review policy.
5. **Lesson manifest YAML** — production source of truth for one video; every slide owns its visible content, narration, notes, visual direction, timing, and source provenance.
6. **TTS configuration** — voice/provider settings independent of lesson content.
7. **Generated assets** — PPTX, notes, narration, subtitles, rendered slides, audio, segment files, and final MP4.

The tracked DOCX under `examples/sample_docs/` is sample data only and is never automatically selected.

## LLM boundary

Content abstraction is an LLM task by default, not a deterministic text-copying task. The deterministic builder remains available for offline/debugging use.

The LLM provider interface is separate from source selection, PowerPoint generation, TTS, and rendering. The shipped provider is Gemini. Model name, thinking level, API-key environment variable, review behavior, and source-packet limits are profile data. This permits model upgrades without changing segmentation or media code.

The bundled profile currently uses the configurable `gemini-flash-latest` selector. Production teams may pin an exact model when reproducibility is more important than automatic movement to a later model.

## Grounding and provenance

Each lesson receives only its selected source blocks with IDs, kinds, heading paths, text, tables, and readable math tokens. Full Office Math provenance is retained by extraction but is not unnecessarily dumped into every prompt.

LLM output is structured. Every source-derived slide must identify supporting block IDs. Unknown/invented source IDs are rejected. A zero-match required selector fails visibly before content generation rather than silently substituting unrelated content.

## Prompt architecture

The prompt system separates stable responsibilities instead of relying on an ad-hoc one-line request. It covers:

- evidence discipline and source fidelity;
- micro-learning pedagogy and cognitive load;
- conceptual compression and lesson flow;
- slide architecture and visual direction;
- natural spoken narration;
- TTS-ready expression of units/symbols;
- scientific/technical integrity;
- assessment design;
- grounded second-pass review/revision.

Prompt files are version-controlled under `src/microvid/prompts/` and can evolve independently of the renderer.

## Pagination independence and document revision handling

The parser does not use rendered Word pages. Changes to margins, page breaks, font size, or pagination do not alter semantic source selection.

Document structure is based on heading level, semantic breadcrumb path, source order, block type, and optional section identifiers. Semantic selectors such as `heading_contains` are preferred over page ranges or rigid numbering. Ordinary renumbering should therefore remain compatible; materially renamed or removed topics are reported as profile drift.

## Generic-course boundary

A different topic does not require Python changes when its DOCX has a reasonably comparable structure. `microvid scaffold-profile` creates an editable starter YAML profile from a new source. Human/editorial review remains responsible for confirming lesson boundaries, source selectors, outcomes, terminology, and priorities before production.

Domain-specific ranking terms belong in the course profile, never in generic Python code.

## Slide as the atomic production unit

Each slide binds together:

- concise on-screen content;
- full natural narration;
- lecturer notes;
- visual/build direction;
- optional exact LaTeX;
- source block IDs;
- estimated timing;
- optional `tts_text` and `tts_replacements`.

The PPTX embeds narration and production guidance in speaker notes while standalone text assets are also written. This keeps the deck useful as a teaching artifact and the media pipeline independently editable.

## TTS architecture

TTS is downstream from instructional authoring. Changing voice should not regenerate the course content.

The TTS provider layer currently supports:

- `google_cloud_chirp3` — production default;
- `sapi` — Windows fallback/offline option.

The default Chirp configuration uses `en-GB-Chirp3-HD-Leda`, but voice, locale, speaking rate, endpoint location, fallback behavior, and scientific normalization are configuration data.

Scientific speech normalization converts common notation conservatively before synthesis. For a difficult expression, `tts_text` explicitly controls the spoken rendering while `equation_latex` preserves exact mathematics on screen.

Every generated video stores `tts_manifest.yaml` containing the actual provider, voice, audio file, language, and spoken text used per slide.

## Media and approval gate

The complete Windows media path is:

```text
PPTX -> PowerPoint PNG export
manifest narration -> normalized text -> TTS audio
PNG + audio -> FFmpeg segment
segments -> final MP4
```

Final media rendering is blocked unless the lesson manifest is `editorial_status: approved`, except when `--allow-draft` is deliberately used for a private preview.

## Repository-name independence

The repository slug is presentation/discovery metadata, not a runtime dependency. Internal documentation should use relative links. Scripts intended to create a new copy default to `microcredential-video-generator`. A GitHub repository rename therefore does not require changes to source selection, profiles, generated workspaces, package imports, or the `microvid` CLI.
