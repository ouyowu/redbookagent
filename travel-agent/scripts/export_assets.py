#!/usr/bin/env python3
"""Export slides, image prompts, and NotebookLM packs for the city content matrix."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = "原创卡通可爱旅行手账风，奶油纸张纹理，彩铅和水彩质感，手绘黑色描边，贴纸拼贴，胶带，邮戳，可爱小图标，少量虚线箭头，竖版9:16，适合手机壁纸和小红书封面。"
TEXT = "图片中文字少而清晰，每张不超过4处文字；中文参考金陵体、圆体、手写圆润标题字；英文为温和现代人文无衬线字体；必须加入小号品牌水印。"
COPYRIGHT = "不要复刻参考图版式、路线、图标排列或水印；不要真实照片、博主截图、真实地图、真实路线图、平台水印、品牌Logo或受版权保护角色。"
LANGS = [
    ("zh-Hans", "中文简体", "扬仔游星球", "image_prompts_zh-Hans.md", "notebooklm_image_pack_zh-Hans.md"),
    ("zh-Hant", "中文繁体", "揚仔遊星球", "image_prompts_zh-Hant.md", "notebooklm_image_pack_zh-Hant.md"),
    ("en", "English", "Yangzai Travel Planet", "image_prompts_en.md", "notebooklm_image_pack_en.md"),
]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d-%H%M")


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def selected(brief: str) -> tuple[str, str]:
    city = re.search(r"^- 城市 slug：(.+)$", brief, re.M)
    theme = re.search(r"^- 内容主题：(.+)$", brief, re.M)
    if not city:
        raise SystemExit("brief.md 缺少城市 slug")
    return city.group(1).strip(), theme.group(1).strip() if theme else "热门旅游内容矩阵"


def slide_rows(city: dict[str, str], theme: str) -> list[tuple[str, str]]:
    n = city["name"]
    return [
        ("封面", f"{n} {theme} 封面手账，中心是可爱大标题和城市代表元素。"),
        ("城市内容矩阵", f"{n} 食住行游购娱六大板块索引页，展示美食、住宿、交通、景点、购物、娱乐。"),
        ("本地美食地图", f"{n} 当地人推荐关键词、美食片区、餐厅、小馆、早餐、甜品和伴手礼。"),
        ("火锅小馆榜单", f"{n} 火锅/代表热菜、苍蝇小馆、烟火气街巷和排队提醒。"),
        ("住宿交通攻略", f"{n} 住哪里、机场高铁进城、地铁打车、少绕路动线和返程提醒。"),
        ("景点游玩清单", f"{n} 首次必看景点、citywalk、博物馆、拍照点、周边一日游。"),
        ("购物值得买", f"{n} 商圈、商场、市集、文创店、特产、零食和什么值得买。"),
        ("夜生活玩法", f"{n} 夜游、夜景、演出、livehouse、夜市、微醺和晚归交通。"),
        ("避坑事实核验", f"{n} 预约、营业时间、价格区间、排队、天气备用和版权风险自查。"),
        ("发布出图清单", f"{n} 小红书标题、正文、标签、图片prompt和三语言版本发布前检查。"),
    ]


def lang_rule(code: str, watermark: str) -> str:
    if code == "zh-Hans":
        return f"语言版本：中文简体；图片内所有文字必须是简体中文；水印文字为“{watermark}”；不要出现繁体字或英文说明。"
    if code == "zh-Hant":
        return f"語言版本：繁體中文；圖片內所有文字必須是繁體中文；水印文字為「{watermark}」；不要出現簡體字或英文說明。"
    return f"Language version: English; all visible text must be short natural English; watermark text: {watermark}; do not include Chinese characters."


def prompt_for(card: int, title: str, script: str, code: str, watermark: str) -> str:
    return f"原创小红书旅行攻略卡通插画，第{card}张，主题：{title}。{script}{STYLE}{TEXT}水印/印章文字：{watermark}。{COPYRIGHT}{lang_rule(code, watermark)}高清竖图，画面活泼但不拥挤，留出手机锁屏可视空间。"


def render_prompts(items: list[dict[str, object]], code: str, name: str) -> str:
    chunks = [f"# 每张图的卡通绘图 prompt｜{name}"]
    for item in items:
        prompts = [p for p in item["prompts"] if p["language"] == code]
        prompt = prompts[0]
        chunks.append(f"## 图 {item['card']}｜{item['title']}\n\n### 画面脚本\n{item['script']}\n\n### Prompt\n文件名：`{prompt['filename']}`\n\n{prompt['prompt']}")
    return "\n\n".join(chunks) + "\n"


def render_pack(city: dict[str, str], theme: str, items: list[dict[str, object]], code: str, watermark: str) -> str:
    header = "NotebookLM 手动出图工作包" if code == "zh-Hans" else ("NotebookLM 手動出圖工作包" if code == "zh-Hant" else "NotebookLM Image Pack")
    lines = [f"# {header}｜{city['name']}｜{theme}", "请一次只生成一张图，确认风格后再生成下一张。", f"统一品牌水印：{watermark}", "整体风格：原创可爱旅行手账、贴纸拼贴、水彩彩铅、少字高可读。", "版权边界：不复制博主图片、截图、真实地图、路线图、平台水印或具体参考图版式。"]
    for item in items:
        prompt = next(p for p in item["prompts"] if p["language"] == code)
        lines += [f"## 图 {item['card']}｜{item['title']}", f"画面脚本：{item['script']}", "```text", prompt["prompt"], "```"]
    return "\n\n".join(lines) + "\n"


def wallpaper_prompt(city: dict[str, str], theme: str) -> str:
    return f"# {city['name']} 治愈系城市壁纸描述词\n\n{city['name']} 城市治愈系旅行风景壁纸，主题围绕“{theme}”，竖版超高清，适合 iPhone/Android 大屏。突出城市地标、街区、山水或夜景层次，温柔通透光线，原创卡通旅行手账气质，少量文字或仅角落水印“扬仔游星球”。不要真实广告牌、不要真实地图、不要平台水印、不要复杂攻略排版。\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    args = parser.parse_args()
    briefs = list((ROOT / "outputs").glob(f"{args.date}-*/brief.md"))
    if not briefs:
        raise SystemExit("请先运行 pick_topic.py 和 generate_post.py")
    out = briefs[0].parent
    city_slug, theme = selected(briefs[0].read_text(encoding="utf-8"))
    city = {x["slug"]: x for x in read_csv("cities.csv")}[city_slug]
    items = []
    for card, (title, script) in enumerate(slide_rows(city, theme), 1):
        prompts = []
        for code, name, watermark, _, _ in LANGS:
            prompts.append({"card": card, "title": title, "language": code, "language_name": name, "watermark": watermark, "filename": f"img_{card}_{code}.png", "prompt": prompt_for(card, title, script, code, watermark)})
        items.append({"card": card, "title": title, "script": script, "prompt": prompts[0]["prompt"], "prompts": prompts})
    prompt_data = [p for item in items for p in item["prompts"]]
    (out / "slides.json").write_text(json.dumps([{k: v for k, v in item.items() if k != "prompts"} for item in items], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "image_prompts.json").write_text(json.dumps(prompt_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "image_prompts.md").write_text("\n\n".join([render_prompts(items, code, name) for code, name, _, _, _ in LANGS]), encoding="utf-8")
    for code, name, watermark, prompt_file, pack_file in LANGS:
        (out / prompt_file).write_text(render_prompts(items, code, name), encoding="utf-8")
        (out / pack_file).write_text(render_pack(city, theme, items, code, watermark), encoding="utf-8")
    (out / "notebooklm_image_pack.md").write_text(render_pack(city, theme, items, "zh-Hans", "扬仔游星球"), encoding="utf-8")
    (out / "wallpaper_prompt.md").write_text(wallpaper_prompt(city, theme), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
