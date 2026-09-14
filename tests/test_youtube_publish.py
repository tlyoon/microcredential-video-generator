from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import microvid.youtube_publish as publishing
from microvid.cli import parser
from microvid.youtube_publish import (
    YouTubePublishError,
    create_course_cover,
    load_course_bundle,
    normalize_metadata,
    publish_course,
)


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace" / "course"
    (root / "manifests").mkdir(parents=True)
    (root / "plans").mkdir()
    (root / "videos").mkdir()
    (root / "subtitles").mkdir()
    course = {
        "course": {"id": "course", "title": "Test Course", "audience": "Students"},
        "global_course_summary": "A compact test course.",
        "videos": [],
    }
    for number in (1, 2, 3):
        lesson_id = f"V{number:02d}"
        filename = f"video_{number:02d}.yaml"
        course["videos"].append({"id": lesson_id, "manifest": filename})
        (root / "manifests" / filename).write_text(
            yaml.safe_dump(
                {
                    "video_id": lesson_id,
                    "title": f"Lesson {number}",
                    "focus": f"Focus {number}",
                    "learning_outcomes": [f"Outcome {number}"],
                }
            ),
            encoding="utf-8",
        )
        (root / "videos" / f"video_{number:02d}.mp4").write_bytes(b"video" + bytes([number]))
        (root / "subtitles" / f"video_{number:02d}.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nTest\n", encoding="utf-8"
        )
    (root / "manifests" / "course.yaml").write_text(
        yaml.safe_dump(course), encoding="utf-8"
    )
    (root / "plans" / "course_plan.yaml").write_text(
        yaml.safe_dump({"course_summary": "Plan summary"}), encoding="utf-8"
    )
    return root


def _metadata(bundle):
    return {
        "course": {"title": "Test Course", "description": "Course description"},
        "cover": {"headline": "Test Course", "subtitle": "Learn clearly"},
        "videos": [
            {
                "lesson_id": video.lesson_id,
                "title": f"{video.number}. Lesson {video.number}",
                "description": f"Description {video.number}",
                "tags": ["test", "course"],
            }
            for video in bundle.videos
        ],
    }


def test_load_course_bundle_orders_videos_and_matches_subtitles(tmp_path):
    root = _workspace(tmp_path)

    bundle = load_course_bundle(root)

    assert [item.lesson_id for item in bundle.videos] == ["V01", "V02", "V03"]
    assert all(item.subtitle_path and item.subtitle_path.is_file() for item in bundle.videos)


def test_youtube_cli_defaults_to_public_uploads():
    args = parser().parse_args(["youtube", "publish", "--workspace", "workspace/course"])

    assert args.privacy == "public"
    assert args.template_playlist == publishing.DEFAULT_TEMPLATE_PLAYLIST_ID


def test_normalize_metadata_requires_exact_lesson_ids(tmp_path):
    bundle = load_course_bundle(_workspace(tmp_path))
    data = _metadata(bundle)
    data["videos"].pop()

    with pytest.raises(YouTubePublishError, match="lesson IDs"):
        normalize_metadata(data, bundle)


def test_course_cover_is_square_and_within_youtube_limit(tmp_path):
    bundle = load_course_bundle(_workspace(tmp_path))
    output = create_course_cover(_metadata(bundle), tmp_path / "cover.jpg")

    from PIL import Image

    with Image.open(output) as image:
        assert image.size == (1200, 1200)
    assert output.stat().st_size < 2_000_000


class _Request:
    def __init__(self, response):
        self.response = response

    def execute(self, **_kwargs):
        return self.response


def test_upload_playlist_image_uses_supported_hero_type(tmp_path):
    class PlaylistImages:
        request = None

        def insert(self, **kwargs):
            self.request = kwargs
            return _Request({"id": "image-1"})

    class YouTube:
        playlist_images = PlaylistImages()

        def playlistImages(self):
            return self.playlist_images

    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"jpeg")
    youtube = YouTube()

    image_id = publishing._upload_playlist_image(youtube, "PL-new", cover)

    assert image_id == "image-1"
    assert youtube.playlist_images.request["body"] == {
        "snippet": {"playlistId": "PL-new", "type": "hero"}
    }


def test_arrange_playlist_items_moves_only_misplaced_videos():
    class PlaylistItems:
        def __init__(self):
            self.updates = []

        def list(self, **_kwargs):
            return _Request(
                {
                    "items": [
                        {
                            "id": f"item-{video_id}",
                            "snippet": {
                                "position": position,
                                "resourceId": {"videoId": video_id},
                            },
                        }
                        for position, video_id in enumerate(("video-3", "video-2", "video-1"))
                    ]
                }
            )

        def update(self, **kwargs):
            self.updates.append(kwargs)
            return _Request(kwargs["body"])

    class YouTube:
        playlist_items = PlaylistItems()

        def playlistItems(self):
            return self.playlist_items

    youtube = YouTube()

    updates = publishing._arrange_playlist_items(
        youtube, "PL-new", ["video-1", "video-2", "video-3"]
    )

    assert updates == 2
    snippets = [request["body"]["snippet"] for request in youtube.playlist_items.updates]
    assert [(item["resourceId"]["videoId"], item["position"]) for item in snippets] == [
        ("video-1", 0),
        ("video-2", 1),
    ]


class _Playlists:
    def __init__(self):
        self.inserts = 0

    def insert(self, **_kwargs):
        self.inserts += 1
        return _Request({"id": "PL-new"})


class _YouTube:
    def __init__(self):
        self.playlists_api = _Playlists()

    def playlists(self):
        return self.playlists_api


def test_publish_state_makes_rerun_idempotent(tmp_path, monkeypatch):
    bundle = load_course_bundle(_workspace(tmp_path))
    metadata = _metadata(bundle)
    cover = create_course_cover(metadata, bundle.output_dir / "course_cover.jpg")
    youtube = _YouTube()
    calls = {"video": 0, "item": 0, "caption": 0, "image": 0, "arrange": 0}

    def upload_video(*_args, **_kwargs):
        calls["video"] += 1
        return f"youtube-{calls['video']}"

    def add_item(*_args, **_kwargs):
        calls["item"] += 1
        return f"item-{calls['item']}"

    def upload_caption(*_args, **_kwargs):
        calls["caption"] += 1
        return f"caption-{calls['caption']}"

    def upload_image(*_args, **_kwargs):
        calls["image"] += 1
        return "image-1"

    def arrange_items(*_args, **_kwargs):
        calls["arrange"] += 1
        return 0

    monkeypatch.setattr(publishing, "_upload_video", upload_video)
    monkeypatch.setattr(publishing, "_add_to_playlist", add_item)
    monkeypatch.setattr(publishing, "_upload_caption", upload_caption)
    monkeypatch.setattr(publishing, "_upload_playlist_image", upload_image)
    monkeypatch.setattr(publishing, "_arrange_playlist_items", arrange_items)

    kwargs = {"template_playlist_id": "PL-template", "privacy": "public"}
    first = publish_course(youtube, bundle, metadata, cover, **kwargs)
    second = publish_course(youtube, bundle, metadata, cover, **kwargs)

    assert first["complete"] is True
    assert second["playlist"]["url"].endswith("PL-new")
    assert calls == {"video": 3, "item": 3, "caption": 3, "image": 1, "arrange": 2}
    assert youtube.playlists_api.inserts == 1
    saved = json.loads((bundle.output_dir / "publish_state.json").read_text())
    assert saved["privacy"] == "public"
