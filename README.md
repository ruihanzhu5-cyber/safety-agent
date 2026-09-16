# Safety Agent · Research Reports

本仓库发布工具型 LLM Agent 安全与攻击后恢复研究的阶段性周报。

- [2026-09-16 周报（HTML）](docs/weekly/2026-09-16/index.html)
- [2026-09-16 研究日志（Markdown）](docs/weekly/2026-09-16/report.md)

GitHub Pages 使用 `main` 分支的 `/docs` 目录；`docs/index.html` 指向最新周报。新增周报请放在 `docs/weekly/YYYY-MM-DD/` 下，并更新首页入口。生成 HTML 可运行 `python tools/render_weekly.py`（需要 `markdown-it-py`）。

公开文件只包含脱敏案例摘要、统计和图。原始 attack/recovery trajectory、环境快照和实验凭据保留在本地实验目录，不随网页发布。
