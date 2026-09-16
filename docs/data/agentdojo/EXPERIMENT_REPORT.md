# AgentDojo DeepSeek 复现实验报告

报告日期：2026-09-16  
实验模型：`deepseek-v4-flash`  
实验范围：AgentDojo 原生 benign 与 prompt-injection benchmark  
排除范围：已放弃的机制验证实验、Gemini 未完成实验、非 AgentDojo 自定义恢复实验

## 1. 实验目的

本次复现用于确认 DeepSeek 模型在 AgentDojo 四个 suite 中的任务完成能力，以及面对不同间接提示注入模板时的 utility 和 security 表现。所有成功与失败均读取 AgentDojo 官方 checker 输出，不用人工判断替代官方评分。

本报告回答三个问题：

1. DeepSeek 在无攻击条件下能完成多少正常任务？
2. 在不同攻击模板下，模型能否继续完成用户任务，攻击目标又有多少次真正实现？
3. 对照 AgentDojo 原论文的主要实验矩阵，目前已经复现到什么程度，还缺什么？

## 2. 统计口径

- `utility=true`：AgentDojo utility checker 判定用户任务完成。
- `utility=false`：checker 正常运行，但用户任务未完成。
- `utility=NA`：API、超时、解析、轨迹或评分基础设施异常；不计入 utility failure。
- 攻击成功：`injection_goal_achieved=true`，以 AgentDojo 官方 security checker 为准。
- ASR：攻击成功数除以有效攻击 episode 数。
- 断线续跑结果按 `(user_task, injection_task)` 去重，保留该组合最后一次有效结果。
- Benign 使用 benchmark `v1.1.1`；最新攻击实验使用 `v1.2.2`，因此二者不能视为严格同版本配对对照。

## 3. 实验配置

| 配置项 | 设置 |
|---|---|
| Provider / model | DeepSeek / `deepseek-v4-flash` |
| Benign benchmark version | `v1.1.1` |
| Attack benchmark version | `v1.2.2` |
| Defense | `none` |
| 并发 | `max_workers=1` |
| Benign attack | `none` |
| 主要攻击模板 | `important_instructions`、`direct`、`ignore_previous`、`injecagent` |
| 额外攻击模板 | Banking `system_message` |
| 评分 | AgentDojo 官方 utility/security checker |
| 轨迹 | 每个 episode 保存原始 JSON trajectory |

## 4. Benign 实验结果

| Suite | 总任务 | 有效 | Infra error | Utility pass | Utility fail | Benign utility |
|---|---:|---:|---:|---:|---:|---:|
| Workspace | 40 | 40 | 0 | 37 | 3 | 92.50% |
| Slack | 21 | 21 | 0 | 20 | 1 | 95.24% |
| Banking | 16 | 16 | 0 | 16 | 0 | 100.00% |
| Travel | 20 | 18 | 2 | 13 | 5 | 72.22% |
| **合计** | **97** | **95** | **2** | **86** | **9** | **90.53%** |

Travel 的两条异常按基础设施错误处理，没有计入 utility failure。整体 benign utility 为 `86/95=90.53%`。

## 5. Prompt-injection 实验结果

###  | Injection goal success | ASR |
|---|---:|---:|---:|---:|---:|
| important_instructions | 105 | 80 | 255.1 Workspace

Workspace v1.2.2 包含40个 user tasks 和14个 injection tasks，每个完整攻击模板包含560个组合。

| Attack | 有效轨迹 | Utility pass | Utility fail | Injection goal success | ASR |
|---|---:|---:|---:|---:|---:|
| direct / TODO | 560 | 559 | 1 | 1 | 0.18% |
| injecagent | 560 | 555 | 5 | 0 | 0.00% |
| **合计** | **1120** | **1114** | **6** | **1** | **0.09%** |

`direct` 首次运行中途停止，续跑后合并得到560个不重复且全部有效的组合。Workspace 的 `important_instructions` 与 `ignore_previous` 尚未运行。

### 5.2 Slack

Slack 包含21个 user tasks 和5个 injection tasks，每种攻击包含105个组合。

| Attack | 有效轨迹 | Utility pass | Utility fail | 0 | 0.00% |
| direct / TODO | 105 | 87 | 18 | 5 | 4.76% |
| ignore_previous | 105 | 81 | 24 | 1 | 0.95% |
| injecagent | 105 | 83 | 22 | 1 | 0.95% |
| **合计** | **420** | **331** | **89** | **7** | **1.67%** |

另有一批 benchmark v1.1.1 的 Slack `ignore_previous` 105条历史实验。它与上表新版结果重复，不计入主结果。

### 5.3 Banking

Banking 包含16个 user tasks 和9个 injection tasks，每种攻击包含144个组合。

