#!/usr/bin/env python3
"""Generate product copy, Xiaohongshu seeding note, license, and risk review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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


def tags(metadata: dict[str, str]) -> list[str]:
    city = metadata["city_name"]
    return [
        "#扬仔游星球",
        "#手机壁纸",
        "#旅行壁纸",
        "#可爱壁纸",
        "#手账风",
        f"#{city}旅行",
        f"#{city}攻略",
        "#锁屏壁纸",
        "#高清壁纸",
        "#数字壁纸",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    output = resolve_output_dir(args.output_dir)
    product = output / "product"
    metadata = json.loads((output / "wallpaper_metadata.json").read_text(encoding="utf-8"))
    title = f"{metadata['city_display']} Cute Travel Wallpaper Pack｜{metadata['city_name']}旅行手机壁纸包"

    (product / "product_title.txt").write_text(title + "\n", encoding="utf-8")
    (product / "product_description.md").write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"这是一套基于“扬仔游星球”每日旅行攻略选题生成的 {metadata['city_name']} 城市旅行手机壁纸售卖包。",
                "",
                "## 你会得到",
                "- 12 张高清无水印 PNG 手机壁纸",
                "- 6 张带水印免费预览图",
                "- 1 张小红书封面图",
                "- 1 张九宫格预览图",
                "- 使用授权说明与版权风险检查",
                "",
                "## 规格",
                f"- 默认尺寸：{metadata['target_size']}，适合 iPhone / Android 竖屏裁切",
                "- 格式：PNG",
                f"- 风格：{metadata['style']}",
                "",
                "## 使用方式",
                "- 下载 `wallpaper_pack.zip` 后解压。",
                "- 将 `wallpapers/` 中的 PNG 保存到手机相册。",
                "- 可设置为锁屏、主屏或个人收藏。",
                "",
                "## 授权",
                "- 仅限个人使用。",
                "- 不允许二次售卖、转卖、打包分发、上传素材库或作为商业设计素材再授权。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (product / "xiaohongshu_post.md").write_text(
        "\n".join(
            [
                f"# {metadata['city_name']}旅行壁纸包｜可爱手账风",
                "",
                f"今天把 {metadata['city_name']} 的旅行灵感做成了一套手机壁纸包。",
                "整体是扬仔游星球统一卡通风：明亮、可爱、旅行手账、贴纸感，还有一点点城市地标氛围。",
                "",
                "里面包含：",
                "- 12 张高清无水印壁纸",
                "- 6 张带水印免费预览",
                "- 锁屏、主屏、日历、地图灵感、美食、夜景等不同场景",
                "",
                "适合想把旅行心情放进手机里的人。数字下载商品，不是实物，不会自动发布，需要人工审核后再发。",
                "",
                " ".join(tags(metadata)),
                "",
            ]
        ),
        encoding="utf-8",
    )
    (product / "tags.txt").write_text("\n".join(tags(metadata)) + "\n", encoding="utf-8")
    (product / "usage_license.txt").write_text(
        "\n".join(
            [
                "使用授权说明",
                "",
                "本壁纸包为数字下载商品，不寄送实物。",
                "购买/下载后，仅限个人使用，可设置为自己的手机锁屏、主屏或个人收藏。",
                "",
                "禁止事项：",
                "- 不允许二次售卖、转卖、打包分发。",
                "- 不允许上传到素材库、网盘公开分享或社群批量分发。",
                "- 不允许作为商业设计素材再授权。",
                "- 不允许去除或篡改预览图水印后作为免费素材传播。",
                "",
                "Personal use only. Resale, redistribution, asset-library upload, and commercial sublicensing are not allowed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (product / "risk_review.md").write_text(
        "\n".join(
            [
                "# 版权风险检查",
                "",
                "## 风险等级",
                "低。当前生成规则要求原创卡通旅行手账风，不使用真实品牌、明星、动漫 IP 或受版权保护角色。",
                "",
                "## 已检查",
                "- 不使用真实品牌 logo。",
                "- 不使用明星、动漫 IP、游戏 IP、影视角色或受版权保护角色。",
                "- 不使用现有艺术家姓名作为风格指令，不生成和现有艺术家高度相似的风格。",
                "- 不复制他人壁纸、截图、路线图、地图切片或平台水印。",
                "- 12 张高清壁纸为无水印交付图；6 张免费预览图带水印。",
                "- 小红书笔记只作为草稿文件生成，不自动发布。",
                "",
                "## 发布前人工复核",
                "- 检查图片中是否意外出现品牌 logo、平台水印、真实地图或疑似 IP 角色。",
                "- 检查城市地标是否为通用手绘表达，不构成对特定摄影作品或插画作品的复刻。",
                "- 检查图片文字是否有错字、乱码、混合语言或排版问题。",
                "- 检查 ZIP 中只包含可交付文件和授权说明。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(product)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
