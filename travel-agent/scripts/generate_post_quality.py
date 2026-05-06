#!/usr/bin/env python3
"""Quality wrapper for concrete, practical travel copy."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

import generate_post as gp

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)


def split(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;；]", value or "") if item.strip()]


def join(items: list[str]) -> str:
    return "、".join(items)


def season_window(city: dict[str, str]) -> tuple[str, str, str]:
    parts = split(city.get("season", ""))
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    tropical = any(key in city.get("country", "") for key in ["印度尼西亚", "泰国", "马来西亚", "新加坡", "菲律宾", "越南", "柬埔寨", "老挝"])
    return ("5-9月户外更稳", "11-3月雨水更多", "4月/10月看天气") if tropical else ("春秋更适合首次去", "大假期更拥挤", "工作日上午更省心")


def cycle(items: list[str], count: int) -> list[str]:
    if not items:
        return []
    return [items[i % len(items)] for i in range(count)]


def practical_items(city: dict[str, str], topic: dict[str, object]) -> list[str]:
    slug = str(topic.get("slug", ""))
    foods = split(city.get("food", ""))
    stays = split(city.get("stay", ""))
    transport = split(city.get("transport", ""))
    visits = split(city.get("visit", ""))
    shopping = split(city.get("shopping", ""))
    fun = split(city.get("entertainment", ""))
    attractions = split(city.get("top_attractions", "")) or visits
    restaurants = split(city.get("restaurants", "")) or foods
    transport_tips = split(city.get("transport_tips", ""))
    pitfalls = split(city.get("pitfalls", ""))
    best, rainy, shoulder = season_window(city)

    if slug in {"restaurants", "food-overview", "fly-restaurants", "hotpot", "breakfast", "desserts"}:
        return [f"{item}：写清推荐菜、所在片区、排队强度、是否需订位和近期人均，发布前用地图再核验。" for item in restaurants[:10]]
    if slug == "transport":
        return transport_tips or [
            f"抵达：先比较 {join(transport[:2])}，行李多或晚归再用 Grab/打车兜底。",
            f"住宿基地：想吃喝逛街优先看 {join(stays[:2])}；想顺景点再看 {join(stays[2:4])}。",
            "避坑：不要把跨城区移动塞在早晚高峰。",
            "解法：每天只锁一个大区域，一个必去点，旁边顺路安排吃饭和购物。",
        ]
    if slug in {"attractions", "citywalk", "photospots", "museums", "daytrip"}:
        return [f"{item}：搭配附近吃喝/商圈一起排，发布前核对开放时间、预约门票和交通耗时。" for item in attractions[:10]]
    if slug == "hotels":
        return [f"{item}：先查到核心景点的通勤时间、夜间返程、噪音和预算，再决定要不要住。" for item in stays[:10]]
    if slug in {"shopping", "what-to-buy", "shoppingstreets", "markets", "snacks"}:
        return [f"{item}：适合逛街或买伴手礼，补查营业时间、是否可议价、保质期和携带限制。" for item in cycle(shopping + foods, 10)]
    if slug in {"nightlife", "nightview", "cafes"}:
        return [f"{item}：写清返程交通、结束时间、最低消费和雨天备用方案。" for item in cycle(fun + shopping + visits, 10)]
    return pitfalls or [
        f"季节：{best}；雨季/拥挤期准备：{rainy}；折中：{shoulder}。",
        "预约：发布前一天看官方页或地图状态。",
        "价格：只写近期核验后的人均/门票区间。",
        "排队：热门餐厅和景点尽量放工作日上午或非饭点。",
        "版权：不用博主截图、路线图、照片、封面文案。",
    ]


def quality_appendix(city: dict[str, str], data: dict[str, object]) -> str:
    attractions = split(city.get("top_attractions", "")) or split(city.get("visit", ""))
    restaurants = split(city.get("restaurants", "")) or split(city.get("food", ""))
    best, rainy, shoulder = season_window(city)
    parts = [
        "\n\n## 具体干货补强版",
        f"### 什么时候去\n- 推荐：{best}\n- 需要备用方案：{rainy}\n- 折中选择：{shoulder}",
        "### 景点 Top10\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(attractions[:10], 1)),
        "### 餐厅/美食 Top10\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(restaurants[:10], 1)),
        "### 交通怎么搭\n" + "\n".join(f"- {x}" for x in (split(city.get("transport_tips", "")) or [f"优先比较：{join(split(city.get('transport', '')))}", "高峰期不要跨区硬赶，按一个大区域一天来排。", "晚归、行李多、下雨时用打车/网约车兜底。"])) ,
        "### 避坑和解决办法\n" + "\n".join(f"- {x}" for x in (split(city.get("pitfalls", "")) or ["发布前核对营业时间、预约、票价和排队强度。", "雨季准备室内商场/博物馆备用线。", "不用博主原图、截图、路线图和原文表达。"])),
        "### 每个热门话题的可写清单",
    ]
    for topic in data.get("topics", [])[:25]:
        parts.append(f"#### {topic.get('rank')}. {topic.get('name')}\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(practical_items(city, topic)[:10], 1)))
    return "\n\n".join(parts) + "\n"


def ensure_brief(date_value: str, city: str | None) -> Path:
    out_root = ROOT / "outputs"
    matches = list(out_root.glob(f"{date_value}-*/brief.md"))
    if matches and not city:
        return matches[0]
    cmd = ["python3", str(ROOT / "scripts" / "pick_topic.py"), "--date", date_value]
    if city:
        cmd.extend(["--city", city])
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return Path(result.stdout.strip())


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d-%H%M")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--city")
    args = parser.parse_args()

    brief_path = ensure_brief(args.date, args.city)
    city_slug = gp.find_selected(brief_path.read_text(encoding="utf-8")) if hasattr(gp, "find_selected") else re.search(r"^- 城市 slug：(.+)$", brief_path.read_text(encoding="utf-8"), re.M).group(1).strip()
    cities = {item["slug"]: item for item in read_csv(ROOT / "cities.csv")}
    facts = {item["slug"]: item for item in read_optional_csv(ROOT / "city_facts.csv")}
    city = {**cities[city_slug], **facts.get(city_slug, {})}
    data_path = brief_path.parent / "hot_topics.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))

    if hasattr(gp, "topic_block") and hasattr(gp, "render_post"):
        gp.topic_block_original = gp.topic_block
        def patched_topic_block(city_arg, topic_arg, language):
            base = gp.topic_block_original(city_arg, topic_arg, language)
            marker = "- 发布前必补查：" if language == "zh-Hans" else "- 發布前必補查：" if language == "zh-Hant" else "- Fact check before posting:"
            block = "- 可直接写进正文的干货清单：\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(practical_items(city_arg, topic_arg)[:10], 1))
            return base.replace(marker, block + "\n" + marker)
        gp.topic_block = patched_topic_block
        for variant in gp.LANGUAGE_VARIANTS:
            content = gp.render_post(args.date, city, data, variant["code"])
            (brief_path.parent / variant["post_file"]).write_text(content, encoding="utf-8")
            if variant["code"] == "zh-Hans":
                (brief_path.parent / "post.md").write_text(content, encoding="utf-8")
    else:
        langs = getattr(gp, "LANGS", [("zh-Hans", "post_zh-Hans.md", "扬仔游星球"), ("zh-Hant", "post_zh-Hant.md", "揚仔遊星球"), ("en", "post_en.md", "Yangzai Travel Planet")])
        for lang, filename, _ in langs:
            base = gp.render(args.date, city, data, lang) if hasattr(gp, "render") else ""
            content = base + (quality_appendix(city, data) if lang == "zh-Hans" else "")
            (brief_path.parent / filename).write_text(content, encoding="utf-8")
            if lang == "zh-Hans":
                (brief_path.parent / "post.md").write_text(content, encoding="utf-8")
                (brief_path.parent / "research.md").write_text(content, encoding="utf-8")
    print(brief_path.parent / "post.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
