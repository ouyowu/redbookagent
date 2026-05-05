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

LANGUAGE_VARIANTS = [
    {
        "code": "zh-Hans",
        "title_suffix": "简体中文",
        "post_file": "post_zh-Hans.md",
        "tag_prefix": "#",
        "headline": "扬仔游星球",
        "day_labels": ["Day 1", "Day 2", "Day 3"],
    },
    {
        "code": "zh-Hant",
        "title_suffix": "繁體中文",
        "post_file": "post_zh-Hant.md",
        "tag_prefix": "#",
        "headline": "揚仔遊星球",
        "day_labels": ["Day 1", "Day 2", "Day 3"],
    },
    {
        "code": "en",
        "title_suffix": "English",
        "post_file": "post_en.md",
        "tag_prefix": "#",
        "headline": "Yangzai Travel Planet",
        "day_labels": ["Day 1", "Day 2", "Day 3"],
    },
]


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


def join(items: list[str], language: str) -> str:
    if language == "en":
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"
    return "、".join(items)


def guide(city: dict[str, str], topic: dict[str, str], language: str) -> dict[str, str]:
    foods = join(split(city["food"]), language)
    stays = join(split(city["stay"]), language)
    transport = join(split(city["transport"]), language)
    visits = join(split(city["visit"]), language)
    shopping = join(split(city["shopping"]), language)
    fun = join(split(city["entertainment"]), language)
    if language == "zh-Hant":
        return {
            "食": f"以 {foods} 為優先，安排在住宿或景點附近最省時間。價格先寫區間，店家營業狀態發布前再核對。",
            "住": f"第一次去可先看 {stays}。這次主題是「{topic['name']}」，住宿最好靠近當天主片區，減少跨城通勤。",
            "行": f"常用交通包括 {transport}。先確認機場或車站到飯店的第一段，再按同方向片區排每日行程。",
            "遊": f"核心玩法可從 {visits} 裡選 2-3 個，再補 1 個街區散步或室內備用點。",
            "購": f"購物與伴手禮可留意 {shopping}。下單前確認退稅、保存期限、尺寸與航空攜帶限制。",
            "娛": f"晚間體驗可從 {fun} 裡挑選。夜間活動務必再核對營業時間、預約規則與返程交通。",
        }
    if language == "en":
        return {
            "Food": f"Start with {foods}. Keep meals close to your hotel or key sights, and publish price ranges only after one more fact check.",
            "Stay": f"For a first visit, shortlist {stays}. Because this theme is about {topic['name']}, staying near the main area of the day will save energy.",
            "Transport": f"Common options include {transport}. Confirm the first leg from the airport or station, then group each day by one travel direction.",
            "Explore": f"Pick 2-3 anchor experiences from {visits}, then add one easy walking district or indoor backup stop.",
            "Shop": f"Shopping and souvenirs can focus on {shopping}. Check tax refund rules, shelf life, size, and airline carry limits before buying.",
            "Night": f"Evening ideas include {fun}. Recheck opening hours, reservation rules, and the trip back before publishing.",
        }
    return {
        "食": f"围绕 {foods} 做选择。建议把用餐安排在住宿或景点附近，价格写区间，具体店铺营业状态发布前再核对。",
        "住": f"第一次去优先考虑 {stays}。主题是「{topic['name']}」时，住宿最好靠近当天主片区，减少跨城通勤。",
        "行": f"常用交通包括 {transport}。先确认机场或车站到酒店的第一段，再按同方向片区安排每日行程。",
        "游": f"核心游玩可从 {visits} 中选择 2-3 个，再补一个街区散步或室内备用点。",
        "购": f"购物和伴手礼可关注 {shopping}。购买前确认退税、保质期、尺寸和航空携带限制。",
        "娱": f"晚间体验可从 {fun} 里挑选。夜间活动务必复核营业时间、预约规则和返程交通。",
    }


