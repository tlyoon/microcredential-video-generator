# Microcredential Video Generator — User Manual

**Package version:** 0.4.0  
**Repository:** `tlyoon/physics-lab-microcredential-video-generator`

This manual explains how to install, configure, and use the package to convert a structured Microsoft Word teaching document into short narrated microcredential videos.

The normal production pipeline is:

```text
Source DOCX
  -> semantic extraction
  -> Gemini lesson/slide abstraction
  -> reviewed YAML lesson manifests
  -> PowerPoint slide decks + speaker notes
  -> narration/notes/subtitles
  -> scientific-speech normalization
  -> Google Cloud Chirp 3 HD TTS
  -> rendered slides + per-slide audio
  -> FFmpeg assembly
  -> MP4 video
```

The bundled Physics Laboratory 101 profile is the reference implementation. The sample DOCX stored in `examples/sample_docs/` is an example only; the program never uses it implicitly. Every real build requires an explicit `--source` path.

---

## 1. What the package produces

A successful course build creates a workspace containing reusable intermediate products rather than only a final video. Typical output is:

```text
workspace/lab101/
  extracted/
    document_structure.json
  manifests/
    video_01.yaml
    video_02.yaml
    ...
  slides/
    video_01.pptx
    video_02.pptx
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
    video_01/
      slide_01.png
      ...
  audio/
    video_01/
      slide_01.wav
      ...
      tts_manifest.yaml
  segments/
    video_01/
      slide_01.mp4
      ...
  videos/
    video_01.mp4
    ...
```

The YAML manifest is the production record for a video. Each slide can contain concise on-screen content, a narration script, lecturer notes, a visual direction, an equation, source provenance, timing information, and optional TTS-specific text.

---

## 2. Recommended workstation

The complete media pipeline is designed primarily for a Windows PC because PowerPoint automation and the SAPI fallback are Windows-specific.

### Required for course-content generation

- Python 3.10 or newer.
- Git.
- A local clone of this repository.
- Internet access for Gemini generation.
- A Gemini API key stored in the `GEMINI_API_KEY` environment variable.

### Required for final MP4 production

- Microsoft PowerPoint desktop on Windows.
- FFmpeg available on `PATH`.
- Google Cloud Text-to-Speech credentials if Chirp 3 HD is used.
- Cloud Text-to-Speech enabled in the Google Cloud project used by the workstation.

Windows SAPI remains available as a fallback TTS provider.

---

## 3. Clone or update the repository

For a new workstation:

```powershell
git clone https://github.com/tlyoon/physics-lab-microcredential-video-generator.git
cd physics-lab-microcredential-video-generator
```

For an existing clone:

```powershell
git switch main
git pull --ff-only
```

---

## 4. Create the Python environment

The repository contains a setup helper:

```powershell
.\scripts\setup-local.ps1
```

It creates `.venv`, activates it, upgrades `pip`, and installs the package in editable mode with development and Windows dependencies.

Equivalent manual commands are:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,windows]"
```

After installation, verify that the CLI is visible:

```powershell
microvid --help
```

---

## 5. Configure Gemini

The normal content-authoring path uses Gemini. The package does not silently switch to the deterministic builder if Gemini credentials are missing.

Set the API key in the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

The model is configured in the course profile and can also be overridden on the command line with `--model`.

For example:

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101 `
  --model gemini-flash-latest
```

The default lesson-generation workflow performs an initial LLM generation pass followed by a grounded review/revision pass. Use `--no-review-pass` only when intentionally producing a faster first-pass draft.

---

## 6. Configure Google Cloud Chirp 3 HD

The production TTS default is Google Cloud Chirp 3 HD. The default packaged voice is:

```text
en-GB-Chirp3-HD-Leda
```

The default configuration is conceptually:

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

The repository contains an editable example at:

```text
examples/tts/chirp3.example.yaml
```

### 6.1 Authenticate Google Cloud locally

A normal local-development setup uses Application Default Credentials:

```powershell
gcloud auth application-default login
```

Do not commit Google credential files or API keys to Git.

### 6.2 Audition the bundled female voices

Before producing a full course, compare the candidate voices using the same scientific narration:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The example configuration includes Leda, Aoede, and Kore.

To audition a particular voice explicitly:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --voice en-GB-Chirp3-HD-Aoede `
  --language-code en-GB
