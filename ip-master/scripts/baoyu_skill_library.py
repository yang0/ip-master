#!/usr/bin/env python3
"""Build and query the Baoyu visual-skill reference catalogue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LIBRARY_DIR = SKILL_DIR / "assets" / "baoyu-skill-library"
MANIFEST_PATH = LIBRARY_DIR / "manifest.json"
UPSTREAM_REPOSITORY = "https://github.com/JimLiu/baoyu-skills"
UPSTREAM_COMMIT = "55223daf5c7c21ce6343935f138fcbe33d683000"
RAW_ROOT = f"https://raw.githubusercontent.com/JimLiu/baoyu-skills/{UPSTREAM_COMMIT}"
EXPECTED_COUNT = 124
VISUAL_ISOLATION = "图片是风格或布局的参数示意，不是最终成片示范，也不作为模型参考图输入；不继承图中的主题、人物、文字、品牌、数据或具体画面。"


def _items(values: str) -> tuple[str, ...]:
    return tuple(values.split())


GROUPS: tuple[dict[str, Any], ...] = (
    {"id": "article-style", "skill_id": "baoyu-article-illustrator", "skill_name": "文章配图", "category": "article-illustration", "title": "选择视觉风格参数", "parameter": "style", "parameter_label": "风格", "directory": "article-illustrator-styles", "how": "这些图只展示可选画面语言；文章主题、图形类型和正文内容仍由你的请求决定。", "combine": "可再在参数说明中指定 type 与 palette。", "values": _items("blueprint chalkboard editorial elegant fantasy-animation flat-doodle flat intuition-machine minimal nature notion pixel-art playful retro scientific sketch-notes sketch vector-illustration vintage warm watercolor")},
    {"id": "comic-style", "skill_id": "baoyu-comic", "skill_name": "知识漫画", "category": "knowledge-comic", "title": "选择画风或叙事预设", "parameter": "art", "parameter_label": "画风 / 预设", "directory": "comic-styles", "how": "先选画面语言；需要控制分镜阅读方式时，再从下一组选择一个布局。", "combine": "可再选择一个漫画布局参数。", "values": _items("classic dramatic ohmsha realistic sepia shoujo vibrant warm wuxia")},
    {"id": "comic-layout", "skill_id": "baoyu-comic", "skill_name": "知识漫画", "category": "knowledge-comic", "title": "选择分镜布局参数", "parameter": "layout", "parameter_label": "布局", "directory": "comic-layouts", "how": "这些图只展示读者阅读分镜的方式；它不改变漫画主题和画风。", "combine": "可再选择一个漫画画风或预设参数。", "values": _items("cinematic dense mixed splash standard webtoon")},
    {"id": "cover-style", "skill_id": "baoyu-cover-image", "skill_name": "文章封面", "category": "cover-poster", "title": "选择封面视觉风格参数", "parameter": "style", "parameter_label": "风格", "directory": "cover-image-styles", "how": "这些图只展示封面的视觉语气；主题、标题、比例与封面类型仍由你的请求决定。", "combine": "可再在参数说明中指定 type、rendering、palette 与 aspect。", "values": _items("blueprint bold-editorial chalkboard dark-atmospheric editorial-infographic elegant fantasy-animation flat-doodle intuition-machine minimal nature notion pixel-art playful retro sketch-notes vector-illustration vintage warm watercolor")},
    {"id": "infographic-style", "skill_id": "baoyu-infographic", "skill_name": "信息图", "category": "knowledge-card", "title": "选择视觉风格参数", "parameter": "style", "parameter_label": "风格", "directory": "infographic-styles", "how": "这些图只展示线条、材质与整体视觉气质；再从下一组选择信息结构。", "combine": "建议再选择一个信息图布局参数。", "values": _items("aged-academia bold-graphic chalkboard claymation corporate-memphis craft-handmade cyberpunk-neon ikea-manual kawaii knolling lego-brick origami pixel-art storybook-watercolor subway-map technical-schematic ui-wireframe")},
    {"id": "infographic-layout", "skill_id": "baoyu-infographic", "skill_name": "信息图", "category": "knowledge-card", "title": "选择信息结构 / 布局参数", "parameter": "layout", "parameter_label": "布局", "directory": "infographic-layouts", "how": "这些图只展示可迁移的信息关系；先选与内容关系相符的结构，再搭配一张视觉风格图。", "combine": "建议再选择一个信息图风格参数。", "values": _items("bridge circular-flow comparison-table do-dont equation feature-list fishbone funnel grid-cards iceberg journey-path layers-stack mind-map nested-circles priority-quadrants pyramid scale-balance timeline-horizontal tree-hierarchy venn")},
    {"id": "xhs-style", "skill_id": "baoyu-xhs-images", "skill_name": "小红书图文", "category": "xiaohongshu", "title": "选择视觉风格参数", "parameter": "style", "parameter_label": "风格", "directory": "xhs-images-styles", "how": "这些图只展示组图的视觉气质；再按内容密度选择排版方式。", "combine": "可再选择一个小红书布局参数。", "values": _items("bold chalkboard cute fresh minimal notion pop retro warm")},
    {"id": "xhs-layout", "skill_id": "baoyu-xhs-images", "skill_name": "小红书图文", "category": "xiaohongshu", "title": "选择排版密度 / 布局参数", "parameter": "layout", "parameter_label": "布局", "directory": "xhs-images-layouts", "how": "这些图只展示信息在一张图里的组织方式；不改变主题、文字和视觉风格。", "combine": "可再选择一个小红书风格参数。", "values": _items("balanced comparison dense flow list sparse")},
    {"id": "slide-style", "skill_id": "baoyu-slide-deck", "skill_name": "PPT", "category": "slide-deck", "title": "选择幻灯片视觉风格参数", "parameter": "style", "parameter_label": "风格", "directory": "slide-deck-styles", "how": "这些图只展示整套幻灯片的视觉系统；受众、页数和内容结构请在请求中补充。", "combine": "不需要再搭配图库内的其他参数图。", "values": _items("blueprint bold-editorial chalkboard corporate dark-atmospheric editorial-infographic fantasy-animation intuition-machine minimal notion pixel-art scientific sketch-notes vector-illustration vintage watercolor")},
)

CHINESE_NAMES = {
    "blueprint": "蓝图", "chalkboard": "黑板粉笔", "editorial": "编辑插画", "elegant": "优雅", "fantasy-animation": "幻想动画", "flat-doodle": "扁平涂鸦", "flat": "扁平插画", "intuition-machine": "直觉机器", "minimal": "极简", "nature": "自然", "notion": "Notion 手绘", "pixel-art": "像素艺术", "playful": "趣味", "retro": "复古", "scientific": "科学图解", "sketch-notes": "手绘笔记", "sketch": "素描", "vector-illustration": "矢量插画", "vintage": "怀旧", "warm": "温暖", "watercolor": "水彩",
    "classic": "经典清线", "dramatic": "戏剧感", "ohmsha": "欧姆社科普", "realistic": "写实", "sepia": "棕褐复古", "shoujo": "少女漫画", "vibrant": "活力", "wuxia": "武侠水墨", "cinematic": "电影分镜", "dense": "密集", "mixed": "混合", "splash": "跨页大画幅", "standard": "标准分镜", "webtoon": "条漫",
    "bold-editorial": "大胆编辑", "dark-atmospheric": "暗调氛围", "editorial-infographic": "编辑信息图", "aged-academia": "旧学术", "bold-graphic": "大胆平面", "claymation": "黏土定格", "corporate-memphis": "企业孟菲斯", "craft-handmade": "手作工艺", "cyberpunk-neon": "赛博霓虹", "ikea-manual": "宜家说明书", "kawaii": "卡哇伊", "knolling": "平铺整理", "lego-brick": "乐高积木", "origami": "折纸", "storybook-watercolor": "绘本水彩", "subway-map": "地铁图", "technical-schematic": "技术示意", "ui-wireframe": "界面线框",
    "bridge": "桥梁", "circular-flow": "循环流程", "comparison-table": "对比表", "do-dont": "正反对照", "equation": "公式关系", "feature-list": "要点清单", "fishbone": "鱼骨图", "funnel": "漏斗结构", "grid-cards": "网格卡片", "iceberg": "冰山", "journey-path": "旅程路径", "layers-stack": "层叠结构", "mind-map": "思维导图", "nested-circles": "嵌套圆", "priority-quadrants": "优先级四象限", "pyramid": "金字塔", "scale-balance": "天平平衡", "timeline-horizontal": "横向时间线", "tree-hierarchy": "树状层级", "venn": "维恩图",
    "bold": "大胆醒目", "cute": "可爱", "fresh": "清新", "pop": "流行", "corporate": "企业专业",
}

COMIC_PARAMETER_OVERRIDES = {
    "classic": ("art", "ligne-claire"), "dramatic": ("tone", "dramatic"), "ohmsha": ("preset", "ohmsha"), "realistic": ("art", "realistic"), "sepia": ("tone", "vintage"), "shoujo": ("preset", "shoujo"), "vibrant": ("tone", "energetic"), "warm": ("tone", "warm"), "wuxia": ("preset", "wuxia"),
}

PARAMETER_GUIDES = {
    "baoyu-article-illustrator": "类型 type：infographic（信息图）、scene（场景）、flowchart（流程）、comparison（对比）、framework（框架）、timeline（时间线）。风格 style：决定画面语言；配色 palette：macaron（马卡龙）、warm（暖色）、neon（霓虹），留空则沿用风格默认色。",
    "baoyu-comic": "画风 art：ligne-claire（清线）、manga（日漫）、realistic（写实）、ink-brush（水墨）、chalk（粉笔）、minimalist（极简）。基调 tone：neutral（中性）、warm（温暖）、dramatic（戏剧）、romantic（浪漫）、energetic（活力）、vintage（复古）、action（动作）。分镜 layout：standard（标准）、cinematic（电影感）、dense（密集）、splash（大画幅）、mixed（混排）、webtoon（条漫）、four-panel（四格）。",
    "baoyu-cover-image": "封面类型 type：hero（主视觉）、conceptual（概念）、typography（文字主导）、metaphor（隐喻）、scene（场景）、minimal（极简）。媒介 rendering：flat（扁平）、watercolor（水彩）、editorial（编辑插画）、photo（摄影）、3d（三维）、paper-cut（纸雕）、clay（黏土）。比例 aspect：landscape（横版）、portrait（竖版）、square（方图）。",
    "baoyu-infographic": "布局 layout：决定信息关系，如 bridge（桥梁）、funnel（漏斗）、timeline-horizontal（横向时间线）、tree-hierarchy（树状层级）、venn（维恩图）。风格 style：决定视觉语言，如 craft-handmade（手作）、corporate-memphis（企业孟菲斯）、technical-schematic（技术示意）。比例 aspect：landscape（16:9 横版）、portrait（9:16 竖版）、square（1:1 方图）或自定义。",
    "baoyu-xhs-images": "风格 style：cute（可爱）、fresh（清新）、warm（温暖）、bold（大胆醒目）、minimal（极简）、retro（复古）、pop（流行）、notion（手绘笔记）、chalkboard（黑板）、study-notes（学习笔记）、screen-print（丝网印刷）、sketch-notes（手绘笔记）。布局 layout：sparse（留白少信息）、balanced（均衡）、dense（密集知识卡）、list（清单）、comparison（对比）、flow（步骤）、mindmap（思维导图）、quadrant（四象限）。配色 palette：macaron（马卡龙）、warm（暖色）、neon（霓虹）。",
    "baoyu-slide-deck": "风格 style：决定整套幻灯片的视觉系统。受众 audience：beginners（新手）、intermediate（有基础）、experts（专家）、executives（管理层）、general（通用）。页数 slide-count：建议 8–25 页，最多 30 页；内容越长，页数通常越多。",
}


def _records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    number = 1
    for group in GROUPS:
        for value in group["values"]:
            parameter, parameter_value = group["parameter"], value
            if group["id"] == "comic-style":
                parameter, parameter_value = COMIC_PARAMETER_OVERRIDES[value]
            relative = f"screenshots/{group['directory']}/{value}.webp"
            records.append({
                "id": f"sample-{number:03d}", "skill_id": group["skill_id"], "skill_name": group["skill_name"], "category": group["category"], "group_id": group["id"], "group_title": group["title"], "parameter": parameter, "parameter_label": group["parameter_label"], "value": parameter_value, "sample_name": CHINESE_NAMES.get(value, value), "source_value": value, "source_path": relative, "image_url": f"{RAW_ROOT}/{relative}", "source_url": f"{UPSTREAM_REPOSITORY}/blob/{UPSTREAM_COMMIT}/{relative}", "how": group["how"], "combine": group["combine"],
            })
            number += 1
    return records


def build_manifest() -> dict[str, Any]:
    records = _records()
    return {"version": 1, "upstream": {"repository": UPSTREAM_REPOSITORY, "commit": UPSTREAM_COMMIT, "asset_policy": "remote-fixed-commit"}, "count": len(records), "visual_isolation_constraint": VISUAL_ISOLATION, "groups": [{key: group[key] for key in ("id", "skill_id", "skill_name", "category", "title", "parameter", "parameter_label", "how", "combine")} for group in GROUPS], "samples": records}


def validate_library(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    path = skill_dir / "assets" / "baoyu-skill-library" / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"cannot read manifest: {exc}"]}
    samples = data.get("samples", [])
    errors: list[str] = []
    if len(samples) != EXPECTED_COUNT: errors.append(f"expected {EXPECTED_COUNT} samples, got {len(samples)}")
    if [item.get("id") for item in samples] != [f"sample-{i:03d}" for i in range(1, EXPECTED_COUNT + 1)]: errors.append("sample identifiers must be contiguous")
    if len({item.get("image_url") for item in samples}) != EXPECTED_COUNT: errors.append("sample image URLs must be unique")
    for item in samples:
        if not all(isinstance(item.get(key), str) and item[key] for key in ("id", "skill_id", "group_id", "parameter", "value", "image_url", "source_url")): errors.append(f"invalid sample: {item.get('id')}")
        elif not item["image_url"].startswith(f"{RAW_ROOT}/screenshots/"): errors.append(f"unfixed image URL: {item['id']}")
    return {"valid": not errors, "count": len(samples), "group_count": len(data.get("groups", [])), "errors": errors}


def _html(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/")
    html = rf'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Baoyu 视觉 Skill 图册</title><style>
:root{{color-scheme:dark;--bg:#111315;--surface:#191d20;--line:#30363b;--text:#f2f3f4;--muted:#aab1b8;--accent:#9cd56a}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 Inter,"PingFang SC","Microsoft YaHei",sans-serif}}a{{color:inherit}}.top{{position:sticky;top:0;z-index:3;border-bottom:1px solid var(--line);background:rgba(17,19,21,.96)}}.bar,main,footer{{width:min(1320px,calc(100% - 36px));margin:auto}}.bar{{min-height:52px;display:flex;align-items:center;gap:18px}}.home{{color:var(--muted);font-size:13px;text-decoration:none}}.home:hover{{color:var(--accent)}}.jump{{display:flex;gap:12px;overflow:auto;white-space:nowrap}}.jump a{{color:var(--muted);font-size:13px;text-decoration:none}}.jump a:hover{{color:var(--text)}}main{{padding:20px 0 48px}}h1{{margin:0 0 5px;font-size:24px}}.intro{{margin:0;color:var(--muted);max-width:880px}}.steps{{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}}.step{{padding:5px 9px;border:1px solid var(--line);color:var(--muted);font-size:12px}}.search{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;margin:18px 0 28px}}input{{min-width:0;padding:10px 12px;border:1px solid var(--line);background:var(--surface);color:var(--text);font:inherit}}#result{{align-self:center;color:var(--muted);font-size:13px}}.skill{{margin-top:42px;padding-top:16px;border-top:1px solid var(--line)}}.skill:first-of-type{{margin-top:0}}.skill h2{{margin:0;font-size:20px}}.skill>p{{margin:5px 0 0;color:var(--muted)}}.group{{margin-top:20px}}.group-head{{display:flex;justify-content:space-between;gap:16px;align-items:baseline;margin-bottom:10px}}h3{{margin:0;font-size:16px}}.group-head p{{margin:0;color:var(--muted);font-size:13px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(142px,1fr));gap:12px}}.sample{{min-width:0;border:1px solid var(--line);background:var(--surface)}}.sample img{{display:block;width:100%;aspect-ratio:3/4;object-fit:contain;background:#24292e}}.sample-body{{padding:8px}}.sample-id{{color:var(--accent);font-weight:700;font-size:12px}}.sample-name{{margin:2px 0 8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px}}button{{border:1px solid var(--line);background:#20262a;color:var(--text);padding:6px 8px;font:12px inherit;cursor:pointer}}button:hover{{border-color:var(--accent);color:var(--accent)}}.use{{width:100%}}details{{margin-top:16px;border-top:1px dashed var(--line);border-bottom:1px dashed var(--line);padding:10px 0}}summary{{cursor:pointer;color:var(--text);font-weight:600}}details p{{margin:8px 0 0;color:var(--muted)}}.notice{{margin:12px 0 0;color:var(--muted);font-size:12px}}.hidden{{display:none!important}}footer{{padding:18px 0 30px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}@media(max-width:650px){{.bar,main,footer{{width:min(100% - 24px,1320px)}}.bar{{gap:12px}}.jump{{gap:10px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.search{{grid-template-columns:1fr}}}}
</style></head><body><div class="top"><nav class="bar"><a class="home" href="../readme/index.html">← 返回首页</a><div class="jump" id="jump"></div></nav></div><main><h1>Baoyu 视觉 Skill 图册</h1><p class="intro">先按创作类型进入，再选决定画风或信息结构的示例。编号只转换为参数，不会把示例图传给模型。</p><div class="steps"><span class="step">1. 选创作类型</span><span class="step">2. 选风格 / 布局</span><span class="step">3. 复制编号调用</span></div><label class="search"><input id="search" placeholder="输入 B074，或搜索：漏斗、PPT、漫画…"><span id="result">共 124 张官方示例</span></label><div id="catalog"></div></main><footer>图片来自 <a href="{UPSTREAM_REPOSITORY}" target="_blank" rel="noopener">Baoyu Skills</a> 固定提交；{VISUAL_ISOLATION}</footer><script>const DATA={payload};const catalog=document.querySelector('#catalog'),search=document.querySelector('#search'),result=document.querySelector('#result'),jump=document.querySelector('#jump');const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));const byGroup=Object.groupBy?Object.groupBy(DATA.samples,s=>s.group_id):DATA.samples.reduce((a,s)=>((a[s.group_id]??=[]).push(s),a),{{}});const bySkill=Object.groupBy?Object.groupBy(DATA.groups,g=>g.skill_id):DATA.groups.reduce((a,g)=>((a[g.skill_id]??=[]).push(g),a),{{}});function command(s){{return `使用 Baoyu ${{s.id}}：${{s.skill_name}}，${{s.parameter}}=${{s.value}}，主题：…`;}}async function copy(t){{try{{await navigator.clipboard.writeText(t);}}catch{{prompt('复制这句：',t);}}}}function card(s){{return `<article class="sample" data-search="${{esc([s.id,s.skill_name,s.group_title,s.sample_name,s.value,s.parameter].join(' ').toLowerCase())}}"><a href="${{esc(s.source_url)}}" target="_blank" rel="noopener"><img loading="lazy" src="${{esc(s.image_url)}}" alt="${{esc(s.id+' '+s.skill_name+' '+s.sample_name)}}" onerror="this.alt='图片未加载，请打开上游原图'"></a><div class="sample-body"><div class="sample-id">${{esc(s.id)}} · ${{esc(s.parameter_label)}}</div><div class="sample-name">${{esc(s.sample_name)}}</div><button class="use" data-id="${{esc(s.id)}}">使用这个${{esc(s.parameter_label)}}</button></div></article>`;}}function render(){{catalog.innerHTML='';jump.innerHTML='';for(const [skill,groups] of Object.entries(bySkill)){{const section=document.createElement('section');section.className='skill';section.id=skill;section.innerHTML=`<h2>${{esc(groups[0].skill_name)}}</h2><p>${{esc(groups.map(g=>g.how).join(' '))}}</p>`;jump.insertAdjacentHTML('beforeend',`<a href="#${{esc(skill)}}">${{esc(groups[0].skill_name)}}</a>`);for(const g of groups){{const samples=byGroup[g.id];section.insertAdjacentHTML('beforeend',`<section class="group"><div class="group-head"><h3>${{esc(g.title)}}</h3><p>${{esc(g.combine)}}</p></div><div class="grid">${{samples.map(card).join('')}}</div></section>`);}}section.insertAdjacentHTML('beforeend',`<details><summary>展开参数说明</summary><p>${{esc(GUIDES[skill])}}</p></details>`);catalog.append(section);}}catalog.addEventListener('click',e=>{{const b=e.target.closest('button[data-id]');if(!b)return;const s=DATA.samples.find(x=>x.id===b.dataset.id);copy(command(s));b.textContent='已复制调用方式';setTimeout(()=>b.textContent='使用这个'+s.parameter_label,1300);}});const GUIDES={json.dumps(PARAMETER_GUIDES, ensure_ascii=False)};search.addEventListener('input',()=>{{const q=search.value.trim().toLowerCase().replace(/\s+/g,'');let n=0;document.querySelectorAll('.sample').forEach(c=>{{const yes=!q||c.dataset.search.replace(/\s+/g,'').includes(q);c.classList.toggle('hidden',!yes);if(yes)n++;}});document.querySelectorAll('.group').forEach(g=>g.classList.toggle('hidden',!g.querySelector('.sample:not(.hidden)')));document.querySelectorAll('.skill').forEach(s=>s.classList.toggle('hidden',!s.querySelector('.group:not(.hidden)')));result.textContent=q?`匹配 ${{n}} 张；选择后复制调用方式`:'共 124 张官方示例';}});render();</script></body></html>'''


    return (html
        .replace("先按创作类型进入，再选决定画风或信息结构的示例。编号只转换为参数，不会把示例图传给模型。", "这些图片只用于理解可选风格或布局参数，不是最终成片示范。采用参数后复制调用模板，不会把图片传给模型。")
        .replace("<span class=\"step\">3. 复制编号调用</span>", "<span class=\"step\">3. 复制调用模板</span>")
        .replace("输入 B074，或搜索：漏斗、PPT、漫画…", "搜索：漏斗、PPT、漫画、黑板…")
        .replace("共 124 张官方示例", "共 124 张官方参数示意图")
        .replace(".sample img{", ".preview{display:block;width:100%;padding:0;border:0;background:transparent;cursor:zoom-in}.sample img{")
        .replace(".hidden{display:none!important}", ".preview-dialog{width:min(940px,94vw);max-height:92vh;padding:14px;border:1px solid var(--line);background:var(--surface);color:var(--text)}.preview-dialog::backdrop{background:rgba(0,0,0,.72)}.preview-dialog img{display:block;width:100%;max-height:76vh;object-fit:contain;background:#24292e}.preview-actions{display:flex;gap:8px;align-items:center;margin-top:10px}.preview-title{margin-right:auto;color:var(--muted);font-size:13px}.hidden{display:none!important}")
        .replace("<div id=\"catalog\"></div>", "<div id=\"catalog\"></div><dialog class=\"preview-dialog\" id=\"preview-dialog\"><img id=\"preview-image\" alt=\"参数示意图\"><div class=\"preview-actions\"><span class=\"preview-title\" id=\"preview-title\"></span><a class=\"source-link\" id=\"preview-source\" target=\"_blank\" rel=\"noopener\">查看上游原图</a><button type=\"button\" id=\"preview-close\">关闭</button></div></dialog>")
        .replace("function command(s){return `使用 Baoyu ${s.id}：${s.skill_name}，${s.parameter}=${s.value}，主题：…`;}", "function command(s){const value=n=>s.parameter===n?s.value:'待填写';const templates={'baoyu-article-illustrator':`使用 baoyu skill 为文章配图，type=待填写，style=${value('style')}，palette=待填写，文章/主题：…`,'baoyu-comic':`使用 baoyu skill 制作知识漫画，art=${value('art')}，tone=${value('tone')}，layout=${value('layout')}，主题：…`,'baoyu-cover-image':`使用 baoyu skill 设计文章封面，type=待填写，style=${value('style')}，rendering=待填写，aspect=待填写，主题：…`,'baoyu-infographic':`使用 baoyu skill 设计信息图，style=${value('style')}，layout=${value('layout')}，aspect=待填写，主题：…`,'baoyu-xhs-images':`使用 baoyu skill 设计小红书图文，style=${value('style')}，layout=${value('layout')}，palette=待填写，主题：…`,'baoyu-slide-deck':`使用 baoyu skill 制作 PPT，style=${value('style')}，audience=待填写，slide-count=待填写，主题：…`};return templates[s.skill_id];}")
        .replace("<a href=\"${esc(s.source_url)}\" target=\"_blank\" rel=\"noopener\"><img loading=\"lazy\"", "<button class=\"preview\" type=\"button\" data-preview=\"${esc(s.id)}\"><img loading=\"lazy\"")
        .replace("onerror=\"this.alt='图片未加载，请打开上游原图'\"></a><div class=\"sample-body\"><div class=\"sample-id\">${esc(s.id)} · ${esc(s.parameter_label)}</div>", "onerror=\"this.alt='图片未加载，请在弹窗中打开上游原图'\"></button><div class=\"sample-body\"><div class=\"sample-id\">${esc(s.parameter_label)}</div>")
        .replace("<div class=\"sample-id\">${esc(s.parameter_label)}</div>", "")
        .replace("使用这个${esc(s.parameter_label)}", "采用这个${esc(s.parameter_label)}")
        .replace("使用这个'+s.parameter_label", "采用这个'+s.parameter_label")
        .replace("已复制调用方式", "已复制参数调用方式")
        .replace("catalog.append(section);}catalog.addEventListener", "catalog.append(section);}}catalog.addEventListener")
        .replace("catalog.addEventListener('click',e=>{const b=e.target.closest('button[data-id]');if(!b)return;", "const dialog=document.querySelector('#preview-dialog'),previewImage=document.querySelector('#preview-image'),previewTitle=document.querySelector('#preview-title'),previewSource=document.querySelector('#preview-source');document.querySelector('#preview-close').addEventListener('click',()=>dialog.close());catalog.addEventListener('click',e=>{const preview=e.target.closest('button[data-preview]');if(preview){const s=DATA.samples.find(x=>x.id===preview.dataset.preview);previewImage.src=s.image_url;previewImage.alt=s.skill_name+' · '+s.parameter_label+'参数 · '+s.sample_name;previewTitle.textContent=s.skill_name+' · '+s.parameter_label+'参数：'+s.sample_name;previewSource.href=s.source_url;dialog.showModal();return;}const b=e.target.closest('button[data-id]');if(!b)return;")
        .replace("选择后复制调用方式", "选择后复制参数调用方式")
    )


def sync(*, skill_dir: Path = SKILL_DIR) -> dict[str, Any]:
    library = skill_dir / "assets" / "baoyu-skill-library"
    library.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    (library / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (library / "index.html").write_text(_html(manifest), encoding="utf-8")
    return validate_library(skill_dir=skill_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and select Baoyu visual examples")
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--check", action="store_true", help="report pinned source revision")
    parser.add_argument("--skill-dir", type=Path, default=SKILL_DIR)
    args = parser.parse_args(argv)
    skill_dir = args.skill_dir.resolve(strict=False)
    if args.sync: output: Any = sync(skill_dir=skill_dir)
    elif args.validate: output = validate_library(skill_dir=skill_dir)
    elif args.check: output = {"repository": UPSTREAM_REPOSITORY, "commit": UPSTREAM_COMMIT, "asset_policy": "remote-fixed-commit"}
    else: parser.error("choose --sync, --validate, or --check")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
