from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "ip-master"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import capability_router  # noqa: E402
import dependency_manager  # noqa: E402
import layout_library  # noqa: E402
import gpt_image_2_case_library  # noqa: E402
from character_router import (  # noqa: E402
    CharacterRegistryError,
    inspect_registry,
    resolve_character_inputs,
)
from register_character import CharacterRegistrationError, register_character  # noqa: E402


def _png_header(width: int, height: int) -> bytes:
    """Minimal PNG header sufficient for the dimension reader."""

    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + width.to_bytes(4, "big") + height.to_bytes(4, "big")


def test_character_registry_has_four_roles_and_yazai_default() -> None:
    report = inspect_registry(skill_dir=SKILL_ROOT)
    assert report["valid"] is True
    assert report["default_character"] == "yazai"
    assert [item["id"] for item in report["items"]] == ["yazai", "rongbao", "abao", "xiaomei"]


def test_advise_never_injects_or_requests_installation() -> None:
    result = capability_router.route("用牙仔做知识漫画", operation="advise")
    assert result["status"] == "advice"
    assert result["target_skill_id"] == "baoyu-comic"
    assert result["character_inputs"] == []
    assert result["referenced_image_paths"] == []
    assert result["inject_character_references"] is False
    assert result["installation_requested"] is False
    assert result["route_mode"] == "advice"


def test_help_request_returns_local_guide_without_routing_or_injection() -> None:
    for request in ("我是第一次用，怎么用 IP Master？", "帮助"):
        result = capability_router.route(request, operation="create")
        assert result["status"] == "guide"
        assert result["route_mode"] == "guide"
        assert result["guide_page"]["relative_path"] == "assets/readme/index.html"
        assert result["guide_page"]["display_surface"] == "browser"
        assert result["guide_page"]["browser_url"].startswith("file:///")
        assert Path(result["guide_page"]["path"]).is_file()
        assert result["selected_skill_id"] is None
        assert result["character_inputs"] == []
        assert result["referenced_image_paths"] == []


def test_guide_html_shows_readme_cases_and_links_local_libraries() -> None:
    guide = SKILL_ROOT / "assets" / "readme" / "index.html"
    html = guide.read_text(encoding="utf-8")
    assert "navigator.clipboard.writeText" in html
    assert "@media (max-width:820px)" in html
    assert "object-fit:cover" not in html
    assert html.count("object-fit:contain") >= 2
    assert html.count('data-copy="') >= 17
    image_sources = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert len(image_sources) == 23
    for source in image_sources:
        if source.startswith("https://"):
            assert source.startswith("https://raw.githubusercontent.com/")
        else:
            assert (guide.parent / source).resolve().is_file()

    for source in (
        "../showcase/baoyu-comic.webp",
        "../../../comic/silver-short/01-cover-silver-energetic-manga-standard-color.png",
        "../generated/yazai-silver-market-framework.png",
        "../generated/ai-agent-corporate-memphis-fishbone.png",
        "../showcase/layout-08-front-back-case.png",
        "../generated/dongfang-posters/yazai-hangzhou-street-case-495.png",
    ):
        assert source in image_sources

    links = re.findall(r'href="([^"]+)"', html)
    for href in (
        "../layout-library/index.html",
        "../gpt-image-2-case-library/index.html",
        "../baoyu-skill-library/index.html",
    ):
        assert href in links
        assert (guide.parent / href).resolve().is_file()
        assert re.search(
            rf'href="{re.escape(href)}" target="_blank" rel="noopener"', html
        )

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    routing = (SKILL_ROOT / "references" / "capability-routing.md").read_text(encoding="utf-8")
    for document in (readme, skill, routing):
        assert "assets/readme/index.html" in document


def test_multiple_article_candidates_require_selection_without_native_fallback() -> None:
    result = capability_router.route("用牙仔做一套文章配图", operation="create")
    assert result["status"] == "selection-required"
    assert result["selection_required"] is True
    assert result["selected_skill_id"] is None
    assert result["character_inputs"] == []
    assert result["native_generation"] is False
    assert result["native_fallback"] is False
    assert {item["skill_id"] for item in result["candidates"]} == {
        "ian-xiaohei-illustrations",
        "ian-xiaohei-scenes",
        "baoyu-article-illustrator",
        "ip-illustration-character-system",
    }


def test_ian_xiaohei_scenes_is_explicitly_routable() -> None:
    result = capability_router.route(
        "用 ian-xiaohei-scenes 做小黑实物场景图", operation="create"
    )
    assert result["status"] == "ready"
    assert result["target_skill_id"] == "ian-xiaohei-scenes"
    assert result["characters"] == ["yazai"]


