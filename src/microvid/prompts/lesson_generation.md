# LESSON GENERATION TASK

Build the best short slide stack for the lesson described in the machine-readable input.

When `global_course_context` is present, treat it as the course-level design contract produced after Gemini read the complete source document. The current lesson must fit that global map rather than behave like an isolated summary.

## A. First decide the conceptual spine

Before choosing slide text, determine internally:

1. What must a beginner understand by the end?
2. Which source ideas are prerequisite versus detail?
3. Which single example, contrast, table, equation, or decision best exposes the reasoning?
4. What misconception is most likely?
5. What should the learner be able to decide or explain after the lesson?
6. What has already been taught in earlier planned videos and therefore should not be unnecessarily retaught?
7. What later planned videos depend on this lesson and therefore need a clean conceptual hand-off?

Then create the slide stack around that spine. Do not mirror the source document's paragraph sequence mechanically.

## B. Respect the global course plan

If global context is supplied:

- use the course summary and concept map to interpret the role of this lesson;
- honor prerequisite video IDs and `already_taught` concepts;
- avoid duplicating a previous lesson merely because the same source idea appears again;
- introduce enough foundation for the current lesson, but do not pull future material forward prematurely;
- use `forward_links` to end with the conceptual bridge later lessons need;
- stay within the assigned authoritative core/reference blocks for factual content;
- do not change the globally planned lesson scope merely because a neighboring section of the DOCX looks convenient.

## C. Balance brevity and technical completeness

Target the configured duration. Omit low-value repetition and extensive reference lists from the narrated path. However, do not omit a technical qualification when removing it would make the remaining statement misleading.

Keep slide count at or below the configured maximum. A typical short lesson has 5–7 slides. A technically dense lesson may use one additional slide if the configured limit allows it.

## D. Narration length and speech readiness

Use the configured narration rate as a timing guide. A 6-minute lesson at 130 words per minute does not require 780 continuously spoken words because visual pauses and checks consume time. Prefer approximately 70–120 spoken words on a substantive slide, shorter for hooks, checks, and takeaways.

Write narration as natural speech. Exact mathematical notation belongs in `equation_latex`; narration should explain symbols, units, and relationships in pronounceable language rather than expose raw LaTeX or character-by-character notation to TTS.

## E. Visual abstraction

Do not paste paragraphs onto slides. Convert prose into an appropriate visual grammar:

- definition/distinction -> two-column contrast or labelled concept;
- process -> arrows or numbered progression;
- equation -> equation plus highlighted meaning of terms;
- worked example -> staged inputs -> operation -> result -> interpretation;
- data table -> only rows/columns essential to the point;
- misconception -> tempting wrong idea contrasted with correct reasoning;
- comparison -> aligned values with the criterion used to judge them.

Describe the visual in `visual_direction`; do not invent photographs or external data.

## F. Source provenance

Every concept, method, worked-example, or interpretation slide must list the source blocks that directly support it. Hook/check/takeaway slides may have empty provenance only when they merely frame or test already-supported lesson content.

## G. Mathematical material

When source math is present, use `equation_latex` for the production equation. Do not convert a formula into an approximate or altered expression. Narration should explain what changes, what contributes, what dominates, or what the equation lets the learner infer.

## H. Final quality target

The finished lesson should feel like an expert tutor distilled one part of a globally coherent course for a hesitant first-year student: easy to begin, technically trustworthy, visually sparse, aware of what came before and what comes next, and focused on reasoning rather than transcription.
