"""
GitHub Trending 数据获取模块
"""

import re
import os
import json
from typing import Optional

import requests
from bs4 import BeautifulSoup

TRENDING_URL = "https://github.com/trending?since=daily"
GITHUB_API = "https://api.github.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "GitHub-Daily-Report-Bot/1.0",
    "Accept": "application/vnd.github.v3+json",
})

if token := os.getenv("GITHUB_TOKEN"):
    SESSION.headers["Authorization"] = f"Bearer {token}"


def fetch_trending_page(language: str = "") -> list[dict]:
    """从 GitHub Trending 页面抓取当日 top 10 项目"""
    url = TRENDING_URL
    if language:
        url += f"?language={language}"

    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    repos = []
    articles = soup.find_all("article", class_="Box-row")[:10]

    for article in articles:
        h2 = article.find("h2", class_="h3")
        if not h2:
            continue
        a_tag = h2.find("a")
        if not a_tag:
            continue

        href = a_tag.get("href", "").strip()
        parts = href.strip("/").split("/")
        if len(parts) < 2:
            continue
        full_name = f"{parts[0]}/{parts[1]}"

        desc_p = article.find("p", class_="col-9")
        description = desc_p.text.strip() if desc_p else ""

        lang_span = article.find("span", itemprop="programmingLanguage")
        language_name = lang_span.text.strip() if lang_span else "Unknown"

        stars_elem = article.find("a", href=re.compile(r"/stargazers"))
        total_stars = _parse_stars(stars_elem.text if stars_elem else "0")

        today_stars_elem = article.find("span", class_="float-sm-right")
        today_stars = _parse_stars(today_stars_elem.text if today_stars_elem else "0")

        forks_elem = article.find("a", href=re.compile(r"/forks"))
        forks = _parse_stars(forks_elem.text if forks_elem else "0")

        repos.append({
            "full_name": full_name,
            "owner": parts[0],
            "name": parts[1],
            "description": description,
            "language": language_name,
            "total_stars": total_stars,
            "stars_today": today_stars,
            "forks": forks,
            "url": f"https://github.com/{full_name}",
        })

    return repos


def _parse_stars(text: str) -> int:
    """解析星标数字文本"""
    text = text.strip().lower().replace(",", "")
    if not text:
        return 0
    try:
        if text.endswith("k"):
            return int(float(text[:-1]) * 1000)
        return int(text)
    except (ValueError, TypeError):
        return 0


def enrich_with_api(repos: list[dict]) ->
