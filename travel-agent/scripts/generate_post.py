#!/usr/bin/env python3
"""Generate original Xiaohongshu travel copy from the daily city content matrix."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = [("zh-Hans", "post_zh-Hans.md", "扬仔游星球"), ("zh-Hant", "post_zh-Hant.md", "揚仔遊星球"), ("en", "post_en.md", "Yangzai Travel Planet")]


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d-%H%M")


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split(value: str) -> list[str]:
    return [x.strip() for x in value.split(";") if x.strip()]


def join(items: list[str], lang: str) -> str:
    if lang == "en":
        return ", ".join(items[:-1]) + (f", and {items[-1]}" if len(items) > 1 else (items[0] if items else ""))
    return "、".join(items)


def ensure_brief(date_value: str, city: str | None) -> Path:
    matches = list((ROOT / "outputs").glob(f"{date_value}-*/brief.md"))
    if matches and not city:
        return matches[0]
    cmd = ["python3", str(ROOT / "scripts" / "pick_topic.py"), "--date", date_value]
    if city:
        cmd += ["--city", city]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return Path(result.stdout.strip())


def city_slug_from_brief(text: str) -> str:
    match = re.search(r"^- 城市 slug：(.+)$", text, re.M)
    if not match:
        raise SystemExit("brief.md 缺少城市 slug")
    return match.group(1).strip()


def topic_hint(slug: str, city: dict[str, str], lang: str) -> tuple[str, str, str]:
    foods = join(split(city.get("food", "")), lang)
    stays = join(split(city.get("stay", "")), lang)
    transport = join(split(city.get("transport", "")), lang)
    visits = join(split(city.get("visit", "")), lang)
    shopping = join(split(city.get("shopping", "")), lang)
    fun = join(split(city.get("entertainment", "")), lang)
    zh = {
        "food-overview": (f"先把 {foods} 拆成餐厅、小馆、早餐、甜品、伴手礼。", "优先写多平台反复出现的本地人推荐关键词。", "补查店名、营业状态、排队强度和人均区间。"),
        "restaurants": (f"按 {foods} 归纳高频吃法，再整理核心商圈、景点周边、居民区。", "写成可执行的片区选择，不做无法证明的绝对排名。", "补查营业时间、预约和排队。"),
        "fly-restaurants": (f"从 {foods} 里拆出烟火气小馆、社区店和老字号。", "写成适合体验本地日常味的方向。", "补查卫生评价、营业时间和是否适合同行人群。"),
        "hotpot": (f"围绕 {foods} 中最代表性的热菜或锅物做索引。", "按口味强度、排队强度、片区顺路程度拆开。", "补查门店状态、锅底价格、人均区间和预约。"),
        "breakfast": (f"把 {foods} 里的本地早餐拆成早起路线。", "写清几点去、哪一带顺路、是否容易售完。", "补查早关门和周末差异。"),
        "snacks": (f"结合 {shopping} 整理零食和伴手礼。", "按送人、自留、方便托运分组。", "补查保质期、包装和航空限制。"),
        "hotels": (f"住宿从 {stays} 做区域选择逻辑。", f"拆成方便吃、方便逛、方便坐 {transport}。", "补查装修年份、噪音和早晚高峰。"),
        "transport": (f"交通从 {transport} 拆开讲。", "先写机场/高铁进城，再写市内移动和少绕路动线。", "补查票价、首末班和节假日拥堵。"),
        "attractions": (f"景点从 {visits} 分成首次必看、轻松散步、文化体验和拍照点。", "按体力、天气、预约难度选择，不照搬路线。", "补查门票、预约、开放时间和限流。"),
        "citywalk": (f"从 {visits} 里挑能顺着走的街区。", "每条路线只保留一个核心主题。", "补查步行时长、坡度和地铁口。"),
        "photospots": (f"从 {visits} 和 {shopping} 中挑辨识度高的点。", "分白天、傍晚、夜景。", "补查限流、预约和光线时段。"),
        "museums": (f"从 {visits} 的文化点延伸博物馆和展览。", "写清预约难度、逛多久、是否顺路。", "补查闭馆日和特展时间。"),
        "shopping": (f"购物从 {shopping} 拆成商圈、商场、商业街、市集和文创店。", "按好逛、好买、好拍、好休息分类。", "补查营业时间、退税和店铺变动。"),
        "what-to-buy": (f"从 {shopping} 和 {foods} 提炼特产、文创、零食、实用小物。", "按送人、自用、轻便好带、不建议多买分组。", "补查保质期、托运限制和价格波动。"),
        "shoppingstreets": (f"商业街结合 {shopping} 来写。", "按年轻人逛街、伴手礼补货、雨天室内组织。", "补查闭店时间和节假日活动。"),
        "markets": (f"市集夜市结合 {shopping} 与 {foods}。", "分早市、夜市、游客友好型市场。", "补查开市时段和卫生争议。"),
        "nightlife": (f"夜生活围绕 {fun} 展开。", "拆夜游、演出、livehouse、微醺、夜景散步。", "补查演出排期、年龄限制和返程交通。"),
        "nightview": (f"夜景结合 {fun} 和 {visits}。", "写哪一带看灯、拍照、返程方便。", "补查亮灯时间、天气和晚归交通。"),
        "cafes": (f"咖啡馆结合 {visits} 或 {shopping} 片区。", "分出片、好坐、适合躲雨。", "补查店休、低消和排队。"),
        "desserts": (f"甜品和 {shopping} 或 {visits} 顺路安排。", "分解馋、打包、拍照。", "补查季节限定和售完时间。"),
        "rainyday": (f"雨天从 {visits}、{shopping}、{fun} 选室内点。", "强调动线短、地铁直达、不狼狈。", "补查雨季开放和室内排队。"),
        "parents": (f"带爸妈用 {stays} 和 {transport} 做少折腾路线。", "写少走路、电梯多、吃饭稳。", "补查摆渡、轮椅和洗手间。"),
        "family": (f"亲子从 {visits} 与 {fun} 中挑轻松点。", "写年龄、预约、遮阳休息。", "补查身高限制和儿童票。"),
        "daytrip": (f"周边一日游从 {transport} 的便利度切入。", "只保留当天能来回的方向。", "补查车次、末班和天气。"),
        "checklist": (f"避坑要连接 {transport}、{stays}、{shopping}、{foods}。", "提前说清第一次去容易忽略的细节。", "补查价格、预约新规和限流。"),
    }
    if lang != "en":
        return zh.get(slug, zh["checklist"])
    cn = zh.get(slug, zh["checklist"])
    return (f"Use city facts around {foods}, {stays}, {transport}, {visits}, {shopping}, and {fun}.", "Rewrite the angle as traveler-friendly choices, not copied creator wording.", "Recheck hours, prices, reservations, transport, and rights before posting.")


def matrix(city: dict[str, str], lang: str) -> str:
    foods, stays, transport = join(split(city.get("food", "")), lang), join(split(city.get("stay", "")), lang), join(split(city.get("transport", "")), lang)
    visits, shopping, fun = join(split(city.get("visit", "")), lang), join(split(city.get("shopping", "")), lang), join(split(city.get("entertainment", "")), lang)
    if lang == "en":
        return "\n".join([f"- Food: restaurants, small eateries, breakfast, signature dishes, desserts, and souvenirs around {foods}.", f"- Stay: compare {stays} by food access, shopping, transit, noise, and budget.", f"- Transport: arrival and in-city movement through {transport}.", f"- Attractions: first-time sights, citywalk, museums, photo spots, and day trips around {visits}.", f"- Shopping: {shopping} as malls, streets, markets, design stores, and what-to-buy.", f"- Nightlife: {fun} for night views, shows, live music, night markets, and safe return."])
    if lang == "zh-Hant":
        return "\n".join([f"- 食：圍繞 {foods}，拆餐廳、小館、早餐、招牌菜、甜品、伴手禮。", f"- 住：圍繞 {stays}，比較吃喝、逛街、交通、噪音與預算。", f"- 行：圍繞 {transport}，說清抵達、市內移動、少繞路和返程。", f"- 遊：圍繞 {visits}，覆蓋首次必看、citywalk、博物館、拍照點和一日遊。", f"- 購：圍繞 {shopping}，拆商圈、市集、文創與什麼值得買。", f"- 娛：圍繞 {fun}，整理夜景、演出、livehouse、夜市、微醺和返程。"])
    return "\n".join([f"- 食：围绕 {foods}，拆餐厅、小馆、早餐、招牌菜、甜品、伴手礼。", f"- 住：围绕 {stays}，比较吃喝便利、逛街便利、交通、噪音和预算。", f"- 行：围绕 {transport}，说清抵达、市内移动、少绕路和返程提醒。", f"- 游：围绕 {visits}，覆盖首次必看、citywalk、博物馆、拍照点和周边一日游。", f"- 购：围绕 {shopping}，拆商圈、商场、市集、文创和什么值得买。", f"- 娱：围绕 {fun}，整理夜景、演出、livehouse、夜市、微醺和安全返程。"])


def image_scripts(city: dict[str, str], lang: str) -> list[tuple[str, str]]:
    n = city["name"]
    if lang == "en":
        return [("Cover", f"{n} city guide cover."), ("Topic Matrix", f"{n} food, stay, transport, attractions, shopping, and nightlife index."), ("Local Food", f"{n} restaurants, small eateries, hot dishes, breakfast, snacks, and desserts."), ("Stay and Transport", f"{n} stay zones, arrival transport, metro, taxi, and low-detour tips."), ("Attractions", f"{n} sights, citywalk, museums, photo spots, and day trips."), ("Shop and Buy", f"{n} shopping districts, markets, souvenirs, local design, and what-to-buy."), ("Nightlife", f"{n} night walks, views, performances, live music, drinks, and late return."), ("Fact Check", f"{n} reservations, queues, weather backup, prices, and copyright notes.")]
    if lang == "zh-Hant":
        return [("封面", f"{n} 熱門話題合集封面。"), ("內容矩陣", f"{n} 食住行遊購娛六大索引。"), ("本地吃喝", f"{n} 餐廳、小館、鍋物、早餐、零食與甜品。"), ("住宿交通", f"{n} 住哪裡、進城交通、地鐵打車和少繞路。"), ("景點玩法", f"{n} 首次必看、citywalk、博物館、拍照點和一日遊。"), ("購物值得買", f"{n} 商圈、市集、伴手禮、文創和什麼值得買。"), ("夜生活", f"{n} 夜遊、夜景、演出、livehouse、微醺和返程。"), ("避坑核驗", f"{n} 預約、排隊、天氣、價格和版權自查。")]
    return [("封面", f"{n} 热门话题合集封面。"), ("内容矩阵", f"{n} 食住行游购娱六大索引。"), ("本地吃喝", f"{n} 餐厅、小馆、火锅热菜、早餐、零食和甜品。"), ("住宿交通", f"{n} 住哪里、进城交通、地铁打车和少绕路。"), ("景点玩法", f"{n} 首次必看、citywalk、博物馆、拍照点和一日游。"), ("购物值得买", f"{n} 商圈、市集、伴手礼、文创和什么值得买。"), ("夜生活", f"{n} 夜游、夜景、演出、livehouse、微醺和返程。"), ("避坑核验", f"{n} 预约、排队、天气、价格和版权自查。")]


def render(date_value: str, city: dict[str, str], data: dict[str, object], lang: str) -> str:
    topics = data["topics"]
    title = f"# 扬仔游星球｜{city['name']}热门旅游内容矩阵 Top{len(topics)}" if lang == "zh-Hans" else (f"# 揚仔遊星球｜{city['name']}熱門旅遊內容矩陣 Top{len(topics)}" if lang == "zh-Hant" else f"# Yangzai Travel Planet | {city['name']} Top {len(topics)} Travel Content Matrix")
    labels = {
        "zh-Hans": ("选题信息", "选题方法", "城市内容矩阵", "高热旅游话题", "小红书标题", "小红书正文", "标签", "配图脚本", "公开来源", "版权风险自查"),
        "zh-Hant": ("選題資訊", "選題方法", "城市內容矩陣", "高熱旅遊話題", "小紅書標題", "小紅書正文", "標籤", "配圖腳本", "公開來源", "版權風險自查"),
        "en": ("Topic Snapshot", "Discovery Method", "City Content Matrix", "Hot Travel Topics", "Title Ideas", "Post Copy", "Tags", "Image Script", "Public Sources", "Copyright Self-Check"),
    }[lang]
    title_ideas = [f"{city['name']}旅游攻略｜食住行游购娱一次看", f"{city['name']}现在大家最爱搜什么？", f"{city['name']}哪里好吃好逛好买？", f"扬仔游星球｜{city['name']}热门话题合集", f"第一次去{city['name']}先看这篇"] if lang == "zh-Hans" else [f"{city['name']} travel guide: food, stay, move, play, shop, night", f"What people keep searching about {city['name']}", f"{city['name']} guide pack from public travel topics", f"Yangzai Travel Planet | {city['name']} hot topics", f"First trip to {city['name']} starts here"]
    blocks = []
    for t in topics:
        advice, structure, checks = topic_hint(str(t["slug"]), city, lang)
        blocks.append("\n".join([f"### {t['rank']}. {t['name']}", f"- 为什么值得做：{t['focus']}" if lang != "en" else f"- Why it matters: {t['focus']}", f"- 内容整理方向：{advice}" if lang != "en" else f"- Structure: {advice}", f"- 收藏向写法：{structure}" if lang != "en" else f"- Reader angle: {structure}", f"- 发布前补查：{checks}" if lang != "en" else f"- Fact check: {checks}"]))
    sources = []
    for t in topics:
        for r in t.get("results", [])[:1]:
            if r.get("link"):
                sources.append(f"- {t['name']}｜{r['platform']}｜{r['title']}｜{r['link']}" if lang != "en" else f"- {t['name']} | {r['platform']} | {r['title']} | {r['link']}")
    tags = " ".join([f"#{x}" for x in ["扬仔游星球", city["name"], f"{city['name']}旅行", f"{city['name']}攻略", "小红书旅行", "旅游话题", "城市攻略", "当地人推荐", "避坑攻略", "什么值得买"]]) if lang != "en" else " ".join(["#YangzaiTravelPlanet", f"#{city['name'].replace(' ', '')}Travel", "#TravelGuide", "#XiaohongshuTravel", "#HotTopics"])
    images = "\n".join(f"- 图 {i}｜{a}：{b}" if lang != "en" else f"- Slide {i} | {a}: {b}" for i, (a, b) in enumerate(image_scripts(city, lang), 1))
    copyright_text = "- 只提炼公开资料里的共性事实和趋势，不复制博主原文、截图、路线图、口播、标题模板或独特表达。\n- 所有店名、价格、营业时间、预约和交通信息发布前必须人工复核。\n- 图片只生成原创卡通手账 prompt，不使用真实品牌 Logo、真实地图或受版权保护角色。" if lang != "en" else "- Public sources are used only for factual and trend signals. No creator wording, screenshots, route maps, titles, or scripts are copied.\n- Exact stores, prices, hours, reservations, and transport details require manual verification before posting.\n- Image prompts are original cartoon travel-journal directions only."
    return "\n\n".join([title, f"## 1. {labels[0]}", f"- 日期：{date_value}\n- 城市：{city['name']}\n- 内容主题：{data['content_theme']}", f"## 2. {labels[1]}", "- 参考小红书、抖音、Bilibili、马蜂窝、携程、飞猪、Tripadvisor、地图点评平台和官方公开资料的高频话题。\n- 只做重写归纳和交叉验证，不照搬任何单一创作者。" if lang != "en" else "- Use public travel topic signals and official/map references as directional evidence.\n- Rewrite and cross-check; do not copy any single creator.", f"## 3. {labels[2]}", matrix(city, lang), f"## 4. {len(topics)}个{labels[3]}", "\n\n".join(blocks), f"## 5. {labels[4]}", "\n".join(f"{i}. {x}" for i, x in enumerate(title_ideas, 1)), f"## 6. {labels[5]}", f"这一篇把 {city['name']} 拆成食、住、行、游、购、娱和避坑几个可连续发布的内容方向。先用内容矩阵帮用户建立城市判断，再把餐厅、小馆、火锅/代表热菜、早餐、住宿片区、交通、景点、购物、值得买、夜生活分别拆成独立笔记。", f"## 7. {labels[6]}", tags, f"## 8. {labels[7]}", images, f"## 9. {labels[8]}", "\n".join(sources) or "- 本轮仅输出关键词方向，发布前补充可访问链接。", f"## 10. {labels[9]}", copyright_text, ""])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today())
    parser.add_argument("--city")
    args = parser.parse_args()
    brief = ensure_brief(args.date, args.city)
    out = brief.parent
    city_slug = city_slug_from_brief(brief.read_text(encoding="utf-8"))
    city = {x["slug"]: x for x in read_csv("cities.csv")}[city_slug]
    data = json.loads((out / "hot_topics.json").read_text(encoding="utf-8"))
    (out / "research.md").write_text(render(args.date, city, data, "zh-Hans"), encoding="utf-8")
    for lang, filename, _ in LANGS:
        content = render(args.date, city, data, lang)
        (out / filename).write_text(content, encoding="utf-8")
        if lang == "zh-Hans":
            (out / "post.md").write_text(content, encoding="utf-8")
    topic_dir = out / "topics"
    topic_dir.mkdir(exist_ok=True)
    for topic in data["topics"]:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(topic["slug"]))
        (topic_dir / f"{int(topic['rank']):02d}-{safe}-zh-Hans.md").write_text(render(args.date, city, {**data, "topics": [topic], "content_theme": topic["name"]}, "zh-Hans"), encoding="utf-8")
    print(out / "post.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