def route(city: dict[str, str], topic: dict[str, str], language: str) -> list[tuple[str, str, str]]:
    visits = split(city["visit"])
    foods = split(city["food"])
    shops = split(city["shopping"])
    fun = split(city["entertainment"])
    if language == "zh-Hant":
        return [
            ("Day 1", "抵達與城市初印象", f"抵達飯店片區 -> {visits[0]} -> 周邊散步 -> {foods[0]} -> {fun[0]}"),
            ("Day 2", f"{topic['name']} 主線日", f"{visits[1]} -> {foods[1]} -> {visits[2]} -> {shops[0]} -> {fun[1]}"),
            ("Day 3", "輕購物與彈性收尾", f"慢早餐 -> {shops[1]} 或 {shops[2]} -> {visits[3]} -> 伴手禮補貨 -> {fun[2]}"),
        ]
    if language == "en":
        return [
            ("Day 1", "Arrival and first feel of the city", f"Hotel area -> {visits[0]} -> easy walk nearby -> {foods[0]} -> {fun[0]}"),
            ("Day 2", f"Main {topic['name']} day", f"{visits[1]} -> {foods[1]} -> {visits[2]} -> {shops[0]} -> {fun[1]}"),
            ("Day 3", "Light shopping and flexible finish", f"Slow breakfast -> {shops[1]} or {shops[2]} -> {visits[3]} -> souvenir top-up -> {fun[2]}"),
        ]
    return [
        ("Day 1", "抵达与城市初印象", f"抵达酒店片区 -> {visits[0]} -> 周边散步 -> {foods[0]} -> {fun[0]}"),
        ("Day 2", f"{topic['name']}主线日", f"{visits[1]} -> {foods[1]} -> {visits[2]} -> {shops[0]} -> {fun[1]}"),
        ("Day 3", "轻购物与弹性收尾", f"慢早餐 -> {shops[1]}或{shops[2]} -> {visits[3]} -> 伴手礼补货 -> {fun[2]}"),
    ]


def titles(city: dict[str, str], topic: dict[str, str], language: str) -> list[str]:
    if language == "zh-Hant":
        return [
            f"{city['name']}{topic['name']} 攻略｜揚仔幫你整理好了",
            f"{city['name']} 3 天怎麼玩？食住行遊購娛一次講清",
            f"第一次去 {city['name']}，照這個思路做攻略",
            f"{city['name']} 不趕路玩法：適合收藏的 3 天遊",
            f"揚仔遊星球｜{city['name']}{topic['name']} 避坑版",
        ]
    if language == "en":
        return [
            f"{city['name']} {topic['name']} guide you will actually save",
            f"How to spend 3 days in {city['name']} without wasting time",
            f"First trip to {city['name']}? Start with this plan",
            f"A softer 3-day {city['name']} itinerary for free travelers",
            f"Yangzai Travel Planet | {city['name']} {topic['name']} cheat sheet",
        ]
    return [
        f"{city['name']}{topic['name']}攻略｜扬仔帮你整理好了",
        f"{city['name']}3 天怎么玩？食住行游购娱一篇讲清",
        f"第一次去{city['name']}，照这个思路做攻略",
        f"{city['name']}不赶路玩法：适合收藏的 3 天游",
        f"扬仔游星球｜{city['name']}{topic['name']}避坑版",
    ]


def tags(city: dict[str, str], topic: dict[str, str], language: str) -> list[str]:
    if language == "en":
        raw = [
            "YangzaiTravelPlanet",
            city["name"].replace(" ", ""),
            f"{city['name']}Travel".replace(" ", ""),
            f"{city['name']}Guide".replace(" ", ""),
            topic["name"].replace(" ", ""),
            "TravelGuide",
            "FreeAndEasyTravel",
            "XiaohongshuTravel",
            "LocalTips",
        ]
        return [f"#{item}" for item in raw]
    if language == "zh-Hant":
        raw = ["揚仔遊星球", city["name"], f"{city['name']}旅行", f"{city['name']}攻略", topic["name"], "旅行攻略", "自由行", "小紅書旅行", "在地推薦"]
        return [f"#{item.replace(' ', '')}" for item in raw]
    raw = ["扬仔游星球", city["name"], f"{city['name']}旅行", f"{city['name']}攻略", topic["name"], "旅行攻略", "自由行", "小红书旅行", "当地人推荐"]
    return [f"#{item.replace(' ', '')}" for item in raw]


def source_strategy(language: str) -> list[str]:
    if language == "zh-Hant":
        return [
            "官方旅遊、景點、交通、票務頁面：核對開放時間、預約、價格區間與交通規則。",
            "1 個開放旅行指南：補充片區理解、常見路線框架與體驗提醒。",
            "只記錄官方頁與開放指南連結及編輯歸納結論，不複製原文、路線圖、截圖、影片腳本或圖片。",
        ]
    if language == "en":
        return [
            "Official tourism, attraction, transport, and ticketing pages: verify opening hours, reservations, price ranges, and transport rules.",
            "One open travel guide: add area context, common route logic, and experience notes.",
            "Only keep links plus editorial summaries from official pages and open guides. Do not copy original wording, maps, screenshots, scripts, or images.",
        ]
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


