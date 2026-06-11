"""
通知模块 — 支持邮件、飞书、钉钉、企业微信多渠道发送
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from html.parser import HTMLParser

import requests


def send_report(report_html: str, report_markdown: str):
    sent = False

    if all([
        os.getenv("SMTP_HOST"),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASSWORD"),
        os.getenv("REPORT_RECIPIENT"),
    ]):
        try:
            _send_email(report_html)
            print("邮件发送成功")
            sent = True
        except Exception as e:
            print(f"邮件发送失败: {e}")

    if os.getenv("FEISHU_WEBHOOK"):
        try:
            _send_feishu(report_markdown)
            print("飞书发送成功")
            sent = True
        except Exception as e:
            print(f"飞书发送失败: {e}")

    if os.getenv("DINGTALK_WEBHOOK"):
        try:
            _send_dingtalk(report_markdown)
            print("钉钉发送成功")
            sent = True
        except Exception as e:
            print(f"钉钉发送失败: {e}")

    if os.getenv("WECOM_WEBHOOK"):
        try:
            _send_wecom(report_markdown)
            print("企业微信发送成功")
            sent = True
        except Exception as e:
            print(f"企业微信发送失败: {e}")

    if not sent:
        print("未配置任何通知渠道，报告仅输出到控制台")
        print(report_markdown)

    return sent


class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, d):
        self.text.append(d)


def _send_email(html_content: str):
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    recipient = os.getenv("REPORT_RECIPIENT", "")

    msg = MIMEMultipart("alternative")
    today = datetime.now().strftime("%Y-%m-%d")
    msg["Subject"] = f"GitHub 星标增长日报 — {today}"
    msg["From"] = user
    msg["To"] = recipient

    s = _Stripper()
    s.feed(html_content)
    plain = "".join(s.text)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [recipient], msg.as_string())


def _send_feishu(markdown: str):
    webhook = os.getenv("FEISHU_WEBHOOK", "")
    today = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"content": f"GitHub 星标增长日报 — {today}", "tag": "plain_text"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": markdown[:15000],
                }
            ],
        },
    }

    resp = requests.post(webhook, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") != 0:
        raise RuntimeError(f"Feishu error: {result}")


def _send_dingtalk(markdown: str):
    webhook = os.getenv("DINGTALK_WEBHOOK", "")
    today = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"GitHub 星标增长日报 — {today}",
            "text": markdown[:20000],
        },
    }

    resp = requests.post(webhook, json=payload, timeout=15)
    resp.raise_for_status()


def _send_wecom(markdown: str):
    webhook = os.getenv("WECOM_WEBHOOK", "")
    today = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"# GitHub 星标增长日报 — {today}\n\n{markdown[:4000]}",
        },
    }

    resp = requests.post(webhook, json=payload, timeout=15)
    resp.raise_for_status()
