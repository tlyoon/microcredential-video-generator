# Architecture and genericity contract

## Production graph

```text
explicit DOCX
  -> semantic extraction
  -> profile-driven lesson source packet
  -> LLM lesson architecture + script generation
  -> grounded LLM review/revision
  -> structured slide manifest
  -> PPTX + speaker notes + narration + SRT
  -> TTS
  -> slide/audio video segments
  -> MP4
```

## Source-of-truth layers

1. **Explicit runtime DOCX** — authoritative subject source selected with `--source`.
2. **Extraction JSON** — ordered semantic blocks with provenance and semantic heading paths.
3. **Course profile YAML** — pedagogical boundaries, model/provider settings, duration targets and ranking terms.
4. **Prompt set** — version-controlled content-generation and review policy.
5. **Lesson manifest YAML** — production source of truth for one video; every slide owns its narration and provenance.
6. **Generated assets** — PPTX, notes, narration, subtitles and media.

The tracked DOCX under `examples/sample_docs/` is sample data only and is never automatically selected.

## LLM boundary

Content abstraction is an LLM task by default, not a deterministic text-extraction task. The deterministic builder remains available only for diagnostics/offline drafting.

The LLM provider interface is separate from lesson selection and rendering. The shipped provider is Gemini; model name, thinking level, API-key environment variable and source-packet limits are profile data. This means later model upgrades do not require changes to the segmentation or media code.

Default profile model selector: `gemini-flash-latest`.

## Grounding

Each lesson receives only its selected core/reference source blocks with IDs, kinds, heading paths, text and readable math tokens. Full OMML XML is preserved in extraction provenance but is not dumped into the prompt unnecessarily.

LLM output is structured JSON. Every source-derived slide must identify supporting block IDs. The normalizer rejects any block ID that was not supplied in the lesson packet. A zero-match profile fails before an LLM call is made.

## Prompt architecture

The prompt set deliberately separates responsibilities:

- system architect contract — invariant evidence/pedagogy/narration rules;
- lesson generation — conceptual spine, compression and visual abstraction;
- lesson review — independent source-grounded revision of the first pass.

This is preferable to one giant ad-hoc prompt because each stage has a clear QA purpose and can be versioned or replaced independently.

## Pagination independence and semantic revision handling

The parser does not use rendered Word pages. Ordinary pagination, margins, font changes and section renumbering do not affect semantic selectors. Materially changed headings/content are reported as profile drift rather than silently substituted.

## New-topic onboarding

`microvid scaffold-profile` creates a starter YAML profile from a new structured DOCX. Editorial review still decides lesson boundaries, outcomes, priorities and source selectors. The same Gemini authoring pipeline can then generate the slide stacks without Python modifications.

## Media architecture

Narration is generated and stored per slide, not as one monolithic script. The PPTX embeds it in speaker notes and standalone narration files are also emitted. TTS therefore generates one audio unit per slide, making isolated correction/regeneration possible. FFmpeg then combines rendered slide images and TTS audio into MP4.
