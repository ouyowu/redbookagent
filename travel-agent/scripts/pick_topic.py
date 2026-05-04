#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def pick(items: list[dict[str, str]], seed: str) -> dict[str, str]:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=today())
    parser.add_argument('--city')
    parser.add_argument('--topic')
    args = parser.parse_args()

    cities = rows('cities.csv')
    topics = rows('topics.csv')
    city = next((x for x in cities if x['slug'] == args.city or x['name'] == args.city), None) or pick(cities, f'{args.date}:city')
    topic = next((x for x in topics if x['slug'] == args.topic or x['name'] == args.topic), None) or pick(topics, f'{args.date}:{city["slug"]}:topic')

    out = ROOT / 'outputs' / f'{args.date}-{city["slug"]}'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'brief.md').write_text(
        '\n'.join([
            '# 今日选题',
            f'- 日期：{args.date}',
            '- 账号：扬仔游星球',
            f'- 城市：{city["name"]}',
            f'- 国家/地区：{city["country"]}',
            f'- 主题：{topic["name"]}',
            f'- 选题角度：{topic["angle"]}',
            f'- 城市 slug：{city["slug"]}',
            f'- 主题 slug：{topic["slug"]}',
            '',
        ]),
        encoding='utf-8',
    )
    print(out / 'brief.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
