# 能力路由

IP Master 只管理角色、外部 Skill 和安装信息，不提供原生生图。依赖
注册表是 [skill-registry.json](skill-registry.json)；表中的 `style_count`
与 `style_summary` 是 README 和 doctor 的唯一能力元数据来源。

## 分类与候选

| 用途 | 可选 Skill |
| --- | --- |
| IP 设计 | `personal-ip-image-pack`、`ip-illustration-character-system` |
| 文章配图 | `ian-xiaohei-illustrations`、`baoyu-article-illustrator`、`ip-illustration-character-system` |
| 知识漫画 | `baoyu-comic` |
| 封面 / 海报 | `dongfang-cover-design`、`baoyu-cover-image`、`gbro-cover-design` |
| 知识卡片 / 信息图 | `baoyu-infographic`、`guizang-social-card-skill`、`ip-illustration-character-system` |
| 贴纸 / 角色设定 | `personal-ip-image-pack`、`ip-illustration-character-system` |
| 小红书 | `baoyu-xhs-images`、`guizang-social-card-skill` |
| 公众号 | `guizang-social-card-skill`、`baoyu-cover-image` |
| PPT | `baoyu-slide-deck` |
| 提示词增强 | `gpt-image-2-style-library` |

文章配图不绑定默认 Skill。IP 设计请求只有在出现真人照片、本人卡通
形象、博主形象、个人头像 IP、照片转卡通或人物表情 / 动作包等信号时，
才进入 `personal-ip-image-pack`；动物、吉祥物和虚构角色不进入该流程。

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
