#!/usr/bin/env python3
"""Export slides.json, image_prompts.json, image_prompts.md, and NotebookLM helper copy."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMAGE_STYLE_RULES = (
    "整体风格：原创卡通可爱旅行手账，竖版手机壁纸构图，适合 iPhone Pro Max 类大屏；"
    "奶油色纸张纹理背景、彩铅和水彩质感、粗细自然的手绘黑色描边、贴纸拼贴、胶带、邮戳、"
    "可爱小图标、星星爱心云朵、少量虚线箭头和抽象旅行动线；"
    "画面活泼但不拥挤，留出手机锁屏可视空间。"
)

TEXT_RULES = (
    "文字要求：只保留重点短句，每张图中文字不超过 4 处，单处尽量 4-10 个汉字或 2-5 个英文单词；"
    "所有文字必须排版美观、清晰可读、无错字、无乱码、无多余文字；"
    "中文字体风格参考金陵体、圆体、手写圆润标题字；英文使用干净现代的人文无衬线字体，类似 claude.com 网站的温和现代字体气质；"
    "必须加入小号水印/印章文字，放在右下角或边缘，不遮挡主体。"
)

COPYRIGHT_RULES = (
    "版权限制：参考的是可爱手账、贴纸拼贴、手绘旅行日记这类通用视觉方向；"
    "不要复刻任何参考图的具体版式、构图、标题、路线、图标排列、水印、人物或独特表达；"
    "不要使用真实照片、博主截图、真实地图、真实路线图、平台水印、品牌 Logo 或受版权保护角色。"
)

LANGUAGE_VARIANTS = [
    {
        "code": "zh-Hans",
        "name": "中文简体",
        "suffix": "zh-Hans",
        "pack_file": "notebooklm_image_pack_zh-Hans.md",
        "prompt_file": "image_prompts_zh-Hans.md",
        "watermark": "扬仔游星球",
        "rules": (
            "语言版本：中文简体。图片内所有文字必须使用简体中文；"
            "水印/印章文字使用“扬仔游星球”；"
            "标题和标签使用可爱圆润中文手写风，不能出现繁体字或英文说明。"
        ),
    },
    {
        "code": "zh-Hant",
        "name": "中文繁体",
        "suffix": "zh-Hant",
        "pack_file": "notebooklm_image_pack_zh-Hant.md",
        "prompt_file": "image_prompts_zh-Hant.md",
        "watermark": "揚仔遊星球",
        "rules": (
            "語言版本：繁體中文。圖片內所有文字必須使用繁體中文；"
            "水印/印章文字使用「揚仔遊星球」；"
            "標題和標籤使用可愛圓潤中文手寫風，不能出現簡體字或英文說明。"
        ),
    },
    {
        "code": "en",
        "name": "English",
        "suffix": "en",
        "pack_file": "notebooklm_image_pack_en.md",
        "prompt_file": "image_prompts_en.md",
        "watermark": "Yangzai Travel Planet",
        "rules": (
            "Language version: English. All visible text inside the image must be natural, short English; "
            "use the small watermark/stamp text “Yangzai Travel Planet”; "
            "use a clean modern humanist sans-serif font with a warm editorial feeling similar to claude.com; "
            "do not include Chinese characters in this English version."
        ),
    },
]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def selected_from_brief(brief: str) -> tuple[str, str]:
    city = re.search(r"^- 城市 slug：(.+)$", brief, re.MULTILINE)
    topic = re.search(r"^- 主题 slug：(.+)$", brief, re.MULTILINE)
    if not city or not topic:
        raise SystemExit("brief.md 缺少城市 slug 或主题 slug")
    return city.group(1).strip(), topic.group(1).strip()


def scripts(city: dict[str, str], topic: dict[str, str]) -> list[dict[str, str]]:
    rows = [
        ("封面", f"{city['name']} {topic['name']} 封面手账，中心是可爱大标题和城市代表元素，四周点缀行李箱、相机、云朵和贴纸。"),
        ("城市速览", f"{city['name']} 旅行印象拼贴，展示 3-4 个代表景点的卡通轮廓、交通卡、天气贴纸和小邮戳，不画真实地图。"),
        ("3天路线", f"{city['name']} 3 天节奏整理页，用手账分区方式展示每天重点、交通顺路感和停留节奏，不画真实地图。"),
        ("美食灵感", f"{city['name']} 美食贴纸页，展示 3-4 个代表小吃或饮品的可爱插画和短标签，像手账便签一样排版。"),
        ("避坑清单", f"{city['name']} 出发前提醒页，整理预约、交通、排队、购物与天气变化等注意事项。"),
    ]
    return [
        {
            "card": index,
            "title": title,
            "script": script,
            "prompt": (
                f"原创小红书旅行攻略卡通插画，第 {index} 张，主题：{title}。{script}"
                f"{IMAGE_STYLE_RULES}{TEXT_RULES}{COPYRIGHT_RULES}"
                "高清、细节精致、竖版 9:16 附近构图、适合手机壁纸和小红书封面。"
            ),
        }
        for index, (title, script) in enumerate(rows, 1)
    ]


def localized_prompt(item: dict[str, str], language: dict[str, str]) -> str:
    return (
        f"{item['prompt']}"
        f"{language['rules']}"
        "最终检查：这是同一张卡的独立语言版本，画面结构可以一致，但文字只能使用本版本语言；"
        "不要把三种语言同时放进一张图；"
        "如果无法保证长句无误，请减少文字，只保留标题、1-3 个短标签和品牌水印。"
    )


def render_notebooklm_pack(city: dict[str, str], topic: dict[str, str], items: list[dict[str, str]], prompt_data: list[dict[str, str]]) -> str:
    return "\n\n".join(
        [
            f"# NotebookLM 手动出图工作包｜{city['name']}｜{topic['name']}",
            "把这整份内容贴进 NotebookLM，适合让它生成 1 张信息整合型旅行图，或者按下方分图要求逐张生成。",
            "## 你的任务",
            (
                f"请基于以下资料，为“扬仔游星球”制作 {city['name']} {topic['name']} 小红书旅行图文配图。"
                "整体风格要原创、可爱、像旅行手账，不要做成真实照片，不要复制任何现成攻略图的版式。"
            ),
            "## 总体要求",
            "- 输出风格：原创卡通旅行手账、奶油纸张纹理、水彩和彩铅质感、手绘描边、贴纸拼贴、邮戳和胶带元素。",
            "- 画幅：竖版，接近 9:16，适合小红书封面和手机大屏浏览。",
            "- 文字控制：少字、短句、排版清晰，宁可少写，也不要长句堆满画面。",
            "- 版权边界：不要使用真实照片、真实地图、路线图、品牌 Logo、平台水印、受版权保护角色，也不要模仿具体插画师风格。",
            "- 品牌标识：可加小号角落水印，中文用“扬仔游星球”，英文用“Yangzai Travel Planet”。",
            "## 城市与主题背景",
            f"- 城市：{city['name']}，{city['country']}",
            f"- 主题：{topic['name']}",
            f"- 角度：{topic['angle']}",
            f"- 官方资料入口：{city['official_url']}",
            f"- 开放旅行指南：{city['guide_url']}",
            "## 建议给 NotebookLM 的一句总指令",
            (
                f"请为“扬仔游星球”生成 {city['name']} {topic['name']} 小红书旅行配图，"
                "做成原创卡通旅行手账风，竖版，高可读、低文字密度、适合收藏，不要真实照片感。"
            ),
            "## 分图要求",
            *[
                "\n".join(
                    [
                        f"### 图 {item['card']}｜{item['title']}",
                        f"画面脚本：{item['script']}",
                        *[
                            (
                                f"- {prompt['language_name']} 文件 `{prompt['filename']}`："
                                f"{prompt['prompt']}"
                            )
                            for prompt in prompt_data
                            if prompt["card"] == item["card"]
                        ],
                    ]
                )
                for item in items
            ],
            "## 最省事用法",
            "- 想先试一张：优先用“图 1｜封面”的中文简体版本。",
            "- 想做整套：让 NotebookLM 按图 1 到图 5 分 5 次生成。",
            "- 想做英文版：直接使用对应 English 段落，不要中英混排。",
            "## 贴给 NotebookLM 的最终短指令",
            (
                f"请先生成图 1 封面，城市是 {city['name']}，主题是 {topic['name']}，"
                "使用中文简体，风格为原创可爱旅行手账，竖版，少字，高可读，不要真实照片感。"
            ),
            "",
        ]
    )


def render_notebooklm_pack_single_language(
    city: dict[str, str],
    topic: dict[str, str],
    items: list[dict[str, str]],
    prompt_data: list[dict[str, str]],
    language: dict[str, str],
) -> str:
    if language["code"] == "zh-Hant":
        title = f"# NotebookLM 手動出圖工作包｜{city['name']}｜{topic['name']}｜繁體中文"
        intro = "把這整份內容貼進 NotebookLM，適合直接生成一套繁體中文旅行配圖。"
        task_header = "## 你的任務"
        task = (
            f"請基於以下資料，為「揚仔遊星球」製作 {city['name']} {topic['name']} 小紅書旅行圖文配圖。"
            "整體風格要原創、可愛、像旅行手帳，不要做成真實照片，也不要複製任何現成攻略圖版式。"
        )
        requirement_header = "## 總體要求"
        requirements = [
            "- 輸出風格：原創卡通旅行手帳、奶油紙張紋理、水彩和彩鉛質感、手繪描邊、貼紙拼貼、郵戳和膠帶元素。",
            "- 畫幅：直式，接近 9:16，適合小紅書封面和手機大螢幕瀏覽。",
            "- 文字控制：少字、短句、排版清晰，寧可少寫，也不要長句塞滿畫面。",
            "- 版權邊界：不要使用真實照片、真實地圖、路線圖、品牌 Logo、平台水印、受版權保護角色，也不要模仿具體插畫師風格。",
            "- 品牌標識：角落可加小號水印，使用「揚仔遊星球」。",
        ]
        context_header = "## 城市與主題背景"
        directive_header = "## 建議給 NotebookLM 的一句總指令"
        directive = (
            f"請為「揚仔遊星球」生成 {city['name']} {topic['name']} 小紅書旅行配圖，"
            "做成原創卡通旅行手帳風，直式，高可讀、低文字密度、適合收藏，不要真實照片感。"
        )
        split_header = "## 分圖要求"
        easy_header = "## 最省事用法"
        easy_lines = [
            "- 想先試一張：先用圖 1 封面的繁體中文版本。",
            "- 想做整套：讓 NotebookLM 按圖 1 到圖 5 分 5 次生成。",
        ]
        final_header = "## 可直接貼上的最終短指令"
        final_line = (
            f"請先生成圖 1 封面，城市是 {city['name']}，主題是 {topic['name']}，"
            "使用繁體中文，風格為原創可愛旅行手帳，直式，少字，高可讀，不要真實照片感。"
        )
    elif language["code"] == "en":
        title = f"# NotebookLM Image Pack | {city['name']} | {topic['name']} | English"
        intro = "Paste this full note into NotebookLM to generate a complete English travel image set."
        task_header = "## Your Task"
        task = (
            f"Use the material below to create Xiaohongshu-style travel visuals for Yangzai Travel Planet about {city['name']} and {topic['name']}. "
            "Keep the look original, cute, and like a travel journal. Do not make it look like a real photo and do not copy any existing guide layout."
        )
        requirement_header = "## Overall Direction"
        requirements = [
            "- Visual style: original cartoon travel journal, cream paper texture, watercolor and colored pencil feeling, hand-drawn outlines, stickers, postage marks, and tape details.",
            "- Canvas: vertical, close to 9:16, suitable for Xiaohongshu covers and phone-first viewing.",
            "- Text: short, sparse, readable. Fewer words are better than long dense captions.",
            "- Copyright boundary: no real photos, real maps, route maps, logos, platform watermarks, protected characters, or artist-style imitation.",
            "- Brand mark: add a small corner watermark using `Yangzai Travel Planet`.",
        ]
        context_header = "## City and Theme Context"
        directive_header = "## One-Line Prompt for NotebookLM"
        directive = (
            f"Create original Xiaohongshu travel visuals for Yangzai Travel Planet about {city['name']} and {topic['name']}, "
            "in a cute cartoon travel-journal style, vertical, readable, low text density, and not photo-real."
        )
        split_header = "## Slide-by-Slide Requirements"
        easy_header = "## Fastest Way To Use This"
        easy_lines = [
            "- If you only want one test image, start with Slide 1 Cover in English.",
            "- If you want the full set, ask NotebookLM to generate Slides 1 through 5 one by one.",
        ]
        final_header = "## Final Short Prompt To Paste"
        final_line = (
            f"Generate Slide 1 Cover for {city['name']} with the theme {topic['name']}, "
            "in English, using an original cute travel-journal style, vertical layout, low text density, and no photo-real look."
        )
    else:
        title = f"# NotebookLM 手动出图工作包｜{city['name']}｜{topic['name']}｜简体中文"
        intro = "把这整份内容贴进 NotebookLM，适合直接生成一套简体中文旅行配图。"
        task_header = "## 你的任务"
        task = (
            f"请基于以下资料，为“扬仔游星球”制作 {city['name']} {topic['name']} 小红书旅行图文配图。"
            "整体风格要原创、可爱、像旅行手账，不要做成真实照片，也不要复制任何现成攻略图版式。"
        )
        requirement_header = "## 总体要求"
        requirements = [
            "- 输出风格：原创卡通旅行手账、奶油纸张纹理、水彩和彩铅质感、手绘描边、贴纸拼贴、邮戳和胶带元素。",
            "- 画幅：竖版，接近 9:16，适合小红书封面和手机大屏浏览。",
            "- 文字控制：少字、短句、排版清晰，宁可少写，也不要长句堆满画面。",
            "- 版权边界：不要使用真实照片、真实地图、路线图、品牌 Logo、平台水印、受版权保护角色，也不要模仿具体插画师风格。",
            "- 品牌标识：角落可加小号水印，使用“扬仔游星球”。",
        ]
        context_header = "## 城市与主题背景"
        directive_header = "## 建议给 NotebookLM 的一句总指令"
        directive = (
            f"请为“扬仔游星球”生成 {city['name']} {topic['name']} 小红书旅行配图，"
            "做成原创卡通旅行手账风，竖版，高可读、低文字密度、适合收藏，不要真实照片感。"
        )
        split_header = "## 分图要求"
        easy_header = "## 最省事用法"
        easy_lines = [
            "- 想先试一张：先用图 1 封面的简体中文版本。",
            "- 想做整套：让 NotebookLM 按图 1 到图 5 分 5 次生成。",
        ]
        final_header = "## 可直接贴上的最终短指令"
        final_line = (
            f"请先生成图 1 封面，城市是 {city['name']}，主题是 {topic['name']}，"
            "使用简体中文，风格为原创可爱旅行手账，竖版，少字，高可读，不要真实照片感。"
        )

    visible_prompts = [prompt for prompt in prompt_data if prompt["language"] == language["code"]]
    return "\n\n".join(
        [
            title,
            intro,
            task_header,
            task,
            requirement_header,
            *requirements,
            context_header,
            f"- 城市：{city['name']}，{city['country']}",
            f"- 主题：{topic['name']}",
            f"- 角度：{topic['angle']}",
            f"- 官方资料入口：{city['official_url']}",
            f"- 开放旅行指南：{city['guide_url']}",
            directive_header,
            directive,
            split_header,
            *[
                "\n".join(
                    [
                        f"### 图 {item['card']}｜{item['title']}" if language["code"] != "en" else f"### Slide {item['card']} | {item['title']}",
                        f"画面脚本：{item['script']}" if language["code"] != "en" else f"Visual brief: {item['script']}",
                        *[
                            f"- 文件 `{prompt['filename']}`：{prompt['prompt']}"
                            if language["code"] != "en"
                            else f"- File `{prompt['filename']}`: {prompt['prompt']}"
                            for prompt in visible_prompts
                            if prompt["card"] == item["card"]
                        ],
                    ]
                )
                for item in items
            ],
            easy_header,
            *easy_lines,
            final_header,
            final_line,
            "",
        ]
    )


def render_image_prompts_single_language(items: list[dict[str, str]], language: dict[str, str]) -> str:
    title = {
        "zh-Hans": "# 每张图的卡通绘图 prompt｜简体中文",
        "zh-Hant": "# 每張圖的卡通繪圖 Prompt｜繁體中文",
        "en": "# Cartoon image prompts for each slide | English",
    }[language["code"]]
    script_label = {
        "zh-Hans": "### 画面脚本",
        "zh-Hant": "### 畫面腳本",
        "en": "### Visual brief",
    }[language["code"]]
    return "\n\n".join(
        [
            title,
            *[
                "\n\n".join(
                    [
                        f"## 图 {item['card']}｜{item['title']}" if language["code"] != "en" else f"## Slide {item['card']} | {item['title']}",
                        f"{script_label}\n{item['script']}",
                        (
                            f"### {language['name']} Prompt\n"
                            f"文件名：`img_{item['card']}_{language['suffix']}.png`\n\n"
                            f"{localized_prompt(item, language)}"
                        )
                        if language["code"] != "en"
                        else (
                            f"### {language['name']} Prompt\n"
                            f"Filename: `img_{item['card']}_{language['suffix']}.png`\n\n"
                            f"{localized_prompt(item, language)}"
                        ),
                    ]
                )
                for item in items
            ],
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    args = parser.parse_args()

    brief_paths = list((ROOT / "outputs").glob(f"{args.date}-*/brief.md"))
    if not brief_paths:
        raise SystemExit("请先运行 pick_topic.py 和 generate_post.py")
    out_dir = brief_paths[0].parent
    city_slug, topic_slug = selected_from_brief(brief_paths[0].read_text(encoding="utf-8"))
    cities = {item["slug"]: item for item in read_csv(ROOT / "cities.csv")}
    topics = {item["slug"]: item for item in read_csv(ROOT / "topics.csv")}
    data = scripts(cities[city_slug], topics[topic_slug])
    prompt_data = []
    for item in data:
        for language in LANGUAGE_VARIANTS:
            prompt_data.append(
                {
                    "card": item["card"],
                    "title": item["title"],
                    "language": language["code"],
                    "language_name": language["name"],
                    "watermark": language["watermark"],
                    "prompt": localized_prompt(item, language),
                    "filename": f"img_{item['card']}_{language['suffix']}.png",
                }
            )

    (out_dir / "slides.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.json").write_text(json.dumps(prompt_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "image_prompts.md").write_text(
        "\n\n".join(
            [
                "# 每张图的卡通绘图 prompt",
                *[
                    "\n\n".join(
                        [
                            f"## 图 {item['card']}｜{item['title']}",
                            f"### 画面脚本\n{item['script']}",
                            *[
                                (
                                    f"### {language['name']} Prompt\n"
                                    f"文件名：`img_{item['card']}_{language['suffix']}.png`\n\n"
                                    f"{localized_prompt(item, language)}"
                                )
                                for language in LANGUAGE_VARIANTS
                            ],
                        ]
                    )
                    for item in data
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )
    for language in LANGUAGE_VARIANTS:
        (out_dir / language["prompt_file"]).write_text(
            render_image_prompts_single_language(data, language),
            encoding="utf-8",
        )
    (out_dir / "notebooklm_image_pack.md").write_text(
        render_notebooklm_pack(cities[city_slug], topics[topic_slug], data, prompt_data),
        encoding="utf-8",
    )
    for language in LANGUAGE_VARIANTS:
        (out_dir / language["pack_file"]).write_text(
            render_notebooklm_pack_single_language(
                cities[city_slug],
                topics[topic_slug],
                data,
                prompt_data,
                language,
            ),
            encoding="utf-8",
        )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
