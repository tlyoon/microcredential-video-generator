# LESSON GENERATION TASK — SELF-LEARNING SLIDE STACK + SYNCHRONIZED NARRATION

Build the best short self-learning microlecture for the lesson described in the machine-readable input. Treat slide design and narration as one synchronized instructional system.

When `global_course_context` is present, it is the course-level design contract produced after the complete source was read. The current lesson must fit that global map rather than behave like an isolated summary.

## A. First plan the teaching logic internally

Before writing slide text, decide internally:

1. What concrete question, observation, problem, or learner difficulty gives this lesson a reason to exist?
2. What must a beginner understand by the end?
3. What intuitive picture should exist before formal mathematics appears?
4. Which source ideas are prerequisite, which are central, and which are detail?
5. Which example, contrast, table, equation, graph, diagram, or decision best exposes the reasoning?
6. What misconception is most likely, and how can the lesson resolve it from the source?
7. What has already been taught and should not be retaught?
8. What later lesson depends on this one?
9. What should the learner be able to explain, predict, calculate, compare, or decide after the conclusion?

Use the lesson's `opening_question`, `narrative_arc`, `key_analogy`, `likely_misconceptions`, and `visual_strategy` when supplied by the global plan.

Do not mirror the source document's paragraph order mechanically. Teach the reasoning.

## B. Mandatory architecture for ordinary structured DOCX/PDF lessons

Unless the source is a textbook subchapter with its stricter rules below, every LLM-generated lesson must use this minimum self-learning architecture:

1. **Introduction** — first slide, `slide_type: introduction`. Use the lesson title as its visible title. Motivate the concept with a concrete question, physical or experimental situation, consequence, or learner problem. Orient the learner to the central idea without an administrative agenda.
2. **Concept development** — one or more concept, method, interpretation, worked-example, comparison, equation, data, or process slides arranged in causal/logical order.
3. **Concept check** — at least one `slide_type: check` that tests reasoning, discrimination, prediction, interpretation, or application rather than recall.
4. **Conclusion** — final slide, `slide_type: conclusion`. Reconstruct the central idea, connect formalism back to intuition, and state what the learner should now be able to do. Introduce no new substantive content.

A typical lesson contains 5–8 slides within the configured maximum. Do not insert a separate title-only slide for an ordinary structured document unless the source/profile explicitly requires it; the opening introduction should immediately begin teaching.

## C. Feynman-inspired explanation without theatrics

Use Feynman-inspired explanatory habits:

- Start concrete, then abstract.
- Establish the “why” before the “how”.
- Define technical terms before relying on them.
- Use a small number of purposeful rhetorical questions to focus reasoning.
- Use one memorable analogy or physical picture only when it genuinely clarifies the structure.
- Before or immediately after an equation, explain what relationship or conservation statement the equation represents physically.
- If a mathematical rule has a non-obvious form, explain the reason or interpretation supported by the source rather than merely reciting the rule.
- Resolve likely misconceptions explicitly when the source supports the correction.
- After a worked calculation, state what the result means and why it matters.
- Make the learner feel the next step is a natural consequence of the previous one.

Do not imitate personality quirks, add jokes for their own sake, or embellish the source with unsupported anecdotes. Clarity is the style.

## D. Slide design: visuals before prose

A slide is a visual teaching surface, not a page of lecture notes. For every slide choose the representation that best communicates the one main idea.

Use `visual_type` as follows:

- `text` — only when concise labels or statements are genuinely the clearest representation;
- `process` — a sequence of stages, operations, or decisions;
- `comparison` — two or more aligned alternatives, cases, or concepts;
- `table` — source-supported rows/columns where alignment matters;
- `diagram` — a conceptual system, causal relationship, hierarchy, or labelled parts;
- `equation_focus` — an important equation plus a compact interpretation of terms or consequences;
- `figure` — supplied textbook/source figure is the main explanatory object;
- `auto` — only when no stronger visual form is justified.

Populate `visual_panels` for process/comparison/diagram slides. Each panel should contain a short heading and a few compact lines. Populate `table_headers` and `table_rows` only from source-supported values or categories. Do not invent data.

