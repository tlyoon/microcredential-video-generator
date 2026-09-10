from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import yaml


def load_profile(name_or_path: str) -> dict:
    p = Path(name_or_path)
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    package_path = files("microvid").joinpath("profiles", f"{name_or_path}.yaml")
    return yaml.safe_load(package_path.read_text(encoding="utf-8"))