def image_scripts(city: dict[str, str], topic: dict[str, str], language: str) -> list[tuple[str, str]]:
    if language == "zh-Hant":
        return [
            ("封面", f"{city['name']} {topic['name']} 封面手帳，中心是可愛大標題與城市代表元素。"),
            ("城市速覽", f"{city['name']} 旅行印象拼貼，展示地標輪廓、天氣貼紙、交通卡與小郵戳。"),
            ("3 天路線", f"{city['name']} 3 天節奏整理頁，使用區塊分區展示每日重點，不畫真實地圖。"),
            ("美食靈感", f"{city['name']} 在地美食貼紙頁，呈現 3-4 個代表小吃或飲品與短標籤。"),
            ("避坑清單", f"{city['name']} 出發前提醒頁，整理交通、預約、排隊與購物注意事項。"),
        ]
    if language == "en":
        return [
            ("Cover", f"{city['name']} {topic['name']} cover page with a clear title area and signature city elements."),
            ("City Overview", f"{city['name']} mood collage with landmark silhouettes, weather stickers, transit card, and travel icons."),
            ("3-Day Plan", f"{city['name']} three-day rhythm page with separate blocks for each day, no real map rendering."),
            ("Food Notes", f"{city['name']} food sticker page showing 3-4 local bites or drinks with short labels."),
            ("Travel Checklist", f"{city['name']} pre-departure reminder page covering transport, reservations, queues, and shopping notes."),
        ]
    return [
        ("封面", f"{city['name']} {topic['name']} 封面手账，中心是可爱大标题和城市代表元素。"),
        ("城市速览", f"{city['name']} 旅行印象拼贴，展示地标轮廓、天气贴纸、交通卡和小邮戳。"),
        ("3天路线", f"{city['name']} 3 天节奏整理页，用分区方式展示每天重点，不画真实地图。"),
        ("美食灵感", f"{city['name']} 本地美食贴纸页，呈现 3-4 个代表小吃或饮品和短标签。"),
        ("避坑清单", f"{city['name']} 出发前提醒页，整理交通、预约、排队和购物注意事项。"),
    ]


def render_intro(city: dict[str, str], topic: dict[str, str], language: str) -> str:
    if language == "zh-Hant":
        return (
            f"揚仔遊星球今天整理的是 {city['name']}「{topic['name']}」攻略。"
            "不是搬運路線，也不複製博主表達，而是把公開資料中的地點、交通與體驗建議重新整理成好收藏的出行框架。"
        )
    if language == "en":
        return (
            f"Today Yangzai Travel Planet is packaging a {city['name']} guide around {topic['name']}. "
            "This is not a copied itinerary. It is an original editorial summary built from public facts, transport notes, and experience cues."
        )
    return (
        f"扬仔游星球今天整理的是 {city['name']}「{topic['name']}」攻略。"
        "不是搬运路线，也不复刻博主表达，只把公开资料里的地点、交通、体验建议重新归纳成一篇好收藏的出行思路。"
    )


def render_user_profile(city: dict[str, str], topic: dict[str, str], language: str) -> str:
    if language == "zh-Hant":
        return (
            f"- 第一次或隔很久再去 {city['name']}，想先抓重點再訂細節的人。\n"
            "- 偏好自由行，希望食、住、行、遊、購、娛一次看懂。\n"
            f"- 對「{topic['name']}」感興趣，但不想照搬別人的完整路線。\n"
            "- 預算中等，願意為交通便利與少踩坑多花一點。"
        )
    if language == "en":
        return (
            f"- Travelers heading to {city['name']} for the first time, or after a long gap, who want the framework before the details.\n"
            "- Free-and-easy travelers who want food, stay, transport, sights, shopping, and evening ideas in one place.\n"
            f"- People curious about {topic['name']} but not interested in copying someone else's exact route.\n"
            "- Mid-range budget travelers who will pay a little more for smoother transport and fewer mistakes."
        )
    return (
        f"- 第一次或久违重游 {city['name']}，希望先抓重点再订细节的人。\n"
        "- 偏好自由行，想要食、住、行、游、购、娱一次性看懂。\n"
        f"- 对「{topic['name']}」感兴趣，但不想照搬别人路线。\n"
        "- 预算中等，愿意为交通便利和少踩坑多花一点点。"
    )


