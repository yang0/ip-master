# IP Master

角色注册、外部设计 Skill 路由与身份参考注入。IP Master 本身不生图，
也不复制上游 Skill；它只把明确选择的角色原图交给明确选择的外部 Skill。

能力名称按各上游真实交付物整理，不用笼统的“社交卡”代替具体功能：归藏
实际负责小红书图文组图、公众号 21:9 + 1:1 封面对和 Live Photo 动态卡。

## 内置 IP

| 牙仔（默认） | 绒宝 | 阿龅 | 小美 |
| --- | --- | --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/characters/yazai.webp" alt="牙仔" width="170"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/characters/rongbao.webp" alt="绒宝" width="170"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/characters/abao.webp" alt="阿龅" width="170"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/characters/xiaomei.webp" alt="小美" width="136"> |
| `yazai` / 牙仔<br>[身份图](ip-master/assets/characters/yazai.webp) · [协议](ip-master/references/characters/yazai.md) | `rongbao` / 绒宝<br>[身份图](ip-master/assets/characters/rongbao.webp) · [协议](ip-master/references/characters/rongbao.md) | `abao` / 阿龅<br>[身份图](ip-master/assets/characters/abao.webp) · [协议](ip-master/references/characters/abao.md) | `xiaomei` / 小美<br>[身份图](ip-master/assets/characters/xiaomei.webp) · [协议](ip-master/references/characters/xiaomei.md) |

写中文名或英文别名即可选择角色；同时写多个名称会按注册顺序分别注入。
未写角色但已明确外部目标时使用默认牙仔。新增角色必须经过用户确认，见
[注册流程](ip-master/scripts/register_character.py)。

## IP 设计类 Skill

