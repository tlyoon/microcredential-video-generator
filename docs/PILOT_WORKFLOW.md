# Physics Lab 101 Reference Pilot — Global-First Workflow

This is a reference-course workflow, not a statement that the software is Physics-specific. In v0.6.0, the most important first checkpoint is no longer a preselected V05 boundary. The first checkpoint is whether Gemini's **whole-document global plan** correctly understands and segments the Lab 101 manual.

V05/propagation of uncertainty remains a useful representative media pilot *if the global plan still assigns that topic to a comparable lesson*. Gemini is allowed to reorganize the final sequence after reading the full source.

## 1. Prepare the workstation

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

Check media dependencies:

```powershell
ffmpeg -version
microvid media-check
```

## 2. Audition the narrator

```powershell
microvid tts-audition `
  --output-dir ".\workspace\voice-audition" `
  --tts-config ".\examples\tts\chirp3.example.yaml"
```

The default production voice is `en-GB-Chirp3-HD-Leda` unless locally changed.

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

Confirm headings, tables, equations, and source order are represented correctly.

## 4. Run whole-document Gemini planning

```powershell
microvid plan `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Inspect:

```text
workspace/lab101/plans/course_plan.yaml
```

Before generating slide decks, verify that Gemini has understood the complete manual:

- Does the course summary accurately characterize the source?
- Is the concept map sensible?
- Are prerequisites ordered correctly?
- Are worked examples attached to the most useful lessons?
- Are important source blocks omitted or duplicated unnecessarily?
- Are video boundaries pedagogically better than simply mirroring section headings?
- Are `already_taught` and `forward_links` coherent?
- Is the planned total duration reasonable?

This is now the most important architectural review point.

## 5. Generate globally informed lessons

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Each lesson receives the global concept/sequence context plus its assigned source blocks. The default performs:

1. lesson generation;
2. deterministic local QA;
3. grounded lesson review/revision;
4. whole-course consistency review;
5. targeted lesson revisions where requested;
6. final whole-course verification.

Inspect:

```text
workspace/lab101/manifests/global_consistency_initial.yaml
workspace/lab101/manifests/global_consistency_final.yaml
```

The final status should be `ready` before normal slide generation.

## 6. Choose a representative lesson for the media pilot

Look in `course_plan.yaml` and identify the planned lesson containing propagation of uncertainty or another technically demanding topic involving equations, units, worked examples, and interpretation.

If this remains V05, use V05 below. If Gemini assigns it another ID, substitute that ID.

## 7. Build the representative PowerPoint

```powershell
microvid slides `
  --workspace ".\workspace\lab101" `
  --video V05
```

Review visible slides and speaker notes. Speaker notes contain narration and production guidance.

## 8. Review the lesson manifest

Inspect, for example:

```text
workspace/lab101/manifests/video_05.yaml
```

Check:

- source block IDs and fidelity;
- equations, units, numerical values, and assumptions;
- consistency with the global course plan;
- whether narration assumes only concepts already taught;
- whether the lesson prepares the planned forward links;
- slide density and conceptual sequence;
- narration naturalness;
- `tts_text` for difficult mathematical expressions;
- estimated timings;
- lecturer notes and visual directions;
- assessment/check question;
- editorial flags.

## 9. Approve the representative lesson

Only after scientific/editorial review, set:

```yaml
editorial_status: approved
```

## 10. Render the pilot MP4 with Chirp

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

Confirm the intended provider and voice were actually used.

## 11. Lock production conventions

After the representative video is accepted, record decisions for narrator voice, speaking rate, slide density, equation presentation, narration tone, worked-example pacing, visual/build conventions, pause timing, and scientific-speech overrides.

Then review/approve and batch-produce the remaining globally planned lessons.

## 12. Legacy comparison only

The old nine-video Lab 101 profile remains available for comparison with the new global segmentation:

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101 `
  --design-mode profile
```

This is not the v0.6.0 production default. It can be useful to compare Gemini's global segmentation with the earlier instructor-defined structure.
