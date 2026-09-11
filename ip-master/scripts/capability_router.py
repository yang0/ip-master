#!/usr/bin/env python3
"""Route IP Master requests to registered external Skills.

IP Master is an orchestration layer. It owns character selection, dependency
metadata, and ordered reference inputs; it does not generate images and never
falls back to a native illustration implementation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REGISTRY_PATH = SKILL_DIR / "references" / "skill-registry.json"
PERSONAL_IP_SKILL_ID = "personal-ip-image-pack"
GUIDE_RELATIVE_PATH = "assets/readme/index.html"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from character_router import resolve_character_inputs  # noqa: E402
from dependency_utils import (  # noqa: E402
    inspect_dependency,
    inspect_dependency_location,
    load_dependency_registry,
)
from layout_library import parse_layout_selection  # noqa: E402
from gpt_image_2_case_library import parse_case_selection  # noqa: E402
from visual_style_library import parse_visual_style_selection  # noqa: E402


# The order is meaningful: personal-photo signals must win over generic
# "cartoon", "sticker", or "cover" words in the same request.
CATEGORY_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "ip-design",
        (
            "真人照片 ip",
            "真人照片ip",
            "个人照片 ip",
            "个人照片ip",
            "真人照片",
            "本人卡通形象",
            "博主形象",
            "个人头像 ip",
            "个人头像ip",
            "照片转卡通",
            "人物表情包",
            "人物动作包",
            "个人卡通 ip",
            "个人卡通ip",
            "个人 ip",
            "个人ip",
            "人物 ip",
            "人物ip",
            "设计 ip",
            "设计ip",
            "制作 ip",
            "制作ip",
            "卡通形象",
            "角色锚点",
            "三视图",
        ),
    ),
    ("knowledge-comic", ("知识漫画", "知识 comic", "knowledge comic", "comic")),
    (
        "article-illustration",
        ("文章配图", "正文配图", "文章插图", "博客配图", "article illustration"),
    ),
    ("wechat-cover", ("公众号封面", "微信封面", "公众号头图")),
    (
        "cover-poster",
        ("横版封面", "竖版封面", "封面", "海报", "方图", "cover", "poster"),
    ),
    ("knowledge-card", ("知识卡片", "知识卡", "信息图", "infographic")),
    ("xiaohongshu", ("小红书", "xhs", "rednote")),
    ("slide-deck", ("ppt", "幻灯片", "演示文稿", "slide deck", "presentation")),
    ("couple-photo", ("情侣照", "情侣写真", "婚纱照", "couple photo", "couple-photo")),
    (
        "portrait",
        ("真实抓拍人像", "生活感人像", "偶然抓拍", "candid photography", "抓拍写真"),
    ),
    (
        "video-workflow",
        ("情侣旅行 vlog", "情侣旅行vlog", "旅行照片墙", "虚拟情侣", "travel vlog"),
    ),
    ("sticker", ("贴纸", "贴纸页", "表情包", "sticker")),
    (
        "prompt-enhancement",
        (
            "提示词增强",
            "风格库增强",
            "模板增强",
            "gpt image 2 风格库",
            "prompt enhancement",
            "手绘风格",
            "手绘风格库",
            "手绘提示词",
            "handdraw style",
            "handraw style",
        ),
    ),
)

# Bare words such as “建议” also occur in article paths (for example
# 运营建议); advice mode requires an intent phrase so paths do not cancel a
# concrete design request.
ADVICE_SIGNALS = ("给我建议", "提供建议", "推荐哪个", "建议用哪个", "哪个skill", "哪个 skill", "能生成什么", "有哪些能力", "不要生图")
GUIDE_SIGNALS = (
    "第一次用",
    "首次使用",
    "怎么用",
    "如何使用",
    "帮助",
    "不会用",
    "使用疑问",
    "使用帮助",
    "ip master 帮助",
    "ipmaster 帮助",
)
PERSONAL_SIGNALS = {
    "真人照片 ip",
    "真人照片ip",
    "个人照片 ip",
    "个人照片ip",
    "真人照片",
    "本人卡通形象",
    "博主形象",
    "个人头像 ip",
    "个人头像ip",
    "照片转卡通",
    "人物表情包",
    "人物动作包",
    "个人卡通 ip",
    "个人卡通ip",
    "个人 ip",
    "个人ip",
}
EXCLUDED_PERSONAL_SIGNALS = (
    "动物 ip",
    "动物ip",
    "动物",
    "吉祥物",
    "虚构角色",
    "虚构人物",
)
PHOTO_SOURCE_SIGNALS = ("真人照片", "人物照片", "上传照片", "上传的照片", "参考照片", "参考图")
FOUR_VIEW_CHOICES = (
    "四视图",
    "转面图",
    "人物四视图",
)
PHOTO_TRAIT_CHOICES = (
    "直接用照片设计",
    "直接使用照片",
    "基于照片",
    "基于真人照片",
    "真人照片特征",
    "基于上传照片",
    "基于上传的照片",
    "根据照片",
    "根据上传照片",
    "参考照片设计",
    "提取照片特征",
    "只参考脸部",
    "仅参考照片",
)

EXPLICIT_ALIASES: dict[str, tuple[str, ...]] = {
    "punk-cover": ("punk cover", "punk-cover", "朋克封面", "Punk 封面"),
    "punk-avatar": ("punk avatar", "punk-avatar", "朋克头像", "Punk 头像", "头像生成"),
    "mono-color": (
        "mono color",
        "mono-color",
        "mono-color-skill",
        "单色海报",
        "双色印刷",
        "单色调视觉",
        "孔版印刷",
        "risograph",
        "网点照片",
    ),
    "ip-as-logo": (
        "ip as logo",
        "ip-as-logo",
        "ip 吉祥物",
        "吉祥物",
        "圆润 ip",
        "极简 ip",
    ),
    PERSONAL_IP_SKILL_ID: (
        "personal ip image pack",
        "personal ip",
        "个人照片 ip",
        "个人照片ip",
        "个人 ip 制作",
        "个人ip制作",
    ),
    "ip-illustration-character-system": (
        "ip illustration character system",
        "everett",
        "萌粒",
        "钢笔涂鸦",
    ),
    "ian-xiaohei-illustrations": ("ian xiaohei illustrations", "ian 小黑配图", "小黑配图"),
    "dongfang-cover-design": ("dongfang", "东方封面", "东方设计"),
    "guizang-social-card-skill": ("guizang social card skill", "归藏", "归藏社交卡"),
    "gbro-cover-design": ("gbro", "gbro cover design", "gbro 封面", "三轮提问封面"),
    "gpt-image-2-style-library": (
        "gpt image 2 style library",
        "gpt image 2 风格库",
        "gpt image 2 模板库",
        "模板库增强",
    ),
    "vibeshot-candid-photography": (
        "vibeshot candid photography",
        "真实抓拍人像",
        "偶然抓拍写真",
        "生活感人像",
    ),
    "virtual-couple-travel-vlog": (
        "virtual couple travel vlog",
        "情侣旅行 vlog",
        "情侣旅行vlog",
        "虚拟情侣旅行",
        "旅行照片墙",
    ),
    "couple-photo-requirements-planner": (
        "couple photo requirements planner",
        "情侣照需求确认",
        "情侣写真需求",
        "情侣照需求规划",
    ),
    "couple-photo-shooting-planner": (
        "couple photo shooting planner",
        "情侣照拍摄规划",
        "情侣照 shot list",
        "8 宫格拍摄",
    ),
    "couple-photo-wardrobe-board": (
        "couple photo wardrobe board",
        "情侣换装",
        "情侣换衣服",
        "重新搭配情侣服装",
    ),
    "couple-photo-orchestrator": (
        "couple photo orchestrator",
        "couple photo",
        "couple-photo",
        "情侣照",
        "情侣写真",
        "婚纱照",
    ),
    "handdraw-style-prompter": (
        "handdraw style prompter",
        "handraw style",
        "handdraw style",
        "手绘风格",
        "手绘风格库",
        "手绘提示词",
        "手绘画风",
    ),
}
CAPABILITY_ALIASES: dict[str, tuple[str, ...]] = {
    "punk-cover": ("朋克封面", "cover prompt"),
    "cover-prompt": ("封面提示词", "cover prompt"),
    "cover-image-generation": ("封面生图", "生成封面"),
    "punk-avatar": ("朋克头像", "avatar prompt"),
    "avatar-image-generation": ("头像生图", "生成头像"),
    "pet-avatar": ("宠物头像", "pet avatar"),
    "object-avatar": ("物品头像", "object avatar"),
    "mono-color-editorial": ("单色编辑", "编辑印刷", "editorial print"),
    "one-ink-print": ("单色印刷", "单墨", "one ink"),
    "duotone-print": ("双色", "双色印刷", "duotone"),
    "editorial-layout": ("编辑排版", "zine", "杂志排版"),
    "mascot-ip": ("IP 吉祥物", "吉祥物", "mascot", "mascot IP"),
    "rounded-silhouette": ("圆润轮廓", "圆润造型", "simplified mascot"),
    "six-candidate-generation": ("六个候选", "6 个候选", "six candidates"),
    "character-anchor": ("角色锚点", "角色形象", "character anchor"),
    "turnaround-sheet": ("三视图", "转面图", "turnaround"),
    "mini-article-illustration": ("萌粒", "萌粒文章插图", "mini illustration"),
    "sticker-sheet-3x4": ("贴纸页", "3:4 贴纸", "sticker sheet"),
    "expression-pack": ("表情包", "表情套图", "expression pack"),
    "action-pack": ("动作包", "动作套图", "action pack"),
    "sticker-pack": ("贴纸套图", "sticker pack"),
    "landscape-cover": ("横版封面", "横屏封面", "landscape cover"),
    "portrait-poster": ("竖版海报", "竖屏海报", "portrait poster"),
    "square-graphic": ("方图", "正方形", "square graphic"),
    "cover-prompt-3x4": ("3:4 封面", "3:4封面", "3x4 封面"),
    "article-illustration": ("文章配图", "正文配图", "文章插图"),
    "comic": ("知识漫画", "knowledge comic"),
    "infographic": ("知识卡片", "信息图", "infographic"),
    "xhs-images": ("小红书图片", "小红书图文", "xhs images"),
    "xhs-social-cards": ("小红书图文组图", "归藏社交卡"),
    "slide-deck": ("幻灯片", "ppt", "slide deck"),
    "prompt-enhancement": ("提示词增强", "风格库增强", "模板增强"),
    "candid-portrait-prompt": ("真实抓拍人像", "偶然抓拍", "抓拍写真"),
    "travel-photo-wall": ("旅行照片墙", "4x4 照片墙", "情侣旅行"),
    "numbered-hand-drawn-style": ("手绘风格", "手绘风格库", "手绘画风", "handdraw style"),
}


def _normalize(text: str) -> str:
    """Normalize case, hyphens, and whitespace while keeping CJK text intact."""

    return re.sub(r"\s+", " ", text.casefold().replace("-", " ").strip())


def _contains(text: str, phrase: str) -> bool:
    phrase = _normalize(phrase)
    if not phrase:
        return False
    if phrase.isascii():
        return re.search(rf"(?<![a-z0-9_]){re.escape(phrase)}(?![a-z0-9_])", text) is not None
    return phrase in text


def detect_category(request: str) -> str | None:
    """Return the first matching user-facing capability category."""

    text = _normalize(request)
    for category, signals in CATEGORY_SIGNALS:
        if any(_contains(text, signal) for signal in signals):
            return category
    return None


def _has_personal_signal(request: str) -> bool:
    text = _normalize(request)
    return any(_contains(text, signal) for signal in PERSONAL_SIGNALS)


def _has_excluded_personal_signal(request: str) -> bool:
    text = _normalize(request)
    return any(_contains(text, signal) for signal in EXCLUDED_PERSONAL_SIGNALS)


def _has_photo_source_signal(request: str) -> bool:
    text = _normalize(request)
    return any(_contains(text, signal) for signal in PHOTO_SOURCE_SIGNALS)


def _has_photo_workflow_choice(request: str) -> bool:
    text = _normalize(request)
    return any(_contains(text, signal) for signal in FOUR_VIEW_CHOICES + PHOTO_TRAIT_CHOICES)


def _has_four_view_choice(request: str) -> bool:
    text = _normalize(request)
    return any(_contains(text, signal) for signal in FOUR_VIEW_CHOICES)


def _photo_workflow_choice_result(request: str, operation: str, category: str) -> dict[str, Any]:
    result = _empty_result(
        request,
        operation,
        category,
        reason="A real-person photo IP request must choose a four-view identity asset or photo-trait-based IP design before routing.",
    )
    result.update(
        {
            "status": "photo-workflow-choice",
            "route_mode": "clarification",
            "clarification_required": True,
            "clarification": {
                "question": "你希望哪一种？",
                "options": [
                    {
                        "id": "four-view-first",
                        "label": "先生成四视图，再作为 IP 身份资产",
                        "next": "先生成四视图候选，再收集并确认名称、年龄、身高、体重，确认后入库。",
                    },
                    {
                        "id": "photo-traits-first",
                        "label": "基于照片特征直接设计 IP",
                        "next": "只提取脸部特征、年龄感和气质来设计 IP，不把照片直接作为正式四视图资产。",
                    },
                ],
            },
        }
    )
    return result


def _dependency_aliases(dependency: dict[str, Any]) -> list[str]:
    skill_id = str(dependency["skill_id"])
    aliases = [skill_id, skill_id.replace("-", " ")]
    install_name = dependency.get("install_name")
    if isinstance(install_name, str):
        aliases.extend((install_name, install_name.replace("-", " ")))
    aliases.extend(EXPLICIT_ALIASES.get(skill_id, ()))
    return aliases


def _explicit_dependency(
    request: str,
    dependencies: list[dict[str, Any]],
    *,
    category: str | None = None,
) -> str | None:
    """Find an explicitly named dependency, without treating generic words as names."""

    text = _normalize(request)
    # Versioned names must win over the generic 小黑配图 alias and a style layer.
    if re.search(r"小黑\s*(?:配图\s*)?2\.0", text):
        return "ian-xiaohei-scenes"
    for dependency in dependencies:
        if any(_contains(text, alias) for alias in _dependency_aliases(dependency)):
            return str(dependency["skill_id"])

    # Baoyu is a family in one upstream repository. The category disambiguates
    # the concrete Skill; without a category it must remain a user choice.
    if _contains(text, "宝玉") or _contains(text, "baoyu"):
        matches = [
            dependency
            for dependency in dependencies
            if str(dependency.get("repo", "")).casefold().startswith("jimliu/")
            and (category is None or category in dependency.get("categories", []))
        ]
        if len(matches) == 1:
            return str(matches[0]["skill_id"])

    return None


def _rank(request: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep registry order; move an item with explicit signal aliases first."""

    text = _normalize(request)
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(candidates):
        score = sum(1 for signal in item.get("signals", []) if _contains(text, str(signal)))
        score += sum(1 for alias in EXPLICIT_ALIASES.get(str(item["skill_id"]), ()) if _contains(text, alias))
        ranked.append((-score, index, item))
    return [item for _, _, item in sorted(ranked)]


