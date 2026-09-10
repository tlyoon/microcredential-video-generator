from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import yaml

from .assets import write_text_assets
from .auto_profile import write_scaffold_profile
from .docx_parser import write_extraction
from .manifest_builder import build_all_manifests
from .llm import provider_from_config
from .llm_manifest_builder import build_all_manifests_with_llm
from .media import build_windows_video, media_capabilities
from .profile import load_profile
from .qa import validate_workspace
from .slides import build_pptx


def _extraction_path(workspace: Path) -> Path:
    return workspace / "extracted" / "document_structure.json"


def _parser_config(profile_name: str | None) -> dict | None:
    if not profile_name:
        return None
    return load_profile(profile_name).get("parser")


def cmd_extract(args) -> int:
    workspace = Path(args.workspace)
    parser_config = _parser_config(getattr(args, "profile", None))
    payload = write_extraction(args.source, _extraction_path(workspace), parser_config=parser_config)
    print(f"Extracted {payload['block_count']} blocks -> {_extraction_path(workspace)}")
    return 0


def cmd_scaffold(args) -> int:
    workspace = Path(args.workspace)
    payload = write_extraction(args.source, _extraction_path(workspace))
    output = write_scaffold_profile(
        payload,
        args.output,
        course_id=args.course_id,
        title=args.title,
        target_video_minutes=args.target_minutes,
        narration_wpm=args.narration_wpm,
        source_compression_ratio=args.source_compression_ratio,
        max_slides=args.max_slides,
    )
    print(f"Scaffolded source-structure profile -> {output}")
    return 0


def cmd_draft(args) -> int:
    workspace = Path(args.workspace)
    p = _extraction_path(workspace)
    if not p.exists():
        raise SystemExit("Run 'microvid extract' first.")
    extraction = json.loads(p.read_text(encoding="utf-8"))
    profile = load_profile(args.profile)
    generator = getattr(args, "generator", "llm")
    if generator == "llm":
        llm_cfg = profile.get("course", {}).get("llm", {})
        provider = provider_from_config(
            llm_cfg,
            model=getattr(args, "model", None),
            thinking_level=getattr(args, "thinking_level", None),
        )
        paths = build_all_manifests_with_llm(
            extraction,
            profile,
            workspace / "manifests",
            provider,
            review_pass=not getattr(args, "no_review_pass", False),
        )
    else:
        paths = build_all_manifests(extraction, profile, workspace / "manifests")
    for path in paths:
        write_text_assets(path, workspace)
    print(f"Generated {len(paths)} lesson manifests with notes, narration and subtitles using {generator} generation.")
    return 0


def cmd_slides(args) -> int:
    workspace = Path(args.workspace)
    paths = sorted((workspace / "manifests").glob("video_*.yaml"))
    if args.video:
        wanted = int(args.video.upper().lstrip("V"))
        paths = [p for p in paths if int(p.stem.split("_")[1]) == wanted]
    if not paths:
        raise SystemExit("No lesson manifests found. Run 'microvid draft' first.")
    for path in paths:
        num = int(path.stem.split("_")[1])
        out = workspace / "slides" / f"video_{num:02d}.pptx"
        build_pptx(path, out)
        print(f"Built {out}")
    return 0


def cmd_validate(args) -> int:
    result = validate_workspace(args.workspace)
    print(yaml.safe_dump(result, sort_keys=False))
    return 1 if result["errors"] else 0


def cmd_all(args) -> int:
    class X: pass
    x = X(); x.source=args.source; x.workspace=args.workspace; x.profile=args.profile
    x.generator=args.generator; x.model=args.model; x.thinking_level=args.thinking_level; x.no_review_pass=args.no_review_pass
    cmd_extract(x)
    cmd_draft(x)
    x.video=None
    cmd_slides(x)
    return cmd_validate(x)


def cmd_media(args) -> int:
    output = build_windows_video(args.workspace, args.video, allow_draft=args.allow_draft)
    print(f"Built {output}")
    return 0


def cmd_media_check(args) -> int:
    print(yaml.safe_dump(media_capabilities(), sort_keys=False))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="microvid", description="DOCX-to-microcredential video asset pipeline")
    sp = p.add_subparsers(dest="command", required=True)

    e = sp.add_parser("extract", help="Extract semantic blocks and provenance from an explicitly supplied DOCX")
    e.add_argument("--source", required=True, help="Runtime DOCX. No bundled sample is used implicitly.")
    e.add_argument("--workspace", required=True)
    e.add_argument("--profile", help="Optional profile whose parser conventions should be applied")
    e.set_defaults(func=cmd_extract)

    sc = sp.add_parser("scaffold-profile", help="Create an editable structural course profile for a new DOCX/topic")
    sc.add_argument("--source", required=True)
    sc.add_argument("--workspace", required=True)
    sc.add_argument("--output", required=True, help="Output YAML profile path")
    sc.add_argument("--course-id", required=True)
    sc.add_argument("--title", required=True)
    sc.add_argument("--target-minutes", type=float, default=6.0)
    sc.add_argument("--narration-wpm", type=int, default=130)
    sc.add_argument("--source-compression-ratio", type=float, default=1.9)
    sc.add_argument("--max-slides", type=int, default=7)
    sc.set_defaults(func=cmd_scaffold)

    d = sp.add_parser("draft", help="Build course and lesson manifests")
    d.add_argument("--workspace", required=True)
    d.add_argument("--profile", default="physics_lab_101")
    d.add_argument("--generator", choices=["llm", "deterministic"], default="llm", help="LLM is the normal content-authoring path; deterministic is offline/debug only.")
    d.add_argument("--model", help="Override the profile's LLM model without editing Python.")
    d.add_argument("--thinking-level", choices=["low", "medium", "high"], help="Override LLM reasoning effort.")
    d.add_argument("--no-review-pass", action="store_true", help="Use one LLM generation pass instead of the default generate+review/revision workflow.")
    d.set_defaults(func=cmd_draft)

    s = sp.add_parser("slides", help="Build PowerPoint decks from manifests")
    s.add_argument("--workspace", required=True)
    s.add_argument("--video", help="Optional video id, e.g. V05")
    s.set_defaults(func=cmd_slides)

    v = sp.add_parser("validate", help="Run content-structure QA")
    v.add_argument("--workspace", required=True)
    v.set_defaults(func=cmd_validate)

    a = sp.add_parser("all", help="Extract, draft, build slides and validate")
    a.add_argument("--source", required=True, help="Runtime DOCX. No bundled sample is used implicitly.")
    a.add_argument("--workspace", required=True)
    a.add_argument("--profile", default="physics_lab_101")
    a.add_argument("--generator", choices=["llm", "deterministic"], default="llm")
    a.add_argument("--model", help="Override the profile's LLM model.")
    a.add_argument("--thinking-level", choices=["low", "medium", "high"], help="Override LLM reasoning effort.")
    a.add_argument("--no-review-pass", action="store_true")
    a.set_defaults(func=cmd_all)

    m = sp.add_parser("media-check", help="Report local media-production capabilities")
    m.set_defaults(func=cmd_media_check)

    mv = sp.add_parser("media", help="Render an approved lesson to MP4 on Windows using PowerPoint + SAPI + ffmpeg")
    mv.add_argument("--workspace", required=True)
    mv.add_argument("--video", required=True, help="Video id, e.g. V05")
    mv.add_argument("--allow-draft", action="store_true", help="Allow private preview rendering before editorial approval")
    mv.set_defaults(func=cmd_media)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
