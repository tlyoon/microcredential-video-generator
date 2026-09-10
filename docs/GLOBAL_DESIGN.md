# Global-First Gemini Course Design

## Why the architecture changed

Earlier releases selected lesson-sized source packets from a hand-authored YAML profile before Gemini generated slides. That approach was source-grounded, but it constrained Gemini to local lesson boundaries chosen before the model had read the complete source document.

The production default is now **global-first**:

> Gemini reads the complete structured source document first, creates a global concept/course map, decides the video boundaries, and only then generates individual slide stacks. After scientific/pedagogical lesson review, a separate Gemini narration editor polishes the spoken script without changing the slide structure or science.

The pre-segmented profile workflow remains available only as an explicit compatibility/debug path.

## End-to-end design

```text
LOCAL PC
  source.docx
      ↓
  semantic extraction
      ↓
  document_structure.json
      │
      │ complete structured document
      ▼
GEMINI — GLOBAL PLANNING PASS 1
  understand entire source
  build concept map
  decide lesson/video boundaries
  assign source block IDs
  define prerequisites / already-taught / forward links
      ↓
LOCAL PC
  validate all block IDs
  identify duplicate core assignments
  identify substantive unassigned blocks
      │
      ▼
GEMINI — GLOBAL PLANNING PASS 2
  review/revise plan against complete source + local findings
      ↓
LOCAL PC
  plans/course_plan.yaml
      ↓
FOR EACH VIDEO
  global course context
  + assigned authoritative blocks
  + assigned reference blocks
      │
      ▼
GEMINI — LESSON GENERATION
  slide stack + first narration
  lecturer notes
  visual directions
  equations
  provenance
      ↓
LOCAL PC
  deterministic lesson QA
      │
      ▼
GEMINI — LESSON SCIENTIFIC/PEDAGOGICAL REVIEW
      ↓
GEMINI — DEDICATED NARRATION POLISH
  rewrite spoken script only
  preserve slide IDs/structure/science/provenance
  optional TTS-specific wording
      ↓
LOCAL PC
  narration speech/timing QA
      ↓
GEMINI — WHOLE-COURSE CONSISTENCY REVIEW
  gaps / repetition / prerequisite order / terminology / notation / hand-offs
      ↓
  if required: targeted lesson revision calls
      ↓
  re-polish narration for any revised lesson
      ↓
GEMINI — FINAL CONSISTENCY VERIFICATION
      ↓
LOCAL PC
  manifests
  PowerPoint
  notes / polished narration / SRT
  scientific-speech normalization
      │
      ▼
GOOGLE CLOUD CHIRP 3 HD
  narration audio per slide
      ↓
LOCAL PC
  PowerPoint PNG render
  FFmpeg assembly
  MP4
```

## What is sent during global planning

The DOCX binary itself is not uploaded by this package. It is parsed locally first. Gemini receives a JSON representation containing every extracted semantic block: ID, kind, section, heading level/path, text, readable math tokens, and whether Office Math is present. The complete packet also includes course constraints such as audience, target lesson duration, target total duration, maximum slides, source role, and editorial policy.

Raw Office Math XML remains local; readable math tokens are sent instead.

## What the global plan contains

`workspace/<course>/plans/course_plan.yaml` contains, among other fields:

```yaml
design_mode: global_llm
source_signature: <sha256>
course_summary: ...
pedagogical_strategy: ...
concept_map:
  - name: ...
    description: ...
    source_block_ids: [...]
    prerequisite_concepts: [...]
videos:
  - id: V01
    title: ...
    focus: ...
    target_minutes: 6
    max_slides: 7
    learning_outcomes: [...]
    check_question: ...
    takeaways: [...]
    core_block_ids: [...]
    reference_block_ids: [...]
    prerequisite_video_ids: [...]
    already_taught: [...]
    forward_links: [...]
coverage_notes: [...]
editorial_flags: [...]
```

