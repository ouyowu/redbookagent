#!/usr/bin/env python3
"""Generate a daily commercial wallpaper pack."""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import io
import json
import os
import textwrap
import zipfile
import struct
import zlib
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - fallback for minimal local environments
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - local fallback when dependencies are not installed
    OpenAI = None  # type: ignore[assignment]


MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "outputs"
CITY_POOL = REPO_ROOT / "travel-agent" / "cities.csv"

WALLPAPERS = [
    ("01-lockscreen.png", "Lockscreen", "cute lockscreen cover, big calm travel mood, room for clock at top"),
    ("02-homescreen.png", "Homescreen", "clean homescreen wallpaper, soft icons area, lots of breathable space"),
    ("03-calendar.png", "Calendar", "monthly calendar style wallpaper, minimal date blocks, cute travel stickers"),
    ("04-map-style.png", "Map Style", "abstract map-inspired wallpaper, dotted path, no real map or route"),
    ("05-food-style.png", "Food Style", "cute local food sticker wallpaper, snacks and drinks, playful layout"),
    ("06-night-style.png", "Night Style", "cozy city night wallpaper, stars, lamps, skyline silhouette"),
]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def pick_city(date_value: str, city_slug: str | None) -> dict[str, str]:
    cities = read_csv(CITY_POOL)
    if city_slug:
        city = next((item for item in cities if item["slug"] == city_slug), None)
        if city is None:
            raise SystemExit(f"找不到城市：{city_slug}")
        return city
    index = sum(ord(ch) for ch in date_value) % len(cities)
    return cities[index]


def display_city(slug: str) -> str:
    return slug.replace("-", " ").title().replace(" ", "")


def output_dir(date_value: str, city: dict[str, str]) -> Path:
    return OUTPUT_ROOT / f"{date_value}-{city['slug']}-wallpaper"


def product_zip_name(city: dict[str, str]) -> str:
    return f"{display_city(city['slug'])}_Cute_Travel_Wallpaper_Pack.zip"


def image_prompt(city: dict[str, str], wallpaper_name: str, concept: str) -> str:
    return (
        f"Original cute travel wallpaper for {display_city(city['slug'])}, {city['country']}. "
        f"Wallpaper type: {wallpaper_name}. Concept: {concept}. "
        "Vertical 1024x1536 mobile wallpaper, suitable for iPhone Pro Max lock screen and home screen. "
        "Cute cartoon travel journal style, cream paper texture, watercolor and colored pencil feeling, hand-drawn outline, "
        "sticker collage, tiny stars, hearts, clouds, luggage, camera, postcard stamp, soft city landmark silhouettes. "
        "Keep composition beautiful, polished, high-resolution, breathable, not crowded. "
        "Text should be minimal and perfectly spelled; if uncertain, use no text except a tiny edge stamp. "
        "Add a small subtle watermark/stamp near the edge: 扬仔游星球. "
        "No real photos, no screenshots, no real maps, no exact route maps, no platform watermarks, no brand logos, "
        "no copyrighted characters, no celebrity likeness, no copied wallpaper layout."
    )


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
    path.write_bytes(png_bytes(1024, 1536, color))


