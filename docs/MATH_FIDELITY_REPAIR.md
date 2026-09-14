# Native-math slide and video repair

Use `scripts/regenerate_math_media.py` when lesson manifests already exist but the
PowerPoint decks show literal LaTeX, ASCII approximations, or incorrectly formatted
scientific notation. The normal slide builder now uses the same native OfficeMath
conversion, so newly generated decks receive the fix automatically.

From the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe scripts\regenerate_math_media.py `
  --workspace .\workspace\lab101 `
  --source-docx .\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx
```

The script performs four checks/actions for each selected video:

1. reads native OMML equations from the source DOCX and audits manifest equations
   against them;
2. creates the PPTX with editable PowerPoint OfficeMath zones and rejects visible
   raw-LaTeX remnants;
3. renders the corrected deck through desktop PowerPoint;
4. reuses the existing per-slide narration audio to rebuild the MP4 with FFmpeg.

The existing PPTX and MP4 are replaced only after their new counterparts build
successfully. Results are recorded in `qa/math_fidelity_report.json` inside the
workspace.

To repair selected videos, repeat `--video`:

```powershell
.\.venv\Scripts\python.exe scripts\regenerate_math_media.py `
  --workspace .\workspace\lab101 `
  --source-docx .\source\Physics_Laboratory_101_Student_Manual_v2_Corrected.docx `
  --video V03 --video V06
```

Use `--slides-only` to rebuild and validate PPTX files without PowerPoint rendering
or MP4 generation. Full MP4 repair requires Windows, desktop PowerPoint, FFmpeg, and
the existing narration files under `workspace/<name>/audio/video_NN/`.
