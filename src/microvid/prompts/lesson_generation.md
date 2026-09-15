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
- do not change the globally planned lesson scope merely because a neighboring section of the source document looks convenient.

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

## I. Mandatory textbook-subchapter slide architecture

When `source_document.classification.kind` is `textbook_subchapter`, the input has already been
scoped to the intended textbook subchapter. Do not reintroduce material from excluded previous
or following sections. Every generated lesson from that source must use this minimum architecture:

1. **Title slide** — `slide_type: title`; it must display only the exact lesson/subchapter title. Set `onscreen` to an empty array, use no figure, and add no subtitle, course code, institution label, page counter, or other framing text.
2. **Introduction slide** — `slide_type: introduction`; explain the central physical question, why it matters, and the conceptual route through the lesson.
3. **Concept development** — one or more source-grounded concept/method/example/interpretation slides that teach the subchapter comprehensively rather than merely summarize it.
4. **Concept-strengthening question** — `slide_type: check`; ask a reasoning question that tests the central concept, misconception, prediction, or application. Prefer explanation/choice reasoning over factual recall.
5. **Conclusion slide** — `slide_type: conclusion`; synthesize the central idea, relationships, and what the learner should now be able to explain or apply.

The title must be the first slide, the introduction the second, and the conclusion the final slide.
If the source's PDF text encoding makes an equation ambiguous or visibly corrupted, do not silently
repair it from memory. Teach only what the supplied source supports and add an editorial flag for
human equation verification.

## J. Textbook figures and adaptive slide layout

When `source_document.classification.kind` is `textbook_subchapter`, use `available_figures` as the only allowed textbook visual assets.

- Include a relevant textbook figure when it materially improves explanation of the concept on that slide.
- Select figures only by their supplied `id`; put selected IDs in `figure_ids`.
- Do not invent, redraw, or substitute an external image when a supplied textbook figure is intended.
- Use `figure_layout_hint` only as a soft layout suggestion; the renderer will make the final fit decision.
- Prefer `image_large` when the figure is the main object of explanation and on-screen text can be minimal.
- Prefer `image_right` or `image_left` when concise explanatory text should remain beside one figure.
- Prefer `grid` when several supplied figure assets must be compared together.
- Reduce on-screen text when a figure is visually rich. A figure slide should be readable at a glance, not a page of prose beside an image.
- Do not force a figure onto a slide when no supplied figure is genuinely relevant.

## K. Textbook narration rules

For a textbook-subchapter lesson, write each slide narration as a clear spoken explanation of only what appears on that slide.

- Explain only the concept shown on the current slide.
- Use clear spoken lecture style with natural sentences and transitions.
- Define a technical term before relying on it.
- If a formula appears on the slide, convert it into natural spoken English and briefly explain the meaning of each quantity in words.
- If a figure appears, briefly describe what it shows and connect that description to the concept being taught.
- Avoid repeating the same explanation across slides.
- Do not mention material from other chapters, other slide decks, prior conversations, or external knowledge unless it is clearly grounded in the current supplied files.
- Keep mathematical notation in `equation_latex` only; narration must not contain raw symbolic equations, TeX, LaTeX, dollar-delimited math, backslash commands, or character-by-character symbol reading.
- Do not expose citation markers, grounding markers, source IDs, page counters, or bracketed provenance artefacts in visible slide text or narration.

## L. Final self-check for textbook-subchapter output

Before returning the structured lesson, silently verify and repair any violation:

- Slide 1 displays only the exact `lesson_title`; its `onscreen` list is empty and it has no figure.
- Slides 2 onward use an empty `title` field. Their visible content belongs in `onscreen`, figures, or `equation_latex`.
- No page-counter, slide-counter, source-section footer, citation marker, grounding marker, or bracketed source artefact appears in visible slide text or narration.
- No invented course code, institution label, or other framing appears unless explicitly grounded in the current source/profile.
- Narration contains no LaTeX, TeX, dollar-delimited math, backslash commands, subscripts, superscripts, or raw symbolic equation strings.
- Every mathematical statement in narration is plain spoken English.
- A slide with a selected figure briefly explains that figure in its narration.
- Figure choices come only from `available_figures` and are relevant to the current slide concept.
- The lesson contains the required title, introduction, concept development, concept-strengthening question, and conclusion sequence.
