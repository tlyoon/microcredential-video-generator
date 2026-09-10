# Microcredential Video Generator — User Manual

**Package version:** 0.7.0  
**Repository:** `tlyoon/microcredential-video-generator`  
**CLI command:** `microvid`

This manual explains how to install, configure, and operate the package from a structured teaching DOCX through globally planned Gemini lessons, separately polished narration, PowerPoint slide decks, Google Cloud Chirp 3 HD audio, and final MP4 video.

Physics Laboratory 101 is the bundled reference course. The engine itself is topic-neutral.

---

## 1. Production philosophy

Two design rules now govern the production path:

> **Gemini reads and understands the complete structured source document before the package asks it to design any individual video or slide.**

> **The spoken narration is given its own dedicated editorial pass after the scientific content and slide structure have been reviewed.**

The normal sequence is:

```text
Source DOCX
  -> local semantic extraction
  -> Gemini whole-document comprehension
  -> Gemini global concept/course map
  -> Gemini video segmentation + source-block assignments
  -> local validation
  -> Gemini global-plan review/revision
  -> per-video Gemini slide + first-narration generation with global context
  -> local lesson QA
  -> per-video Gemini scientific/pedagogical review/revision
  -> dedicated Gemini narration-only polish
  -> local narration timing/speech QA
  -> Gemini whole-course consistency review
  -> targeted lesson revision if needed
       -> narration is polished again for revised lessons
  -> final whole-course verification
  -> local PowerPoint + notes + polished narration + SRT
  -> local scientific-speech normalization
  -> Google Cloud Chirp 3 HD TTS
  -> local PowerPoint slide rendering
  -> local FFmpeg MP4 assembly
```

The previous profile-first workflow remains only for explicit compatibility/debug use.

---

## 2. What runs locally and what uses cloud services

### Local PC

The following operations are performed on your computer:

- reading the DOCX;
- extracting headings, paragraphs, tables, source order, and Office Math provenance;
- creating `document_structure.json`;
- computing the source signature;
- validating Gemini source-block IDs;
- storing the global plan;
- deterministic QA of generated lesson manifests;
- checking polished narration for obvious raw LaTeX/markup or internal production language;
- calculating narration word count and estimated spoken duration;
- creating PowerPoint files;
- embedding polished narration/production notes in PowerPoint speaker notes;
- writing narration Markdown and SRT subtitles;
- scientific-speech normalization;
- exporting PowerPoint slides to PNG;
- FFmpeg assembly of slide/audio segments and final MP4;
- all workspace and provenance files.

### Google Gemini

Gemini is used for instructional and editorial reasoning:

- whole-document comprehension;
- concept mapping;
- deciding video/lesson boundaries;
- assigning source blocks to videos;
- defining prerequisite and sequence relationships;
- creating slide stacks and first-pass narration;
- grounded scientific/pedagogical lesson review/revision;
- dedicated narration-only polishing;
- whole-course consistency review;
- targeted course-level correction when required.

### Google Cloud Text-to-Speech

Chirp 3 HD receives the spoken narration text after local scientific-speech normalization and returns audio. It is a separate cloud service from Gemini.

---

## 3. What is sent to Gemini

The package does **not** upload the binary DOCX directly to Gemini. The DOCX is parsed locally first.

For global planning, Gemini receives the complete prompt-facing structured extraction. Each block includes information such as:

```json
{
  "id": "b0142",
  "kind": "paragraph",
  "section": "8.2",
  "heading_level": null,
  "heading_path": [
    "8. Propagation of uncertainty",
    "8.2 Multiplication and division"
  ],
  "text": "...",
  "math_text": ["..."],
  "contains_office_math": true
}
```

Raw OMML XML is retained locally. Readable math tokens are supplied to Gemini instead.

For per-video generation, Gemini receives the global course map and sequence context plus only the authoritative/reference source blocks assigned to that video.

For the dedicated narration-polish pass, Gemini receives the **fixed reviewed lesson manifest** plus the same source/global context. The narration editor can return only:

```yaml
slides:
  - slide_id: V05S01
    narration: >
      polished spoken script
    tts_text: null
```

It is not allowed to return replacement slide titles, bullets, equations, visual directions, source IDs, or lesson structure. Local code requires every existing slide ID exactly once.

See [GLOBAL_DESIGN.md](GLOBAL_DESIGN.md) and [NARRATION_QUALITY.md](NARRATION_QUALITY.md).

---

