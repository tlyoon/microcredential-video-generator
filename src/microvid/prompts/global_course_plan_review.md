# GLOBAL COURSE PLAN REVIEW — SECOND PASS

Review the first global course plan against the complete structured source document. Return a complete revised course plan, not comments about the old plan.

Check especially:

- whether the plan demonstrates whole-source understanding rather than mechanically following section boundaries;
- whether foundational concepts appear before dependent concepts;
- whether related material separated in the document has been brought together where pedagogically useful;
- whether worked examples are attached to the lessons where they best support understanding;
- whether important assumptions, equations, limitations, data relationships, and reporting conventions have been lost;
- whether source blocks are duplicated across lessons without a clear pedagogical reason;
- whether omitted substantive blocks are genuinely reference-only or administrative;
- whether each lesson is cognitively manageable for the configured audience and duration;
- whether every lesson reserves enough capacity for introduction, concept development, a reasoning check, and conclusion;
- whether every `opening_question` gives the lesson a concrete reason to exist rather than sounding like an agenda item;
- whether each `narrative_arc` progresses coherently from motivation/intuitive picture to formalism/interpretation/application as appropriate;
- whether `key_analogy` is empty when no analogy is genuinely useful and source-compatible;
- whether `likely_misconceptions` identifies real conceptual risks supported by the source rather than invented straw men;
- whether `visual_strategy` uses diagrams, processes, comparisons, tables, graphs, equations, examples, or source figures only where they improve comprehension;
- whether the course would otherwise devolve into repeated heading-plus-bullets slides;
- whether the sequence minimizes unnecessary repetition while preserving useful reinforcement;
- whether every `core_block_id` and `reference_block_id` is grounded in the supplied source;
- whether `already_taught`, prerequisite relationships, and forward links accurately reflect the planned sequence.

Apply Feynman-inspired clarity as a planning criterion: each lesson should expose the question behind the formalism, build intuition before or alongside equations, and end with an interpretable conclusion. Do not add unsupported anecdotes, analogies, data, or domain facts.

Use local QA findings as evidence to reconsider omissions or duplicate assignments. Do not blindly eliminate a flagged duplication if repetition is pedagogically justified; make the intent explicit instead.

Return only a complete JSON object conforming to the same course-plan schema.
