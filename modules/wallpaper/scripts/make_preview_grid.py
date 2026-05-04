#!/usr/bin/env python3
"""Create a simple HTML preview grid for generated wallpaper files."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def latest_output_dir() -> Path:
    candidates = sorted((ROOT / "outputs").glob("*"))
    if not candidates:
        raise SystemExit("没有找到壁纸输出目录，请先运行 generate_wallpaper_pack.py")
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else latest_output_dir()
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    images = sorted(out_dir.glob("*.png"))
    cards = "\n".join(
        f'<figure><img src="{image.name}" alt="{image.name}"><figcaption>{image.name}</figcaption></figure>'
        for image in images
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wallpaper Preview</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f3ea; color: #26221d; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px; }}
    h1 {{ font-size: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 18px; }}
    figure {{ margin: 0; }}
    img {{ width: 100%; aspect-ratio: 2 / 3; object-fit: cover; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.12); background: #fff; }}
    figcaption {{ margin-top: 8px; font-size: 12px; word-break: break-all; }}
  </style>
</head>
<body>
  <main>
    <h1>Wallpaper Preview</h1>
    <div class="grid">{cards}</div>
  </main>
</body>
</html>
"""
    (out_dir / "preview.html").write_text(html, encoding="utf-8")
    print(out_dir / "preview.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
