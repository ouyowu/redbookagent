#!/usr/bin/env python3
"""Generate 12 original phone wallpapers from the daily travel-agent topic."""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import io
import json
import os
import shutil
import re
import struct
import textwrap
import zlib
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "outputs"
TRAVEL_ROOT = REPO_ROOT / "travel-agent"
TARGET_SIZE = (1440, 3200)
API_SIZE = "1024x1536"

WALLPAPER_SPECS = [
    ("01-lockscreen.png", "Lockscreen", "airy lock screen, calm city mood, clear space for time at top"),
    ("02-homescreen.png", "Homescreen", "clean home screen, soft background, app icons will remain readable"),
    ("03-calendar.png", "Calendar", "cute monthly planning mood, tiny blank calendar stickers, no real date dependency"),
    ("04-map-style.png", "Map Style", "abstract travel map feeling, dotted paths and stickers, not a real map"),
    ("05-food-style.png", "Food Style", "local food sticker collage, playful snacks and drinks inspired by the city"),
    ("06-night-style.png", "Night Style", "cozy city night, soft lamps, stars, skyline silhouette, warm healing mood"),
    ("07-landmark-style.png", "Landmark Style", "cute landmark silhouettes, postcard stamps, no realistic copyrighted architecture detail"),
    ("08-sticker-style.png", "Sticker Style", "dense but tidy travel sticker sheet, camera, luggage, tickets, clouds"),
    ("09-minimal-style.png", "Minimal Style", "minimal healing wallpaper, lots of cream paper space, tiny city icons"),
    ("10-journal-style.png", "Journal Style", "travel journal page, washi tape, paper notes, hand-drawn decorations"),
    ("11-sunrise-style.png", "Sunrise Style", "soft sunrise city mood, gentle pastel sky, hopeful travel feeling"),
    ("12-souvenir-style.png", "Souvenir Style", "souvenir collage, stamps, postcards, small gifts, cute city memories"),
]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def parse_brief(path: Path) -> tuple[str | None, str | None]:
    text = path.read_text(encoding="utf-8")
    city = re.search(r"^- 城市 slug：(.+)$", text, re.MULTILINE)
    topic = re.search(r"^- 主题 slug：(.+)$", text, re.MULTILINE)
    return (city.group(1).strip() if city else None, topic.group(1).strip() if topic else None)


def pick_from_daily_travel(date_value: str) -> tuple[str | None, str | None]:
    briefs = sorted((TRAVEL_ROOT / "outputs").glob(f"{date_value}-*/brief.md"))
    if not briefs:
        return None, None
    return parse_brief(briefs[0])


def pick_city(date_value: str, city_slug: str | None) -> dict[str, str]:
    cities = read_csv(TRAVEL_ROOT / "cities.csv")
    chosen_slug = city_slug or pick_from_daily_travel(date_value)[0]
    if chosen_slug:
        city = next((item for item in cities if item["slug"] == chosen_slug), None)
        if city:
            return city
        raise SystemExit(f"找不到城市：{chosen_slug}")
    return cities[sum(ord(ch) for ch in date_value) % len(cities)]


def pick_topic(date_value: str, topic_slug: str | None) -> dict[str, str]:
    topics = read_csv(TRAVEL_ROOT / "topics.csv")
    chosen_slug = topic_slug or pick_from_daily_travel(date_value)[1]
    if chosen_slug:
        topic = next((item for item in topics if item["slug"] == chosen_slug), None)
        if topic:
            return topic
        raise SystemExit(f"找不到主题：{chosen_slug}")
    return topics[(sum(ord(ch) for ch in date_value) + 11) % len(topics)]


def display_city(slug: str) -> str:
    return slug.replace("-", " ").title().replace(" ", "")


def out_dir(date_value: str, city: dict[str, str]) -> Path:
    return OUTPUT_ROOT / f"{date_value}-{city['slug']}-wallpaper"


