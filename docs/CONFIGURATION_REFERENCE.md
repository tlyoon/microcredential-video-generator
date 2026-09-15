# Configuration Reference

This document describes the configuration surfaces of **Microcredential Video Generator v0.8.0**. The production default is whole-document Gemini course design, globally informed lesson generation/review, a dedicated narration-only polish pass, whole-course consistency review, then local slide/TTS/media production. Runtime sources may be structured DOCX files or text-readable PDFs.

## 1. Configuration precedence

For LLM generation, the selected course profile supplies defaults and CLI options such as `--model` and `--thinking-level` override them.

For TTS, settings are resolved in this order, from lowest to highest priority:

1. built-in `TTSConfig` defaults;
2. `course.tts` in the selected course profile;
3. standalone `--tts-config` YAML;
4. explicit CLI overrides.

## 2. Course profile in global mode

A global-mode profile is primarily a **constraint profile**. It describes the audience, source role, parser behavior, timing targets, LLM settings, editorial policy, and TTS preferences. It does not need to predefine the videos.

Example:

```yaml
course:
  id: heat_transfer
  title: Introduction to Heat Transfer
  audience: First-year engineering students
  source_role: The explicitly supplied DOCX or text-readable PDF is the authoritative content source.
  design_principle: Video teaches the reasoning; the source document carries the detail.
  narration_wpm: 130
  max_slides: 7
  target_video_minutes: 6
  target_total_minutes: 55

  llm:
    provider: gemini
    model: gemini-flash-latest
    thinking_level: high
    api_key_env: GEMINI_API_KEY
    review_pass: true
    narration_polish_pass: true
    max_source_characters_per_lesson: 220000
    prompt_set: global_design_v1+microcredential_v3+narration_polish_v1
    global_design:
      enabled: true
      max_source_characters: 800000
      max_videos: 30
      plan_review_pass: true
      course_consistency_review: true

parser:
  heading_style_patterns:
    - '^Heading\s*(\d+)$'
  use_outline_level: true
  infer_numbered_headings: false

videos: []
```

The empty `videos` list is deliberate in a newly scaffolded global-first profile. Gemini designs the actual lesson sequence after reading the whole extracted source.

## 3. Parser configuration

The source dispatcher chooses the local parser from the file extension: `.docx` uses the DOCX parser and `.pdf` uses the PyMuPDF parser. Both produce the same downstream semantic block schema.

Shared/typical parser settings:

```yaml
parser:
  heading_style_patterns:
    - '^Heading\s*(\d+)$'
  use_outline_level: true
  infer_numbered_headings: false
  section_number_regex: '^(\d+(?:\.\d+)*)\.?\s+'
  key_idea_patterns:
    - '^key\s+idea\b'
  worked_example_patterns:
    - '^worked\s+example\b'
    - '^example\b'
```

DOCX behavior:

- rendered Word pagination is ignored;
- semantic heading breadcrumb paths are retained;
- numeric section labels are optional metadata;
- custom heading patterns may be supplied;
- paragraphs, tables, headings, source order, and Office Math provenance are extracted locally.

PDF behavior:

- text is extracted locally with PyMuPDF; no intermediate DOCX conversion is required;
- physical page numbers are retained only in block provenance metadata and are not used for lesson segmentation;
- repeated headers/footers and page-number labels are filtered where possible;
- heading levels are inferred from numbered headings plus font prominence/boldness;
- equation-like blocks may be identified from math-font prevalence;
- image-only/scanned PDFs fail visibly when too little extractable text is present; OCR is not invoked automatically;
- embedded figures/images are not yet passed to Gemini as multimodal inputs.

Optional PDF-tuning keys include:

```yaml
parser:
  pdf_min_extractable_characters: 100
  pdf_header_footer_margin_ratio: 0.09
  pdf_repeated_margin_min_pages: 3
  pdf_repeated_margin_fraction: 0.40
  pdf_page_number_regex: '^(?:page\s+)?\d+\s*$'
  pdf_heading_min_size_delta: 1.5
  pdf_heading_max_chars: 180
  pdf_equation_math_font_fraction: 0.65
  pdf_equation_max_chars: 500
```

