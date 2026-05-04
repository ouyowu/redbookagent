#!/usr/bin/env python3
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


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def split(v: str) -> list[str]:
    return [x.strip() for x in v.split(';') if x.strip()]


def join(v: str) -> str:
    return '、'.join(split(v))


def ensure_brief(date: str, city: str | None, topic: str | None) -> Path:
    matches = sorted((ROOT / 'outputs').glob(f'{date}-*/brief.md'))
    if matches and not city and not topic:
        return matches[0]
    cmd = ['python3', str(ROOT / 'scripts' / 'pick_topic.py'), '--date', date]
    if city:
        cmd += ['--city', city]
    if topic:
        cmd += ['--topic', topic]
    return Path(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip())


def selected(brief: str) -> tuple[str, str]:
    city = re.search(r'^- 城市 slug：(.+)$', brief, re.M)
    topic = re.search(r'^- 主题 slug：(.+)$', brief, re.M)
    if not city or not topic:
        raise SystemExit('brief.md 缺少 slug')
    return city.group(1).strip(), topic.group(1).strip()


def guide(c: dict[str, str], t: dict[str, str]) -> dict[str, str]:
    return {
        '食': f'围绕{join(c["food"])}做选择。建议把用餐安排在住宿或景点附近，价格写区间，具体店铺营业状态发布前再核对。',
        '住': f'第一次去优先考虑{join(c["stay"])}。主题是「{t["name"]}」时，住宿最好靠近当天主片区，减少跨城通勤。',
        '行': f'常用交通包括{join(c["transport"])}。先确认机场/车站到酒店的第一段，再按同方向片区安排每日行程。',
        '游': f'核心游玩可从{join(c["visit"])}中选择 2-3 个，再补一个街区散步或室内备用点。',
        '购': f'购物和伴手礼可关注{join(c["shopping"])}。购买前确认退税、保质期、尺寸和航空携带限制。',
        '娱': f'晚间体验可从{join(c["entertainment"])}里挑选。夜间活动务必复核营业时间、预约规则和返程交通。',
    }


def route(c: dict[str, str], t: dict[str, str]) -> list[str]:
    v, f, s, e = split(c['visit']), split(c['food']), split(c['shopping']), split(c['entertainment'])
    return [
        f'Day 1｜抵达与城市初印象：抵达酒店片区 -> {v[0]} -> 周边散步 -> {f[0]} -> {e[0]}',
        f'Day 2｜{t["name"]}主线日：{v[1]} -> {f[1]} -> {v[2]} -> {s[0]} -> {e[1]}',
        f'Day 3｜轻购物与弹性收尾：慢早餐 -> {s[1]}或{s[2]} -> {v[3]} -> 伴手礼补货 -> {e[2]}',
    ]


def titles(c: dict[str, str], t: dict[str, str]) -> list[str]:
    return [
        f'{c["name"]}{t["name"]}攻略｜扬仔帮你整理好了',
        f'{c["name"]}3 天怎么玩？食住行游购娱一篇讲清',
        f'第一次去{c["name"]}，照这个思路做攻略',
        f'{c["name"]}不赶路玩法：适合收藏的 3 天游',
        f'扬仔游星球｜{c["name"]}{t["name"]}避坑版',
    ]


def tags(c: dict[str, str], t: dict[str, str]) -> str:
    raw = ['扬仔游星球', c['name'], f'{c["name"]}旅行', f'{c["name"]}攻略', t['name'], '旅行攻略', '自由行', '小红书旅行', '当地人推荐', '食住行游购娱']
    return ' '.join('#' + x.replace(' ', '') for x in raw)


def source_strategy() -> list[str]:
    return [
        '官方旅游、景点、交通、票务页面：核对开放时间、预约、价格区间和交通规则。',
        '小红书、抖音、bilibili等公开高互动攻略：提炼高频地点、体验关键词、避坑点和当地人推荐线索。',
        '马蜂窝、携程、飞猪、Tripadvisor、Google Maps/高德/大众点评等公开评价与攻略：交叉验证热度、排队、片区选择和近期反馈。',
        '只记录可访问来源链接和编辑归纳结论，不复制原文、评论、截图、路线图、视频脚本或图片。',
    ]


def local_keywords(c: dict[str, str], t: dict[str, str]) -> list[str]:
    return [
        f'{c["name"]} 当地人推荐 {t["name"]}',
        f'{c["name"]} 本地人常去 美食 街区',
        f'{c["name"]} 少游客 不绕路 避坑',
        f'{c["name"]} 第一次去 交通 住宿 区域',
        f'{c["name"]} 小红书 抖音 bilibili 高赞攻略',
    ]


