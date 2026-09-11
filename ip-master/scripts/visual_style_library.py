#!/usr/bin/env python3
"""Resolve numbered Punk visual-library selections."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
MANIFEST_PATH = SKILL_DIR / "references" / "visual-style-library.json"
_CODE_PATTERN = re.compile(r"(?<![A-Z0-9])(PC|PA)\s*[-_]?\s*(\d{1,2})(?!\d)", re.IGNORECASE)


def load_manifest(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    return json.loads((skill_dir / "references" / "visual-style-library.json").read_text(encoding="utf-8"))


def parse_visual_style_selection(request: str, *, skill_dir: Path = SKILL_DIR) -> dict[str, Any] | None:
    matches = {(prefix.upper(), int(number)) for prefix, number in _CODE_PATTERN.findall(request)}
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("一次只能选择一个 PC 或 PA 风格编号")
    prefix, number = matches.pop()
    code = f"{prefix}{number:02d}"
    manifest = load_manifest(skill_dir=skill_dir)
    library_key = {"PC": "punk-cover", "PA": "punk-avatar"}[prefix]
    library = manifest["libraries"][library_key]
    item = next((entry for entry in library["items"] if entry["code"] == code), None)
    if item is None:
        raise ValueError(f"unknown visual style code: {code}")
    return {"library": library_key, "code": code, "item": item, "repo": library["repo"], "ref": library["ref"]}
