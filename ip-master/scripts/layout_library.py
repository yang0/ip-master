#!/usr/bin/env python3
"""Maintain and expose the local portrait-poster layout reference library."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LIBRARY_DIR = SKILL_DIR / "assets" / "layout-library"
THUMBNAILS_DIR = LIBRARY_DIR / "thumbnails"
MANIFEST_PATH = LIBRARY_DIR / "manifest.json"
GALLERY_PATH = LIBRARY_DIR / "index.html"
BLUEPRINT_PATH = SKILL_DIR / "references" / "layout-blueprints.json"
UPSTREAM_REPOSITORY = "https://github.com/nevertoday/100-layout-compositions.git"
UPSTREAM_WEB_URL = "https://github.com/nevertoday/100-layout-compositions"
UPSTREAM_BRANCH = "main"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
THUMBNAIL_PATTERN = re.compile(r"^layout-(\d+)\.jpg$", re.IGNORECASE)

BLUEPRINT_FIELDS = ("layout_principle", "translation_rule")
VISUAL_ISOLATION_CONSTRAINT = (
    "仅采用上述构图方法论，不复制示例画面的坐标、配色、几何装饰、字体、文案、"
    "人物、物件、品牌、纹理或任何具体视觉元素；用户主题、角色身份、指定文案和视觉风格优先。"
)


def _layout_records(thumbnails_dir: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in thumbnails_dir.glob("layout-*.jpg"):
        match = THUMBNAIL_PATTERN.fullmatch(path.name)
        if not match:
            continue
        number = int(match.group(1))
        if number < 1:
            continue
        records.append(
            {
                "id": f"layout-{number:03d}",
                "number": f"{number:02d}",
                "thumbnail": f"thumbnails/{path.name}",
            }
        )
    records.sort(key=lambda item: int(item["id"].rsplit("-", 1)[1]))
    return records


def _validate_records(records: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    previous = 0
    for item in records:
        layout_id = item["id"]
        number = int(layout_id.rsplit("-", 1)[1])
        if layout_id in seen:
            errors.append(f"duplicate layout id: {layout_id}")
        seen.add(layout_id)
        if number <= previous:
            errors.append("layout ids are not strictly increasing")
        previous = number
    if not records:
        errors.append("no layout thumbnails found")
    return errors


def _manifest(commit: str, records: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "version": 1,
        "upstream": {
            "repository": UPSTREAM_WEB_URL,
            "git": UPSTREAM_REPOSITORY,
            "branch": UPSTREAM_BRANCH,
            "commit": commit,
            "license": "CC BY 4.0",
            "license_url": LICENSE_URL,
            "asset_kind": "thumbnails only",
        },
        "layouts": records,
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_blueprints(*, skill_dir: Path = SKILL_DIR) -> dict[str, dict[str, str]]:
    """Load text-only spatial blueprints keyed by stable layout id."""

    path = skill_dir / "references" / "layout-blueprints.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read layout blueprints: {exc}") from exc
    entries = data.get("blueprints") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError("layout blueprints must contain a blueprints list")
    blueprints: dict[str, dict[str, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("each layout blueprint needs a string id")
        layout_id = entry["id"]
        if layout_id in blueprints:
            raise ValueError(f"duplicate layout blueprint: {layout_id}")
        values = {field: entry.get(field) for field in BLUEPRINT_FIELDS}
        if not all(isinstance(value, str) and value.strip() for value in values.values()):
            raise ValueError(f"incomplete layout blueprint: {layout_id}")
        blueprints[layout_id] = {field: values[field].strip() for field in BLUEPRINT_FIELDS}
    return blueprints


def _blueprint_instruction(blueprint: dict[str, str]) -> str:
    lines = ["构图方法论（根据当前主题重新落位，不复制示例画面）："]
    lines.append(f"- 构图原则：{blueprint['layout_principle']}")
    lines.append(f"- 主题迁移：{blueprint['translation_rule']}")
    lines.append("- 优先级：用户主题、角色身份、指定文案和视觉风格高于方法论；用户明确位置要求覆盖默认落位。")
    lines.append(f"- 视觉隔离：{VISUAL_ISOLATION_CONSTRAINT}")
    return "\n".join(lines)


def _gallery_html(manifest: dict[str, Any], blueprints: dict[str, dict[str, str]]) -> str:
    layouts = json.dumps(
        [
            {
                **item,
                "principle": blueprints.get(item["id"], {}).get("layout_principle", "待建立方法论"),
            }
            for item in manifest["layouts"]
        ],
        ensure_ascii=False,
    )
    commit = manifest["upstream"]["commit"]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IP Master 竖版海报排版库</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif; }}
    body {{ margin: 0; background: #f5f5f2; color: #151515; }}
    header {{ padding: 40px clamp(20px, 6vw, 96px) 26px; background: #171717; color: #fff; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(28px, 4vw, 48px); }}
    header p {{ max-width: 680px; margin: 0; line-height: 1.7; color: #d7d7d7; }}
    main {{ padding: 28px clamp(20px, 6vw, 96px) 56px; }}
    .hint {{ margin: 0 0 24px; padding: 14px 16px; border-left: 4px solid #f15b45; background: #fff; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 16px; }}
    .card {{ cursor: pointer; overflow: hidden; padding: 0; border: 1px solid #deded8; border-radius: 12px; background: #fff; box-shadow: 0 3px 12px rgba(0,0,0,.05); text-align: left; }}
    .card:hover, .card:focus-visible {{ outline: 3px solid #f15b45; outline-offset: 2px; }}
    .card img {{ display: block; width: 100%; aspect-ratio: 3 / 4; object-fit: cover; background: #e8e8e2; }}
    .number {{ display: block; padding: 10px 12px; font-size: 16px; font-weight: 700; letter-spacing: .08em; }}
    dialog {{ max-width: min(900px, 92vw); padding: 0; border: 0; border-radius: 14px; box-shadow: 0 18px 70px rgba(0,0,0,.35); }}
    dialog::backdrop {{ background: rgba(0,0,0,.62); }}
    .modal {{ padding: 18px; background: #fff; }}
    .modal img {{ display: block; max-width: min(760px, 84vw); max-height: 74vh; margin: 0 auto 14px; }}
    .modal-row {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
    button {{ font: inherit; }}
    .copy {{ border: 0; border-radius: 8px; padding: 10px 14px; background: #171717; color: #fff; cursor: pointer; }}
    .close {{ border: 0; background: transparent; font-size: 22px; cursor: pointer; }}
    footer {{ padding: 22px clamp(20px, 6vw, 96px); border-top: 1px solid #deded8; font-size: 14px; line-height: 1.65; color: #555; }}
    a {{ color: inherit; }}
  </style>
</head>
<body>
  <header>
    <h1>竖版海报排版库</h1>
    <p>点击任意构图查看大图并复制编号；回到对话后说“用 23 重新排版”即可采用对应的构图方法论。首轮海报不会自动套用此库。</p>
  </header>
  <main>
    <p class="hint">共 <strong id="count"></strong> 种构图。编号代表构图方法，不是示例样图坐标；每次都会按你的主题重新落位，不会复制样图的颜色、图形、字体或内容。</p>
    <section class="grid" id="grid" aria-label="排版构图列表"></section>
  </main>
  <dialog id="preview"><div class="modal"><img id="preview-image" alt=""><div class="modal-row"><strong id="preview-number"></strong><span><button class="copy" id="copy">复制编号</button><button class="close" id="close" aria-label="关闭">×</button></span></div></div></dialog>
  <footer>
    排版参考来自 <a href="{UPSTREAM_WEB_URL}">nevertoday/100-layout-compositions</a>，按 <a href="{LICENSE_URL}">CC BY 4.0</a> 使用；本地快照提交：<code>{commit}</code>。页面仅包含缩略图，高清原图仍由上游仓库提供。
  </footer>
  <script>
    const layouts = {layouts};
    const grid = document.querySelector('#grid');
    const dialog = document.querySelector('#preview');
    const image = document.querySelector('#preview-image');
    const label = document.querySelector('#preview-number');
    let selected = null;
    document.querySelector('#count').textContent = layouts.length;
    function openLayout(item) {{
      selected = item;
      image.src = item.thumbnail;
      image.alt = `排版 ${{item.number}}`;
      label.textContent = `编号 ${{item.number}} · ${{item.principle}}`;
      dialog.showModal();
    }}
    for (const item of layouts) {{
      const card = document.createElement('button');
      card.className = 'card';
      card.type = 'button';
      card.innerHTML = `<img loading="lazy" src="${{item.thumbnail}}" alt="排版 ${{item.number}}：${{item.principle}}"><span class="number">${{item.number}} · ${{item.principle}}</span>`;
      card.addEventListener('click', () => openLayout(item));
      grid.append(card);
    }}
    document.querySelector('#close').addEventListener('click', () => dialog.close());
    document.querySelector('#copy').addEventListener('click', async () => {{
      if (!selected) return;
      const text = `用 ${{selected.number}} 重新排版`;
      try {{ await navigator.clipboard.writeText(text); }} catch {{}}
      document.querySelector('#copy').textContent = '已复制';
      setTimeout(() => document.querySelector('#copy').textContent = '复制编号', 1200);
    }});
  </script>
</body>
</html>
"""


