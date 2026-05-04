# 扬仔游星球 Travel Agent

这个仓库的核心项目在 `travel-agent/`。它把公开旅行资料整理成原创小红书图文攻略，按城市池和热点池每天自动生成选题、文案、卡通图脚本和版权/事实检查。

## 项目结构

```text
travel-agent/
├─ cities.csv
├─ topics.csv
├─ prompts/
│  ├─ planner.md
│  ├─ researcher.md
│  ├─ writer.md
│  ├─ designer.md
│  └─ compliance.md
├─ outputs/
│  └─ 2026-05-04-tokyo/
│     ├─ brief.md
│     ├─ research.md
│     ├─ post.md
│     ├─ slides.json
│     ├─ image_prompts.json
│     └─ image_prompts.md
├─ scripts/
│  ├─ pick_topic.py
│  ├─ generate_post.py
│  └─ export_assets.py
└─ .github/workflows/daily.yml
```

仓库根部也有 `.github/workflows/daily.yml`，用于让 GitHub Actions 真正识别并每天运行 `travel-agent/` 里的脚本。

## 本地运行

```bash
cd travel-agent
python3 scripts/pick_topic.py
python3 scripts/generate_post.py
python3 scripts/export_assets.py
```

生成图片需要配置 `OPENAI_API_KEY`，会读取输出目录里的 `image_prompts.json`：

```bash
cd travel-agent
python3 scripts/generate_images.py --output-dir outputs/2026-05-04-tokyo
```

指定日期、城市和主题：

```bash
cd travel-agent
python3 scripts/pick_topic.py --date 2026-05-04 --city tokyo --topic first-time
python3 scripts/generate_post.py --date 2026-05-04
python3 scripts/export_assets.py --date 2026-05-04
```

## 自动运行

GitHub Actions 每天早上 9 点运行：

- cron: `0 2 * * *`
- GitHub Actions 使用 UTC，`02:00 UTC` 对应 Asia/Bangkok / 北京时间 `09:00`
- 运行环境：Python `3.11`
- 依赖安装：`openai pandas requests beautifulsoup4`
- 密钥：可读取 GitHub Secret `OPENAI_API_KEY`

每日自动流程：

1. 从 `cities.csv` 选择城市。
2. 结合 `topics.csv` 生成当天选题。
3. 整理公开资料、搜索趋势信号和攻略要点，输出 `research.md`。
4. 提炼成“食住行游购娱”结构。
5. 生成小红书标题、正文、标签。
6. 生成 6-9 张卡通演示图脚本。
7. 做版权检查：不复制原文、不用原图、不照搬路线图。
8. 输出到 `travel-agent/outputs/日期-城市/` 文件夹。
9. 可选自动开 PR，人工审核后发布。

默认模式会用 `travel-agent <agent@example.com>` 提交并推送每日产物。若希望自动开 PR，请在 GitHub 仓库变量中设置：

```text
TRAVEL_AGENT_OPEN_PR=true
```

默认只生成文案和图片 prompt，不自动调用图片生成接口。若希望每天同时生成图片，请设置仓库变量：

```text
TRAVEL_AGENT_GENERATE_IMAGES=true
```

## 内容原则

- 不复制博主原文、图片、截图、路线图或独特表达。
- 只提炼公开资料中的事实、地点、价格区间、交通方式和体验建议。
- 所有内容必须重写、归纳、交叉验证，并标注信息来源链接。
- 图片只输出原创卡通图脚本和绘图 prompt，不使用真实照片或真实地图路线。
