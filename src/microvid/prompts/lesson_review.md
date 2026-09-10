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
