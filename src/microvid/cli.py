from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import yaml

from .assets import write_text_assets
from .auto_profile import write_scaffold_profile
from .docx_parser import write_extraction
from .global_planner import build_global_course_plan, extraction_signature, write_global_course_plan
from .manifest_builder import build_all_manifests
from .llm import provider_from_config
from .llm_manifest_builder import build_all_manifests_with_llm
from .media import audition_voices, build_windows_video, media_capabilities
from .profile import load_profile
from .qa import validate_workspace
from .slides import build_pptx
from .tts import TTSConfig


def _extraction_path(workspace: Path) -> Path:
    return workspace / "extracted" / "document_structure.json"


def _plan_path(workspace: Path) -> Path:
    return workspace / "plans" / "course_plan.yaml"


def _parser_config(profile_name: str | None) -> dict | None:
    if not profile_name:
        return None
    return load_profile(profile_name).get("parser")


def _llm_provider(profile: dict, args):
    llm_cfg = profile.get("course", {}).get("llm", {})
    return provider_from_config(
        llm_cfg,
        model=getattr(args, "model", None),
        thinking_level=getattr(args, "thinking_level", None),
    )


def _tts_config_from_args(args) -> TTSConfig:
    data: dict = {}
    profile_name = getattr(args, "profile", None)
    if profile_name:
        profile = load_profile(profile_name)
        data.update(profile.get("course", {}).get("tts", {}) or {})

    tts_config_path = getattr(args, "tts_config", None)
    if tts_config_path:
        raw = yaml.safe_load(Path(tts_config_path).read_text(encoding="utf-8")) or {}
        data.update(raw.get("tts", raw))

    cfg = TTSConfig.from_mapping(data).with_overrides(
        provider=getattr(args, "tts_provider", None),
        voice_name=getattr(args, "voice_name", None),
        language_code=getattr(args, "language_code", None),
        speaking_rate=getattr(args, "speaking_rate", None),
        location=getattr(args, "tts_location", None),
    )
    if getattr(args, "no_tts_fallback", False):
        cfg = cfg.with_overrides(fallback_on_error=False, fallback_provider=None)
    return cfg


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


def _load_extraction(workspace: Path) -> dict:
    path = _extraction_path(workspace)
    if not path.exists():
        raise SystemExit("Run 'microvid extract' first.")
    return json.loads(path.read_text(encoding="utf-8"))


def _get_or_build_global_plan(workspace: Path, extraction: dict, profile: dict, provider, args) -> dict:
    path = _plan_path(workspace)
    replan = bool(getattr(args, "replan", False))
    if path.exists() and not replan:
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if existing.get("source_signature") == extraction_signature(extraction):
            print(f"Reusing source-matched global course plan -> {path}")
            return existing
        print("Existing global plan does not match the current extracted DOCX; replanning.")

    plan = build_global_course_plan(
        extraction,
        profile,
        provider,
        review_pass=not bool(getattr(args, "no_plan_review_pass", False)),
    )
    write_global_course_plan(plan, path)
    print(f"Built global Gemini course plan ({len(plan.get('videos', []))} videos) -> {path}")
    return plan


def cmd_plan(args) -> int:
    workspace = Path(args.workspace)
    extraction = _load_extraction(workspace)
    profile = load_profile(args.profile)
    provider = _llm_provider(profile, args)
    args.replan = True
    _get_or_build_global_plan(workspace, extraction, profile, provider, args)
    return 0


def cmd_draft(args) -> int:
    workspace = Path(args.workspace)
    extraction = _load_extraction(workspace)
    profile = load_profile(args.profile)
    generator = getattr(args, "generator", "llm")
    design_mode = getattr(args, "design_mode", "global")

    if generator == "llm":
        provider = _llm_provider(profile, args)
        global_plan = None
        if design_mode == "global":
            global_plan = _get_or_build_global_plan(
                workspace, extraction, profile, provider, args
            )
        paths = build_all_manifests_with_llm(
            extraction,
            profile,
            workspace / "manifests",
            provider,
            review_pass=not getattr(args, "no_review_pass", False),
            global_plan=global_plan,
            course_consistency_review=(
                design_mode == "global"
                and not getattr(args, "no_global_consistency_review", False)
            ),
        )
    else:
        if design_mode != "profile":
            raise SystemExit(
                "Deterministic generation has no whole-document reasoning. Use "
                "--design-mode profile with --generator deterministic."
            )
        paths = build_all_manifests(extraction, profile, workspace / "manifests")

    for path in paths:
        write_text_assets(path, workspace)
    print(
        f"Generated {len(paths)} lesson manifests with notes, narration and subtitles "
        f"using {generator} generation ({design_mode} design)."
    )
    return 0