```

Once a voice is chosen for a course, keep the same voice throughout the series unless there is a deliberate pedagogical reason to change it.

---

## 7. Prepare the source DOCX

A source document should preferably use real Word heading styles such as `Heading 1`, `Heading 2`, and `Heading 3`. The Physics Laboratory 101 parser profile recognizes standard heading styles, outline levels, and the configured semantic patterns.

The engine does not use page numbers. Pagination, margins, font sizes, and page breaks may therefore change without changing lesson selection.

For production use, keep the actual source document wherever convenient, for example:

```text
source/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

The program must still be told the path explicitly.

The bundled file:

```text
examples/sample_docs/Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

is reference/sample data only and is never selected automatically.

---

## 8. Fastest complete Lab 101 content build

After configuring the Gemini API key, run:

```powershell
microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

`microvid all` performs four stages:

1. semantic DOCX extraction;
2. Gemini lesson-manifest generation and review;
3. PowerPoint deck generation;
4. structural validation.

It does **not** automatically render final videos. Media production is a deliberate later step after human review.

---

## 9. Recommended staged workflow

For production work, running the stages separately is easier to inspect and troubleshoot.

### Stage A — Extract the DOCX

```powershell
microvid extract `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Primary output:

```text
workspace/lab101/extracted/document_structure.json
```

This file records the semantic document blocks and source provenance used by later stages.

### Stage B — Generate lesson manifests with Gemini

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Outputs include:

```text
workspace/lab101/manifests/video_01.yaml
workspace/lab101/manifests/video_02.yaml
...
```

The same stage also writes human-readable narration, lecturer notes, and SRT subtitle files.

A deterministic builder is available for debugging/offline testing:

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101 `
  --generator deterministic
```

Do not treat deterministic output as the preferred instructional-authoring path.

### Stage C — Build PowerPoint decks

Build every available deck:

```powershell
microvid slides `
  --workspace ".\workspace\lab101"
```

Or only one video:

```powershell
microvid slides `
  --workspace ".\workspace\lab101" `
  --video V05
```

The PPTX contains the visual slide content. Narration, lecturer notes, visual directions, and source provenance are also carried in the presentation notes where supported by the generator.

### Stage D — Validate the workspace

```powershell
microvid validate `
  --workspace ".\workspace\lab101"
```

Do not proceed to final publication merely because the command reports no structural errors; scientific and editorial review is still required.

---

## 10. Review before video rendering

LLM-generated lesson manifests begin as draft material requiring review. Inspect at least:

- scientific correctness;
- fidelity to the source DOCX;
- equations, units, numerical values, and assumptions;
- slide density and readability;
- narration naturalness;
- narration timing;
- pronunciation of scientific terms and symbols;
- conceptual-check quality;
- source provenance.

Final media rendering is blocked unless the manifest has:

```yaml
editorial_status: approved
```

For a private preview only, the media command can be run with `--allow-draft`.

A sensible pilot is one technically demanding lesson such as V05 before generating the entire course.

---

## 11. Scientific speech handling

The narration is written for speech, while exact mathematics remains separately represented for display.

Before TTS, common scientific notation can be normalized. Examples include:

```text
±       -> plus or minus
%       -> percent
Ω       -> ohms
π       -> pi
m s⁻²   -> metres per second squared
```

This normalizer is deliberately conservative. It is not a complete general LaTeX-to-speech engine.

For a slide requiring an exact spoken rendering, edit its manifest to provide `tts_text`:

