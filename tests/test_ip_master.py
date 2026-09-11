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
import baoyu_skill_library  # noqa: E402
import visual_style_library  # noqa: E402
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


def test_embedded_visual_libraries_do_not_repeat_home_navigation() -> None:
    for relative_path in (
        "assets/layout-library/index.html",
        "assets/gpt-image-2-case-library/index.html",
        "assets/vsc-skill-library/index.html",
    ):
        page = SKILL_ROOT / relative_path
        html = page.read_text(encoding="utf-8")
        assert 'href="../readme/index.html"' not in html
        assert "返回首页" not in html


def test_baoyu_parameter_gallery_is_browse_only_with_fillable_templates() -> None:
    report = baoyu_skill_library.validate_library(skill_dir=SKILL_ROOT)
    assert report["valid"] is True
    assert report["count"] == 124
    assert report["group_count"] == 9

    html = (SKILL_ROOT / "assets" / "baoyu-skill-library" / "index.html").read_text(encoding="utf-8")
    assert "首屏浮动" not in html
    assert "不是最终成片示范" in html
    assert "展开参数说明" in html
    assert "参数说明" in html and "马卡龙" in html and "清线" in html
    assert "使用 baoyu skill 设计小红书图文" in html
    assert "value('layout')" in html and "palette=待填写" in html
    assert "preview-dialog" in html and "data-preview" in html
    assert 'href="${esc(s.source_url)}"' not in html
    assert "复制编号调用" not in html
    assert "B001" not in html and "B124" not in html
    assert "https://raw.githubusercontent.com/JimLiu/baoyu-skills/55223daf5c7c21ce6343935f138fcbe33d683000/screenshots/" in html
    assert 'href="../readme/index.html"' in html

    title_link_script = (SKILL_ROOT / "assets" / "github-title-link.js").read_text(encoding="utf-8")
    assert "library === 'baoyu-skill-library'" in title_link_script
    assert "document.querySelector('.top')?.remove()" in title_link_script

    routed = capability_router.route("用 baoyu-infographic 做信息图", operation="create")
    assert routed["target_skill_id"] == "baoyu-infographic"
    assert all(item["role"] != "baoyu_parameter_method" for item in routed["reference_inputs"])


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


def test_couple_photo_workflow_is_registered_and_explicitly_routed() -> None:
    registry = json.loads((SKILL_ROOT / "references" / "skill-registry.json").read_text(encoding="utf-8"))
    items = {item["skill_id"]: item for item in registry["dependencies"]}
    expected = {
        "couple-photo-requirements-planner": "skills/kefu",
        "couple-photo-shooting-planner": "skills/paishe",
        "couple-photo-wardrobe-board": "skills/huanzhuang",
        "couple-photo-orchestrator": "skills/zongkong",
    }
    for skill_id, path in expected.items():
        assert skill_id in items
        assert items[skill_id]["repo"] == "yang0/couple-photo"
        assert items[skill_id]["path"] == path
        assert items[skill_id]["ref"] == "5b15ba756798ba4f08faf9c8907ce8f68ef66055"
    assert items["couple-photo-orchestrator"]["workflow_entry"] == "primary"

    orchestrated = capability_router.route("我想拍一组情侣照", operation="create")
    assert orchestrated["target_skill_id"] == "couple-photo-orchestrator"
    assert orchestrated["category"] == "couple-photo"
    wedding = capability_router.route("我想拍婚纱照", operation="create")
    assert wedding["target_skill_id"] == "couple-photo-orchestrator"
    wardrobe = capability_router.route("情侣换装", operation="create")
    assert wardrobe["target_skill_id"] == "couple-photo-wardrobe-board"
    shooting = capability_router.route("情侣照拍摄规划", operation="create")
    assert shooting["target_skill_id"] == "couple-photo-shooting-planner"
    ordinary = capability_router.route("制作一张人物写真", operation="create")
    assert not str(ordinary.get("target_skill_id") or "").startswith("couple-photo-")


def test_couple_photo_library_page_uses_remote_readme_examples() -> None:
    page = SKILL_ROOT / "assets" / "couple-photo-library" / "index.html"
    html = page.read_text(encoding="utf-8")
    assert "Couple Photo 情侣照工作流" in html
    assert html.count("raw.githubusercontent.com/yang0/couple-photo/5b15ba756798ba4f08faf9c8907ce8f68ef66055/docs/assets/readme/") == 4
    assert "reference-female.png" in html and "reference-male.png" in html
    assert html.count("class=\"copy\"") == 2
    assert html.count("使用 couple-photo-orchestrator") == 2
    assert "选择绝对项目目录" in html
    assert "需求确认" in html and "2×4 宫格" in html and "选编号精修" in html
    assert 'href="https://github.com/yang0/couple-photo"' in html
    assert 'target="_blank" rel="noopener"' in html
    assert "navigator.clipboard.writeText" in html and "window.prompt" in html


