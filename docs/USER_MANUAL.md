# Microcredential Video Generator — User Manual

**Package version:** 0.8.0  
**Repository:** `tlyoon/microcredential-video-generator`  
**CLI command:** `microvid`

This manual explains how to install, configure, and operate the package from a structured teaching DOCX or text-readable PDF through globally planned Gemini lessons, separately polished narration, PowerPoint slide decks, Google Cloud Chirp 3 HD audio, final MP4 video, and optional YouTube course publishing.

Physics Laboratory 101 is the bundled reference course. The engine itself is topic-neutral.

For the final publishing stage, see [YOUTUBE_PUBLISHING.md](YOUTUBE_PUBLISHING.md). The
publisher discovers completed courses under `workspace\`, produces original metadata and a
course image, uploads the MP4/SRT set, creates the ordered playlist, and defaults to public
visibility.

## Operator quick start

For a normal new course, use this sequence:

1. Install the package with `.[dev,windows]` and confirm `microvid --help` works.
2. Put `GEMINI_API_KEY` in `%LOCALAPPDATA%\Microvid\.env`.
3. Configure Google Cloud TTS credentials and audition the chosen voice.
4. Create or review a course profile; pin a concrete Gemini model when reproducibility matters.
5. Run `extract`, `plan`, `draft`, `slides`, and `validate` once as separate stages.
6. Render one representative lesson with `media`, inspect it, then render the remaining lessons.
7. Run `microvid youtube publish --dry-run`, review the metadata and course image, then publish.
8. If a Video 00 trailer is required, follow [COURSE_TRAILER.md](COURSE_TRAILER.md) and keep it
   outside the lesson `videos` directory during automated publishing.

The shortest production command after the setup is understood is:

```powershell
microvid all `
  --source .\source\my_course.pdf `
  --workspace .\workspace\my_course `
  --profile .\profiles\my_course.yaml
```

`microvid all` creates plans, manifests and slides, but it does not render every lesson MP4 or
publish to YouTube. Run `microvid media` for each lesson and `microvid youtube publish`
separately.

---

## 1. Production philosophy

Two design rules now govern the production path:

> **Gemini reads and understands the complete structured source document before the package asks it to design any individual video or slide.**

> **The spoken narration is given its own dedicated editorial pass after the scientific content and slide structure have been reviewed.**

The normal sequence is:

```text
Source DOCX or text-readable PDF
  -> local format-aware semantic extraction
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

- reading the explicitly supplied DOCX or text-readable PDF;
- format-aware extraction into the common semantic block schema;
- for DOCX, extracting headings, paragraphs, tables, source order, and Office Math provenance;
- for PDF, extracting text blocks, font/heading cues, equation-like text where identifiable, and page provenance while filtering repeated page boilerplate where possible;
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

The package does **not** upload the binary DOCX or PDF directly to Gemini. The source is parsed locally first and normalized into a common structured extraction.

For DOCX input, headings, paragraphs, tables, source order, semantic heading paths, and readable Office Math tokens are extracted; raw OMML XML stays local. For PDF input, PyMuPDF extracts text blocks, font/heading cues, equation-like text where identifiable, and page provenance; repeated page headers/footers and page-number labels are filtered where possible. PDF page numbers remain provenance only and are not used as lesson boundaries. Image-only/scanned PDFs fail visibly rather than being silently OCRed.

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
  "math_text": ["..."]
}
```

Format-specific binary structures stay local. Embedded PDF figures/images are not yet supplied to Gemini as multimodal source material.

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

The recommended one-time Windows setup is to create:

```text
%LOCALAPPDATA%\Microvid\.env
```

containing:

