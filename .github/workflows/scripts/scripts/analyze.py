"""
AI 分析模块 — 支持多个 AI 后端，无 API Key 时自动降级为规则分析
"""

import os
import json as _json
from typing import Optional

DOMAIN_RULES = {
    "AI/机器学习": {
        "keywords": ["ai", "llm", "gpt", "machine-learning", "deep-learning", "neural",
                      "transformer", "nlp", "computer-vision", "stable-diffusion", "rag",
                      "embedding", "vector", "agent", "langchain", "llama", "mistral",
                      "fine-tune", "inference", "tokenizer", "attention", "diffusion"],
        "value": "可以帮助你构建 AI 应用、训练模型或集成 LLM 能力到你的项目中",
    },
    "前端开发": {
        "keywords": ["react", "vue", "angular", "svelte", "next", "nuxt", "tailwind",
                      "css", "component", "ui", "frontend", "web", "browser", "dom",
                      "typescript", "javascript", "jsx", "wasm"],
        "value": "可以提升前端开发效率、改善 UI/UX 或学习现代前端架构",
    },
    "后端开发": {
        "keywords": ["api", "server", "backend", "database", "sql", "graphql", "rest",
                      "microservice", "queue", "cache", "redis", "postgres", "mysql",
                      "mongodb", "orm", "migration", "auth", "jwt", "oauth"],
        "value": "可以优化后端架构、提升 API 性能或简化数据管理",
    },
    "DevOps/基础设施": {
        "keywords": ["docker", "kubernetes", "k8s", "ci", "cd", "terraform", "ansible",
                      "monitoring", "logging", "prometheus", "grafana", "helm", "aws",
                      "cloud", "serverless", "infrastructure", "proxy", "gateway"],
        "value": "可以简化部署流程、提升系统可靠性或降低运维成本",
    },
    "开发工具": {
        "keywords": ["cli", "tool", "vscode", "editor", "plugin", "extension", "lint",
                      "format", "debug", "test", "git", "terminal", "shell", "compiler",
                      "build", "bundler", "vite", "esbuild", "webpack", "package"],
        "value": "可以提升开发效率、改善代码质量或简化工作流程",
    },
    "安全/隐私": {
        "keywords": ["security", "privacy", "encrypt", "auth", "vulnerability",
                      "firewall", "ssl", "tls", "crypto", "blockchain"],
        "value": "可以增强系统安全性、保护用户隐私或学习安全最佳实践",
    },
    "数据科学": {
        "keywords": ["data", "analytics", "visualization", "pandas", "numpy", "spark",
                      "etl", "pipeline", "dashboard", "bi", "statistics", "big-data"],
        "value": "可以提升数据分析能力、优化数据管道或构建更好的数据产品",
    },
}


def rule_based_analyze(repo: dict, interests: list[str]) -> str:
    text = " ".join([
        repo.get("description", ""),
        repo.get("language", ""),
        " ".join(repo.get("topics", [])),
        repo.get("full_name", ""),
    ]).lower()

    matched_domains = []
    for domain, rules in DOMAIN_RULES.items():
        for kw in rules["keywords"]:
            if kw in text:
                matched_domains.append(domain)
                break

    if not matched_domains:
        return "这是一个新兴项目，建议关注其后续发展，评估是否与你的技术栈匹配"

    user_interest_hits = [d for d in matched_domains if any(
        interest.strip() in d for interest in interests
    )]

    parts = []
    for domain in matched_domains[:2]:
        parts.append(DOMAIN_RULES[domain]["value"])

    if user_interest_hits:
        parts.append(f"⚠️ 该项目与你的兴趣领域「{'、'.join(user_interest_hits)}」高度相关，建议重点关注")

    return "；".join(parts)


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
        lines.append(
            f"{i}. **{r['full_name']}**\n"
            f"   描述：{r.get('description', '暂无')}\n"
            f"   语言：{r.get('language', 'Unknown')} | "
            f"总星标：{r.get('total_stars', 0):,} | "
            f"今日新增：{r.get('stars_today', 0):,}\n"
            f"   Topics：{', '.join(r.get('topics', []))}\n"
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

    system_prompt = """你是一个资深技术分析师，专注于评估开源项目对开发者的实用价值。
请对每个项目给出简洁的分析（50-80字），包含：
1. 项目的核心价值（解决了什么问题）
2. 对用户可能的具体帮助（结合用户兴趣领域）
3. 建议关注程度（🔥强烈关注 / ⭐值得关注 / 💡了解一下）

直接返回 JSON 数组，格式：[{"full_name": "owner/repo", "analysis": "分析内容"}, ...]
不要包含任何其他文字。"""

    user_prompt = f"""用户的兴趣领域：{interest_text}

以下是今日 GitHub 星标增长最快的项目：

{repos_text}

请分析每个项目对用户的价值。"""

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