def test_visual_skill_hub_includes_couple_photo_gallery() -> None:
    hub = (SKILL_ROOT / "assets" / "visual-skill-hub" / "index.html").read_text(encoding="utf-8")
    assert "Couple Photo 情侣照" in hub
    assert "../couple-photo-library/index.html" in hub
    assert "4 阶段" in hub


def test_handdraw_style_skill_is_registered_and_explicitly_routed() -> None:
    registry = json.loads((SKILL_ROOT / "references" / "skill-registry.json").read_text(encoding="utf-8"))
    items = {item["skill_id"]: item for item in registry["dependencies"]}
    item = items["handdraw-style-prompter"]
    assert item["repo"] == "yang0/handraw-style"
    assert item["path"] == "."
    assert item["ref"] == "58dee6151874c6fc381e6a0d97430f1c275c1696"
    assert item["style_count"] == 261
    assert item["skill_type"] == "design-skill"
    assert item["ip_injection"] == "supported"

    by_name = capability_router.route(
        "使用 handdraw-style-prompter，用牙仔做 041 号手绘风格海报，主题：秋天的第一杯奶茶",
        operation="prompt",
    )
    assert by_name["target_skill_id"] == "handdraw-style-prompter"
    assert by_name["target_capability"] == "numbered-hand-drawn-style"
    assert by_name["characters"] == ["yazai"]

    by_alias = capability_router.route("041号手绘风格，主题：秋天的第一杯奶茶", operation="prompt")
    assert by_alias["target_skill_id"] == "handdraw-style-prompter"
    assert by_alias["target_capability"] == "numbered-hand-drawn-style"

    ordinary = capability_router.route("用牙仔做一张海报，主题是杭州街头", operation="create")
    assert ordinary["target_skill_id"] != "handdraw-style-prompter"


def test_mono_readme_gallery_and_punk_numbered_visual_libraries() -> None:
    manifest = visual_style_library.load_manifest(skill_dir=SKILL_ROOT)
    libraries = manifest["libraries"]
    assert [item["code"] for item in libraries["punk-cover"]["items"]] == [f"PC{i:02d}" for i in range(1, 32)]
    assert [item["code"] for item in libraries["punk-avatar"]["items"]] == [f"PA{i:02d}" for i in range(1, 8)]
    assert libraries["punk-cover"]["ref"] == "bda2d0fd535d764c53cf6795e1003553a54da9d9"

    cover = capability_router.route("用 PC08 做封面", operation="create")
    avatar = capability_router.route("用 PA04 做人物头像", operation="create")
    paper = capability_router.route("用 PA07 做人物头像", operation="create")
    assert cover["target_skill_id"] == "punk-cover"
    assert avatar["target_skill_id"] == "punk-avatar"
    assert cover["composition_contract"]["visual_style_override"]["style"] == "layered-paper-cut-concept-poster"
    assert avatar["composition_contract"]["visual_style_override"]["style"] == "fashion-sketch-observation"
    assert paper["composition_contract"]["visual_style_override"]["required_parameters"] == ["mode"]
    for result in (cover, avatar):
        assert result["referenced_image_paths"] == []
        assert result["reference_inputs"][-1]["role"] == "visual_style_method"

    assert capability_router.route("用 PC99 做封面")["status"] == "invalid-visual-style"
    assert capability_router.route("用 PC08 和 PC09 做封面")["status"] == "invalid-visual-style"
    assert capability_router.route("用 PA04 做封面")["status"] == "incompatible"
    legacy_mono = capability_router.route("用 MC03 做海报")
    assert legacy_mono["selected_skill_id"] != "mono-color"
    natural_mono = capability_router.route("使用 mono-color-skill 做单色海报", operation="create")
    assert natural_mono["target_skill_id"] == "mono-color"

    mono_page = (SKILL_ROOT / "assets" / "mono-color-library" / "index.html").read_text(encoding="utf-8")
    punk_page = (SKILL_ROOT / "assets" / "punk-skill-library" / "index.html").read_text(encoding="utf-8")
    assert "MC01" not in mono_page and "recipe=" not in mono_page
    assert "navigator.clipboard.writeText" in mono_page and "dialog.showModal()" in mono_page
    assert mono_page.count('class="copy"') == 4
    assert mono_page.count("使用 mono-color-skill") == 4
    assert mono_page.count("https://raw.githubusercontent.com/yanliudesign/mono-color-skill/") == 1
    for filename in (
        "example-cycling.png", "example-zebra.png", "example-chair.png", "example-sardines.png",
        "example-headphones.png", "example-sunscreen.png", "example-teapot.png", "example-merchandise.png",
        "example-tea.png", "example-night-photography.png", "example-radio.png", "example-night-market.png",
    ):
        assert filename in mono_page
    assert "不是模板" in mono_page and "不会作为模型参考图传入" in mono_page
    assert "PC01" in punk_page and "PC31" in punk_page and "PA07" in punk_page
    assert "navigator.clipboard.writeText" in punk_page and "dialog.showModal()" in punk_page
    assert "raw.githubusercontent.com/adrianpunk/Punk-Skill" in punk_page


