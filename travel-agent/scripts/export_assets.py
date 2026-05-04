#!/usr/bin/env python3
"""Export slides.json, image_prompts.json, and image_prompts.md."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMAGE_STYLE_RULES = (
    "整体风格：原创卡通可爱旅行手账，竖版手机壁纸构图，适合 iPhone Pro Max 类大屏；"
    "奶油色纸张纹理背景、彩铅和水彩质感、粗细自然的手绘黑色描边、贴纸拼贴、胶带、邮戳、"
    "可爱小图标、星星爱心云朵、少量虚线箭头和抽象旅行动线；"
    "画面活泼但不拥挤，留出手机锁屏可视空间。"
)

TEXT_RULES = (
    "文字要求：只保留重点短句，每张图中文字不超过 4 处，单处尽量 4-10 个汉字；"
    "中文字体风格参考金陵体、圆体、手写圆润标题字，要求清晰可读；"
    "必须加入小号水印/印章文字“扬仔游星球”，放在右下角或边缘，不遮挡主体。"
)

COPYRIGHT_RULES = (
    "版权限制：参考的是可爱手账、贴纸拼贴、手绘旅行日记这类通用视觉方向；"
    "不要复刻任何参考图的具体版式、构图、标题、路线、图标排列、水印、人物或独特表达；"
    "不要使用真实照片、博主截图、真实地图、真实路线图、平台水印、品牌 Logo 或受版权保护角色。"
)


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def selected_from_brief(brief: str) -> tuple[str, str]:
    city = re.search(r"^- 城市 slug：(.+)$", brief, re.MULTILINE)
    topic = re.search(r"^- 主题 slug：(.+)$", brief, re.MULTILINE)
    if not city or not topic:
        raise SystemExit("brief.md 缺少城市 slug 或主题 slug")
    return city.group(1).strip(), topic.group(1).strip()


def scripts(city: dict[str, str], topic: dict[str, str]) -> list[dict[str, str]]:
    rows = [
        ("封面", f"{city['name']} {topic['name']} 封面手账，中心是可爱大标题和城市代表元素，四周点缀行李箱、相机、云朵和贴纸。"),
        ("城市速览", f"{city['name']} 旅行印象拼贴，展示 3-4 个代表景点的卡通轮廓、交通卡、天气贴纸和小邮戳，不画真实地图。"),
        ("食", f"{city['name']} 美食贴纸页，展示 3 个代表小吃/饮品的可爱插画和短标签，像手账便签一样排版。"),
        ("住行", "住宿区域与交通方式合并成一张清爽信息卡，酒店、车票、站牌、行李箱和步行箭头都用可爱图标呈现。"),
        ("游", "景点游玩页，使用 3 个景点小插画和抽象虚线串联，强调这是灵感动线，不是真实路线图。"),
        ("购娱", "购物伴手礼与晚间活动拼贴，购物袋、夜景、演出门票、咖啡杯和小星星组成轻松画面。"),
        ("3 天计划", "三天行程手账时间轴，Day 1-3 分成三块贴纸便签，每天只写关键词，配少量虚线箭头。"),
        ("避坑清单", "出发前可爱提醒卡，包含预约、营业时间、天气、交通、行李等原创图标，像贴在手账最后一页。"),
    ]
    return [
        {
            "card": index,
            "title": title,
            "script": script,
            "prompt": (
                f"原创小红书旅行攻略卡通插画，第 {index} 张，主题：{title}。{script}"
                f"{IMAGE_STYLE_RULES}{TEXT_RULES}{COPYRIGHT_RULES}"
                "高清、细节精致、竖版 9:16 附近构图、适合手机壁纸和小红书封面。"
            ),
        }
        for index, (title, script) in enumerate(rows, 1)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    args = parser.parse_args()

    brief_paths = list((ROOT / "outputs").glob(f"{args.date}-*/brief.md"))
    if not brief_paths:
        raise SystemExit("请先运行 pick_topic.py 和 generate_post.py")
    out_dir = brief_paths[0].parent
    city_slug, topic_slug = selected_from_brief(brief_paths[0].read_text(encoding="utf-8"))
    cities = {item["slug"]: item for item in read_csv(ROOT / "cities.csv")}
    topics = {item["slug"]: item for item in read_csv(ROOT / "topics.csv")}
    data = scripts(cities[city_slug], topics[topic_slug])
    prompt_data = [
        {
            "card": item["card"],
            "title": item["title"],
            "prompt": item["prompt"],
            "filename": f"img_{item['card']}.png",
        }
        for item in data
    ]

    (out_dir / "slides.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.json").write_text(json.dumps(prompt_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.md").write_text(
        "\n\n".join(
            [
                "# 每张图的卡通绘图 prompt",
                *[f"## 图 {item['card']}｜{item['title']}\n\n### 画面脚本\n{item['script']}\n\n### Prompt\n{item['prompt']}" for item in data],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