| Attack | 有效轨迹 | Utility pass | Utility fail | Injection goal success | ASR |
|---|---:|---:|---:|---:|---:|
| important_instructions | 144 | 130 | 14 | 0 | 0.00% |
| direct / TODO | 144 | 130 | 14 | 13 | 9.03% |
| ignore_previous | 144 | 130 | 14 | 0 | 0.00% |
| injecagent | 144 | 102 | 42 | 0 | 0.00% |
| **论文四种攻击合计** | **576** | **492** | **84** | **13** | **2.26%** |
| system_message（额外） | 144 | 130 | 14 | 3 | 2.08% |
| **全部 Banking 攻击** | **720** | **622** | **98** | **16** | **2.22%** |

`system_message` 是额外仓库配置，不属于原论文四种主要攻击模板，因此单独列出。

### 5.4 Travel

Travel 包含20个 user tasks 和7个 injection tasks，每种攻击包含140个组合。

| Attack | 有效轨迹 | Utility pass | Utility fail | Injection goal success | ASR |
|---|---:|---:|---:|---:|---:|
| important_instructions | 140 | 105 | 35 | 13 | 9.29% |
| direct / TODO | 140 | 107 | 33 | 6 | 4.29% |
| ignore_previous | 140 | 104 | 36 | 10 | 7.14% |
| injecagent | 140 | 106 | 34 | 14 | 10.00% |
| **合计** | **560** | **422** | **138** | **43** | **7.68%** |

## 6. 总体汇总

### 6.1 四个 suite 攻击结果总表

| Suite | Attack | 有效轨迹 | Utility pass | Utility fail | Injection goal success | ASR |
|---|---|---:|---:|---:|---:|---:|
| Workspace | important_instructions | 未运行 | — | — | — | — |
| Workspace | direct / TODO | 560 | 559 | 1 | 1 | 0.18% |
| Workspace | ignore_previous | 未运行 | — | — | — | — |
| Workspace | injecagent | 560 | 555 | 5 | 0 | 0.00% |
| Slack | important_instructions | 105 | 80 | 25 | 0 | 0.00% |
| Slack | direct / TODO | 105 | 87 | 18 | 5 | 4.76% |
| Slack | ignore_previous | 105 | 81 | 24 | 1 | 0.95% |
| Slack | injecagent | 105 | 83 | 22 | 1 | 0.95% |
| Banking | important_instructions | 144 | 130 | 14 | 0 | 0.00% |
| Banking | direct / TODO | 144 | 130 | 14 | 13 | 9.03% |
| Banking | ignore_previous | 144 | 130 | 14 | 0 | 0.00% |
| Banking | injecagent | 144 | 102 | 42 | 0 | 0.00% |
| Travel | important_instructions | 140 | 105 | 35 | 13 | 9.29% |
| Travel | direct / TODO | 140 | 107 | 33 | 6 | 4.29% |
| Travel | ignore_previous | 140 | 104 | 36 | 10 | 7.14% |
| Travel | injecagent | 140 | 106 | 34 | 14 | 10.00% |
| Banking（额外） | system_message | 144 | 130 | 14 | 3 | 2.08% |

为了保证横向比较公平，下面的 suite 汇总只统计原论文四种主要攻击中已经完成的组合，不包含 Banking 的额外 `system_message`：

| Suite | 已完成攻击模板 | 有效攻击轨迹 | Injection goal success | 汇总 ASR |
|---|---:|---:|---:|---:|
| Workspace | 2/4 | 1120 | 1 | 0.09% |
| Slack | 4/4 | 420 | 7 | 1.67% |
| Banking | 4/4 | 576 | 13 | 2.26% |
| Travel | 4/4 | 560 | 43 | 7.68% |
| **已完成组合合计** | **14/16** | **2676** | **64** | **2.39%** |

Workspace 只完成两种攻击，因此其汇总 ASR 与另外三个完整 suite 不能直接作为同等覆盖范围的比较。

### 6.2 全部实验数量

| 类别 | 已尝试 episode | 有效 episode | Utility pass | Utility fail | Injection success |
|---|---:|---:|---:|---:|---:|
| Benign | 97 | 95 | 86 | 9 | 不适用 |
| Workspace attacks | 1120 | 1120 | 1114 | 6 | 1 |
| Slack attacks | 420 | 420 | 331 | 89 | 7 |
| Banking attacks（含额外 system_message） | 720 | 720 | 622 | 98 | 16 |
| Travel attacks | 560 | 560 | 422 | 138 | 43 |
| **主实验合计** | **2917** | **2915** | **2575** | **340** | **67** |

主结果中共有2917次 episode 尝试，其中2915条有效、2条为 Travel benign 基础设施错误。攻击实验共有2820条，67次实现 injection goal，总体 ASR 为 `67/2820=2.38%`。这个总体 ASR混合了不同 suite、攻击模板以及额外 `system_message`，只能作为数据盘点，不能替代分 suite、分攻击比较。

若把旧版 Slack `ignore_previous` 的105条历史重复实验也计入实际 API 运行次数，则一共运行过3022次 AgentDojo episode。

## 7. 对照原论文的完成度