This file is the global design contract for later lesson generation.

## Source-signature protection

The plan stores a SHA-256 signature derived from the complete prompt-facing extraction. If the source DOCX is changed and re-extracted, the signature changes. A stale plan is therefore not silently reused.

`microvid draft` may reuse an existing plan only when the source signature matches exactly. `microvid all` replans by default because it performs a fresh extraction; `--reuse-plan` allows reuse only when the signature still matches.

## Per-video generation after global planning

Gemini is not sent the complete source again for every video. Instead, each lesson call receives the global course summary, pedagogical strategy, concept map, compact full video sequence, current prerequisites/already-taught/forward-link context, and that lesson's authoritative/reference source blocks.

This keeps the local call focused while preserving knowledge of the lesson's place in the whole course.

## Dedicated narration polishing after lesson review

The first two lesson calls optimize lesson structure, scientific fidelity and pedagogy. Narration quality is important during those passes, but v0.7.0 no longer assumes that the resulting script is final.

A separate Gemini call then receives the fixed lesson manifest and the same source/global context. Its response schema only permits:

```yaml
slides:
  - slide_id: V01S01
    narration: >
      polished spoken script
    tts_text: null
```

This pass cannot redesign the lesson. The local package rejects missing/duplicate/unknown slide IDs and rejects obvious raw LaTeX or internal production language in the polished narration. Word count and estimated spoken duration are recorded for each slide, with warnings when the script is too dense for the assigned timing.

The narration prompt explicitly emphasizes writing for the ear, smooth slide-to-slide continuity, visual synchronization, explanation rather than bullet recitation, natural sentence rhythm, concise lecturer-like tone, mathematical speech readiness, and avoidance of generic AI/filler phrases.

See [NARRATION_QUALITY.md](NARRATION_QUALITY.md).

## Whole-course consistency review

After all individual lessons have been generated, reviewed and narration-polished, Gemini sees the global plan together with compact versions of every lesson. It checks for course-level problems including missing concepts, accidental repetition, prerequisite violations, inconsistent terminology/notation/units/definitions, premature later-course concepts, poor transitions, duplicated checks/takeaways, and drift from the global plan.

The reviewer returns either `ready` or `revision_required` plus targeted revision instructions. The package can automatically re-open only the affected lessons, with their source packets and global context. Any revised lesson is narration-polished again before final course verification.

If blocking issues remain, draft manifests and review reports are saved but normal slide production is blocked.

Review files are written under:

```text
workspace/<course>/manifests/global_consistency_initial.yaml
workspace/<course>/manifests/global_consistency_final.yaml
```

## Commands

Staged production:

```powershell
microvid extract `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile my_course

microvid plan `
  --workspace ".\workspace\my_course" `
  --profile my_course

microvid draft `
  --workspace ".\workspace\my_course" `
  --profile my_course

microvid slides `
  --workspace ".\workspace\my_course"
```

One-command production:

```powershell
microvid all `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile my_course
```

## Development overrides

These options deliberately weaken parts of the normal production workflow and should mainly be used for cost/debugging experiments:

```text
--no-plan-review-pass
--no-review-pass
--no-global-consistency-review
--design-mode profile
```

Narration polish is controlled in the course profile:

```yaml
course:
  llm:
    narration_polish_pass: true
```

It defaults to true when omitted. Disable it only for deliberate cost/diagnostic comparisons.

The deterministic builder cannot perform global semantic reasoning. Therefore deterministic generation must be requested explicitly with the legacy profile design mode:

```powershell
microvid all ... --generator deterministic --design-mode profile
```

## Very large documents

The current global planner sends the complete structured source in the planning request and refuses to truncate silently. The configurable limit defaults to 800,000 source characters.

For a source larger than that limit, the package fails visibly. A future hierarchical planner can summarize chapters/major units first and then perform global synthesis. Raising the limit blindly is not equivalent to a well-designed hierarchical strategy.
