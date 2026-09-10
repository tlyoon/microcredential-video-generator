# Narration Quality and Dedicated Script Polishing

Microcredential Video Generator treats narration as a first-class production artifact. In v0.7.0, the final narration is no longer accepted directly from the general slide-generation/review pass. A dedicated Gemini narration-editor pass is enabled by default.

## Production sequence

For each lesson, the normal LLM sequence is:

```text
Gemini lesson generation
  -> local deterministic lesson QA
  -> Gemini grounded scientific/pedagogical lesson review
  -> Gemini dedicated narration-only polish
  -> whole-course consistency review
  -> targeted lesson revision if required
       -> narration-only polish is run again for that revised lesson
  -> final whole-course verification
```

The narration editor receives the fixed lesson manifest, global course context, authoritative/reference source blocks, narration rate, slide timing, equations, visible content, and visual directions. Its response schema permits only:

- `slide_id`;
- polished `narration`;
- optional `tts_text`.

It cannot return replacement slide titles, bullets, equations, visual directions, source IDs, or lesson structure. The local code also requires every existing slide ID to be returned exactly once. This keeps stylistic polishing separate from scientific and structural decisions.

## Narration style contract

The final script should sound like an experienced university lecturer speaking naturally to first-year students. It should not sound like textbook prose, an AI summary, marketing copy, or bullet points being read aloud.

The dedicated prompt asks Gemini to:

- write for the ear rather than the page;
- use clear short-to-medium sentences and varied rhythm;
- explain relationships, reasoning, decisions, misconceptions and interpretation rather than repeat visible text;
- coordinate speech with `visual_direction` and staged builds;
- create smooth transitions between slides;
- refer briefly to concepts already taught rather than reteach them;
- avoid pulling future-course material forward;
- remove filler and generic AI phrasing;
- keep equations exact on screen while rendering their meaning naturally in speech;
- use punctuation intentionally for TTS pacing;
- fit the narration to each slide's allocated time.

A useful internal model for a substantive slide is:

```text
orient attention -> explain relationship -> interpret -> hand off
```

This is guidance, not a rigid template. Hooks, checks and takeaways should remain lighter.

## Anti-patterns explicitly discouraged

The prompt discourages repetitive or low-value phrases such as:

- “In this slide...”;
- “On this slide...”;
- generic “As you can see...”;
- “Let's dive in”;
- “It is important to note”;
- “Basically”;
- “Obviously” / “Clearly” / “Simply” when they add no meaning;
- repeated “remember”, “note that”, “now”, or “so” openings.

It also forbids raw LaTeX, production/meta language, internal source IDs, JSON/prompt references, and hard-to-pronounce code-like notation in narration.

## Timing model

The prompt treats timing as a production constraint. The theoretical spoken capacity of a slide is approximately:

```text
estimated_seconds * narration_wpm / 60
```

For normal explanatory slides, the narration editor is instructed to use roughly 70–85% of that theoretical capacity, leaving room for visual attention and natural pauses. Hooks, checks and takeaways may be shorter.

The package records for each polished slide:

```yaml
narration_word_count: ...
narration_estimated_spoken_seconds: ...
```

and emits a narration-quality warning when the script is too dense for its allocated time.

## `tts_text`

`narration` remains the canonical human-readable spoken script. For material whose exact written notation would sound awkward in TTS, the narration editor may additionally return `tts_text`.

Example:

```yaml
equation_latex: >
  g = \frac{4\pi^2}{m}

narration: >
  Once the slope has been determined, this relationship gives the value of gravitational acceleration.

tts_text: >
  Once the slope has been determined, this relationship gives the value of gravitational acceleration.
```

For a case where a formula must be verbalized, `tts_text` may spell out the exact spoken form while preserving the same scientific meaning.

## Local hard checks

After Gemini returns the polished script, local code rejects narration containing obvious speech-channel contamination such as raw LaTeX commands, code fences, internal source-block language, JSON-schema language, or internal-prompt language.

Timing density is currently reported as a warning rather than a hard failure because slide types differ in how much silence and visual observation they need.

## Configuration

The feature is enabled by default:

```yaml
course:
  llm:
    narration_polish_pass: true
```

The engine also defaults this setting to `true` when the field is absent, so older profiles automatically receive the improved narration workflow. Set it to `false` only for cost/diagnostic comparisons.

## Human editorial review still matters

The dedicated pass improves fluency and production quality but does not make the result automatically publishable. Before setting `editorial_status: approved`, review representative scripts aloud or with the selected Chirp voice. Check scientific nuance, terminology, pacing, pronunciation, visual synchronization and transitions between slides.
