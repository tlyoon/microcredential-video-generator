# GLOBAL COURSE PLAN REVIEW — SECOND PASS

Review the first global course plan against the complete structured source document. Return a complete revised course plan, not comments about the old plan.

Check especially:

- whether the plan demonstrates understanding of the whole source rather than mechanically following section boundaries;
- whether foundational concepts appear before dependent concepts;
- whether related material separated in the document has been brought together where pedagogically useful;
- whether worked examples are attached to the lessons where they best support understanding;
- whether important assumptions, equations, limitations, and reporting conventions have been lost;
- whether source blocks are duplicated across lessons without a clear pedagogical reason;
- whether substantive blocks omitted from all lessons are genuinely reference-only or administrative;
- whether each lesson is cognitively manageable for the configured audience and duration;
- whether the sequence minimizes unnecessary repetition while preserving useful reinforcement;
- whether every `core_block_id` and `reference_block_id` is grounded in the supplied source;
- whether `already_taught`, prerequisite relationships, and forward links accurately reflect the planned sequence.

Use the local QA findings as evidence to reconsider omissions or duplicate assignments. Do not blindly eliminate a flagged duplication if repetition is pedagogically justified; instead make the plan's intent clear.

Return only a complete JSON object conforming to the same course-plan schema.