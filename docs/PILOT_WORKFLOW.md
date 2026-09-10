# Physics Lab 101 Reference Pilot — V05 Propagation of Uncertainty

This document is a **reference-course workflow**, not a statement that the software is Physics-specific. V05 remains the recommended first live pilot because it exercises prose, equations, units, worked examples, source grounding, narration, scientific speech, TTS, and final media assembly.

## 1. Prepare the workstation

Update the package and activate the environment:

```powershell
git switch main
git pull --ff-only
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,windows]"
```

Set Gemini credentials:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Configure Google Cloud Application Default Credentials for Chirp:

```powershell
gcloud auth application-default login
```

Confirm FFmpeg and local media capabilities:

```powershell
ffmpeg -version
microvid media-check
```

## 2. Audition the narrator

Before producing the course, compare the packaged Chirp candidate voices:

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

Choose one consistent course voice. The default is `en-GB-Chirp3-HD-Leda`.

## 3. Extract the authoritative runtime manual

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

The tracked sample DOCX under `examples/sample_docs/` is not used unless its path is explicitly supplied.

## 4. Generate lesson manifests with Gemini

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

The default workflow performs LLM generation followed by a grounded review/revision pass.

## 5. Build and inspect V05 PowerPoint

```powershell
microvid slides `
  --workspace ".\workspace\lab101" `
  --video V05
```

Review both the visible slides and PowerPoint speaker notes. Speaker notes contain narration and production guidance.

## 6. Review the V05 manifest

Inspect:

```text
workspace/lab101/manifests/video_05.yaml
```

Check:

- source block IDs and source fidelity;
- equations and assumptions;
- units and numerical values;
- slide density and conceptual sequence;
- narration naturalness;
- `tts_text` for difficult mathematical expressions;
- estimated timings;
- lecturer notes and visual directions;
- assessment/check question;
- editorial flags.

Compare important claims back to the authoritative DOCX and extraction JSON.

## 7. Approve the lesson

Only after scientific/editorial review, set:

```yaml
editorial_status: approved
```

## 8. Render the pilot MP4 with Chirp

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml" `
  --no-tts-fallback
```

Expected output:

```text
workspace/lab101/videos/video_05.mp4
```

Also inspect:

```text
workspace/lab101/audio/video_05/tts_manifest.yaml
```

Confirm the intended provider and voice were actually used for every slide.

## 9. Lock the production conventions

After reviewing V05, record decisions for:

- preferred narrator voice;
- speaking rate;
- slide density;
- equation presentation;
- narration tone;
- worked-example pacing;
- visual/build conventions;
- pause timing;
- scientific speech overrides.

Then use those accepted conventions when producing the remaining Lab 101 videos.

## 10. Why this pilot matters

A successful V05 run validates the most demanding parts of the pipeline before batch production. Simpler lessons should then require less adjustment.
