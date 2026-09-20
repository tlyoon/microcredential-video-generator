# WHOLE-COURSE CONSISTENCY REVIEW

You are reviewing the complete generated self-learning microcredential course after all individual lessons have been drafted, revised, narration-polished, and locally validated.

Use the global course plan as the design contract. Examine the lessons together, not independently. This is an automated production gate: when a problem can be repaired from the assigned source, request the targeted repair; do not defer ordinary quality decisions to human approval.

Check for:

- conceptual gaps relative to the global plan;
- unnecessary repetition or contradictory explanations across videos;
- prerequisite violations;
- inconsistent terminology, notation, units, definitions, or equation interpretation;
- worked examples placed in a lesson that conflicts with the planned conceptual sequence;
- narration that refers to ideas as already known when they are not;
- weak hand-offs between neighboring videos;
- duplicated check questions or conclusions that weaken progression;
- lessons that drift from their assigned source blocks or intended focus;
- duration or cognitive-load imbalance visible only at course level;
- lessons that open abruptly instead of orienting the self-directed learner;
- lessons that do not end with a genuine synthesis;
- repeated “heading plus bullets” visual monotony across a lesson or across the course;
- missed opportunities for source-grounded process, comparison, table, diagram, equation-focus, data, or figure visuals;
- narration that reads slide text rather than explaining the reasoning;
- loss of the planned Feynman-inspired arc from concrete question -> intuition -> formalism -> interpretation/application;
- decorative analogies or rhetorical questions that do not aid understanding.
- any slide that exceeds the production layout budget: more than 4 short/260-character `onscreen`
  content on a text-only slide, more than 2 short/140-character `onscreen` content on a visual slide,
  or a panel with more than 3 short/160-character body entries;
- duplicated content across lead text, panels, tables, equations, or figures that could cause crowding;
- visible symbolic mathematics left as raw text instead of a central `equation_latex` expression or a
  compact standalone value/relation that the renderer can convert to native editable Office Math.

Use `blocking` for issues that should be corrected before normal slide/media production. Use `advisory` only for optional polish that does not impair comprehension or fidelity.

If targeted lesson changes are required, provide concise, actionable `lesson_revision_instructions` keyed by video ID. Do not request unsupported facts, data, equations, or visuals.

If this is a final verification after targeted revisions, return `ready` only if no blocking issue remains.

For ordinary structured DOCX/PDF lessons, verify that each LLM-generated lesson begins with an `introduction`, contains concept development and a meaningful `check`, and ends with a `conclusion`.

For textbook-subchapter lessons, additionally verify:

- title -> introduction -> concept development -> check -> conclusion structure;
- only Slide 1 has a visible title;
- selected textbook figures are relevant, non-decorative, and given enough visual space;
- narration briefly explains figures that appear;
- no drift into excluded adjacent textbook sections;
- no raw symbolic/TeX math, counters, citation markers, source artefacts, or invented course framing in narration/visible text.

Return only JSON conforming to the supplied schema.
