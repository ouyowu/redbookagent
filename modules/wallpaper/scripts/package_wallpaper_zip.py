#!/usr/bin/env python3
"""Package paid wallpapers and license into product/wallpaper_pack.zip."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "outputs"


def latest_output_dir() -> Path:
    candidates = sorted(OUTPUT_ROOT.glob("*-wallpaper"))
    if not candidates:
        raise SystemExit("没有找到壁纸输出目录")
    return candidates[-1]


def resolve_output_dir(value: str | None) -> Path:
    if not value:
        return latest_output_dir()
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    output = resolve_output_dir(args.output_dir)
    zip_path = output / "product" / "wallpaper_pack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((output / "wallpapers").glob("*.png")):
            archive.write(path, arcname=f"wallpapers/{path.name}")
        for name in ["usage_license.txt", "product_description.md", "risk_review.md"]:
            path = output / "product" / name
            if path.exists():
                archive.write(path, arcname=name)
    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
