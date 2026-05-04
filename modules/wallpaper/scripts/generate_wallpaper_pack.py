#!/usr/bin/env python3
"""Generate a wallpaper pack brief and image prompts from local CSV pools."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs"


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def pick(items: list[dict[str, str]], date_value: str, offset: int = 0) -> dict[str, str]:
    index = (sum(ord(ch) for ch in date_value) + offset) % len(items)
    return items[index]


def split(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def language_rules(code: str) -> dict[str, str]:
    rules = {
        "zh-Hans": {
            "name": "中文简体",
            "suffix": "zh-Hans",
            "watermark": "扬仔游星球",
            "text": "只使用简体中文，字体参考金陵体、圆体、可爱手写圆润标题字。",
        },
        "zh-Hant": {
            "name": "中文繁体",
            "suffix": "zh-Hant",
            "watermark": "揚仔遊星球",
            "text": "只使用繁體中文，字體參考可愛圓潤中文手寫風。",
        },
        "en": {
            "name": "English",
            "suffix": "en",
            "watermark": "Yangzai Travel Planet",
            "text": "Use short natural English only, with a warm modern humanist sans-serif font similar to claude.com.",
        },
    }
    return rules[code]


def wallpaper_prompt(style: dict[str, str], product: dict[str, str], index: int, language: dict[str, str]) -> str:
    return (
        f"Original vertical mobile wallpaper, card {index}, product: {product['name']}. "
        f"Visual style: {style['visual_style']}. Palette: {style['palette']}. "
        "Cute, polished, high-resolution, clean composition, suitable for iPhone Pro Max style lock screen, 1024x1536 vertical canvas. "
        "Keep the top lock-screen time area and bottom gesture area visually breathable. "
        f"Text rule: {language['text']} Keep text minimal: max 4 text areas, short phrases only, beautiful layout, no typos, no gibberish. "
        f"Add a small subtle watermark/stamp near the edge: {language['watermark']}. "
        "No real photos, no copyrighted characters, no brand logos, no platform watermarks, no copied wallpaper layout, no celebrity likeness."
    )


def build_pack(date_value: str, style_slug: str | None, product_slug: str | None) -> tuple[Path, dict[str, str], dict[str, str], list[dict[str, str]]]:
    styles = read_csv(ROOT / "data" / "wallpaper_styles.csv")
    products = read_csv(ROOT / "data" / "wallpaper_products.csv")
    style = next((item for item in styles if item["slug"] == style_slug), None) if style_slug else pick(styles, date_value)
    product = next((item for item in products if item["slug"] == product_slug), None) if product_slug else pick(products, date_value, offset=7)
    if style is None:
        raise SystemExit(f"找不到壁纸风格：{style_slug}")
    if product is None:
        raise SystemExit(f"找不到壁纸商品：{product_slug}")

    out_dir = OUTPUT_ROOT / f"{date_value}-{product['slug']}-{style['slug']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pack_size = int(product["pack_size"])
    prompts: list[dict[str, str]] = []
    for index in range(1, pack_size + 1):
        for code in split(product["languages"]):
            lang = language_rules(code)
            prompts.append(
                {
                    "card": index,
                    "language": code,
                    "language_name": lang["name"],
                    "filename": f"wallpaper_{index:02d}_{lang['suffix']}.png",
                    "prompt": wallpaper_prompt(style, product, index, lang),
                }
            )
    return out_dir, style, product, prompts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--style")
    parser.add_argument("--product")
    args = parser.parse_args()

    out_dir, style, product, prompts = build_pack(args.date, args.style, args.product)
    brief = "\n".join(
        [
            f"# 壁纸包选题｜{product['name']}｜{style['name']}",
            "",
            f"- 日期：{args.date}",
            f"- 商品：{product['name']}",
            f"- 风格：{style['name']}",
            f"- 人群：{product['audience']}",
            f"- 张数：{product['pack_size']} 张基础图，每张包含 {product['languages']} 语言版本",
            f"- 使用场景：{style['use_case']}",
            f"- 商业备注：{product['commercial_note']}",
            "",
        ]
    )
    (out_dir / "brief.md").write_text(brief, encoding="utf-8")
    (out_dir / "image_prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.md").write_text(
        "\n\n".join([f"## {item['filename']}\n{item['prompt']}" for item in prompts]) + "\n",
        encoding="utf-8",
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