## 4. Recommended workstation

The complete media workflow is designed primarily for Windows because PowerPoint automation and the Windows SAPI fallback are Windows-specific.

Recommended software:

- Windows 10 or 11;
- Python 3.10 or later;
- Microsoft PowerPoint desktop;
- Git;
- FFmpeg on `PATH`;
- Google Cloud CLI (`gcloud`) for Application Default Credentials;
- a Gemini API key;
- a Google Cloud project with Cloud Text-to-Speech enabled.

Content extraction and Gemini authoring can run without PowerPoint, but final PNG rendering currently uses Windows PowerPoint automation.

---

## 5. Clone or update the repository

Fresh clone:

```powershell
git clone https://github.com/tlyoon/microcredential-video-generator.git
cd microcredential-video-generator
```

Existing clone:

```powershell
git switch main
git pull --ff-only
```

If an older clone still points to the previous repository name:

```powershell
git remote set-url origin https://github.com/tlyoon/microcredential-video-generator.git
git remote -v
```

---

## 6. Install the Python environment

From the repository root:

```powershell
.\scripts\setup-local.ps1
```

or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,windows]"
```

Verify:

```powershell
microvid --help
python -m pytest
```

---

## 7. Configure Gemini

Set the API key in the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Do not commit the key to Git.

Typical profile settings are:

```yaml
course:
  llm:
    provider: gemini
    model: gemini-flash-latest
    thinking_level: high
    api_key_env: GEMINI_API_KEY
    review_pass: true
    narration_polish_pass: true
    max_source_characters_per_lesson: 220000
    global_design:
      max_source_characters: 800000
      max_videos: 30
```

`narration_polish_pass` defaults to `true` even when an older profile omits it. Set it to `false` only for deliberate cost/diagnostic comparison.

The model is configuration data. You may override it at runtime:

```powershell
--model "MODEL_NAME"
--thinking-level high
```

For reproducible production runs, pin an exact supported model instead of a moving alias.

---

## 8. Configure Chirp TTS

Authenticate Google Cloud locally:

```powershell
gcloud auth application-default login
```

Ensure Cloud Text-to-Speech is enabled for the selected Google Cloud project.

The packaged production defaults are conceptually:

```yaml
tts:
  provider: google_cloud_chirp3
  language_code: en-GB
  voice_name: en-GB-Chirp3-HD-Leda
  audio_encoding: LINEAR16
  speaking_rate: 1.0
  location: global
  normalize_scientific_speech: true
  fallback_provider: sapi
  fallback_on_error: true
```

Example configuration:

```text
examples/tts/chirp3.example.yaml
```

Audition candidate voices before committing to a course narrator:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

---

## 9. Prepare the source DOCX

The runtime source is always explicit. The bundled Lab 101 DOCX is never used automatically.

For example:

```text
source/my_course.docx
```

For best results, use meaningful Word heading styles and a coherent hierarchy. Paragraphs, tables, headings, and Office Math are extracted. The parser does not depend on rendered page numbers.

---

## 10. Create a profile for a new course

For a new topic:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

The scaffold **does not pre-segment the DOCX into videos**. The generated `videos` list is intentionally empty.

Review and edit the course constraints that matter before global planning, especially course title, audience, target video/total duration, maximum slides, parser conventions, LLM model, narration rate, `narration_polish_pass`, editorial policy, and TTS settings.

Gemini will determine the lesson boundaries after reading the complete structured source.

---

## 11. Recommended staged workflow

The staged workflow is best for the first run of a new course because each intermediate artifact can be inspected.

### 11.1 Extract the DOCX locally

```powershell
microvid extract `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

Output:

```text
workspace/my_course/extracted/document_structure.json
```

### 11.2 Ask Gemini to design the whole course

```powershell
microvid plan `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

Gemini reads the complete structured source and proposes a course summary, pedagogical strategy, concept map, video sequence, source assignments, prerequisite relationships, checks, and takeaways. The local PC validates source IDs and coverage; a second Gemini pass reviews/revises the plan.

Output:

```text
workspace/my_course/plans/course_plan.yaml
```

### 11.3 Inspect the global plan

Before expensive lesson generation, inspect at least the course summary, pedagogical strategy, concept map, video order/titles, core/reference block IDs, prerequisite relationships, forward links, coverage notes, and editorial flags.

### 11.4 Generate and polish lesson manifests

```powershell
microvid draft `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

For each planned video, the normal path now performs:

1. Gemini slide + first-narration generation;
2. local deterministic lesson QA;
3. Gemini grounded scientific/pedagogical review/revision;
4. **Gemini dedicated narration-only polish**;
5. local narration speech/timing checks.

The narration editor is intentionally constrained to spoken fields only. Its detailed prompt asks for a natural lecturer voice, smooth slide-to-slide continuity, visual synchronization, explanation rather than bullet recitation, restrained conversational tone, TTS-ready mathematical speech, deliberate punctuation, and realistic pacing.

For most explanatory slides, it targets roughly 70–85% of theoretical speaking capacity:

```text
estimated_seconds * narration_wpm / 60
```

The final slide record may include:

```yaml
narration: >
  polished spoken script