def placeholder_image(city: dict[str, str], title: str, prompt: str):
    if Image is None or ImageDraw is None:
        return None
    image = Image.new("RGB", (1024, 1536), "#f7efe0")
    draw = ImageDraw.Draw(image)
    title_font = font(70)
    body_font = font(34)
    small_font = font(26)

    colors = ["#88c7d9", "#f7b7a3", "#f4d35e", "#9bc995", "#c6a4d8", "#f28f8f"]
    for index, color in enumerate(colors):
        x = 120 + (index % 3) * 280
        y = 240 + (index // 3) * 260
        draw.rounded_rectangle((x, y, x + 180, y + 150), radius=36, fill=color, outline="#2f2a24", width=4)

    draw.text((92, 92), display_city(city["slug"]), fill="#2f2a24", font=title_font)
    draw.text((94, 182), title, fill="#5d554d", font=body_font)
    draw.line((92, 235, 932, 235), fill="#2f2a24", width=4)

    wrapped = textwrap.wrap(prompt, width=34)[:8]
    y = 650
    for line in wrapped:
        draw.text((92, y), line, fill="#4b443d", font=small_font)
        y += 42

    draw.rounded_rectangle((650, 1400, 940, 1460), radius=28, fill="#fff8e8", outline="#2f2a24", width=3)
    draw.text((680, 1415), "扬仔游星球", fill="#2f2a24", font=small_font)
    return image


def generate_with_openai(prompt: str):
    if OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return None
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    result = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1536", quality="high")
    data = result.data[0].b64_json
    if not data:
        return None
    if Image is None:
        return base64.b64decode(data)
    return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")


def save_wallpaper(city: dict[str, str], filename: str, title: str, concept: str, out_dir: Path) -> dict[str, str]:
    prompt = image_prompt(city, title, concept)
    image = generate_with_openai(prompt)
    if image is None:
        image = placeholder_image(city, title, prompt)
    path = out_dir / "wallpapers" / filename
    if isinstance(image, bytes):
        path.write_bytes(image)
    elif image is None:
        write_plain_png(path)
    else:
        image.save(path)
    return {"filename": filename, "title": title, "prompt": prompt}


def add_preview_watermark(source: Path, target: Path) -> None:
    if Image is None or ImageDraw is None:
        target.write_bytes(source.read_bytes())
        return
    image = Image.open(source).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    mark_font = font(52)
    text = "PREVIEW · 扬仔游星球"
    draw.rounded_rectangle((80, image.height - 160, image.width - 80, image.height - 70), radius=38, fill=(255, 248, 232, 218))
    draw.text((130, image.height - 140), text, fill=(47, 42, 36, 235), font=mark_font)
    Image.alpha_composite(image, overlay).convert("RGB").save(target)


def make_preview_grid(wallpaper_dir: Path, target: Path) -> None:
    if Image is None or ImageDraw is None:
        write_plain_png(target, color=(245, 232, 207))
        return
    images = [Image.open(path).convert("RGB").resize((240, 360)) for path in sorted(wallpaper_dir.glob("*.png"))]
    grid = Image.new("RGB", (820, 1180), "#f7efe0")
    draw = ImageDraw.Draw(grid)
    draw.text((44, 36), "Wallpaper Preview Grid", fill="#2f2a24", font=font(46))
    positions = [(44, 120), (290, 120), (536, 120), (44, 530), (290, 530), (536, 530)]
    for image, position in zip(images, positions):
        grid.paste(image, position)
    draw.text((44, 1088), "Watermarked preview only · 扬仔游星球", fill="#5d554d", font=font(30))
    grid.save(target)


def write_product_files(city: dict[str, str], out_dir: Path) -> None:
    city_en = display_city(city["slug"])
    title = f"{city_en} Cute Travel Wallpaper Pack"
    (out_dir / "product" / "product_title.txt").write_text(title + "\n", encoding="utf-8")
    (out_dir / "product" / "product_description.md").write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"一套以 {city['name']} 旅行灵感为主题的可爱卡通手机壁纸包。",
                "",
                "## 包含内容",
                "- 6 张竖版高清手机壁纸",
                "- 锁屏、主屏、日历、地图灵感、美食灵感、夜景灵感 6 个场景",
                "- 适合 iPhone Pro Max 类大屏，也可按其他手机型号裁切使用",
                "",
                "## 使用说明",
                "- 下载 zip 后解压，将 PNG 保存到手机相册。",
                "- 可设置为锁屏、主屏或社媒内容灵感板。",
                "- 这是数字下载商品，不寄送实物。",
                "",
                "## 授权边界",
                "- 仅限个人使用。",
                "- 不允许二次售卖、转卖、打包分发、上传素材库或作为商业设计素材再授权。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "product" / "xiaohongshu_post.md").write_text(
        "\n".join(
            [
                f"# {city['name']}旅行壁纸包｜可爱手账风",
                "",
                f"给喜欢 {city['name']} 的你整理了一套可爱旅行壁纸：锁屏、主屏、日历、地图灵感、美食和夜景都放进去了。",
                "",
                "适合：",
                "- 想换一套旅行感手机壁纸",
                "- 喜欢卡通手账、贴纸、奶油纸张质感",
                "- 想把旅行心情留在手机里",
                "",
                "包含 6 张 PNG 高清竖图。数字下载商品，不是实物。",
                "",
                "#手机壁纸 #旅行壁纸 #可爱壁纸 #手账风 #扬仔游星球",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "product" / "usage_license.txt").write_text(
        "\n".join(
            [
                "Usage License",
                "",
                "This wallpaper pack is for personal use only.",
                "You may use the files as your own phone lock screen, home screen, or personal collection.",
                "You may not resell, redistribute, upload to asset libraries, claim authorship, or use as commercial design materials.",
                "",
                "数字商品使用授权：",
                "仅限个人使用，不允许二次售卖、转卖、打包分发、上传素材库或商用再授权。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def package_zip(city: dict[str, str], out_dir: Path) -> None:
    zip_path = out_dir / "product" / product_zip_name(city)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((out_dir / "wallpapers").glob("*.png")):
            archive.write(path, arcname=f"wallpapers/{path.name}")
        archive.write(out_dir / "product" / "usage_license.txt", arcname="usage_license.txt")


def prepare_dirs(out_dir: Path) -> None:
    for child in ["preview", "product", "wallpapers"]:
        (out_dir / child).mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--city", help="City slug from travel-agent/cities.csv")
    args = parser.parse_args()

    city = pick_city(args.date, args.city)
    out_dir = output_dir(args.date, city)
    prepare_dirs(out_dir)

    prompt_records = [
        save_wallpaper(city, filename, title, concept, out_dir)
        for filename, title, concept in WALLPAPERS
    ]
    (out_dir / "image_prompts.json").write_text(json.dumps(prompt_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.md").write_text(
        "\n\n".join([f"## {item['filename']}\n{item['prompt']}" for item in prompt_records]) + "\n",
        encoding="utf-8",
    )

    add_preview_watermark(out_dir / "wallpapers" / "01-lockscreen.png", out_dir / "preview" / "01-preview-watermarked.png")
    make_preview_grid(out_dir / "wallpapers", out_dir / "preview" / "preview-grid.png")
    write_product_files(city, out_dir)
    package_zip(city, out_dir)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
