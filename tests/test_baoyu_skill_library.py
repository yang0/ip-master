import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = PROJECT_ROOT / "ip-master" / "assets" / "baoyu-skill-library" / "index.html"


def test_baoyu_visual_skill_library_is_complete_and_source_linked() -> None:
    html = LIBRARY.read_text(encoding="utf-8")

    for skill_id in ("article", "comic", "cover", "infographic", "xhs", "slide"):
        assert f'id="{skill_id}"' in html
    for image in (
        "baoyu-article-illustration.webp",
        "baoyu-comic.webp",
        "baoyu-cover.webp",
        "baoyu-infographic.webp",
        "baoyu-slide-deck.webp",
    ):
        assert image in html
        assert (PROJECT_ROOT / "ip-master" / "assets" / "showcase" / image).is_file()
    assert "../generated/yazai-todays-outfit-cute-balanced.png" in html
    assert (
        PROJECT_ROOT / "ip-master" / "assets" / "generated" / "yazai-todays-outfit-cute-balanced.png"
    ).is_file()
    assert "../../../comic/silver-short/01-cover-silver-energetic-manga-standard-color.png" in html
    assert (PROJECT_ROOT / "comic" / "silver-short" / "01-cover-silver-energetic-manga-standard-color.png").is_file()
    assert "../../../slide-deck/hangzhou-attractions/01-slide-hangzhou-attractions.png" in html
    assert (PROJECT_ROOT / "slide-deck" / "hangzhou-attractions" / "01-slide-hangzhou-attractions.png").is_file()
    for skill in (
        "baoyu-article-illustrator",
        "baoyu-comic",
        "baoyu-cover-image",
        "baoyu-infographic",
        "baoyu-xhs-images",
        "baoyu-slide-deck",
    ):
        assert f"skills/{skill}" in html
    for label in ("图片结构", "画面风格", "配色", "画风", "情绪基调", "分镜布局", "封面类型", "绘制媒介", "布局", "风格", "画幅", "受众", "页数"):
        assert label in html
    assert "copy-command" in html
    assert "navigator.clipboard.writeText" in html
    assert "data-preview" in html
    assert html.count("object-fit: contain") >= 3
    assert html.count('class="enum-guide"') == 6
    assert "parameter-list" not in html
    assert '<details class="enum-guide">' not in html
    assert "<summary>全部可选值（中文）</summary>" not in html
    for value in ("信息图（<code>infographic</code>）", "二元对比（<code>binary-comparison</code>）", "蓝图技术（<code>blueprint</code>）"):
        assert value in html

    referenced_paths = re.findall(r'(?:src|data-preview)="([^"]+)"', html)
    missing = [path for path in referenced_paths if not (LIBRARY.parent / path).resolve().is_file()]
    assert missing == []