def _supports_category(dependency: dict[str, Any], category: str | None) -> bool:
    if category is None:
        return True
    if dependency.get("skill_id") == "handdraw-style-prompter" and category in {
        "cover-poster",
        "article-illustration",
        "knowledge-card",
        "xiaohongshu",
        "slide-deck",
        "portrait",
        "prompt-enhancement",
    }:
        return True
    if category in dependency.get("categories", []):
        return True
    capabilities = {str(item) for item in dependency.get("capabilities", [])}
    aliases = {
        "ip-design": {
            "personal-ip-prototype",
            "character-anchor",
            "turnaround-sheet",
            "mini-article-illustration",
        },
        "sticker": {"sticker-pack", "sticker-sheet-3x4", "expression-pack"},
        "article-illustration": {"mini-article-illustration"},
    }
    return bool(capabilities.intersection(aliases.get(category, set())))


def _target_capability(request: str, dependency: dict[str, Any], category: str | None) -> str | None:
    capabilities = [str(item) for item in dependency.get("capabilities", [])]
    text = _normalize(request)
    for capability in capabilities:
        aliases = CAPABILITY_ALIASES.get(capability, ())
        if _contains(text, capability) or any(_contains(text, alias) for alias in aliases):
            return capability
    if category:
        category_caps = {
            "ip-design": ("personal-ip-prototype", "character-anchor", "mascot-ip"),
            "article-illustration": ("article-illustration", "article-shot-list", "mini-article-illustration"),
            "knowledge-comic": ("comic",),
            "cover-poster": ("landscape-cover", "cover-image", "cover-prompt-3x4"),
            "knowledge-card": ("infographic", "article-infographic-3x4"),
            "xiaohongshu": ("xhs-images", "xhs-social-cards"),
            "wechat-cover": ("wechat-cover-pair", "cover-image"),
            "slide-deck": ("slide-deck",),
            "couple-photo": ("couple-photo-orchestration", "couple-requirements", "shot-list", "wardrobe-board"),
            "sticker": ("sticker-pack", "sticker-sheet-3x4"),
            "prompt-enhancement": ("prompt-enhancement",),
        }
        for capability in category_caps.get(category, ()):
            if capability in capabilities:
                return capability
    return capabilities[0] if len(capabilities) == 1 else None