```dotenv
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Every `microvid` command loads this file automatically. Existing process environment variables take precedence, so CI systems and temporary overrides continue to work. For a nonstandard location, set `MICROVID_CONFIG_DIR` to the directory containing `.env`.

Setting the API key for only the current PowerShell session is also supported:

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

`gemini-flash-latest` does not name one permanently fixed model. It is a Google-managed alias
that can move to a newer Flash release. That makes it useful when you want current behavior,
but two runs made at different times may not use the same underlying model. For repeatable
production or regression comparisons:

1. choose a concrete model ID that is available to your Gemini account;
2. set it in `course.llm.model` or pass `--model` where that command supports the option;
3. retain the generated plan/manifests, which record model provenance;
4. change the pinned ID deliberately after reviewing release behavior.

The package uses the official `google-genai` SDK. Model availability is controlled by the
Gemini service and the credentials in use, not by Microvid itself.

---

## 8. Configure Chirp TTS

For the simplest service-account setup, copy the authorized JSON file to:

```text
%LOCALAPPDATA%\Microvid\google_cloud_credentials.json
```

The package automatically sets `GOOGLE_APPLICATION_CREDENTIALS` before creating the Google Cloud TTS client. If the preferred filename is absent, it uses the only `*.json` file in that directory. It will not guess when several differently named JSON files are present. An existing `GOOGLE_APPLICATION_CREDENTIALS` value always takes precedence.

Application Default Credentials through the Google Cloud CLI remain supported as an alternative:

```powershell
gcloud auth application-default login
```

Ensure Cloud Text-to-Speech is enabled for the selected Google Cloud project.

The packaged production defaults are conceptually:

```yaml
tts:
  provider: google_cloud_chirp3
  language_code: en-US
  voice_name: en-US-Chirp-HD-F
  ssml_gender: FEMALE
  audio_encoding: LINEAR16
  speaking_rate: 0.8
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

## 9. Prepare the source document

The runtime source is always explicit. The bundled Lab 101 sample DOCX is never used automatically.

Supported source formats are:

```text
.docx
.pdf   (text-readable PDF)
```

Examples:

```text
source/my_course.docx
source/my_course.pdf
```

DOCX works best with meaningful Word heading styles and a coherent hierarchy. Paragraphs, tables, headings, and Office Math are extracted without depending on rendered Word page numbers.

PDF input is parsed natively with PyMuPDF. Repeated page headers/footers and page-number labels are filtered where possible, while page numbers are retained only for provenance. Image-only/scanned PDFs are rejected visibly because OCR is not invoked automatically. Embedded PDF figures/images are not yet passed to Gemini as multimodal source material.

---

## 10. Create a profile for a new course

For a new topic:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.pdf" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

The scaffold **does not pre-segment the source document into videos**. The generated `videos` list is intentionally empty.

Review and edit the course constraints that matter before global planning, especially course title, audience, target video/total duration, maximum slides, parser conventions, LLM model, narration rate, `narration_polish_pass`, editorial policy, and TTS settings.

Gemini will determine the lesson boundaries after reading the complete structured source.

---

## 11. Recommended staged workflow

The staged workflow is best for the first run of a new course because each intermediate artifact can be inspected.

### 11.1 Extract the source locally

```powershell
microvid extract `
  --source ".\source\my_course.pdf" `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

A `.docx` path can be supplied in exactly the same command.

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
  --source ".\source\my_course.pdf" `
  --workspace ".\workspace\my_course" `
  --profile ".\profiles\my_course.yaml"
```

The same command accepts a `.docx` source.

This performs fresh local extraction, global Gemini course planning/review, per-video lesson generation/review, dedicated narration polishing, whole-course consistency review/revision/verification, slide generation, and structural validation.

A normal `all` run replans after the fresh extraction. Use `--reuse-plan` only when deliberately reusing a plan; the package still checks that the source signature matches exactly.

---

## 13. Source-signature protection

`course_plan.yaml` stores:

```yaml
source_signature: <sha256>
```

The signature is generated from the complete prompt-facing extraction. If the source document changes and is re-extracted, the signature changes. A stale plan is not silently applied to a revised source.

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

### 14.1 Version-controlled instruction prompts

The package ships its LLM instructions under `src/microvid/prompts/`. These files are part of
the installed package, so prompt edits are code-package changes and should be reviewed,
tested, committed, and released like Python changes.

The prompts that directly control lesson slides and narration are:

| Prompt file | Purpose | Used automatically? |
| --- | --- | --- |
| `system_microcredential_architect.md` | Shared source-fidelity, pedagogy, slide, visual, narration and output rules | Yes |
| `lesson_generation.md` | Creates each lesson's slide stack and first narration | Yes |
| `lesson_review.md` | Reviews and revises scientific and pedagogical quality | Yes |
| `narration_polish.md` | Rewrites only the spoken narration/optional `tts_text` after the slide design is fixed | Yes |
| `global_course_planning.md` | Designs the whole course and lesson boundaries | Yes |
| `global_course_plan_review.md` | Reviews/revises that global plan | Yes |
| `global_course_consistency_review.md` | Checks the completed lesson set for consistency and coverage | Yes |
| `course_trailer_advertisement_video_generation.md` | Defines the editorial package for a promotional Video 00 | No; it is currently a guided/manual workflow |