def _write_gallery(manifest: dict[str, Any], library_dir: Path, *, skill_dir: Path = SKILL_DIR) -> None:
    (library_dir / "index.html").write_text(
        _gallery_html(manifest, _load_blueprints(skill_dir=skill_dir)), encoding="utf-8"
    )


def validate_library(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    library_dir = skill_dir / "assets" / "layout-library"
    manifest_path = library_dir / "manifest.json"
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "valid": False,
            "asset_valid": False,
            "blueprints_valid": False,
            "errors": [f"cannot read manifest: {exc}"],
            "count": 0,
            "blueprint_count": 0,
        }
    layouts = manifest.get("layouts") if isinstance(manifest, dict) else None
    if not isinstance(layouts, list):
        errors.append("manifest layouts must be a list")
        layouts = []
    records = [item for item in layouts if isinstance(item, dict)]
    errors.extend(_validate_records(records))
    for item in records:
        thumbnail = item.get("thumbnail")
        if not isinstance(thumbnail, str) or not (library_dir / thumbnail).is_file():
            errors.append(f"missing thumbnail: {thumbnail}")
    if not (library_dir / "index.html").is_file():
        errors.append("missing gallery HTML")
    asset_errors = list(errors)
    blueprint_errors: list[str] = []
    try:
        blueprints = _load_blueprints(skill_dir=skill_dir)
    except ValueError as exc:
        blueprint_errors.append(str(exc))
        blueprints = {}
    layout_ids = {item.get("id") for item in records}
    blueprint_ids = set(blueprints)
    missing_blueprints = sorted(layout_ids - blueprint_ids)
    extra_blueprints = sorted(blueprint_ids - layout_ids)
    if missing_blueprints:
        blueprint_errors.append("missing layout blueprints: " + ", ".join(missing_blueprints))
    if extra_blueprints:
        blueprint_errors.append("blueprints without thumbnails: " + ", ".join(extra_blueprints))
    errors.extend(blueprint_errors)
    return {
        "valid": not errors,
        "asset_valid": not asset_errors,
        "blueprints_valid": not blueprint_errors,
        "errors": errors,
        "count": len(records),
        "blueprint_count": len(blueprints),
        "manifest": manifest,
    }


