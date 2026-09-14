from __future__ import annotations

import hashlib
import json
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .llm import JSONLLMProvider
from .runtime_config import local_config_directory

DEFAULT_TEMPLATE_PLAYLIST_ID = "PLUUmsE42J5mQfq1c3jh0g0Rwoe2ldQA43"
YOUTUBE_CLIENT_SECRET_FILENAME = "youtube_client_secret.json"
YOUTUBE_TOKEN_FILENAME = "youtube_token.json"
YOUTUBE_SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
)
_VIDEO_FILE = re.compile(r"^video_(\d+)\.mp4$", re.IGNORECASE)


class YouTubePublishError(RuntimeError):
    """Raised when a course cannot safely be prepared or published."""


@dataclass(frozen=True)
class CourseVideo:
    lesson_id: str
    number: int
    path: Path
    subtitle_path: Path | None
    manifest: dict[str, Any]


@dataclass(frozen=True)
class CourseBundle:
    workspace: Path
    course: dict[str, Any]
    plan: dict[str, Any]
    videos: tuple[CourseVideo, ...]

    @property
    def output_dir(self) -> Path:
        return self.workspace / "youtube"


def _read_yaml(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise YouTubePublishError(f"Required course file is missing: {path}")
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise YouTubePublishError(f"Expected a YAML mapping in {path}")
    return value


def find_latest_workspace(workspace_root: str | Path = "workspace") -> Path:
    root = Path(workspace_root).expanduser().resolve()
    if not root.is_dir():
        raise YouTubePublishError(f"Workspace root does not exist: {root}")
    candidates = [
        path
        for path in root.iterdir()
        if path.is_dir()
        and (path / "manifests" / "course.yaml").is_file()
        and any((path / "videos").glob("video_*.mp4"))
    ]
    if not candidates:
        raise YouTubePublishError(
            f"No completed course with manifests and MP4 files was found under {root}"
        )
    return max(candidates, key=lambda path: path.stat().st_mtime).resolve()


def load_course_bundle(workspace: str | Path) -> CourseBundle:
    root = Path(workspace).expanduser().resolve()
    course = _read_yaml(root / "manifests" / "course.yaml")
    plan = _read_yaml(root / "plans" / "course_plan.yaml", required=False)
    lesson_index = {
        str(item.get("id", "")): item
        for item in course.get("videos", [])
        if isinstance(item, dict)
    }
    found: list[CourseVideo] = []
    videos_dir = root / "videos"
    for path in videos_dir.glob("video_*.mp4"):
        match = _VIDEO_FILE.fullmatch(path.name)
        if not match or path.name.casefold().endswith(".concat.txt"):
            continue
        number = int(match.group(1))
        lesson_id = f"V{number:02d}"
        index_item = lesson_index.get(lesson_id, {})
        manifest_name = str(index_item.get("manifest") or f"video_{number:02d}.yaml")
        manifest = _read_yaml(root / "manifests" / manifest_name)
        if str(manifest.get("video_id", lesson_id)) != lesson_id:
            raise YouTubePublishError(f"Manifest/video mismatch for {path.name}")
        subtitle = root / "subtitles" / f"video_{number:02d}.srt"
        found.append(
            CourseVideo(
                lesson_id=lesson_id,
                number=number,
                path=path.resolve(),
                subtitle_path=subtitle.resolve() if subtitle.is_file() else None,
                manifest=manifest,
            )
        )
    found.sort(key=lambda item: item.number)
    if not found:
        raise YouTubePublishError(f"No video_*.mp4 files found in {videos_dir}")
    if len(found) < 3:
        raise YouTubePublishError("A YouTube Course requires at least three videos.")
    expected = [item for item in course.get("videos", []) if isinstance(item, dict)]
    if expected and len(found) != len(expected):
        raise YouTubePublishError(
            f"Found {len(found)} MP4 files but the course manifest defines {len(expected)} lessons."
        )
    return CourseBundle(root, course, plan, tuple(found))


def authenticate_youtube(*, config_dir: str | Path | None = None):
    """Authorize the installed app and return a YouTube Data API client.

    The first call opens a local browser consent flow. Later calls refresh and reuse
    ``youtube_token.json`` without asking the user to sign in again.
    """
    directory = (
        Path(config_dir).expanduser()
        if config_dir is not None
        else local_config_directory()
    )
    client_secret = directory / YOUTUBE_CLIENT_SECRET_FILENAME
    token_path = directory / YOUTUBE_TOKEN_FILENAME
    if not client_secret.is_file():
        raise YouTubePublishError(
            f"YouTube OAuth credentials are missing. Download a Desktop app OAuth client "
            f"and save it as {client_secret}"
        )
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise YouTubePublishError(
            "YouTube publishing dependencies are missing. Reinstall the package dependencies."
        ) from exc

    credentials = None
    if token_path.is_file():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(token_path), list(YOUTUBE_SCOPES)
            )
        except (ValueError, json.JSONDecodeError):
            credentials = None
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret), list(YOUTUBE_SCOPES)
        )
        credentials = flow.run_local_server(port=0, open_browser=True)
    directory.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def fetch_template_playlist(youtube, playlist_id: str) -> dict[str, Any]:
    response = youtube.playlists().list(part="snippet,status", id=playlist_id).execute(
        num_retries=5
    )
    items = response.get("items", [])
    if not items:
        raise YouTubePublishError(f"Template playlist was not found: {playlist_id}")
    playlist = items[0]
    lessons: list[dict[str, Any]] = []
    page_token = None
    while True:
        page = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute(num_retries=5)
        for item in page.get("items", []):
            snippet = item.get("snippet", {})
            lessons.append(
                {
                    "position": snippet.get("position"),
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                }
            )
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    snippet = playlist.get("snippet", {})
    return {
        "id": playlist_id,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "lesson_count": len(lessons),
        "lessons": lessons,
    }


