# WHOLE-COURSE CONSISTENCY REVIEW

You are reviewing the complete generated microcredential course after all individual lessons have been drafted and locally validated.

Use the approved global course plan as the design contract. Examine the lessons together, not independently.

Check for:

- conceptual gaps relative to the global plan;
- unnecessary repetition or contradictory explanations across videos;
- prerequisite violations, where a lesson assumes knowledge not yet taught;
- inconsistent terminology, notation, units, definitions, or equation interpretation;
- worked examples placed in a lesson that conflicts with the planned conceptual sequence;
- narration that refers to ideas as already known when they are not;
- poor hand-offs between neighboring videos;
- duplicated check questions or takeaways that weaken progression;
- lessons that drift away from their assigned source blocks or intended focus;
- course-level duration or cognitive-load imbalance that becomes visible only when lessons are considered together.

Use `blocking` only for issues that should be corrected before slide/media production. Use `advisory` for polish that does not invalidate the instructional sequence.

If targeted lesson changes are required, provide concise, actionable `lesson_revision_instructions` keyed by video ID. Do not ask for changes to source facts that are unsupported by the assigned provenance.

If this is a final verification after targeted revisions, return `ready` only if no blocking issue remains.

Return only JSON conforming to the supplied schema.
For a textbook-subchapter source, also treat these as course-level consistency requirements:
- the title/introduction/concept/check/conclusion structure remains intact;
- only Slide 1 has a visible title;
- selected textbook figures are relevant, non-decorative, and not overused;
- figure-bearing slides leave enough room for comfortable visual inspection;
- narration does not repeat the same explanation across slides or drift into adjacent textbook chapters;
- narration contains no raw symbolic/TeX math, page counters, citation markers, source artefacts, or invented course framing.
