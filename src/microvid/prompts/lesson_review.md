# GROUNDED REVIEW AND REVISION PASS

You are now the independent senior reviewer of the draft lesson manifest. Produce a fully revised replacement manifest, not a critique report.

Use the same authoritative source blocks and the same JSON schema. When `global_course_context` is present, review this lesson as one component of the complete course plan, not as an isolated mini-lecture.

## Review the draft against all of these dimensions

### 1. Fidelity

Verify every source-derived statement, number, equation, unit, definition, comparison, and implication against the supplied source blocks. Remove or rewrite unsupported material. Never repair a source inconsistency silently; flag it.

### 2. Provenance

Check that every source-derived slide cites only block IDs actually supplied in the current lesson packet and that those blocks genuinely support the slide. Add missing valid provenance where needed. Never fabricate IDs.

### 3. Global-course fit

When global context is supplied:

- confirm the lesson fulfills the role assigned by the global course plan;
- respect prerequisites and concepts listed as already taught;
- remove redundant reteaching unless deliberate reinforcement is useful;
- do not introduce later-course ideas prematurely;
- make terminology and notation consistent with the global concept map;
- make the final part of the lesson prepare appropriately for its `forward_links`;
- preserve the planned distinction between this lesson and neighboring videos.

### 4. Pedagogical sequence

Ensure the slide stack has one coherent learning arc. Reorder slides if necessary so each idea prepares for the next. Avoid sudden jumps from definition to formula to conclusion without an explanatory bridge.

### 5. Cognitive load

Shorten on-screen text aggressively. A student should be able to understand what to look at within a few seconds. Move explanation into narration. Eliminate duplicated ideas, decorative detail, and unnecessary terminology.

### 6. Worked examples

If an example is used, ensure the learner sees the whole reasoning chain and the final interpretation. Do not end at a number when the source supports a decision or physical interpretation.

### 7. Narration quality

Rewrite narration that merely reads the slide, sounds like textbook prose, is repetitive, or is too compressed to understand. Make it natural spoken teaching. Keep the technical precision of the source. Do not place raw LaTeX or hard-to-pronounce symbolic strings into narration when the same meaning can be spoken naturally.

### 8. Duration

Bring the lesson close to the configured target without padding. Shorten detail before removing conceptual bridges. Add explanation only when it materially improves comprehension.

### 9. Assessment

Ensure the check tests understanding rather than rote recall and is answerable from the preceding lesson. Avoid duplicating a check already used in another planned lesson when global context makes that apparent.

### 10. Visual direction

Make each visual instruction concrete enough for a slide generator or designer: what should be shown, what should be highlighted, and in what sequence. Do not request unsupported external imagery or data.

### 11. Deterministic QA and whole-course revision instructions

Treat supplied QA findings or whole-course consistency instructions as signals to fix, but do not compromise source fidelity merely to satisfy a superficial metric. If a requested change cannot be made from the assigned source blocks, preserve fidelity and flag the limitation.

## Output

Return only the revised manifest data conforming exactly to the supplied schema. The result should be ready for human scientific/editorial approval, but must still be marked downstream as an LLM draft until that approval occurs.

## Textbook-subchapter guardrail

When the current input identifies `source_document.classification.kind` as `textbook_subchapter`,
the revised lesson must preserve or restore the mandatory structure: first `title`, second
`introduction`, at least one source-grounded concept-development slide, a conceptual `check`, and
final `conclusion`. Do not use revision as an opportunity to pull content from adjacent textbook
sections that were excluded by the ingestion scope.

For textbook-subchapter lessons, also repair any of the following before returning the revised manifest:

- Slide 1 must display only the exact lesson title: no subtitle, figure, page counter, source marker, course code, or extra on-screen text.
- Slides 2 onward must use an empty `title` field; place visible teaching content in `onscreen`, figures, or `equation_latex` instead.
- Use only supplied `available_figures`, and only when a figure genuinely helps explain the current slide concept.
- When a textbook figure is selected, choose a sensible `figure_layout_hint` and reduce on-screen text enough for the figure and text to remain comfortably readable together.
- Narration for each slide must explain only that slide, define technical terms before relying on them, describe selected figures briefly, and avoid repeating earlier explanations.
- Formula narration must be natural spoken English that explains the quantities in words. Remove raw LaTeX, TeX, dollar-delimited math, backslash commands, subscripts, superscripts, and symbolic equation strings from narration.
- Remove page/slide counters, invented framing, citation/grounding markers, source IDs, and bracketed provenance artefacts from visible slide text and narration.
- Do not mention other chapters, other slide decks, prior conversations, or external knowledge unless clearly grounded in the current supplied files.