For normal lesson generation, the system prompt is combined with `lesson_generation.md`;
the review pass combines it with `lesson_review.md`; and the dedicated narration pass combines
it with `narration_polish.md`. The trailer prompt is intentionally documented separately
because no `microvid trailer` command consumes it yet.

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
visual_type: process
visual_panels:
  - heading: Measure
    body: [record value and uncertainty]
  - heading: Propagate
    body: [combine source-supported contributions]
table_headers: []
table_rows: []
equation_latex: null
source_block_ids: [b0214, b0215]
estimated_seconds: 70
narration_word_count: 96
narration_estimated_spoken_seconds: 44.3
```

The manifest also records source assignments, Gemini provider/model, generation pass count, narration-polish provenance, design mode, narration-quality findings, visual structure, and automated production status.

---

## 16. Automated review and production gating

The normal workflow does not require a human approval flag. Lesson generation is followed by a grounded revision pass, dedicated narration polish, whole-course consistency review, targeted revision when necessary, and deterministic QA. Blocking QA findings stop the automated path; nonblocking warnings remain visible for diagnostics.

Generated lessons use:

```yaml
editorial_status: automated_ready
```

The status records that the lesson passed through the automated production workflow; it is not a claim that source ambiguities may be guessed. Ambiguous textbook boundaries and other unsafe source conditions still fail visibly.

You may still audition a representative TTS output or inspect a deck when desired, but this is optional quality observation rather than a required approval step.

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

After the lesson passes the automated generation/QA workflow:

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

## 19. Publish lesson videos to YouTube

First create and review the local publishing assets without remote writes:

```powershell
microvid youtube publish `
  --workspace .\workspace\my_course `
  --expected-channel @your_handle `
  --dry-run
```

Review `youtube/youtube_metadata.yaml` and `youtube/course_cover.jpg`, then repeat the command
without `--dry-run`. Publishing is public by default. State is saved after each remote action,
so rerunning the same command resumes an interrupted upload. If lesson MP4s change after an
upload, use the guarded replacement flags documented in
[YOUTUBE_PUBLISHING.md](YOUTUBE_PUBLISHING.md); do not delete the state file and start over.

YouTube publishing uses a Desktop OAuth client and a user consent token. The Google Cloud
service-account credential used for TTS cannot authorize channel uploads.

---

## 20. Create and publish a course trailer (Video 00)

The package includes the reusable editorial prompt
`src/microvid/prompts/course_trailer_advertisement_video_generation.md`. It defines a truthful
45–55 second promotional master, including positioning, narration, edit beats, clip selection,
overlays, title/CTA, adaptation notes and QA.

This is currently a guided production workflow, not an automated `microvid trailer` command.
Generate the trailer package from the completed course assets, assemble the final MP4 with the
course-native visuals and selected TTS voice, and store it in a dedicated location such as:

```text
workspace/my_course/trailer/video_00.mp4
```

Do **not** put `video_00.mp4` in `workspace/my_course/videos/` before running the standard
YouTube publisher. That command currently discovers every `video_*.mp4` in that directory and
requires one matching lesson manifest for each file; Video 00 therefore appears as an invalid
extra lesson. Upload the trailer separately and place it first in the playlist after the lesson
publisher completes. Follow [COURSE_TRAILER.md](COURSE_TRAILER.md) for the complete procedure.

---

## 21. Physics Laboratory 101 reference workflow

For the current PDF-source pilot, assume the runtime manual is:

```text
source/Physics_Laboratory_101_Student_Manual_v2.pdf
```

Run:

```powershell
microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2.pdf" `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

The corrected DOCX version remains equally valid when supplied explicitly with `--source`.

The existing nine-video definitions in the Lab 101 profile do not control the production segmentation in default global mode. They remain for legacy/profile comparison. Narration polishing is enabled explicitly in the Lab 101 profile.

---

## 22. Deterministic/debug generation

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

## 23. Development/cost controls

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

## 24. Large documents

The global planner sends the complete structured extraction during global planning and refuses silent truncation. The default global source limit is:

```yaml
max_source_characters: 800000
```