def image_scripts(c: dict[str, str], t: dict[str, str]) -> list[tuple[str, str]]:
    return [
        ('封面', f'扬仔游星球 {c["name"]} {t["name"]} 攻略封面，原创城市氛围、手账贴纸和标题区。'),
        ('用户画像', '卡通人物展示第一次自由行、收藏攻略、查交通和做预算的场景。'),
        ('城市速览', f'{c["name"]} 城市氛围拼贴，地标轮廓、天气图标、交通卡、行李箱，不画真实地图。'),
        ('食住行', '三栏信息卡：美食、住宿区域、交通方式，用原创图标和短标签呈现。'),
        ('游购娱', '三栏信息卡：景点街区、购物伴手礼、晚间体验，用原创图标和卡通人物呈现。'),
        ('3 天路线', '三天行程时间轴，使用抽象箭头和片区标签，不绘制真实路线图或地图路径。'),
        ('避坑提醒', '出发前提醒卡，包含预约、营业时间、末班车、退税、天气等原创图标。'),
        ('版权自查', '内容合规检查卡，展示原创、重写、来源链接、禁止截图和禁止搬运的图标。'),
    ]


def prompt_for(i: int, title: str, script: str) -> str:
    return (
        f'原创小红书旅行攻略卡通插画，第 {i} 张，主题：{title}。{script}'
        '画面风格：可爱卡通旅行手账、奶油色纸张纹理、水彩和彩铅质感、手绘黑色细描边、贴纸拼贴、胶带、印章、星星爱心、旅行小图标；'
        '构图：竖版手机壁纸比例，适合 iPhone 17 Pro Max 视觉裁切，高清细节，留出安全边距；'
        '文字：只保留核心短句，使用金陵体、圆体或相近的圆润手写中文字体；'
        '品牌：角落加入小而清晰的原创水印/印章文字“扬仔游星球”；'
        '版权限制：不要使用真实照片、博主截图、真实地图、真实路线图、平台水印、品牌 Logo、受版权保护角色，也不要复刻参考图的具体版式和独特表达。'
    )


def render_post(date: str, c: dict[str, str], t: dict[str, str]) -> str:
    g, r, imgs = guide(c, t), route(c, t), image_scripts(c, t)
    body = '\n\n'.join([
        f'扬仔游星球今天整理的是 {c["name"]}「{t["name"]}」攻略。不是搬运路线，也不复刻博主表达，只把公开资料里的地点、交通、体验建议重新归纳成一篇好收藏的出行思路。',
        '\n'.join(f'{k}｜{v}' for k, v in g.items()),
        '3 天可以这样排：', '\n'.join(r),
        '发布前记得再查一次营业时间、票价、预约和交通变化；这篇更适合做攻略框架，不替代实时官方信息。',
    ])
    return '\n\n'.join([
        f'# 扬仔游星球｜{c["name"]}｜{t["name"]} 小红书图文攻略',
        '## 1. 今日选题', f'- 日期：{date}\n- 账号：扬仔游星球\n- 城市：{c["name"]}，{c["country"]}\n- 主题：{t["name"]}\n- 选题角度：{t["angle"]}',
        '## 2. 用户画像', f'- 第一次或久违重游 {c["name"]}，希望先抓重点再订细节的人。\n- 偏好自由行，想要食、住、行、游、购、娱一次性看懂。\n- 对「{t["name"]}」感兴趣，但不想照搬别人路线。\n- 预算中等，愿意为交通便利和少踩坑多花一点点。',
        '## 3. 城市速览', f'- {c["name"]} 适合按街区和交通节点规划，每天控制在 1-2 个核心片区更舒服。\n- 本期主题是「{t["name"]}」，重点放在体验密度、通勤顺路和可核验信息。\n- 资料来自官方旅游页面和开放旅行指南；正文只做归纳重写。\n- 价格、营业时间、预约政策和交通规则变化较快，发布前需要二次确认。',
        '## 3.1 资料参考策略', '\n'.join('- ' + x for x in source_strategy()),
        '## 3.2 当地人推荐关键词', '\n'.join('- ' + x for x in local_keywords(c, t)),
        '## 4. 食住行游购娱攻略', '\n'.join(f'### {k}\n{v}' for k, v in g.items()),
        '## 5. 3 天路线', '\n'.join('- ' + x for x in r),
        '## 6. 避坑提醒', '- 不直接照搬网上完整路线，先核对景点是否同方向、是否需要预约、是否当天开放。\n- 热门餐厅和展览至少交叉查看官方页面、地图营业状态和近期评价。\n- 交通信息以官方或运营方为准，末班车、机场线、节假日班次需要出发前再查。\n- 购物前确认退税门槛、付款方式、保质期和行李限制。\n- 热门区域可能人多，给拍照、排队、安检和休息留出缓冲。',
        '## 7. 小红书标题', '\n'.join(f'{i}. {x}' for i, x in enumerate(titles(c, t), 1)),
        '## 8. 小红书正文', body,
        '## 9. 标签', tags(c, t),
        '## 10. 6-9 张图的画面脚本', '\n'.join(f'- 图 {i}｜{title}：{script}' for i, (title, script) in enumerate(imgs, 1)),
        '## 11. 每张图的卡通绘图 prompt', '\n\n'.join(f'### 图 {i}｜{title}\n{prompt_for(i, title, script)}' for i, (title, script) in enumerate(imgs, 1)),
        '## 12. 信息来源', f'- 官方/开放资料：{c["official_url"]}\n- 开放旅行指南：{c["guide_url"]}\n- 平台参考方向：小红书、抖音、bilibili、马蜂窝、携程、飞猪、Tripadvisor、Google Maps/高德/大众点评等公开攻略与评价；实际发布前应补充当天检索到的具体链接。',
        '## 13. 版权风险自查', '- 未复制任何博主原文、评论、标题模板或独特表达。\n- 未使用博主图片、平台截图、路线图、地图切片或水印素材。\n- 未复用小红书、抖音、bilibili等平台单条内容的镜头脚本、封面构图、口播结构或独特梗。\n- 只提炼事实、地点、价格区间、交通方式和体验建议，并重新组织为原创内容。\n- 3 天路线为编辑重组的参考框架，不复刻任何单一博主行程顺序。\n- 图片部分只提供原创卡通演示图脚本和 AI 绘图 prompt。',
        '',
    ])


