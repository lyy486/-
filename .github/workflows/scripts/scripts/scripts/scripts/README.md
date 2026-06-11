# 📊 GitHub 星标增长日报

每天自动抓取 GitHub Trending 数据，分析星标增长最快的 10 个项目，**告诉你每个项目对你可能有什么帮助**，并通过邮件或 IM 推送给你。

## ✨ 功能

- 🔥 每日抓取 GitHub Trending（daily）TOP 10
- 🤖 **AI 智能分析**每个项目对你的价值（支持 DeepSeek / OpenAI / Claude / Ollama）
- 📧 多渠道推送：**邮件** / 飞书 / 钉钉 / 企业微信
- 📈 历史星标追踪，计算真实日增量
- 🆓 无 AI Key 也能用（自动降级为规则分析）

## 🚀 配置步骤

### 第 1 步：创建 GitHub Token

打开 https://github.com/settings/tokens → 点击 **Generate new token (classic)**：

- Note：填 `daily-report`
- Expiration：选 **No expiration**
- 勾选 `public_repo`
- 点击 **Generate token**，**复制保存**（只显示一次）

### 第 2 步：配置 Secrets

进入仓库 **Settings → Secrets and variables → Actions → Secrets**，添加以下配置：

**必填：**

| Secret | 说明 |
|--------|------|
| `GITHUB_TOKEN` | 第 1 步创建的 Token |

**通知方式（至少选一种）：**

| Secret | 说明 |
|--------|------|
| `SMTP_HOST` | SMTP 服务器（Gmail 填 `smtp.gmail.com`） |
| `SMTP_PORT` | 端口（Gmail 填 `587`） |
| `SMTP_USER` | 你的邮箱 |
| `SMTP_PASSWORD` | SMTP 密码（Gmail 需[应用专用密码](https://support.google.com/accounts/answer/185833)） |
| `REPORT_RECIPIENT` | 接收报告的邮箱 |
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook |
| `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook |
| `WECOM_WEBHOOK` | 企业微信机器人 Webhook |

**AI 分析（可选，不填则规则分析）：**

| Secret | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key（推荐） |
| `OPENAI_API_KEY` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | Claude API Key |
| `OLLAMA_BASE_URL` | Ollama 地址 |

### 第 3 步：设置兴趣领域（可选）

进入 **Settings → Secrets and variables → Actions → Variables**：

| Variable | 值 |
|----------|-----|
| `MY_INTERESTS` | `AI/机器学习,全栈开发,DevOps` |

### 第 4 步：测试

进入 **Actions → 📊 GitHub 星标增长日报 → Run workflow**，手动触发一次。

## ⏰ 自动运行

每天 **北京时间 9:00** 自动运行，报告推送到你配置的渠道。

## 📧 报告样例

- 🥇🥈🥉 排名 + 项目链接
- ⭐ 今日新增 / 总星标
- 🔧 编程语言 / 许可证
- 📝 项目描述 + 🏷️ Topics
- 💡 **AI 分析：对你可能有什么帮助**