```yaml
equation_latex: >
  g = \frac{4\pi^2}{m}

narration: >
  The fitted slope allows us to determine gravitational acceleration.

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

The displayed equation remains mathematically precise while the TTS engine receives natural spoken language.

For a small local pronunciation correction, a slide may also define `tts_replacements`.

---

## 12. Check media-production capability

Before rendering MP4 files, run:

```powershell
microvid media-check
```

The command reports whether the current machine can see items such as FFmpeg, PowerPoint automation support, Windows SAPI support, and the Google Cloud TTS Python package.

Correct any missing prerequisite before attempting final rendering.

---

## 13. Render one video to MP4

After reviewing and approving the corresponding lesson manifest:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The renderer performs the following sequence:

```text
video_05.pptx
  -> PowerPoint exports slide PNG files
  -> narration is converted to speech-ready text
  -> Chirp produces one audio file per slide
  -> FFmpeg produces one video segment per slide
  -> FFmpeg concatenates all segments
  -> workspace/lab101/videos/video_05.mp4
```

The TTS production log is written to:

```text
workspace/lab101/audio/video_05/tts_manifest.yaml
```

Inspect it when auditing a build. It records the actual provider, voice, language, audio path, and normalized spoken text used for each slide.

---

## 14. Override the voice or speaking rate

A one-off voice override does not require editing Python:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --voice-name en-GB-Chirp3-HD-Aoede
```

A speaking-rate override is similarly possible:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --speaking-rate 0.95
```

Other available TTS overrides include:

```text
--tts-provider
--voice-name
--language-code
--speaking-rate
--tts-location
--no-tts-fallback
```

Use `--no-tts-fallback` for final production if you prefer the build to fail rather than silently change from Chirp to the configured fallback provider.

---

## 15. Generate a private preview before approval

If you need to inspect pacing and visual synchronization before formally approving the manifest:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --allow-draft
```

Treat the resulting MP4 as a preview, not a publication-ready asset.

---

## 16. Use the package with a different DOCX or subject

The Python engine is designed so a new topic does not require editing the engine source code.

For a new structured DOCX, first create a starter profile:

```powershell
microvid scaffold-profile `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --output ".\profiles\heat_transfer.yaml" `
  --course-id "heat_transfer" `
  --title "Introduction to Heat Transfer"
```

Then review and edit the generated YAML profile. In particular, verify:

- lesson titles and boundaries;
- semantic source selectors;
- learning outcomes;
- target durations;
- slide limits;
- subject-specific priority terms;
- Gemini model settings;
- TTS settings if they differ from the defaults.

Then use the new profile:

```powershell
microvid all `
  --source ".\source\Introduction_to_Heat_Transfer.docx" `
  --workspace ".\workspace\heat_transfer" `
  --profile ".\profiles\heat_transfer.yaml"
```

The engine selects content semantically rather than by page number. A profile can contain selectors such as:

```yaml
core_selectors:
  - heading_contains: "Conduction"
```

If the source is materially reorganized or the configured heading no longer exists, revise the profile rather than assuming the generator can infer the author's new intent safely.

---

## 17. Profile configuration philosophy

Keep course-specific decisions in YAML rather than Python whenever possible.

Typical profile responsibilities include:

- parser conventions;
- course title and audience;
- lesson definitions;
- target video duration;
- slide limit;
- narration words per minute;
- content-selection priority terms;
- Gemini provider/model/thinking level;
- editorial policy;
- optional TTS configuration.

The Python engine should remain reusable across subjects.

---

## 18. Common CLI commands

```text
microvid extract           Extract semantic blocks from an explicit DOCX
microvid scaffold-profile  Create a starter profile for a new DOCX/topic
microvid draft             Generate lesson manifests and text assets
microvid slides            Build PowerPoint decks
microvid validate          Run structural QA
microvid all               Extract + draft + slides + validate
microvid media-check       Check local media capabilities
microvid tts-audition      Compare candidate TTS voices
microvid media             Render one lesson to MP4
```

Use the built-in help for any command:

```powershell
microvid media --help
microvid draft --help
microvid tts-audition --help
```

---

## 19. Troubleshooting

### `GEMINI_API_KEY` is missing

Set it in the current shell before running `draft` or `all` with the default LLM generator:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

### Chirp authentication fails

Configure Google Cloud Application Default Credentials and confirm the intended Google Cloud project has Cloud Text-to-Speech enabled.

```powershell
gcloud auth application-default login
```

### Chirp unexpectedly uses SAPI

The default configuration permits fallback. Inspect:

