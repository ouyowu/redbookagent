#!/usr/bin/env python3
"""Generate a product page draft for a wallpaper pack."""

from __future__ import annotations

import argparse
import json
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
    prompts_path = out_dir / "image_prompts.json"
    prompts = json.loads(prompts_path.read_text(encoding="utf-8")) if prompts_path.exists() else []
    languages = sorted({item.get("language_name", item.get("language", "")) for item in prompts})
    base_count = len({item.get("card") for item in prompts})
    page = "\n".join(
        [
            "# 商品页草稿",
            "",
            "## 标题",
            f"扬仔游星球｜手机壁纸数字下载包｜{base_count} 款多语言版本",
            "",
            "## 卖点",
            "- 竖版高清手机壁纸，适合 iPhone Pro Max 类大屏。",
            "- 统一可爱治愈视觉风格，适合作为锁屏、主屏或社媒素材灵感。",
            f"- 包含语言版本：{'、'.join(languages) if languages else '以实际文件为准'}。",
            "- 数字文件下载，购买后可保存到手机使用。",
            "",
            "## 包含内容",
            f"- 壁纸基础款：{base_count} 张",
            f"- 多语言图片文件：{len(prompts)} 张",
            "- 预览页、prompt 记录和版权说明。",
            "",
            "## 使用授权",
            "- 仅限个人使用，可用于自己的手机壁纸和个人收藏。",
            "- 不允许二次售卖、转卖、打包分发、上传素材库或作为商业设计素材再授权。",
            "",
            "## 注意事项",
            "- 这是数字下载商品，不寄送实物。",
            "- 不同手机型号显示区域会略有差异，可按需要自行裁切。",
            "- 图片中文字和排版发布前请人工复核。",
            "",
            "## 标签",
            "#手机壁纸 #数字壁纸 #治愈壁纸 #可爱壁纸 #扬仔游星球 #锁屏壁纸",
            "",
        ]
    )
    (out_dir / "product_page.md").write_text(page, encoding="utf-8")
    print(out_dir / "product_page.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
