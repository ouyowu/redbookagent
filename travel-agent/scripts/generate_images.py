#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def output_dir(value: str | None) -> Path:
    if value:
        p = Path(value)
        return p if p.is_absolute() else ROOT / p
    matches = sorted((ROOT / 'outputs').glob(f'{today()}-*')) or sorted((ROOT / 'outputs').glob('*-*'))
    if not matches:
        raise SystemExit('没有找到输出目录，请先运行 export_assets.py')
    return matches[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir')
    parser.add_argument('--size', default='1024x1024')
    args = parser.parse_args()

    out = output_dir(args.output_dir)
    prompts_path = out / 'image_prompts.json'
    if not prompts_path.exists():
        raise SystemExit(f'找不到 {prompts_path}')
    if not os.getenv('OPENAI_API_KEY'):
        raise SystemExit('缺少 OPENAI_API_KEY')

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompts = json.loads(prompts_path.read_text(encoding='utf-8'))
    for i, item in enumerate(prompts, 1):
        prompt = item['prompt'] if isinstance(item, dict) else item
        filename = item.get('filename', f'img_{i}.png') if isinstance(item, dict) else f'img_{i}.png'
        result = client.images.generate(model='gpt-image-1', prompt=prompt, size=args.size)
        (out / filename).write_bytes(base64.b64decode(result.data[0].b64_json))
        print(out / filename)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