def test_vsc_library_page_and_assets_exist() -> None:
    page = SKILL_ROOT / "assets" / "vsc-skill-library" / "index.html"
    html = page.read_text(encoding="utf-8")
    assert "真实抓拍人像" in html
    assert "虚拟情侣旅行 Vlog" in html
    assert "vsc-candid-photography-demo.png" in html
    assert "vsc-couple-travel-vlog-demo.png" in html
    assert "navigator.clipboard.writeText" in html
    assert "target=\"_blank\" rel=\"noopener\"" in html
    assert 'href="../readme/index.html"' not in html
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


def test_visual_skill_hub_links_all_galleries_and_accepts_project_role_library() -> None:
    hub = SKILL_ROOT / "assets" / "visual-skill-hub" / "index.html"
    page = hub.read_text(encoding="utf-8")
    assert "项目角色库" in page
    assert "手绘风格库" in page
    assert "350 布局库" in page
    assert "GPT-Image 2 案例库" in page
    assert "Baoyu 图册" in page
    assert "预置角色" in page
    assert "小黑配图" in page
    assert "归藏图册" in page
    assert "狗哥图册" in page
    assert "VSC 图册" in page
    for source in (
        "../layout-library/index.html",
        "../gpt-image-2-case-library/index.html",
        "../baoyu-skill-library/index.html",
        "../built-in-character-library/index.html",
        "../xiaohei-skill-library/index.html",
        "../guizang-skill-library/index.html",
        "../gbro-skill-library/index.html",
        "../vsc-skill-library/index.html",
        "file:///C:/Users/yang0/.codex/skills/handdraw-style-prompter/handdraw-style-prompter/gallery/index.html",
    ):
        assert source in page
    assert "get('project')" in page
    assert "<iframe" in page
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "VSC Candid Photography" in readme
    assert "VSC Virtual Couple Travel Vlog" in readme
    assert "ip-master/assets/showcase/vsc-candid-photography-demo.png" in readme
    assert "ip-master/assets/showcase/vsc-couple-travel-vlog-demo.png" in readme


def test_new_visual_hub_galleries_keep_official_images_remote() -> None:
    builtins = SKILL_ROOT / "assets" / "built-in-character-library" / "index.html"
    xiaohei = SKILL_ROOT / "assets" / "xiaohei-skill-library" / "index.html"
    guizang = SKILL_ROOT / "assets" / "guizang-skill-library" / "index.html"
    gbro = SKILL_ROOT / "assets" / "gbro-skill-library" / "index.html"
    for page in (builtins, xiaohei, guizang, gbro):
        assert page.is_file()
        html = page.read_text(encoding="utf-8")
        assert "navigator.clipboard.writeText" in html

    builtins_html = builtins.read_text(encoding="utf-8")
    for name in ("牙仔", "绒宝", "阿龅", "小美"):
        assert name in builtins_html

    xiaohei_html = xiaohei.read_text(encoding="utf-8")
    for filename in (
        "01-two-breakpoints.png",
        "14-trust-bridge.png",
        "01-meeting-pull-in.png",
        "07-long-scroll-story-master.png",
    ):
        assert filename in xiaohei_html
    assert "ian-xiaohei-illustrations" in xiaohei_html
    assert "ian-xiaohei-scenes" in xiaohei_html
    assert xiaohei_html.count("先读取并理解传入的文章") == 2
    assert "file:///C:/Users/yang0/.codex/skills/" in xiaohei_html

    guizang_html = guizang.read_text(encoding="utf-8")
    assert "归藏 PPT Skill" in guizang_html
    assert "归藏社媒卡 Skill" in guizang_html
    assert "user-attachments/assets/5dc316a2" in guizang_html
    assert "user-attachments/assets/d370abcc" in guizang_html

    gbro_html = gbro.read_text(encoding="utf-8")
    assert "10 种构图怎么选" in gbro_html
    assert "为传入的文章设计" in gbro_html
    assert "自动提炼并优化" in gbro_html
    assert "8d1a0a5487e9ee6539b2b0a471b58469aadfedd6" in gbro_html
    assert "raw.githubusercontent.com/pyang5166/gbro-cover-design" in gbro_html

    for label in (
        "Style A · 电子杂志风",
        "Style B · 瑞士国际主义风",
        "Editorial 社媒卡",
        "Swiss 社媒卡",
        "墨水经典",
        "IKB 蓝",
        "Live Photo",
    ):
        assert label in guizang_html


