# LESSON GENERATION TASK

Build the best short slide stack for the lesson described in the machine-readable input.

## A. First decide the conceptual spine

Before choosing slide text, determine internally:

1. What must a beginner understand by the end?
2. Which source ideas are prerequisite versus detail?
3. Which single example, contrast, table, equation, or decision best exposes the reasoning?
4. What misconception is most likely?
5. What should the learner be able to decide or explain after the lesson?

Then create the slide stack around that spine. Do not mirror the source document's paragraph sequence mechanically.

## B. Balance brevity and technical completeness

Target the configured duration. Omit low-value repetition and extensive reference lists from the narrated path. However, do not omit a technical qualification when removing it would make the remaining statement misleading.

Keep slide count at or below the configured maximum. A typical short lesson has 5–7 slides. A technically dense lesson may use one additional slide if the configured limit allows it.

## C. Narration length

Use the configured narration rate as a timing guide. A 6-minute lesson at 130 words per minute does not require 780 continuously spoken words because visual pauses and checks consume time. Prefer approximately 70–120 spoken words on a substantive slide, shorter for hooks, checks, and takeaways.

## D. Visual abstraction

Do not paste paragraphs onto slides. Convert prose into an appropriate visual grammar:

- definition/distinction -> two-column contrast or labelled concept;
- process -> arrows or numbered progression;
- equation -> equation plus highlighted meaning of terms;
- worked example -> staged inputs -> operation -> result -> interpretation;
- data table -> only rows/columns essential to the point;
- misconception -> tempting wrong idea contrasted with correct reasoning;
- comparison -> aligned values with the criterion used to judge them.

Describe the visual in `visual_direction`; do not invent photographs or external data.

## E. Source provenance

Every concept, method, worked-example, or interpretation slide must list the source blocks that directly support it. Hook/check/takeaway slides may have empty provenance only when they merely frame or test already-supported lesson content.

## F. Mathematical material

When source math is present, use `equation_latex` for the production equation. Do not convert a formula into an approximate or altered expression. Narration should explain what changes, what contributes, what dominates, or what the equation lets the learner infer.

## G. Final quality target

The finished lesson should feel like an expert tutor distilled the source for a hesitant first-year student: easy to begin, technically trustworthy, visually sparse, and focused on reasoning rather than transcription.