def render_city_summary(city: dict[str, str], topic: dict[str, str], language: str) -> str:
    if language == "zh-Hant":
        return (
            f"- {city['name']} 適合按街區與交通節點規劃，每天控制在 1-2 個核心片區會更舒服。\n"
            f"- 本期主題是「{topic['name']}」，重點放在體驗密度、通勤順路與可核驗資訊。\n"
            "- 資料來自官方旅遊頁與開放旅行指南；正文只做歸納重寫。\n"
            "- 價格、營業時間、預約政策與交通規則變化較快，發布前需要再確認。"
        )
    if language == "en":
        return (
            f"- {city['name']} works best when you plan by district and transit node, with only 1-2 core areas per day.\n"
            f"- This edition focuses on {topic['name']}, with emphasis on route flow, experience density, and verifiable information.\n"
            "- Sources come from official tourism pages and one open travel guide; the copy is rewritten as an original editorial summary.\n"
            "- Prices, hours, reservation policies, and transport rules can shift quickly, so verify again before posting."
        )
    return (
        f"- {city['name']} 适合按街区和交通节点规划，每天控制在 1-2 个核心片区更舒服。\n"
        f"- 本期主题是「{topic['name']}」，重点放在体验密度、通勤顺路和可核验信息。\n"
        "- 资料来自官方旅游页面和开放旅行指南；正文只做归纳重写。\n"
        "- 价格、营业时间、预约政策和交通规则变化较快，发布前需要二次确认。"
    )


def render_risk_notes(language: str) -> str:
    if language == "zh-Hant":
        return (
            "- 不直接照搬網上完整路線，先核對景點是否同方向、是否需要預約、是否當天開放。\n"
            "- 熱門餐廳與展覽至少交叉查看官方頁、地圖營業狀態與近期評價。\n"
            "- 交通資訊以官方或營運方為準，末班車、機場線與假日班次需要出發前再查。\n"
            "- 購物前確認退稅門檻、付款方式、保存期限與行李限制。\n"
            "- 熱門區域人流可能很高，給拍照、排隊、安檢與休息留出緩衝。"
        )
    if language == "en":
        return (
            "- Do not copy a full itinerary from the internet. First check whether sights are in the same direction, open that day, and reservation-ready.\n"
            "- Cross-check hot restaurants and exhibitions with official pages, current map status, and recent reviews.\n"
            "- Treat transport info as operator-owned facts; last trains, airport lines, and holiday schedules should be rechecked before departure.\n"
            "- Confirm tax refund thresholds, payment methods, shelf life, and luggage limits before shopping.\n"
            "- Busy areas need buffer time for photos, queues, security, and rest."
        )
    return (
        "- 不直接照搬网上完整路线，先核对景点是否同方向、是否需要预约、是否当天开放。\n"
        "- 热门餐厅和展览至少交叉查看官方页面、地图营业状态和近期评价。\n"
        "- 交通信息以官方或运营方为准，末班车、机场线、节假日班次需要出发前再查。\n"
        "- 购物前确认退税门槛、付款方式、保质期和行李限制。\n"
        "- 热门区域可能人多，给拍照、排队、安检和休息留出缓冲。"
    )


