#!/usr/bin/env python3
"""Maintain and expose the local 350-layout reference library."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LIBRARY_DIR = SKILL_DIR / "assets" / "layout-library"
TRANSLATION_RULES_PATH = SKILL_DIR / "references" / "layout-translation-rules.json"
IMAGE_BINDINGS_PATH = LIBRARY_DIR / "image-bindings.json"
UPSTREAM_REPOSITORY = "https://github.com/nevertoday/350-layout-compositions.git"
UPSTREAM_WEB_URL = "https://github.com/nevertoday/350-layout-compositions"
UPSTREAM_BRANCH = "main"
CATALOG_RELATIVE_PATH = PurePosixPath("v2/catalog.json")
RAW_CONTENT_ROOT = "https://raw.githubusercontent.com/nevertoday/350-layout-compositions"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
EXPECTED_COUNT = 350
EXPECTED_SUBCATEGORY_COUNT = 33
EXPECTED_CATEGORY_COUNTS = {
    "构图逻辑": 86,
    "视觉原则与阅读模式": 45,
    "平面、出版与广告": 36,
    "字体、网格与东亚文字": 54,
    "网页与 UI": 79,
    "影视画面构图": 14,
    "中国传统构图": 20,
    "演示文稿页面": 16,
}
RECORD_FIELDS = (
    "id", "number", "name", "category", "category_slug", "subcategory",
    "subcategory_slug", "source_number", "recognized_catalog_number",
    "recognition_status", "visual_category", "visual_subcategory", "visual_subcategory_slug",
    "local_image", "image_sha256", "source_thumbnail", "source_image",
)
VISUAL_ISOLATION_CONSTRAINT = (
    "仅采用上述布局方法论，不复制示例画面的坐标、配色、几何装饰、字体、文案、"
    "人物、物件、品牌、纹理或任何具体视觉元素；用户主题、角色身份、指定文案和视觉风格优先。"
)


def _safe_relative_path(value: Any, *, prefix: tuple[str, ...], suffix: str) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("catalog asset path must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.parts[: len(prefix)] != prefix or path.suffix.lower() != suffix:
        raise ValueError(f"invalid catalog asset path: {value}")
    return path


def _catalog_records(source_dir: Path) -> list[dict[str, str]]:
    catalog_path = source_dir / Path(CATALOG_RELATIVE_PATH)
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read upstream catalog: {exc}") from exc
    if not isinstance(catalog, list):
        raise ValueError("upstream catalog must be a list")
    records: list[dict[str, str]] = []
    for item in catalog:
        if not isinstance(item, dict):
            raise ValueError("each catalog entry must be an object")
        required = ("id", "name", "category", "category_slug", "subcategory", "subcategory_slug")
        if not all(isinstance(item.get(field), str) and item[field].strip() for field in required):
            raise ValueError("catalog entry is missing text metadata")
        try:
            number = int(item["id"])
        except ValueError as exc:
            raise ValueError(f"invalid catalog id: {item['id']}") from exc
        source_thumbnail = _safe_relative_path(item.get("thumbnail"), prefix=("v2", "thumbnails"), suffix=".jpg")
        source_image = _safe_relative_path(item.get("image"), prefix=("v2", "images"), suffix=".png")
        records.append({
            "id": f"layout-{number:03d}", "number": f"{number:03d}", "name": item["name"].strip(),
            "category": item["category"].strip(), "category_slug": item["category_slug"].strip(),
            "subcategory": item["subcategory"].strip(), "subcategory_slug": item["subcategory_slug"].strip(),
            "source_thumbnail": source_thumbnail.as_posix(),
            "source_image": source_image.as_posix(),
        })
    records.sort(key=lambda item: int(item["number"]))
    return records


def _validate_records(records: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if len(records) != EXPECTED_COUNT:
        errors.append(f"expected {EXPECTED_COUNT} layout records, got {len(records)}")
    expected_numbers = list(range(1, len(records) + 1))
    actual_numbers: list[int] = []
    ids: set[str] = set()
    for item in records:
        missing = [field for field in RECORD_FIELDS if not isinstance(item.get(field), str) or not item[field].strip()]
        if missing:
            errors.append("layout record has missing fields: " + ", ".join(missing))
            continue
        try:
            number = int(item["number"])
        except ValueError:
            errors.append(f"invalid layout number: {item['number']}")
            continue
        actual_numbers.append(number)
        if item["id"] != f"layout-{number:03d}" or item["number"] != f"{number:03d}":
            errors.append(f"inconsistent layout identifier: {item['id']}")
        if item["id"] in ids:
            errors.append(f"duplicate layout id: {item['id']}")
        ids.add(item["id"])
        try:
            _safe_relative_path(item["source_thumbnail"], prefix=("v2", "thumbnails"), suffix=".jpg")
            _safe_relative_path(item["source_image"], prefix=("v2", "images"), suffix=".png")
        except ValueError as exc:
            errors.append(str(exc))
    if actual_numbers != expected_numbers:
        errors.append("layout numbers must be contiguous from 001")
    if dict(Counter(item.get("category") for item in records)) != EXPECTED_CATEGORY_COUNTS:
        errors.append("unexpected primary category counts")
    if len({item.get("subcategory_slug") for item in records}) != EXPECTED_SUBCATEGORY_COUNT:
        errors.append(f"expected {EXPECTED_SUBCATEGORY_COUNT} subcategories")
    return errors


def _load_image_bindings(*, library_dir: Path = LIBRARY_DIR) -> dict[str, Any]:
    try:
        data = json.loads((library_dir / "image-bindings.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read image bindings: {exc}") from exc
    bindings = data.get("bindings") if isinstance(data, dict) else None
    if not isinstance(bindings, list) or len(bindings) != EXPECTED_COUNT:
        raise ValueError(f"image bindings must contain {EXPECTED_COUNT} entries")
    numbers = [item.get("number") for item in bindings if isinstance(item, dict)]
    if numbers != [f"{i:03d}" for i in range(1, EXPECTED_COUNT + 1)]:
        raise ValueError("image binding numbers must be contiguous from 001")
    if len({item.get("source_number") for item in bindings}) != EXPECTED_COUNT:
        raise ValueError("image bindings contain duplicate source images")
    if len({item.get("local_image") for item in bindings}) != EXPECTED_COUNT:
        raise ValueError("image bindings contain duplicate local images")
    for item in bindings:
        if not isinstance(item, dict) or not all(isinstance(item.get(field), str) and item[field].strip() for field in ("number", "source_number", "recognized_catalog_number", "recognized_title", "recognition_status", "local_image", "sha256")):
            raise ValueError("image binding has missing recognition metadata")
        _safe_relative_path(item["local_image"], prefix=("images",), suffix=".jpg")
    return data


def _manifest(commit: str, records: list[dict[str, str]], bindings: dict[str, Any]) -> dict[str, Any]:
    by_number = {item["number"]: item for item in records}
    layouts: list[dict[str, str]] = []
    for binding in bindings["bindings"]:
        source = by_number[binding["source_number"]]
        recognized = by_number[binding["recognized_catalog_number"]]
        layouts.append({
            "id": f"layout-{binding['number']}", "number": binding["number"], "name": binding["recognized_title"],
            "category": source["category"], "category_slug": source["category_slug"],
            "subcategory": source["subcategory"], "subcategory_slug": source["subcategory_slug"],
            "source_number": source["number"], "recognized_catalog_number": recognized["number"],
            "recognition_status": binding["recognition_status"], "local_image": binding["local_image"],
            "visual_category": recognized["category"], "visual_subcategory": recognized["subcategory"], "visual_subcategory_slug": recognized["subcategory_slug"],
            "image_sha256": binding["sha256"], "source_thumbnail": source["source_thumbnail"], "source_image": source["source_image"],
        })
    return {
        "version": 3,
        "upstream": {"repository": UPSTREAM_WEB_URL, "git": UPSTREAM_REPOSITORY, "branch": UPSTREAM_BRANCH, "commit": commit, "license": "CC BY 4.0", "license_url": LICENSE_URL, "asset_kind": "locally cloned thumbnail snapshot; source paths retained"},
        "catalog": {"path": CATALOG_RELATIVE_PATH.as_posix(), "layout_count": EXPECTED_COUNT, "category_count": len(EXPECTED_CATEGORY_COUNTS), "subcategory_count": EXPECTED_SUBCATEGORY_COUNT},
        "image_bindings": {"path": "image-bindings.json", "basis": bindings.get("basis", "visual title audit")},
        "layouts": layouts,
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_translation_rules(*, skill_dir: Path = SKILL_DIR) -> dict[str, str]:
    try:
        data = json.loads((skill_dir / "references" / "layout-translation-rules.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read layout translation rules: {exc}") from exc
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, dict):
        raise ValueError("layout translation rules must contain a rules object")
    normalized: dict[str, str] = {}
    for slug, rule in rules.items():
        if not isinstance(slug, str) or not slug.strip() or not isinstance(rule, str) or not rule.strip():
            raise ValueError("each layout translation rule needs a slug and non-empty text")
        normalized[slug.strip()] = rule.strip()
    return normalized


def _layout_methods(records: list[dict[str, str]], rules: dict[str, str]) -> dict[str, dict[str, str]]:
    record_slugs = {record.get("visual_subcategory_slug", record["subcategory_slug"]) for record in records}
    missing = sorted(record_slugs - set(rules))
    extra = sorted(set(rules) - record_slugs)
    if missing:
        raise ValueError("missing layout translation rules: " + ", ".join(missing))
    return {
        record["id"]: {
            "layout_principle": record["name"],
            "category": record.get("visual_category", record["category"]),
            "subcategory": record.get("visual_subcategory", record["subcategory"]),
            "translation_rule": rules[record.get("visual_subcategory_slug", record["subcategory_slug"])],
            "visual_features": (
                f"主体位置：围绕“{record['name']}”的核心关系安排主体与信息模块；"
                "视觉动线：先建立主焦点，再用方向、尺度或重复关系引导阅读；"
                "空间组织：保留清晰的前后层级与可呼吸留白；"
                "迁移边界：只迁移结构逻辑，不复制示例图的对象、文案、颜色或具体坐标。"
            ),
        }
        for record in records
    }


def _blueprint_instruction(blueprint: dict[str, str]) -> str:
    return "\n".join((
        "布局方法论（根据当前主题重新落位，不复制示例画面）：",
        f"- 布局名称：{blueprint['layout_principle']}（{blueprint['category']} / {blueprint['subcategory']}）",
        f"- 主题迁移：{blueprint['translation_rule']}",
        f"- 构图细化：{blueprint['visual_features']}",
        "- 优先级：用户主题、角色身份、指定文案和视觉风格高于方法论；用户明确位置要求覆盖默认落位。",
        f"- 视觉隔离：{VISUAL_ISOLATION_CONSTRAINT}",
    ))


def _source_image_url(item: dict[str, str], commit: str) -> str:
    return f"{RAW_CONTENT_ROOT}/{commit}/{quote(item['source_image'], safe='/')}"


def _gallery_html(manifest: dict[str, Any], methods: dict[str, dict[str, str]]) -> str:
    commit = manifest["upstream"]["commit"]
    layouts = [{**item, "translation_rule": methods[item["id"]]["translation_rule"], "visual_features": methods[item["id"]]["visual_features"], "image_url": item["local_image"], "source_image_url": _source_image_url(item, commit)} for item in manifest["layouts"]]
    serialized_layouts = json.dumps(layouts, ensure_ascii=False).replace("</", "<\\/")
    serialized_categories = json.dumps(list(EXPECTED_CATEGORY_COUNTS), ensure_ascii=False)
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="IP Master 350 种视觉布局库">
  <title>IP Master · 350 种视觉布局库</title>
  <style>
    :root { color-scheme: dark; --bg:#101214; --surface:#171a1e; --surface-2:#1d2228; --text:#f2f4f6; --muted:#a8afb8; --line:#2b3138; --accent:#90d76b; }
    * { box-sizing:border-box; } html { scroll-behavior:smooth; } body { margin:0; background:var(--bg); color:var(--text); font:15px/1.55 Inter,"PingFang SC","Microsoft YaHei",sans-serif; } a { color:inherit; }
    .topbar { position:sticky; top:0; z-index:10; min-height:54px; display:flex; align-items:center; padding:0 max(20px,calc((100vw - 1240px)/2)); background:rgba(16,18,20,.96); border-bottom:1px solid var(--line); } .home { color:var(--muted); text-decoration:none; font-size:13px; } .home:hover { color:var(--accent); }
    header, main, footer { width:min(1240px,calc(100% - 40px)); margin:auto; } header { padding:30px 0 24px; border-bottom:1px solid var(--line); } h1 { margin:0 0 7px; font-size:28px; letter-spacing:-.03em; } header p { max-width:760px; margin:0; color:var(--muted); }
    main { padding:22px 0 44px; } .tools { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; align-items:center; margin-bottom:14px; } input { width:100%; min-height:40px; padding:9px 12px; border:1px solid var(--line); border-radius:5px; background:var(--surface); color:var(--text); font:inherit; } input:focus { outline:2px solid var(--accent); outline-offset:1px; } #count { color:var(--muted); font-size:13px; white-space:nowrap; }
    .filters { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; } .filter { min-height:32px; padding:5px 10px; border:1px solid var(--line); border-radius:999px; background:transparent; color:var(--muted); font:13px inherit; cursor:pointer; } .filter:hover,.filter[aria-pressed="true"] { border-color:var(--accent); color:var(--text); background:#1c291a; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(154px,1fr)); gap:14px; } .card { min-width:0; overflow:hidden; padding:0; border:1px solid var(--line); background:var(--surface); color:var(--text); text-align:left; cursor:pointer; } .card:hover,.card:focus-visible { outline:2px solid var(--accent); outline-offset:2px; } .card img { display:block; width:100%; aspect-ratio:3/4; object-fit:contain; background:#242a30; } .card-copy { display:block; padding:9px 10px 11px; } .number { display:block; color:var(--accent); font-size:12px; font-weight:700; } .name { display:block; margin-top:2px; font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .empty { grid-column:1/-1; padding:28px 0; color:var(--muted); text-align:center; } dialog { width:min(940px,94vw); max-height:92vh; padding:0; border:1px solid var(--line); background:var(--surface); color:var(--text); } dialog::backdrop { background:rgba(0,0,0,.7); } .modal { display:grid; grid-template-columns:minmax(0,1fr) minmax(240px,.45fr); gap:18px; padding:18px; } .modal img { display:block; width:100%; max-height:72vh; object-fit:contain; background:#242a30; } .modal-info { min-width:0; } .eyebrow { margin:0 0 6px; color:var(--accent); font-size:12px; font-weight:700; } .modal h2 { margin:0 0 8px; font-size:21px; } .meta,.rule { margin:0 0 14px; color:var(--muted); font-size:13px; } .rule { padding-top:12px; border-top:1px solid var(--line); } .actions { display:flex; flex-wrap:wrap; gap:8px; } .action { display:inline-flex; align-items:center; min-height:35px; padding:7px 10px; border:1px solid #3d4852; background:var(--surface-2); color:var(--text); text-decoration:none; font:13px inherit; cursor:pointer; } .action:hover { border-color:var(--accent); color:var(--accent); } .close { margin-left:auto; }
    footer { padding:20px 0 34px; border-top:1px solid var(--line); color:var(--muted); font-size:13px; } footer a { color:var(--text); } @media (max-width:680px) { header,main,footer { width:min(100% - 28px,1240px); } header { padding-top:22px; } h1 { font-size:24px; } .tools { grid-template-columns:1fr; } .modal { grid-template-columns:1fr; } .modal img { max-height:52vh; } } @media (prefers-reduced-motion:reduce) { html { scroll-behavior:auto; } }
  </style>
</head>
<body>
  <div class="topbar"><a class="home" href="../readme/index.html">← 返回首页</a></div>
  <header><h1>350 种视觉布局库</h1><p>覆盖构图逻辑、视觉原则、出版广告、字体网格、网页 UI、影视、中国传统与演示文稿。选择编号后，系统只迁移布局方法，会按你的主题重新组织内容，不复制示例画面。</p></header>
  <main><div class="tools"><input id="search" type="search" placeholder="搜索编号、布局名称、分类或主题" aria-label="搜索布局"><span id="count" aria-live="polite"></span></div><div class="filters" id="filters" aria-label="布局分类"></div><section class="grid" id="grid" aria-label="350 种布局列表"></section></main>
  <dialog id="preview"><div class="modal"><img id="preview-image" alt=""><div class="modal-info"><p class="eyebrow" id="preview-number"></p><h2 id="preview-name"></h2><p class="meta" id="preview-meta"></p><p class="rule" id="preview-rule"></p><div class="actions"><button class="action" id="copy" type="button">复制重排指令</button><a class="action" id="source" target="_blank" rel="noopener">打开高清原图 ↗</a><button class="action close" id="close" type="button">关闭</button></div></div></div></dialog>
  <footer>排版参考来自 <a href="__UPSTREAM_URL__" target="_blank" rel="noopener">nevertoday/350-layout-compositions</a>，按 <a href="__LICENSE_URL__" target="_blank" rel="noopener">CC BY 4.0</a> 使用；固定提交：<code>__COMMIT__</code>。页面图片是按图内标题核验后的本地快照，高清原图仍可打开上游来源。</footer>
  <script>
    const layouts = __LAYOUTS__;
    const categories = __CATEGORIES__;
    const grid = document.querySelector('#grid'); const filters = document.querySelector('#filters'); const search = document.querySelector('#search'); const count = document.querySelector('#count'); const dialog = document.querySelector('#preview'); const state = { category: '', query: '', selected: null };
    function button(label, category) { const item = document.createElement('button'); item.className = 'filter'; item.type = 'button'; item.textContent = label; item.dataset.category = category; item.setAttribute('aria-pressed', String(state.category === category)); item.addEventListener('click', () => { state.category = category; render(); }); return item; }
    function visibleLayouts() { const query = state.query.trim().toLocaleLowerCase(); return layouts.filter((item) => (!state.category || item.category === state.category) && (!query || [item.number,item.name,item.category,item.subcategory].join(' ').toLocaleLowerCase().includes(query))); }
    function openLayout(item) { state.selected = item; document.querySelector('#preview-image').src = item.image_url; document.querySelector('#preview-image').alt = `布局 ${item.number}：${item.name}`; document.querySelector('#preview-number').textContent = `编号 ${item.number} · 原始图片 ${item.source_number}`; document.querySelector('#preview-name').textContent = item.name; document.querySelector('#preview-meta').textContent = `${item.visual_category} · ${item.visual_subcategory}`; document.querySelector('#preview-rule').textContent = `主题迁移：${item.translation_rule}\n构图细化：${item.visual_features}`; document.querySelector('#source').href = item.source_image_url; document.querySelector('#copy').textContent = '复制重排指令'; dialog.showModal(); }
    function render() { filters.replaceChildren(button(`全部 ${layouts.length}`, '')); for (const category of categories) filters.append(button(`${category} ${layouts.filter((item) => item.category === category).length}`, category)); const visible = visibleLayouts(); count.textContent = `${visible.length} / ${layouts.length} 种布局`; grid.replaceChildren(); if (!visible.length) { const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = '没有匹配的布局，请换一个关键词。'; grid.append(empty); return; } for (const item of visible) { const card = document.createElement('button'); card.className = 'card'; card.type = 'button'; const image = document.createElement('img'); image.loading = 'lazy'; image.src = item.image_url; image.alt = `布局 ${item.number}：${item.name}`; const copy = document.createElement('span'); copy.className = 'card-copy'; const number = document.createElement('span'); number.className = 'number'; number.textContent = item.number; const name = document.createElement('span'); name.textContent = item.name; copy.append(number, name); card.append(image, copy); card.addEventListener('click', () => openLayout(item)); grid.append(card); } }
    search.addEventListener('input', () => { state.query = search.value; render(); }); document.querySelector('#close').addEventListener('click', () => dialog.close()); dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); }); document.querySelector('#copy').addEventListener('click', async () => { if (!state.selected) return; try { await navigator.clipboard.writeText(`用 ${state.selected.number} 重新排版`); } catch {} document.querySelector('#copy').textContent = '已复制'; setTimeout(() => { document.querySelector('#copy').textContent = '复制重排指令'; }, 1200); }); render();
  </script>
</body>
</html>
""".replace("__LAYOUTS__", serialized_layouts).replace("__CATEGORIES__", serialized_categories).replace("__UPSTREAM_URL__", UPSTREAM_WEB_URL).replace("__LICENSE_URL__", LICENSE_URL).replace("__COMMIT__", commit)


