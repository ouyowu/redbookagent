#!/usr/bin/env python3
"""Generate original Xiaohongshu travel copy from local city/topic pools."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def split(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def find_selected(brief: str) -> tuple[str, str]:
    city = re.search(r"^- 城市 slug：(.+)$", brief, re.MULTILINE)
    topic = re.search(r"^- 主题 slug：(.+)$", brief, re.MULTILINE)
    if not city or not topic:
        raise SystemExit("brief.md 缺少城市 slug 或主题 slug")
    return city.group(1).strip(), topic.group(1).strip()


def ensure_brief(date_value: str, city: str | None, topic: str | None) -> Path:
    out_root = ROOT / "outputs"
    matches = list(out_root.glob(f"{date_value}-*/brief.md"))
    if matches and not city and not topic:
        return matches[0]
    cmd = ["python3", str(ROOT / "scripts" / "pick_topic.py"), "--date", date_value]
    if city:
        cmd.extend(["--city", city])
    if topic:
        cmd.extend(["--topic", topic])
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return Path(result.stdout.strip())


def guide(city: dict[str, str], topic: dict[str, str]) -> dict[str, str]:
    return {
        "食": f"围绕{join(split(city['food']))}做选择。建议把用餐安排在住宿或景点附近，价格写区间，具体店铺营业状态发布前再核对。",
        "住": f"第一次去优先考虑{join(split(city['stay']))}。主题是「{topic['name']}」时，住宿最好靠近当天主片区，减少跨城通勤。",
        "行": f"常用交通包括{join(split(city['transport']))}。先确认机场/车站到酒店的第一段，再按同方向片区安排每日行程。",
        "游": f"核心游玩可从{join(split(city['visit']))}中选择 2-3 个，再补一个街区散步或室内备用点。",
        "购": f"购物和伴手礼可关注{join(split(city['shopping']))}。购买前确认退税、保质期、尺寸和航空携带限制。",
        "娱": f"晚间体验可从{join(split(city['entertainment']))}里挑选。夜间活动务必复核营业时间、预约规则和返程交通。",
    }


def join(items: list[str]) -> str:
    return "、".join(items)


def route(city: dict[str, str], topic: dict[str, str]) -> list[tuple[str, str, str]]:
    visits = split(city["visit"])
    foods = split(city["food"])
    shops = split(city["shopping"])
    fun = split(city["entertainment"])
    return [
        ("Day 1", "抵达与城市初印象", f"抵达酒店片区 -> {visits[0]} -> 周边散步 -> {foods[0]} -> {fun[0]}"),
        ("Day 2", f"{topic['name']}主线日", f"{visits[1]} -> {foods[1]} -> {visits[2]} -> {shops[0]} -> {fun[1]}"),
        ("Day 3", "轻购物与弹性收尾", f"慢早餐 -> {shops[1]}或{shops[2]} -> {visits[3]} -> 伴手礼补货 -> {fun[2]}"),
    ]


def titles(city: dict[str, str], topic: dict[str, str]) -> list[str]:
    return [
        f"{city['name']}{topic['name']}攻略｜扬仔帮你整理好了",
        f"{city['name']}3 天怎么玩？食住行游购娱一篇讲清",
        f"第一次去{city['name']}，照这个思路做攻略",
        f"{city['name']}不赶路玩法：适合收藏的 3 天游",
        f"扬仔游星球｜{city['name']}{topic['name']}避坑版",
    ]


def tags(city: dict[str, str], topic: dict[str, str]) -> list[str]:
    raw = ["扬仔游星球", city["name"], f"{city['name']}旅行", f"{city['name']}攻略", topic["name"], "旅行攻略", "自由行", "小红书旅行", "当地人推荐", "食住行游购娱"]
    return [f"#{item.replace(' ', '')}" for item in raw]


def source_strategy() -> list[str]:
    return [
        "官方旅游、景点、交通、票务页面：核对开放时间、预约、价格区间和交通规则。",
        "1 个开放旅行指南：补充片区理解、常见路线框架和体验提醒。",
        "只记录官方页和开放指南链接及编辑归纳结论，不复制原文、路线图、截图、视频脚本或图片。",
    ]


def local_keywords(city: dict[str, str], topic: dict[str, str]) -> list[str]:
    return [
        f"{city['name']} official tourism {topic['name']}",
        f"{city['name']} open travel guide first time itinerary",
    ]


def image_scripts(city: dict[str, str], topic: dict[str, str]) -> list[tuple[str, str]]:
    return [
        ("封面", f"扬仔游星球 {city['name']} {topic['name']} 攻略封面，原创城市氛围、手账贴纸和标题区。"),
        ("城市速览", f"{city['name']} 城市氛围拼贴，地标轮廓、天气图标、交通卡、行李箱，不画真实地图。"),
        ("美食灵感", "本地代表美食贴纸页，用原创食物小图标和短标签呈现，不画真实店铺或品牌。"),
    ]


def prompt_for(index: int, title: str, script: str) -> str:
    return (
        f"原创小红书旅行攻略卡通插画，第 {index} 张，主题：{title}。{script}"
        "画面风格：可爱卡通旅行手账、奶油色纸张纹理、水彩和彩铅质感、手绘黑色细描边、贴纸拼贴、胶带、印章、星星爱心、旅行小图标；"
        "构图：竖版手机壁纸比例，适合 iPhone 17 Pro Max 视觉裁切，高清细节，留出安全边距；"
        "文字：只保留核心短句，使用金陵体、圆体或相近的圆润手写中文字体；"
        "品牌：角落加入小而清晰的原创水印/印章文字“扬仔游星球”；"
        "版权限制：不要使用真实照片、博主截图、真实地图、真实路线图、平台水印、品牌 Logo、受版权保护角色，也不要复刻参考图的具体版式和独特表达。"
    )


def render_post(date_value: str, city: dict[str, str], topic: dict[str, str]) -> str:
    g = guide(city, topic)
    r = route(city, topic)
    images = image_scripts(city, topic)
    body = "\n\n".join(
        [
            f"扬仔游星球今天整理的是 {city['name']}「{topic['name']}」攻略。不是搬运路线，也不复刻博主表达，只把公开资料里的地点、交通、体验建议重新归纳成一篇好收藏的出行思路。",
            "\n".join(f"{key}｜{value}" for key, value in g.items()),
            "3 天可以这样排：",
            "\n".join(f"{day}：{line}" for day, _, line in r),
            "发布前记得再查一次营业时间、票价、预约和交通变化；这篇更适合做攻略框架，不替代实时官方信息。",
        ]
    )
    return "\n\n".join(
        [
            f"# 扬仔游星球｜{city['name']}｜{topic['name']} 小红书图文攻略",
            "## 1. 今日选题",
            f"- 日期：{date_value}\n- 账号：扬仔游星球\n- 城市：{city['name']}，{city['country']}\n- 主题：{topic['name']}\n- 选题角度：{topic['angle']}",
            "## 2. 用户画像",
            f"- 第一次或久违重游 {city['name']}，希望先抓重点再订细节的人。\n- 偏好自由行，想要食、住、行、游、购、娱一次性看懂。\n- 对「{topic['name']}」感兴趣，但不想照搬别人路线。\n- 预算中等，愿意为交通便利和少踩坑多花一点点。",
            "## 3. 城市速览",
            f"- {city['name']} 适合按街区和交通节点规划，每天控制在 1-2 个核心片区更舒服。\n- 本期主题是「{topic['name']}」，重点放在体验密度、通勤顺路和可核验信息。\n- 资料来自官方旅游页面和开放旅行指南；正文只做归纳重写。\n- 价格、营业时间、预约政策和交通规则变化较快，发布前需要二次确认。",
            "## 3.1 资料参考策略",
            "\n".join(f"- {item}" for item in source_strategy()),
            "## 3.2 精简检索关键词",
            "\n".join(f"- {item}" for item in local_keywords(city, topic)),
            "## 4. 食住行游购娱攻略",
            "\n".join(f"### {key}\n{value}" for key, value in g.items()),
            "## 5. 3 天路线",
            "\n".join(f"- {day}｜{theme}：{line}" for day, theme, line in r),
            "## 6. 避坑提醒",
            "- 不直接照搬网上完整路线，先核对景点是否同方向、是否需要预约、是否当天开放。\n- 热门餐厅和展览至少交叉查看官方页面、地图营业状态和近期评价。\n- 交通信息以官方或运营方为准，末班车、机场线、节假日班次需要出发前再查。\n- 购物前确认退税门槛、付款方式、保质期和行李限制。\n- 热门区域可能人多，给拍照、排队、安检和休息留出缓冲。",
            "## 7. 小红书标题",
            "\n".join(f"{i}. {item}" for i, item in enumerate(titles(city, topic), 1)),
            "## 8. 小红书正文",
            body,
            "## 9. 标签",
            " ".join(tags(city, topic)),
            "## 10. 3 张图的画面脚本",
            "\n".join(f"- 图 {index}｜{title}：{script}" for index, (title, script) in enumerate(images, 1)),
            "## 11. 每张图的卡通绘图 prompt",
            "\n\n".join(f"### 图 {index}｜{title}\n{prompt_for(index, title, script)}" for index, (title, script) in enumerate(images, 1)),
            "## 12. 信息来源",
            f"- 官方旅游页面：{city['official_url']}\n- 开放旅行指南：{city['guide_url']}",
            "## 13. 版权风险自查",
            "- 未复制任何博主原文、评论、标题模板或独特表达。\n- 未使用博主图片、平台截图、路线图、地图切片或水印素材。\n- 只提炼事实、地点、价格区间、交通方式和体验建议，并重新组织为原创内容。\n- 3 天路线为编辑重组的参考框架，不复刻任何单一博主行程顺序。\n- 图片部分只提供原创卡通演示图脚本和 AI 绘图 prompt。\n- 发布前如加入真实图片，必须使用自拍、授权素材或可商用素材，并记录授权来源。",
            "",
        ]
    )


def render_research(date_value: str, city: dict[str, str], topic: dict[str, str]) -> str:
    g = guide(city, topic)
    r = route(city, topic)
    return "\n\n".join(
        [
            f"# 资料搜集与攻略要点｜{city['name']}｜{topic['name']}",
            "## 公开资料",
            f"- 官方旅游页面：{city['official_url']}",
            f"- 开放旅行指南/补充资料：{city['guide_url']}",
            "## 搜索趋势信号",
            f"- 城市池命中：{city['name']}，适合做稳定型目的地内容。",
            f"- 热点池命中：{topic['name']}，内容角度为「{topic['angle']}」。",
            "- 趋势判断来自本地 topics.csv 热点池；如接入实时搜索工具，发布前应补充搜索日期、平台和关键词。",
            "## 官方资料与开放指南关键词",
            "\n".join(f"- {item}" for item in source_strategy()),
            "\n".join(f"- 检索词：{item}" for item in local_keywords(city, topic)),
            "## 攻略要点",
            "\n".join(f"- {key}：{value}" for key, value in g.items()),
            "## 3 天路线提炼",
            "\n".join(f"- {day}｜{theme}：{line}" for day, theme, line in r),
            "## 发布前事实核验",
            "- 核对景点开放时间、票价和预约规则。",
            "- 核对公共交通末班车、机场线和节假日班次。",
            "- 核对餐厅、商店、展览等营业状态，不把未核验内容写成确定事实。",
            "- 价格只写区间或提示复核，不编造精确价格。",
            "## 版权边界",
            "- 只提炼事实、地点、价格区间、交通方式和体验建议。",
            "- 不复制博主原文、图片、截图、路线图或独特表达。",
            "- 3 天路线为编辑重组，不照搬任何单一来源的完整顺序。",
            f"- 生成日期：{date_value}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--city")
    parser.add_argument("--topic")
    args = parser.parse_args()

    brief_path = ensure_brief(args.date, args.city, args.topic)
    city_slug, topic_slug = find_selected(brief_path.read_text(encoding="utf-8"))
    cities = {item["slug"]: item for item in read_csv(ROOT / "cities.csv")}
    topics = {item["slug"]: item for item in read_csv(ROOT / "topics.csv")}
    out_dir = brief_path.parent
    city = cities[city_slug]
    topic = topics[topic_slug]
    (out_dir / "research.md").write_text(render_research(args.date, city, topic), encoding="utf-8")
    (out_dir / "post.md").write_text(render_post(args.date, city, topic), encoding="utf-8")
    print(out_dir / "post.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