def _dependency_report(
    dependency: dict[str, Any],
    *,
    skill_dir: Path,
    dependency_root: Path | None,
) -> dict[str, Any]:
    report = inspect_dependency(dependency, skill_root=skill_dir)
    if dependency_root is None:
        return report
    # A test harness or caller may provide an already-installed root without
    # changing CODEX_HOME. Probe it first, retaining normal locations.
    candidate = dependency_root.expanduser().resolve(strict=False)
    location = inspect_dependency_location(dependency, candidate)
    report["locations"] = [location] + [item for item in report["locations"] if item["path"] != str(candidate)]
    report["installed"] = location["valid"] or report["installed"]
    report["available"] = report["installed"]
    report["status"] = "installed" if report["installed"] else ("invalid" if location["exists"] else report["status"])
    report["installed_location"] = str(candidate) if location["valid"] else report["installed_location"]
    return report


def _empty_result(request: str, operation: str, category: str | None, *, reason: str) -> dict[str, Any]:
    return {
        "request": request,
        "operation": operation,
        "category": category,
        "status": "unsupported",
        "route_mode": "no-target",
        "native_generation": False,
        "native_fallback": False,
        "selected_skill_id": None,
        "target_skill_id": None,
        "target_capability": None,
        "selected_dependency": None,
        "candidates": [],
        "selection_required": False,
        "style_selection_required": False,
        "inject_characters": False,
        "inject_character_references": False,
        "characters": [],
        "character_inputs": [],
        "referenced_image_paths": [],
        "reference_inputs": [],
        "installation_requested": False,
        "requires_install_confirmation": False,
        "install_command": None,
        "generation_ready": False,
        "layout_library": None,
        "case_library": None,
        "guide_page": None,
        "reason": reason,
    }


