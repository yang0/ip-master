from __future__ import annotations

import json
import re
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
from ip_project import initialize_project  # noqa: E402
from annotate_four_view import annotate_four_view  # noqa: E402


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
    assert "当前图片只是示例，不代表全部选项" in html
    case_blocks = re.findall(r'<article class="case">.*?</article>', html, flags=re.DOTALL)
    assert len(case_blocks) == 12
    assert all('class="coverage"' in block for block in case_blocks)
    for coverage in (
        "5 个漫画预设",
        "7 种版式",
        "7 种情绪色调",
        "23 种细分风格",
        "7 个核心风格入口",
        "26 个风格预设",
        "7 种渲染媒介",
        "22 种视觉风格",
        "12 种基础风格",
        "26 个小红书预设",
        "17 种幻灯片视觉风格",
        "10 种 3:4 构图风格",
        "1 套白底怪诞手绘风",
        "1 套真实物件互动风",
        "6 类视觉方向",
        "2 套主视觉系统",
    ):
        assert coverage in html
    image_sources = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert len(image_sources) == 21
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
    assert "350-layout-compositions" in readme
    assert "100-layout-compositions" not in readme
    assert "前后构图" not in readme
    assert "350 种视觉布局库" in html


def test_visual_libraries_have_a_working_home_link() -> None:
    for relative_path in (
        "assets/layout-library/index.html",
        "assets/gpt-image-2-case-library/index.html",
        "assets/baoyu-skill-library/index.html",
    ):
        page = SKILL_ROOT / relative_path
        html = page.read_text(encoding="utf-8")
        assert 'href="../readme/index.html"' in html
        assert "返回首页" in html
        assert (page.parent / "../readme/index.html").resolve().is_file()


def test_vsc_design_skills_are_registered_and_ip_injectable() -> None:
    registry = json.loads((SKILL_ROOT / "references" / "skill-registry.json").read_text(encoding="utf-8"))
    items = {item["skill_id"]: item for item in registry["dependencies"]}
    assert set(("vibeshot-candid-photography", "virtual-couple-travel-vlog")).issubset(items)
    assert "shan-ze-school" not in items
    for skill_id in ("vibeshot-candid-photography", "virtual-couple-travel-vlog"):
        item = items[skill_id]
        assert item["repo"] == "vibeshotclub/vsc-skills"
        assert item["ref"] == "3c33b43e770e4ecd0084fe4adfbd7a637494fa02"
        assert item["skill_type"] == "design-skill"
        assert item["ip_injection"] == "supported"

    candid = capability_router.route("使用 vibeshot-candid-photography，用牙仔生成真实抓拍人像", operation="create")
    assert candid["target_skill_id"] == "vibeshot-candid-photography"
    assert candid["category"] == "portrait"
    assert candid["characters"] == ["yazai"]
    assert candid["selected_dependency"]["skill_type"] == "design-skill"
    assert candid["selected_dependency"]["ip_injection"] == "supported"

    couple = capability_router.route("用 virtual-couple-travel-vlog，把阿龅放进杭州情侣旅行 Vlog", operation="create")
    assert couple["target_skill_id"] == "virtual-couple-travel-vlog"
    assert couple["category"] == "video-workflow"
    assert couple["characters"] == ["abao"]
    assert couple["referenced_image_paths"]

    ordinary = capability_router.route("用牙仔做一张海报，主题是杭州街头", operation="create")
    assert ordinary["target_skill_id"] != "vibeshot-candid-photography"
    assert ordinary["target_skill_id"] != "virtual-couple-travel-vlog"

    human_photo = capability_router.route("用上传的真人照片设计人物 IP", operation="create")
    assert human_photo["status"] == "photo-workflow-choice"
    assert human_photo["clarification_required"] is True
    assert human_photo["character_inputs"] == []
    assert len(human_photo["clarification"]["options"]) == 2

    four_view = capability_router.route("用上传的真人照片先生成四视图，再设计人物 IP", operation="create")
    assert four_view["status"] in {"ready", "selection-required"}
    assert four_view["character_workflow"]["mode"] == "human-photo-four-view-first"
    assert four_view["character_workflow"]["required_profile"] == ["name", "age", "height_cm", "weight_kg"]

    trait_based = capability_router.route("基于上传照片提取脸部特征设计人物 IP", operation="create")
    assert trait_based["status"] in {"ready", "selection-required"}
    assert trait_based["character_workflow"]["mode"] == "human-photo-traits-first"
    assert trait_based["character_workflow"]["requires_user_confirmation_before_registration"] is False


