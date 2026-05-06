#!/usr/bin/env python3
"""Quality wrapper for concrete, practical travel copy."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
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


def cycle_to_count(items: list[str], count: int) -> list[str]:
    if not items:
        return []
    return [items[index % len(items)] for index in range(count)]


def season_window(city: dict[str, str], language: str) -> tuple[str, str, str]:
    parts = split(city.get("season", ""))
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], parts[1]
    if len(parts) == 1:
        return parts[0], parts[0], parts[0]
    tropical = any(key in city["country"] for key in ["印度尼西亚", "泰国", "马来西亚", "新加坡", "菲律宾", "越南", "柬埔寨", "老挝"])
    if language == "en":
        return ("May-Sep is easier outdoors", "Nov-Mar needs rain backup", "Apr/Oct depends on weather") if tropical else ("spring/autumn is easier", "major holidays are crowded", "weekday mornings are safer")
    if language == "zh-Hant":
        return ("5-9月戶外更穩", "11-3月雨水更多", "4月/10月看天氣") if tropical else ("春秋更適合首次去", "大假期更擁擠", "工作日上午更省心")
    return ("5-9月户外更稳", "11-3月雨水更多", "4月/10月看天气") if tropical else ("春秋更适合首次去", "大假期更拥挤", "工作日上午更省心")


def numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def practical_items(city: dict[str, str], topic: dict[str, object], language: str) -> list[str]:
    slug = str(topic["slug"])
    foods = split(city["food"])
    stays = split(city["stay"])
    transport = split(city["transport"])
    visits = split(city["visit"])
    shopping = split(city["shopping"])
    fun = split(city["entertainment"])
    attractions = split(city.get("top_attractions", "")) or visits
    restaurants = split(city.get("restaurants", ""))
    transport_tips = split(city.get("transport_tips", ""))
    pitfalls = split(city.get("pitfalls", ""))
    best, avoid, shoulder = season_window(city, language)

    if slug in {"restaurants", "food-overview", "fly-restaurants", "hotpot", "breakfast", "desserts"}:
        base = restaurants or cycle_to_count(foods + shopping + stays, 10)
        return [f"{item}：写清推荐菜、所在片区、排队强度、是否需订位和近期人均，发布前用地图再核验。" for item in base]
    if slug == "transport":
        return transport_tips or [
            f"抵达：先比较 {gp.join(transport[:2], language)}，行李多或晚归再用 Grab/打车兜底。",
            f"住宿基地：想吃喝逛街优先看 {gp.join(stays[:2], language)}；想顺景点再看 {gp.join(stays[2:4], language)}。",
            "避坑：不要把跨城区移动塞在早晚高峰。",
            "解法：每天只锁一个大区域，一个必去点，旁边顺路安排吃饭和购物。",
        ]
    if slug in {"attractions", "citywalk", "photospots", "museums", "daytrip"}:
        return [f"{item}：搭配附近吃喝/商圈一起排，发布前核对开放时间、预约门票和交通耗时。" for item in attractions]
    if slug == "hotels":
        return [f"{item}：先查到核心景点的通勤时间、夜间返程、噪音和预算，再决定要不要住。" for item in stays]
    if slug in {"shopping", "what-to-buy", "shoppingstreets", "markets", "snacks"}:
        base = cycle_to_count(shopping + foods, 10)
        return [f"{item}：适合逛街或买伴手礼，补查营业时间、是否可议价、保质期和携带限制。" for item in base]
    if slug in {"nightlife", "nightview", "cafes"}:
        base = cycle_to_count(fun + shopping + visits, 10)
        return [f"{item}：写清返程交通、结束时间、最低消费和雨天备用方案。" for item in base]
    return pitfalls or [
        f"季节：{best}；要避开/准备：{avoid}；折中：{shoulder}。",
        "预约：发布前一天看官方页或地图状态。",
        "价格：只写近期核验后的人均/门票区间。",
        "排队：热门餐厅和景点尽量放工作日上午或非饭点。",
        "版权：不用博主截图、路线图、照片、封面文案。",
    ]


def practical_block(city: dict[str, str], topic: dict[str, object], language: str) -> str:
    title = "Practical list:" if language == "en" else "可直接写进正文的干货清单："
    return f"- {title}\n{numbered(practical_items(city, topic, language)[:10])}"


def topic_block(city: dict[str, str], topic: dict[str, object], language: str) -> str:
    base = gp.topic_block_original(city, topic, language)
    marker = "- 发布前必补查：" if language == "zh-Hans" else "- 發布前必補查：" if language == "zh-Hant" else "- Fact check before posting:"
    return base.replace(marker, practical_block(city, topic, language) + "\n" + marker)


def image_scripts(city: dict[str, str], language: str) -> list[tuple[str, str]]:
    foods = split(city["food"])
    stays = split(city["stay"])
    transport = split(city["transport"])
    visits = split(city["visit"])
    shopping = split(city["shopping"])
    fun = split(city["entertainment"])
    attractions = split(city.get("top_attractions", "")) or visits
    restaurants = split(city.get("restaurants", "")) or foods
    best, rainy, shoulder = season_window(city, language)
    return [
        ("封面", f"{city['name']} 实用攻略封面，标出{best}、{rainy}。"),
        ("什么时候去", f"{city['name']} 淡旺季：{best}、{rainy}、{shoulder}，加雨天备用方案。"),
        ("景点Top清单", f"{city['name']} 推荐景点Top10：{gp.join(attractions[:10], language)}。"),
        ("本地吃喝清单", f"{city['name']} 餐厅/美食Top10：{gp.join(restaurants[:10], language)}。"),
        ("住哪里最方便", f"{city['name']} 住宿区域：{gp.join(stays, language)}，按交通、噪音、预算比较。"),
        ("交通怎么搭", f"{city['name']} 交通：{gp.join(transport, language)}，写机场进城、高峰缓冲、晚归兜底。"),
        ("购物值得买", f"{city['name']} 购物：{gp.join(shopping + foods[:2], language)}，写保质期、议价、携带限制。"),
        ("夜生活玩法", f"{city['name']} 夜生活：{gp.join(fun, language)}，写结束时间、返程交通、最低消费。"),
        ("避坑解法", f"{city['name']} 避坑：预约、营业时间、价格、排队、天气，每项都写解决办法。"),
        ("发布前核验", f"{city['name']} 核验：官网、地图近期评价、交通票价、餐厅营业状态、图片版权。"),
    ]


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

    gp.topic_block_original = gp.topic_block
    gp.topic_block = topic_block
    gp.image_scripts = image_scripts

    brief_path = ensure_brief(args.date, args.city)
    city_slug = gp.find_selected(brief_path.read_text(encoding="utf-8"))
    cities = {item["slug"]: item for item in read_csv(ROOT / "cities.csv")}
    facts = {item["slug"]: item for item in read_optional_csv(ROOT / "city_facts.csv")}
    city = {**cities[city_slug], **facts.get(city_slug, {})}
    data = gp.load_hot_topics(brief_path.parent)

    (brief_path.parent / "research.md").write_text(gp.render_research(args.date, city, data), encoding="utf-8")
    topic_dir = brief_path.parent / "topics"
    topic_dir.mkdir(exist_ok=True)
    for variant in gp.LANGUAGE_VARIANTS:
        content = gp.render_post(args.date, city, data, variant["code"])
        (brief_path.parent / variant["post_file"]).write_text(content, encoding="utf-8")
        if variant["code"] == "zh-Hans":
            (brief_path.parent / "post.md").write_text(content, encoding="utf-8")
        for topic in data["topics"]:
            filename = f"{int(topic['rank']):02d}-{gp.slugify_topic_name(str(topic['slug']))}-{variant['code']}.md"
            (topic_dir / filename).write_text(gp.render_single_topic_post(args.date, city, topic, variant["code"]), encoding="utf-8")
    print(brief_path.parent / "post.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