For a source larger than that limit, use a deliberate hierarchical planning strategy rather than arbitrary truncation.

---

## 25. Troubleshooting

### `microvid` is not recognized

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,windows]"
```

### Gemini authentication fails

```powershell
$env:GEMINI_API_KEY
```

If it is empty, confirm `%LOCALAPPDATA%\Microvid\.env` exists and contains `GEMINI_API_KEY=...`. Also confirm the configured model is available.

### PDF extraction fails with “too little extractable text”

The file is probably image-only/scanned or has insufficient embedded text. v0.8.0 deliberately does not invoke OCR automatically. Provide a text-readable PDF or a DOCX source.

### Narration polish fails with a speech-hygiene error

Inspect the Gemini output or source for raw LaTeX/code-like text or internal production language in the spoken channel. The narration editor is expected to verbalize mathematics naturally. Exact equations belong in `equation_latex`; TTS-specific wording belongs in `tts_text`.

### Narration has timing warnings

Compare `narration_word_count`, `narration_estimated_spoken_seconds`, and `estimated_seconds`. A warning means the script may sound rushed at the configured narration rate. Shorten repetition or increase the slide timing only when pedagogically justified.

### Existing plan is unexpectedly rebuilt

The extracted source signature no longer matches the stored plan. This is intentional protection against stale global plans.

### Whole-course review blocks slides

Inspect `global_consistency_initial.yaml` and `global_consistency_final.yaml`. Resolve remaining blocking findings. `--allow-unreviewed-course` should be used only for diagnostics.

### Chirp authentication fails

Confirm `%LOCALAPPDATA%\Microvid\google_cloud_credentials.json` exists, or that the directory contains exactly one JSON credential file. An explicit `GOOGLE_APPLICATION_CREDENTIALS` setting or `gcloud auth application-default login` may be used instead.

Also confirm Cloud Text-to-Speech is enabled and the project has suitable permissions/billing.

### YouTube publishing reports an extra lesson or missing manifest

Check `workspace/<course>/videos/` for a promotional `video_00.mp4` or any other MP4 that is
not listed in `manifests/course.yaml`. The lesson publisher requires a one-to-one match. Move
the trailer to `workspace/<course>/trailer/`, rerun publishing, then upload and position the
trailer separately as described in [COURSE_TRAILER.md](COURSE_TRAILER.md).

### YouTube OAuth or token refresh fails

Confirm that `youtube_client_secret.json` is a Desktop app OAuth credential, the YouTube Data
API is enabled, and the authorizing Google account owns or manages the intended channel. If a
request to `oauth2.googleapis.com` fails with a TLS/SSL connection error, check the system
clock, proxy or HTTPS inspection, firewall, and local certificate store before retrying. Keep a
backup of `youtube_token.json` before deliberately reauthorizing; never substitute the TTS
service-account JSON for the YouTube user token.

### FFmpeg is missing

Install the project with its Windows extra. This includes a supported FFmpeg binary through `imageio-ffmpeg`:

```powershell
python -m pip install -e ".[windows]"
microvid media-check
```

The media pipeline prefers `MICROVID_FFMPEG` when explicitly set, then the packaged binary, then `ffmpeg` on `PATH`. It stages FFmpeg inputs and outputs in the local system temporary directory before copying finished artifacts back, which supports Google Drive and other cloud-synced workspaces.

Each FFmpeg operation has a 300-second timeout. Override it only for unusually slow machines:

```powershell
$env:MICROVID_FFMPEG_TIMEOUT_SECONDS = "600"
```

### TTS pronounces equations badly

Use natural narration and explicit `tts_text` for difficult expressions. Do not feed raw LaTeX to TTS.

---

## 26. Recommended first production test

For any new course:

1. run `extract`;
2. inspect `document_structure.json`, especially heading structure and source provenance;
3. run `plan` and inspect `course_plan.yaml`;
4. run `draft`;
5. inspect the global consistency reports;
6. inspect one representative lesson manifest, paying special attention to the polished narration and timing metrics;
7. build its PPTX and check narration against the visual sequence;
8. audition/confirm the Chirp voice;
9. listen to the representative narrated lesson;
10. approve one lesson;
11. render one MP4;
12. only then batch-produce the rest of the course.

This staged pilot catches source-extraction, global segmentation, scientific content, narration style, voice, and media issues before they are multiplied across the course.
