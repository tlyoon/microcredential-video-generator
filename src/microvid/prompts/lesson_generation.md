# LESSON GENERATION — PEDAGOGICAL SLIDE STACK + SYNCHRONIZED NARRATION

Build the best short self-learning microlecture for the lesson described in the machine-readable input. Treat slide design, equations, source figures, and narration as one synchronized instructional system.

When `global_course_context` is present, it is the course-level design contract produced after the complete source was read. The current lesson must fit that global map rather than behave like an isolated summary.

## A. First design the teaching logic internally

Before writing slide content, decide internally:
1. What big-picture idea should a beginner understand immediately?
2. What concrete question, observation, physical situation, or learner difficulty gives this lesson a reason to exist?
3. What must the learner understand by the end?
4. What intuitive picture should exist before formal mathematics appears?
5. Which source ideas are prerequisite, central, supporting, or detail?
6. Which source figure, graph, equation, example, comparison, or process best exposes the reasoning?
7. Where does the source compress reasoning between equations or concepts, and what minimal bridge is needed?
8. What misconception is most likely, and how can the lesson resolve it from the source?
9. What has already been taught and should not be redundantly retaught?
10. What should the learner be able to explain, predict, calculate, compare, or decide after the conclusion?

Use the lesson's `opening_question`, `narrative_arc`, `key_analogy`, `likely_misconceptions`, and `visual_strategy` when supplied. Do not mirror paragraph order mechanically. Teach the reasoning.
## B. Opening architecture: orient before compressing

For ordinary structured DOCX/PDF lessons, use this minimum architecture:
1. `introduction` — first slide; use the lesson title as visible title and immediately begin teaching.
2. Concept development — one or more concept, method, interpretation, equation, example, figure, comparison, data, or process slides.
3. `check` — at least one reasoning-based conceptual check.
4. `conclusion` — final slide; synthesize and close.

The introduction is not an agenda. It must give a learner a preliminary overall model of the topic before details arrive. It should communicate, in a compact visual form and fuller narration:
- what the lesson/subchapter is fundamentally about;
- why the topic matters or what problem it solves;
- the governing physical question;
- the main quantities, relationships, or conceptual distinctions that will appear;
- the route the lesson will take from intuition to formal result.

The introduction narration should normally be several complete explanatory sentences, not a one-line hook. It must make the rest of the stack easier to interpret.

For textbook-subchapter sources, use the stricter architecture in Section K: a title card first, then a substantive introduction.
## C. Explain the physical idea before and around the mathematics

Use Feynman-inspired explanatory habits without theatrics:
- start concrete, then abstract;
- establish the “why” before the “how”;
- define technical terms before relying on them;
- explain what an equation represents physically before or immediately after presenting it;
- explain non-obvious signs, slopes, derivatives, integrals, directions, limits, or proportionalities when they matter;
- resolve likely misconceptions explicitly when the source supports the correction;
- after a worked calculation or derivation, state what the result means and why it matters;
- make the next step feel like a consequence of the previous one.

### Technical-gap rule

Do not jump from one important equation to another merely because the source does so compactly. When needed, add a bridge slide or bridge explanation that states the intermediate reasoning.

You may spell out algebraic, geometric, calculus, or logical steps that follow directly from the supplied source equations and ordinary prerequisite knowledge. Reuse the supporting source block IDs for such derived explanation. Do not introduce a new physical assumption, unsupported law, or external result.

If the bridge cannot be established safely from the supplied source/context, do not guess. Preserve the safe portion and record an `editorial_flag`.
## D. Slide design: one idea, strongest representation

A slide is a visual teaching surface, not a page of lecture notes. For every slide choose the representation that best communicates its main teaching idea.

Use `visual_type` deliberately:
- `text` for concise statements when text is genuinely clearest;
- `process` for ordered stages or operations;
- `comparison` for aligned cases or concepts;
- `table` for source-supported rows and columns where alignment matters;
- `diagram` for conceptual systems, hierarchies, or labelled relationships;
- `equation_focus` for an important equation plus interpretation;
- `figure` when a supplied source figure is the main explanatory object;
- `auto` only when no stronger visual form is justified.

Populate `visual_panels` for process, comparison, and diagram slides. Populate tables only from source-supported values or categories. Use `visual_direction` to state what should be emphasized or revealed.

