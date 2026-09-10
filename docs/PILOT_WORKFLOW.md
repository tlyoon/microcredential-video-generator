# Pilot workflow — V05 Propagation of Uncertainty

V05 remains the recommended first live Gemini pilot because it exercises prose, equations, units, worked examples, interpretation, source grounding and assessment.

1. Set `$env:GEMINI_API_KEY` locally.
2. Put the working corrected manual in `source/` or use another explicit path.
3. Run `microvid extract --source ... --workspace .\workspace\lab101 --profile physics_lab_101`.
4. Run the LLM authoring pipeline with `microvid draft --workspace .\workspace\lab101 --profile physics_lab_101`.
5. The default performs generation plus a grounded review/revision pass using Gemini.
6. Inspect `workspace/lab101/manifests/video_05.yaml`, especially source block IDs, equations, narration, timings and `editorial_flags`.
7. Generate/review the PPTX. Narration and production guidance are also present in PowerPoint speaker notes.
8. Compare source-derived slides to the extraction JSON and authoritative DOCX.
9. Revise/approve the lesson, then set `editorial_status: approved`.
10. Run the media stage to synthesize per-slide audio and assemble the MP4.
11. Use the approved V05 visual/narration conventions to tune the profile/prompts before batch-producing V01–V09.
