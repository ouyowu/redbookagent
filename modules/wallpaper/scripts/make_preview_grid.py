#!/usr/bin/env python3
"""Create 6 watermarked previews, a Xiaohongshu cover, and a 9-grid preview."""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "outputs"


def latest_output_dir() -> Path:
    candidates = sorted(OUTPUT_ROOT.glob("*-wallpaper"))
    if not candidates:
        raise SystemExit("没有找到壁纸输出目录，请先运行 generate_wallpaper_pack.py")
    return candidates[-1]


def resolve_output_dir(value: str | None) -> Path:
    if not value:
        return latest_output_dir()
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


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


def write_plain_png(path: Path, width: int = 1440, height: int = 3200, color: tuple[int, int, int] = (245, 232, 207)) -> None:
    path.write_bytes(png_bytes(width, height, color))


def add_watermark(source: Path, target: Path, text: str) -> None:
    if Image is None or ImageDraw is None:
        target.write_bytes(source.read_bytes())
        return
    image = Image.open(source).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    mark_font = font(64)
    band_h = 150
    draw.rounded_rectangle((90, image.height - band_h - 90, image.width - 90, image.height - 90), radius=54, fill=(255, 248, 232, 225))
    draw.text((140, image.height - band_h - 48), text, fill=(47, 42, 36, 238), font=mark_font)
    Image.alpha_composite(image, overlay).convert("RGB").save(target)


def make_cover(output: Path, metadata: dict[str, str]) -> None:
    cover_path = output / "preview" / "xiaohongshu-cover.png"
    if Image is None or ImageDraw is None:
        write_plain_png(cover_path, 1440, 1920)
        return
    base = Image.open(output / "wallpapers" / "01-lockscreen.png").convert("RGB").resize((1440, 3200))
    cover = base.crop((0, 360, 1440, 2280)).convert("RGBA")
    overlay = Image.new("RGBA", cover.size, (255, 248, 232, 70))
    cover = Image.alpha_composite(cover, overlay)
    draw = ImageDraw.Draw(cover)
    draw.rounded_rectangle((90, 90, 1350, 420), radius=70, fill=(255, 248, 232, 235))
    draw.text((150, 140), f"{metadata['city_name']}旅行壁纸包", fill="#2f2a24", font=font(88))
    draw.text((154, 260), "12张高清无水印 + 6张免费预览", fill="#5d554d", font=font(46))
    draw.rounded_rectangle((930, 1680, 1320, 1780), radius=48, fill=(255, 248, 232, 230))
    draw.text((980, 1705), "扬仔游星球", fill="#2f2a24", font=font(42))
    cover.convert("RGB").save(cover_path)


def make_grid(output: Path) -> None:
    grid_path = output / "preview" / "preview-grid.png"
    if Image is None or ImageDraw is None:
        write_plain_png(grid_path, 1440, 1440)
        return
    files = sorted((output / "wallpapers").glob("*.png"))[:9]
    thumbs = [Image.open(path).convert("RGB").resize((420, 620)) for path in files]
    grid = Image.new("RGB", (1440, 2160), "#f7efe0")
    draw = ImageDraw.Draw(grid)
    draw.text((74, 54), "Wallpaper Preview", fill="#2f2a24", font=font(72))
    positions = [(75 + col * 450, 170 + row * 650) for row in range(3) for col in range(3)]
    for image, position in zip(thumbs, positions):
        grid.paste(image, position)
    draw.text((74, 2070), "Watermarked preview only · 扬仔游星球", fill="#5d554d", font=font(42))
    grid.save(grid_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    output = resolve_output_dir(args.output_dir)
    metadata = json.loads((output / "wallpaper_metadata.json").read_text(encoding="utf-8"))

    previews = sorted((output / "wallpapers").glob("*.png"))[:6]
    for index, source in enumerate(previews, start=1):
        add_watermark(source, output / "preview" / f"{index:02d}-preview-watermarked.png", "PREVIEW · 扬仔游星球")
    make_cover(output, metadata)
    make_grid(output)
    print(output / "preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