def test_everett_capabilities_are_discoverable_without_becoming_default() -> None:
    article = capability_router.route("文章配图有哪些 Skill，不要生图", operation="advise")
    assert article["status"] == "advice"
    assert "ip-illustration-character-system" in {
        item["skill_id"] for item in article["candidates"]
    }

    sticker = capability_router.route("用牙仔做贴纸页", operation="create")
    assert sticker["target_skill_id"] == "ip-illustration-character-system"
    assert sticker["characters"] == ["yazai"]


def test_selected_external_skill_injects_default_and_named_roles_in_registry_order() -> None:
    default_result = capability_router.route("用 baoyu-comic 做知识漫画", operation="create")
    assert default_result["status"] == "ready"
    assert default_result["target_skill_id"] == "baoyu-comic"
    assert default_result["characters"] == ["yazai"]
    assert [Path(path).name for path in default_result["referenced_image_paths"]] == ["yazai.webp"]

    multi_result = capability_router.route(
        "用小美和绒宝让 baoyu-comic 做一套知识漫画", operation="create"
    )
    assert multi_result["target_skill_id"] == "baoyu-comic"
    assert multi_result["characters"] == ["rongbao", "xiaomei"]
    assert [Path(path).name for path in multi_result["referenced_image_paths"]] == [
        "rongbao.webp",
        "xiaomei.webp",
    ]
    assert [item["input_order"] for item in multi_result["reference_inputs"]] == [1, 2]


def test_layout_library_returns_composition_methods_without_thumbnail_image_inputs() -> None:
    report = layout_library.validate_library(skill_dir=SKILL_ROOT)
    assert report["valid"] is True
    assert report["count"] == 100
    assert report["blueprint_count"] == 100

    selected = [
        layout_library.parse_layout_selection(value, skill_dir=SKILL_ROOT)
        for value in ("用 23 重新排版", "用 023 重新排版", "layout-023")
    ]
    assert {item["id"] for item in selected if item is not None} == {"layout-023"}
    assert all("asset_path" not in item for item in selected if item is not None)

    layout_eight = layout_library.parse_layout_selection("排版用08", skill_dir=SKILL_ROOT)
    assert layout_eight is not None
    assert layout_eight["layout_method"]["layout_principle"] == "前后构图"
    instruction = layout_eight["generation_instruction"]
    assert all(term in instruction for term in ("前景", "中景", "背景", "遮挡", "尺度", "纵深"))
    assert "左侧上至中部" not in instruction
    assert "右下主体" not in instruction
    assert "不得复用布局样图的配色、几何装饰" not in instruction
    assert "不复制示例画面的坐标、配色、几何装饰" in instruction

    with pytest.raises(ValueError, match="unknown layout number"):
        layout_library.parse_layout_selection("用 101 重新排版", skill_dir=SKILL_ROOT)

    routed = capability_router.route(
        "用 dongfang 做一张竖版海报，用 23 重新排版", operation="create"
    )
    assert routed["layout_library"]["selection"]["id"] == "layout-023"
    assert routed["reference_inputs"][-1]["role"] == "composition_method"
    assert "asset_path" not in routed["reference_inputs"][-1]
    assert routed["reference_inputs"][-1]["layout_method"]["layout_principle"] == "Z形构图"
    assert "layout-023.jpg" not in routed["referenced_image_paths"]
    assert all("layout-" not in Path(path).name for path in routed["referenced_image_paths"])
    assert "不复制示例画面的坐标、配色、几何装饰" in routed["reference_inputs"][-1]["generation_instruction"]

    first_pass = capability_router.route("用 dongfang 做一张竖版海报", operation="create")
    assert first_pass["layout_library"]["selection"] is None
    assert all(item["role"] != "layout_reference" for item in first_pass["reference_inputs"])

    prompt_only = capability_router.route("用 gbro 做一张 3:4 封面", operation="create")
    assert prompt_only["layout_library"]["post_generation_delivery"] is False


def test_layout_delivery_note_only_applies_to_final_portrait_raster(tmp_path: Path) -> None:
    portrait = tmp_path / "portrait.png"
    portrait.write_bytes(_png_header(600, 900))
    landscape = tmp_path / "landscape.png"
    landscape.write_bytes(_png_header(900, 600))

    eligible = layout_library.portrait_delivery_note(portrait, skill_dir=SKILL_ROOT)
    assert eligible["eligible"] is True
    assert "回复编号（如：23）" in eligible["message"]
    assert eligible["gallery_path"].endswith("layout-library\\index.html")

    assert layout_library.portrait_delivery_note(landscape, skill_dir=SKILL_ROOT)["eligible"] is False
    assert layout_library.portrait_delivery_note(
        portrait, skill_dir=SKILL_ROOT, prompt_only=True
    )["reason"] == "prompt-only output"