```text
audio/video_NN/tts_manifest.yaml
```

For final production, rerun with:

```text
--no-tts-fallback
```

so a Chirp error stops the build.

### `ffmpeg is not available on PATH`

Install FFmpeg and make sure a new PowerShell session can run:

```powershell
ffmpeg -version
```

### PowerPoint rendering fails

The current renderer requires Windows, Microsoft PowerPoint desktop, and the Windows Python dependencies installed through `.[windows]`.

Run:

```powershell
microvid media-check
```

before troubleshooting further.

### Manifest/deck missing

Run the earlier stages first:

```powershell
microvid extract ...
microvid draft ...
microvid slides ...
```

or run `microvid all`.

### Media rendering says the lesson is not approved

Review the YAML manifest and set:

```yaml
editorial_status: approved
```

only after scientific/editorial approval. Use `--allow-draft` only for a private preview.

### A renamed/reorganized document no longer matches the profile

Update the semantic `heading_contains` selectors or scaffold/review a new profile. Do not solve structural drift by hard-coding page numbers.

### Scientific pronunciation sounds wrong

Prefer, in order:

1. improve the Gemini narration so it is naturally speakable;
2. add `tts_text` for that slide;
3. add a small `tts_replacements` mapping;
4. use the generic scientific normalizer only for common symbols/units.

---

## 20. Recommended production procedure for Physics Laboratory 101

For the first real course production, use this sequence:

```text
1. Pull latest main.
2. Run setup-local.ps1.
3. Configure GEMINI_API_KEY.
4. Configure Google Cloud ADC for Chirp.
5. Run tts-audition and choose the course voice.
6. Run microvid all on the explicit corrected Lab 101 DOCX.
7. Inspect the nine YAML manifests.
8. Inspect the generated PPTX decks and speaker notes.
9. Run microvid validate.
10. Select V05 as the first media pilot.
11. Correct scientific wording, slide density, TTS text, and timing as needed.
12. Set only V05 to editorial_status: approved.
13. Render V05 with --no-tts-fallback.
14. Review the MP4 on desktop and phone.
15. Once the style is accepted, apply the same review procedure to V01–V09.
```

This staged approach keeps content generation, scientific review, voice generation, and final media rendering independently inspectable.

---

## 21. Important design rules

1. The runtime source DOCX is always explicit; the bundled sample is never an implicit source.
2. The video is an instructional abstraction, not a spoken copy of the manual.
3. Gemini is the normal content-authoring path; deterministic generation is a debugging/offline fallback.
4. Exact equations and natural spoken equations are separate concerns.
5. Every slide should remain traceable to authoritative source blocks.
6. TTS is downstream from lesson authoring; changing a voice should not require regenerating lesson content.
7. Final MP4 generation should happen only after scientific and editorial review.
8. Keep configuration in profiles/YAML rather than adding subject-specific logic to the Python engine.
9. Preserve intermediate assets so problems can be corrected locally without rebuilding unrelated stages.
10. For final production, prefer explicit failure over silent fallback when consistency matters.

---

## 22. Minimal end-to-end command sequence

For an already configured workstation, the shortest practical sequence is:

```powershell
git switch main
git pull --ff-only

.\.venv\Scripts\Activate.ps1

$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

gcloud auth application-default login

microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"

microvid all `
  --source ".\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx" `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101

microvid validate `
  --workspace ".\workspace\lab101"

# After reviewing V05 and setting editorial_status: approved:
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml" `
  --no-tts-fallback
```

The final video is then expected at:

```text
workspace/lab101/videos/video_05.mp4
```

---

## 23. Related documentation

- `README.md` — project overview and short examples.
- `docs/ARCHITECTURE.md` — internal architecture.
- `docs/PILOT_WORKFLOW.md` — pilot-production workflow.
- `docs/CHIRP_TTS.md` — Chirp-specific setup and voice usage.
- `examples/tts/chirp3.example.yaml` — editable Chirp configuration example.
- `src/microvid/profiles/physics_lab_101.yaml` — bundled Lab 101 course profile.

For normal use, start with this manual and refer to the specialist documents only when needed.
