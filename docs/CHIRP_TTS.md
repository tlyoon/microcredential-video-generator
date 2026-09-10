# Google Cloud Chirp 3 HD TTS

The production TTS default is Google Cloud Text-to-Speech using a Chirp 3 HD female voice. Windows SAPI remains available as a fallback.

## Default voice

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

`en-GB-Chirp3-HD-Leda` is a female Chirp 3 HD voice. The voice is configuration data; it is not hard-coded into the media renderer.

## Local Google Cloud authentication

Install/update the package, enable Cloud Text-to-Speech in the Google Cloud project used for production, then configure Application Default Credentials. A common local setup is:

```powershell
gcloud auth application-default login
```

Alternatively, point `GOOGLE_APPLICATION_CREDENTIALS` to an authorized service-account credential file if that is how the workstation is managed.

No Google credential or key file belongs in Git.

## Audition three female voices

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The packaged audition list is:

- `en-GB-Chirp3-HD-Leda`
- `en-GB-Chirp3-HD-Aoede`
- `en-GB-Chirp3-HD-Kore`

A different voice can be tested without editing code:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --voice en-US-Chirp3-HD-Aoede `
  --language-code en-US
```

## Use Chirp when rendering a lesson

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

CLI options can override configuration values, for example:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --voice-name en-GB-Chirp3-HD-Aoede `
  --speaking-rate 0.95
```

## Scientific speech normalization

The slide manifest keeps the scientifically exact on-screen equation separately from the narration. Before TTS, the media layer conservatively normalizes common notation such as:

- `±` -> `plus or minus`
- `m s⁻²` -> `metres per second squared`
- `%` -> `percent`
- `Ω` -> `ohms`
- `π` -> `pi`

This is intentionally not a full LaTeX-to-speech system. If a particular expression needs a precise reading, a slide may provide `tts_text` in its YAML manifest. `tts_text` is used for speech while the normal `narration` remains the human-readable script.

A slide may also provide a small `tts_replacements` mapping for local pronunciation overrides.

## Fallback behavior

If Chirp synthesis fails and `fallback_on_error: true`, the renderer attempts the configured fallback provider. The default fallback is Windows SAPI. The generated `audio/video_NN/tts_manifest.yaml` records which provider and voice actually produced every slide, so an unnoticed fallback cannot be mistaken for Chirp output.

For final production, use `--no-tts-fallback` if you want the build to fail rather than change voice.
