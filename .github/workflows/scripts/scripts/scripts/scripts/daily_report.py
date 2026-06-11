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

    md_lines = [
        f"## 🔥 GitHub 星标增长 TOP 10 — {today}",
        "",
        f"> 关注领域：**{interest_text}** | 数据来源：GitHub Trending (daily)",
        "",
        "---",
        "",
    ]

    for i, r in enumerate(repos, 1):
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        stars_today = r.get("stars_today", 0)
        total_stars = r.get("total_stars", 0)
        lang = r.get("language", "Unknown")
        desc = r.get("description", "暂无描述")
        analysis = r.get("ai_analysis", "")
        topics = r.get("topics", [])
        topics_str = " ".join([f"`{t}`" for t in topics[:8]]) if topics else ""

        md_lines += [
            f"### {rank_emoji} [{r['full_name']}]({r['url']})",
            f"⭐ **+{stars_today:,}** 今日 | {total_stars:,} 总计 | 🔧 {lang}",
            "",
            f"> {desc}",
            "",
        ]
        if topics_str:
            md_lines.append(f"{topics_str}")
            md_lines.append("")
        md_lines += [
            f"💡 **对你的帮助：** {analysis}",
            "",
            "---",
            "",
        ]

    md_lines += [
        f"*报告由 GitHub Actions 自动生成于 {date_iso}*",
        "",
        "> 💬 如需调整兴趣领域或通知方式，请修改仓库 Settings → Secrets/Variables",
    ]

    markdown = "\n".join(md_lines)

    html_parts = [
        f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub 星标增长日报 — {today}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; margin: 0; padding: 20px; color: #1a1a2e; }}
  .container {{ max-width: 720px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 28px 32px; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 22px; }}
  .header p {{ margin: 0; opacity: 0.85; font-size: 14px; }}
  .card {{ padding: 20px 32px; border-bottom: 1px solid #eee; }}
  .card:last-child {{ border-bottom: none; }}
  .rank {{ display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 50%; background: #667eea; color: #fff; font-weight: bold; font-size: 14px; margin-right: 8px; }}
  .rank-1 {{ background: #f6c343; }}
  .rank-2 {{ background: #a0a0a0; }}
  .rank-3 {{ background: #cd7f32; }}
  .repo-link {{ font-size: 18px; font-weight: 600; color: #0366d6; text-decoration: none; }}
  .repo-link:hover {{ text-decoration: underline; }}
  .meta {{ margin: 8px 0; font-size: 13px; color: #666; }}
  .meta strong {{ color: #e36209; }}
  .desc {{ font-size: 14px; color: #444; margin: 8px 0; padding: 10px 14px; background: #f8f9fa; border-left: 3px solid #667eea; border-radius: 0 6px 6px 0; }}
  .analysis {{ font-size: 14px; color: #2d6a4f; margin: 8px 0; padding: 10px 14px; background: #f0fff4; border-left: 3px solid #2d6a4f; border-radius: 0 6px 6px 0; }}
  .topics {{ margin: 6px 0; }}
  .topic {{ display: inline-block; background: #e8ecf1; color: #555; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin: 2px 4px 2px 0; }}
  .footer {{ padding: 16px 32px; font-size: 12px; color: #999; text-align: center; background: #fafafa; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>🔥 GitHub 星标增长日报</h1>
  <p>{today} · 关注领域：{interest_text}</p>
</div>
"""
    ]

    for i, r in enumerate(repos, 1):
        rank_class = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(i, "")
        stars_today = r.get("stars_today", 0)
        total_stars = r.get("total_stars", 0)
        lang = r.get("language", "Unknown")
        desc = r.get("description", "暂无描述")
        analysis = r.get("ai_analysis", "")
        topics = r.get("topics", [])
        topics_html = "".join([f'<span class="topic">{t}</span>' for t in topics[:8]])

        html_parts.append(f"""
<div class="card">
  <div>
    <span class="rank {rank_class}">{i}</span>
    <a class="repo-link" href="{r['url']}" target="_blank">{r['full_name']}</a>
  </div>
  <div class="meta">
    ⭐ <strong>+{stars_today:,} 今日</strong> &nbsp;|&nbsp;
    {total_stars:,} 总计 &nbsp;|&nbsp;
    🔧 {lang} &nbsp;|&nbsp;
    📋 {r.get('license', 'N/A')}
  </div>
  <div class="desc">📝 {desc}</div>
  {f'<div class="topics">{topics_html}</div>' if topics_html else ''}
  <div class="analysis">💡 <strong>对你的帮助：</strong>{analysis}</div>
</div>
""")

    html_parts.append(f"""
<div class="footer">
  报告由 GitHub Actions 自动生成于 {date_iso} · 数据来源：GitHub Trending
</div>
</div>
</body>
</html>
""")

    html = "\n".join(html_parts)
    return html, markdown


def main():
    print("=" * 60)
    print("🚀 GitHub 星标增长日报生成器")
    print("=" * 60)

    print("\n📡 正在获取 GitHub Trending 数据...")
    repos = fetch_trending_page()
    print(f"   获取到 {len(repos)} 个项目")

    if os.getenv("GITHUB_TOKEN"):
        print("🔍 正在通过 API 补充项目详情...")
        repos = enrich_with_api(repos)
        print("   详情补充完成")

    repos = calculate_daily_growth(repos)
    save_star_history(repos)

    interests = [
        s.strip() for s in os.getenv("MY_INTERESTS", "").split(",") if s.strip()
    ]
    print(f"🧠 正在进行 AI 分析（兴趣领域：{interests or '不限'}）...")
    repos = ai_analyze(repos, interests)

    print("\n📊 今日 TOP 10：")
    print("-" * 60)
    for i, r in enumerate(repos, 1):
        print(f"  {i:2}. {r['full_name']:<40s} ⭐+{r.get('stars_today', 0):>6,}")

    print("\n📝 正在生成报告...")
    html, md = build_report(repos, interests)

    print("📤 正在发送报告...")
    send_report(html, md)

    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