def _write_gallery(manifest: dict[str, Any], library_dir: Path, methods: dict[str, dict[str, str]]) -> None:
    (library_dir / "index.html").write_text(_gallery_html(manifest, methods), encoding="utf-8")


def validate_library(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    library_dir = skill_dir / "assets" / "layout-library"
    errors: list[str] = []
    try:
        manifest = json.loads((library_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "asset_valid": False, "blueprints_valid": False, "errors": [f"cannot read manifest: {exc}"], "count": 0, "blueprint_count": 0, "translation_rule_count": 0}
    layouts = manifest.get("layouts") if isinstance(manifest, dict) else None
    if not isinstance(layouts, list):
        errors.append("manifest layouts must be a list")
        layouts = []
    records = [item for item in layouts if isinstance(item, dict)]
    errors.extend(_validate_records(records))
    upstream = manifest.get("upstream") if isinstance(manifest, dict) else None
    if not isinstance(upstream, dict) or upstream.get("repository") != UPSTREAM_WEB_URL:
        errors.append("manifest does not reference the 350-layout upstream")
    try:
        bindings = _load_image_bindings(library_dir=library_dir)
        if bindings.get("upstream_commit") != upstream.get("commit"):
            errors.append("image bindings do not match manifest upstream commit")
    except ValueError as exc:
        errors.append(str(exc))
    images_dir = library_dir / "images"
    if not images_dir.is_dir():
        errors.append("missing local layout images directory")
    else:
        image_paths = sorted(images_dir.glob("*.jpg"))
        if len(image_paths) != EXPECTED_COUNT:
            errors.append(f"expected {EXPECTED_COUNT} local layout images, got {len(image_paths)}")
        for item in records:
            image_path = library_dir / item.get("local_image", "")
            if not image_path.is_file():
                errors.append(f"missing local layout image: {item.get('local_image')}")
            elif item.get("image_sha256"):
                import hashlib
                if hashlib.sha256(image_path.read_bytes()).hexdigest() != item["image_sha256"]:
                    errors.append(f"local image hash mismatch: {item['number']}")
    if not (library_dir / "index.html").is_file():
        errors.append("missing gallery HTML")
    asset_errors = list(errors)
    blueprint_errors: list[str] = []
    try:
        rules = _load_translation_rules(skill_dir=skill_dir)
        methods = _layout_methods(records, rules)
    except ValueError as exc:
        blueprint_errors.append(str(exc))
        rules, methods = {}, {}
    errors.extend(blueprint_errors)
    return {"valid": not errors, "asset_valid": not asset_errors, "blueprints_valid": not blueprint_errors, "errors": errors, "count": len(records), "blueprint_count": len(methods), "translation_rule_count": len(rules), "category_count": len({item.get('category') for item in records}), "subcategory_count": len({item.get('subcategory_slug') for item in records}), "manifest": manifest}


def parse_layout_selection(request: str, *, skill_dir: Path = SKILL_DIR) -> dict[str, Any] | None:
    """Resolve an explicit new-library layout number into a text-only method."""
    text = request.casefold()
    patterns = (
        r"layout\s*[-#]?\s*0*(\d{1,4})",
        r"(?:用|选|选择|改用)\s*0*(\d{1,4})\s*(?:号)?\s*(?:布局|排版|构图|重新排版)",
        r"(?:布局|排版|构图)\s*(?:用|选|选择|改用)\s*0*(\d{1,4})",
        r"(?:用|选|选择|改用)\s*0*(\d{1,4})\s*(?:号)?\s*(?:做|制作)\s*(?:ppt|幻灯片|演示文稿|slide\s*deck)",
    )
    match = next((found for pattern in patterns if (found := re.search(pattern, text))), None)
    if match is None:
        return None
    number = int(match.group(1))
    report = validate_library(skill_dir=skill_dir)
    if not report["asset_valid"]:
        raise ValueError("layout library is unavailable: " + "; ".join(report["errors"]))
    layouts = report["manifest"]["layouts"]
    selected = next((item for item in layouts if int(item["number"]) == number), None)
    if selected is None:
        raise ValueError(f"unknown layout number: {number}; choose 001–{EXPECTED_COUNT}")
    blueprint = _layout_methods(layouts, _load_translation_rules(skill_dir=skill_dir))[selected["id"]]
    library_dir = skill_dir / "assets" / "layout-library"
    return {"id": selected["id"], "number": selected["number"], "name": selected["name"], "category": selected["category"], "subcategory": selected["subcategory"], "gallery_path": str((library_dir / "index.html").resolve()), "layout_method": blueprint, "generation_instruction": _blueprint_instruction(blueprint), "visual_isolation_constraint": VISUAL_ISOLATION_CONSTRAINT, "prompt_label": f"布局 {selected['number']}：{selected['name']}（重新落位，不复制视觉元素）"}


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
            while marker == b"\xff": marker = handle.read(1)
            if not marker: break
            code = marker[0]; length_bytes = handle.read(2)
            if len(length_bytes) != 2: break
            length = struct.unpack(">H", length_bytes)[0]
            if 0xC0 <= code <= 0xC3 or 0xC5 <= code <= 0xC7 or 0xC9 <= code <= 0xCB or 0xCD <= code <= 0xCF:
                data = handle.read(5); height, width = struct.unpack(">HH", data[1:5]); return width, height
            handle.seek(length - 2, 1)
    raise ValueError("cannot determine image dimensions")


def portrait_delivery_note(image_path: Path, *, skill_dir: Path = SKILL_DIR, prompt_only: bool = False) -> dict[str, Any]:
    if prompt_only: return {"eligible": False, "reason": "prompt-only output"}
    width, height = _image_dimensions(image_path)
    if height <= width: return {"eligible": False, "reason": "not a portrait image", "width": width, "height": height}
    report = validate_library(skill_dir=skill_dir)
    if not report["asset_valid"]: return {"eligible": False, "reason": "layout library unavailable", "errors": report["errors"]}
    gallery_path = (skill_dir / "assets" / "layout-library" / "index.html").resolve()
    message = f"不满意可打开排版库：[选择 350 种视觉布局]({gallery_path})，回复编号（如：008）让我重新排版。"
    return {"eligible": True, "width": width, "height": height, "gallery_path": str(gallery_path), "message": message}


def _source_commit(source_dir: Path) -> str:
    return subprocess.run(["git", "-C", str(source_dir), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def sync_library(*, source_dir: Path | None = None, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    temporary_clone: tempfile.TemporaryDirectory[str] | None = None
    if source_dir is None:
        temporary_clone = tempfile.TemporaryDirectory(prefix="ip-master-layouts-")
        source_dir = Path(temporary_clone.name) / "source"
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", UPSTREAM_BRANCH, UPSTREAM_REPOSITORY, str(source_dir)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(source_dir), "sparse-checkout", "set", "--skip-checks", CATALOG_RELATIVE_PATH.as_posix(), "v2/thumbnails"],
            check=True,
        )
    source_dir = source_dir.resolve(); records = _catalog_records(source_dir); errors = _validate_records(records)
    if errors: raise ValueError("invalid upstream layout snapshot: " + "; ".join(errors))
    bindings = _load_image_bindings(library_dir=skill_dir / "assets" / "layout-library")
    commit = _source_commit(source_dir)
    if bindings.get("upstream_commit") != commit:
        raise ValueError("upstream commit changed; review image bindings before syncing")
    methods = _layout_methods(records, _load_translation_rules(skill_dir=skill_dir)); library_dir = skill_dir / "assets" / "layout-library"; library_dir.mkdir(parents=True, exist_ok=True)
    manifest = _manifest(commit, records, bindings)
    _write_json(library_dir / "manifest.json", manifest)
    _write_gallery(manifest, library_dir, methods)
    thumbnail_dir = library_dir / "thumbnails"
    if thumbnail_dir.exists():
        shutil.rmtree(thumbnail_dir)
    images_dir = library_dir / "images"
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True)
    by_source = {item["number"]: item for item in records}
    for binding in bindings["bindings"]:
        source_path = source_dir / Path(by_source[binding["source_number"]]["source_thumbnail"])
        if not source_path.is_file():
            raise ValueError(f"missing upstream thumbnail: {source_path}")
        shutil.copy2(source_path, library_dir / Path(binding["local_image"]))
    if temporary_clone is not None: temporary_clone.cleanup()
    return {"commit": commit, "count": len(records), "library": str(library_dir)}


def check_upstream(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    report = validate_library(skill_dir=skill_dir)
    if not report["asset_valid"]: raise ValueError("layout library is unavailable: " + "; ".join(report["errors"]))
    current = report["manifest"]["upstream"]["commit"]
    result = subprocess.run(["git", "ls-remote", UPSTREAM_REPOSITORY, f"refs/heads/{UPSTREAM_BRANCH}"], capture_output=True, text=True, check=True)
    return {"current_commit": current, "remote_commit": result.stdout.split()[0], "update_available": current != result.stdout.split()[0], "count": report["count"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Maintain the local IP Master 350-layout library")
    parser.add_argument("--check", action="store_true", help="compare the pinned snapshot with upstream main"); parser.add_argument("--sync", action="store_true", help="refresh the pinned catalog and local verified image snapshot"); parser.add_argument("--source-dir", type=Path, help="local upstream checkout for a deterministic sync"); parser.add_argument("--validate", action="store_true", help="validate the current local library"); parser.add_argument("--select", help="resolve a user layout selection such as 008 or layout-008"); parser.add_argument("--delivery-note", type=Path, help="emit the optional note for a final image file"); parser.add_argument("--prompt-only", action="store_true", help="suppress delivery guidance for prompt-only output"); parser.add_argument("--skill-dir", type=Path, default=SKILL_DIR); parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv); selected = sum(bool(value) for value in (args.check, args.sync, args.validate, args.select, args.delivery_note))
    if selected != 1: parser.error("choose exactly one action")
    try:
        if args.check: payload = check_upstream(skill_dir=args.skill_dir)
        elif args.sync: payload = sync_library(source_dir=args.source_dir, skill_dir=args.skill_dir)
        elif args.validate: payload = validate_library(skill_dir=args.skill_dir)
        elif args.select: payload = parse_layout_selection(args.select, skill_dir=args.skill_dir)
        else: payload = portrait_delivery_note(args.delivery_note, skill_dir=args.skill_dir, prompt_only=args.prompt_only)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"layout library error: {exc}", file=sys.stderr); return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.as_json else payload)
    return 0 if payload is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