def _metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["course", "cover", "videos"],
        "properties": {
            "course": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "description"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "cover": {
                "type": "object",
                "additionalProperties": False,
                "required": ["headline", "subtitle"],
                "properties": {
                    "headline": {"type": "string"},
                    "subtitle": {"type": "string"},
                },
            },
            "videos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["lesson_id", "title", "description", "tags"],
                    "properties": {
                        "lesson_id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    }


def _prompt_payload(bundle: CourseBundle, template: dict[str, Any]) -> dict[str, Any]:
    course_info = bundle.course.get("course", {})
    lessons = []
    for video in bundle.videos:
        manifest = video.manifest
        lessons.append(
            {
                "lesson_id": video.lesson_id,
                "sequence_number": video.number,
                "title": manifest.get("title", ""),
                "focus": manifest.get("focus", ""),
                "learning_outcomes": manifest.get("learning_outcomes", []),
                "target_minutes": manifest.get("target_minutes"),
            }
        )
    return {
        "template": {
            "title": template.get("title", ""),
            "description": str(template.get("description", ""))[:5000],
            "lessons": [
                {
                    "position": item.get("position"),
                    "title": item.get("title", ""),
                    "description": str(item.get("description", ""))[:1200],
                }
                for item in template.get("lessons", [])[:30]
            ],
        },
        "new_course": {
            "title": course_info.get("title", bundle.workspace.name),
            "audience": course_info.get("audience", ""),
            "summary": bundle.course.get("global_course_summary")
            or bundle.plan.get("course_summary", ""),
            "pedagogical_strategy": bundle.plan.get("pedagogical_strategy", ""),
            "lessons": lessons,
        },
    }


def generate_youtube_metadata(
    bundle: CourseBundle,
    template: dict[str, Any],
    provider: JSONLLMProvider,
) -> dict[str, Any]:
    payload = _prompt_payload(bundle, template)
    prompt = """You are preparing an original educational course for YouTube.

Use the existing playlist only as a structural and editorial style reference. Never copy
topic-specific claims, titles, descriptions, affiliations, URLs, or calls to action from it.
Use only the supplied new-course facts. Produce a welcoming course introduction, clear
learning value, intended audience, prerequisites when supported, lesson sequence, and concise
educational video metadata. Number every video title consistently. Descriptions should explain
what viewers will learn and may include a short course-navigation line, but must not invent links.
Tags must be specific, non-spammy phrases. The cover text must be brief enough for a square image.

YouTube constraints:
- course title: at most 150 characters
- video title: at most 100 characters
- descriptions: at most 5000 characters
- return exactly one video record for every supplied lesson_id, in sequence

INPUT JSON:
""" + json.dumps(payload, ensure_ascii=False, indent=2)
    result = provider.generate_json(prompt, _metadata_schema())
    return normalize_metadata(result, bundle)


def _clean_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit].rstrip()


def _clean_tags(values: Any) -> list[str]:
    tags: list[str] = []
    total = 0
    for raw in values if isinstance(values, list) else []:
        tag = " ".join(str(raw).split()).strip(",")[:60]
        if not tag or tag.casefold() in {item.casefold() for item in tags}:
            continue
        projected = total + len(tag) + (1 if tags else 0)
        if projected > 450:
            break
        tags.append(tag)
        total = projected
    return tags


def normalize_metadata(data: dict[str, Any], bundle: CourseBundle) -> dict[str, Any]:
    course = data.get("course", {})
    cover = data.get("cover", {})
    raw_videos = data.get("videos", [])
    if not isinstance(course, dict) or not isinstance(cover, dict) or not isinstance(raw_videos, list):
        raise YouTubePublishError("Gemini returned malformed YouTube metadata.")
    by_id = {
        str(item.get("lesson_id")): item
        for item in raw_videos
        if isinstance(item, dict) and item.get("lesson_id")
    }
    expected_ids = [video.lesson_id for video in bundle.videos]
    if set(by_id) != set(expected_ids):
        raise YouTubePublishError(
            "Generated metadata lesson IDs do not exactly match the course: "
            f"expected {expected_ids}, received {sorted(by_id)}"
        )
    title = _clean_text(course.get("title"), 150)
    description = _clean_text(course.get("description"), 5000)
    if not title or not description:
        raise YouTubePublishError("Generated course title and description must not be empty.")
    videos = []
    for video in bundle.videos:
        item = by_id[video.lesson_id]
        video_title = _clean_text(item.get("title"), 100)
        video_description = _clean_text(item.get("description"), 5000)
        if not video_title or not video_description:
            raise YouTubePublishError(f"Incomplete metadata for {video.lesson_id}")
        videos.append(
            {
                "lesson_id": video.lesson_id,
                "title": video_title,
                "description": video_description,
                "tags": _clean_tags(item.get("tags", [])),
            }
        )
    return {
        "course": {"title": title, "description": description},
        "cover": {
            "headline": _clean_text(cover.get("headline") or title, 80),
            "subtitle": _clean_text(cover.get("subtitle"), 100),
        },
        "videos": videos,
    }


def _font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows"))
        / "Fonts"
        / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _wrapped_lines(draw, text: str, font, max_width: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = textwrap.shorten(lines[-1], width=max(8, len(lines[-1]) - 1), placeholder="…")
    return lines


def create_course_cover(metadata: dict[str, Any], output_path: str | Path) -> Path:
    """Create a polished square playlist/course image under the workspace."""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise YouTubePublishError("Pillow is required to create the course image.") from exc

    size = 1200
    image = Image.new("RGB", (size, size), "#081629")
    pixels = image.load()
    for y in range(size):
        ratio = y / (size - 1)
        for x in range(size):
            glow = max(0.0, 1.0 - (((x - 930) ** 2 + (y - 180) ** 2) ** 0.5) / 900)
            pixels[x, y] = (
                int(8 + 11 * ratio + 9 * glow),
                int(22 + 18 * ratio + 64 * glow),
                int(41 + 33 * ratio + 76 * glow),
            )
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((810, -170, 1370, 390), fill=(36, 195, 181, 38), outline=(99, 241, 220, 90), width=5)
    draw.ellipse((900, -80, 1250, 270), outline=(255, 190, 77, 130), width=7)
    for offset in range(0, 1100, 90):
        draw.line((70, 1040 - offset // 6, 1130, 780 - offset), fill=(108, 174, 210, 18), width=2)
    draw.rounded_rectangle((70, 78, 340, 142), radius=28, fill=(32, 205, 184, 230))
    label_font = _font(31, bold=True)
    draw.text((102, 92), "MICROCREDENTIAL", font=label_font, fill=(5, 35, 48, 255))
    headline = str(metadata.get("cover", {}).get("headline", "Course"))
    subtitle = str(metadata.get("cover", {}).get("subtitle", ""))
    title_font = _font(88, bold=True)
    title_lines = _wrapped_lines(draw, headline, title_font, 1010, 5)
    y = 240
    for line in title_lines:
        draw.text((78, y), line, font=title_font, fill=(247, 250, 252, 255), stroke_width=1)
        y += 108
    if subtitle:
        subtitle_font = _font(39)
        y += 28
        for line in _wrapped_lines(draw, subtitle, subtitle_font, 940, 3):
            draw.text((82, y), line, font=subtitle_font, fill=(190, 218, 230, 255))
            y += 54
    draw.rounded_rectangle((78, 1060, 630, 1118), radius=22, fill=(255, 255, 255, 25))
    draw.text((104, 1074), "Structured lessons • Clear explanations", font=_font(27), fill=(224, 238, 245, 230))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="JPEG", quality=90, optimize=True)
    if output.stat().st_size > 2_000_000:
        image.save(output, format="JPEG", quality=78, optimize=True)
    return output.resolve()


def _file_fingerprint(path: Path) -> str:
    stat = path.stat()
    raw = f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}".encode()
    return hashlib.sha256(raw).hexdigest()


def _read_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": 1, "playlist": {}, "videos": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise YouTubePublishError(f"Invalid publishing state: {path}")
    data.setdefault("playlist", {})
    data.setdefault("videos", {})
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_channel(youtube, expected_handle: str | None = None) -> dict[str, str]:
    result = youtube.channels().list(part="id,snippet", mine=True).execute(num_retries=5)
    items = result.get("items", [])
    if len(items) != 1:
        raise YouTubePublishError("Could not identify the authorized YouTube channel.")
    item = items[0]
    snippet = item.get("snippet", {})
    actual = str(snippet.get("customUrl", ""))
    if expected_handle and actual and actual.casefold() != expected_handle.casefold():
        raise YouTubePublishError(
            f"Authorized channel {actual!r} does not match expected channel {expected_handle!r}."
        )
    return {"id": str(item.get("id", "")), "title": str(snippet.get("title", "")), "handle": actual}


def _upload_video(youtube, video: CourseVideo, metadata: dict[str, Any], options: dict[str, Any]) -> str:
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata.get("tags", []),
            "categoryId": options["category_id"],
            "defaultLanguage": options["language"],
            "defaultAudioLanguage": options["language"],
        },
        "status": {
            "privacyStatus": options["privacy"],
            "selfDeclaredMadeForKids": options["made_for_kids"],
            "embeddable": True,
            "license": "youtube",
        },
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        notifySubscribers=options["notify_subscribers"],
        media_body=MediaFileUpload(str(video.path), mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024),
    )
    response = None
    while response is None:
        progress, response = request.next_chunk(num_retries=5)
        if progress:
            print(f"  {video.lesson_id}: {progress.progress() * 100:.0f}% uploaded")
    return str(response["id"])