def test_vsc_library_page_and_assets_exist() -> None:
    page = SKILL_ROOT / "assets" / "vsc-skill-library" / "index.html"
    html = page.read_text(encoding="utf-8")
    assert "真实抓拍人像" in html
    assert "虚拟情侣旅行 Vlog" in html
    assert "vsc-candid-photography-demo.png" in html
    assert "vsc-couple-travel-vlog-demo.png" in html
    assert "navigator.clipboard.writeText" in html
    assert "target=\"_blank\" rel=\"noopener\"" in html
    assert 'href="../readme/index.html"' in html
    for source in re.findall(r'<img[^>]+src="([^"]+)"', html):
        assert (page.parent / source).resolve().is_file()
    for prompt in (
        "vsc-candid-photography-demo.md",
        "vsc-couple-travel-vlog-demo.md",
    ):
        assert (PROJECT_ROOT / "prompts" / prompt).is_file()
    guide = (SKILL_ROOT / "assets" / "readme" / "index.html").read_text(encoding="utf-8")
    assert "../vsc-skill-library/index.html" in guide
    assert "VSC 视觉设计 Skill 图册" in guide
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "VSC Candid Photography" in readme
    assert "VSC Virtual Couple Travel Vlog" in readme
    assert "ip-master/assets/showcase/vsc-candid-photography-demo.png" in readme
    assert "ip-master/assets/showcase/vsc-couple-travel-vlog-demo.png" in readme


