# 能力路由

IP Master 只管理角色、外部 Skill 和安装信息，不提供原生生图。依赖
注册表是 [skill-registry.json](skill-registry.json)；表中的 `style_count`
与 `style_summary` 是 README 和 doctor 的唯一能力元数据来源。

## 分类与候选

| 用途 | 可选 Skill |
| --- | --- |
| IP 设计 | `personal-ip-image-pack`、`ip-as-logo` |
| 单色 / 双色编辑印刷 | `mono-color` |
| 封面 | `punk-cover` |
| 人物 / 宠物 / 物件头像 | `punk-avatar` |
| 角色绘制媒介 / 可注入风格 | `ip-illustration-character-system` |
| 文章配图 | `ian-xiaohei-illustrations`、`baoyu-article-illustrator`、`ip-illustration-character-system` |
| 知识漫画 | `baoyu-comic` |
| 封面 / 海报 | `dongfang-cover-design`、`baoyu-cover-image`、`gbro-cover-design` |
| 知识卡片 / 信息图 | `baoyu-infographic`、`ip-illustration-character-system` |
| 小红书图文 / 公众号封面对 / Live Photo | `guizang-social-card-skill` |
| 贴纸 / 角色设定 | `personal-ip-image-pack`、`ip-illustration-character-system` |
| 小红书 | `baoyu-xhs-images`、`guizang-social-card-skill` |
| 公众号 | `guizang-social-card-skill`、`baoyu-cover-image` |
| PPT | `baoyu-slide-deck` |
| 提示词增强 | `gpt-image-2-style-library` |
| 真实抓拍人像设计 | `vibeshot-candid-photography` |
| 情侣旅行 Vlog 设计 | `virtual-couple-travel-vlog` |
| 手绘风格提示词 | `handdraw-style-prompter` |

VSC 的两个 Skill 是“被 IP 注入的设计 Skill”，不是 IP 设计 Skill：先解析用户
明确指定的角色，再把角色作为视觉设计主体或叙事角色交给目标 Skill。普通 IP
设计请求不会自动触发它们。

`yang0/couple-photo` 是一个完整的情侣照工作流，包含 `kefu` 需求确认、`paishe`
拍摄与 8 宫格、`huanzhuang` 6 套换装候选和 `zongkong` 总协调。用户明确说“情侣照”、
“情侣写真”或“婚纱照”时，默认进入 `couple-photo-orchestrator`；明确提到需求确认、
拍摄规划或情侣换装时命中对应阶段。首次进入必须提供绝对项目目录，按“需求 → Couple
Look → 8 条 Shot → 2×4 宫格 → 选编号精修”推进；不自动复用目录，不把流程图册图片作为
模型参考图。预览页是 `assets/couple-photo-library/index.html`。

`handdraw-style-prompter` 是手绘视觉设计 Skill，不负责创建 IP。用户需要明确
给出 `001–261` 的风格编号和主题，例如“041 号手绘风格，主题：秋天的第一杯
奶茶”。Skill 默认输出中文和英文提示词；明确要求生图时，再依据当前模型能力
决定只使用风格名称、加入可迁移风格特征，或使用对应编号的单张风格参考图。
风格图只用于画风参考，不得把其中的主体、人物、构图、文字或故事带入新图。

`ip-as-logo` 是 IP 设计 Skill，适合设计极简、圆润、可长期复用的吉祥物形象。
默认从用户指定的动物、物件或角色概念提出 3 个设计方向，用户确认后生成 6 张
独立候选；它不是文章配图或普通海报 Skill。预览页见
`assets/ip-as-logo-library/index.html`。

`mono-color` 是被 IP 注入的视觉设计 Skill，适合单色海报、双色孔版印刷、网点
照片、编辑排版、zine 和社媒卡。它负责纸张、墨色、网点、留白和版式语法；用户
明确指定 IP 时才注入角色，普通请求不会自动使用。

Mono Color 使用 README 的自然语言工作方式：用户提供主题、短句、物件、文章想法
或照片；默认受控双色，明确要求“单色 / 单墨”时才切换为单墨。用户可以按需说明
油墨、用途、标题、比例与是否保留照片主体身份；具体版式和字体关系由 Skill 决定。
图册中的官方输出案例只用于浏览，不得作为模型参考图。

Punk-Skill 包含两个独立入口：`punk-cover` 负责文章、小红书、公众号和 X 封面；
`punk-avatar` 负责人物、宠物和物件头像。两者都需要显式调用，不会自动替换
其他封面或 IP 设计 Skill；视觉预览见 `assets/punk-skill-library/index.html`。

Punk 图册提供 `PC01–PC31`（封面）与 `PA01–PA07`（头像）编号。可直接说
“用 PC08 做封面”或“用 PA04 做人物头像”；路由只注入对应的 `style` 文本参数。
`PA07` 还需要明确 `mode=before-after` 或 `mode=final-artwork`。图册图片不进入
模型参考图输入。

