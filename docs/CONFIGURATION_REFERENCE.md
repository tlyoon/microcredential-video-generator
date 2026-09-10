# Configuration Reference

This document describes the configuration surfaces of **Microcredential Video Generator v0.5.0**. Runtime behavior is intentionally soft-coded: course-specific content, model choice, source selection, lesson boundaries, TTS voice, and media options should be changed through YAML or CLI options rather than by editing Python.

## 1. Configuration precedence

For TTS, settings are resolved in this order, from lowest to highest priority:

1. built-in `TTSConfig` defaults;
2. `course.tts` in the selected course profile;
3. standalone `--tts-config` YAML;
4. explicit CLI overrides.

For LLM generation, the course profile supplies defaults and CLI options such as `--model` and `--thinking-level` override them.

## 2. Course profile

A course profile is YAML. The bundled reference profile is:

```text
src/microvid/profiles/physics_lab_101.yaml
```

The Physics Lab profile is an example of a course-specific layer. The Python engine itself does not require Physics terminology.

### 2.1 Parser configuration

Typical parser configuration:

```yaml
parser:
  heading_style_patterns:
    - '^Heading\s*(\d+)$'
  use_outline_level: true
  infer_numbered_headings: false
  section_number_regex: '^(\d+(?:\.\d+)*)\.?\s+'
```

Important behavior:

- pagination is ignored;
- heading levels and semantic breadcrumb paths are retained;
- numeric section labels are optional metadata rather than the primary selector;
- custom heading patterns may be supplied for non-standard Word documents;
- Office Math provenance is retained during extraction.

### 2.2 Course metadata

Example:

```yaml
course:
  id: physics_lab_101
  title: Physics Laboratory 101
  audience: First-year undergraduate physics students
  narration_wpm: 130
  max_slides: 7
  target_video_minutes: 6
```

These values guide lesson construction but do not identify the software package itself.

### 2.3 LLM settings

Example:

```yaml
course:
  llm:
    provider: gemini
    model: gemini-flash-latest
    thinking_level: high
    api_key_env: GEMINI_API_KEY
    review_pass: true
    max_source_characters_per_lesson: 220000
```

`provider` selects the LLM backend. The shipped backend is Gemini.

`model` is deliberately configuration data. A moving alias can be used for convenience, while a pinned model is preferable when exact reproducibility of a production build is required.

`thinking_level` controls the configured reasoning effort where supported.

`api_key_env` identifies the environment variable containing the Gemini API key. Credentials must not be committed to Git.

`review_pass` enables the default two-pass workflow: generation followed by an independent grounded review/revision.

### 2.4 Content-selection settings

Course profiles may define ranking and compression rules such as:

```yaml
course:
  content_selection:
    priority_terms:
      - uncertainty
      - measurement
      - graph
    priority_term_score: 2
    preferred_min_chars: 40
    preferred_max_chars: 500
    source_words_per_slide: 110
    max_context_blocks: 6
```

These terms belong to the course profile, not the engine. A different discipline should supply its own terms.

### 2.5 Lesson definitions

A lesson may use semantic source selectors:

```yaml
videos:
  - id: V05
    title: Propagation of Uncertainty
    target_minutes: 7
    max_slides: 8
    core_selectors:
      - heading_contains: "Propagation of uncertainty"
```

Semantic selectors are preferred over fixed page numbers and brittle section-number ranges. Renumbering a heading should not normally break a semantic selector. If a required topic disappears or is materially renamed, the pipeline should fail visibly rather than silently substitute unrelated material.

## 3. Standalone TTS configuration

Example file:

```text
examples/tts/chirp3.example.yaml
```

Typical contents:

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
  audition_voices:
    - en-GB-Chirp3-HD-Leda
    - en-GB-Chirp3-HD-Aoede
    - en-GB-Chirp3-HD-Kore
```

### 3.1 TTS fields

`provider` — currently `google_cloud_chirp3` or `sapi`.

`language_code` — locale passed to the TTS provider, for example `en-GB`.

`voice_name` — provider-specific voice identifier.

`audio_encoding` — Google Cloud output encoding. The default `LINEAR16` produces WAV output in the package.

`speaking_rate` — configured speaking pace.

`location` — Google Cloud Text-to-Speech endpoint location. `global` uses the default endpoint.

`normalize_scientific_speech` — enables conservative conversion of common scientific notation before synthesis.

`fallback_provider` — secondary provider attempted when the primary provider fails.

`fallback_on_error` — whether fallback is permitted. For final production, `--no-tts-fallback` is recommended when voice consistency must be guaranteed.

`audition_voices` — voices used by `microvid tts-audition` when no explicit `--voice` options are supplied.

## 4. Per-slide TTS overrides

A lesson manifest may provide a specific spoken rendering:

```yaml
narration: >
  The fitted relationship allows us to calculate gravitational acceleration.

equation_latex: >
  g = \frac{4\pi^2}{m}

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

`tts_text` affects speech only. It does not replace the human-readable narration or on-screen equation.

A small local pronunciation replacement mapping may also be supplied:

```yaml
tts_replacements:
  "u_xbar": "standard uncertainty of the mean"
```

Use explicit overrides for expressions whose correct spoken form cannot be inferred reliably from plain text.

## 5. CLI overrides

### LLM

```powershell
microvid draft `
  --workspace ".\workspace\course" `
  --profile my_course `
  --model "MODEL_NAME" `
  --thinking-level high
```

### TTS provider

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --tts-provider google_cloud_chirp3
```

### Voice

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --voice-name en-GB-Chirp3-HD-Aoede
```

### Speaking rate

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --speaking-rate 0.95
```

### Disable fallback

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --no-tts-fallback
```

## 6. Environment variables and credentials

Gemini authoring normally requires:

```powershell
$env:GEMINI_API_KEY = "..."
```

Google Cloud Chirp normally uses Application Default Credentials. A common local setup is:

```powershell
gcloud auth application-default login
```

Do not commit API keys, OAuth tokens, service-account JSON files, or other credentials.

## 7. Runtime source selection

Every production build requires an explicit source path:

```powershell
microvid all `
  --source ".\source\course.docx" `
  --workspace ".\workspace\course" `
  --profile my_course
```

The sample DOCX under `examples/sample_docs/` is not used unless the user explicitly passes its path.

## 8. Workspace isolation

Use a different workspace for each course or source revision:

```text
workspace/
  lab101/
  heat_transfer/
  optics_2027/
```

This prevents manifests, slide decks, TTS output, and MP4s from unrelated projects from being mixed.

## 9. Editorial status

The media stage expects explicit approval:

```yaml
editorial_status: approved
```

Use `--allow-draft` only for private previews. It should not be treated as a substitute for scientific/editorial review.

## 10. Repository-name independence

The Python distribution is `microcredential-video-generator`, and the CLI is `microvid`. Runtime code does not depend on the GitHub repository slug. Internal documentation uses relative paths wherever possible. Renaming the GitHub repository therefore does not require changing source code or local workspace formats.