def test_layout_gallery_uses_verified_local_image_bindings() -> None:
    library = SKILL_ROOT / "assets" / "layout-library"
    html = (library / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((library / "manifest.json").read_text(encoding="utf-8"))
    commit = manifest["upstream"]["commit"]
    assert manifest["upstream"]["asset_kind"] == "locally cloned thumbnail snapshot; source paths retained"
    assert "image_url" in html
    assert "image-bindings.json" in html or "images/layout-001.jpg" in html
    assert f"https://raw.githubusercontent.com/nevertoday/350-layout-compositions/{commit}/v2/images/" in html
    assert "image.src = item.image_url" in html
    assert "image.src = item.thumbnail;" not in html
    assert 'href="../readme/index.html"' in html
    assert "返回首页" in html
    assert "const categories" in html
    assert "构图逻辑" in html
    assert "演示文稿页面" in html
    assert not (library / "thumbnails").exists()
    assert len(list((library / "images").glob("*.jpg"))) == 350
    assert manifest["layouts"][20]["name"] == "水平构图"
    assert manifest["layouts"][20]["source_number"] == "051"
    assert "object-fit:contain" in html


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
    assert report["count"] == 350
    assert report["blueprint_count"] == 350
    assert report["translation_rule_count"] == 33
    assert report["category_count"] == 8
    assert report["subcategory_count"] == 33
    assert not (SKILL_ROOT / "assets" / "layout-library" / "thumbnails").exists()

    selected = [
        layout_library.parse_layout_selection(value, skill_dir=SKILL_ROOT)
        for value in ("用 1 重新排版", "用 001 重新排版", "layout-001")
    ]
    assert {item["id"] for item in selected if item is not None} == {"layout-001"}
    assert all("asset_path" not in item for item in selected if item is not None)

    layout_eight = layout_library.parse_layout_selection("排版用08", skill_dir=SKILL_ROOT)
    assert layout_eight is not None
    assert layout_eight["layout_method"]["layout_principle"] == "空间法则构图"
    instruction = layout_eight["generation_instruction"]
    assert "空间法则构图" in instruction
    assert "经典法则与空间留白" in instruction
    assert "不复制示例画面的坐标、配色、几何装饰" in instruction

    with pytest.raises(ValueError, match="unknown layout number"):
        layout_library.parse_layout_selection("用 351 重新排版", skill_dir=SKILL_ROOT)

    routed = capability_router.route(
        "用 dongfang 做一张竖版海报，用 008 重新排版", operation="create"
    )
    assert routed["layout_library"]["selection"]["id"] == "layout-008"
    assert routed["reference_inputs"][-1]["role"] == "composition_method"
    assert "asset_path" not in routed["reference_inputs"][-1]
    assert routed["reference_inputs"][-1]["layout_method"]["layout_principle"] == "空间法则构图"
    assert "layout-008.jpg" not in routed["referenced_image_paths"]
    assert all("layout-" not in Path(path).name for path in routed["referenced_image_paths"])
    assert "不复制示例画面的坐标、配色、几何装饰" in routed["reference_inputs"][-1]["generation_instruction"]

    first_pass = capability_router.route("用 dongfang 做一张竖版海报", operation="create")
    assert first_pass["layout_library"]["selection"] is None
    assert all(item["role"] != "layout_reference" for item in first_pass["reference_inputs"])

    prompt_only = capability_router.route("用 gbro 做一张 3:4 封面", operation="create")
    assert prompt_only["layout_library"]["post_generation_delivery"] is False

    slide_deck = capability_router.route("做 PPT，主题：杭州景点，用 341 做 PPT", operation="create")
    assert slide_deck["target_skill_id"] == "baoyu-slide-deck"
    assert slide_deck["layout_library"]["selection"]["id"] == "layout-341"
    assert slide_deck["reference_inputs"][-1]["role"] == "composition_method"
    assert slide_deck["layout_library"]["post_generation_delivery"] is False


def test_layout_delivery_note_only_applies_to_final_portrait_raster(tmp_path: Path) -> None:
    portrait = tmp_path / "portrait.png"
    portrait.write_bytes(_png_header(600, 900))
    landscape = tmp_path / "landscape.png"
    landscape.write_bytes(_png_header(900, 600))

    eligible = layout_library.portrait_delivery_note(portrait, skill_dir=SKILL_ROOT)
    assert eligible["eligible"] is True
    assert "回复编号（如：008）" in eligible["message"]
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
    assert personal["status"] == "photo-workflow-choice"
    assert personal["target_skill_id"] is None
    assert personal["category"] == "ip-design"

    explicit_personal = capability_router.route(
        "用 personal-ip-image-pack 基于真人照片特征设计人物 IP", operation="create"
    )
    assert explicit_personal["target_skill_id"] == "personal-ip-image-pack"
    assert explicit_personal["category"] == "ip-design"

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


def test_project_character_registration_stays_outside_skill_and_builds_gallery(tmp_path: Path) -> None:
    project_dir = tmp_path / "brand-ip"
    initialized = initialize_project(project_dir, name="品牌 IP")
    assert initialized["initialized"] is True
    assert (project_dir / "ip-master-project.json").is_file()
    assert (project_dir / "index.html").is_file()
    prototype = SKILL_ROOT / "assets" / "characters" / "xiaomei.webp"

    with pytest.raises(CharacterRegistrationError, match="project directory is required"):
        register_character("newrole", "新角", ["新角", "newrole"], prototype, confirm=True, age=45, height_cm=156, weight_kg=55)

    with pytest.raises(CharacterRegistrationError, match="explicit confirmation"):
        register_character(
            "newrole",
            "新角",
            ["新角", "newrole"],
            prototype,
            project_dir=project_dir,
        )

    result = register_character(
        "newrole",
        "新角",
        ["新角", "newrole"],
        prototype,
        project_dir=project_dir,
        age=45,
        height_cm=156,
        weight_kg=55,
        identity_text="# 新角身份协议\n\n- 保持轮廓。\n",
        confirm=True,
    )
    assert result["registered"] is True
    assert result["open_gallery"] is True
    assert result["gallery_url"].startswith("file:///")
    assert Path(result["gallery_path"]).is_file()
    assert (project_dir / "characters" / "assets" / "newrole.webp").is_file()
    assert not (SKILL_ROOT / "assets" / "characters" / "newrole.webp").exists()
    registry = json.loads(
        (project_dir / "characters" / "registry.json").read_text(encoding="utf-8")
    )
    record = next(item for item in registry["characters"] if item["id"] == "newrole")
    assert record["asset"] == "characters/assets/newrole.webp"
    assert record["identity_reference"] == "characters/identities/newrole.md"
    resolved = resolve_character_inputs("用新角做图", skill_dir=SKILL_ROOT, project_dir=project_dir)
    assert resolved[0]["id"] == "newrole"
    assert resolved[0]["source"] == "project"
    assert resolve_character_inputs("做图", skill_dir=SKILL_ROOT, project_dir=project_dir)[0]["id"] == "yazai"
    gallery = (project_dir / "index.html").read_text(encoding="utf-8")
    assert "新角" in gallery
    assert "yazai.webp" not in gallery
    assert "navigator.clipboard.writeText" in gallery
    assert "@media(max-width:760px)" in gallery

    routed = capability_router.route(
        "用新角做知识漫画", operation="create", skill_dir=SKILL_ROOT, project_dir=project_dir
    )
    assert routed["characters"] == ["newrole"]
    assert Path(routed["referenced_image_paths"][0]).parent == project_dir / "characters" / "assets"

    with pytest.raises(CharacterRegistrationError, match="built-in"):
        register_character(
            "another-role", "另一角", ["牙仔", "another-role"], prototype,
            project_dir=project_dir, confirm=True, age=45, height_cm=156, weight_kg=55,
        )


def test_four_view_annotation_adds_identity_strip_without_overwriting_source(tmp_path: Path) -> None:
    from PIL import Image

    source = tmp_path / "four-view.png"
    Image.new("RGB", (200, 200), "white").save(source)
    source_size = source.stat().st_size
    destination = tmp_path / "annotated" / "xue.png"
    annotate_four_view(source, destination, name="xue", age=45, height_cm=156, weight_kg=55)
    assert source.stat().st_size == source_size
    with Image.open(destination) as annotated:
        assert annotated.size[0] == 200
        assert annotated.size[1] > 200
