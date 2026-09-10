# Microcredential Video Generator — User Manual

**Package version:** 0.6.0  
**Repository:** `tlyoon/microcredential-video-generator`  
**CLI command:** `microvid`

This manual explains how to install, configure, and operate the package from a structured teaching DOCX through globally planned Gemini lessons, PowerPoint slide decks, narration, Google Cloud Chirp 3 HD audio, and final MP4 video.

Physics Laboratory 101 is the bundled reference course. The engine itself is topic-neutral.

---

## 1. The v0.6.0 production philosophy

The central design rule is:

> **Gemini reads and understands the complete structured source document before the package asks it to design any individual video or slide.**

The production sequence is therefore:

```text
Source DOCX
  -> local semantic extraction
  -> Gemini whole-document comprehension
  -> Gemini global concept/course map
  -> Gemini video segmentation + source-block assignments
  -> local validation
  -> Gemini global-plan review/revision
  -> per-video Gemini slide/narration generation with global context
  -> local QA
  -> per-video Gemini review/revision
  -> Gemini whole-course consistency review
  -> targeted lesson revision if needed
  -> final whole-course verification
  -> local PowerPoint + notes + narration + SRT
  -> local scientific-speech normalization
  -> Google Cloud Chirp 3 HD TTS
  -> local PowerPoint slide rendering
  -> local FFmpeg MP4 assembly
```

The previous profile-first workflow is retained only for explicit compatibility/debug use.

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
- creating PowerPoint files;
- embedding narration/production notes in PowerPoint speaker notes;
- writing narration Markdown and SRT subtitles;
- scientific-speech normalization;
- exporting PowerPoint slides to PNG;
- FFmpeg assembly of slide/audio segments and final MP4;
- all workspace and provenance files.

### Google Gemini

Gemini is used for the instructional reasoning:

- whole-document comprehension;
- concept mapping;
- deciding video/lesson boundaries;
- assigning source blocks to videos;
- defining prerequisite and sequence relationships;
- creating slide stacks and narration;
- grounded lesson review/revision;
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

For later per-video generation, Gemini receives the global course map and sequence context plus only the authoritative source blocks assigned to that video. This avoids repeatedly sending the entire document while preserving global understanding.

See [GLOBAL_DESIGN.md](GLOBAL_DESIGN.md) for the detailed request boundary.

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
    max_source_characters_per_lesson: 220000
    global_design:
      max_source_characters: 800000
      max_videos: 30
```

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

### Important v0.6.0 change

The scaffold **does not pre-segment the DOCX into videos**. The generated `videos` list is intentionally empty.

Review and edit only the course constraints that matter before global planning, especially:

- course title;
- learner audience;
- source role;
- target video duration;
- target total duration if known;
- maximum slides;
- parser conventions;
- LLM model/reasoning settings;
- editorial policy;
- TTS settings.

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

Inspect this file if heading recognition, equations, tables, or source ordering look wrong.

### 11.2 Ask Gemini to design the whole course

```powershell
microvid plan `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

The first Gemini pass reads the complete structured source and proposes:

- a course summary;
- pedagogical strategy;
- global concept map;
- video count and sequence;
- source block assignments;
- prerequisite relationships;
- concepts already taught by each point;
- forward links to later lessons;
- learning outcomes, checks, and takeaways.

The local PC validates the returned source IDs and coverage. A second Gemini pass reviews/revises the complete plan against the whole source.

Output:

```text
workspace/my_course/plans/course_plan.yaml
```

### 11.3 Inspect the global plan

Before expensive lesson generation, inspect at least:

- `course_summary`;
- `pedagogical_strategy`;
- `concept_map`;
- video order and titles;
- `core_block_ids`;
- `reference_block_ids`;
- `prerequisite_video_ids`;
- `already_taught`;
- `forward_links`;
- coverage notes and editorial flags.

This is the most important place to judge whether Gemini actually understood the source globally.

### 11.4 Generate lesson manifests

```powershell
microvid draft `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

For each planned video, Gemini receives:

- the global course summary;
- concept map;
- full compact video sequence;
- current lesson prerequisites and forward links;
- assigned authoritative core blocks;
- assigned reference blocks.

The package performs a generation pass and a grounded lesson review/revision pass by default.

### 11.5 Whole-course consistency review

After all lessons are generated, the normal `draft` workflow asks Gemini to review all lessons together against the global plan.

The review checks for:

- missing concepts;
- unnecessary repetition;
- prerequisite violations;
- inconsistent terminology or notation;
- poor neighboring-lesson handoffs;
- scope drift;
- duplicated/weak checks and takeaways.

Outputs:

```text
workspace/my_course/manifests/global_consistency_initial.yaml
workspace/my_course/manifests/global_consistency_final.yaml
```

If the initial review requests targeted lesson corrections, only the affected lessons are reopened with their original source packets and global context. Gemini then performs a final course verification.

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

`--allow-unreviewed-course` exists only as a diagnostic override if global consistency is not ready.

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

This performs:

1. fresh local extraction;
2. fresh global Gemini course planning by default;
3. global-plan review;
4. per-video lesson generation;
5. per-video grounded review;
6. whole-course consistency review/revision/verification;
7. slide generation;
8. structural validation.

A normal `all` run replans after the fresh extraction. Use `--reuse-plan` only when deliberately reusing a plan; the package still checks that the source signature matches exactly.

---

## 13. Source-signature protection

`course_plan.yaml` stores:

```yaml
source_signature: <sha256>
```

The signature is generated from the complete prompt-facing extraction. If the DOCX changes and is re-extracted, the signature changes.

`microvid draft` reuses an existing plan only when the signature matches. A stale plan is not silently applied to a revised source.

To force replanning during a staged workflow:

```powershell
microvid draft `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml" `
  --replan