def font(size: int):
    if ImageFont is None:
        return None
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def png_bytes(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    raw = b"".join(bytes([0, *rgb]) * width for _ in range(height))

    def chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def write_plain_png(path: Path, color: tuple[int, int, int] = (247, 239, 224)) -> None:
    path.write_bytes(png_bytes(TARGET_SIZE[0], TARGET_SIZE[1], color))


def prompt_for(city: dict[str, str], topic: dict[str, str], filename: str, title: str, concept: str) -> str:
    return (
        f"Original phone wallpaper for {display_city(city['slug'])}, {city['country']}, theme {topic['name']}. "
        f"Output file concept: {filename}, {title}: {concept}. "
        "Unified Yangzai Travel Planet cartoon style: travel journal, cute, bright, healing, hand-drawn city landmarks, "
        "sticker collage, cream paper texture, watercolor and colored pencil feeling, soft shadows, tidy composition. "
        "Final wallpaper must work for iPhone and Android vertical screens at 1440x3200 or 1290x2796 crop, PNG, high resolution. "
        "Keep top and bottom safe areas breathable. Text should be minimal; if text appears, it must be perfectly spelled and beautiful. "
        "Do not add watermark on paid wallpaper files. "
        "Strict copyright safety: no real brand logos, no celebrities, no anime/comic/game IP, no protected characters, "
        "no artist-name style imitation, no existing wallpaper copy, no real map tiles, no real route map, every image must be original."
    )


def fit_to_target(image):
    if Image is None:
        return image
    src_w, src_h = image.size
    target_w, target_h = TARGET_SIZE
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)))
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def placeholder(city: dict[str, str], title: str):
    if Image is None or ImageDraw is None:
        return None
    image = Image.new("RGB", TARGET_SIZE, "#f7efe0")
    draw = ImageDraw.Draw(image)
    title_font = font(96)
    body_font = font(52)
    small_font = font(38)
    colors = ["#88c7d9", "#f7b7a3", "#f4d35e", "#9bc995", "#c6a4d8", "#f28f8f"]
    for index, color in enumerate(colors):
        x = 150 + (index % 2) * 560
        y = 560 + (index // 2) * 420
        draw.rounded_rectangle((x, y, x + 420, y + 300), radius=64, fill=color, outline="#2f2a24", width=8)
    draw.text((120, 170), display_city(city["slug"]), fill="#2f2a24", font=title_font)
    draw.text((124, 300), title, fill="#5d554d", font=body_font)
    draw.line((120, 390, 1320, 390), fill="#2f2a24", width=6)
    for idx, line in enumerate(textwrap.wrap("Cute travel journal wallpaper · original placeholder", width=32)[:3]):
        draw.text((120, 2360 + idx * 58), line, fill="#5d554d", font=small_font)
    return image


def generate_image(prompt: str):
    if OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return None
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    result = client.images.generate(model="gpt-image-1", prompt=prompt, size=API_SIZE, quality="low")
    data = result.data[0].b64_json
    if not data:
        return None
    if Image is None:
        return base64.b64decode(data)
    image = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
    return fit_to_target(image)


def save_wallpaper(city: dict[str, str], topic: dict[str, str], output: Path, spec: tuple[str, str, str]) -> dict[str, str]:
    filename, title, concept = spec
    prompt = prompt_for(city, topic, filename, title, concept)
    image = generate_image(prompt)
    target = output / "wallpapers" / filename
    if isinstance(image, bytes):
        target.write_bytes(image)
    else:
        if image is None:
            image = placeholder(city, title)
        if image is None:
            write_plain_png(target)
        else:
            image.save(target)
    return {"filename": filename, "title": title, "concept": concept, "prompt": prompt, "watermark": False}


def prepare(output: Path) -> None:
    for name in ["wallpapers", "preview", "product"]:
        target = output / name
        if target.exists():
            shutil.rmtree(target)
    for name in ["wallpapers", "preview", "product"]:
        (output / name).mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--city")
    parser.add_argument("--topic")
    args = parser.parse_args()

    city = pick_city(args.date, args.city)
    topic = pick_topic(args.date, args.topic)
    output = out_dir(args.date, city)
    prepare(output)

    records = [save_wallpaper(city, topic, output, spec) for spec in WALLPAPER_SPECS]
    metadata = {
        "date": args.date,
        "city_slug": city["slug"],
        "city_name": city["name"],
        "city_display": display_city(city["slug"]),
        "topic_slug": topic["slug"],
        "topic_name": topic["name"],
        "target_size": f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]}",
        "free_preview_count": 6,
        "paid_wallpaper_count": 12,
        "style": "扬仔游星球统一卡通风、旅行手账、可爱、明亮、治愈、城市地标、贴纸感",
    }
    (output / "wallpaper_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "image_prompts.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "image_prompts.md").write_text("\n\n".join([f"## {item['filename']}\n{item['prompt']}" for item in records]) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
