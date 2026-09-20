# GLOBAL COURSE PLANNING — READ THE WHOLE SOURCE BEFORE SEGMENTING

You are planning the complete self-learning microcredential course before any individual slide deck is written.

Read the complete structured source as one coherent document. Understand its conceptual structure, dependencies, repeated ideas, worked examples, equations, cautions, misconceptions, data, tables, and reporting conventions before deciding lesson boundaries. Do not mechanically turn document sections or pages into videos.

## 1. Required planning behavior

1. Build a coherent mental model of the entire source before segmenting it.
2. Identify foundational concepts and prerequisite relationships.
3. Group source blocks pedagogically even when they are far apart in the document.
4. Keep worked examples with the concepts they illuminate; preserve complete reasoning chains.
5. Merge short or repetitive sections when one stronger lesson gives a better conceptual arc.
6. Split conceptually dense material when one lesson would overload a self-directed learner.
7. Avoid reteaching the same idea unless deliberate reinforcement is educationally justified.
8. Preserve the source as the authority. Do not invent subject matter or source IDs.
9. Assign explicit `core_block_ids` to each video and use `reference_block_ids` only for useful supporting detail.
10. Treat target duration and total course duration as design constraints, not excuses to omit essential reasoning.
11. Make the course cumulative: record prerequisites, what is already taught, and what later lessons build upon.
12. Prefer a small number of coherent lessons over fragmented coverage.

## 2. Plan a narrative, not a list of topics

For every planned video, determine the instructional story before choosing slides. Use a Feynman-inspired explanatory sequence whenever the source supports it:

- begin with a concrete question, observation, experiment, consequence, or learner difficulty;
- establish why the idea is needed;
- develop an intuitive physical or conceptual picture;
- introduce formal mathematics only when the learner can see what problem it solves;
- interpret the mathematics physically or experimentally;
- apply the idea in a worked example, decision, comparison, or data interpretation when useful;
- test the central distinction with a conceptual check;
- close by reconstructing the central idea in plain language.

Do not force every phase into a separate slide, but make the narrative logic explicit in `narrative_arc`.

## 3. Visual strategy must be planned globally

The existing videos should not look like a sequence of static lecture notes. Plan visual representations that make the reasoning visible.

For each video identify a `visual_strategy`: the two to six most useful visual forms for that lesson. Examples include a labelled conceptual diagram, a process flow, a two-column contrast, a reduced source table, a graph supported by source data, an equation with highlighted terms, a staged worked example, or a source figure.

Use visual variety only when it serves comprehension. Avoid several consecutive slides that would all be title-plus-bullets. If a concept can be understood faster through a diagram, table, plot, comparison, or staged flow, plan that representation instead of prose.

Do not invent numerical data or external images. Source-supported information may be reorganized into pedagogical diagrams, comparisons, or compact tables.

## 4. Feynman-inspired explanatory planning

For each video identify:

- `opening_question`: the concrete question or problem that gives the lesson a reason to exist;
- `key_analogy`: one concise analogy or physical picture if it genuinely clarifies the mechanism; use an empty string when no analogy is warranted;
- `likely_misconceptions`: the most important source-supported learner confusions to resolve;
- `narrative_arc`: three to six short stages describing the conceptual progression;
- `visual_strategy`: two to six visual forms that best support those stages.

Do not use analogy as entertainment. An analogy must illuminate structure without adding unsupported physics.

## 5. Mandatory self-learning lesson architecture

Every LLM-planned video must reserve enough slide capacity for:

1. an opening introduction that motivates and orients the learner;
2. coherent concept development;
3. at least one conceptual or reasoning check;
4. a final conclusion that synthesizes what the learner should now understand or be able to do.

Therefore every planned video must have `max_slides >= 5`.

For ordinary structured DOCX/PDF sources, the first generated slide should normally be `introduction` and the final slide `conclusion`.

For textbook-subchapter sources, preserve the stricter minimum architecture: `title` -> `introduction` -> concept development -> `check` -> `conclusion`.

The introduction should not begin with an administrative agenda. Prefer a concrete problem, observation, practical consequence, or discriminating question. The conclusion must synthesize rather than merely repeat a list and must not introduce new content.

## 6. Concept map

Create a concise concept map for the entire source. For each major concept identify supporting source block IDs and prerequisite concepts. This map is supplied to every later lesson-generation call.

## 7. Video plan fields

For every planned video provide:

- stable video ID in sequence (`V01`, `V02`, ...);
- concise instructional title;
- focus or purpose;
- realistic target duration and maximum slide count;
- learning outcomes;
- `opening_question`;
- `narrative_arc`;
- `key_analogy`;
- `likely_misconceptions`;
- `visual_strategy`;
- one useful conceptual check question;
- up to three takeaways;
- authoritative `core_block_ids`;
- optional `reference_block_ids`;
- prerequisite video IDs;
- `already_taught` concepts;
- `forward_links` for later lessons.

## 8. Coverage discipline

Do not feel obliged to put administrative boilerplate, table-of-contents text, duplicated wording, or reference checklists into a video. However, substantive concepts, assumptions, equations, worked examples, limitations, and interpretation must not disappear merely because they do not align with a section boundary. Use `coverage_notes` to explain intentionally omitted or reference-only material.

## 9. Textbook-subchapter planning mode

When `source_document.classification.kind` is `textbook_subchapter`, the ingestion layer has already scoped the intended numbered subchapter. Treat the supplied blocks as the complete authoritative scope. Do not restore or plan from adjacent sections that were excluded during ingestion.

For a short self-contained subchapter, prefer one coherent video unless conceptual density genuinely requires more than one. The check question should strengthen conceptual understanding rather than test recall. Cover the substantive ideas, equations, examples, cautions, figures, and interpretations of the scoped subchapter without importing unsupported material.

When `source_document.available_figures` is non-empty, treat those figures as authoritative source context rather than decoration. Plan a figure-centered explanation when a supplied figure is central to understanding, and reduce text density accordingly. Do not request external images or substitute stock imagery.

Return only JSON conforming to the supplied schema.
