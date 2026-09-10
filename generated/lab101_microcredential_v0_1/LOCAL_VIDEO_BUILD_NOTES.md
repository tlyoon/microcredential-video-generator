# Local Video Build Notes

These assets are intended to be pulled to a local PC and turned into video files there. The current committed output provides the course map plus slide-by-slide on-screen text and narration scripts. Final MP4 generation should be done locally with PowerPoint/slide rendering, TTS audio, and FFmpeg.

## Recommended local workflow

1. Pull the repository.

```powershell
git switch main
git pull --ff-only
```

2. Review the generated draft.

```text
generated/lab101_microcredential_v0_1/course_plan.yaml
generated/lab101_microcredential_v0_1/slide_stack_and_scripts.md
```

3. Build or revise PowerPoint decks from the slide stack. Each slide should use the listed title and on-screen bullets. Put the corresponding narration script into speaker notes.

4. Generate one audio file per slide using the chosen TTS provider. For the package default, use Google Cloud Chirp 3 HD with the configured female voice, usually `en-GB-Chirp3-HD-Leda`, unless overridden.

5. Export each slide to PNG.

6. Build one video segment per slide with FFmpeg. Example:

```powershell
ffmpeg -y -loop 1 -i slide_01.png -i slide_01.wav -c:v libx264 -tune stillimage -c:a aac -shortest segment_01.mp4
```

7. Create `segments.txt`.

```text
file 'segment_01.mp4'
file 'segment_02.mp4'
file 'segment_03.mp4'
```

8. Concatenate the segments.

```powershell
ffmpeg -y -f concat -safe 0 -i segments.txt -c copy final_video.mp4
```

## Package media route

Once the slide stack has been converted into a normal package workspace with approved manifests and PowerPoint decks, the package media command can be used:

```powershell
microvid media `
  --workspace ".\workspace\lab101" `
  --video V05 `
  --tts-config ".\examples\tts\chirp3.example.yaml" `
  --no-tts-fallback
```

## Review warning

The committed slide stack is a draft for instructor review. Do not treat it as approved teaching material until the scientific content, equations, units, examples, narration tone, and slide pacing have been checked.