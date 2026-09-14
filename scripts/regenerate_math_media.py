"""Regenerate Microvid PPTX and MP4 files with native, source-audited OfficeMath.

This repair path preserves existing narration audio. It rebuilds each deck from its
manifest, validates that every expected math zone is native PowerPoint OfficeMath, renders
the deck through desktop PowerPoint, and replaces the MP4 only after every new segment has
been created successfully.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import yaml
from lxml import etree
from omml2latex import convert_omml

from microvid.docx_parser import extract_docx
from microvid.media import _make_segment, concat_segments, render_powerpoint
from microvid.office_math import DRAWING_2010_NS, MATH_NS, looks_like_math
from microvid.slides import build_pptx

_RAW_LATEX = re.compile(r"\\(?:frac|sqrt|sum|text|left|right|pm|times|approx|implies)\b")
_NORMALIZE_COMMANDS = re.compile(r"\\(?:left|right|boxed|mathrm|text|quad|qquad|,|;|!)")
_NON_SEMANTIC = re.compile(r"[^0-9A-Za-zα-ωΑ-Ω+\-=/<>.%]+")
_AUDIO_SUFFIXES = (".wav", ".mp3", ".m4a", ".aac", ".flac")


def _normalize_latex(value: str) -> str:
    value = value.strip().strip("$")
    value = _NORMALIZE_COMMANDS.sub("", value)
    replacements = {
        r"\pm": "±",
        r"\times": "×",
        r"\approx": "≈",
        r"\neq": "≠",
        r"\leq": "≤",
        r"\geq": "≥",
        r"\implies": "→",
        r"\rightarrow": "→",
        r"\rho": "ρ",
        r"\pi": "π",
        r"\sigma": "σ",
        r"\Delta": "Δ",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = value.replace("{", "").replace("}", "")
    return _NON_SEMANTIC.sub("", value).casefold()


def _source_equations(source_docx: Path) -> list[str]:
    # Parse through the project extractor first so a malformed/truncated DOCX fails early.
    extracted = extract_docx(source_docx)
    if not any(block.get("omml") for block in extracted.get("blocks", [])):
        raise RuntimeError(f"No native OfficeMath was found in source document: {source_docx}")

    with ZipFile(source_docx) as archive:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
    equations: list[str] = []
    for node in document.iter(f"{{{MATH_NS}}}oMath"):
        equations.append(convert_omml(node).strip("$"))
    if not equations:
        raise RuntimeError(f"No source equations could be decoded from: {source_docx}")
    return equations


def _best_source_match(equation: str, source_equations: list[str]) -> tuple[float, str]:
    normalized = _normalize_latex(equation)
    best_score = -1.0
    best_equation = ""
    for source in source_equations:
        candidate = _normalize_latex(source)
        if not normalized or not candidate:
            score = 0.0
        else:
            score = SequenceMatcher(None, normalized, candidate).ratio()
        if score > best_score:
            best_score = score
            best_equation = source
    return best_score, best_equation


def _manifest_math_count(manifest: dict) -> int:
    count = 0
    for slide in manifest.get("slides", []):
        count += sum(looks_like_math(str(line)) for line in slide.get("onscreen", []))
        count += bool(slide.get("equation_latex"))
    return count


def _validate_deck(path: Path, expected_math_count: int) -> dict[str, int]:
    math_count = 0
    raw_latex_count = 0
    with ZipFile(path) as archive:
        slide_names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        for name in slide_names:
            xml = archive.read(name)
            root = etree.fromstring(xml)
            math_count += len(root.findall(f".//{{{DRAWING_2010_NS}}}m"))
            visible_text = "".join(root.itertext())
            raw_latex_count += len(_RAW_LATEX.findall(visible_text))
    if math_count != expected_math_count:
        raise RuntimeError(
            f"{path.name} has {math_count} native math zones; expected {expected_math_count}."
        )
    if raw_latex_count:
        raise RuntimeError(f"{path.name} still contains {raw_latex_count} visible raw-LaTeX tokens.")
    return {"native_math_zones": math_count, "raw_latex_tokens": raw_latex_count}


def _audio_path(audio_dir: Path, slide_number: int) -> Path:
    stem = f"slide_{slide_number:02d}"
    matches = [audio_dir / f"{stem}{suffix}" for suffix in _AUDIO_SUFFIXES]
    matches = [path for path in matches if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one existing narration file for {stem} in {audio_dir}; found {len(matches)}."
        )
    return matches[0]


def _selected_manifests(workspace: Path, videos: list[str] | None) -> list[Path]:
    manifests = sorted((workspace / "manifests").glob("video_*.yaml"))
    if videos:
        wanted = {int(value.upper().lstrip("V")) for value in videos}
        manifests = [path for path in manifests if int(path.stem.split("_")[1]) in wanted]
    if not manifests:
        raise RuntimeError("No matching video manifests were found.")
    return manifests


def regenerate(
    workspace: Path,
    source_docx: Path,
    *,
    videos: list[str] | None = None,
    slides_only: bool = False,
    minimum_source_match: float = 0.45,
) -> dict:
    workspace = workspace.resolve()
    source_docx = source_docx.resolve()
    manifests = _selected_manifests(workspace, videos)
    source_equations = _source_equations(source_docx)
    report: dict = {
        "workspace": str(workspace),
        "source_docx": str(source_docx),
        "source_equation_count": len(source_equations),
        "minimum_source_match": minimum_source_match,
        "videos": [],
    }

    equation_audit: list[dict] = []
    for manifest_path in manifests:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        for slide in manifest.get("slides", []):
            equation = slide.get("equation_latex")
            if not equation:
                continue
            score, source_match = _best_source_match(str(equation), source_equations)
            equation_audit.append(
                {
                    "video_id": manifest.get("video_id"),
                    "slide_id": slide.get("id"),
                    "manifest_latex": str(equation),
                    "source_match": source_match,
                    "score": round(score, 3),
                    "source_block_ids": slide.get("source_block_ids", []),
                }
            )
    weak = [item for item in equation_audit if item["score"] < minimum_source_match]
    report["equation_audit"] = equation_audit
    report["weak_source_matches"] = weak
    if weak:
        identifiers = ", ".join(str(item["slide_id"]) for item in weak)
        raise RuntimeError(
            f"Source-math audit failed for {len(weak)} slides ({identifiers}); no files were replaced."
        )

    for manifest_path in manifests:
        number = int(manifest_path.stem.split("_")[1])
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        final_deck = workspace / "slides" / f"video_{number:02d}.pptx"
        final_video = workspace / "videos" / f"video_{number:02d}.mp4"
        with tempfile.TemporaryDirectory(prefix=f"math-v{number:02d}-", dir=workspace) as raw_temp:
            temp = Path(raw_temp)
            temp_deck = temp / final_deck.name
            build_pptx(manifest_path, temp_deck)
            deck_validation = _validate_deck(temp_deck, _manifest_math_count(manifest))

            video_report = {
                "video_id": manifest.get("video_id", f"V{number:02d}"),
                "deck": str(final_deck),
                **deck_validation,
            }
            if not slides_only:
                images = render_powerpoint(temp_deck, temp / "rendered")
                if len(images) != len(manifest.get("slides", [])):
                    raise RuntimeError(f"Rendered slide count mismatch for {manifest_path.name}.")
                segments: list[Path] = []
                audio_dir = workspace / "audio" / f"video_{number:02d}"
                for slide_number, image in enumerate(images, start=1):
                    segment = temp / "segments" / f"slide_{slide_number:02d}.mp4"
                    _make_segment(image, _audio_path(audio_dir, slide_number), segment)
                    segments.append(segment)
                temp_video = temp / final_video.name
                concat_segments(segments, temp_video)
                final_video.parent.mkdir(parents=True, exist_ok=True)
                os.replace(temp_video, final_video)
                video_report["video"] = str(final_video)

            final_deck.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temp_deck, final_deck)
            report["videos"].append(video_report)
            print(
                f"Rebuilt V{number:02d}: {deck_validation['native_math_zones']} native math zones"
                + (" and MP4" if not slides_only else "")
            )

    report_path = workspace / "qa" / "math_fidelity_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Math fidelity report -> {report_path}")
    return report


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--workspace", required=True, type=Path)
    command.add_argument("--source-docx", required=True, type=Path)
    command.add_argument("--video", action="append", help="Limit repair to V01, V02, etc.; repeatable")
    command.add_argument("--slides-only", action="store_true", help="Regenerate PPTX files without MP4 files")
    command.add_argument("--minimum-source-match", type=float, default=0.45)
    return command


def main() -> int:
    args = parser().parse_args()
    regenerate(
        args.workspace,
        args.source_docx,
        videos=args.video,
        slides_only=args.slides_only,
        minimum_source_match=args.minimum_source_match,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
