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

### VSC visual design Skills

The registry includes two VSC Skills from `vibeshotclub/vsc-skills`:

- `vibeshot-candid-photography` — real-life candid portrait direction with
  unusual camera positions, natural occlusion, and varied prompt batches.
- `virtual-couple-travel-vlog` — a virtual-couple travel asset workflow with
  a 4×4 memory wall, identity-consistent character cards, video prompts, and
  staged Vlog assembly.

These are design Skills, not IP-design Skills. When the user names one, first
resolve the explicitly named IP character and then pass its identity inputs to
the selected Skill. They must not be silently selected for ordinary poster,
cover, or IP-creation requests. The local visual overview is
`assets/vsc-skill-library/index.html`.

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

### 真人照片入库流程

如果用户上传真人照片并要求“设计人物 IP”，但没有说明是“先做四视图作为身份资产”还是“只基于照片特征设计 IP”，必须先询问并暂停生成；不得替用户默认选择。路由器对此返回 `status: photo-workflow-choice` 和两个选项。

当用户上传清晰真人照片并要建立人物 IP 时，先走 `human-photo-four-view-first`，不要直接把原照片注册进项目：

1. 读取照片的整体头部特征、年龄感和气质，不复制原场景、姿势、瞬时表情或原服装。
2. 先生成一张纯色背景的高清四视图候选：颈部以上脸部特写、全身正视、严格 90° 侧视、全身背视；四个视图必须是同一人且全身不裁切。
3. 要求用户补充并确认名称、年龄、身高和体重。姓名和这三项资料必须以清晰文字写入四视图图片；生成后优先用确定性图像标注脚本校正文字，不依赖模型自由生成文字。
4. 候选图交给用户确认。未确认前只放在项目 `candidates/`，不写入角色注册表，也不进入正式 IP 图册。
5. 用户确认后，使用 `scripts/register_character.py --project-dir <项目目录> --id <id> --display-name <名称> --age <年龄> --height-cm <身高> --weight-kg <体重> --prototype <四视图图片> --confirm` 注册；注册后的图片、资料和项目图册只写入项目目录。
6. 每次注册成功后，立即用渲染浏览器打开返回结果中的 `gallery_url`（项目根目录 `index.html`），让用户查看新 IP；不要用代码面板打开，以免显示 HTML 源码。

四视图是身份参考资产，不是最终设计作品；后续目标 Skill 仍决定媒介、服装、场景和构图。姓名、年龄、身高和体重属于项目元数据，不得从照片臆测，缺失时必须询问。

## 350 visual layout library

The local `assets/layout-library/index.html` is a 350-item browser gallery,
not a generation target and not a default style. Its thumbnails are locally
cloned from the pinned upstream commit, with original source paths retained.
Do not put it into a first-pass
prompt unless the user explicitly selects a numbered layout for a poster,
cover, or slide deck.

- For a user request such as `用 008 重新排版`, `layout-008`, or `用 341 做
  PPT`, resolve the number with `scripts/layout_library.py --select`. Pass its
  `generation_instruction` as text after character identity inputs; it is a
  composition method, not a coordinate template. Never pass a gallery image
  to the image model.
- Keep the original target Skill, theme, character identity, required copy,
  and visual medium. Apply the selected method to the new theme; user-specified
  placement overrides its default landing. Do not reuse the gallery sample's
  coordinates, colours, geometry, typography, text, people, objects, brands,
  or textures.
- After a selected cover/poster Skill has produced a final portrait raster image, run
  `scripts/layout_library.py --delivery-note <final-image>`. Append its
  message only when it reports `eligible: true`. It deliberately excludes
  landscape images and prompt-only outputs.
- `001–350` are the verified display numbers ordered by the actual titles in
  the images; each record also keeps the original upstream number. Old 1–100
  meanings are retired. Always use the current gallery label rather than
  assuming an old number has the same meaning.
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

### Project character libraries

Built-in roles remain global defaults. User-approved custom roles belong to an
explicit IP project, never this installed Skill directory. Initialize one at a
user-selected location with `python scripts/ip_project.py --init --project-dir
"E:\\projects\\品牌IP" --name "品牌 IP"`. Register an approved prototype with
`scripts/register_character.py --project-dir "E:\\projects\\品牌IP" --confirm
...`; its registry, WebP asset, identity protocol, and `index.html` are written
only under that project. Supply the same `--project-dir` when routing. Reuse a
user-declared project for the current conversation only; do not persist it.

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
python scripts/capability_router.py "用项目角色做知识漫画" --project-dir "E:\\projects\\品牌IP" --operation create --json
python scripts/capability_router.py "我想知道有哪些 Skill" --operation advise --json
python scripts/doctor.py --strict --json
```

For dependency metadata and display-only installation plans, use
`scripts/dependency_manager.py`. For an explicitly user-approved new role,
use `scripts/register_character.py --project-dir <project-path> --confirm`; never register a prototype
without the user's confirmation and a non-conflicting id/alias set.
