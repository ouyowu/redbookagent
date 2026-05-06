#!/usr/bin/env python3
"""Pick a city and build the daily full travel content topic matrix."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC_COUNT = 25


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d-%H%M")


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pick(items: list[dict[str, str]], seed: str) -> dict[str, str]:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def city_pool() -> list[dict[str, str]]:
    ranked = ROOT / "hot_cities_cn.csv"
    if ranked.exists():
        cities = {item["slug"]: item for item in read_csv("cities.csv")}
        rows = []
        for item in read_csv("hot_cities_cn.csv"):
            if item["slug"] in cities:
                merged = dict(cities[item["slug"]])
                merged["rank"] = item.get("rank", "")
                rows.append(merged)
        if rows:
            return rows
    return read_csv("cities.csv")


def build_topics(city: dict[str, str], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    topics = []
    for rank, item in enumerate(candidates[:TOPIC_COUNT], 1):
        topics.append(
            {
                "rank": rank,
                "slug": item["slug"],
                "name": f"{city['name']}{item['name']}",
                "focus": item["focus"],
                "query_terms": item["query_terms"],
                "score": TOPIC_COUNT - rank + 1,
                "fallback": True,
                "results": [
                    {
                        "platform": "public-search-keywords",
                        "title": f"{city['name']} {item['query_terms']}",
                        "link": city.get("guide_url") or city.get("official_url") or "",
                        "snippet": "用于后续人工交叉验证的公开检索关键词，不复制任何平台原文。",
                    }
                ],
            }
        )
    return topics


def write_outputs(date_value: str, city: dict[str, str], topics: list[dict[str, object]]) -> Path:
    out = ROOT / "outputs" / f"{date_value}-{city['slug']}"
    out.mkdir(parents=True, exist_ok=True)
    title = f"{city['name']}热门旅游内容矩阵 Top{len(topics)}"
    brief = "\n".join(
        [
            "# 今日选题",
            f"- 日期：{date_value}",
            "- 账号：扬仔游星球",
            f"- 城市：{city['name']}",
            f"- 国家/地区：{city.get('country', '')}",
            f"- 城市热度排名：{city.get('rank', '')}",
            f"- 内容主题：{title}",
            "- 选题逻辑：固定覆盖美食、住宿、交通、景点、购物、值得买、夜生活、本地人推荐和避坑。",
            "- 参考平台：小红书；抖音；Bilibili；马蜂窝；携程；飞猪；Tripadvisor；地图点评平台；官方公开资料",
            f"- 热门话题数量：{len(topics)}",
            f"- 城市 slug：{city['slug']}",
            "- 内容类型 slug：city-content-matrix",
            "",
            f"## 热门话题 Top{len(topics)}",
            *[f"- {item['rank']}. {item['name']}" for item in topics],
            "",
        ]
    )
    (out / "brief.md").write_text(brief, encoding="utf-8")
    (out / "hot_topics.json").write_text(
        json.dumps(
            {
                "date": date_value,
                "city": {"slug": city["slug"], "name": city["name"], "country": city.get("country", ""), "rank": city.get("rank", "")},
                "content_theme": title,
                "platforms": ["xiaohongshu", "douyin", "bilibili", "mafengwo", "ctrip", "official", "maps"],
                "topics": topics,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return out / "brief.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--city")
    args = parser.parse_args()

    cities = city_pool()
    candidates = read_csv("hot_topic_candidates.csv") if (ROOT / "hot_topic_candidates.csv").exists() else read_csv("topics.csv")
    city = next((x for x in cities if x["slug"] == args.city or x["name"] == args.city), None) if args.city else None
    city = city or pick(cities, f"{args.date}:city")
    print(write_outputs(args.date, city, build_topics(city, candidates)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
