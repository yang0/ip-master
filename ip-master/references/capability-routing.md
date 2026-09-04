# 能力路由

IP Master 只管理角色、外部 Skill 和安装信息，不提供原生生图。依赖
注册表是 [skill-registry.json](skill-registry.json)；表中的 `style_count`
与 `style_summary` 是 README 和 doctor 的唯一能力元数据来源。

## 分类与候选

| 用途 | 可选 Skill |
| --- | --- |
| IP 设计 | `personal-ip-image-pack` |
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

VSC 的两个 Skill 是“被 IP 注入的设计 Skill”，不是 IP 设计 Skill：先解析用户
明确指定的角色，再把角色作为视觉设计主体或叙事角色交给目标 Skill。普通 IP
设计请求不会自动触发它们。

## 首次使用与帮助

`assets/readme/index.html` 是本地 HTML 使用指南，包含最短调用方式和三个
案例库入口。每个新会话第一次使用 IP Master 时先显示该页，再继续处理同一条
请求；用户说“第一次用”“怎么用”“帮助”“不会用”或表达使用疑问时，也显示该页。
这不是一个 Skill 候选：帮助路由返回 `status: guide` 和 `guide_page`，不得选择
Skill、注入角色、安装依赖或生成图片。

## 项目角色库

内置角色保留在 IP Master Skill 中，可直接调用且默认仍是牙仔。用户确认后的
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

`assets/baoyu-skill-library/index.html` 展示六个 Baoyu 视觉 Skill 的示例图和
常用参数枚举。它只用于浏览与理解，不会自动选择目标 Skill，也不会覆盖用户
明确给出的内容、尺寸或参数。

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
