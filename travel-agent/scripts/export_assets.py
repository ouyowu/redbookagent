#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def selected(brief: str) -> tuple[str, str]:
    city = re.search(r'^- 城市 slug：(.+)$', brief, re.M)
    topic = re.search(r'^- 主题 slug：(.+)$', brief, re.M)
    if not city or not topic:
        raise SystemExit('brief.md 缺少 slug')
    return city.group(1).strip(), topic.group(1).strip()


def scripts(c: dict[str, str], t: dict[str, str]) -> list[dict[str, str]]:
    rows = [
        ('封面', f'扬仔游星球 {c["name"]} {t["name"]} 攻略封面，原创城市氛围、手账贴纸和标题区。'),
        ('用户画像', '卡通人物展示第一次自由行、收藏攻略、查交通和做预算的场景。'),
        ('城市速览', f'{c["name"]} 城市氛围拼贴，地标轮廓、天气图标、交通卡、行李箱，不画真实地图。'),
        ('食住行', '三栏信息卡：美食、住宿区域、交通方式，用原创图标和短标签呈现。'),
        ('游购娱', '三栏信息卡：景点街区、购物伴手礼、晚间体验，用原创图标和卡通人物呈现。'),
        ('3 天路线', '三天行程时间轴，使用抽象箭头和片区标签，不绘制真实路线图或地图路径。'),
        ('避坑提醒', '出发前提醒卡，包含预约、营业时间、末班车、退税、天气等原创图标。'),
        ('版权自查', '内容合规检查卡，展示原创、重写、来源链接、禁止截图和禁止搬运的图标。'),
    ]
    data = []
    for i, (title, script) in enumerate(rows, 1):
        prompt = f'原创小红书旅行攻略卡通插画，第 {i} 张，主题：{title}。{script}风格：明亮、干净、手账感、扁平卡通、细节丰富；画幅 3:4；不要使用真实照片、博主截图、真实地图、真实路线图、品牌 Logo、水印或受版权保护角色。'
        data.append({'card': i, 'title': title, 'script': script, 'prompt': prompt})
    return data


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument('--date', default=today()); args = p.parse_args()
    matches = sorted((ROOT / 'outputs').glob(f'{args.date}-*/brief.md'))
    if not matches:
        raise SystemExit('请先运行 pick_topic.py 和 generate_post.py')
    out = matches[0].parent
    city_slug, topic_slug = selected(matches[0].read_text(encoding='utf-8'))
    cities = {x['slug']: x for x in read_csv('cities.csv')}; topics = {x['slug']: x for x in read_csv('topics.csv')}
    data = scripts(cities[city_slug], topics[topic_slug])
    prompts = [{'card': x['card'], 'title': x['title'], 'prompt': x['prompt'], 'filename': f"img_{x['card']}.png"} for x in data]
    (out / 'slides.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'image_prompts.json').write_text(json.dumps(prompts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'image_prompts.md').write_text('\n\n'.join(['# 每张图的卡通绘图 prompt', *[f"## 图 {x['card']}｜{x['title']}\n\n### 画面脚本\n{x['script']}\n\n### Prompt\n{x['prompt']}" for x in data], '']), encoding='utf-8')
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
