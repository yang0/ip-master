#!/usr/bin/env python3
"""Maintain the source-linked GPT-Image 2 example-case gallery."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LIBRARY_DIR = SKILL_DIR / "assets" / "gpt-image-2-case-library"
MANIFEST_PATH = LIBRARY_DIR / "manifest.json"
GALLERY_PATH = LIBRARY_DIR / "index.html"
UPSTREAM_REPOSITORY = "https://github.com/freestylefly/awesome-gpt-image-2"
UPSTREAM_GIT = f"{UPSTREAM_REPOSITORY}.git"
UPSTREAM_BRANCH = "main"
LICENSE_URL = f"{UPSTREAM_REPOSITORY}/blob/main/LICENSE"
EXPECTED_CASE_COUNT = 544
EXPECTED_CATEGORY_COUNT = 13
KNOWN_SOURCE_OMISSIONS = frozenset({12, 169, 170})
DEFAULT_CATEGORY = "🧪 其他应用场景"
CASE_HEADING = re.compile(r"^###\s+例\s*(\d+)：\s*(.+?)\s*$", re.MULTILINE)
IMAGE = re.compile(r"\]\(\.\./data/images/([^)]*case(\d+)\.[^)]+)\)")
CATEGORY_HEADING = re.compile(r"^###\s+.+?\s·\s(\d+)\s+cases\s*$", re.MULTILINE)
CASE_LINK = re.compile(r"例\s*(\d+)：([^]]+)")
PROMPT_BLOCK = re.compile(r"\*\*(?:提示词|Prompt)：?\*\*\s*```[^\n]*\n(.*?)\n```", re.IGNORECASE | re.DOTALL)
SELECTION_PATTERNS = (
    r"(?:案例|case)\s*[-#]?\s*0*(\d{1,4})",
    r"(?:用|选|选择|改用)\s*0*(\d{1,4})\s*(?:号)?\s*案例",
)


def _fetch_text(url: str) -> str:
    try:
        with urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")
    except (OSError, URLError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot fetch upstream source: {url}: {exc}") from exc


def _remote_commit() -> str:
    result = subprocess.run(
        ["git", "ls-remote", UPSTREAM_GIT, f"refs/heads/{UPSTREAM_BRANCH}"],
        capture_output=True,
        text=True,
        check=True,
    )
    fields = result.stdout.split()
    if not fields:
        raise ValueError("cannot resolve upstream main commit")
    return fields[0]


def _category_name(heading: str) -> str:
    heading = re.sub(r"^###\s+", "", heading).strip()
    return heading.rsplit(" · ", 1)[0].strip()


def _parse_categories(gallery: str) -> dict[int, str]:
    """Map case numbers to the category headings in docs/gallery.md."""

    matches = list(CATEGORY_HEADING.finditer(gallery))
    categories: dict[int, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(gallery)
        section = gallery[match.end() : end]
        category = _category_name(match.group(0))
        for case_match in CASE_LINK.finditer(section):
            categories.setdefault(int(case_match.group(1)), category)
    return categories


def _parse_cases(document: str, *, part: int, commit: str, categories: dict[int, str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    headings = list(CASE_HEADING.finditer(document))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(document)
        body = document[heading.end() : end]
        image = IMAGE.search(body)
        if image is None:
            raise ValueError(f"case {heading.group(1)} has no source image")
        number = int(heading.group(1))
        image_name = image.group(1)
        image_number = int(image.group(2))
        if number != image_number:
            raise ValueError(f"case {number} points to unexpected image {image_name}")
        title = heading.group(2).strip()
        prompt_match = PROMPT_BLOCK.search(body)
        if prompt_match is None or not prompt_match.group(1).strip():
            raise ValueError(f"case {number} has no prompt block")
        prompt = prompt_match.group(1).strip()
        source_path = f"docs/gallery-part-{part}.md"
        category = categories.get(number, DEFAULT_CATEGORY)
        cases.append(
            {
                "id": f"case-{number:03d}",
                "number": number,
                "title": title,
                "prompt": prompt,
                "category": category,
                "image_url": f"https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/{commit}/data/images/{image_name}",
                "source_path": source_path,
                "source_anchor": f"例 {number}：{title}",
                "source_url": f"{UPSTREAM_REPOSITORY}/blob/{commit}/{source_path}#{quote(f'例 {number}：{title}')}",
                "adaptation_hint": (
                    f"参考案例 {number} 的「{category}」视觉方向与信息层级，按当前主题重新设计；"
                    "不得复用案例中的人物、品牌、版权素材、文字、坐标或具体画面。"
                ),
            }
        )
    return cases


def build_manifest(gallery: str, part_one: str, part_two: str, *, commit: str) -> dict[str, Any]:
    """Build a deterministic, image-free manifest from upstream Markdown."""

    categories = _parse_categories(gallery)
    cases = _parse_cases(part_one, part=1, commit=commit, categories=categories)
    cases.extend(_parse_cases(part_two, part=2, commit=commit, categories=categories))
    cases.sort(key=lambda item: item["number"])
    return {
        "version": 1,
        "upstream": {
            "repository": UPSTREAM_REPOSITORY,
            "git": UPSTREAM_GIT,
            "branch": UPSTREAM_BRANCH,
            "commit": commit,
            "license": "MIT",
            "license_url": LICENSE_URL,
            "asset_kind": "remote images only",
            "disclaimer": "案例图及提示词仅供学习与参考；第三方内容的商业使用须取得原权利人授权。",
        },
        "cases": cases,
        "source_report": {
            "reported_case_count": EXPECTED_CASE_COUNT,
            "available_case_count": len(cases),
            "missing_case_numbers": sorted(set(range(1, EXPECTED_CASE_COUNT + 1)) - {item["number"] for item in cases}),
        },
    }


def _gallery_html(manifest: dict[str, Any]) -> str:
    cases = json.dumps(manifest["cases"], ensure_ascii=False).replace("</", "<\\/")
    upstream = manifest["upstream"]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IP Master · GPT-Image 2 案例库</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif; }}
    body {{ margin: 0; background: #f5f5f2; color: #171717; }} header {{ padding: 40px clamp(20px,6vw,96px) 26px; background:#171717; color:#fff; }}
    h1 {{ margin:0 0 10px; font-size:clamp(28px,4vw,48px); }} header p {{ max-width:780px; margin:0; color:#d7d7d7; line-height:1.7; }}
    main {{ padding:28px clamp(20px,6vw,96px) 56px; }} .tools {{ display:flex; flex-wrap:wrap; gap:10px; margin:0 0 24px; }}
    input, button, select {{ font:inherit; }} input {{ min-width:min(100%,320px); padding:10px 12px; border:1px solid #bbb; border-radius:8px; }}
    .filter, .copy, .source, .close {{ border:0; border-radius:8px; padding:10px 13px; cursor:pointer; }} .filter {{ background:#e5e5df; }} .filter.active,.copy {{ background:#f15b45; color:#fff; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:16px; }} .card {{ overflow:hidden; padding:0; border:1px solid #deded8; border-radius:12px; background:#fff; text-align:left; cursor:pointer; box-shadow:0 3px 12px rgba(0,0,0,.05); }}
    .card:hover,.card:focus-visible {{ outline:3px solid #f15b45; outline-offset:2px; }} .card img {{ display:block; width:100%; aspect-ratio:3/4; object-fit:cover; background:#ddd; }} .meta {{ padding:10px 12px 14px; }} .number {{ display:block; font-size:13px; color:#a13b2d; font-weight:700; }} .title {{ display:block; margin-top:5px; line-height:1.4; }}
    dialog {{ max-width:min(980px,94vw); border:0; border-radius:14px; padding:0; box-shadow:0 18px 70px rgba(0,0,0,.35); }} dialog::backdrop {{ background:rgba(0,0,0,.62); }} .modal {{ padding:18px; background:#fff; }} .modal img {{ display:block; max-width:min(760px,88vw); max-height:68vh; margin:0 auto 14px; }} .modal h2 {{ margin:0 0 7px; font-size:20px; }} .modal p {{ margin:0 0 14px; color:#555; line-height:1.6; }} .prompt-label {{ margin:12px 0 6px; font-weight:700; }} .prompt {{ max-height:220px; overflow:auto; margin:0 0 14px; padding:12px; white-space:pre-wrap; border-radius:8px; background:#f4f4f0; color:#333; font:13px/1.55 Consolas,monospace; }} .actions {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }} .source {{ background:#171717; color:#fff; text-decoration:none; }} .close {{ margin-left:auto; background:transparent; font-size:20px; }}
    footer {{ padding:22px clamp(20px,6vw,96px); border-top:1px solid #deded8; color:#555; font-size:14px; line-height:1.65; }} a {{ color:inherit; }} .empty {{ grid-column:1/-1; padding:26px; background:#fff; border-radius:12px; }}
  </style>
</head>
<body>
  <header><h1>GPT-Image 2 案例库</h1><p>浏览案例、搜索或按类别筛选；选中后复制“用案例 N 设计”。案例只提供可迁移的视觉方向，图片不会作为生图参考图输入。</p></header>
  <main><div class="tools"><input id="search" type="search" placeholder="搜索案例号、标题或类别" aria-label="搜索案例"><button class="filter active" data-category="">全部</button><span id="filters"></span></div><p id="count"></p><section id="grid" class="grid" aria-label="GPT-Image 2 案例列表"></section></main>
  <dialog id="preview"><div class="modal"><img id="preview-image" alt=""><h2 id="preview-title"></h2><p id="preview-hint"></p><div class="prompt-label">源案例提示词</div><pre class="prompt" id="preview-prompt"></pre><div class="actions"><button class="copy" id="copy">复制编号</button><button class="copy" id="copy-prompt">复制提示词</button><a class="source" id="source" target="_blank" rel="noreferrer">查看源案例</a><button class="close" id="close" aria-label="关闭">×</button></div></div></dialog>
  <footer>案例索引来自 <a href="{upstream['repository']}" target="_blank" rel="noreferrer">freestylefly/awesome-gpt-image-2</a>，按 <a href="{upstream['license_url']}" target="_blank" rel="noreferrer">MIT</a> 使用；固定提交：<code>{upstream['commit']}</code>。{upstream['disclaimer']}</footer>
  <script>
    const cases = {cases}; const grid = document.querySelector('#grid'); const search = document.querySelector('#search'); const filters = document.querySelector('#filters'); const count = document.querySelector('#count'); const dialog = document.querySelector('#preview'); let category = ''; let selected = null;
    const categories = [...new Set(cases.map(item => item.category))];
    for (const name of categories) {{ const button = document.createElement('button'); button.className='filter'; button.textContent=name; button.dataset.category=name; filters.append(button); }}
    function render() {{ const query=search.value.trim().toLowerCase(); const visible=cases.filter(item => (!category || item.category===category) && (!query || `${{item.number}} ${{item.title}} ${{item.category}}`.toLowerCase().includes(query))); count.textContent=`显示 ${{visible.length}} / ${{cases.length}} 个案例`; grid.replaceChildren(); if (!visible.length) {{ const empty=document.createElement('p'); empty.className='empty'; empty.textContent='没有匹配案例。'; grid.append(empty); return; }} for (const item of visible) {{ const card=document.createElement('button'); card.className='card'; card.type='button'; const image=document.createElement('img'); image.loading='lazy'; image.src=item.image_url; image.alt=`案例 ${{item.number}}：${{item.title}}`; const meta=document.createElement('span'); meta.className='meta'; const number=document.createElement('span'); number.className='number'; number.textContent=`案例 ${{item.number}} · ${{item.category}}`; const title=document.createElement('span'); title.className='title'; title.textContent=item.title; meta.append(number,title); card.append(image,meta); card.addEventListener('click',()=>openCase(item)); grid.append(card); }} }}
    function openCase(item) {{ selected=item; document.querySelector('#preview-image').src=item.image_url; document.querySelector('#preview-image').alt=`案例 ${{item.number}}：${{item.title}}`; document.querySelector('#preview-title').textContent=`案例 ${{item.number}} · ${{item.title}}`; document.querySelector('#preview-hint').textContent=item.adaptation_hint; document.querySelector('#preview-prompt').textContent=item.prompt; document.querySelector('#source').href=item.source_url; dialog.showModal(); }}
    document.querySelector('.tools').addEventListener('click', event => {{ const button=event.target.closest('[data-category]'); if (!button) return; category=button.dataset.category; document.querySelectorAll('.filter').forEach(item=>item.classList.toggle('active',item===button)); render(); }}); search.addEventListener('input',render); document.querySelector('#close').addEventListener('click',()=>dialog.close()); document.querySelector('#copy').addEventListener('click',async event=>{{ if(!selected) return; try {{ await navigator.clipboard.writeText(`用案例 ${{selected.number}} 设计`); }} catch {{}} event.currentTarget.textContent='已复制'; setTimeout(()=>event.currentTarget.textContent='复制编号',1200); }}); document.querySelector('#copy-prompt').addEventListener('click',async event=>{{ if(!selected) return; try {{ await navigator.clipboard.writeText(selected.prompt); }} catch {{}} event.currentTarget.textContent='已复制'; setTimeout(()=>event.currentTarget.textContent='复制提示词',1200); }}); render();
  </script>
</body></html>"""


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_library(manifest: dict[str, Any], library_dir: Path) -> None:
    library_dir.mkdir(parents=True, exist_ok=True)
    _write_json(library_dir / "manifest.json", manifest)
    (library_dir / "index.html").write_text(_gallery_html(manifest), encoding="utf-8")