def _add_to_playlist(youtube, playlist_id: str, youtube_video_id: str, position: int) -> str:
    response = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "position": position,
                "resourceId": {"kind": "youtube#video", "videoId": youtube_video_id},
            }
        },
    ).execute(num_retries=5)
    return str(response["id"])


def _list_playlist_items(youtube, playlist_id: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    page_token = None
    while True:
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute(num_retries=5)
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            resource_id = snippet.get("resourceId", {})
            items.append(
                {
                    "id": str(item.get("id", "")),
                    "video_id": str(resource_id.get("videoId", "")),
                }
            )
        page_token = response.get("nextPageToken")
        if not page_token:
            return items


def _arrange_playlist_items(
    youtube,
    playlist_id: str,
    ordered_video_ids: list[str],
) -> int:
    """Put course videos first in the requested order, moving only misplaced items."""
    items = _list_playlist_items(youtube, playlist_id)
    updates = 0
    for position, video_id in enumerate(ordered_video_ids):
        current_position = next(
            (index for index, item in enumerate(items) if item["video_id"] == video_id),
            None,
        )
        if current_position is None:
            raise YouTubePublishError(
                f"Uploaded video {video_id!r} is missing from playlist {playlist_id!r}."
            )
        if current_position == position:
            continue
        item = items[current_position]
        youtube.playlistItems().update(
            part="snippet",
            body={
                "id": item["id"],
                "snippet": {
                    "playlistId": playlist_id,
                    "position": position,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                },
            },
        ).execute(num_retries=5)
        items.insert(position, items.pop(current_position))
        updates += 1
    return updates


def _verify_playlist_prefix(
    youtube,
    playlist_id: str,
    ordered_video_ids: list[str],
) -> None:
    """Require every replacement to be live and correctly ordered before cleanup."""
    actual = [item["video_id"] for item in _list_playlist_items(youtube, playlist_id)]
    if actual[: len(ordered_video_ids)] != ordered_video_ids:
        raise YouTubePublishError(
            "Replacement videos are not yet verified at the start of the playlist. "
            "The old playlist entries were preserved; rerun the command to reconcile."
        )


def _remove_video_from_playlist(youtube, playlist_id: str, video_id: str) -> int:
    matches = [
        item for item in _list_playlist_items(youtube, playlist_id) if item["video_id"] == video_id
    ]
    for item in matches:
        youtube.playlistItems().delete(id=item["id"]).execute(num_retries=5)
    return len(matches)


def _retire_video(youtube, video_id: str, policy: str) -> None:
    if policy == "keep":
        return
    if policy == "delete":
        existing = youtube.videos().list(part="id", id=video_id).execute(num_retries=5)
        if not existing.get("items"):
            return
        youtube.videos().delete(id=video_id).execute(num_retries=5)
        return
    response = youtube.videos().list(part="status", id=video_id).execute(num_retries=5)
    items = response.get("items", [])
    if not items:
        raise YouTubePublishError(f"Cannot change visibility; old video was not found: {video_id}")
    current = items[0].get("status", {})
    mutable_fields = {
        "privacyStatus",
        "publishAt",
        "license",
        "embeddable",
        "publicStatsViewable",
        "selfDeclaredMadeForKids",
    }
    status = {key: value for key, value in current.items() if key in mutable_fields}
    status["privacyStatus"] = policy
    status.pop("publishAt", None)
    youtube.videos().update(
        part="status",
        body={"id": video_id, "status": status},
    ).execute(num_retries=5)


def _upload_caption(youtube, video_id: str, subtitle_path: Path, language: str) -> str:
    from googleapiclient.http import MediaFileUpload

    response = youtube.captions().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": "Course subtitles",
                "isDraft": False,
            }
        },
        media_body=MediaFileUpload(str(subtitle_path), mimetype="application/octet-stream"),
    ).execute(num_retries=5)
    return str(response["id"])


