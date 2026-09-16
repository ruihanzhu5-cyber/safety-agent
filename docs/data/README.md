# 实验数据目录

本目录是本地实验输出的**复制快照**。`tools/archive_experiments.py` 只读取源目录，把文件逐字节复制到这里，并生成包含 SHA-256 的索引；原始实验目录和 trajectory 未被修改。

| 数据组 | 文件 / 口径 | 入口 |
|---|---:|---|
| AgentDojo 攻击复现 | 2820 条有效 JSON；其中论文四模板 2676 条，额外 Banking `system_message` 144 条 | [attack-index.json](agentdojo/attack-index.json) |
| AgentDojo benign | 97 条原始 JSON；其中 95 条有效、2 条 Travel 基础设施异常 | [benign-index.json](agentdojo/benign-index.json) |
| 历史 Slack 攻击批次 | 105 条 v1.1.1 `ignore_previous` 原始 JSON，单列保存，不计入主结果 | [历史索引](agentdojo/historical/slack-ignore-previous-v1.1.1/index.json) |
| 事故筛选 | 64 条 checker 阳性中 19 条确认有害外部副作用 | [incident_triage.jsonl](triage/incident_triage.jsonl) |
| Recovery pilot | 19 incident × 5 policy = 95 个结果 JSON 与 95 个终态快照 | [run-index.json](recovery-pilot/run-index.json) |
| 总清单 | 数据规模、分组和索引路径 | [manifest.json](manifest.json) |

## 目录结构

```text
data/
├── manifest.json
├── agentdojo/
│   ├── attack-index.json
│   ├── attack-trajectories/<suite>/<attack>/<user_task>/<injection_task>.json
│   ├── benign-index.json
│   ├── benign-trajectories/<suite>/<user_task>.json
│   ├── historical/slack-ignore-previous-v1.1.1/
│   ├── run-results/                 # 逐 run 原始 CSV，保留续跑记录
│   ├── version_manifest.json
│   └── EXPERIMENT_REPORT.md
├── triage/
│   ├── incident_triage.jsonl
│   ├── incident_triage_summary.md
│   └── recovery_opportunity_characterization.jsonl
└── recovery-pilot/
    ├── run-index.json
    ├── summaries/                 # Stage-3C 原始汇总与失败案例 JSON
    └── runs/<incident>/<policy>/
        ├── c3_run_001.json
        └── c3_run_001.final_environment.json
```

## 使用与口径

1. 从 `manifest.json` 进入对应索引。索引里的 `path`、`result_path` 和 `final_environment_path` 均相对于本目录，可用于定位文件；哈希用于核对复制件。
2. `run-results/` 保留原始逐 run CSV，包括中断后的续跑。规范化 `attack-index.json` 按 `(suite, attack, user_task, injection_task)` 保留最后一个有效结果，避免重复计数。
3. 旧版 Slack 的 105 条为历史重复实验，基准版本不同；它们与 2820 条当前攻击复现分开保存。当前攻击 2820 + benign 97 + 历史 Slack 105，正好对应此前实验记录中约 3022 次 API episode。
4. `checker_positive` 是 AgentDojo 官方 security checker 输出；它**不等于**经工具调用和环境变化确认的外部伤害。后者见 `triage/`。
5. Recovery 原始结果中的某些路径字段记录了实验机器上的历史位置；在本仓库中查找对应快照请使用 `run-index.json` 的相对路径。请根据环境快照、工具轨迹和 evaluator 输出解释结果，不以 final response 判定修复成功。
6. 这些文件包含原始 benchmark 内容和攻击 payload。两份研究原文另存于 `docs/source/`，同时完整收录在根目录 README。

本地更新命令（参数填写你自己的实验目录）：

```powershell
python tools/archive_experiments.py --agentdojo-root <agentdojo目录> --recovery-root <agentdojo_recovery目录>
python tools/render_weekly.py
```

当前目录是 2026-09-16 的一次实验快照；新实验应新增带日期的目录和独立清单，避免覆盖这批可复查结果。

