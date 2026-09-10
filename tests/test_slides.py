from pathlib import Path
import yaml
from pptx import Presentation
from microvid.slides import build_pptx


def test_build_pptx(tmp_path):
    manifest = {
      "video_id":"V01", "title":"Measurement", "slides":[
        {"id":"V01S01", "slide_type":"hook", "title":"Measurement", "onscreen":["Why uncertainty matters"], "source_sections":[]}
      ]
    }
    m = tmp_path / "m.yaml"
    m.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    out = tmp_path / "out.pptx"
    build_pptx(m, out)
    assert out.exists()
    assert len(Presentation(out).slides) == 1