def _guide_result(request: str, operation: str, skill_dir: Path) -> dict[str, Any]:
    """Return a display-only local-guide result without selecting a Skill."""

    result = _empty_result(
        request,
        operation,
        None,
        reason="Open the local IP Master guide, then continue with the user's request when one is present.",
    )
    result.update(
        {
            "status": "guide",
            "route_mode": "guide",
            "guide_page": {
                "path": str((skill_dir / GUIDE_RELATIVE_PATH).resolve()),
                "relative_path": GUIDE_RELATIVE_PATH,
                "browser_url": (skill_dir / GUIDE_RELATIVE_PATH).resolve().as_uri(),
                "display_surface": "browser",
                "display_rule": "Navigate to browser_url in a rendered browser tab; do not open path in a code or file panel. Do not select a Skill, inject references, install dependencies, or generate an image.",
            },
        }
    )
    return result


def route(
    request: str,
    *,
    operation: str = "create",
    skill_dir: Path = SKILL_DIR,
    dependency_root: Path | None = None,
    project_dir: Path | None = None,
    reference_photo: bool | None = None,
) -> dict[str, Any]:
    """Route one request without installing or generating anything.

    ``advise`` is intentionally non-mutating and never injects character
    references. ``create`` and ``prompt`` inject references only after a
    concrete target Skill has been selected. Multiple candidates always
    return ``selection-required`` instead of silently picking one.
    """

    if operation not in {"advise", "prompt", "create"}:
        raise ValueError("operation must be advise, prompt, or create")
    skill_dir = skill_dir.expanduser().resolve(strict=False)
    normalized_request = _normalize(request)
    if any(_contains(normalized_request, signal) for signal in GUIDE_SIGNALS):
        return _guide_result(request, operation, skill_dir)
    registry = load_dependency_registry(skill_dir / "references" / "skill-registry.json")
    dependencies: list[dict[str, Any]] = registry["dependencies"]
    category = detect_category(request)
    try:
        visual_style_selection = parse_visual_style_selection(request, skill_dir=skill_dir)
    except ValueError as error:
        return {
            **_empty_result(request, operation, category, reason=str(error)),
            "status": "invalid-visual-style",
        }
    if visual_style_selection is not None:
        category = category or ("ip-design" if visual_style_selection["library"] == "punk-avatar" else "cover-poster")
    photo_present = _has_photo_source_signal(request) if reference_photo is None else reference_photo
    if (
        operation in {"create", "prompt"}
        and category == "ip-design"
        and photo_present
        and visual_style_selection is None
        and not _has_excluded_personal_signal(request)
        and not _has_photo_workflow_choice(request)
    ):
        return _photo_workflow_choice_result(request, operation, category)
    explicit = _explicit_dependency(request, dependencies, category=category)
    named_explicit = explicit
    style_match = re.search(r"(?:手绘(?:风格库|风格|画风|库|风)?|handdraw\s+style)\s*[:：#]?\s*(\d{1,3})(?!\d)", normalized_request)
    style_number = int(style_match.group(1)) if style_match else None
    if visual_style_selection is not None and style_number is not None:
        return {
            **_empty_result(request, operation, category, reason="一次请求不能同时选择手绘编号与 PC、PA 编号"),
            "status": "incompatible-style-selection",
        }
    if style_number is not None and not 1 <= style_number <= 261:
        return {**_empty_result(request, operation, category, reason="手绘风格编号必须在 001–261 之间"), "status": "invalid-style"}
    if style_number is not None:
        method_dependencies = [item for item in dependencies if item["skill_id"] not in {"handdraw-style-prompter", "gpt-image-2-style-library"}]
        explicit = _explicit_dependency(request, method_dependencies, category=category) or explicit or "handdraw-style-prompter"
    if visual_style_selection is not None:
        if named_explicit is not None and named_explicit != visual_style_selection["library"]:
            return {
                **_empty_result(
                    request,
                    operation,
                    category,
                    reason=f"{visual_style_selection['code']} 只能用于 {visual_style_selection['library']}，不能与 {named_explicit} 混用",
                ),
                "status": "incompatible-style-selection",
            }
        explicit = visual_style_selection["library"]
    if explicit == "ian-xiaohei-scenes":
        category = "article-illustration"
    case_selection = parse_case_selection(request, skill_dir=skill_dir)

    # A case number on its own requests the installed prompt-enhancement
    # workflow. When a concrete design Skill is named, the case remains an
    # explicit enhancement layer for that target instead.
    if case_selection is not None and explicit is None:
        category = "prompt-enhancement"
        explicit = "gpt-image-2-style-library"

    if category is None and explicit is None:
        return _empty_result(
            request,
            operation,
            category,
            reason="IP Master only routes registered external Skills; no native fallback is available.",
        )

    if explicit:
        candidates = [item for item in dependencies if item["skill_id"] == explicit]
        if not candidates:
            return _empty_result(request, operation, category, reason=f"unregistered Skill: {explicit}")
        if explicit == PERSONAL_IP_SKILL_ID and _has_excluded_personal_signal(request):
            return {
                **_empty_result(
                    request,
                    operation,
                    category,
                    reason="personal-ip-image-pack is only for an authorised person's IP, not animals, mascots, or fictional roles",
                ),
                "status": "incompatible",
            }
        if not _supports_category(candidates[0], category):
            return {
                **_empty_result(request, operation, category, reason=f"{explicit} does not provide {category}"),
                "status": "incompatible",
                "candidates": [_dependency_report(candidates[0], skill_dir=skill_dir, dependency_root=dependency_root)],
            }
    else:
        candidates = [
            dependency
            for dependency in dependencies
            if category and category in dependency.get("categories", [])
        ]
        # Personal-photo creation is a distinct boundary. Animal, mascot,
        # and fictional-character requests must never silently enter that pack.
        if category == "ip-design":
            if _has_personal_signal(request) and not _has_excluded_personal_signal(request):
                candidates = [item for item in candidates if item["skill_id"] == PERSONAL_IP_SKILL_ID]
            else:
                candidates = [item for item in candidates if item["skill_id"] != PERSONAL_IP_SKILL_ID]

    candidates = _rank(request, candidates)
    reports = [
        _dependency_report(item, skill_dir=skill_dir, dependency_root=dependency_root)
        for item in candidates
    ]

    advice = operation == "advise" or any(_contains(_normalize(request), signal) for signal in ADVICE_SIGNALS)
    selected: dict[str, Any] | None = None
    if explicit and reports:
        selected = reports[0]
    elif len(reports) == 1:
        selected = reports[0]

    selection_required = not advice and selected is None and len(reports) > 1
    status = "advice" if advice else ("ready" if selected else ("selection-required" if selection_required else "unsupported"))
    character_inputs: list[dict[str, Any]] = []
    if selected is not None and not advice:
        character_inputs = resolve_character_inputs(request, skill_dir=skill_dir, project_dir=project_dir)

    selected_definition = next(
        (item for item in dependencies if selected and item["skill_id"] == selected["skill_id"]),
        None,
    )
    target_capability = (
        _target_capability(request, selected_definition, category)
        if selected_definition is not None
        else None
    )
    referenced_image_paths = [item["asset_path"] for item in character_inputs]
    reference_inputs = [
        {
            "role": "character_identity",
            "character_id": item["id"],
            "display_name": item["display_name"],
            "asset_path": item["asset_path"],
            "identity_reference_path": item["identity_reference_path"],
            "input_order": item["input_order"],
            "prompt_label": item["prompt_label"],
        }
        for item in character_inputs
    ]
    layout_categories = {"cover-poster", "slide-deck"}
    layout_selection = None
    if selected is not None and not advice and category in layout_categories:
        layout_selection = parse_layout_selection(request, skill_dir=skill_dir)
        if layout_selection is not None:
            reference_inputs.append(
                {
                    "role": "composition_method",
                    "layout_id": layout_selection["id"],
                    "display_name": f"布局 {layout_selection['number']} · {layout_selection['name']}",
                    "input_order": len(reference_inputs) + 1,
                    "prompt_label": layout_selection["prompt_label"],
                    "layout_method": layout_selection["layout_method"],
                    "generation_instruction": layout_selection["generation_instruction"],
                    "visual_isolation_constraint": layout_selection["visual_isolation_constraint"],
                }
            )
    if selected is not None and not advice and case_selection is not None:
        reference_inputs.append(
            {
                "role": "example_case_method",
                "case_id": case_selection["id"],
                "case_number": case_selection["number"],
                "display_name": f"案例 {case_selection['number']}",
                "input_order": len(reference_inputs) + 1,
                "prompt_label": case_selection["prompt_label"],
                "category": case_selection["category"],
                "source_url": case_selection["source_url"],
                "generation_instruction": case_selection["generation_instruction"],
                "visual_isolation_constraint": case_selection["visual_isolation_constraint"],
            }
        )
    layout_library = None
    if selected is not None and category in layout_categories:
        gallery_path = skill_dir / "assets" / "layout-library" / "index.html"
        layout_library = {
            "gallery_path": str(gallery_path.resolve()),
            "selection": layout_selection,
            "post_generation_delivery": category == "cover-poster" and selected.get("output_mode") != "prompt-only",
            "delivery_rule": (
                "Append the layout-library note only after a final raster image is confirmed portrait; "
                "never attach it to prompt-only output."
                if category == "cover-poster"
                else "For slide decks, use a selected layout only as a text method; do not append a portrait-raster delivery note."
            ),
        }
    case_library = None
    if case_selection is not None:
        case_library = {
            "gallery_path": case_selection["gallery_path"],
            "selection": case_selection,
            "mode": "prompt-only" if selected and selected["skill_id"] == "gpt-image-2-style-library" else "style-enhancement",
            "delivery_rule": "Treat the selected case as text-only visual direction; never add its remote image URL to model reference inputs.",
        }
    install_confirmation = bool(selected and selected["status"] != "installed")
    human_photo_workflow = bool(
        category == "ip-design"
        and photo_present
        and not _has_excluded_personal_signal(request)
    )
    composition_contract = {
        "method_skill_id": selected["skill_id"] if selected else None,
        "character_mode": "replace-default" if character_inputs else "no-injection",
        "character_instruction": (
            "指定 IP 替换目标 Skill 默认角色，并承担其核心动作。删除默认角色的名称、外形及参考图；只有用户明确要求同框才保留。"
            if character_inputs else "未明确指定角色，不注入牙仔或其他项目角色；目标 Skill 自带角色按其自身规则处理。"
        ),
        "style_override": None,
        "visual_style_override": None,
        "qa": ["指定 IP 是否替换默认角色", "角色是否承担核心动作", "画风是否符合选中风格而非原 Skill 默认画风"],
    }
    if visual_style_selection is not None and selected is not None:
        selection = visual_style_selection
        expected_skill = selection["library"]
        if selected["skill_id"] != expected_skill:
            return {
                **_empty_result(
                    request,
                    operation,
                    category,
                    reason=f"{selection['code']} 只能用于 {expected_skill}",
                ),
                "status": "incompatible-style-selection",
            }
        item = selection["item"]
        visual_instruction = (
            f"采用编号 {selection['code']} 的文本化视觉方法：{item['name']}。"
            + (
                f"设置 style={item['style']}。" if "style" in item else
                f"设置 mode={item['mode']}，palette={item['palette']}，layout={item['layout']}。"
            )
            + " 图册图片仅供浏览，不得作为模型参考图传入。"
        )
        visual_method = {
            "role": "visual_style_method",
            "style_code": selection["code"],
            "library": expected_skill,
            "display_name": f"{selection['code']} · {item['name']}",
            "input_order": len(reference_inputs) + 1,
            "generation_instruction": visual_instruction,
            "visual_isolation_constraint": "Do not add gallery screenshots or remote image URLs to model reference inputs.",
        }
        if "style" in item:
            visual_method["style"] = item["style"]
        else:
            visual_method["recipe"] = {key: item[key] for key in ("mode", "palette", "layout")}
        if item.get("requires_mode"):
            visual_method["required_parameters"] = ["mode"]
            visual_method["mode_options"] = ["before-after", "final-artwork"]
        reference_inputs.append(visual_method)
        composition_contract["visual_style_override"] = visual_method
    if style_number is not None:
        style_definition = next(item for item in dependencies if item["skill_id"] == "handdraw-style-prompter")
        style_dependency = _dependency_report(style_definition, skill_dir=skill_dir, dependency_root=None)
        composition_contract["style_override"] = {
            "skill_id": "handdraw-style-prompter",
            "number": f"{style_number:03d}",
            "dependency": style_dependency,
            "instruction": "读取该编号风格与实际模型的 resolve_reference.py 结果，按结果使用风格名、正向特征或参考图。显式风格接管媒介、笔触、配色和材质；移除目标 Skill 冲突的默认画风要求。保留其文章分析、隐喻、物理动作和输出用途。角色参考图只控制身份。",
        }
        if not style_dependency["available"]:
            install_confirmation = True
            status = "missing-style-dependency"
    return {
        "request": request,
        "operation": operation,
        "category": category,
        "status": status,
        "route_mode": "advice" if advice else ("external-skill" if selected else "selection"),
        "native_generation": False,
        "native_fallback": False,
        "selected_skill_id": selected["skill_id"] if selected else None,
        "target_skill_id": selected["skill_id"] if selected else None,
        "target_capability": target_capability,
        "selected_dependency": selected,
        "candidates": reports,
        "selection_required": selection_required,
        "style_selection_required": selection_required,
        "inject_characters": bool(character_inputs),
        "inject_character_references": bool(character_inputs),
        "characters": [item["id"] for item in character_inputs],
        "project_dir": str(project_dir.expanduser().resolve(strict=False)) if project_dir else None,
        "character_workflow": (
            {
                "mode": "human-photo-four-view-first" if _has_four_view_choice(request) else "human-photo-traits-first",
                "required_profile": ["name", "age", "height_cm", "weight_kg"] if _has_four_view_choice(request) else [],
                "requires_user_confirmation_before_registration": _has_four_view_choice(request),
                "annotate_profile_on_image": _has_four_view_choice(request),
            }
            if human_photo_workflow
            else None
        ),
        "character_inputs": character_inputs,
        "composition_contract": composition_contract,
        "referenced_image_paths": referenced_image_paths,
        "reference_inputs": reference_inputs,
        "installation_requested": False,
        "requires_install_confirmation": install_confirmation,
        "install_command": selected["install"]["command"] if selected else None,
        "generation_ready": bool(selected and not install_confirmation),
        "layout_library": layout_library,
        "case_library": case_library,
        "reason": (
            "IP Master routes and injects only; the selected external Skill owns generation."
            if selected
            else "Choose one registered external Skill before IP Master injects character references."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route an IP Master request to an external Skill")
    parser.add_argument("request")
    parser.add_argument("--operation", choices=("advise", "prompt", "create"), default="create")
    parser.add_argument("--skill-dir", type=Path, default=SKILL_DIR, help="IP Master Skill root")
    parser.add_argument("--dependency-root", type=Path, help="optional installed dependency root to probe first")
    parser.add_argument("--project-dir", type=Path, help="optional initialized IP project directory")
    parser.add_argument("--reference-photo", action="store_true", help="indicate an attached real-person reference photo")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        result = route(
            args.request,
            operation=args.operation,
            skill_dir=args.skill_dir,
            dependency_root=args.dependency_root,
            project_dir=args.project_dir,
            reference_photo=True if args.reference_photo else None,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"router error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"], result.get("selected_skill_id") or "")
    return 0 if result["status"] not in {"unsupported", "incompatible"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
