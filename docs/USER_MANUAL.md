# Microcredential Video Generator — User Manual

**Package version:** 0.5.0  
**Preferred repository name:** `microcredential-video-generator`  
**CLI command:** `microvid`

This manual explains how to install, configure, and use the package to convert a structured teaching DOCX into short narrated microcredential videos. Physics Laboratory 101 is the bundled reference implementation; the software itself is designed to be reusable for other topics with similar document structure.

## 1. What the package does

The normal production pipeline is:

```text
Source DOCX
  -> semantic extraction with provenance
  -> course/profile-based source selection
  -> Google Gemini slide/narration authoring by default
  -> grounded LLM review/revision
  -> YAML lesson manifests
  -> PowerPoint slide decks with speaker notes
  -> narration, lecturer-note and SRT assets
  -> scientific-speech normalization
  -> Google Cloud Chirp 3 HD TTS by default
  -> rendered slide images + per-slide audio
  -> FFmpeg assembly
  -> MP4 video
```

The package deliberately preserves intermediate files. A final MP4 is not the only output; the PowerPoint, narration, notes, subtitles, manifests, and TTS provenance remain independently inspectable and editable.

## 2. Important design rules

### 2.1 The runtime DOCX is explicit

Every production run requires `--source`. The program never silently chooses the sample DOCX stored in the repository.

### 2.2 The sample Physics Lab 101 DOCX is reference data only

The tracked example is located under:

```text
examples/sample_docs/
```

It demonstrates the expected kind of structured teaching document and supports testing/reference. It is not a hidden default input.

### 2.3 Pagination does not control generation

The parser works from Word structure, heading paths, paragraphs, tables, equations, and source order. Moving text between pages, changing margins, or inserting page breaks should not alter semantic source selection.

### 2.4 LLM content generation is the normal path

Gemini is used to abstract selected source material into a compact pedagogical slide stack and narration rather than simply copying the DOCX into slides.

### 2.5 Final videos require explicit approval

Generated lesson manifests begin in a review-required state. Final media rendering is blocked until the manifest is marked:

```yaml
editorial_status: approved
```

Use `--allow-draft` only for private previews.

## 3. Recommended workstation

The complete media path is designed primarily for Windows because PowerPoint automation and the SAPI fallback are Windows-specific.

Recommended software:

- Windows 10 or 11;
- Python 3.10 or later;
- Microsoft PowerPoint desktop;
- Git;
- FFmpeg on `PATH`;
- Google Cloud CLI (`gcloud`) for Application Default Credentials;
- a Gemini API key;
- access to a Google Cloud project with Cloud Text-to-Speech enabled.

Content extraction, LLM authoring, and PowerPoint-file generation are Python operations. Final slide rendering uses PowerPoint automation on Windows.

## 4. Clone and update the repository

After the GitHub repository has been renamed to the preferred generic slug, a fresh clone should use:

```powershell
git clone https://github.com/tlyoon/microcredential-video-generator.git
cd microcredential-video-generator
```

If you already cloned the repository under its earlier Physics-specific name, GitHub normally redirects the old repository URL after a rename. You may nevertheless update the remote explicitly:

```powershell
git remote set-url origin https://github.com/tlyoon/microcredential-video-generator.git
```

For routine updates:

```powershell
git switch main
git pull --ff-only
```

## 5. Install the local Python environment

From the repository root:

```powershell
.\scripts\setup-local.ps1
```

Or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,windows]"
```

The package installs the `microvid` CLI.

Check it with:

```powershell
microvid --help
```

Run regression tests:

```powershell
python -m pytest
```

## 6. Configure Gemini

The bundled profile uses Gemini as the default LLM provider through the official `google-genai` SDK.

Set the API key in the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Do not store the key in Git.

The model is soft-coded in the course profile and may also be overridden at the CLI. The bundled profile currently uses:

```yaml
course:
  llm:
    provider: gemini
    model: gemini-flash-latest
    thinking_level: high
    review_pass: true