def sync_library(*, skill_dir: Path = SKILL_DIR, source_dir: Path | None = None) -> dict[str, Any]:
    """Fetch source Markdown, pin it to one commit, and write metadata only."""

    if source_dir is None:
        commit = _remote_commit()
        base = f"https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/{commit}"
        gallery, part_one, part_two = (
            _fetch_text(f"{base}/docs/gallery.md"),
            _fetch_text(f"{base}/docs/gallery-part-1.md"),
            _fetch_text(f"{base}/docs/gallery-part-2.md"),
        )
    else:
        source_dir = source_dir.expanduser().resolve(strict=True)
        commit = subprocess.run(["git", "-C", str(source_dir), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        gallery = (source_dir / "docs" / "gallery.md").read_text(encoding="utf-8")
        part_one = (source_dir / "docs" / "gallery-part-1.md").read_text(encoding="utf-8")
        part_two = (source_dir / "docs" / "gallery-part-2.md").read_text(encoding="utf-8")
    manifest = build_manifest(gallery, part_one, part_two, commit=commit)
    report = validate_manifest(manifest)
    if not report["valid"]:
        raise ValueError("invalid upstream case collection: " + "; ".join(report["errors"]))
    target = skill_dir / "assets" / "gpt-image-2-case-library"
    with tempfile.TemporaryDirectory(prefix="gpt-image-2-library-", dir=target.parent) as temp:
        staged = Path(temp) / "library"
        _write_library(manifest, staged)
        backup = target.with_name(f"{target.name}.backup")
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.replace(backup)
        try:
            staged.replace(target)
        except Exception:
            if target.exists():
                shutil.rmtree(target)
            if backup.exists():
                backup.replace(target)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    return {"commit": commit, "count": len(manifest["cases"]), "library": str(target)}


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    upstream = manifest.get("upstream") if isinstance(manifest, dict) else None
    cases = manifest.get("cases") if isinstance(manifest, dict) else None
    if not isinstance(upstream, dict):
        errors.append("manifest upstream must be an object")
    if not isinstance(cases, list):
        errors.append("manifest cases must be a list")
        cases = []
    records = [item for item in cases if isinstance(item, dict)]
    numbers = [item.get("number") for item in records]
    expected_numbers = set(range(1, EXPECTED_CASE_COUNT + 1))
    available_numbers = {number for number in numbers if isinstance(number, int)}
    missing_numbers = expected_numbers - available_numbers
    if missing_numbers not in (set(), set(KNOWN_SOURCE_OMISSIONS)):
        errors.append("unexpected missing case numbers: " + ", ".join(str(item) for item in sorted(missing_numbers)))
    if len(records) != len(available_numbers):
        errors.append("case records are duplicated")
    if len(set(numbers)) != len(records):
        errors.append("case numbers are not unique")
    if available_numbers - expected_numbers:
        errors.append("case numbers must stay within 1-544")
    categories = {item.get("category") for item in records if isinstance(item.get("category"), str) and item["category"]}
    if len(categories) != EXPECTED_CATEGORY_COUNT:
        errors.append(f"expected {EXPECTED_CATEGORY_COUNT} categories, found {len(categories)}")
    for item in records:
        required = ("id", "number", "title", "category", "prompt", "image_url", "source_path", "source_anchor", "source_url", "adaptation_hint")
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in required if key != "number") or not isinstance(item.get("number"), int):
            errors.append(f"incomplete case record: {item.get('number')}")
            continue
        if not item["image_url"].startswith("https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/"):
            errors.append(f"unexpected remote image URL: {item['number']}")
        if not item["source_url"].startswith(f"{UPSTREAM_REPOSITORY}/blob/"):
            errors.append(f"unexpected source URL: {item['number']}")
    return {
        "valid": not errors,
        "errors": errors,
        "count": len(records),
        "category_count": len(categories),
        "missing_case_numbers": sorted(missing_numbers),
    }


def validate_library(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    try:
        manifest = json.loads((skill_dir / "assets" / "gpt-image-2-case-library" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"cannot read manifest: {exc}"], "count": 0, "category_count": 0}
    report = validate_manifest(manifest)
    if not (skill_dir / "assets" / "gpt-image-2-case-library" / "index.html").is_file():
        report["errors"].append("missing gallery HTML")
        report["valid"] = False
    report["manifest"] = manifest
    return report


def parse_case_selection(request: str, *, skill_dir: Path = SKILL_DIR) -> dict[str, Any] | None:
    match = next((found for pattern in SELECTION_PATTERNS if (found := re.search(pattern, request, flags=re.IGNORECASE))), None)
    if match is None:
        return None
    number = int(match.group(1))
    report = validate_library(skill_dir=skill_dir)
    if not report["valid"]:
        raise ValueError("case library is unavailable: " + "; ".join(report["errors"]))
    selected = next((item for item in report["manifest"]["cases"] if item["number"] == number), None)
    if selected is None:
        raise ValueError(f"unknown case number: {number}; choose 1-{EXPECTED_CASE_COUNT}")
    return {
        **selected,
        "gallery_path": str((skill_dir / "assets" / "gpt-image-2-case-library" / "index.html").resolve()),
        "generation_instruction": selected["adaptation_hint"],
        "visual_isolation_constraint": "案例图仅供浏览，不能作为模型输入；不得复用案例中的人物、品牌、版权素材、文字、坐标或具体画面。",
        "prompt_label": f"案例 {number}：{selected['title']}（仅迁移视觉方向）",
    }


def check_upstream(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    report = validate_library(skill_dir=skill_dir)
    if not report["valid"]:
        raise ValueError("case library is unavailable: " + "; ".join(report["errors"]))
    remote = _remote_commit()
    current = report["manifest"]["upstream"]["commit"]
    return {"current_commit": current, "remote_commit": remote, "update_available": current != remote, "count": report["count"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Maintain the GPT-Image 2 source-linked case library")
    parser.add_argument("--sync", action="store_true", help="fetch upstream Markdown and refresh the local index")
    parser.add_argument("--source-dir", type=Path, help="local upstream checkout for a deterministic sync")
    parser.add_argument("--validate", action="store_true", help="validate the local index and gallery")
    parser.add_argument("--check", action="store_true", help="compare the pinned commit with upstream main")
    parser.add_argument("--select", help="resolve a selected case, for example: 用案例 539 设计")
    parser.add_argument("--skill-dir", type=Path, default=SKILL_DIR)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    if sum(bool(value) for value in (args.sync, args.validate, args.check, args.select)) != 1:
        parser.error("choose exactly one action")
    try:
        if args.sync:
            payload = sync_library(skill_dir=args.skill_dir, source_dir=args.source_dir)
        elif args.validate:
            payload = validate_library(skill_dir=args.skill_dir)
        elif args.check:
            payload = check_upstream(skill_dir=args.skill_dir)
        else:
            payload = parse_case_selection(args.select, skill_dir=args.skill_dir)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"case library error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload)
    return 0 if payload is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
