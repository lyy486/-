"""
AI 分析模块 — 深度分析项目内容和用户价值
"""

import os
import re
import json as _json
from typing import Optional

DOMAIN_RULES = {
    "AI/机器学习": {
        "keywords": ["ai", "llm", "gpt", "machine-learning", "deep-learning", "neural",
                      "transformer", "nlp", "computer-vision", "stable-diffusion", "rag",
                      "embedding", "vector", "agent", "langchain", "llama", "mistral",
                      "fine-tune", "inference", "tokenizer", "attention", "diffusion",
                      "mcp", "context", "reasoning", "chatbot", "copilot"],
        "value": "AI/LLM 工具或框架，可用于构建智能应用、微调模型或集成 AI 能力",
    },
    "前端开发": {
        "keywords": ["react", "vue", "angular", "svelte", "next", "nuxt", "tailwind",
                      "css", "component", "ui", "frontend", "web", "browser",
                      "typescript", "javascript", "jsx", "wasm", "html", "canvas"],
        "value": "前端框架/组件库，可提升 UI 开发效率和用户体验",
    },
    "后端开发": {
        "keywords": ["api", "server", "backend", "database", "sql", "graphql", "rest",
                      "microservice", "queue", "cache", "redis", "postgres", "mysql",
                      "mongodb", "orm", "migration", "auth", "jwt", "oauth", "grpc"],
        "value": "后端框架/中间件，可优化服务架构和数据管理",
    },
    "DevOps/基础设施": {
        "keywords": ["docker", "kubernetes", "k8s", "ci", "cd", "terraform", "ansible",
                      "monitoring", "logging", "prometheus", "grafana", "helm", "aws",
                      "cloud", "serverless", "infrastructure", "proxy", "gateway",
                      "deploy", "pipeline", "orchestration", "vpn", "dns", "tunnel",
                      "censorship", "firewall", "networking"],
        "value": "DevOps/基础设施/网络工具，可简化部署运维、提升系统可靠性",
    },
    "CLI/开发工具": {
        "keywords": ["cli", "tool", "vscode", "editor", "plugin", "extension", "lint",
                      "format", "debug", "test", "git", "terminal", "shell", "compiler",
                      "build", "bundler", "vite", "esbuild", "webpack", "package",
                      "sdk", "library", "framework", "rust", "golang", "zig"],
        "value": "开发工具/SDK，可直接提升日常编码效率",
    },
    "安全/隐私": {
        "keywords": ["security", "privacy", "encrypt", "auth", "vulnerability",
                      "firewall", "ssl", "tls", "crypto", "blockchain", "zero-trust",
                      "osint", "dossier", "investigation", "recon", "pentest",
                      "forensics", "cybersecurity", "information-gathering"],
        "value": "安全/调查工具，可增强系统安全或用于信息收集分析",
    },
    "数据科学": {
        "keywords": ["data", "analytics", "visualization", "pandas", "numpy", "spark",
                      "etl", "pipeline", "dashboard", "bi", "statistics", "big-data",
                      "dataframe", "csv", "parquet", "warehouse"],
        "value": "数据处理/分析工具，可提升数据工程和 BI 能力",
    },
}


def _synthesize_what(repo: dict) -> str:
    """综合 description + README 摘要 + topics 推断项目是什么"""
    desc = repo.get("description", "").strip()
    readme = repo.get("readme_summary", "").strip()
    topics = repo.get("topics", [])
    lang = repo.get("language", "")

    # 描述够长且有意义就用它
    if desc and len(desc) >= 30 and not desc.startswith("http"):
        return desc

    # 从 README 摘要找第一句有意义的话
    if readme:
        sentences = re.split(r'[。.!！?；;\n]', readme)
        for s in sentences:
            s = s.strip()
            if len(s) >= 20 and not s.startswith("http") and not s.startswith("!["):
                return s[:150]

    # 描述太短但有 readme：拼在一起
    if desc and readme:
        combined = f"{desc}。{readme[:100]}"
        return combined[:150]

    # 只有 topics：根据标签推断
    if topics:
        return f"这是一个 {'/'.join(topics[:4])} 相关的 {lang} 项目"

    return f"{lang} 项目（暂无详细描述）" if lang else "暂无详细描述"