| Skill | 风格数量 | 风格摘要 | 触发 |
| --- | ---: | --- | --- |
| [`personal-ip-image-pack`](https://github.com/DoraRabbitYan/personal-ip-image-pack) | 6 | IP-01 至 IP-06；真人照片→个人卡通 IP→表情、动作、贴纸包 | 真人照片、本人卡通形象、博主形象 |
| [`ip-illustration-character-system`](https://github.com/EverettFish/ip_illustration_for_yourself) | 1 | 萌粒钢笔涂鸦视觉系统 | 角色锚点、三视图、萌粒 |

个人照片包上游未声明许可证；按需安装，不推断许可证、不复制源码或素材。
动物、吉祥物和虚构角色不会误路由到个人照片包。

| Personal IP Image Pack | Everett Mini Illustration System |
| --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/personal-ip-image-pack.webp" alt="小美个人 IP 制作流程" width="360"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/everett-character-anchor.webp" alt="Everett 角色锚点示例" width="230"> |
| 真人照片 → 个人卡通 IP 流程 | 萌粒角色锚点 |

## 可注入 Skill

### 文章配图

| Skill | 风格数量 | 风格摘要 | 备注 |
| --- | ---: | --- | --- |
| [`ian-xiaohei-illustrations`](https://github.com/helloianneo/ian-xiaohei-illustrations) | 1 | 白底怪诞手绘、红橙蓝批注、大量留白 | 可选；无默认 |
| [`baoyu-article-illustrator`](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-article-illustrator) | 23 | 细分风格与编辑插画入口，含场景、流程图、信息图 | 可选；无默认 |
| [`ip-illustration-character-system`](https://github.com/EverettFish/ip_illustration_for_yourself) | 1 | 萌粒钢笔涂鸦文章插图 | 可选；需 GPT Image 2 |

| 小黑手绘 | Baoyu 编辑插画 | Everett 萌粒插画 |
| --- | --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/xiaohei-article-illustration.webp" alt="小黑文章配图示例" width="280"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-article-illustration.webp" alt="Baoyu 文章插画示例" width="280"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/everett-mini-article-illustration.webp" alt="Everett 萌粒文章插图示例" width="210"> |
| `ian-xiaohei-illustrations` · 16:9 | `baoyu-article-illustrator` · 16:9 | `ip-illustration-character-system` · 3:4 |

| Baoyu · 纸艺拼贴编辑插画 |
| --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-article-paper-cut.webp" alt="Baoyu 纸艺拼贴文章插图" width="420"> |

### 知识漫画

| Skill | 风格数量 | 风格摘要 |
| --- | ---: | --- |
| [`baoyu-comic`](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-comic) | 5 | 5 个漫画预设；6 种画风、7 种情绪和多种分镜版式 |

<img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-comic.webp" alt="Baoyu 知识漫画示例" width="420">

`baoyu-comic` · 4:3 知识漫画

### 封面 / 海报

| Skill | 风格数量 | 风格摘要 |
| --- | ---: | --- |
| [`dongfang-cover-design`](https://github.com/yang0/dongfang) | 6 | 东方美学方向，横版、竖版、方图 |
| [`baoyu-cover-image`](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-cover-image) | 26 | 文章封面：6 类内容类型、11 套色板、7 种渲染媒介 |
| [`gbro-cover-design`](https://github.com/pyang5166/gbro-cover-design) | 10 | 3:4 构图风格；只输出封面提示词 |

| Dongfang 横版封面 | Baoyu 封面 | GBRO 3:4 封面提示词 |
| --- | --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/dongfang-cover.webp" alt="Dongfang 横版封面示例" width="280"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-cover.webp" alt="Baoyu 封面示例" width="210"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/gbro-cover.webp" alt="GBRO 封面示例" width="210"> |
| `dongfang-cover-design` · 16:9 | `baoyu-cover-image` · 4:3 | `gbro-cover-design` · 3:4 |

| Baoyu · 黏土定格 3D | GBRO · 孔版印刷复古海报 |
| --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-cover-clay.webp" alt="Baoyu 黏土 3D 封面" width="280"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/gbro-riso-cover.webp" alt="GBRO 孔版印刷封面" width="210"> |

### 知识卡片 / 信息图

| Skill | 风格数量 | 风格摘要 |
| --- | ---: | --- |
| [`baoyu-infographic`](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-infographic) | 22 | 21 种信息结构 × 22 种视觉风格，生成结构化信息图 |
| [`ip-illustration-character-system`](https://github.com/EverettFish/ip_illustration_for_yourself) | 1 | 萌粒钢笔涂鸦 3:4 信息图 |

| Baoyu 信息图 | Everett 3:4 信息图 |
| --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-infographic.webp" alt="Baoyu 信息图示例" width="250"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/everett-infographic.webp" alt="Everett 信息图示例" width="210"> |
| `baoyu-infographic` | `ip-illustration-character-system` |

| Baoyu · 霓虹等距信息图 |
| --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-infographic-neon.webp" alt="Baoyu 霓虹等距信息图" width="420"> |

### 贴纸 / 角色设定

| Skill | 风格数量 | 风格摘要 |
| --- | ---: | --- |
| [`personal-ip-image-pack`](https://github.com/DoraRabbitYan/personal-ip-image-pack) | 6 | 真人卡通 IP 的表情、动作与贴纸套图 |
| [`ip-illustration-character-system`](https://github.com/EverettFish/ip_illustration_for_yourself) | 1 | 萌粒角色锚点、三视图与 3:4 贴纸页 |

<img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/everett-sticker.webp" alt="阿龅贴纸示例" width="240">

`ip-illustration-character-system` · 3:4 单角色贴纸预览

### 小红书图文 / 公众号封面对 / Live Photo

| 归藏 Swiss 瑞士国际主义 | 归藏 Editorial 电子杂志 |
| --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/guizang-social-card.webp" alt="归藏 Swiss 小红书图文组图" width="230"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/guizang-editorial.webp" alt="归藏 Editorial 小红书图文组图" width="230"> |
| `guizang-social-card-skill` · 网格、锚点色、强字号对比 | `guizang-social-card-skill` · 克制版面、叙事与生活方式 |

### 小红书 / PPT / 提示词增强

| 用途 | Skill | 风格数量 | 风格摘要 |
| --- | --- | ---: | --- |
| 小红书 | [`baoyu-xhs-images`](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-xhs-images) | 12 | 12 种视觉风格 × 8 种版式 × 3 套配色，输出 1–10 张图文卡片 |
| PPT | [`baoyu-slide-deck`](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-slide-deck) | 17 | 17 套预设，组合材质、情绪、字体与信息密度 |
| 提示词增强 | [`gpt-image-2-style-library`](https://github.com/freestylefly/awesome-gpt-image-2) | 500+ | GPT Image 2 案例模板，只增强提示词，不替换基础 Skill |

| Baoyu 小红书 | Baoyu 幻灯片 | GPT Image 2 风格库增强示意 |
| --- | --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-xhs.webp" alt="Baoyu 小红书图文示例" width="210"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-slide-deck.webp" alt="Baoyu 幻灯片示例" width="280"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/gpt-image-2-style-library.webp" alt="高密度彩色海报风格增强示意" width="210"> |
| `baoyu-xhs-images` · 3:4 | `baoyu-slide-deck` · 16:9 | 增强层与 `dongfang-cover-design` 组合 · 3:4 |

| Baoyu 小红书 · 手账拼贴 | Baoyu 幻灯片 · 暗色 cinematic keynote |
| --- | --- |
| <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-xhs-scrapbook.webp" alt="Baoyu 小红书手账拼贴" width="210"> | <img src="https://raw.githubusercontent.com/yang0/ip-master/main/ip-master/assets/showcase/baoyu-slide-deck-dark.webp" alt="Baoyu 暗色 keynote 幻灯片" width="360"> |

普通“文章配图”与多候选场景会先列出可选 Skill；IP Master 不擅自安装或
决定一个默认目标。点名 Skill 后，缺失依赖会展示来源和安装命令，确认后
才由系统安装器处理。完整规则见
[能力路由](ip-master/references/capability-routing.md)和
[角色注入协议](ip-master/references/character-injection.md)。

## 示例边界

以上预览均为本项目此前生成的衍生示例，只用于说明可注入后的输出类型；
不是上游 Skill 的源码、模板或官方素材。

## 最小调用

```text
用牙仔做一套知识漫画
用绒宝和阿龅做一张横版封面
用本人照片制作个人卡通 IP，并使用 personal-ip-image-pack
我只想知道文章配图有哪些 Skill（不要安装或生图）
```

脚本入口：[`capability_router.py`](ip-master/scripts/capability_router.py)、
[`dependency_manager.py`](ip-master/scripts/dependency_manager.py)、
[`doctor.py`](ip-master/scripts/doctor.py)。

## 来源与边界

感谢各上游项目维护者。所有可选 Skill 均按需从其公开仓库安装，IP Master
不复制其源码、模板、示例或素材；许可证与来源以各上游仓库声明为准。

- [Personal IP Image Pack](https://github.com/DoraRabbitYan/personal-ip-image-pack)：上游未声明许可证。
- [IP Mini Illustration System](https://github.com/EverettFish/ip_illustration_for_yourself)
- [Dongfang](https://github.com/yang0/dongfang)
- [Baoyu Skills](https://github.com/JimLiu/baoyu-skills)
- [归藏小红书图文与公众号封面对技能（上游仓库）](https://github.com/op7418/guizang-social-card-skill)
- [GBRO Cover Design](https://github.com/pyang5166/gbro-cover-design)
- [GPT Image 2 Style Library](https://github.com/freestylefly/awesome-gpt-image-2)

详见 [NOTICE](NOTICE.md) 与 [LICENSE](LICENSE)。
