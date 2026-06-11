"""
GitHub 星标增长日报 — 主脚本
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from fetch_trending import (
    fetch_trending_page,
    enrich_with_api,
    calculate_daily_growth,
    save_star_history,
)
from analyze import ai_analyze
from notify import send_report


def build_report(repos: list[dict], interests: list[str]) -> tuple[str, str]:
    today = datetime.now().strftime("%Y年%m月%d日")
    date_iso = datetime.now().strftime("%Y-%m-%d")
    interest_text = "、".join(interests) if interests else "不限领域"

    # ── Markdown ──
    md_lines = [
        f"## 🔥 GitHub 星标增长 TOP 10 — {today}",
        "",
        f"> 🎯 关注领域：**{interest_text}**",
        "",
        "---",
        "",
    ]

    for i, r in enumerate(repos, 1):
        rank_bar = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"  ")
        stars_today = r.get("stars_today", 0)
        total_stars = r.get("total_stars", 0)
        lang = r.get("language", "")
        desc = r.get("description", "")
        analysis = r.get("ai_analysis", "")
        topics = r.get("topics", [])
        topics_str = " · ".join([f"`{t}`" for t in topics[:6]]) if topics else ""
        readme = r.get("readme_summary", "")

        # 增长高亮
        growth_bar = _growth_bar(stars_today)

        md_lines.append(f"### {rank_bar}  [{r['full_name']}]({r['url']})")
        md_lines.append(f"⭐ **+{stars_today:,}** 今日新增 {growth_bar} ｜ {total_stars:,} 总星标")
        if lang:
            md_lines.append(f"🔧 {lang} ｜ 📋 {r.get('license', 'N/A')} ｜ 🕐 创建于 {r.get('created_at', 'N/A')}")
        md_lines.append("")

        if desc:
            md_lines.append(f"> 📝 {desc}")
            md_lines.append("")

        if readme and len(readme) > 30:
            md_lines.append(f"📖 {readme[:200]}...")
            md_lines.append("")

        if topics_str:
            md_lines.append(f"🏷️ {topics_str}")
            md_lines.append("")

        md_lines.append(f"{analysis}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_lines.append(f"📡 数据来源：GitHub Trending · 自动生成于 {date_iso}")

    markdown = "\n".join(md_lines)

    # ── HTML ──
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0d1117; margin: 0; padding: 20px; color: #c9d1d9; }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #238636 0%, #1a7f37 100%); color: #fff; padding: 24px 28px; border-radius: 12px 12px 0 0; }}
  .header h1 {{ margin: 0; font-size: 20px; }}
  .header p {{ margin: 4px 0 0; opacity: 0.85; font-size: 13px; }}
  .card {{ background: #161b22; padding: 18px 24px; border-bottom: 1px solid #21262d; }}
  .card:last-child {{ border-bottom: none; border-radius: 0 0 12px 12px; }}
  .rank {{ color: #58a6ff; font-weight: bold; font-size: 16px; }}
  .repo-link {{ font-size: 17px; font-weight: 600; color: #58a6ff; text-decoration: none; }}
  .growth {{ font-size: 20px; font-weight: bold; color: #3fb950; }}
  .bar {{ color: #f0883e; }}
  .meta {{ margin: 6px 0; font-size: 12px; color: #8b949e; }}
  .desc {{ font-size: 13px; color: #c9d1d9; margin: 8px 0; padding: 10px 14px; background: #1c2128; border-left: 3px solid #58a6ff; border-radius: 0 6px 6px 0; }}
  .readme {{ font-size: 12px; color: #8b949e; margin: 6px 0; padding: 8px 12px; background: #0d1117; border-radius: 6px; }}
  .analysis {{ font-size: 13px; margin: 8px 0; padding: 10px 14px; background: #1a2332; border-left: 3px solid #3fb950; border-radius: 0 6px 6px 0; white-space: pre-line; }}
  .topic {{ display: inline-block; background: #21262d; color: #58a6ff; padding: 2px 7px; border-radius: 10px; font-size: 11px; margin: 2px 3px 2px 0; }}
  .footer {{ padding: 14px 24px; font-size: 11px; color: #484f58; text-align: center; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>🔥 GitHub 星标增长日报</h1>
  <p>{today} · 关注领域：{interest_text}</p>
</div>
""" + "".join([
    f"""<div class="card">
  <span class="rank">#{i}</span>
  <a class="repo-link" href="{r['url']}" target="_blank">{r['full_name']}</a>
  <div style="margin:6px 0"><span class="growth">+{r.get('stars_today', 0):,}</span> <span style="font-size:13px;color:#8b949e">今日新增 {_growth_bar(r.get('stars_today', 0))}</span> ｜ {r.get('total_stars', 0):,} 总星标</div>
  <div class="meta">🔧 {r.get('language', 'Unknown')} ｜ 📋 {r.get('license', 'N/A')} ｜ 🕐 {r.get('created_at', 'N/A')}</div>
  {f'<div class="desc">📝 {r.get("description", "")}</div>' if r.get("description") else ""}
  {f'<div class="readme">📖 {r.get("readme_summary", "")[:200]}...</div>' if r.get("readme_summary", "") and len(r.get("readme_summary", "")) > 30 else ""}
  {f'<div>{"".join([f"<span class=topic>{t}</span>" for t in r.get("topics", [])[:6]])}</div>' if r.get("topics") else ""}
  <div class="analysis">{r.get('ai_analysis', '')}</div>
</div>"""
    for i, r in enumerate(repos, 1)
]) + f"""
<div class="footer">📡 数据来源：GitHub Trending · 自动生成于 {date_iso}</div>
</div>
</body>
</html>"""

    return html, markdown


def _growth_bar(stars: int) -> str:
    if stars >= 2000:
        return "🔥🔥🔥"
    if stars >= 1000:
        return "🔥🔥"
    if stars >= 500:
        return "🔥"
    if stars >= 200:
        return "📈"
    return "⬆️"


def main():
    print("=" * 60)
    print("  GitHub 星标增长日报")
    print("=" * 60)

    print("\n📡 获取 GitHub Trending...")
    repos = fetch_trending_page()
    print(f"  获取到 {len(repos)} 个项目")

    if os.getenv("GITHUB_TOKEN"):
        print("🔍 补充 API 详情 + README 摘要...")
        repos = enrich_with_api(repos)
        print("  详情补充完成")

    repos = calculate_daily_growth(repos)
    save_star_history(repos)

    # 过滤掉今日星标增长为 0 的项目，只保留真正热门的
    repos = [r for r in repos if r.get("stars_today", 0) > 0][:10]

    interests = [s.strip() for s in os.getenv("MY_INTERESTS", "").split(",") if s.strip()]
    print(f"🧠 AI 分析中（兴趣：{interests or '不限'}）...")
    repos = ai_analyze(repos, interests)

    print("\n📊 今日 TOP 10：")
    print("-" * 60)
    for i, r in enumerate(repos, 1):
        bar = _growth_bar(r.get("stars_today", 0))
        print(f"  {i:2}. {r['full_name']:<38s} ⭐+{r.get('stars_today', 0):>7,}  {bar}")

    print("\n📝 生成报告...")
    html, md = build_report(repos, interests)

    print("📤 发送报告...")
    send_report(html, md)
    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
