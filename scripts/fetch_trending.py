"""
GitHub Trending 数据获取模块
支持 Trending 页面 + API 补充 + README 摘要提取
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


def fetch_trending_page() -> list[dict]:
    """从 GitHub Trending 页面抓取当日项目（两种解析策略）"""
    resp = SESSION.get(TRENDING_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    repos = _parse_trending_v1(soup)
    if len(repos) < 3:
        repos = _parse_trending_v2(soup)

    return repos[:15]


def _parse_trending_v1(soup: BeautifulSoup) -> list[dict]:
    """标准解析：article.Box-row"""
    repos = []
    articles = soup.find_all("article", class_="Box-row")
    for article in articles:
        repo = _extract_repo_from_article(article)
        if repo:
            repos.append(repo)
    return repos


def _parse_trending_v2(soup: BeautifulSoup) -> list[dict]:
    """备用解析：h2.h3 > a"""
    repos = []
    for h2 in soup.find_all("h2", class_="h3"):
        a_tag = h2.find("a")
        if not a_tag:
            continue
        href = a_tag.get("href", "").strip()
        parts = href.strip("/").split("/")
        if len(parts) < 2:
            continue
        full_name = f"{parts[0]}/{parts[1]}"

        parent = h2.find_parent("article") or h2.find_parent("div")
        desc_p = parent.find("p") if parent else None
        description = desc_p.text.strip() if desc_p else ""

        lang_span = parent.find("span", itemprop="programmingLanguage") if parent else None
        language_name = lang_span.text.strip() if lang_span else "Unknown"

        stars_elem = parent.find("a", href=re.compile(r"/stargazers")) if parent else None
        total_stars = _parse_stars(stars_elem.text if stars_elem else "0")

        today_elem = parent.find("span", string=re.compile(r"star")) if parent else None
        if not today_elem and parent:
            today_elem = parent.find("span", class_="float-sm-right")
        today_stars = _parse_stars(today_elem.text if today_elem else "0")

        repos.append({
            "full_name": full_name,
            "owner": parts[0],
            "name": parts[1],
            "description": description,
            "language": language_name,
            "total_stars": total_stars,
            "stars_today_str": f"+{today_stars:,}",
            "stars_today": today_stars,
            "url": f"https://github.com/{full_name}",
        })

    repos.sort(key=lambda r: r.get("stars_today", 0), reverse=True)
    return repos[:10]


def _extract_repo_from_article(article) -> Optional[dict]:
    h2 = article.find("h2", class_="h3")
    if not h2:
        return None
    a_tag = h2.find("a")
    if not a_tag:
        return None

    href = a_tag.get("href", "").strip()
    parts = href.strip("/").split("/")
    if len(parts) < 2:
        return None
    full_name = f"{parts[0]}/{parts[1]}"

    desc_p = article.find("p", class_="col-9")
    description = desc_p.text.strip() if desc_p else ""

    lang_span = article.find("span", itemprop="programmingLanguage")
    language_name = lang_span.text.strip() if lang_span else "Unknown"

    stars_elem = article.find("a", href=re.compile(r"/stargazers"))
    total_stars = _parse_stars(stars_elem.text if stars_elem else "0")

    today_elem = article.find("span", class_="float-sm-right")
    today_text = today_elem.text.strip() if today_elem else ""
    today_stars = _parse_stars(today_text)

    forks_elem = article.find("a", href=re.compile(r"/forks"))
    forks = _parse_stars(forks_elem.text if forks_elem else "0")

    return {
        "full_name": full_name,
        "owner": parts[0],
        "name": parts[1],
        "description": description,
        "language": language_name,
        "total_stars": total_stars,
        "stars_today_str": f"+{today_stars:,}" if today_stars > 0 else today_text,
        "stars_today": today_stars,
        "forks": forks,
        "url": f"https://github.com/{full_name}",
    }


def _parse_stars(text: str) -> int:
    text = text.strip().lower().replace(",", "").replace("stars", "").replace("star", "").strip()
    if not text:
        return 0
    try:
        if text.endswith("k"):
            return int(float(text[:-1]) * 1000)
        return int(text)
    except (ValueError, TypeError):
        return 0


def enrich_with_api(repos: list[dict]) -> list[dict]:
    """通过 GitHub API 补充 topics、描述、README 摘要"""
    for repo in repos:
        try:
            info = _get_repo_info(repo["full_name"])
            if not info:
                continue

            repo["topics"] = info.get("topics", [])
            # 优先用 API 返回的描述（更完整）
            api_desc = info.get("description", "")
            if api_desc and api_desc != repo.get("description", ""):
                repo["description"] = api_desc
            repo["created_at"] = info.get("created_at", "")[:10]
            repo["updated_at"] = info.get("updated_at", "")[:10]
            repo["homepage"] = info.get("homepage", "")
            repo["license"] = (info.get("license") or {}).get("spdx_id", "")
            repo["total_stars"] = info.get("stargazers_count", repo["total_stars"])
            repo["forks"] = info.get("forks_count", repo.get("forks", 0))
            repo["open_issues"] = info.get("open_issues_count", 0)
            repo["language"] = info.get("language") or repo.get("language", "Unknown")

            # 读 README 摘要
            readme_text = _fetch_readme(repo["full_name"])
            if readme_text:
                repo["readme_summary"] = readme_text[:500]
        except Exception:
            continue

    repos.sort(key=lambda r: r.get("stars_today", 0), reverse=True)
    return repos


def _get_repo_info(full_name: str) -> Optional[dict]:
    url = f"{GITHUB_API}/repos/{full_name}"
    resp = SESSION.get(url, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return None


def _fetch_readme(full_name: str) -> Optional[str]:
    """尝试获取 README 前 500 字用于摘要"""
    try:
        url = f"{GITHUB_API}/repos/{full_name}/readme"
        resp = SESSION.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        download_url = data.get("download_url", "")
        if not download_url:
            return None
        readme_resp = SESSION.get(download_url, timeout=10)
        if readme_resp.status_code == 200:
            text = readme_resp.text[:1000]
            # 去图片语法（必须先做）
            text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
            # 去 HTML 标签
            text = re.sub(r'<[^>]+>', '', text)
            # 去 markdown 标记
            text = re.sub(r'#{1,6}\s+', '', text)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            text = re.sub(r'[*_~`>|]', '', text)
            text = re.sub(r'!\[[^\]]*\]', '', text)
            text = re.sub(r'\n{2,}', '\n', text).strip()
            return text[:500]
    except Exception:
        pass
    return None


# ── 缓存 ─────────────────────────────────────────────────────────

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "stars_history.json")


def load_star_history() -> dict[str, int]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_star_history(repos: list[dict]):
    os.makedirs(CACHE_DIR, exist_ok=True)
    history = {}
    for r in repos:
        history[r["full_name"]] = r.get("total_stars", 0)
    with open(CACHE_FILE, "w") as f:
        json.dump(history, f, indent=2)


def calculate_daily_growth(repos: list[dict]) -> list[dict]:
    history = load_star_history()
    for r in repos:
        prev = history.get(r["full_name"])
        current = r.get("total_stars", 0)
        if prev and prev > 0 and current > prev:
            growth = current - prev
            if growth > 0:
                r["stars_today"] = growth
                r["stars_today_str"] = f"+{growth:,}"
        r["total_stars_str"] = f"{r.get('total_stars', 0):,}"
    repos.sort(key=lambda r: r.get("stars_today", 0), reverse=True)
    return repos