```

---

## 14. Generated workspace

A typical v0.6.0 workspace contains:

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
    video_01_notes.md
    ...
  narration/
    video_01.md
    ...
  subtitles/
    video_01.srt
    ...
  rendered_slides/
  audio/
  segments/
  videos/
```

The global plan is the course-level design contract. Each `video_NN.yaml` is the production record for one lesson.

---

## 15. Lesson-manifest structure

A generated slide record includes fields such as:

```yaml
id: V05S03
slide_type: worked_example
title: Which measurement dominates?
onscreen:
  - concise visible teaching content
narration: >
  Natural spoken explanation for this exact slide.
lecturer_notes:
  - teaching emphasis
visual_direction: >
  Show the contributions sequentially.
equation_latex: null
source_block_ids: [b0214, b0215]
estimated_seconds: 70
```

The manifest also records:

- source core/reference block counts;
- exact assigned source block IDs;
- Gemini provider/model;
- generation pass count;
- design mode (`global_llm` or legacy `profile`);
- editorial status.

---

## 16. Human review and approval

Even after Gemini's lesson review and whole-course consistency review, final scientific/editorial acceptance remains human-controlled.

Review:

- factual fidelity to the source;
- equations, units, assumptions, and numerical values;
- conceptual sequence;
- slide density;
- narration quality;
- examples and visual directions;
- pronunciation of scientific notation;
- source provenance;
- duration;
- assessment/check questions.

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

For example:

```yaml
equation_latex: >
  g = \frac{4\pi^2}{m}

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

Common symbols and SI expressions are normalized conservatively before TTS. If the automatic spoken form is not satisfactory, use `tts_text` or a local `tts_replacements` mapping.

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

The media stage:

1. exports each PowerPoint slide as PNG;
2. obtains narration or explicit `tts_text`;
3. normalizes scientific speech;
4. synthesizes one audio file per slide;
5. combines slide PNG + audio into MP4 segments;
6. concatenates segments into the final video.

The TTS audit file is:

```text
workspace/my_course/audio/video_NN/tts_manifest.yaml
```

It records the actual provider, voice, language, audio file, and spoken text used for every slide.

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

In v0.6.0, the existing nine-video definitions in the Lab 101 profile no longer control the production segmentation in default global mode. They are retained for legacy/profile mode and regression comparison. Gemini is free to confirm, merge, split, or reorganize the course after reading the entire structured manual, subject to course constraints.

For the old instructor-presegmented behavior:

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101 `
  --design-mode profile
```

---

## 20. Deterministic/debug generation

The deterministic builder has no global semantic reasoning. It therefore cannot be used with the production global design mode.

Use:

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

## 21. Development/cost-control overrides

The following options deliberately weaken the normal review architecture and should not be routine production defaults:

```text
--no-plan-review-pass
--no-review-pass
--no-global-consistency-review
--design-mode profile
```

`--allow-unreviewed-course` allows slide generation when the global consistency status is not ready, but only for diagnostics.

`--allow-draft` allows private media previews before human approval.

---

## 22. Large documents

v0.6.0 sends the complete structured extraction during global planning and refuses silent truncation.

Default global source limit:

```yaml
max_source_characters: 800000
```

If a source exceeds that limit, the package fails visibly. For a very large textbook, the better future architecture is hierarchical planning—major-unit/chapter comprehension followed by global synthesis—rather than blindly truncating the document.

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

### Existing plan is unexpectedly rebuilt

The extracted source signature no longer matches the stored plan. This is intentional protection against using a stale plan after a DOCX change.

### Global planning fails because the source is too large

Do not simply assume truncation is safe. Review `global_design.max_source_characters` and consider a hierarchical planning strategy for very large sources.

### Whole-course review blocks slides

Inspect:

```text
manifests/global_consistency_initial.yaml
manifests/global_consistency_final.yaml
```

Resolve remaining blocking findings. `--allow-unreviewed-course` should be used only for diagnostics.

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

Use human-readable narration and an explicit `tts_text` for difficult expressions. Do not feed raw LaTeX to TTS.

---

## 24. Recommended first production test

For any new course:

1. run `extract`;
2. run `plan`;
3. inspect `course_plan.yaml` before generating all lessons;
4. run `draft`;
5. inspect the global consistency reports;
6. inspect one representative lesson PPTX and narration;
7. audition/confirm the Chirp voice;
8. approve one lesson;
9. render one MP4;
10. only then batch-produce the rest of the course.

This staged pilot catches global segmentation, scientific content, narration, voice, and media issues before they are multiplied across the course.