def rule_based_analyze(repo: dict, interests: list[str]) -> str:
    # 领域匹配：只用 description + topics + language
    text = " ".join([
        repo.get("description", ""),
        repo.get("language", ""),
        " ".join(repo.get("topics", [])),
    ]).lower()

    matched_domains = []
    for domain, rules in DOMAIN_RULES.items():
        for kw in rules["keywords"]:
            if kw in text:
                matched_domains.append(domain)
                break

    # 综合推断项目是什么
    what = _synthesize_what(repo)
    parts = [f"📌 **这是什么：** {what}"]

    if matched_domains:
        parts.append(f"🏷️ **领域：** {'、'.join(matched_domains[:3])}")
        # 不同领域给不同价值描述
        value = DOMAIN_RULES[matched_domains[0]]["value"]
        if len(matched_domains) >= 2:
            second_value = DOMAIN_RULES[matched_domains[1]]["value"]
            parts.append(f"💡 **价值：** {value}；{second_value}")
        else:
            parts.append(f"💡 **价值：** {value}")
    else:
        parts.append("💡 **价值：** 新兴项目，建议关注后续发展")

    user_hits = [d for d in matched_domains if any(
        interest.strip() in d for interest in interests
    )]
    if user_hits:
        parts.append(f"🎯 **与你相关：** 匹配你的兴趣领域「{'、'.join(user_hits)}」，建议深入了解")

    return "\n".join(parts)


def _get_ai_client() -> Optional[str]:
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OLLAMA_BASE_URL"):
        return "ollama"
    return None


def _format_repos_for_ai(repos: list[dict]) -> str:
    lines = []
    for i, r in enumerate(repos, 1):
        readme = r.get("readme_summary", "")
        readme_preview = readme[:200] if readme else "无"
        lines.append(
            f"{i}. **{r['full_name']}**\n"
            f"   描述：{r.get('description', '暂无')}\n"
            f"   README 摘要：{readme_preview}\n"
            f"   语言：{r.get('language', 'Unknown')} | "
            f"总星标：{r.get('total_stars', 0):,} | "
            f"今日新增：{r.get('stars_today', 0):,}\n"
            f"   Topics：{', '.join(r.get('topics', []))}\n"
            f"   许可证：{r.get('license', 'N/A')} | "
            f"创建于：{r.get('created_at', 'N/A')}\n"
            f"   URL：{r['url']}"
        )
    return "\n\n".join(lines)


def _call_ai(backend: str, system_prompt: str, user_prompt: str) -> str:
    if backend == "deepseek":
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return resp.choices[0].message.content

    elif backend == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return resp.choices[0].message.content

    elif backend == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        resp = client.messages.create(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=4096,
        )
        return resp.content[0].text

    elif backend == "ollama":
        from openai import OpenAI
        client = OpenAI(
            base_url=f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/v1",
            api_key="ollama",
        )
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return resp.choices[0].message.content

    raise ValueError(f"Unknown AI backend: {backend}")


def ai_analyze(repos: list[dict], interests: list[str]) -> list[dict]:
    backend = _get_ai_client()
    if not backend:
        for r in repos:
            r["ai_analysis"] = rule_based_analyze(r, interests)
        return repos

    repos_text = _format_repos_for_ai(repos)
    interest_text = "、".join(interests) if interests else "不限领域"

    system_prompt = """你是资深技术分析师。对每个项目给出分析，每条包含4项（用中文，60-100字）：

1. 📌 这是什么：简洁说清楚项目是做什么的
2. 🏷️ 领域：所属技术领域
3. 💡 对用户的价值：它能帮用户解决什么问题、提升什么能力
4. 🎯 关注程度：🔥强烈关注 / ⭐值得关注 / 💡了解一下

直接返回 JSON：[
  {"full_name": "owner/repo", "analysis": "📌 ...\n🏷️ ...\n💡 ...\n🎯 ..."},
  ...
]"""

    user_prompt = f"""用户兴趣领域：{interest_text}

今日 GitHub 星标增长最快项目（含 README 摘要）：

{repos_text}

请逐一分析。"""

    try:
        result = _call_ai(backend, system_prompt, user_prompt)
        analyses = _json.loads(result)
        analysis_map = {a["full_name"]: a["analysis"] for a in analyses}
        for r in repos:
            r["ai_analysis"] = analysis_map.get(
                r["full_name"],
                rule_based_analyze(r, interests)
            )
    except Exception:
        for r in repos:
            r["ai_analysis"] = rule_based_analyze(r, interests)

    return repos
