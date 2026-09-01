---
name: ip-master
description: "Manage registered IP characters and route design requests to suitable available Skills; when several Skills fit, ask the user to choose and remember that choice for the current conversation."
---

# IP Master

IP Master is an orchestration layer for four registered IPs and external
design Skills. It does not generate images, render layouts, or provide a
native article-illustration fallback.

## Operating modes

- On the first IP Master request in each conversation, display the local
  [HTML guide](assets/readme/index.html) before proceeding with the same
  request. This is conversation-local presentation only: do not persist it or
  ask the user to repeat a concrete request. At any time, show the same guide
  when the user says `第一次用`、`怎么用`、`帮助`、`不会用` or expresses a
  usage question. For an explicit help request, use the router's `guide_page`
  result and navigate its `browser_url` in a rendered browser tab. Do not use a
  file/code panel for this step because that displays the HTML source. The
  guide step must not select a Skill, inject references, install, or generate.
- For advice or capability questions, inspect the registered dependencies and
  the Skills available in the current environment, then return suitable
  candidates. Do not install a dependency, inject a character reference, or
  generate an image.
- For `create` or `prompt`, resolve the requested capability first. Apply the
  selection protocol below when more than one Skill is a plausible target; do
  not silently rank one as the winner.
- After a concrete target is selected, pass the target Skill's own contract
  together with the selected character originals. If the target dependency is
  missing or invalid, show its source and exact installation command and ask
  for confirmation before any installation. IP Master itself never installs
  or copies upstream files.

## Multi-Skill selection protocol

Before starting a design request, discover candidates from both the IP Master
registry and the current environment's available Skills. A Skill does not need
to be registered in `skill-registry.json` to be presented as a candidate when
its own scope clearly satisfies the user's request.

1. If the user explicitly names a compatible Skill, use it. This explicit
   choice replaces any earlier default for the same capability in this
   conversation.
2. If exactly one compatible Skill exists, use it.
3. If two or more compatible Skills exist and the user has not previously
   chosen one for this capability in the current conversation, list every
   candidate by **Skill name** with one concise sentence explaining its
   relevant difference, then ask: `想用哪个 Skill 来设计？`
4. After the user selects a Skill, remember it as the default for that
   capability for the rest of the current conversation. For later compatible
   requests, use this default without asking again.
5. Do not reuse a default when the new request is outside that Skill's scope,
   when it belongs to a different capability, or when the user asks to choose
   again. Re-run candidate discovery in those cases.

This is conversation-local working state only. Do not write it to a file,
registry, preference store, or cross-conversation memory.

### Person IP candidates

For a request to design a human, creator, or account-based person IP, evaluate
at least these two available Skill paths when they are present:

- `character-ip` — turns an account, topic, source materials, reference photo,
  or persona into a first-pass 5×5 board of 25 human-character candidates.
- `personal-ip-image-pack` — turns authorised personal photos into a
  higher-fidelity personal prototype, then supports confirmed-avatar,
  expression, action, and sticker assets.

When both fit, present both names and their distinction before doing any
design. An account link alone does not establish the photo authorisation
required by `personal-ip-image-pack`; keep that limitation explicit. Animal,
mascot, object, and fictional-character requests are incompatible with both
of these person-IP paths and must be discovered or routed separately.

## Portrait-poster layout library

The local `assets/layout-library/index.html` is a reference gallery, not a
generation target and not a default style. Do not put it into a first-pass
prompt, including a high-density request, unless the user explicitly selects
a numbered layout for a re-layout.

- For a user request such as `用 23 重新排版` or `用 layout-023 重排`, resolve
  the number with `scripts/layout_library.py --select`. Pass its
  `generation_instruction` as text after character identity inputs; it is a
  composition method, not a coordinate template. Never pass the thumbnail to
  the image model.
- Keep the original target Skill, theme, character identity, required copy,
  and visual medium. Apply the selected method to the new theme; user-specified
  placement overrides its default landing. Do not reuse the gallery sample's
  coordinates, colours, geometry, typography, text, people, objects, brands,
  or textures.
- After a selected cover/poster Skill has produced a final raster image, run
  `scripts/layout_library.py --delivery-note <final-image>`. Append its
  message only when it reports `eligible: true`. It deliberately excludes
  landscape images and prompt-only outputs.
- To check whether the source collection changed, use
  `scripts/layout_library.py --check`; use `--sync` only when an updated
  snapshot is wanted. Never synchronize during ordinary image generation.

## GPT-Image 2 案例参考库

`assets/gpt-image-2-case-library/index.html` is a source-linked case gallery.
It is opt-in: never select an example case automatically. Users can browse the
gallery and say `用案例 539 设计`, or add a case number to a concrete design
request such as `用牙仔和 dongfang 做海报，案例 539`.

- Resolve an explicit selection with `scripts/gpt_image_2_case_library.py
  --select`. The selection is a text-only visual-direction layer: do not pass
  its remote image URL to an image model and do not copy its people, brands,
  protected material, wording, coordinates, or concrete scene.
- With a case number but no target design Skill, route to
  `gpt-image-2-style-library` and produce a copyable GPT-Image-2 prompt. With
  a concrete design Skill, retain that target and append the selection after
  character and composition inputs as an enhancement layer.
- User theme, character identity, required copy, dimensions, and the target
  Skill's own contract always override the example case. A case is not a
  default style or a model reference image.
- The gallery stores metadata only and loads images from the upstream source.
  Run `scripts/gpt_image_2_case_library.py --check` to detect an update and
  `--sync` only when an updated index is explicitly wanted.

## Baoyu 视觉 Skill 图册

`assets/baoyu-skill-library/index.html` is a local visual reference for the
six Baoyu creation Skills: article illustration, knowledge comic, cover,
infographic, Xiaohongshu images, and slide deck. It is a browse-and-learn
page, not a routing candidate or a default parameter preset. Let users open
it when they want examples or parameter explanations; their explicit request
and the selected target Skill contract still control generation.

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
