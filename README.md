# GitHub 星标增长日报

每天自动抓取 GitHub Trending TOP 10，分析每个项目对你的价值，推送到飞书。

## 功能

- 每日抓取 GitHub Trending TOP 10
- AI 智能分析（支持 DeepSeek / OpenAI / Claude / Ollama）
- 无 AI Key 也能用（规则分析）
- 多渠道推送：邮件 / 飞书 / 钉钉 / 企业微信

## 配置

在 Settings → Secrets and variables → Actions → Secrets 中添加：

| Secret | 说明 |
|--------|------|
| GITHUB_TOKEN | GitHub Token（必填） |
| FEISHU_WEBHOOK | 飞书 Webhook |
| DEEPSEEK_API_KEY | DeepSeek Key（可选） |

## 运行

每天北京时间 9:00 自动运行，或进入 Actions 手动触发。