def test_gpt_image_2_case_library_is_source_linked_and_text_only() -> None:
    report = gpt_image_2_case_library.validate_library(skill_dir=SKILL_ROOT)
    assert report["valid"] is True
    assert report["count"] == 541
    assert report["category_count"] == 13
    assert report["missing_case_numbers"] == [12, 169, 170]

    selected = gpt_image_2_case_library.parse_case_selection("用案例 539 设计", skill_dir=SKILL_ROOT)
    assert selected is not None
    assert selected["id"] == "case-539"
    assert selected["prompt"]
    assert selected["image_url"].startswith("https://raw.githubusercontent.com/freestylefly/")
    assert "不能作为模型输入" in selected["visual_isolation_constraint"]
    with pytest.raises(ValueError, match="unknown case number"):
        gpt_image_2_case_library.parse_case_selection("案例 12", skill_dir=SKILL_ROOT)


def test_case_selection_routes_to_prompt_or_existing_target_without_image_input() -> None:
    prompt = capability_router.route("用案例 539 设计一张 AI 海报", operation="prompt")
    assert prompt["target_skill_id"] == "gpt-image-2-style-library"
    assert prompt["case_library"]["mode"] == "prompt-only"
    assert prompt["reference_inputs"][-1]["role"] == "example_case_method"
    assert "image_url" not in prompt["reference_inputs"][-1]

    enhanced = capability_router.route(
        "用牙仔和 dongfang 做一张竖版海报，案例 539", operation="create"
    )
    assert enhanced["target_skill_id"] == "dongfang-cover-design"
    assert enhanced["case_library"]["mode"] == "style-enhancement"
    assert enhanced["reference_inputs"][-1]["case_id"] == "case-539"
    assert all("case539" not in Path(path).name for path in enhanced["referenced_image_paths"])

    first_pass = capability_router.route("用 dongfang 做一张竖版海报", operation="create")
    assert first_pass["case_library"] is None
    assert all(item["role"] != "example_case_method" for item in first_pass["reference_inputs"])


def test_personal_photo_boundary_and_animal_exclusion() -> None:
    personal = capability_router.route("用 personal-ip-image-pack 做真人照片 IP", operation="create")
    assert personal["target_skill_id"] == "personal-ip-image-pack"
    assert personal["category"] == "ip-design"

    animal = capability_router.route("用 personal-ip-image-pack 做动物 IP", operation="create")
    assert animal["status"] == "incompatible"
    assert animal["native_fallback"] is False

    generic_animal = capability_router.route("设计动物 IP", operation="create")
    assert generic_animal["status"] == "unsupported"
    assert generic_animal["target_skill_id"] is None


def test_dependency_manager_is_read_only_and_emits_exact_install_plan() -> None:
    plan = dependency_manager.installation_plan("personal-ip-image-pack", skill_dir=SKILL_ROOT)
    assert plan["repo"] == "DoraRabbitYan/personal-ip-image-pack"
    assert plan["path"] == "."
    assert plan["install_name"] == "personal-ip-image-pack"
    assert plan["install"]["args"] == [
        "--repo",
        "DoraRabbitYan/personal-ip-image-pack",
        "--path",
        ".",
        "--name",
        "personal-ip-image-pack",
        "--ref",
        "main",
    ]

    with pytest.raises(dependency_manager.UnknownDependencyError):
        dependency_manager.get_dependency("not-registered", skill_dir=SKILL_ROOT)


def test_register_character_requires_confirmation_and_uses_characters_asset_dir(tmp_path: Path) -> None:
    temporary_skill = tmp_path / "skill"
    shutil.copytree(SKILL_ROOT, temporary_skill)
    prototype = SKILL_ROOT / "assets" / "characters" / "xiaomei.webp"

    with pytest.raises(CharacterRegistrationError, match="explicit confirmation"):
        register_character(
            "newrole",
            "新角",
            ["新角", "newrole"],
            prototype,
            skill_dir=temporary_skill,
        )

    result = register_character(
        "newrole",
        "新角",
        ["新角", "newrole"],
        prototype,
        skill_dir=temporary_skill,
        identity_text="# 新角身份协议\n\n- 保持轮廓。\n",
        confirm=True,
    )
    assert result["registered"] is True
    assert (temporary_skill / "assets" / "characters" / "newrole.webp").is_file()
    registry = json.loads(
        (temporary_skill / "references" / "character-registry.json").read_text(encoding="utf-8")
    )
    record = next(item for item in registry["characters"] if item["id"] == "newrole")
    assert record["asset"] == "assets/characters/newrole.webp"
    assert record["identity_reference"] == "references/newrole-identity.md"
    assert resolve_character_inputs("用新角做图", skill_dir=temporary_skill)[0]["id"] == "newrole"