def parse_layout_selection(request: str, *, skill_dir: Path = SKILL_DIR) -> dict[str, Any] | None:
    """Resolve a user-selected layout number into a stable local reference."""

    text = request.casefold()
    patterns = (
        r"layout\s*[-#]?\s*0*(\d{1,4})",
        r"(?:用|选|选择|改用)\s*0*(\d{1,4})\s*(?:号)?\s*(?:布局|排版|构图|重新排版)",
        r"(?:布局|排版|构图)\s*(?:用|选|选择|改用)\s*0*(\d{1,4})",
    )
    match = next((found for pattern in patterns if (found := re.search(pattern, text))), None)
    if match is None:
        return None
    number = int(match.group(1))
    report = validate_library(skill_dir=skill_dir)
    if not report["asset_valid"]:
        raise ValueError("layout library is unavailable: " + "; ".join(report["errors"]))
    layouts = report["manifest"]["layouts"]
    selected = next((item for item in layouts if int(item["id"].rsplit("-", 1)[1]) == number), None)
    if selected is None:
        maximum = max(int(item["id"].rsplit("-", 1)[1]) for item in layouts)
        raise ValueError(f"unknown layout number: {number}; choose 01–{maximum:02d}")
    blueprints = _load_blueprints(skill_dir=skill_dir)
    blueprint = blueprints.get(selected["id"])
    if blueprint is None:
        raise ValueError(f"layout blueprint unavailable: {selected['id']}")
    library_dir = skill_dir / "assets" / "layout-library"
    return {
        "id": selected["id"],
        "number": selected["number"],
        "gallery_path": str((library_dir / "index.html").resolve()),
        "layout_method": blueprint,
        "generation_instruction": _blueprint_instruction(blueprint),
        "visual_isolation_constraint": VISUAL_ISOLATION_CONSTRAINT,
        "prompt_label": f"构图方法 {selected['number']}：{blueprint['layout_principle']}（重新落位，不复制视觉元素）",
    }