tts_text: >
  optional TTS-specific wording

narration_word_count: 82
narration_estimated_spoken_seconds: 37.8
```

### 11.5 Whole-course consistency review

After all lessons have been generated and narration-polished, Gemini reviews them together against the global plan. It checks missing concepts, unnecessary repetition, prerequisite violations, terminology/notation consistency, neighboring-lesson handoffs, scope drift, and weak/duplicated assessments.

Outputs:

```text
workspace/my_course/manifests/global_consistency_initial.yaml
workspace/my_course/manifests/global_consistency_final.yaml
```

If the review requests a targeted correction, only the affected lesson is reopened. **Any revised lesson is sent through narration polishing again** before final course verification.

If blocking issues remain, normal slide generation is blocked.

### 11.6 Build PowerPoint decks

```powershell
microvid slides `
  --workspace ".\workspace\my_course"
```

One lesson only:

```powershell
microvid slides `
  --workspace ".\workspace\my_course" `
  --video V05
```

### 11.7 Validate

```powershell
microvid validate `
  --workspace ".\workspace\my_course"
```

Validation is structural. It does not replace expert scientific/editorial review.

---

## 12. One-command workflow

Once the workflow is understood:

```powershell
microvid all `
  --source ".\source\my_course.docx" `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

This performs fresh local extraction, global Gemini course planning/review, per-video lesson generation/review, dedicated narration polishing, whole-course consistency review/revision/verification, slide generation, and structural validation.

A normal `all` run replans after the fresh extraction. Use `--reuse-plan` only when deliberately reusing a plan; the package still checks that the source signature matches exactly.

---

## 13. Source-signature protection

`course_plan.yaml` stores:

```yaml
source_signature: <sha256>
```

The signature is generated from the complete prompt-facing extraction. If the DOCX changes and is re-extracted, the signature changes. A stale plan is not silently applied to a revised source.

---

## 14. Generated workspace

A typical workspace contains:

```text
workspace/my_course/
  extracted/
    document_structure.json
  plans/
    course_plan.yaml
  manifests/
    course.yaml
    video_01.yaml
    video_02.yaml
    ...
    global_consistency_initial.yaml
    global_consistency_final.yaml
  slides/
    video_01.pptx
    ...
  notes/
  narration/
  subtitles/
  rendered_slides/
  audio/
  segments/
  videos/
```

The global plan is the course-level design contract. Each `video_NN.yaml` is the production record for one lesson.

---

## 15. Lesson-manifest structure

A polished generated slide record includes fields such as:

```yaml
id: V05S03
slide_type: worked_example
title: Which measurement dominates?
onscreen:
  - concise visible teaching content
narration: >
  Polished natural spoken explanation for this exact slide.
tts_text: null
lecturer_notes:
  - teaching emphasis
visual_direction: >
  Show the contributions sequentially.
equation_latex: null
source_block_ids: [b0214, b0215]
estimated_seconds: 70
narration_word_count: 96
narration_estimated_spoken_seconds: 44.3
```

The manifest also records source assignments, Gemini provider/model, generation pass count, narration-polish provenance, design mode, narration-quality findings, and editorial status.

---

## 16. Human review and approval

Even after Gemini's scientific/pedagogical review, dedicated narration polish, and whole-course consistency review, final acceptance remains human-controlled.

Review factual fidelity, equations/units/assumptions, conceptual sequence, slide density, narration naturalness, visual synchronization, pacing, pronunciation, source provenance, duration, and assessment quality.

For narration, the best check is to **listen to at least one representative lesson using the intended Chirp voice**, not merely read the text.

Generated lessons begin as:

```yaml
editorial_status: llm_draft_requires_review
```

After approval, change to:

```yaml
editorial_status: approved
```

---

## 17. Scientific speech

Exact mathematics and spoken mathematics are intentionally separated.

```yaml
equation_latex: >
  g = \frac{4\pi^2}{m}

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

The narration editor may propose `tts_text` when useful, and the local TTS layer also normalizes common symbols and SI expressions conservatively. If the spoken form is still unsatisfactory, edit `tts_text` or use `tts_replacements`.

---

## 18. Generate final media

After approving a lesson:

```powershell
microvid media `
  --workspace ".\workspace\my_course" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml" `
  --no-tts-fallback
```

Typical output:

```text
workspace/my_course/videos/video_05.mp4
```

The media stage exports PowerPoint slides to PNG, uses polished narration or explicit `tts_text`, normalizes scientific speech, synthesizes one audio file per slide, combines PNG + audio into MP4 segments, then concatenates the segments.

The TTS audit file is:

```text
workspace/my_course/audio/video_NN/tts_manifest.yaml
```

---

## 19. Physics Laboratory 101 reference workflow

Assume the runtime manual is:

```text
source/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

Run:

```powershell
microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

The existing nine-video definitions in the Lab 101 profile do not control the production segmentation in default global mode. They remain for legacy/profile comparison. Narration polishing is enabled explicitly in the Lab 101 profile.

---

## 20. Deterministic/debug generation

The deterministic builder has no global semantic reasoning and no Gemini narration editor. Use it only with profile mode:

```powershell
microvid all `
  --source ".\source\course.docx" `
  --workspace ".\workspace\debug" `
  --profile my_profile `
  --generator deterministic `
  --design-mode profile
```

This path is for diagnostics/regression work, not normal instructional authoring.

---

## 21. Development/cost controls

The following options weaken parts of the normal review architecture and should not be routine production defaults:

```text
--no-plan-review-pass
--no-review-pass
--no-global-consistency-review
--design-mode profile
```

Narration polish is controlled in YAML:

```yaml
course:
  llm:
    narration_polish_pass: true
```

Set it to `false` only for deliberate A/B cost/quality testing.

---

## 22. Large documents

The global planner sends the complete structured extraction during global planning and refuses silent truncation. The default global source limit is:

```yaml
max_source_characters: 800000
```

For a source larger than that limit, use a deliberate hierarchical planning strategy rather than arbitrary truncation.

---

## 23. Troubleshooting

### `microvid` is not recognized

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,windows]"
```

### Gemini authentication fails

```powershell
$env:GEMINI_API_KEY
```

Confirm the key is set and the configured model is available.

### Narration polish fails with a speech-hygiene error

Inspect the Gemini output or source for raw LaTeX/code-like text or internal production language in the spoken channel. The narration editor is expected to verbalize mathematics naturally. Exact equations belong in `equation_latex`; TTS-specific wording belongs in `tts_text`.

### Narration has timing warnings

Compare `narration_word_count`, `narration_estimated_spoken_seconds`, and `estimated_seconds`. A warning means the script may sound rushed at the configured narration rate. Shorten repetition or increase the slide timing only when pedagogically justified.

### Existing plan is unexpectedly rebuilt

The extracted source signature no longer matches the stored plan. This is intentional protection against stale global plans.

### Whole-course review blocks slides

Inspect `global_consistency_initial.yaml` and `global_consistency_final.yaml`. Resolve remaining blocking findings. `--allow-unreviewed-course` should be used only for diagnostics.

### Chirp authentication fails

```powershell
gcloud auth application-default login
```

Also confirm Cloud Text-to-Speech is enabled and the project has suitable permissions/billing.

### FFmpeg is missing

```powershell
ffmpeg -version
```

must work from the same terminal.

### TTS pronounces equations badly

Use natural narration and explicit `tts_text` for difficult expressions. Do not feed raw LaTeX to TTS.

---

## 24. Recommended first production test

For any new course:

1. run `extract`;
2. run `plan` and inspect `course_plan.yaml`;
3. run `draft`;
4. inspect the global consistency reports;
5. inspect one representative lesson manifest, paying special attention to the polished narration and timing metrics;
6. build its PPTX and check narration against the visual sequence;
7. audition/confirm the Chirp voice;
8. listen to the representative narrated lesson;
9. approve one lesson;
10. render one MP4;
11. only then batch-produce the rest of the course.

This staged pilot catches global segmentation, scientific content, narration style, voice, and media issues before they are multiplied across the course.
