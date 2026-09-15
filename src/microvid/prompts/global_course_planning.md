# GLOBAL COURSE PLANNING — READ THE WHOLE SOURCE BEFORE SEGMENTING

You are planning the complete microcredential course before any individual slide deck is written.

The complete structured source document is supplied below. Read it as one coherent document. Your first responsibility is to understand its global conceptual structure, dependencies, repeated ideas, worked examples, important equations, cautions, and reporting conventions. Do not mechanically turn Word sections or pages into videos.

## Required planning behavior

1. Build a coherent mental model of the entire source before deciding lesson boundaries.
2. Identify foundational concepts and prerequisite relationships.
3. Identify which source blocks belong together pedagogically even when they are far apart in the document.
4. Keep worked examples with the concepts they best illuminate; do not split a reasoning chain merely because a heading changes.
5. Merge short/repetitive sections when a single lesson gives a better conceptual arc.
6. Split conceptually dense material when one lesson would overload the learner.
7. Avoid reteaching the same idea in several videos unless deliberate spaced reinforcement is educationally justified.
8. Preserve the source document as the authority. Do not invent subject-matter content or source IDs.
9. Assign explicit `core_block_ids` to each video. Use `reference_block_ids` for useful supporting detail from anywhere in the document.
10. Consider the configured target duration and total course duration as design constraints, not as reasons to omit essential reasoning.
11. Make the sequence cumulative: record what should already have been taught and what later lessons will build on.
12. Prefer a small number of meaningful lessons over many fragmented videos.

## Concept map

Create a concise concept map for the entire source. For each major concept, identify supporting source block IDs and prerequisite concepts. This map will be given back to Gemini during every later lesson-generation call.

## Video plan

For every planned video provide:

- stable video ID in sequence (`V01`, `V02`, ...);
- concise instructional title;
- focus/purpose;
- realistic target duration and maximum slide count;
- learning outcomes;
- one useful conceptual check question;
- up to three takeaways;
- authoritative `core_block_ids`;
- optional `reference_block_ids`, which may come from non-contiguous parts of the source;
- prerequisite video IDs;
- `already_taught`: concepts the lesson may assume without reteaching;
- `forward_links`: concepts or skills that later lessons will build from this lesson.

## Coverage discipline

Do not feel obliged to put administrative boilerplate, table-of-contents text, duplicated wording, or detailed reference checklists into a video. However, substantive concepts, assumptions, equations, worked examples, and limitations should not disappear merely because they do not align with a pre-existing section boundary. Use `coverage_notes` to explain intentionally omitted or reference-only material.

Return only JSON conforming to the supplied schema.
## Textbook-subchapter planning mode

When `source_document.classification.kind` is `textbook_subchapter`, the local ingestion layer has
already identified and scoped the dominant intended numbered subchapter. Treat the supplied blocks
as the complete authoritative scope: do not infer, restore, or plan lessons from adjacent sections
that were excluded during ingestion.

For a short self-contained subchapter, prefer one coherent video unless conceptual density genuinely
requires more than one. If multiple videos are pedagogically justified, each video must still be a
complete micro-lesson. Reserve enough slide capacity for the mandatory textbook architecture:
`title` -> `introduction` -> substantive concept development -> conceptual `check` -> `conclusion`.
Therefore every planned textbook video must have `max_slides >= 5`.

The check question should strengthen conceptual understanding rather than test trivial recall. The
course plan should cover the substantive ideas, equations, examples, cautions, and interpretations
of the scoped subchapter without importing unsupported material from general knowledge.

## Textbook figure planning

When the scoped source is a textbook subchapter and `source_document.available_figures` is non-empty, account for those supplied textbook visuals while planning the lesson sequence.

- Treat the supplied figures as part of the authoritative source context, not decoration.
- Plan concept development so a relevant figure can be used where it genuinely clarifies the physical idea, mechanism, comparison, or example.
- Do not force a figure into every lesson or slide.
- Do not request external images, substitute stock imagery, or invent a figure that is absent from the supplied source.
- Preserve enough slide capacity for a figure-centered explanation when a figure is central to understanding.
- Keep visual density low enough that a figure and the necessary explanatory text can be inspected comfortably at normal presentation size.