def _image_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(32)
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", header[16:24])
        if header[:2] != b"\xff\xd8":
            raise ValueError("unsupported image format; use PNG or JPEG")
        handle.seek(2)
        while True:
            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if not marker:
                break
            code = marker[0]
            length_bytes = handle.read(2)
            if len(length_bytes) != 2:
                break
            length = struct.unpack(">H", length_bytes)[0]
            if 0xC0 <= code <= 0xC3 or 0xC5 <= code <= 0xC7 or 0xC9 <= code <= 0xCB or 0xCD <= code <= 0xCF:
                data = handle.read(5)
                height, width = struct.unpack(">HH", data[1:5])
                return width, height
            handle.seek(length - 2, 1)
    raise ValueError("cannot determine image dimensions")


def portrait_delivery_note(image_path: Path, *, skill_dir: Path = SKILL_DIR, prompt_only: bool = False) -> dict[str, Any]:
    """Return the optional post-image delivery guidance for a portrait output."""

    if prompt_only:
        return {"eligible": False, "reason": "prompt-only output"}
    width, height = _image_dimensions(image_path)
    if height <= width:
        return {"eligible": False, "reason": "not a portrait image", "width": width, "height": height}
    report = validate_library(skill_dir=skill_dir)
    if not report["asset_valid"]:
        return {"eligible": False, "reason": "layout library unavailable", "errors": report["errors"]}
    gallery_path = (skill_dir / "assets" / "layout-library" / "index.html").resolve()
    message = f"不满意可打开排版库：[选择竖版海报排版]({gallery_path})，回复编号（如：23）让我重新排版。"
    return {"eligible": True, "width": width, "height": height, "gallery_path": str(gallery_path), "message": message}