Use `visual_direction` to state what should be emphasized, compared, highlighted, or revealed in sequence. It is not a place for vague decorative requests.

### Visual design rules

- One principal teaching idea per slide.
- Visible text should normally be much shorter than narration.
- Prefer 2–4 short visual units over a dense list.
- Use large, inspectable elements with whitespace.
- Avoid several consecutive “heading + bullets” slides; if the concept supports a diagram, process, comparison, table, equation focus, or figure, use it.
- A graph is appropriate only when source data or a source-supported relationship is available. Do not fabricate points or trends.
- A table should be reduced to the rows and columns needed for the teaching point.
- An equation slide should visually separate the formal relationship from its physical interpretation.
- A worked example should show the reasoning in stages, not dump all algebra at once.
- If a visual is rich, reduce text rather than shrinking everything.
- Do not request external stock photography or decorative icons as substitutes for explanation.

Hard layout budget:

- text-only slide: no more than 4 short `onscreen` entries or 260 visible characters;
- panel/table/figure/equation slide: no more than 2 short `onscreen` entries or 140 visible characters;
- panel: heading no longer than 7 words, no more than 3 short body entries, and no more than 160 body characters;
- never duplicate in `onscreen` what the panels, table, figure, or equation already shows;
- if the budget is insufficient, add or redesign a slide within the configured slide limit; never solve it by producing smaller text.

## E. Narration must be synchronized to the visual

Write the first-pass narration as concise spoken teaching that explains what the learner is currently looking at.

Core rules:

- Explain only the concept shown on the current slide.
- Do not read the title, bullets, panel labels, or table cells verbatim.
- Tell the learner what to notice, why it matters, and how the visible parts connect.
- Define technical terms before relying on them.
- If a figure appears, briefly describe the relevant feature and connect it to the concept.
- If a table appears, direct attention to the comparison, pattern, or decision rather than reading every entry.
- If a process appears, narrate it in the same order as the visual stages.
- If a formula appears, express it in natural spoken English and explain what the quantities or groups of terms mean.
- Avoid repeating the same explanation across slides.
- Use natural slide-to-slide bridges so the narration forms one continuous explanation.
- Keep transitions purposeful; do not force every slide to begin with “Now” or end with a teaser.
- Use occasional direct questions when they genuinely help reasoning.
- Do not mention material from other chapters, slide decks, conversations, or general knowledge unless grounded in the current source/context.

Narration should be precise, concise, completely comprehensible, and suitable for a junior undergraduate learner. Prefer clear short-to-medium sentences over ornate prose.

## F. TTS speech engineering

Narration and `tts_text` must be ready for text-to-speech.

- No raw LaTeX, TeX, dollar-delimited math, backslash commands, code-like notation, or long symbolic equations in spoken text.
- Keep exact mathematical expressions in `equation_latex`.
- Rewrite every spoken mathematical relationship into natural English.
- Introduce symbols only when useful, then explain their meaning in words.
- Write powers and units naturally, for example “ten to the sixth metres per second” rather than exposing symbol syntax.
- Use commas, dashes, and sentence boundaries to support natural cadence; do not overuse ellipses or dramatic punctuation.
- Avoid unexplained abbreviations that TTS may pronounce poorly.

Use the configured `narration_wpm` and `estimated_seconds` as timing constraints. Do not fill every available second. Leave room for visual inspection, equations, graphs, and thinking pauses. For most explanatory slides, aim for roughly 65–80% of theoretical word capacity. Checks and conclusions may be shorter.

## G. Respect the global course plan

When global context is supplied:

- use the course summary and concept map to interpret this lesson's role;
- honor prerequisites and `already_taught` concepts;
- avoid redundant reteaching;
- do not pull later material forward prematurely;
- use `forward_links` only as a conceptual hand-off, not as an excuse to teach future content;
- stay within the assigned authoritative core/reference blocks for factual claims;
- preserve the globally planned opening question, narrative arc, misconception strategy, and visual strategy unless the source packet proves one of them impossible.

## H. Source provenance and technical fidelity

Every concept, method, worked-example, data, comparison, or interpretation slide must list the source blocks that directly support it. Introduction/check/conclusion slides may reuse source IDs when they restate source-supported content; they may be empty only when they purely frame or test already-supported material.

