# Google Cloud Chirp 3 HD TTS

This guide describes the production text-to-speech layer used by **Microcredential Video Generator v0.5.0**. TTS is deliberately independent of course subject matter and independent of the LLM that writes the lesson.

## Default configuration

```yaml
tts:
  provider: google_cloud_chirp3
  language_code: en-US
  voice_name: en-US-Chirp-HD-F
  ssml_gender: FEMALE
  audio_encoding: LINEAR16
  speaking_rate: 1.2
  location: global
  normalize_scientific_speech: true
  fallback_provider: sapi
  fallback_on_error: true
```

The default voice is configuration data, not hard-coded in the renderer. A different supported Chirp 3 HD voice or locale can be selected without changing Python.

## Authentication

Install/update the Python package and enable Cloud Text-to-Speech in the Google Cloud project used for production. For automatic local service-account authentication, place the authorized file at:

```text
%LOCALAPPDATA%\Microvid\google_cloud_credentials.json
```

The package sets `GOOGLE_APPLICATION_CREDENTIALS` automatically. If that preferred filename is absent, it uses the only `*.json` file in the directory. Explicit environment configuration takes precedence.

Google Cloud CLI-managed Application Default Credentials remain an alternative:

```powershell
gcloud auth application-default login
```

A managed workstation may alternatively set `GOOGLE_APPLICATION_CREDENTIALS` explicitly.

Never commit Google credentials, API keys, OAuth tokens, or service-account JSON files to Git.

## Voice audition

The repository includes a standalone example:

```text
examples/tts/chirp3.example.yaml
```

Audition the configured candidate voices using identical scientific narration:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The packaged candidate list currently includes:

- `en-GB-Chirp3-HD-Leda`
- `en-GB-Chirp3-HD-Aoede`
- `en-GB-Chirp3-HD-Kore`

To audition a different voice:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --voice en-US-Chirp3-HD-Aoede `
  --language-code en-US
```

Repeat `--voice` when several explicit candidates should be compared.
For one explicit candidate, `--voice-name en-US-Chirp3-HD-Aoede` is also supported and selects that voice rather than the configured audition list.

## Render a video with Chirp

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The same command works for Physics Lab 101 or any other course workspace.

### Override a voice

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --voice-name en-GB-Chirp3-HD-Aoede
```

### Override speaking rate

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --speaking-rate 0.95
```

### Select SAPI explicitly

```powershell
microvid media `
  --workspace ".\workspace\course" `
  --video V01 `
  --tts-provider sapi
```

## Scientific speech normalization

The exact mathematics shown to students and the text spoken by TTS are separate representations.

For example:

```yaml
equation_latex: >
  g = \frac{4\pi^2}{m}

narration: >
  The fitted slope can be used to obtain gravitational acceleration.

tts_text: >
  g equals four pi squared divided by the fitted slope.
```

The normalizer conservatively handles common notation such as:

- `±` -> `plus or minus`
- `m s⁻²` -> `metres per second squared`
- `%` -> `percent`
- `Ω` -> `ohms`
- `π` -> `pi`

This is intentionally not a universal LaTeX-to-speech system. Use explicit `tts_text` for an expression that needs a precise spoken rendering.

A slide may also define local corrections:

```yaml
tts_replacements:
  "u_xbar": "standard uncertainty of the mean"
```

The LLM system prompt is designed to reduce normalization burden by writing narration as natural spoken prose and keeping exact symbolic mathematics in `equation_latex`.

## Fallback behavior

If Chirp fails and the configuration permits fallback, Windows SAPI is attempted. For private previews this can be convenient. For final production, voice consistency is usually more important, so use:

```powershell
microvid media ... --no-tts-fallback
```

This forces the build to fail instead of silently changing narrator.

## TTS provenance

For every rendered lesson, the package writes:

```text
workspace/<course>/audio/video_NN/tts_manifest.yaml
```

It records the requested TTS configuration and, for each slide:

- actual provider used;
- actual voice used;
- language code;
- audio file path;
- normalized spoken text.

This makes an accidental fallback or voice mismatch auditable.

## Configuration precedence

TTS values are resolved from:

1. built-in defaults;
2. `course.tts` in the selected course profile;
3. `--tts-config` YAML;
4. explicit CLI overrides.

See [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for the complete configuration contract.
