#!/usr/bin/env python3
"""Generate cartoon images from exported OpenAI image prompts."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path

from openai import BadRequestError, OpenAI


ROOT = Path(__file__).resolve().parents[1]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def latest_output_dir() -> Path:
    candidates = sorted((ROOT / "outputs").glob("*-*"))
    if not candidates:
        raise SystemExit("没有找到输出目录，请先运行 pick_topic.py、generate_post.py 和 export_assets.py")
    return candidates[-1]


def resolve_output_dir(value: str | None) -> Path:
    if value:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        return path

    today_matches = sorted((ROOT / "outputs").glob(f"{today()}-*"))
    if today_matches:
        return today_matches[0]
    return latest_output_dir()


def load_prompts(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    prompts: list[dict[str, str]] = []
    for index, item in enumerate(data, start=1):
        if isinstance(item, str):
            prompts.append({"prompt": item, "filename": f"img_{index}.png"})
        else:
            prompts.append(
                {
                    "prompt": item["prompt"],
                    "filename": item.get("filename") or f"img_{item.get('card', index)}.png",
                }
            )
    return prompts


def generate_image(client: OpenAI, prompt: str, filename: Path, size: str, quality: str) -> None:
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        quality=quality,
    )
    image_base64 = result.data[0].b64_json
    filename.write_bytes(base64.b64decode(image_base64))


def is_billing_limit_error(error: BadRequestError) -> bool:
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return False
    error_body = body.get("error")
    if not isinstance(error_body, dict):
        return False
    return error_body.get("code") == "billing_hard_limit_reached"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PNG images from image_prompts.json.")
    parser.add_argument("--output-dir", help="Output directory containing image_prompts.json. Defaults to today's output.")
    parser.add_argument("--size", default="1024x1536", help="Vertical image size for gpt-image-1.")
    parser.add_argument("--quality", default="low", choices=["low", "medium", "high", "auto"], help="Image quality for gpt-image-1.")
    args = parser.parse_args()

    output_dir = resolve_output_dir(args.output_dir)
    prompts_path = output_dir / "image_prompts.json"
    if not prompts_path.exists():
        raise SystemExit(f"找不到 {prompts_path}，请先运行 scripts/export_assets.py")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("缺少 OPENAI_API_KEY，无法调用图片生成接口")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompts = load_prompts(prompts_path)
    try:
        for item in prompts:
            filename = output_dir / item["filename"]
            generate_image(client, item["prompt"], filename, args.size, args.quality)
            print(filename)
    except BadRequestError as error:
        if not is_billing_limit_error(error):
            raise
        status_path = output_dir / "image_generation_status.md"
        status_path.write_text(
            "\n".join(
                [
                    "# Image generation skipped",
                    "",
                    "OpenAI billing hard limit has been reached.",
                    "Text assets and image prompts were generated successfully.",
                    "Top up billing or raise the spending limit, then rerun image generation.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"跳过图片生成：OpenAI 账户已达到 billing hard limit。状态已写入 {status_path}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