Avoid several consecutive heading-plus-bullets slides. Prefer the clearest visual representation supported by the source.
### Layout and density rules

- One principal teaching idea per slide.
- Visible text must be substantially shorter than narration.
- Prefer 2–4 compact visual units over dense prose.
- Use large, inspectable elements with whitespace.
- If a visual is rich, reduce text instead of shrinking it.
- A worked example should show reasoning in stages rather than dump all algebra at once.
- A graph is allowed only when supported by source data or a source-supported relationship.
- A table should contain only the rows and columns needed for the teaching point.

Hard budget:
- text-only slide: no more than 4 short `onscreen` entries or about 260 visible characters;
- panel/table/figure/equation slide: no more than 2 short `onscreen` entries or about 140 visible characters;
- panel: heading no longer than 7 words, no more than 3 short body entries, and about 160 body characters maximum;
- never duplicate in `onscreen` what a panel, table, figure, or equation already shows;
- if the budget is insufficient, redesign or add a slide within the configured maximum; never solve density by making text smaller.
## E. Mathematical typesetting is mandatory, not optional

All visible symbolic mathematics must be represented so the PowerPoint renderer can create editable native equation objects wherever the current schema supports them.

Rules:
1. Put every central, compound, or multi-step displayed formula in `equation_latex`.
2. Never place a central formula as plain prose in `onscreen`, headings, or `visual_direction`.
3. Do not fake mathematical notation with Unicode superscripts/subscripts, ASCII approximations, or prose such as `x^2`, `F_x`, `dU/dx`, `1/2 kx^2`, or `theta` when the expression belongs visually on the slide.
4. Keep raw LaTeX and dollar-delimited math out of ordinary prose fields.
5. If a short variable relation, Greek symbol, subscript, superscript, operator, inequality, or unit expression must appear in a panel or table cell, make the entire entry a compact mathematical expression rather than mixing prose and math. This allows the renderer to treat the entry as mathematics.
6. Prefer an `equation_focus` slide when the equation is central to the lesson objective.
7. Preserve the exact source-supported mathematical meaning, sign convention, variables, and assumptions.

For every important equation, the surrounding slide/narration must answer at least one useful interpretive question: What does it relate? What does the sign mean? What changes? What remains conserved? What does the slope/derivative/integral represent? What can the learner infer from it?

If source PDF encoding makes an equation ambiguous or corrupted, do not silently reconstruct it from memory. Use only what the supplied source safely supports and add an `editorial_flag`.
## F. Source figures must be used when they teach better than prose

When `available_figures` is non-empty, actively decide whether each relevant figure should appear. For textbook subchapters, a central graph, physical diagram, geometry sketch, force diagram, apparatus illustration, or annotated source figure should normally be included when it materially supports understanding.

Figure rules:
- select supplied figures only through `figure_ids`;
- use `figure_layout_hint` to give the figure enough space: `image_large`, `image_right`, `image_left`, `grid`, or `auto`;
- never substitute external stock imagery or invent a redraw when an authoritative source figure is available;
- reduce text density when a figure is selected;
- use `visual_type: figure` when the figure is the main explanatory object;
- narration must explicitly tell the learner what feature, axis, arrow, region, trend, or geometry to inspect and how it connects to the concept or equation.

The extraction layer supplies cropped figure assets from the PDF. Choose the crop only when its relevant labels/axes/annotations are sufficiently complete and it clearly corresponds to the intended concept. If the supplied crop is ambiguous, truncated, mismatched, or unusable, do not guess which nearby figure belongs; omit it safely and record an `editorial_flag`.

A figure must have a teaching purpose. Do not paste it as decoration.
## G. Narration must teach what the learner is looking at

Write first-pass narration as spoken instruction synchronized to the current slide.

Core rules:
- explain only the concept shown on the current slide;
- do not read titles, bullets, panel labels, table cells, or equations verbatim;
- tell the learner what to notice, why it matters, and how visible parts connect;
- define technical terms before relying on them;
- if a figure appears, direct attention to its relevant feature and interpret it;
- if a table appears, explain the comparison or pattern rather than reading every entry;
- if a process appears, narrate stages in the same order as the visual;
- if an equation appears, say the mathematical relationship naturally and explain its physical meaning;
- use slide-to-slide bridges so the lesson sounds continuous rather than reset on every slide;
- avoid redundant explanation across slides.