def _upload_playlist_image(youtube, playlist_id: str, cover_path: Path) -> str:
    from googleapiclient.http import MediaFileUpload

    response = youtube.playlistImages().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id, "type": "hero"}},
        media_body=MediaFileUpload(str(cover_path), mimetype="image/jpeg"),
    ).execute(num_retries=5)
    return str(response.get("id", ""))


def publish_course(
    youtube,
    bundle: CourseBundle,
    metadata: dict[str, Any],
    cover_path: Path,
    *,
    template_playlist_id: str,
    privacy: str = "public",
    category_id: str = "27",
    language: str = "en-GB",
    made_for_kids: bool = False,
    notify_subscribers: bool = False,
    replace_changed_videos: bool = False,
    confirm_playlist_id: str | None = None,
    retire_replaced_videos: str = "keep",
) -> dict[str, Any]:
    """Publish or resume a complete course. State is saved after every remote write."""
    output_dir = bundle.output_dir
    state_path = output_dir / "publish_state.json"
    state = _read_state(state_path)
    state["template_playlist_id"] = template_playlist_id
    state["privacy"] = privacy
    playlist = state["playlist"]
    if not playlist.get("id"):
        response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": metadata["course"],
                "status": {"privacyStatus": privacy},
            },
        ).execute(num_retries=5)
        playlist["id"] = str(response["id"])
        playlist["url"] = f"https://www.youtube.com/playlist?list={response['id']}"
        _write_json(state_path, state)
    playlist_id = str(playlist["id"])

    if retire_replaced_videos not in {"keep", "unlisted", "private", "delete"}:
        raise YouTubePublishError(
            "retire_replaced_videos must be keep, unlisted, private, or delete."
        )

    replacements: list[tuple[CourseVideo, dict[str, Any], str]] = []
    for video in bundle.videos:
        record = state["videos"].get(video.lesson_id, {})
        fingerprint = _file_fingerprint(video.path)
        if record.get("fingerprint") and record["fingerprint"] != fingerprint:
            replacements.append((video, record, fingerprint))
    if replacements and not replace_changed_videos:
        names = ", ".join(video.path.name for video, _, _ in replacements)
        raise YouTubePublishError(
            f"Changed uploaded files detected ({names}). Rerun with "
            "--replace-changed-videos and --confirm-playlist-id to use controlled replacement."
        )
    if replacements and confirm_playlist_id != playlist_id:
        raise YouTubePublishError(
            "Controlled replacement requires --confirm-playlist-id to exactly match "
            f"the existing destination playlist ({playlist_id})."
        )

    options = {
        "privacy": privacy,
        "category_id": category_id,
        "language": language,
        "made_for_kids": made_for_kids,
        "notify_subscribers": notify_subscribers,
    }
    video_metadata = {item["lesson_id"]: item for item in metadata["videos"]}
    for position, video in enumerate(bundle.videos):
        record = state["videos"].setdefault(video.lesson_id, {})
        fingerprint = _file_fingerprint(video.path)
        changed = bool(record.get("fingerprint") and record["fingerprint"] != fingerprint)
        if changed:
            replacement = record.get("replacement")
            if replacement and replacement.get("target_fingerprint") != fingerprint:
                raise YouTubePublishError(
                    f"{video.path.name} changed again during an unfinished replacement. "
                    "Restore the expected file or resolve publish_state.json manually."
                )
            if not replacement:
                replacement = {
                    "target_fingerprint": fingerprint,
                    "old_youtube_video_id": record.get("youtube_video_id"),
                    "old_playlist_item_id": record.get("playlist_item_id"),
                    "old_caption_id": record.get("caption_id"),
                    "old_fingerprint": record.get("fingerprint"),
                }
                record["replacement"] = replacement
                state["complete"] = False
                _write_json(state_path, state)
            if not replacement.get("new_youtube_video_id"):
                print(f"Uploading replacement for {video.lesson_id}: {video.path.name}...")
                replacement["new_youtube_video_id"] = _upload_video(
                    youtube, video, video_metadata[video.lesson_id], options
                )
                replacement["new_url"] = (
                    f"https://youtu.be/{replacement['new_youtube_video_id']}"
                )
                _write_json(state_path, state)
            if not replacement.get("new_playlist_item_id"):
                replacement["new_playlist_item_id"] = _add_to_playlist(
                    youtube,
                    playlist_id,
                    replacement["new_youtube_video_id"],
                    position,
                )
                _write_json(state_path, state)
            if video.subtitle_path and not replacement.get("new_caption_id"):
                replacement["new_caption_id"] = _upload_caption(
                    youtube,
                    replacement["new_youtube_video_id"],
                    video.subtitle_path,
                    language,
                )
                _write_json(state_path, state)
            continue
        if not record.get("youtube_video_id"):
            print(f"Uploading {video.path.name} as {privacy} video {video.lesson_id}...")
            record["youtube_video_id"] = _upload_video(
                youtube, video, video_metadata[video.lesson_id], options
            )
            record["fingerprint"] = fingerprint
            record["url"] = f"https://youtu.be/{record['youtube_video_id']}"
            _write_json(state_path, state)
        if not record.get("playlist_item_id"):
            record["playlist_item_id"] = _add_to_playlist(
                youtube, playlist_id, record["youtube_video_id"], position
            )
            _write_json(state_path, state)
        if video.subtitle_path and not record.get("caption_id"):
            record["caption_id"] = _upload_caption(
                youtube, record["youtube_video_id"], video.subtitle_path, language
            )
            _write_json(state_path, state)
    ordered_video_ids = []
    for video in bundle.videos:
        record = state["videos"][video.lesson_id]
        replacement = record.get("replacement") or {}
        ordered_video_ids.append(
            str(replacement.get("new_youtube_video_id") or record["youtube_video_id"])
        )
    reordered = _arrange_playlist_items(youtube, playlist_id, ordered_video_ids)
    if reordered:
        print(f"Reordered {reordered} playlist items into lesson sequence.")
    else:
        print("Verified playlist lesson sequence.")
    if replacements:
        _verify_playlist_prefix(youtube, playlist_id, ordered_video_ids)
        for video, record, fingerprint in replacements:
            replacement = record["replacement"]
            old_video_id = str(replacement["old_youtube_video_id"])
            if not replacement.get("old_playlist_removed"):
                removed = _remove_video_from_playlist(youtube, playlist_id, old_video_id)
                replacement["old_playlist_removed"] = True
                replacement["removed_playlist_items"] = removed
                _write_json(state_path, state)
            if not replacement.get("old_video_retired"):
                _retire_video(youtube, old_video_id, retire_replaced_videos)
                replacement["old_video_retired"] = True
                replacement["retirement_policy"] = retire_replaced_videos
                _write_json(state_path, state)

            history = record.setdefault("replacement_history", [])
            history.append(
                {
                    "youtube_video_id": old_video_id,
                    "url": record.get("url"),
                    "fingerprint": replacement.get("old_fingerprint"),
                    "playlist_item_id": replacement.get("old_playlist_item_id"),
                    "caption_id": replacement.get("old_caption_id"),
                    "retirement_policy": retire_replaced_videos,
                }
            )
            record["youtube_video_id"] = replacement["new_youtube_video_id"]
            record["url"] = replacement["new_url"]
            record["playlist_item_id"] = replacement["new_playlist_item_id"]
            record["caption_id"] = replacement.get("new_caption_id")
            record["fingerprint"] = fingerprint
            del record["replacement"]
            _write_json(state_path, state)
        print(f"Replaced {len(replacements)} changed course videos safely.")
    if not playlist.get("image_id"):
        playlist["image_id"] = _upload_playlist_image(youtube, playlist_id, cover_path)
        _write_json(state_path, state)
    state["complete"] = True
    _write_json(state_path, state)
    return state


def write_metadata(bundle: CourseBundle, metadata: dict[str, Any]) -> Path:
    path = bundle.output_dir / "youtube_metadata.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path.resolve()


def load_metadata(path: str | Path, bundle: CourseBundle) -> dict[str, Any]:
    return normalize_metadata(_read_yaml(Path(path)), bundle)
