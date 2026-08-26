#!/usr/bin/env python3
"""Read-only registry and installation-plan manager for IP Master.

IP Master does not install, clone, or copy external Skills itself.  This
module centralises lookup of registered dependencies and emits the exact
arguments a user-approved system installer can run.  The separation keeps
``advise`` and ordinary routing side-effect free.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REGISTRY_PATH = SKILL_DIR / "references" / "skill-registry.json"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dependency_utils import (  # noqa: E402
    DependencyRegistryError,
    dependency_install_info,
    dependency_source_url,
    inspect_dependency,
    load_dependency_registry,
)


class UnknownDependencyError(KeyError):
    """Raised when a caller asks for an unregistered external Skill."""


def load_registry(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    """Load and validate the registry belonging to *skill_dir*."""

    root = skill_dir.expanduser().resolve(strict=False)
    return load_dependency_registry(root / "references" / "skill-registry.json")


def get_dependency(skill_id: str, *, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    """Return one registered dependency, preserving registry order elsewhere."""

    wanted = skill_id.strip().casefold()
    if not wanted:
        raise UnknownDependencyError(skill_id)
    for dependency in load_registry(skill_dir=skill_dir)["dependencies"]:
        if str(dependency["skill_id"]).casefold() == wanted:
            return dependency
    raise UnknownDependencyError(skill_id)


def installation_plan(skill_id: str, *, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    """Return source, metadata, and installer arguments without running them."""

    dependency = get_dependency(skill_id, skill_dir=skill_dir)
    return {
        "skill_id": dependency["skill_id"],
        "repo": dependency["repo"],
        "path": dependency["path"],
        "install_name": dependency.get("install_name", dependency["skill_id"]),
        "ref": dependency["ref"],
        "optional": bool(dependency.get("optional", False)),
        "purpose": dependency.get("purpose"),
        "capabilities": dependency.get("capabilities", []),
        "categories": dependency.get("categories", []),
        "style_count": dependency.get("style_count"),
        "style_summary": dependency.get("style_summary"),
        "license": dependency.get("license"),
        "source": dependency_source_url(dependency),
        "install": dependency_install_info(dependency),
        "action": "display-only; run the system installer only after explicit user confirmation",
    }


def diagnose_dependency(
    skill_id: str,
    *,
    skill_dir: Path = SKILL_DIR,
    environment: dict[str, str] | None = None,
    home: Path | None = None,
) -> dict[str, Any]:
    """Return one read-only installation report plus its installation plan."""

    dependency = get_dependency(skill_id, skill_dir=skill_dir)
    report = inspect_dependency(
        dependency,
        skill_root=skill_dir.expanduser().resolve(strict=False),
        environment=environment,
        home=home,
    )
    report["installation_plan"] = installation_plan(skill_id, skill_dir=skill_dir)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect IP Master external Skill dependencies")
    parser.add_argument("skill_id", nargs="?", help="registered Skill id")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="emit the display-only installation plan instead of probing locations",
    )
    args = parser.parse_args(argv)
    try:
        if args.skill_id:
            result: Any = (
                installation_plan(args.skill_id)
                if args.plan
                else diagnose_dependency(args.skill_id)
            )
        else:
            registry = load_registry()
            result = {
                "dependencies": [
                    installation_plan(dependency["skill_id"])
                    if args.plan
                    else diagnose_dependency(dependency["skill_id"])
                    for dependency in registry["dependencies"]
                ]
            }
    except (DependencyRegistryError, UnknownDependencyError, OSError, ValueError) as exc:
        if args.as_json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.skill_id:
        if args.plan:
            print(result["install"]["command"])
        else:
            print(f"{result['skill_id']}: {result['status']}")
    else:
        for item in result["dependencies"]:
            print(item["skill_id"] if args.plan else f"{item['skill_id']}: {item['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
