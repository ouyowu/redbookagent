#!/usr/bin/env python3
"""Quality wrapper for concrete image scripts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

import export_assets as ea
from generate_post_quality import read_optional_csv, season_window, split

ROOT = Path(__file__).resolve().parents[1]
STYLE = getattr(ea, "IMAGE_STYLE_RULES", getattr(ea, "STYLE", "原创卡通可爱旅行手账风，高清竖图。"))
TEXT_RULES = getattr(ea, "TEXT_RULES", getattr(ea, "TEXT", "图片中文字少而清晰，标题圆润可爱。"))
COPYRIGHT_RULES = getattr(ea, "COPYRIGHT_RULES", getattr(ea, "COPYRIGHT", "不复制博主图片、截图、真实地图、路线图、平台水印或品牌Logo。"))
LANGUAGE_VARIANTS = getattr(ea, "LANGUAGE_VARIANTS", [
    {"code": "zh-Hans", "name": "中文简体", "watermark": "扬仔游星球", "suffix": "zh-Hans", "prompt_file": "image_prompts_zh-Hans.md"},
    {"code": "zh-Hant", "name": "中文繁体", "watermark": "揚仔遊星球", "suffix": "zh-Hant", "prompt_file": "image_prompts_zh-Hant.md"},
    {"code": "en", "name": "English", "watermark": "Yangzai Travel Planet", "suffix": "en", "prompt_file": "image_prompts_en.md"},
])


def join(items: list[str]) -> str:
    return "、".join(items)


def selected_from_brief(brief: str) -> tuple[str, str]:
    if hasattr(ea, "selected_from_brief"):
        return ea.selected_from_brief(brief)
    if hasattr(ea, "selected"):
        return ea.selected(brief)
    city = re.search(r"^- 城市 slug：(.+)$", brief, re.M)
    theme = re.search(r"^- 内容主题：(.+)$", brief, re.M)
    if not city:
        raise SystemExit("brief.md 缺少城市 slug")
    return city.group(1).strip(), theme.group(1).strip() if theme else "热门旅游攻略"


def lang_rule(language: dict[str, str]) -> str:
    code = language["code"]
    watermark = language["watermark"]
    if code == "zh-Hans":
        return f"语言版本：中文简体；所有可见文字必须是简体中文；水印为“{watermark}”。"
    if code == "zh-Hant":
        return f"語言版本：繁體中文；所有可見文字必須是繁體中文；水印為「{watermark}」。"
    return f"Language version: English; all visible text must be concise English; watermark: {watermark}."


def prompt_only(item: dict[str, object], language: dict[str, str]) -> str:
    return (
        f"原创小红书旅行攻略卡通插画，第 {item['card']} 张，主题：{item['title']}。"
        f"{item['script']} {STYLE} {TEXT_RULES} {COPYRIGHT_RULES} {lang_rule(language)} "
        "高清、细节精致、竖版9:16构图，适合手机壁纸和小红书封面，文字少但重点明确，排版美观。"
    )


def scripts(city: dict[str, str], theme: str) -> list[dict[str, object]]:
    foods = split(city.get("food", ""))
    stays = split(city.get("stay", ""))
    transport = split(city.get("transport", ""))
    shopping = split(city.get("shopping", ""))
    fun = split(city.get("entertainment", ""))
    attractions = split(city.get("top_attractions", "")) or split(city.get("visit", ""))
    restaurants = split(city.get("restaurants", "")) or foods
    best, rainy, shoulder = season_window(city)
    rows = [
        ("封面", f"{city['name']} {theme} 实用攻略封面，显示季节提示“{best}”、备用提醒“{rainy}”。"),
        ("什么时候去", f"{city['name']} 淡旺季和天气卡：{best}、{rainy}、{shoulder}，加工作日上午和雨天备用。"),
        ("景点Top清单", f"{city['name']} 推荐景点Top10：{join(attractions[:10])}，每个点放开放时间、预约、交通耗时图标。"),
        ("本地吃喝清单", f"{city['name']} 餐厅/美食Top10：{join(restaurants[:10])}，提醒查推荐菜、人均和排队。"),
        ("住哪里最方便", f"{city['name']} 住宿区域：{join(stays)}，按吃喝、景点距离、交通、噪音、预算比较。"),
        ("交通怎么搭", f"{city['name']} 交通：{join(transport)}，写机场进城、市内移动、高峰缓冲、晚归兜底。"),
        ("购物值得买", f"{city['name']} 购物：{join(shopping + foods[:2])}，提醒保质期、议价、携带限制。"),
        ("夜生活玩法", f"{city['name']} 夜间活动：{join(fun)}，标出结束时间、返程交通、最低消费和雨天备用。"),
        ("避坑解法", f"{city['name']} 避坑解决办法：预约、营业时间、价格、排队、天气备用、版权来源。"),
        ("发布前核验", f"{city['name']} 检查卡：官网、地图近期评价、交通票价、餐厅营业状态、图片版权。"),
    ]
    return [{"card": i, "title": title, "script": script} for i, (title, script) in enumerate(rows, 1)]


def render_prompt_file(data: list[dict[str, object]], language: dict[str, str]) -> str:
    chunks = [f"# 可直接复制给 ChatGPT 生图的 Prompt｜{language['name']}"]
    for item in data:
        chunks.append(f"## 图 {item['card']}｜{item['title']}\n\n### 画面脚本\n{item['script']}\n\n### Prompt\n```text\n{prompt_only(item, language)}\n```")
    return "\n\n".join(chunks) + "\n"


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    args = parser.parse_args()

    read_csv = ea.read_csv
    try:
        cities = {item["slug"]: item for item in read_csv(ROOT / "cities.csv")}
    except TypeError:
        cities = {item["slug"]: item for item in read_csv("cities.csv")}
    facts = {item["slug"]: item for item in read_optional_csv(ROOT / "city_facts.csv")}
    brief_paths = list((ROOT / "outputs").glob(f"{args.date}-*/brief.md"))
    if not brief_paths:
        raise SystemExit("请先运行 pick_topic.py 和 generate_post.py")
    out_dir = brief_paths[0].parent
    city_slug, theme = selected_from_brief(brief_paths[0].read_text(encoding="utf-8"))
    city = {**cities[city_slug], **facts.get(city_slug, {})}
    data = scripts(city, theme)

    prompt_data = []
    for item in data:
        item_prompts = []
        for language in LANGUAGE_VARIANTS:
            prompt = prompt_only(item, language)
            row = {
                "card": item["card"],
                "title": item["title"],
                "language": language["code"],
                "language_name": language["name"],
                "watermark": language["watermark"],
                "prompt": prompt,
                "filename": f"img_{item['card']}_{language['suffix']}.png",
            }
            prompt_data.append(row)
            item_prompts.append(row)
        item["prompts"] = item_prompts
        item["prompt"] = item_prompts[0]["prompt"]

    (out_dir / "slides.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.json").write_text(json.dumps(prompt_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for language in LANGUAGE_VARIANTS:
        (out_dir / language["prompt_file"]).write_text(render_prompt_file(data, language), encoding="utf-8")
    (out_dir / "image_prompts.md").write_text("\n\n".join(render_prompt_file(data, language) for language in LANGUAGE_VARIANTS), encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