## 首次使用与帮助

`assets/readme/index.html` 是本地 HTML 使用指南，包含最短调用方式和三个
案例库入口。每个新会话第一次使用 IP Master 时先显示该页，再继续处理同一条
请求；用户说“第一次用”“怎么用”“帮助”“不会用”或表达使用疑问时，也显示该页。
这不是一个 Skill 候选：帮助路由返回 `status: guide` 和 `guide_page`，不得选择
Skill、注入角色、安装依赖或生成图片。

## 项目角色库

内置角色保留在 IP Master Skill 中，只有明确点名才注入。用户确认后的
自定义 IP 必须注册到用户指定的独立项目目录：先运行
`scripts/ip_project.py --init --project-dir <项目目录>`，再运行
`scripts/register_character.py --project-dir <项目目录> --confirm ...`。
项目内会保存角色图、身份协议、注册表和仅展示项目角色的 `index.html` 图册。
每次注册新 IP 成功后，都应立即在渲染浏览器中打开项目 `index.html`，让用户检查
新角色；不要在代码面板中打开该页面。
路由时传入同一 `--project-dir`，检索范围是内置角色加该项目角色；项目角色
不得复用内置角色的 ID 或别名。项目路径仅在当前对话中复用，不写入全局配置。

## 350 种视觉布局参考库

`assets/layout-library/index.html` 是按图内标题核验后的本地图片浏览库，不是
路由候选，也不会在首轮请求中自动生效。仅当用户明确给出 `001–350` 编号
（如 `用 008 重新排版`、`layout-008` 或 `用 341 做 PPT`）时，才将对应的
构图方法论传给原先选定的海报、封面或 PPT Skill。缩略图只供用户浏览，绝不
能作为生图图片引用；方法论会按新主题重新落位，不得继承样图坐标或视觉元素。
仅海报/封面在最终实际图片为竖版时可附画廊链接；PPT 和只输出提示词的 Skill
不附。旧版 1–100 的编号语义已废弃；新版编号按当前图库图片实际标题整理，原始上游编号保存在清单中。

## GPT-Image 2 案例参考库

`assets/gpt-image-2-case-library/index.html` 提供上游案例的本地索引和
远程原图预览。案例只有在用户明确选择编号（如 `案例 539` 或 `case 539`）
时才生效：若没有具体设计 Skill，则路由到 `gpt-image-2-style-library`
输出可复制提示词；若已有具体设计 Skill，则作为文本化风格增强层附加给它。
案例图只供浏览，不得作为生图参考图输入，也不得复制其中的人物、品牌、
版权素材、文案、坐标或具体画面。主题、角色、文字、尺寸与目标 Skill 规则
始终优先。

## Baoyu 视觉 Skill 图册

`assets/baoyu-skill-library/index.html` 将 124 张 Baoyu 官方图片按参数功能
分组：画风、信息结构、分镜布局或成稿视觉系统。图片是参数示意，不是最终成片
示范；它们不会自动选择目标 Skill，也不会覆盖用户明确给出的内容、尺寸或参数。

点击图册的参数卡片会复制带有 `待填写` 字段的调用模板；图册不参与路由，也不
自动选择参数。绝不把 Baoyu 示例图片作为模型参考图输入。

文章配图不绑定默认 Skill。IP 设计请求只有在出现真人照片、本人卡通
形象、博主形象、个人头像 IP、照片转卡通或人物表情 / 动作包等信号时，
才进入 `personal-ip-image-pack`；动物、吉祥物和虚构角色不进入该流程。

真人照片进入人物 IP 流程时，先生成纯色背景四视图候选，再询问并确认名称、年龄、
身高和体重；四项信息由用户提供，不能从照片推断。姓名和数值必须写入候选四视图
图片。未确认的候选只保存在项目 `candidates/`，确认后才调用注册脚本写入项目角色库。
如果用户只说“上传真人照片设计 IP”而未选择四视图流程或照片特征流程，路由返回
`status: photo-workflow-choice`，先询问用户，不生成、不注入、不入库。

## 选择优先级

1. 用户明确点名 Skill id、上游项目名或已注册的中文触发词时，使用该
   Skill；若用途不兼容，返回 `incompatible`。
2. 用户未点名但只有一个分类候选时，可以选中该候选。
3. 有两个或更多候选时，`create` / `prompt` 返回 `selection-required`，
   列出候选、风格数量和摘要；不按仓库顺序静默决定。
4. `advise` 永远只返回建议，不安装、不注入角色、不生成图片，即使用户
   点名了一个 Skill。
5. 没有可识别的外部目标时返回 `unsupported`。不得创建 native target 或
   以原生生图兜底。

缺失依赖只返回来源、状态与 display-only 安装命令；得到用户确认后，才
可由系统安装器处理。IP Master 不复制上游源码、模板或素材。