def _source_commit(source_dir: Path) -> str:
    result = subprocess.run(["git", "-C", str(source_dir), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def sync_library(*, source_dir: Path | None = None, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    """Stage a complete upstream snapshot before replacing local thumbnails."""

    temporary_clone: tempfile.TemporaryDirectory[str] | None = None
    if source_dir is None:
        temporary_clone = tempfile.TemporaryDirectory(prefix="ip-master-layouts-")
        source_dir = Path(temporary_clone.name) / "source"
        subprocess.run(["git", "clone", "--depth", "1", "--branch", UPSTREAM_BRANCH, UPSTREAM_REPOSITORY, str(source_dir)], check=True)
    source_dir = source_dir.resolve()
    source_thumbnails = source_dir / "thumbnails"
    records = _layout_records(source_thumbnails)
    errors = _validate_records(records)
    if errors:
        raise ValueError("invalid upstream layout snapshot: " + "; ".join(errors))
    commit = _source_commit(source_dir)
    library_dir = skill_dir / "assets" / "layout-library"
    library_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="layout-stage-", dir=library_dir.parent) as temp:
        staged_dir = Path(temp) / "thumbnails"
        staged_dir.mkdir()
        for record in records:
            filename = Path(record["thumbnail"]).name
            shutil.copy2(source_thumbnails / filename, staged_dir / filename)
        if len(list(staged_dir.glob("layout-*.jpg"))) != len(records):
            raise ValueError("staged thumbnail count mismatch")
        target = library_dir / "thumbnails"
        backup = library_dir / "thumbnails.backup"
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.replace(backup)
        try:
            staged_dir.replace(target)
            manifest = _manifest(commit, records)
            _write_json(library_dir / "manifest.json", manifest)
            _write_gallery(manifest, library_dir, skill_dir=skill_dir)
        except Exception:
            if target.exists():
                shutil.rmtree(target)
            if backup.exists():
                backup.replace(target)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    if temporary_clone is not None:
        temporary_clone.cleanup()
    return {"commit": commit, "count": len(records), "library": str(library_dir)}


def check_upstream(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    report = validate_library(skill_dir=skill_dir)
    if not report["asset_valid"]:
        raise ValueError("layout library is unavailable: " + "; ".join(report["errors"]))
    current = report["manifest"]["upstream"]["commit"]
    result = subprocess.run(["git", "ls-remote", UPSTREAM_REPOSITORY, f"refs/heads/{UPSTREAM_BRANCH}"], capture_output=True, text=True, check=True)
    remote = result.stdout.split()[0]
    return {"current_commit": current, "remote_commit": remote, "update_available": current != remote, "count": report["count"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Maintain the local IP Master layout library")
    parser.add_argument("--check", action="store_true", help="compare the pinned snapshot with upstream main")
    parser.add_argument("--sync", action="store_true", help="download a complete new upstream thumbnail snapshot")
    parser.add_argument("--source-dir", type=Path, help="local upstream checkout for a deterministic sync")
    parser.add_argument("--validate", action="store_true", help="validate the current local library")
    parser.add_argument("--select", help="resolve a user layout selection such as 23 or layout-023")
    parser.add_argument("--delivery-note", type=Path, help="emit the optional note for a final image file")
    parser.add_argument("--prompt-only", action="store_true", help="suppress delivery guidance for prompt-only output")
    parser.add_argument("--skill-dir", type=Path, default=SKILL_DIR)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    selected = sum(bool(value) for value in (args.check, args.sync, args.validate, args.select, args.delivery_note))
    if selected != 1:
        parser.error("choose exactly one action")
    try:
        if args.check:
            payload = check_upstream(skill_dir=args.skill_dir)
        elif args.sync:
            payload = sync_library(source_dir=args.source_dir, skill_dir=args.skill_dir)
        elif args.validate:
            payload = validate_library(skill_dir=args.skill_dir)
        elif args.select:
            payload = parse_layout_selection(args.select, skill_dir=args.skill_dir)
        else:
            payload = portrait_delivery_note(args.delivery_note, skill_dir=args.skill_dir, prompt_only=args.prompt_only)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"layout library error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload)
    return 0 if payload is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
