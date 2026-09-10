# Configuration Reference

This document describes the configuration surfaces of **Microcredential Video Generator v0.6.0**. The production default is whole-document Gemini course design followed by globally informed lesson generation and final whole-course consistency review.

## 1. Configuration precedence

For LLM generation, the selected course profile supplies defaults and CLI options such as `--model` and `--thinking-level` override them.

For TTS, settings are resolved in this order, from lowest to highest priority:

1. built-in `TTSConfig` defaults;
2. `course.tts` in the selected course profile;
3. standalone `--tts-config` YAML;
4. explicit CLI overrides.

## 2. Course profile in global mode

A v0.6.0 global-mode profile is primarily a **constraint profile**. It should describe the audience, source role, parser behavior, timing targets, LLM settings, editorial policy, and TTS preferences. It does not need to predefine the videos.

Example:

```yaml
course:
  id: heat_transfer
  title: Introduction to Heat Transfer
  audience: First-year engineering students
  source_role: The explicitly supplied DOCX is the authoritative content source.
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
    max_source_characters_per_lesson: 220000
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

Typical parser settings:

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

Important behavior:

- pagination is ignored;
- semantic heading breadcrumb paths are retained;
- numeric section labels are optional metadata;
- custom heading patterns may be supplied;
- paragraphs, tables, headings, and Office Math provenance are extracted locally.

## 4. LLM settings

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

`provider` — shipped production adapter is Gemini.

`model` — deliberately configuration data; use a moving alias for convenience or pin a supported model for reproducibility.

`thinking_level` — configured reasoning effort where supported.

`api_key_env` — environment variable containing the Gemini API key.

`review_pass` — normal lesson generation uses a generation pass followed by a grounded lesson review/revision pass.

`max_source_characters_per_lesson` — fail-visible upper bound for an individual lesson source packet. The package does not silently truncate a lesson packet.

## 5. Global-design settings

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

## 6. Global plan output

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

The `source_signature` is computed from the complete prompt-facing extraction. A plan is reusable only when the current extraction has the same signature.

## 7. Global-design CLI controls

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

Development/cost overrides:

```text
--no-plan-review-pass
--no-review-pass
--no-global-consistency-review
```

Compatibility path using locally predefined `videos`:

```text
--design-mode profile
```

Deterministic generation requires profile mode:

```text
--generator deterministic --design-mode profile
```

## 8. Legacy/profile-mode lesson definitions

Existing course profiles may still contain lesson definitions such as:

```yaml
videos:
  - id: V05
    title: Propagation of Uncertainty
    core_selectors:
      - heading_contains: "Propagation of uncertainty"
```

These definitions are ignored by normal global mode. They are used only when `--design-mode profile` is requested or by deterministic legacy/debug generation.

This preserves backward compatibility without allowing old hand-authored segmentation to constrain the new production design.

## 9. Whole-course consistency review

Global builds create:

```text
workspace/<course>/manifests/global_consistency_initial.yaml
workspace/<course>/manifests/global_consistency_final.yaml
```

Possible status values are:

```text
ready
revision_required
```

The initial review may issue targeted revision instructions for one or more videos. Those lessons are regenerated using their assigned source blocks plus global context. A final verification is then performed.

If blocking issues remain, normal `microvid slides` is blocked. `--allow-unreviewed-course` exists only as a diagnostic override.

## 10. Standalone TTS configuration

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

`provider` — currently `google_cloud_chirp3` or `sapi`.

`language_code` — locale passed to the provider.

`voice_name` — provider-specific voice identifier.

`audio_encoding` — Cloud TTS output encoding; default `LINEAR16` produces WAV output.

`speaking_rate` — narration pace.

`location` — Cloud TTS endpoint location.

`normalize_scientific_speech` — enables conservative scientific-symbol/unit normalization.

`fallback_provider` / `fallback_on_error` — optional secondary TTS behavior. For final production, `--no-tts-fallback` is recommended when voice consistency is essential.

## 11. Per-slide TTS overrides

```yaml
narration: >
  The fitted relationship allows us to calculate gravitational acceleration.

equation_latex: >
  g = \frac{4\pi^2}{m}

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

`tts_text` affects speech only. A small `tts_replacements` mapping may also be supplied for local pronunciation corrections.

## 12. Credentials

Gemini:

```powershell
$env:GEMINI_API_KEY = "..."
```

Google Cloud Chirp normally uses Application Default Credentials:

```powershell
gcloud auth application-default login
```

Do not commit API keys, OAuth tokens, service-account JSON, or other credentials.

## 13. Runtime source and workspace isolation

Every build requires an explicit source path. The bundled sample DOCX is never selected automatically.

Use a separate workspace for each course/source revision when practical:

```text
workspace/
  lab101/
  heat_transfer/
  optics_2027/
```

This keeps plans, manifests, slides, audio, and final media isolated.
