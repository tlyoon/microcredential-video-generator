# Physics Lab 101 Reference Pilot — Global-First + Narration-Polish Workflow

This is a reference-course workflow, not a statement that the software is Physics-specific. The first checkpoint is whether Gemini's **whole-document global plan** correctly understands and segments the Lab 101 manual. The second major checkpoint is whether the dedicated narration editor produces natural, technically faithful spoken teaching before TTS.

Propagation of uncertainty remains a useful representative media pilot if the global plan assigns that topic to a comparable lesson. Gemini is allowed to reorganize the sequence after reading the full source.

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

Inspect `workspace/lab101/extracted/document_structure.json` and confirm headings, tables, equations, and source order are represented correctly.

## 4. Run whole-document Gemini planning

```powershell
microvid plan `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Inspect `workspace/lab101/plans/course_plan.yaml` and verify the course summary, concept map, prerequisites, source assignments, worked-example placement, video boundaries, `already_taught`, `forward_links`, and planned total duration.

## 5. Generate, review and polish the lessons

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101
```

Each lesson receives the global concept/sequence context plus its assigned source blocks. The default performs:

1. lesson/slide generation with first-pass narration;
2. deterministic local lesson QA;
3. grounded Gemini scientific/pedagogical review/revision;
4. **dedicated Gemini narration-only polish**;
5. local narration speech/timing QA;
6. whole-course consistency review;
7. targeted lesson revisions where requested;
8. re-polishing of any revised lesson narration;
9. final whole-course verification.

Inspect:

```text
workspace/lab101/manifests/global_consistency_initial.yaml
workspace/lab101/manifests/global_consistency_final.yaml
```

The final status should be `ready` before normal slide generation.

## 6. Choose a representative lesson for narration/media review

Look in `course_plan.yaml` and identify a technically demanding lesson involving equations, units, worked reasoning, and interpretation. Propagation of uncertainty is a strong candidate.

If the lesson is V05, use V05 below. If Gemini assigns another ID, substitute it.

## 7. Inspect the polished narration before building media

Open, for example:

```text
workspace/lab101/manifests/video_05.yaml
```

For every slide, inspect:

```yaml
narration: ...
tts_text: ...
narration_word_count: ...
narration_estimated_spoken_seconds: ...
estimated_seconds: ...
```

Check that the script:

- sounds like one continuous lecturer explanation rather than isolated captions;
- explains rather than reads visible bullets;
- uses terminology consistent with the source/global plan;
- synchronizes naturally with `visual_direction`;
- verbalizes equations and units naturally;
- avoids generic filler and repeated stock transitions;
- fits comfortably within the allocated slide time;
- preserves all scientific qualifications and assumptions.

The narration polish stage is source-grounded but remains subject to human review. See `docs/NARRATION_QUALITY.md` for the full contract.

## 8. Build the representative PowerPoint

```powershell
microvid slides `
  --workspace ".\workspace\lab101" `
  --video V05
```

Review visible slides and speaker notes together. Speaker notes contain the final polished narration and production guidance.

## 9. Review the complete lesson

Check source block IDs/fidelity, equations, units, numerical values, assumptions, global-course fit, slide density, polished narration, `tts_text`, timing, lecturer notes, visual directions, assessment, and editorial flags.

## 10. Approve the representative lesson

Only after scientific/editorial review, set:

```yaml
editorial_status: approved
```

## 11. Render the pilot MP4 with Chirp

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

## 12. Listen, do not only read

The final narration quality test should be auditory. Listen to the entire representative video and check cadence, pauses, sentence rhythm, mathematical pronunciation, timing against visual builds, and whether transitions feel natural. If needed, edit `narration`/`tts_text` manually before approving the remaining course.

## 13. Lock production conventions

After the representative video is accepted, record decisions for narrator voice, speaking rate, slide density, equation presentation, narration tone, worked-example pacing, visual/build conventions, pause timing, and scientific-speech overrides.

Then review/approve and batch-produce the remaining globally planned lessons.

## 14. Legacy comparison only

The old nine-video Lab 101 profile remains available for comparison:

```powershell
microvid draft `
  --workspace ".\workspace\lab101" `
  --profile physics_lab_101 `
  --design-mode profile
```

This is not the production default; it is useful only when comparing Gemini's global segmentation with the earlier instructor-defined structure.
