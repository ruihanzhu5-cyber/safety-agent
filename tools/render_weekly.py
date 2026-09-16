from pathlib import Path
from markdown_it import MarkdownIt

root = Path(__file__).resolve().parents[1]
week = root / "docs" / "weekly" / "2026-09-16"
source = week / "report.md"
target = week / "index.html"
md = MarkdownIt("commonmark", {"html": False}).enable("table")
tokens = md.parse(source.read_text(encoding="utf-8"))
section = 0
for token in tokens:
    if token.type == "heading_open" and token.tag == "h2":
        section += 1
        token.attrSet("id", f"section-{section}")
body = md.renderer.render(tokens, md.options, {})
nav = "".join(f'<a href="#section-{i}">{label}</a>' for i, label in enumerate([
    "Research Question", "What I Did", "Experimental Evidence",
    "Current Hypotheses", "Evaluator", "Next Step", "导师讨论", "证据边界"
], 1))
page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Tool-Using LLM Agent 攻击后恢复科研周报，2026-09-16">
<title>Weekly Research Report · 2026-09-16</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="masthead">
  <div class="wrap">
    <div class="eyebrow">WEEKLY RESEARCH REPORT · 2026-09-16</div>
    <h1>攻击后 Tool-Using Agent 的状态恢复</h1>
    <p class="dek">从 AgentDojo 复现与 95 条 recovery trajectory，走向效果级恢复评测。</p>
    <div class="metrics" aria-label="本阶段实验规模">
      <div><strong>2,676</strong><span>有效攻击轨迹</span></div>
      <div><strong>19</strong><span>确认外部伤害 incident</span></div>
      <div><strong>95</strong><span>恢复轨迹</span></div>
    </div>
  </div>
</header>
<nav class="toc wrap" aria-label="页面目录">{nav}</nav>
<main class="wrap report">{body}</main>
<footer class="wrap footer">本页展示阶段结论；原始 trajectory 与环境快照可由<a href="../../data/README.md">实验数据目录</a>核对。<br><a href="report.md">阅读 Markdown 研究日志</a></footer>
</body>
</html>"""
target.write_text(page, encoding="utf-8")
print(target)