def render_research(date: str, c: dict[str, str], t: dict[str, str]) -> str:
    return '\n\n'.join([
        f'# 资料搜集与攻略要点｜{c["name"]}｜{t["name"]}',
        '## 公开资料', f'- 官方旅游页面：{c["official_url"]}\n- 开放旅行指南/补充资料：{c["guide_url"]}',
        '## 搜索趋势信号', f'- 城市池命中：{c["name"]}，适合做稳定型目的地内容。\n- 热点池命中：{t["name"]}，内容角度为「{t["angle"]}」。\n- 趋势判断来自本地 topics.csv 热点池；如接入实时搜索工具，发布前应补充搜索日期、平台和关键词。',
        '## 平台参考与当地人推荐关键词', '\n'.join('- ' + x for x in source_strategy()), '\n'.join('- 检索词：' + x for x in local_keywords(c, t)),
        '## 攻略要点', '\n'.join(f'- {k}：{v}' for k, v in guide(c, t).items()),
        '## 3 天路线提炼', '\n'.join('- ' + x for x in route(c, t)),
        '## 发布前事实核验', '- 核对景点开放时间、票价和预约规则。\n- 核对公共交通末班车、机场线和节假日班次。\n- 核对餐厅、商店、展览等营业状态，不把未核验内容写成确定事实。\n- 价格只写区间或提示复核，不编造精确价格。',
        '## 版权边界', '- 只提炼事实、地点、价格区间、交通方式和体验建议。\n- 不复制博主原文、图片、截图、路线图或独特表达。\n- 不把单个平台、单个账号、单条视频里的推荐直接当成最终结论。\n- 3 天路线为编辑重组，不照搬任何单一来源的完整顺序。',
        f'- 生成日期：{date}', '',
    ])


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument('--date', default=today()); p.add_argument('--city'); p.add_argument('--topic'); args = p.parse_args()
    brief = ensure_brief(args.date, args.city, args.topic)
    city_slug, topic_slug = selected(brief.read_text(encoding='utf-8'))
    cities = {x['slug']: x for x in read_csv('cities.csv')}; topics = {x['slug']: x for x in read_csv('topics.csv')}
    c, t, out = cities[city_slug], topics[topic_slug], brief.parent
    (out / 'research.md').write_text(render_research(args.date, c, t), encoding='utf-8')
    (out / 'post.md').write_text(render_post(args.date, c, t), encoding='utf-8')
    print(out / 'post.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
