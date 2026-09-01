# IP Master

让已有角色或新角色进入海报、封面、漫画、信息图、PPT 等视觉作品。IP Master 负责选择合适的外部 Skill、传入角色身份，不自行生成图片。

## 从这里开始

安装后，打开 [HTML 使用指南](ip-master/assets/readme/index.html)。它提供最短调用示例，以及三个可直接浏览的本地案例库。

安装时，把下面这句话连同本仓库链接发给 Codex：

```text
请安装这个 Skill：https://github.com/yang0/ip-master
```

## 最短用法

```text
用牙仔做一张 3:4 海报，主题：杭州城市
```

```text
读取这篇文章，用绒宝制作知识漫画
```

```text
用阿龅做一张信息图，主题：AI Agent 如何工作
```

如果多个 Skill 都适合，IP Master 会列出候选并让你选择；本次对话选过后会沿用该选择。首次使用或遇到疑问时，直接说“怎么用 IP Master”即可打开指南。

## 案例库

- [IP Master 使用指南](ip-master/assets/readme/index.html)
- [竖版海报排版库](ip-master/assets/layout-library/index.html)：成图后按编号重新排版。
- [GPT-Image 2 案例库](ip-master/assets/gpt-image-2-case-library/index.html)：浏览后说“用案例 539 设计”。案例只迁移文字化视觉方向，不作为模型参考图。
- [Baoyu 视觉 Skill 图册](ip-master/assets/baoyu-skill-library/index.html)：查看文章配图、知识漫画、封面、信息图、小红书图文和 PPT 的示例及参数。

内置角色：牙仔（默认）、绒宝、阿龅、小美。也可提供账号、资料、照片或一句需求，让合适的角色 IP Skill 先生成候选方向。

## 集成 Skill

IP Master 可路由到 Character IP、Mascot IP、Personal IP Image Pack、Baoyu Skills、Dongfang Cover Design、GBRO Cover Design、Guizang Social Card、Ian Xiaohei Illustrations / Scenes 与 GPT-Image 2 Style Library。完整候选、安装状态和边界见 [使用指南](ip-master/assets/readme/index.html)。

Released under the [MIT License](LICENSE).
