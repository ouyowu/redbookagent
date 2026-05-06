#!/usr/bin/env python3
"""Package one output directory and email it as a zip attachment."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import smtplib
import zipfile
from email.message import EmailMessage
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANGKOK = dt.timezone(dt.timedelta(hours=7))


def today_prefix() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone(BANGKOK).strftime("%Y-%m-%d")


def resolve_output_dir(value: str | None) -> Path:
    if value:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        return path

    matches = sorted((ROOT / "outputs").glob(f"{today_prefix()}-*"))
    if not matches:
        raise SystemExit("今天还没有找到可发送的 outputs 目录")
    return matches[-1]


def read_city_and_theme(output_dir: Path) -> tuple[str, str]:
    brief_path = output_dir / "brief.md"
    if not brief_path.exists():
        return output_dir.name, "旅行内容包"
    brief = brief_path.read_text(encoding="utf-8")
    city = re.search(r"^- 城市：(.+)$", brief, re.MULTILINE)
    theme = re.search(r"^- 内容主题：(.+)$", brief, re.MULTILINE)
    city_name = city.group(1).strip() if city else output_dir.name
    theme_name = theme.group(1).strip() if theme else "旅行内容包"
    return city_name, theme_name


def build_zip(output_dir: Path) -> Path:
    zip_path = output_dir / f"{output_dir.name}-email-pack.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if not path.is_file() or path == zip_path:
                continue
            archive.write(path, path.relative_to(output_dir))
    return zip_path


def build_body(city_name: str, theme_name: str, output_dir: Path) -> str:
    return "\n".join(
        [
            "你好，",
            "",
            "今天的「扬仔游星球」自动内容包已经生成完成，现已附上压缩包。",
            "",
            f"- 城市：{city_name}",
            f"- 主题：{theme_name}",
            f"- 输出目录：{output_dir.name}",
            "",
            "压缩包内通常包含：",
            "- 攻略正文",
            "- 标题与标签",
            "- 图片脚本与生图提示词",
            "- 研究与核验文件",
            "- 如已开启生图，还会包含 PNG 图片",
            "",
            "这封邮件由 GitHub Actions 自动发送。",
            "",
            "扬仔游星球内容 Agent",
        ]
    )


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"缺少环境变量：{name}")
    return value


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    attachment: Path,
) -> None:
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(
        attachment.read_bytes(),
        maintype="application",
        subtype="zip",
        filename=attachment.name,
    )

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_username, smtp_password)
        server.send_message(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Zip one output folder and email it.")
    parser.add_argument("--output-dir", help="Output directory to package and send.")
    parser.add_argument("--to", help="Recipient email. Defaults to TRAVEL_AGENT_EMAIL_TO.")
    args = parser.parse_args()

    output_dir = resolve_output_dir(args.output_dir)
    if not output_dir.exists():
        raise SystemExit(f"输出目录不存在：{output_dir}")

    smtp_host = os.getenv("TRAVEL_AGENT_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("TRAVEL_AGENT_SMTP_PORT", "465"))
    smtp_username = require_env("TRAVEL_AGENT_SMTP_USERNAME")
    smtp_password = require_env("TRAVEL_AGENT_SMTP_PASSWORD")
    from_email = os.getenv("TRAVEL_AGENT_EMAIL_FROM", smtp_username)
    to_email = args.to or require_env("TRAVEL_AGENT_EMAIL_TO")

    city_name, theme_name = read_city_and_theme(output_dir)
    zip_path = build_zip(output_dir)
    subject = f"扬仔游星球｜{city_name}｜自动内容包"
    body = build_body(city_name, theme_name, output_dir)
    send_email(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        attachment=zip_path,
    )
    print(zip_path)
    print(to_email)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
