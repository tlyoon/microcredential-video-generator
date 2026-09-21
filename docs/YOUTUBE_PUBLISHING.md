# YouTube course publishing

The YouTube add-on publishes one completed Microvid workspace as an ordered educational
playlist. It uses playlist `PLUUmsE42J5mQfq1c3jh0g0Rwoe2ldQA43` as its default structural
and editorial reference, while Gemini writes original metadata from the new course manifests.

The workflow validates all `video_*.mp4` files, reads the course plan and lesson manifests,
generates course and lesson metadata, creates a square course image, uploads the videos and
matching SRT files, and creates an ordered playlist. It saves every remote ID so an interrupted
run can resume without knowingly duplicating videos.

This command publishes course lessons V01–VNN. It does not currently manage a promotional
Video 00. Keep `video_00.mp4` outside the workspace `videos` directory while using this command;
see [COURSE_TRAILER.md](COURSE_TRAILER.md).

## One-time Google setup

YouTube channel writes require user OAuth. The service-account JSON used by Google Cloud
Text-to-Speech cannot manage a personal YouTube channel.

In Google Cloud Console:

1. Create or select a project and enable **YouTube Data API v3**.
2. Configure the OAuth consent screen.
3. Create an OAuth client with application type **Desktop app**.
4. Download, rename, and save it as:

```text
%LOCALAPPDATA%\Microvid\youtube_client_secret.json
```

The complete private configuration directory is:

```text
%LOCALAPPDATA%\Microvid\
|-- .env
|-- google_cloud_credentials.json
|-- youtube_client_secret.json
`-- youtube_token.json              # created automatically after consent
```

Do not commit these files. On the first publishing command, a browser opens so you can choose
and authorize the Google account that owns the channel. Later runs reuse `youtube_token.json`.
If the OAuth consent screen is in Testing mode, add your Google account as a test user.

If authorization or token refresh fails, verify that the credential is a Desktop app client,
the YouTube Data API is enabled, and the selected account manages the target channel. TLS/SSL
errors contacting `oauth2.googleapis.com` usually indicate a local clock, proxy/HTTPS
inspection, firewall or certificate-store problem. Correct that connection problem before
re-authorizing, and back up the existing token before deliberately replacing it.

## Publish

Publish the newest completed course directly under `workspace\`:

```powershell
microvid youtube publish --expected-channel "@tlyoon"
```

Or select the course explicitly:

```powershell
microvid youtube publish `
  --workspace ".\workspace\lab101" `
  --expected-channel "@tlyoon"
```

`--expected-channel` stops the command before remote writes if YouTube reports a different
authorized custom handle. It can instead be placed in `%LOCALAPPDATA%\Microvid\.env`:

```dotenv
YOUTUBE_EXPECTED_CHANNEL_HANDLE=@tlyoon
```

The default visibility is `public`; there is no private staging upload. Subscriber notifications
are off by default so a course does not emit a separate notification for every lesson. Add
`--notify-subscribers` to request them. The default category is Education (`27`) and the default
metadata/caption language is `en-GB`.

YouTube can restrict uploads from a new, unaudited API project to private visibility even when
Microvid requests public visibility. That restriction belongs to the API project and must be
resolved through Google's audit process.

## Preview and edit before uploading

OAuth is still needed to read the reference playlist, but `--dry-run` performs no YouTube write:

```powershell
microvid youtube publish `
  --workspace ".\workspace\lab101" `
  --expected-channel "@tlyoon" `
  --dry-run
```

It creates:

```text
workspace\lab101\youtube\youtube_metadata.yaml
workspace\lab101\youtube\course_cover.jpg
```

The normal publish command reuses this YAML. It can be edited first, explicitly selected with
`--metadata`, or regenerated with `--refresh-metadata`.

## Resume and results

Publishing progress is stored after every completed remote operation in:

```text
workspace\lab101\youtube\publish_state.json
```

After a network, quota, or processing failure, run the same command again. Recorded videos,
playlist entries, captions, and the playlist image are skipped. If a local MP4 changes after
upload, the publisher stops rather than creating a silent duplicate. The completed state file
contains the playlist URL and each uploaded video URL.

### Controlled replacement of regenerated videos

YouTube cannot replace the media bytes behind an existing video ID. When previously
published MP4 files change, use the guarded replacement mode and confirm the exact
destination playlist ID:

```powershell
.\.venv\Scripts\python.exe -m microvid.cli youtube publish `
  --workspace ".\workspace\lab101" `
  --expected-channel "@tlyoon" `
  --replace-changed-videos `
  --confirm-playlist-id "YOUR_EXISTING_PLAYLIST_ID"
```

For every changed lesson, the publisher uploads the new video and caption, inserts the
new playlist item, reconciles the complete V01-to-VNN order, and verifies that the new
videos occupy the beginning of the playlist. Only after that verification succeeds does
it remove the superseded playlist entries. Progress is written after every remote change,
so an interrupted replacement resumes without intentionally uploading another copy.

The old videos remain on the channel by default. Use
`--retire-replaced-videos unlisted`, `private`, or `delete` to change that behavior.
Deletion is irreversible; `keep` is the default and safest policy. Old IDs, fingerprints,
and the chosen policy are retained in each lesson's `replacement_history` record.

Every normal publish or resume also reads the live playlist and reconciles the course videos
to lesson order (`V01`, `V02`, `V03`, and so on). Only misplaced items are moved, and course
videos are kept together at the start of the playlist. This final pass protects the sequence
even if an interrupted upload or a later YouTube-side change disturbed the insertion order.

## Convert the playlist to a formal YouTube Course

The Data API supports uploads, playlist creation, captions, ordering, metadata, and a playlist
image. YouTube currently exposes the final **Set as course** action in Studio:

1. Open YouTube Studio on desktop.
2. Go to **Content**, then **Playlists**.
3. Open the new playlist menu and choose **Set as course**.

This Studio action requires channel access to YouTube's Course feature. The public playlist is
already usable if that option is unavailable.

## Add a course trailer as Video 00

Run the lesson publisher first with only `video_01.mp4` through `video_NN.mp4` in the `videos`
directory. Upload the completed trailer separately, add it to the same playlist, then move it
ahead of Lesson 1 in YouTube Studio. The trailer has its own production guide because adding it
to `videos/` makes the current lesson publisher treat it as an unexpected manifest-backed
lesson. See [COURSE_TRAILER.md](COURSE_TRAILER.md) for file layout, production and verification.

## Command options

```text
--workspace PATH             Select a completed course
--workspace-root PATH        Change the automatic search root
--template-playlist ID       Change the reference playlist
--refresh-metadata           Ask Gemini to rewrite metadata
--metadata PATH              Use reviewed metadata from YAML
--expected-channel HANDLE    Verify the authorized channel
--privacy public             Default; deliberately override if needed
--category-id 27             Education category
--language en-GB             Metadata and caption language
--made-for-kids              Declare the videos as made for children
--notify-subscribers         Request upload notifications
--replace-changed-videos     Safely swap changed MP4s into the existing playlist
--confirm-playlist-id ID     Required exact playlist confirmation for replacement
--retire-replaced-videos P   keep (default), unlisted, private, or delete
--dry-run                    Prepare local publishing assets only
```
