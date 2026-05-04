#!/usr/bin/env python3
"""Package wallpaper PNGs and metadata into a zip file."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def latest_output_dir() -> Path:
    candidates = sorted((ROOT / "outputs").glob("*"))
    if not candidates:
        raise SystemExit("没有找到壁纸输出目录")
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else latest_output_dir()
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    zip_path = out_dir / f"{out_dir.name}.zip"
    include_ext = {".png", ".md", ".json", ".html"}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out_dir.iterdir()):
            if path == zip_path or path.suffix.lower() not in include_ext:
                continue
            archive.write(path, arcname=path.name)
    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