```

For a reproducible production build, you may replace the moving alias with an exact supported model name in your local profile or pass `--model`.

## 7. Configure Google Cloud Chirp TTS

Google Cloud Chirp 3 HD is the default production TTS provider. Configure Application Default Credentials:

```powershell
gcloud auth application-default login
```

Ensure Cloud Text-to-Speech is enabled in the Google Cloud project used for synthesis.

The default TTS configuration is conceptually:

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

A standalone sample configuration is provided at:

```text
examples/tts/chirp3.example.yaml
```

## 8. Audition voices before producing a course

Generate identical sample narration with the configured candidate voices:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The packaged candidates include Leda, Aoede, and Kore. Select one consistent narrator for a course unless there is a deliberate pedagogical reason to vary voices.

To audition an explicit voice:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --voice en-US-Chirp3-HD-Aoede `
  --language-code en-US
```

## 9. Prepare a runtime source DOCX

Place the working document somewhere convenient, for example:

```text
source/my_course.docx
```

The `source/` directory is intended for local runtime material and should not be used as a place to commit production credentials or unrelated artifacts.

For best results, use meaningful Word heading styles and a coherent hierarchical structure. Tables, paragraphs, and Office Math can be extracted. A document with completely inconsistent visual-only headings may require parser/profile adjustment.

## 10. Physics Laboratory 101: first full content build

Assume the corrected runtime manual is:

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

This performs extraction, Gemini-based lesson drafting, PowerPoint generation, and structural validation.

For a cheaper/diagnostic run without LLM authoring:

```powershell
microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101_debug" `
  --profile physics_lab_101 `
  --generator deterministic
```

The deterministic mode is not the preferred content-authoring workflow.

## 11. Run stages separately when reviewing or debugging

### 11.1 Extract

```powershell
microvid extract `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Inspect:

```text
workspace/lab101/extracted/document_structure.json
```

### 11.2 Draft manifests with Gemini

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

The default performs generation followed by grounded LLM review/revision.

Use `--no-review-pass` only when deliberately making a cheaper first-pass draft.

### 11.3 Build PowerPoint decks

```powershell
microvid slides `
  --workspace ".\workspace\lab101"
```

Build one lesson only:

```powershell
microvid slides `
  --workspace ".\workspace\lab101" `
  --video V05
```

### 11.4 Validate

```powershell
microvid validate `
  --workspace ".\workspace\lab101"
```

Validation checks structure; it does not replace expert review of scientific correctness, pedagogical quality, narration, or visual design.

## 12. Understand the generated workspace

A typical workspace contains:

```text
workspace/course/
  extracted/
    document_structure.json
  manifests/
    video_01.yaml
    video_02.yaml
    ...
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

The lesson manifest is the most important production record. Each slide may contain:

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

## 13. Review a lesson before video production

For the Lab 101 pilot, V05 is useful because it exercises equations, units, worked examples, narration, source grounding, and technical interpretation.

Review:

- source block IDs against the authoritative DOCX;
- equations and assumptions;
- numerical values and units;
- visible slide density;
- narration naturalness;
- estimated timing;
- visual directions;
- assessment/check question;
- scientific speech of symbols and units.

When satisfied, change:

```yaml
editorial_status: llm_draft_requires_review
```

to:

```yaml
editorial_status: approved
```

## 14. Scientific speech and TTS text

Exact mathematics belongs in the mathematical representation, while spoken language should be natural.

Example:

```yaml
equation_latex: >
  g = \frac{4\pi^2}{m}

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

The package normalizes common symbols conservatively, including representations such as plus/minus, percent, pi, ohms, and common SI-unit expressions.

If the automatic form is not satisfactory, set `tts_text` explicitly for that slide. A local `tts_replacements` mapping may also correct a specific pronunciation without altering the displayed content.

## 15. Generate the MP4

After approval:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml" `
  --no-tts-fallback