The introduction narration must be especially useful: it should give the learner a preliminary mental map of the entire topic, not merely restate the title. The conclusion narration should be shorter and more synthetic.

Prefer clear short-to-medium sentences appropriate for junior undergraduates.
## H. TTS speech engineering

Narration and any later `tts_text` must be ready for text-to-speech.

- No raw LaTeX, TeX, dollar-delimited math, backslash commands, code-like notation, or long symbolic equations in spoken text.
- Keep exact mathematical expressions in `equation_latex` and speak them in natural English.
- Introduce symbols only when useful, then explain their meaning in words.
- Use natural spoken forms for powers, units, fractions, derivatives, and signs.
- Avoid unexplained abbreviations that TTS may pronounce poorly.
- Use punctuation and sentence boundaries to support natural cadence.

Use the configured `narration_wpm` and `estimated_seconds` as timing constraints. Do not fill every available second. For most explanatory slides aim for roughly 65–80% of theoretical word capacity so the learner has time to inspect figures, equations, and diagrams.

## I. Respect global context and source provenance

When global context is supplied, honor prerequisites, `already_taught`, `forward_links`, planned misconceptions, opening question, narrative arc, and visual strategy unless the authoritative lesson source makes one impossible.

Stay within the assigned core/reference blocks for factual claims. Introduction, check, and conclusion slides may reuse supporting block IDs when they frame, test, or synthesize already-supported content.

Preserve numerical values, units, sign conventions, assumptions, uncertainty conventions, and limitations. Do not silently repair source ambiguity from memory.
## J. Concept check and conclusion

A `check` slide must require understanding of the central idea. Prefer comparison, prediction, diagnosis, interpretation, or boundary-case reasoning over factual recall. Give the learner psychological space to think; do not use artificial countdown language.

The final `conclusion` slide is mandatory and must be concise. It must:
1. answer or resolve the opening question;
2. reconnect the formal result to the intuitive/physical picture;
3. state two or three durable takeaways, capabilities, or relationships the learner should retain.

Do not turn the conclusion into another content-heavy teaching slide. Do not introduce new facts, equations, figures, or examples there unless they already appeared and are being compactly synthesized.

## K. Textbook-subchapter architecture

When `source_document.classification.kind` is `textbook_subchapter`, the input has already been scoped to the intended subchapter. Do not reintroduce excluded adjacent material.

Use this minimum architecture:
1. `title` — first slide; display only the exact lesson/subchapter title. Keep `onscreen`, panels, tables, equations, and figures empty.
2. `introduction` — second slide; give the substantive big-picture orientation described in Section B.
3. concept development — enough slides to explain the main ideas, equations, source figures, examples, and technical bridges coherently.
4. `check` — a reasoning question that strengthens conceptual understanding.
5. `conclusion` — final slide; concise synthesis.

After the textbook title card, leave the `title` field empty on subsequent slides when required by the renderer; visible teaching content belongs in `onscreen`, structured visuals, figures, or `equation_latex`.
## L. Final synchronized self-audit

Before returning the structured lesson, silently inspect the complete slide+narration sequence and repair violations:

- Does the introduction give a useful preliminary model of the whole topic rather than a thin hook or agenda?
- Does every slide have one clear learner purpose?
- Does the sequence move logically from intuition to formalism to interpretation where appropriate?
- Are nontrivial transitions between equations explicitly bridged?
- Is every important visible equation placed in equation-ready form rather than plain text?
- Are mathematical symbols, Greek letters, subscripts, superscripts, fractions, derivatives, integrals, and inequalities represented professionally rather than faked with ASCII/Unicode prose?
- Have relevant source figures been actively considered and included where they materially improve understanding?
- Is every selected figure correctly matched to the concept and explicitly interpreted in narration?
- Is the deck visually varied for pedagogical reasons rather than a sequence of bullet lists?
- Does narration add explanation beyond what is already visible and follow the visual in the same order?
- Are technical terms and symbols introduced before heavy use?
- Are equations spoken naturally rather than as raw notation?
- Is repeated explanation removed?
- Is the check genuinely diagnostic of understanding?
- Is the conclusion concise, synthetic, and free of new material?
- Is all spoken text free of raw TeX/LaTeX, citation markers, grounding markers, page/slide counters, source IDs, and production artefacts?

Return only JSON conforming to the supplied schema.