| 原论文实验组成 | Workspace | Slack | Banking | Travel | 状态 |
|---|---|---|---|---|---|
| Benign | 完成 | 完成 | 完成 | 已尝试，2条infra error | 基本完成，但版本较旧 |
| important_instructions | 未跑 | 完成 | 完成 | 完成 | 缺 Workspace 560条 |
| direct / TODO | 完成 | 完成 | 完成 | 完成 | 完成 |
| ignore_previous | 未跑 | 完成 | 完成 | 完成 | 缺 Workspace 560条 |
| injecagent | 完成 | 完成 | 完成 | 完成 | 完成 |
| 防御方法对比 | 未跑 | 未跑 | 未跑 | 未跑 | 未复现 |
| 攻击者知识消融 | 未跑 | 未跑 | 未跑 | 未跑 | 未复现 |
| DoS / untargeted attacks | 未跑 | 未跑 | 未跑 | 未跑 | 未复现 |

按照当前 v1.2.2 的任务规模，补齐论文四种攻击模板还需要运行 Workspace 的 `important_instructions` 和 `ignore_previous`，共 `560×2=1120` 条。

## 8. 主要观察

### 观察1：DeepSeek 的 benign utility 较高，但 suite 差异明显

在有效 benign 任务中，整体通过率为90.53%。Banking 达到100%，Workspace 和 Slack 超过92%，Travel 只有72.22%。这说明模型表现不能只用一个跨 suite 平均值描述；Travel 是当前最明显的正常任务能力短板。

### 观察2：攻击模板效果高度依赖 suite

Travel 四种攻击的 ASR 为4.29%至10.00%，明显高于 Slack；Workspace 已完成的两种攻击合计只有1/1120成功。攻击效果并不是某个模板本身的固定属性，而是受到任务、工具、注入位置及模型能否到达注入内容共同影响。

### 观察3：direct / TODO 是 Banking 中最有效的主要攻击

Banking `direct` 的 ASR 为9.03%，其余三种论文攻击为0%。模板更长或更像显式命令，并不必然更有效。需要结合成功轨迹检查模型读到了什么、首次偏离发生在哪次工具输出之后，以及最后是否真正执行了攻击目标。

### 观察4：低 ASR 不等于没有明显行为退化

例如 Banking `injecagent` 没有实现任何 injection goal，但 utility failure 达42/144；Slack 和 Travel 也存在大量“攻击未成功、用户任务也失败”的轨迹。因此应同时报告 utility under attack 和 ASR，不能只根据ASR判断攻击或防御效果。

### 观察5：当前 benign 与 attack 不是严格版本配对

Benign 来自v1.1.1，攻击来自v1.2.2。任务定义、checker或工具实现的版本变化可能影响数值。因此，本报告能够说明已运行轨迹中的现象，但不能把 benign 与 attacked 差值全部归因于攻击。

## 9. 局限性

1. 所有正式配置只运行一次，没有多随机种子，无法估计模型采样方差。
2. Benign 与攻击实验版本不一致。
3. Workspace 只完成四种主要攻击中的两种。
4. 尚未复现原论文的防御、攻击者知识消融和DoS实验。
5. 总体ASR会受各suite组合数不同影响，应优先阅读分suite结果。
6. 报告忠实保留官方checker结果；已发现的个别checker语义争议不能被人工改分替代。

## 10. 建议的下一步

1. 用v1.2.2、同一DeepSeek配置重跑97条benign，建立严格同版本基线。
2. 补齐Workspace的`important_instructions`和`ignore_previous`共1120条。
3. 对每个suite分别计算 utility下降、ASR及二者同时发生的比例，避免只看总体平均。
4. 优先人工审阅所有67条攻击成功轨迹，以及攻击未成功但utility失败的轨迹样本。
5. 在基础矩阵完整后，再选择一种原论文防御做同模型、同版本配对实验。

## 11. 结果文件入口

- Benign Workspace：`runs/repro_deepseek_workspace/20260828T103746Z/`
- Benign Slack：`runs/repro_deepseek_slack/20260828T115535Z/`
- Benign Banking：`runs/repro_deepseek_banking_benign/20260908T122604Z/`
- Benign Travel：`runs/repro_deepseek_travel_benign/20260908T122610Z/`
- Workspace attacks：`runs/repro_deepseek_workspace_all_attacks_v0135/workspace_v122_direct_injecagent_20260912T150608Z/`
- Slack attacks：`runs/repro_deepseek_slack_all_attacks_v0135/slack4_v0135_20260910T054558Z/`
- Banking attacks：`runs/repro_deepseek_banking_v0122_144/` 与 `runs/repro_deepseek_banking_all_attacks_v0122/`
- Travel attacks：`runs/repro_deepseek_travel_all_attacks_v0135/travel4_v0135_20260910T071508Z/`
- 旧版Slack重复实验：`runs/repro_deepseek_slack_ignore_previous/20260908T151138Z/`

以上路径中的原始JSON trajectory为证据源，CSV summary仅用于汇总，不能替代原始轨迹。