def test_library_titles_load_the_shared_github_source_link() -> None:
    script = SKILL_ROOT / "assets" / "github-title-link.js"
    source = script.read_text(encoding="utf-8")
    assert "github.com/pyang5166/gbro-cover-design" in source
    assert "github.com/op7418/guizang-ppt-skill" in source
    assert "github.com/JimLiu/baoyu-skills" in source
    assert "aria-label" in source

    for relative_path in (
        "assets/readme/index.html",
        "assets/visual-skill-hub/index.html",
        "assets/built-in-character-library/index.html",
        "assets/xiaohei-skill-library/index.html",
        "assets/guizang-skill-library/index.html",
        "assets/gbro-skill-library/index.html",
        "assets/layout-library/index.html",
        "assets/gpt-image-2-case-library/index.html",
        "assets/baoyu-skill-library/index.html",
        "assets/vsc-skill-library/index.html",
        "assets/couple-photo-library/index.html",
    ):
        html = (SKILL_ROOT / relative_path).read_text(encoding="utf-8")
        assert 'src="../github-title-link.js" defer' in html


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
    assert 'href="../readme/index.html"' not in html
    assert "返回首页" not in html
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
        "mono-color",
    }


def test_composed_method_character_and_style() -> None:
    result = capability_router.route("ip:牙仔+小黑配图2.0的配图逻辑+手绘库047风格 为文章配图")
    assert result["target_skill_id"] == "ian-xiaohei-scenes"
    assert result["characters"] == ["yazai"]
    contract = result["composition_contract"]
    assert contract["character_mode"] == "replace-default"
    assert contract["style_override"]["number"] == "047"
    assert [Path(p).name for p in result["referenced_image_paths"]] == ["yazai.webp"]
    plain = capability_router.route("类似案例72，手绘风199，主题苹果")
    assert plain["characters"] == []
    assert plain["composition_contract"]["style_override"]["number"] == "199"
    assert plain["case_library"]["selection"]["number"] == 72
    assert capability_router.route("手绘库999风格苹果")["status"] == "invalid-style"
    article_path = capability_router.route(
        "ip:牙仔+小黑配图2.0的配图逻辑+手绘库046风格 为G:\\投资笔记\\运营建议 下的文章配图，只要出一张就行"
    )
    assert article_path["status"] == "ready"
    assert article_path["characters"] == ["yazai"]
    assert article_path["composition_contract"]["character_mode"] == "replace-default"
    for operation in ("create", "prompt", "advise"):
        unnamed = capability_router.route("使用 baoyu-comic 制作漫画", operation=operation)
        assert unnamed["characters"] == []
        assert unnamed["referenced_image_paths"] == []


def test_ian_xiaohei_scenes_is_explicitly_routable() -> None:
    result = capability_router.route(
        "用 ian-xiaohei-scenes 做小黑实物场景图", operation="create"
    )
    assert result["status"] == "ready"
    assert result["target_skill_id"] == "ian-xiaohei-scenes"
    assert result["characters"] == []


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
    assert default_result["characters"] == []
    assert default_result["referenced_image_paths"] == []

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


def test_empty_project_gallery_has_role_creation_prompt_without_visual_hub_link(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-project"
    initialized = initialize_project(project_dir, name="空项目")

    assert initialized["initialized"] is True
    gallery = (project_dir / "index.html").read_text(encoding="utf-8")
    assert "打开视觉预览中心" not in gallery
    assert "使用上传的人物参考图生成一张高清人物四视图" in gallery
    assert "复制创建提示词" in gallery
    assert "navigator.clipboard.writeText" in gallery
    assert "window.prompt" in gallery
    assert "内置角色仍可直接调用，但不会显示在这里" in gallery


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
    assert result["visual_hub_url"].startswith("file:///")
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
    assert resolve_character_inputs("做图", skill_dir=SKILL_ROOT, project_dir=project_dir) == []
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