def render_body(date_value: str, city: dict[str, str], topic: dict[str, str], language: str) -> str:
    g = guide(city, topic, language)
    r = route(city, topic, language)
    images = image_scripts(city, topic, language)
    labels = {
        "zh-Hans": {
            "title": f"# 扬仔游星球｜{city['name']}｜{topic['name']} 小红书图文攻略｜简体中文",
            "pick": "## 1. 今日选题",
            "profile": "## 2. 用户画像",
            "summary": "## 3. 城市速览",
            "sources": "## 3.1 资料参考策略",
            "keywords": "## 3.2 精简检索关键词",
            "guide": "## 4. 食住行游购娱攻略",
            "route": "## 5. 3天路线",
            "risk": "## 6. 避坑提醒",
            "titles": "## 7. 小红书标题",
            "body": "## 8. 小红书正文",
            "tags": "## 9. 标签",
            "images": "## 10. 5张图的画面脚本",
            "prompts": "## 11. 每张图的卡通绘图 prompt",
            "info": "## 12. 信息来源",
            "copyright": "## 13. 版权风险自查",
        },
        "zh-Hant": {
            "title": f"# 揚仔遊星球｜{city['name']}｜{topic['name']} 小紅書圖文攻略｜繁體中文",
            "pick": "## 1. 今日選題",
            "profile": "## 2. 使用者輪廓",
            "summary": "## 3. 城市速覽",
            "sources": "## 3.1 資料參考策略",
            "keywords": "## 3.2 精簡檢索關鍵詞",
            "guide": "## 4. 食住行遊購娛攻略",
            "route": "## 5. 3天路線",
            "risk": "## 6. 避坑提醒",
            "titles": "## 7. 小紅書標題",
            "body": "## 8. 小紅書正文",
            "tags": "## 9. 標籤",
            "images": "## 10. 5張圖的畫面腳本",
            "prompts": "## 11. 每張圖的卡通繪圖 Prompt",
            "info": "## 12. 資訊來源",
            "copyright": "## 13. 版權風險自查",
        },
        "en": {
            "title": f"# Yangzai Travel Planet | {city['name']} | {topic['name']} Xiaohongshu Guide | English",
            "pick": "## 1. Topic Snapshot",
            "profile": "## 2. Audience",
            "summary": "## 3. City Summary",
            "sources": "## 3.1 Source Strategy",
            "keywords": "## 3.2 Search Keywords",
            "guide": "## 4. Food Stay Move Explore Shop Night",
            "route": "## 5. 3-Day Route",
            "risk": "## 6. Watchouts",
            "titles": "## 7. Xiaohongshu Title Ideas",
            "body": "## 8. Post Copy",
            "tags": "## 9. Tags",
            "images": "## 10. Image Scripts for 5 Slides",
            "prompts": "## 11. Cartoon Prompt for Each Slide",
            "info": "## 12. Sources",
            "copyright": "## 13. Copyright Self-Check",
        },
    }[language]
    meta = {
        "zh-Hans": f"- 日期：{date_value}\n- 账号：扬仔游星球\n- 城市：{city['name']}，{city['country']}\n- 主题：{topic['name']}\n- 选题角度：{topic['angle']}",
        "zh-Hant": f"- 日期：{date_value}\n- 帳號：揚仔遊星球\n- 城市：{city['name']}，{city['country']}\n- 主題：{topic['name']}\n- 選題角度：{topic['angle']}",
        "en": f"- Date: {date_value}\n- Account: Yangzai Travel Planet\n- City: {city['name']}, {city['country']}\n- Theme: {topic['name']}\n- Angle: {topic['angle']}",
    }[language]
    body_text = "\n\n".join(
        [
            render_intro(city, topic, language),
            "\n".join(f"{key}｜{value}" for key, value in g.items()),
            "3 天可以这样排：" if language == "zh-Hans" else ("3 天可以這樣排：" if language == "zh-Hant" else "A clean 3-day flow could look like this:"),
            "\n".join(f"{day}：{line}" if language != "en" else f"{day}: {line}" for day, _, line in r),
            "发布前记得再查一次营业时间、票价、预约和交通变化；这篇更适合做攻略框架，不替代实时官方信息。"
            if language == "zh-Hans"
            else (
                "發布前記得再查一次營業時間、票價、預約與交通變化；這篇更適合作為攻略框架，不替代即時官方資訊。"
                if language == "zh-Hant"
                else "Before posting, recheck opening hours, prices, reservations, and transport changes. This is a planning framework, not a replacement for live official information."
            ),
        ]
    )
    return "\n\n".join(
        [
            labels["title"],
            labels["pick"],
            meta,
            labels["profile"],
            render_user_profile(city, topic, language),
            labels["summary"],
            render_city_summary(city, topic, language),
            labels["sources"],
            "\n".join(f"- {item}" for item in source_strategy(language)),
            labels["keywords"],
            "\n".join(f"- {item}" for item in local_keywords(city, topic)),
            labels["guide"],
            "\n".join(f"### {key}\n{value}" for key, value in g.items()),
            labels["route"],
            "\n".join(f"- {day}｜{theme}：{line}" if language != "en" else f"- {day} | {theme}: {line}" for day, theme, line in r),
            labels["risk"],
            render_risk_notes(language),
            labels["titles"],
            "\n".join(f"{i}. {item}" for i, item in enumerate(titles(city, topic, language), 1)),
            labels["body"],
            body_text,
            labels["tags"],
            " ".join(tags(city, topic, language)),
            labels["images"],
            "\n".join(f"- 图 {index}｜{title}：{script}" if language != "en" else f"- Slide {index} | {title}: {script}" for index, (title, script) in enumerate(images, 1)),
            labels["prompts"],
            "\n\n".join(
                f"### 图 {index}｜{title}\n{script}"
                if language != "en"
                else f"### Slide {index} | {title}\n{script}"
                for index, (title, script) in enumerate(images, 1)
            ),
            labels["info"],
            f"- 官方旅游页面：{city['official_url']}\n- 开放旅行指南：{city['guide_url']}"
            if language == "zh-Hans"
            else (
                f"- 官方旅遊頁面：{city['official_url']}\n- 開放旅行指南：{city['guide_url']}"
                if language == "zh-Hant"
                else f"- Official tourism page: {city['official_url']}\n- Open travel guide: {city['guide_url']}"
            ),
            labels["copyright"],
            (
                "- 未复制任何博主原文、评论、标题模板或独特表达。\n- 未使用博主图片、平台截图、路线图、地图切片或水印素材。\n- 只提炼事实、地点、价格区间、交通方式和体验建议，并重新组织为原创内容。\n- 3天路线为编辑重组的参考框架，不复刻任何单一博主行程顺序。\n- 图片部分只提供原创卡通演示图脚本，供你自行出图。\n- 发布前如加入真实图片，必须使用自拍、授权素材或可商用素材，并记录授权来源。"
                if language == "zh-Hans"
                else (
                    "- 未複製任何博主原文、評論、標題模板或獨特表達。\n- 未使用博主圖片、平台截圖、路線圖、地圖切片或水印素材。\n- 只提煉事實、地點、價格區間、交通方式與體驗建議，並重新組織為原創內容。\n- 3天路線為編輯重組的參考框架，不複刻任何單一博主行程順序。\n- 圖片部分只提供原創卡通示意腳本，供你自行出圖。\n- 發布前如加入真實圖片，必須使用自拍、授權素材或可商用素材，並記錄授權來源。"
                    if language == "zh-Hant"
                    else "- No blogger wording, comments, title templates, or distinctive expressions were copied.\n- No blogger photos, platform screenshots, route maps, map tiles, or watermarked assets were used.\n- Only facts, places, price ranges, transport modes, and experience notes were extracted and rewritten as original copy.\n- The 3-day route is an editorial framework, not a cloned sequence from any one source.\n- The image section only provides original cartoon slide scripts for your own image production.\n- If you later add real photos, use self-shot, licensed, or commercially usable assets and keep the source record."
                )
            ),
            "",
        ]
    )


