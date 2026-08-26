---
name: ip-master
description: "Manage registered IP characters and route design requests to optional external Skills; provide advice without installation or injection, and inject selected original references only after a concrete target is chosen."
---

# IP Master

IP Master is an orchestration layer for four registered IPs and external
design Skills. It does not generate images, render layouts, or provide a
native article-illustration fallback.

## Operating modes

- For advice or capability questions, read the registries and return suitable
  candidates. Do not install a dependency, inject a character reference, or
  generate an image.
- For `create` or `prompt`, resolve the requested capability first. If more
  than one external Skill is a plausible target, return `selection-required`
  and ask the user to choose; do not silently rank one as the winner.
- After a concrete target is selected, pass the target Skill's own contract
  together with the selected character originals. If the target dependency is
  missing or invalid, show its source and exact installation command and ask
  for confirmation before any installation. IP Master itself never installs
  or copies upstream files.

## Character references

The built-in registry is [character-registry.json](references/character-registry.json).
It contains `yazai`/牙仔 (the default), `rongbao`/绒宝, `abao`/阿龅, and
`xiaomei`/小美. Explicit Chinese or English aliases select one or more
characters; multiple characters remain separate and are passed in registry
order. When a target is selected without a character name, use the registered
default 牙仔.

Read each selected character's original asset and identity protocol. Put the
original asset paths before all target-Skill style or layout references, and
label them as identity-only inputs. The target Skill controls medium, layout,
scene, and rendering; it must not turn several characters into a hybrid.

## Routing boundaries

Use [capability-routing.md](references/capability-routing.md) for category
selection and dependency choices. Use
[character-injection.md](references/character-injection.md) when assembling
ordered references. The personal IP pack is only for an authorised person's
photo-to-cartoon IP, prototype, expression, action, or sticker workflow. It
must not be selected for animals, mascots, fictional characters, or ordinary
requests to use an existing registered IP.

Run the read-only helpers when deterministic output is needed:

```text
python scripts/capability_router.py "用牙仔做知识漫画" --operation create --json
python scripts/capability_router.py "我想知道有哪些 Skill" --operation advise --json
python scripts/doctor.py --strict --json
```

For dependency metadata and display-only installation plans, use
`scripts/dependency_manager.py`. For an explicitly user-approved new role,
use `scripts/register_character.py --confirm`; never register a prototype
without the user's confirmation and a non-conflicting id/alias set.
