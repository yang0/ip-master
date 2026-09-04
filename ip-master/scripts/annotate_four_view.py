#!/usr/bin/env python3
"""Add deterministic identity metadata to a generated four-view board."""

from __future__ import annotations

import argparse
from pathlib import Path


def annotate_four_view(
    source: Path,
    destination: Path,
    *,
    name: str,
    age: int,
    height_cm: int,
    weight_kg: float,
) -> Path:
    """Add a readable metadata strip without changing the original image."""

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required to annotate a four-view image") from exc
    if not source.is_file():
        raise FileNotFoundError(source)
    if not name.strip() or age <= 0 or height_cm <= 0 or weight_kg <= 0:
        raise ValueError("name, age, height_cm, and weight_kg must be positive")

    with Image.open(source) as original:
        image = original.convert("RGB")
    strip_height = max(90, image.height // 16)
    canvas = Image.new("RGB", (image.width, image.height + strip_height), "#242424")
    canvas.paste(image, (0, strip_height))
    draw = ImageDraw.Draw(canvas)
    font_candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    font_path = next((path for path in font_candidates if path.is_file()), None)
    font = ImageFont.truetype(str(font_path), max(24, strip_height // 3)) if font_path else ImageFont.load_default()
    text = f"{name}  |  {age}岁  |  {height_cm}cm  |  {weight_kg:g}kg  |  人物四视图身份参考"
    draw.text((image.width // 2, strip_height // 2), text, fill="#f3f1e9", font=font, anchor="mm")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG", optimize=True)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Annotate a generated four-view identity board")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--age", required=True, type=int)
    parser.add_argument("--height-cm", required=True, type=int)
    parser.add_argument("--weight-kg", required=True, type=float)
    args = parser.parse_args(argv)
    annotate_four_view(
        args.source,
        args.destination,
        name=args.name,
        age=args.age,
        height_cm=args.height_cm,
        weight_kg=args.weight_kg,
    )
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