def _course_ready_for_slides(workspace: Path) -> tuple[bool, str | None]:
    path = workspace / "manifests" / "course.yaml"
    if not path.exists():
        return True, None
    course_index = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if course_index.get("design_mode") != "global_llm":
        return True, None
    status = str(course_index.get("global_consistency_status", "revision_required"))
    return status == "ready", status


def cmd_slides(args) -> int:
    workspace = Path(args.workspace)
    ready, status = _course_ready_for_slides(workspace)
    if not ready and not getattr(args, "allow_unreviewed_course", False):
        raise SystemExit(
            f"Whole-course consistency status is '{status}'. Slide production is blocked. "
            "Resolve the global review or use --allow-unreviewed-course only for diagnostics."
        )
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
    class X:
        pass

    x = X()
    x.source = args.source
    x.workspace = args.workspace
    x.profile = args.profile
    x.generator = args.generator
    x.design_mode = args.design_mode
    x.model = args.model
    x.thinking_level = args.thinking_level
    x.no_review_pass = args.no_review_pass
    x.no_plan_review_pass = args.no_plan_review_pass
    x.no_global_consistency_review = args.no_global_consistency_review
    x.replan = not args.reuse_plan
    cmd_extract(x)
    cmd_draft(x)
    x.video = None
    x.allow_unreviewed_course = False
    cmd_slides(x)
    return cmd_validate(x)


def cmd_media(args) -> int:
    cfg = _tts_config_from_args(args)
    output = build_windows_video(
        args.workspace,
        args.video,
        allow_draft=args.allow_draft,
        tts_config=cfg,
    )
    print(f"Built {output} using TTS provider {cfg.provider}, voice {cfg.voice_name}")
    return 0


def cmd_tts_audition(args) -> int:
    cfg = _tts_config_from_args(args)
    text = args.text or (
        "A measured value is incomplete without its uncertainty and units. "
        "For example, an acceleration of 9.81 m s⁻² ± 0.02 m s⁻² should be reported clearly."
    )
    paths = audition_voices(args.output_dir, text, cfg, voices=args.voices)
    for path in paths:
        print(f"Built {path}")
    return 0


def cmd_media_check(args) -> int:
    print(yaml.safe_dump(media_capabilities(), sort_keys=False))
    return 0


def _add_llm_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--model", help="Override the profile's LLM model without editing Python.")
    p.add_argument(
        "--thinking-level",
        choices=["low", "medium", "high"],
        help="Override LLM reasoning effort.",
    )


def _add_global_design_options(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--design-mode",
        choices=["global", "profile"],
        default="global",
        help="Global Gemini whole-document design is the production default; profile preserves the legacy pre-segmented workflow.",
    )
    p.add_argument(
        "--no-plan-review-pass",
        action="store_true",
        help="Skip the second Gemini review of the whole-document course plan.",
    )
    p.add_argument(
        "--no-global-consistency-review",
        action="store_true",
        help="Skip the final whole-course review. Intended only for development/cost diagnostics.",
    )