These are heuristics rather than semantic truth. When using a new PDF family, inspect `document_structure.json` before expensive Gemini generation.

## 4. LLM settings

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
```

`provider` — shipped production adapter is Gemini.

`model` — deliberately configuration data; use a moving alias for convenience or pin a supported model for reproducibility.

`thinking_level` — configured reasoning effort where supported.

`api_key_env` — environment variable containing the Gemini API key.

`review_pass` — normal lesson construction uses a generation pass followed by a grounded scientific/pedagogical lesson review/revision pass.

`narration_polish_pass` — enables the dedicated narration-only Gemini editor after lesson content and structure have been settled. The engine defaults this to `true` even when an older profile omits the field. Set it to `false` only for deliberate cost/diagnostic comparisons.

`max_source_characters_per_lesson` — fail-visible upper bound for an individual lesson source packet. The package does not silently truncate a lesson packet.

## 5. Dedicated narration-polish behavior

The narration editor receives the fixed lesson, source packet, global course context, slide timing, visual directions, equations, and current narration. Its structured output may contain only:

```yaml
slides:
  - slide_id: V03S01
    narration: >
      Polished natural spoken script.
    tts_text: null
```

The editor cannot return a replacement title, on-screen bullets, equation, source IDs, visual direction, or slide structure. Local code verifies that every existing slide ID is returned exactly once.

After polishing, the manifest records:

```yaml
generation:
  narration_polish:
    enabled: true
    provider: gemini
    model: ...
    prompt_set: narration_polish_v1

slides:
  - id: V03S01
    narration_word_count: 83
    narration_estimated_spoken_seconds: 38.3
```

An optional `tts_text` is retained when a more explicit spoken rendering is useful for equations, units, abbreviations, or symbols.

The local narration quality checker rejects obvious raw LaTeX/markup or internal production-language contamination in the final narration and warns when the word count is too dense for the assigned `estimated_seconds` at the configured `narration_wpm`.

See [NARRATION_QUALITY.md](NARRATION_QUALITY.md) for the full script-writing contract.

## 6. Global-design settings

```yaml
course:
  llm:
    global_design:
      enabled: true
      max_source_characters: 800000
      max_videos: 30
      plan_review_pass: true
      course_consistency_review: true
```

`enabled` — documents intended global-first behavior. The CLI production default is global even when this key is omitted; use `--design-mode profile` only when deliberately requesting legacy profile segmentation.

`max_source_characters` — upper bound for the complete prompt-facing structured extraction sent during whole-document planning. Exceeding it causes a visible failure rather than truncation.

`max_videos` — upper bound exposed to the global course-plan JSON schema.

`plan_review_pass` — policy marker for the expected second whole-document planning pass. CLI option `--no-plan-review-pass` can deliberately disable that pass for development/cost testing.

`course_consistency_review` — policy marker for the final cross-lesson review. CLI option `--no-global-consistency-review` can deliberately disable it.

## 7. Global plan output

The reviewed plan is stored at:

```text
workspace/<course>/plans/course_plan.yaml
```

Important fields include:

```yaml
design_mode: global_llm
source_signature: <sha256>
course_summary: ...
pedagogical_strategy: ...
concept_map: [...]
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
```

The `source_signature` is computed from the complete prompt-facing extraction. A plan is reusable only when the current extraction has the same signature, regardless of whether the original source was DOCX or PDF.

## 8. Global-design CLI controls

Normal global planning after extraction:

```powershell
microvid plan `
  --workspace ".\workspace\course" `
  --profile my_course
```

Force a fresh global plan during staged drafting:

```powershell
microvid draft `
  --workspace ".\workspace\course" `
  --profile my_course `
  --replan
```

One-command builds replan by default. Reuse is allowed only when the existing plan exactly matches the current extraction:

```powershell
microvid all ... --reuse-plan
```

Development/cost overrides include:

```text
--no-plan-review-pass
--no-review-pass
--no-global-consistency-review
```

Narration polish is profile-controlled through `course.llm.narration_polish_pass` rather than a CLI flag so the production policy is recorded in the course configuration.

Compatibility path using locally predefined `videos`:

```text
--design-mode profile
```

Deterministic generation requires profile mode:

