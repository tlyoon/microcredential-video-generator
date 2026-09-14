from zipfile import ZipFile

import yaml
from lxml import etree
from pptx import Presentation

from microvid.office_math import DRAWING_2010_NS, MATH_NS, visible_math_to_latex
from microvid.slides import build_pptx


def test_build_pptx(tmp_path):
    manifest = {
        "video_id": "V01",
        "title": "Measurement",
        "slides": [
            {
                "id": "V01S01",
                "slide_type": "hook",
                "title": "Measurement",
                "onscreen": ["Why uncertainty matters"],
                "source_sections": [],
            }
        ],
    }
    source = tmp_path / "manifest.yaml"
    source.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    output = tmp_path / "out.pptx"

    build_pptx(source, output)

    assert output.exists()
    assert len(Presentation(output).slides) == 1


def test_build_pptx_emits_native_office_math(tmp_path):
    manifest = {
        "video_id": "V01",
        "title": "Measurement",
        "slides": [
            {
                "id": "V01S01",
                "slide_type": "equation",
                "title": "Density",
                "onscreen": ["Mass: m = 56.20 ± 0.05 g"],
                "equation_latex": r"\rho = \frac{4m}{\pi D^2 h}",
                "source_sections": ["9.1"],
            }
        ],
    }
    source = tmp_path / "manifest.yaml"
    source.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    output = tmp_path / "math.pptx"

    build_pptx(source, output)

    with ZipFile(output) as archive:
        slide_xml = archive.read("ppt/slides/slide1.xml")
    root = etree.fromstring(slide_xml)
    assert len(root.findall(f".//{{{DRAWING_2010_NS}}}m")) == 2
    assert len(root.findall(f".//{{{MATH_NS}}}oMath")) == 2
    assert "Mass:\u00a0m\u00a0=" in "".join(root.itertext())
    assert b"Equation (LaTeX source)" not in slide_xml
    assert b"\\frac" not in slide_xml


def test_build_pptx_handles_overbar_as_native_office_math(tmp_path):
    manifest = {
        "video_id": "V03",
        "title": "Statistics",
        "slides": [
            {
                "id": "V03S01",
                "slide_type": "equation",
                "title": "Mean",
                "onscreen": [],
                "equation_latex": r"\bar{x} = \frac{1}{N}\sum_{i=1}^{N}x_i",
                "source_sections": ["4.1"],
            }
        ],
    }
    source = tmp_path / "manifest.yaml"
    source.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    output = tmp_path / "bar.pptx"

    build_pptx(source, output)

    with ZipFile(output) as archive:
        slide_xml = archive.read("ppt/slides/slide1.xml")
    root = etree.fromstring(slide_xml)
    assert len(root.findall(f".//{{{DRAWING_2010_NS}}}m")) == 1
    assert len(root.findall(f".//{{{MATH_NS}}}bar")) == 1


def test_visible_math_normalizes_ascii_and_unicode_notation():
    latex = visible_math_to_latex("Mean: D_bar = sqrt(sum(x_i)^2); T²; t₁₀ approx 2")

    assert r"\bar{D}" in latex
    assert r"\sqrt{\sum" in latex
    assert r"\sum" in latex
    assert "T^{2}" in latex
    assert "t_{10}" in latex
    assert r"\approx" in latex