```

The final file is normally:

```text
workspace/lab101/videos/video_05.mp4
```

The media step:

1. exports each PowerPoint slide as a PNG;
2. obtains narration/`tts_text` from the manifest;
3. normalizes scientific speech where enabled;
4. synthesizes one audio file per slide;
5. combines each PNG and audio file into an MP4 segment;
6. concatenates the segments into the lesson video.

For final production, `--no-tts-fallback` is recommended so a Chirp failure does not silently switch the narrator to Windows SAPI.

## 16. TTS audit trail

The package writes:

```text
workspace/<course>/audio/video_NN/tts_manifest.yaml
```

This records the requested TTS configuration and the actual provider, voice, locale, audio file, and spoken text used for each slide.

Check this file when voice consistency matters.

## 17. Use the package with a different topic

For a new structured teaching document, create a starter profile:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

Review the generated profile carefully. Confirm:

- course/audience metadata;
- parser conventions;
- lesson boundaries;
- semantic source selectors;
- learning outcomes;
- priority terms;
- duration and slide targets;
- LLM settings;
- TTS settings.

Then run the same pipeline using that profile path:

```powershell
microvid all `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --profile ".\profiles\heat_transfer.yaml"
```

A similarly structured replacement document should not require Python modification. Major semantic/structural changes may require profile edits, and required selectors that no longer match should fail visibly rather than cause silent guessing.

## 18. Configuration precedence

For TTS, effective settings are resolved from:

1. built-in defaults;
2. `course.tts` in the selected profile;
3. standalone `--tts-config` YAML;
4. explicit CLI overrides.

Examples:

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --voice-name en-GB-Chirp3-HD-Aoede `
  --speaking-rate 0.95
```

For LLM generation, profile values can similarly be overridden with options such as:

```powershell
--model "MODEL_NAME"
--thinking-level high
```

See [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for details.

## 19. Media capability check

Run:

```powershell
microvid media-check
```

This reports whether the local environment can see components such as FFmpeg, Windows/PowerPoint automation support, SAPI, and the Google Cloud TTS Python package.

## 20. Common problems

### `microvid` is not recognized

Activate the virtual environment and reinstall editable package dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,windows]"
```

### Gemini authentication fails

Verify:

```powershell
$env:GEMINI_API_KEY
```

and confirm that the selected model is available to the API key/account.

### Chirp authentication fails

Refresh Application Default Credentials:

```powershell
gcloud auth application-default login
```

Also confirm the Cloud Text-to-Speech API is enabled and billing/permissions permit synthesis.

### FFmpeg is unavailable

Ensure:

```powershell
ffmpeg -version
```

works from the same terminal.

### Final media is blocked

Check the manifest status. It must be `approved` unless deliberately using `--allow-draft` for a private preview.

### TTS pronounces mathematics badly

Do not put raw LaTeX into the spoken channel. Add a clear `tts_text` field for the slide and optionally `tts_replacements` for local corrections.

### A revised DOCX no longer matches the profile

Inspect `document_structure.json` and update semantic selectors. Do not weaken the pipeline into silently accepting unrelated sections.

## 21. Repository rename and local clones

The preferred generic GitHub slug is:

```text
microcredential-video-generator
```

The runtime package does not depend on the repository slug. After the GitHub repository is renamed, existing clones may continue to work through GitHub redirects, but updating the remote is cleaner:

```powershell
git remote set-url origin https://github.com/tlyoon/microcredential-video-generator.git
```

Verify:

```powershell
git remote -v
```

## 22. Recommended production practice

For a new course:

1. preserve an authoritative source DOCX;
2. create/review a course profile;
3. generate one technically demanding pilot lesson;
4. review source grounding and slide pedagogy;
5. audition and lock a narrator voice;
6. review scientific speech;
7. approve and render the pilot;
8. use the accepted conventions for the rest of the course;
9. keep manifests, decks, TTS provenance, and final MP4s together in a course-specific workspace.

This staged approach keeps the system reusable without surrendering scientific/editorial control.

## 23. Related documentation

- [README](../README.md)
- [Architecture](ARCHITECTURE.md)
- [Configuration reference](CONFIGURATION_REFERENCE.md)
- [Chirp TTS guide](CHIRP_TTS.md)
- [Physics Lab 101 pilot workflow](PILOT_WORKFLOW.md)
- [Changelog](../CHANGELOG.md)
