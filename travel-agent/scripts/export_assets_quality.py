#!/usr/bin/env python3
"""Quality wrapper for concrete image scripts."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import export_assets as ea
from generate_post_quality import read_optional_csv, season_window, split


ROOT = Path(__file__).resolve().parents[1]


def join(items: list[str]) -> str:
    return "、".join(items)


def scripts(city: dict[str, str], theme: str) -> list[dict[str, str]]:
    foods = split(city["food"])
    stays = split(city["stay"])
    transport = split(city["transport"])
    shopping = split(city["shopping"])
    fun = split(city["entertainment"])
    attractions = split(city.get("top_attractions", "")) or split(city["visit"])
    restaurants = split(city.get("restaurants", "")) or foods
    best, rainy, shoulder = season_window(city, "zh-Hans")
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
    return [
        {
            "card": index,
            "title": title,
            "script": script,
            "prompt": f"原创小红书旅行攻略卡通插画，第 {index} 张，主题：{title}。{script}{ea.IMAGE_STYLE_RULES}{ea.TEXT_RULES}{ea.COPYRIGHT_RULES}高清、细节精致、竖版 9:16 附近构图、适合手机壁纸和小红书封面。",
        }
        for index, (title, script) in enumerate(rows, 1)
    ]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    args = parser.parse_args()

    cities = {item["slug"]: item for item in ea.read_csv(ROOT / "cities.csv")}
    facts = {item["slug"]: item for item in read_optional_csv(ROOT / "city_facts.csv")}
    brief_paths = list((ROOT / "outputs").glob(f"{args.date}-*/brief.md"))
    if not brief_paths:
        raise SystemExit("请先运行 pick_topic.py 和 generate_post.py")
    out_dir = brief_paths[0].parent
    city_slug, theme = ea.selected_from_brief(brief_paths[0].read_text(encoding="utf-8"))
    city = {**cities[city_slug], **facts.get(city_slug, {})}
    data = scripts(city, theme)

    prompt_data = []
    for item in data:
        for language in ea.LANGUAGE_VARIANTS:
            prompt_data.append(
                {
                    "card": item["card"],
                    "title": item["title"],
                    "language": language["code"],
                    "language_name": language["name"],
                    "watermark": language["watermark"],
                    "prompt": ea.localized_prompt(item, language),
                    "filename": f"img_{item['card']}_{language['suffix']}.png",
                }
            )
    (out_dir / "slides.json").write_text(ea.json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.json").write_text(ea.json.dumps(prompt_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for language in ea.LANGUAGE_VARIANTS:
        (out_dir / language["prompt_file"]).write_text(ea.render_image_prompts_single_language(data, language), encoding="utf-8")
    (out_dir / "image_prompts.md").write_text(
        "\n\n".join(
            [
                "# 可直接复制给 ChatGPT 生图的 Prompt",
                *[
                    "\n\n".join(
                        [
                            f"## 图 {item['card']}｜{item['title']}",
                            *[
                                f"### {language['name']}\n```text\n{ea.prompt_only(item, language)}\n```"
                                for language in ea.LANGUAGE_VARIANTS
                            ],
                        ]
                    )
                    for item in data
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
