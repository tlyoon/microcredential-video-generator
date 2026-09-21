# Course trailer / Video 00 workflow

Microvid includes a reusable editorial prompt for producing a short course advertisement:

```text
src/microvid/prompts/course_trailer_advertisement_video_generation.md
```

The prompt is subject-neutral and asks for a truthful 45–55 second, 16:9 master built from
the completed course's own source, plan, lessons and visual assets. It produces the positioning,
narration, edit plan, clip map, overlays, title/CTA, adaptation notes and QA checklist needed to
assemble Video 00.

## Current support boundary

There is not yet a `microvid trailer` command. The prompt is a version-controlled production
instruction, while trailer editing/assembly and upload are currently guided steps.

The standard `microvid youtube publish` command is lesson-only. It discovers every
`videos/video_*.mp4`, derives a matching lesson ID and requires the number of files to equal the
lesson count in `manifests/course.yaml`. Therefore, do not place a trailer named `video_00.mp4`
in the lesson `videos` directory during automated publishing.

Use this layout instead:

```text
workspace/my_course/
  manifests/                 # V01–VNN lesson manifests
  videos/                    # video_01.mp4–video_NN.mp4 only
  trailer/
    trailer_package.md       # generated positioning/script/edit plan
    video_00.mp4             # final trailer master
    video_00.srt             # optional captions
```

## Recommended production procedure

1. Complete the global plan and all lesson manifests.
2. Render the final lesson MP4s and inspect representative audio/visual quality.
3. Give the trailer prompt access to the authoritative source, `plans/course_plan.yaml`, lesson
   manifests, final lesson videos, rendered slides and course/channel metadata.
4. Generate and save the full trailer package. Check every promise against the course evidence.
5. Select five to eight visually clear moments from different lessons where possible. Keep
   critical content in a central safe region for later 9:16 or 1:1 adaptation.
6. Record the 95–120 word master narration with the same approved course voice and TTS settings,
   unless the course has an explicit reason to use another voice.
7. Assemble a 45–55 second master; the absolute maximum in the prompt is 59 seconds. Add captions
   and use only music for which you have appropriate rights.
8. Save the final master under `workspace/<course>/trailer/`, not `videos/`.
9. Publish the lesson set with `microvid youtube publish` and allow its state file to finish.
10. Upload Video 00 separately through YouTube Studio or another approved YouTube upload path,
    add it to the same playlist, and move it to position 1 ahead of Lesson 1.
11. Verify the public watch URL, playlist order, title, description, captions, thumbnail,
    visibility and playback before promoting it.

## Run the editorial prompt

The prompt is deliberately independent of one LLM interface. Supply its complete contents as
the instruction and provide the course artifacts listed above as context. Do not run it from
the course title alone. Save the returned sections without discarding the clip evidence or QA
checklist; those make the final edit auditable.

The prompt is shipped in built distributions through the package-data rule in `pyproject.toml`.
Changing it changes production behavior and should be committed and reviewed with the package.

## Pre-upload checklist

- Duration is below 59 seconds and the opening earns attention within 2–3 seconds.
- The trailer sells a supported transformation rather than reciting the syllabus.
- Claims, terminology and visuals are grounded in the current course.
- Text remains readable on mobile and critical visuals stay in the central safe region.
- Narration is clear, captions are synchronized and audio does not clip.
- There is one primary CTA.
- `workspace/<course>/videos/` still contains lesson MP4s only.
- The final playlist order is Video 00, V01, V02, …, VNN.

## Future automation note

When native trailer generation and publishing are added, the implementation should introduce a
separate trailer manifest/state path rather than silently treating V00 as a lesson. Until then,
the separation above preserves the publisher's resume and replacement guarantees.