```text
--generator deterministic --design-mode profile
```

## 9. Legacy/profile-mode lesson definitions

Existing course profiles may still contain lesson definitions such as:

```yaml
videos:
  - id: V05
    title: Propagation of Uncertainty
    core_selectors:
      - heading_contains: "Propagation of uncertainty"
```

These definitions are ignored by normal global mode. They are used only when `--design-mode profile` is requested or by deterministic legacy/debug generation.

## 10. Whole-course consistency review

Global builds create:

```text
workspace/<course>/manifests/global_consistency_initial.yaml
workspace/<course>/manifests/global_consistency_final.yaml
```

Possible status values are `ready` and `revision_required`.

The initial review may issue targeted revision instructions for one or more videos. Those lessons are regenerated using their assigned source blocks plus global context. In v0.8.0, any lesson changed by this targeted consistency revision is sent through the dedicated narration-polish pass again before final course verification.

If blocking issues remain, normal `microvid slides` is blocked. `--allow-unreviewed-course` exists only as a diagnostic override.

## 11. Standalone TTS configuration

Example file:

```text
examples/tts/chirp3.example.yaml
```

Typical contents:

```yaml
tts:
  provider: google_cloud_chirp3
  language_code: en-US
  voice_name: en-US-Chirp-HD-F
  ssml_gender: FEMALE
  audio_encoding: LINEAR16
  speaking_rate: 0.9
  location: global
  normalize_scientific_speech: true
  fallback_provider: sapi
  fallback_on_error: true
  audition_voices:
    - en-GB-Chirp3-HD-Leda
    - en-GB-Chirp3-HD-Aoede
    - en-GB-Chirp3-HD-Kore
```

`provider` — currently `google_cloud_chirp3` or `sapi`.

`language_code` — locale passed to the provider.

`voice_name` — provider-specific voice identifier.

`ssml_gender` — Google Cloud SSML gender selector, such as `FEMALE`.

`audio_encoding` — Cloud TTS output encoding; default `LINEAR16` produces WAV output.

`speaking_rate` — narration pace.

`location` — Cloud TTS endpoint location.

`normalize_scientific_speech` — enables conservative scientific-symbol/unit normalization.

`fallback_provider` / `fallback_on_error` — optional secondary TTS behavior. For final production, `--no-tts-fallback` is recommended when voice consistency is essential.

## 12. Per-slide TTS overrides

```yaml
narration: >
  The fitted relationship allows us to calculate gravitational acceleration.

equation_latex: >
  g = \frac{4\pi^2}{m}

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

`tts_text` affects speech only. A small `tts_replacements` mapping may also be supplied for local pronunciation corrections.

## 13. Credentials

The CLI automatically checks the following per-user Windows directory:

```text
%LOCALAPPDATA%\Microvid
```

Place a `.env` file there containing:

```dotenv
GEMINI_API_KEY=...
```

Place the Google Cloud service-account credentials at:

```text
%LOCALAPPDATA%\Microvid\google_cloud_credentials.json
```

The preferred JSON filename is used when present. Otherwise, the package uses the only `*.json` file in the directory and refuses to guess when several are present. A relative `GOOGLE_APPLICATION_CREDENTIALS` path loaded from `.env` is resolved relative to this directory.

Configuration precedence is:

1. an existing process environment variable;
2. a value loaded from `%LOCALAPPDATA%\Microvid\.env`;
3. automatic Google credential-file discovery.

`MICROVID_CONFIG_DIR` may override the per-user directory. Existing environment-based configuration remains supported:

```powershell
$env:GEMINI_API_KEY = "..."
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secure\google-credentials.json"
```

Google Cloud CLI-managed Application Default Credentials remain available as an alternative:

```powershell
gcloud auth application-default login
```

Do not commit API keys, OAuth tokens, service-account JSON, or other credentials.

## 14. Runtime source and workspace isolation

Every build requires an explicit source path. The bundled sample DOCX is never selected automatically. Supported runtime source formats are `.docx` and text-readable `.pdf`.

Use a separate workspace for each course/source revision when practical:

```text
workspace/
  lab101/
  heat_transfer/
  optics_2027/
```

This keeps plans, manifests, slides, audio, and final media isolated.