Preserve numerical values, units, sign conventions, uncertainty conventions, assumptions, and limitations. Do not silently repair source ambiguity from memory. If an ambiguity materially affects correctness, record it in `editorial_flags`; automated production may continue only when the lesson itself remains correct without guessing.

## I. Mathematical material

Use `equation_latex` only for a source-supported equation. Do not alter a formula to make it prettier. Use an `equation_focus` layout when the equation is central to the learning objective; otherwise keep it subordinate to the concept.

All visible symbolic mathematics must be rendered in native equation mode. Put every central, compound,
or multi-step formula in `equation_latex`, never in prose. Keep raw LaTeX and dollar-delimited math out of
`onscreen`, panel text, headings, and tables. If a short source-supported value, unit expression, variable
relation, Greek symbol, subscript, superscript, operator, or inequality belongs in a panel or table cell,
make it a compact standalone entry so the renderer can convert that whole entry to editable Office Math.
Do not fake notation with Unicode superscripts/subscripts or plain-text equation strings.

Narration should explain what the equation lets the learner infer: what changes, what is conserved, what contributions combine, what dominates, what cancels, or what decision follows.

## J. Checks and conclusion

A check slide should ask a question that requires understanding of the central idea. Prefer comparison, prediction, diagnosis, or boundary-case reasoning over factual recall. Give the learner psychological space to think. Do not use artificial countdown language.

The conclusion slide must do three things economically:

1. answer the opening question or resolve the motivating problem;
2. reconnect the mathematical/formal result to the intuitive picture;
3. state two or three durable takeaways or capabilities.

Do not add new facts on the conclusion slide.

## K. Textbook-subchapter architecture and figures

When `source_document.classification.kind` is `textbook_subchapter`, the input has already been scoped to the intended subchapter. Do not reintroduce excluded adjacent material.

Use this minimum architecture:

1. `title` — first slide; display only the exact lesson/subchapter title. `onscreen`, `visual_panels`, table fields, and figures must be empty.
2. `introduction` — second slide; establish the central physical question, why it matters, and the conceptual route.
3. concept development — one or more source-grounded concept/method/example/interpretation slides.
4. `check` — a reasoning question that strengthens conceptual understanding.
5. `conclusion` — final slide; synthesize the subchapter.

Slides after the textbook title slide must use an empty `title` field; visible teaching content belongs in `onscreen`, visual structures, figures, or `equation_latex`.

When `available_figures` is non-empty:

- include a relevant supplied textbook figure when it materially improves explanation;
- select figures only by supplied `id` in `figure_ids`;
- never invent, redraw, or substitute external imagery for a supplied figure;
- use `figure_layout_hint` as a soft suggestion: `image_large`, `image_right`, `image_left`, `grid`, or `auto`;
- reduce on-screen text when the figure is visually rich;
- narration must briefly describe what the learner should notice in the figure.

If source PDF text encoding makes an equation ambiguous or corrupted, do not silently repair it from memory. Use only what can be supported by the supplied source and retain an explicit flag.

## L. Final synchronized self-check

Before returning the structured lesson, silently inspect the complete slide+narration sequence and repair violations:

- Does the lesson begin naturally rather than abruptly?
- Does every slide answer one clear learner question?
- Is there a logical progression from intuition to formalism to interpretation where appropriate?
- Is the deck visually varied for pedagogical reasons rather than a sequence of bullet lists?
- Could any dense text be replaced by a process, comparison, table, diagram, equation focus, or source figure?
- Is every visual source-grounded and large enough to inspect?
- Does narration add explanation beyond what is already visible?
- Does narration follow the visual in the same order?
- Are technical terms defined before use?
- Are equations spoken naturally rather than as raw notation?
- Is repeated explanation removed?
- Is the check genuinely diagnostic of understanding?
- Does the conclusion resolve the lesson without introducing new material?
- Is all spoken text free of raw TeX/LaTeX, citation markers, grounding markers, page counters, slide counters, source IDs, and production artefacts?

Return only JSON conforming to the supplied schema.