def render_research(date_value: str, city: dict[str, str], topic: dict[str, str]) -> str:
    g = guide(city, topic, "zh-Hans")
    r = route(city, topic, "zh-Hans")
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
            "\n".join(f"- {item}" for item in source_strategy("zh-Hans")),
            "\n".join(f"- 检索词：{item}" for item in local_keywords(city, topic)),
            "## 攻略要点",
            "\n".join(f"- {key}：{value}" for key, value in g.items()),
            "## 3天路线提炼",
            "\n".join(f"- {day}｜{theme}：{line}" for day, theme, line in r),
            "## 发布前事实核验",
            "- 核对景点开放时间、票价和预约规则。",
            "- 核对公共交通末班车、机场线和节假日班次。",
            "- 核对餐厅、商店、展览等营业状态，不把未核验内容写成确定事实。",
            "- 价格只写区间或提示复核，不编造精确价格。",
            "## 版权边界",
            "- 只提炼事实、地点、价格区间、交通方式和体验建议。",
            "- 不复制博主原文、图片、截图、路线图或独特表达。",
            "- 3天路线为编辑重组，不照搬任何单一来源的完整顺序。",
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
    for variant in LANGUAGE_VARIANTS:
        content = render_body(args.date, city, topic, variant["code"])
        (out_dir / variant["post_file"]).write_text(content, encoding="utf-8")
        if variant["code"] == "zh-Hans":
            (out_dir / "post.md").write_text(content, encoding="utf-8")
    print(out_dir / "post.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
