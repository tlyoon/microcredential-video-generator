# GLOBAL COURSE PLANNING — WHOLE-SOURCE PEDAGOGICAL DESIGN

You are planning the complete self-learning microcredential course before any individual slide deck is written.

Read the complete structured source as one coherent document. Understand its conceptual structure, dependencies, repeated ideas, worked examples, equations, figures, cautions, misconceptions, data, tables, and interpretation before deciding lesson boundaries. Do not mechanically turn pages or headings into videos.

## 1. Planning priorities

1. Build a coherent mental model of the entire source before segmenting it.
2. Identify foundational concepts and prerequisite relationships.
3. Group source blocks pedagogically even when they are separated in the document.
4. Keep worked examples with the concepts they illuminate and preserve complete reasoning chains.
5. Merge short or repetitive sections when one stronger lesson gives a better conceptual arc.
6. Split conceptually dense material when one lesson would overload a self-directed learner.
7. Avoid reteaching the same idea unless deliberate reinforcement is educationally justified.
8. Preserve the source as the authority; do not invent subject matter, numerical data, equations, source IDs, or external figures.
9. Assign explicit `core_block_ids` to each video and use `reference_block_ids` only for useful supporting detail.
10. Treat duration and slide limits as design constraints, not excuses to omit essential reasoning.
11. Make the course cumulative: record prerequisites, what is already taught, and what later lessons build upon.
12. Prefer a small number of coherent lessons over fragmented coverage.
## 2. Plan a teaching story, not a topic list

For every planned video, design a deliberate instructional arc. The learner should be able to see why the topic matters, how the ideas connect, and where the formal mathematics fits.

Use this sequence when the source supports it:
- begin with a concrete physical question, observation, consequence, or learner difficulty;
- give a big-picture orientation before details;
- establish the intuitive or physical model;
- introduce formal mathematics only after its purpose is clear;
- explain what each important equation means physically;
- bridge nontrivial transitions between equations or ideas;
- use a worked example, figure, graph, comparison, or decision when it advances understanding;
- test the central distinction with a conceptual check;
- finish with a concise synthesis.

Do not force every phase into a separate slide, but make the logic explicit in `narrative_arc`.

The first substantive teaching slide must not be a thin agenda. It must orient the learner to the whole lesson: what the topic is about, the governing question, the important quantities or relationships, and the route the lesson will take.

The final slide must be a true conclusion: resolve the opening question, reconnect formalism to intuition, and state the two or three most durable takeaways. It must not introduce new content.
## 3. Mathematical continuity and technical bridges

Plan enough slide capacity for the mathematics to be understandable rather than merely displayed.

When the source moves from one equation to another with compressed reasoning, preserve the source result but plan a bridge that makes the transition intelligible. A bridge may explain:
- which definition, conservation statement, derivative, algebraic substitution, limiting case, or sign convention is being used;
- why the next expression follows;
- what changes physically and what remains invariant;
- what a slope, derivative, integral, proportionality, negative sign, vector direction, or boundary condition means.

You may spell out intermediate algebra/calculus/logic that follows directly from the supplied source and ordinary prerequisites. Do not introduce a new physical assumption or unsupported result. If a safe bridge cannot be made from the source/context, preserve the ambiguity and flag it.

Plan equation-centered slides when a formula is central. Do not plan dense prose around an important equation. Where several equations form one reasoning chain, allocate enough slides or stages to make the chain readable.

## 4. Visual strategy and source figures

The course must not look like static lecture notes. For each video identify two to six useful visual forms in `visual_strategy`: source figure, labelled conceptual diagram, process flow, comparison, reduced source table, source-supported graph, equation focus, or staged worked example.

When `source_document.available_figures` is non-empty, actively inspect whether a supplied figure is pedagogically important. For textbook subchapters, include relevant source figures whenever they materially improve understanding; do not omit a central graph or diagram merely to simplify production.
For each important source figure, plan what the learner should notice and which equation or concept it supports. Prefer a figure-centered explanation over duplicating the same information in bullets. Never request external stock imagery or invent a replacement for an authoritative source figure.

Use visual variety only when it improves comprehension. Avoid several consecutive title-plus-bullets slides. If a concept can be understood faster through a figure, graph, diagram, comparison, process, compact table, or equation focus, plan that representation instead.

## 5. Mandatory lesson architecture

Every LLM-planned video must reserve enough slide capacity for:
1. an opening introduction that motivates and orients the learner;
2. coherent concept development with sufficient technical bridges;
3. at least one conceptual or reasoning check;
4. a concise final conclusion.

Therefore every planned video must have `max_slides >= 5`.

For ordinary structured DOCX/PDF lessons, the first generated slide should normally be `introduction` and the final slide `conclusion`.

For textbook-subchapter sources, preserve the stricter architecture: `title` -> `introduction` -> concept development -> `check` -> `conclusion`.

The textbook title slide is only a visual title card. The following introduction slide must carry the substantive orientation: the topic's big idea, motivating question, key quantities/relationships, and a short conceptual roadmap.

## 6. Concept map and video plan fields

Create a concise concept map for the complete source. For each major concept identify supporting source block IDs and prerequisite concepts.

For every planned video provide the schema-required fields faithfully, including `opening_question`, `narrative_arc`, `key_analogy`, `likely_misconceptions`, `visual_strategy`, `check_question`, `takeaways`, authoritative block IDs, prerequisites, already-taught concepts, and forward links.
## 7. Coverage discipline

Do not put administrative boilerplate, contents text, duplicated wording, or reference-only material into a video merely for completeness. However, substantive concepts, assumptions, equations, worked examples, figures, limitations, and interpretations must not disappear because they do not align with a section boundary. Use `coverage_notes` to explain intentional omission or reference-only treatment.

## 8. Textbook-subchapter mode

When `source_document.classification.kind` is `textbook_subchapter`, the ingestion layer has already scoped the intended numbered subchapter. Treat the supplied blocks and figure assets as the complete authoritative scope. Do not restore excluded adjacent sections.

For a short self-contained subchapter, prefer one coherent video unless conceptual density genuinely requires more than one. Cover the substantive ideas, equations, examples, cautions, figures, and interpretation of the scoped subchapter without importing unsupported content.

The planned stack should read as a miniature lesson rather than a summary: orient -> explain -> bridge -> interpret -> check -> conclude.

## 9. Planning self-audit

Before returning the plan, silently verify:
- Does every lesson have a strong big-picture introduction rather than a thin agenda?
- Is enough slide capacity reserved to explain nontrivial equation transitions?
- Are important source figures deliberately assigned where useful?
- Is the visual strategy richer than repeated bullet slides?
- Is there a genuine reasoning check?
- Does the conclusion resolve the opening question and give concise durable takeaways?
- Is every substantive claim and source assignment grounded in the supplied document?

Return only JSON conforming to the supplied schema.