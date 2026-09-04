#!/usr/bin/env python3
"""Create and maintain a portable IP Master character project."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


PROJECT_MANIFEST = "ip-master-project.json"
PROJECT_REGISTRY = Path("characters") / "registry.json"
PROJECT_GALLERY = "index.html"


class IPProjectError(ValueError):
    """Raised when a project directory cannot safely be used."""


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def project_paths(project_dir: Path) -> dict[str, Path]:
    root = project_dir.expanduser().resolve(strict=False)
    return {
        "root": root,
        "manifest": root / PROJECT_MANIFEST,
        "registry": root / PROJECT_REGISTRY,
        "gallery": root / PROJECT_GALLERY,
        "assets": root / "characters" / "assets",
        "identities": root / "characters" / "identities",
    }


def initialize_project(project_dir: Path, *, name: str | None = None) -> dict[str, str | bool]:
    """Initialize an empty project without touching the installed Skill."""

    paths = project_paths(project_dir)
    root = paths["root"]
    if root.exists() and not root.is_dir():
        raise IPProjectError(f"project path is not a directory: {root}")
    if root.exists() and any(root.iterdir()) and not paths["manifest"].is_file():
        raise IPProjectError(f"project directory is not empty: {root}")
    if paths["manifest"].is_file():
        load_project(project_dir)
        rebuild_gallery(project_dir)
        return {
            "initialized": False,
            "project_dir": str(root),
            "gallery_path": str(paths["gallery"]),
            "gallery_url": paths["gallery"].as_uri(),
        }

    root.mkdir(parents=True, exist_ok=True)
    paths["assets"].mkdir(parents=True, exist_ok=True)
    paths["identities"].mkdir(parents=True, exist_ok=True)
    _write_text(
        paths["manifest"],
        json.dumps(
            {
                "version": 1,
                "name": (name or root.name or "IP Master 项目").strip(),
                "character_registry": PROJECT_REGISTRY.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    _write_text(paths["registry"], json.dumps({"version": 1, "characters": []}, ensure_ascii=False, indent=2) + "\n")
    rebuild_gallery(project_dir)
    return {
        "initialized": True,
        "project_dir": str(root),
        "gallery_path": str(paths["gallery"]),
        "gallery_url": paths["gallery"].as_uri(),
    }


def load_project(project_dir: Path) -> dict[str, Any]:
    paths = project_paths(project_dir)
    try:
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IPProjectError(f"cannot read IP project: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise IPProjectError("project manifest must be a version 1 object")
    if manifest.get("character_registry") != PROJECT_REGISTRY.as_posix():
        raise IPProjectError("project manifest has an unsupported character registry path")
    if not isinstance(registry, dict) or registry.get("version") != 1 or not isinstance(registry.get("characters"), list):
        raise IPProjectError("project character registry must be a version 1 object with a characters list")
    return {"paths": paths, "manifest": manifest, "registry": registry}


def rebuild_gallery(project_dir: Path) -> Path:
    """Render the project-only role browser as portable local HTML."""

    project = load_project(project_dir)
    paths = project["paths"]
    cards: list[str] = []
    for item in project["registry"]["characters"]:
        if not isinstance(item, dict):
            continue
        display_name = str(item.get("display_name", "未命名角色"))
        aliases = " · ".join(str(alias) for alias in item.get("aliases", []) if isinstance(alias, str))
        identity_path = paths["root"] / str(item.get("identity_reference", ""))
        try:
            identity = identity_path.read_text(encoding="utf-8").strip().splitlines()
            summary = next((line.lstrip("- ").strip() for line in identity if line.startswith("- ")), "已确认项目角色")
        except (OSError, UnicodeError):
            summary = "已确认项目角色"
        call = f"使用 IP：{display_name}，制作一张 [图片类型]，主题：[主题]。"
        profile = item.get("profile") if isinstance(item.get("profile"), dict) else {}
        profile_text = (
            f"{profile.get('age', '—')}岁 · {profile.get('height_cm', '—')}cm · "
            f"{profile.get('weight_kg', '—')}kg"
        )
        cards.append(
            "<article class=\"card\">"
            f"<img src=\"{html.escape(str(item.get('asset', '')), quote=True)}\" alt=\"{html.escape(display_name, quote=True)}\">"
            "<div class=\"body\">"
            f"<h2>{html.escape(display_name)}</h2><p class=\"aliases\">{html.escape(aliases)}</p>"
            f"<p class=\"profile\">{html.escape(profile_text)}</p>"
            f"<p>{html.escape(summary)}</p>"
            f"<button type=\"button\" data-copy=\"{html.escape(call, quote=True)}\">复制调用</button>"
            "</div></article>"
        )
    content = "\n".join(cards) if cards else (
        "<div class=\"empty\"><h2>还没有项目角色</h2><p>让 Codex 设计 IP；确认后使用注册命令保存到当前项目。内置角色仍可直接调用，但不会显示在这里。</p></div>"
    )
    title = html.escape(str(project["manifest"].get("name") or "IP Master 项目"))
    page = f"""<!doctype html>
<html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{title} · IP 角色库</title>
<style>:root{{color-scheme:dark;--bg:#101214;--surface:#191d22;--line:#303842;--text:#f2f4f6;--muted:#aab3bd;--accent:#90d76b}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 Inter,"PingFang SC","Microsoft YaHei",sans-serif}}main{{width:min(1120px,calc(100% - 36px));margin:auto}}header{{padding:28px 0 22px;border-bottom:1px solid var(--line)}}h1{{margin:0;font-size:26px}}.note,.aliases,p{{color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding:24px 0 42px}}.card,.empty{{border:1px solid var(--line);background:var(--surface)}}.card img{{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#242a30;padding:10px}}.body{{padding:14px}}h2{{margin:0;font-size:17px}}.aliases{{margin:3px 0 9px;font-size:13px}}button{{border:1px solid #495762;background:#222a31;color:var(--text);border-radius:4px;padding:8px 11px;cursor:pointer}}button:hover{{color:var(--accent);border-color:var(--accent)}}.empty{{grid-column:1/-1;padding:28px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}main{{width:min(100% - 28px,1120px)}}}}</style></head>
<body><main><header><h1>{title} · IP 角色库</h1><p class=\"note\">仅展示本项目已登记的自定义 IP。内置角色可继续直接调用，但不在此列表中。</p></header><section class=\"grid\">{content}</section></main>
<script>document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{{const t=b.textContent;try{{await navigator.clipboard.writeText(b.dataset.copy);b.textContent='已复制'}}catch{{b.textContent='请手动复制'}}setTimeout(()=>b.textContent=t,1200)}}));</script></body></html>"""
    _write_text(paths["gallery"], page)
    return paths["gallery"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize or rebuild an IP Master project")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--init", action="store_true", help="create an empty IP project")
    action.add_argument("--build-gallery", action="store_true", help="rebuild the project role browser")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--name", help="project name used by --init")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        result: dict[str, Any]
        if args.init:
            result = initialize_project(args.project_dir, name=args.name)
        else:
            gallery = rebuild_gallery(args.project_dir)
            result = {"gallery_path": str(gallery), "gallery_url": gallery.as_uri()}
    except IPProjectError as exc:
        result = {"error": str(exc)}
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"error: {exc}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result.get("gallery_path", result["project_dir"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
