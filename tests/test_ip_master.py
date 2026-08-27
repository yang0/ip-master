from __future__ import annotations

import json
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
from character_router import (  # noqa: E402
    CharacterRegistryError,
    inspect_registry,
    resolve_character_inputs,
)
from register_character import CharacterRegistrationError, register_character  # noqa: E402


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