def _add_tts_options(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--profile", default="physics_lab_101", help="Course profile; may contain course.tts settings"
    )
    p.add_argument(
        "--tts-config",
        help="Optional standalone YAML file. Use either a top-level tts: mapping or the mapping itself.",
    )
    p.add_argument(
        "--tts-provider",
        choices=["google_cloud_chirp3", "sapi"],
        help="Override configured TTS provider",
    )
    p.add_argument("--voice-name", help="Override Google Cloud voice, e.g. en-GB-Chirp3-HD-Leda")
    p.add_argument("--language-code", help="Override TTS locale, e.g. en-GB")
    p.add_argument("--speaking-rate", type=float, help="Override TTS speaking rate")
    p.add_argument("--tts-location", help="Google Cloud TTS location, e.g. global or asia-southeast1")
    p.add_argument(
        "--no-tts-fallback",
        action="store_true",
        help="Fail instead of falling back to the configured secondary TTS provider",
    )


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="microvid", description="DOCX-to-microcredential video asset pipeline"
    )
    sp = p.add_subparsers(dest="command", required=True)

    e = sp.add_parser("extract", help="Extract semantic blocks and provenance from an explicitly supplied DOCX")
    e.add_argument("--source", required=True, help="Runtime DOCX. No bundled sample is used implicitly.")
    e.add_argument("--workspace", required=True)
    e.add_argument("--profile", help="Optional profile whose parser conventions should be applied")
    e.set_defaults(func=cmd_extract)

    sc = sp.add_parser("scaffold-profile", help="Create an editable constraint/profile shell for a new DOCX/topic")
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

    pl = sp.add_parser("plan", help="Have Gemini read the complete extracted DOCX and design the whole course before lesson generation")
    pl.add_argument("--workspace", required=True)
    pl.add_argument("--profile", default="physics_lab_101")
    _add_llm_options(pl)
    pl.add_argument("--no-plan-review-pass", action="store_true")
    pl.set_defaults(func=cmd_plan)

    d = sp.add_parser("draft", help="Build course and lesson manifests")
    d.add_argument("--workspace", required=True)
    d.add_argument("--profile", default="physics_lab_101")
    d.add_argument(
        "--generator",
        choices=["llm", "deterministic"],
        default="llm",
        help="LLM is the normal content-authoring path; deterministic is offline/debug only.",
    )
    _add_llm_options(d)
    _add_global_design_options(d)
    d.add_argument("--replan", action="store_true", help="Force a fresh whole-document Gemini plan even when a source-matched plan exists.")
    d.add_argument(
        "--no-review-pass",
        action="store_true",
        help="Use one lesson-generation pass instead of generation + grounded lesson review.",
    )
    d.set_defaults(func=cmd_draft)

    s = sp.add_parser("slides", help="Build PowerPoint decks from manifests")
    s.add_argument("--workspace", required=True)
    s.add_argument("--video", help="Optional video id, e.g. V05")
    s.add_argument("--allow-unreviewed-course", action="store_true", help="Diagnostic override for a global course whose consistency review is not ready.")
    s.set_defaults(func=cmd_slides)

    v = sp.add_parser("validate", help="Run content-structure QA")
    v.add_argument("--workspace", required=True)
    v.set_defaults(func=cmd_validate)

    a = sp.add_parser("all", help="Extract, globally plan, draft, globally review, build slides and validate")
    a.add_argument("--source", required=True, help="Runtime DOCX. No bundled sample is used implicitly.")
    a.add_argument("--workspace", required=True)
    a.add_argument("--profile", default="physics_lab_101")
    a.add_argument("--generator", choices=["llm", "deterministic"], default="llm")
    _add_llm_options(a)
    _add_global_design_options(a)
    a.add_argument("--reuse-plan", action="store_true", help="Reuse an existing plan only when its source signature exactly matches the extracted DOCX.")
    a.add_argument("--no-review-pass", action="store_true")
    a.set_defaults(func=cmd_all)

    m = sp.add_parser("media-check", help="Report local media-production capabilities")
    m.set_defaults(func=cmd_media_check)

    mv = sp.add_parser("media", help="Render an approved lesson to MP4 on Windows using PowerPoint + configurable TTS + ffmpeg")
    mv.add_argument("--workspace", required=True)
    mv.add_argument("--video", required=True, help="Video id, e.g. V05")
    mv.add_argument("--allow-draft", action="store_true", help="Allow private preview rendering before editorial approval")
    _add_tts_options(mv)
    mv.set_defaults(func=cmd_media)

    av = sp.add_parser("tts-audition", help="Synthesize the same sample narration with several candidate voices")
    av.add_argument("--output-dir", required=True)
    av.add_argument("--text", help="Optional audition text; a short scientific sample is used by default")
    av.add_argument("--voice", action="append", dest="voices", help="Voice to audition; repeat for multiple voices")
    _add_tts_options(av)
    av.set_defaults(func=cmd_tts_audition)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
