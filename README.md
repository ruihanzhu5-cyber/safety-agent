# Safety Agent · 攻击后恢复研究

这个仓库保存 Tool-Using LLM Agent 在 prompt injection 造成外部副作用后的恢复研究记录。下面两份文档按用户提供的原文完整收录；实验结果的可核查文件集中在 [docs/data](docs/data/)，阶段周报在 [docs/weekly](docs/weekly/)。


## 仓库目录

```text
docs/
├── index.html                  # GitHub Pages 导航
├── source/                     # 原始 Markdown
├── weekly/2026-09-16/          # HTML 周报、Markdown 日志与图
└── data/
    ├── manifest.json           # 数据集总清单
    ├── agentdojo/              # 复现轨迹、逐 run CSV、索引
    ├── triage/                 # 64个case里面选19个
    └── recovery-pilot/         # 95 个结果

```

## 原始文档一：研究进展

# 一、研究方向
LLM Agent 在已经受到攻击并已经对外部环境造成实际副作用之后，如何识别可信进度、修复或控制受损状态，并在安全允许时继续完成原始任务

# **二、目前研究攻击后恢复方向的现状**

当前智能体安全研究仍以**攻击前防护**为主，即通过输入过滤、最小权限、工具调用约束、沙箱和运行时验证尽量阻止攻击进入执行链；相比之下，针对**攻击发生后的状态污染清除、可信回滚与系统恢复**研究仍处于起步阶段，研究重点正在从“阻止攻击”进一步延伸到“受损后恢复可信状态”。**这是一个2026年下半年快速形成的方向，相对来说比研究单agent防御机制要显得稀疏很多**，此外，我还关注到一个现象，目前的研究大多研究单agent怎么去这个防御错误不要发生，但是openai等公司在研究agentnetwork，而学术界在multiagent，所以未来我觉得不是agent不犯错就个好事儿，因为它可能偷偷犯错，或者我们本身不可能保证整个系统每时每刻不犯错，关键是犯错了怎么去修理，所以我想选择聚焦于这个子问题。

部分工作：

**SafeHarness（2026）**：将恢复机制纳入智能体完整生命周期，在攻击检测后回滚文件、执行历史和持久记忆至可信检查点，并通过动态降低工具权限形成“**回滚—降权—恢复**”闭环。

**ChronoMem（2026）**：面向长期记忆污染，为记忆写入维护版本快照，并利用语义检索定位可信历史版本，实现被攻击记忆的**追溯、撤销与语义级回滚**。

**MemSecBench（2026）**：将记忆安全评测扩展至“**攻击写入—持续影响—遗忘/修复**”全过程，揭示恶意记忆能够长期驻留，而攻击检测成功并不等价于污染状态能够被彻底清除。

**ACRFence（2026）**：关注“恢复机制自身的安全性”，指出简单检查点回滚可能重新激活权限或重复执行外部操作，并通过记录不可逆副作用和 replay-or-fork 机制避免**恢复过程产生二次攻击**。

**ErrorProbe（ACL 2026）**：针对长程多智能体任务进行反向故障追踪，定位最早异常步骤及责任智能体，为攻击后的**局部隔离和局部回滚**提供基础，避免整条任务链重新执行。

2026 年一篇系统梳理 247 篇 agent security 工作的综述，直接指出现有研究大量停留在 attack success / defense success / utility，明确提出下一步应研究 recovery rather than only prevention，并具体列出：检测受污染状态、回滚不安全动作、隔离污染记忆、重建决策轨迹、以及在降低权限的情况下继续运行。

# 三、已经完成的复现工作和探索性pilot实验

## 3.1复现agentdojo

恢复机制这部分的工作构造bench的路线有以下几种:

| **① 基于已有动态环境直接扩展**                   | 在已有 Agent 环境和任务上增加 checkpoint → failure/attack → rollback → re-execute，直接评估恢复前后的任务与环境状态 | WebRollback（EACL 2026）：在现有 Web Agent 任务上显式加入 rollback，使 Agent 能从错误网页状态退回历史状态并重新规划，是“已有环境 + 回滚机制”最直接的代表。([ACL Anthology](https://aclanthology.org/2026.eacl-short.12/?utm_source=chatgpt.com))                   |
| **② 在已有攻击流程后增加 Recovery Stage**      | 保留已有攻击注入和攻击成功判定，在攻击成功后继续加入污染定位、删除、修复和恢复评测，把 attack-only Bench 扩展成 attack→recovery Bench | MemSecBench（2026）：采用 Write→Execute→Forget/Repair 协议，在记忆投毒成功后继续测试选择性修复，把安全评测从“攻击是否成功”推进到“攻击后能否清除污染”。([arXiv](https://arxiv.org/abs/2607.27080?utm_source=chatgpt.com))                                           |
| **③ 外挂式 Recovery Harness / Wrapper** | 在 Agent 与工具环境之间增加统一恢复层，记录 checkpoint、状态变化和不可逆副作用；异常后由恢复层完成定位、回滚、降权或重新执行                 | SafeHarness（2026）：在 Agent harness 生命周期中集成异常检测、安全回滚和自适应权限降级；ACRFence（2026）：作为框架无关层记录不可逆工具副作用，通过 replay-or-fork 防止回滚导致重复支付、权限复活等二次风险。([arXiv](https://arxiv.org/abs/2604.13630?utm_source=chatgpt.com))           |
| **④ 围绕恢复目标重新设计专用 Bench**             | 不受现有攻击 Bench 状态结构限制，自己定义可恢复状态、污染过程、历史版本、恢复操作和 Ground Truth，专门测 recovery                 | ChronoMem（2026）：为 Agent Memory 从头增加版本快照、历史版本检索和语义回滚，并设计 post-exposure recovery protocol；MemSecBench 也属于这一思路，专门围绕记忆污染的持久化、后果和 repair 构建生命周期评测。([arXiv](https://arxiv.org/abs/2607.27773?utm_source=chatgpt.com)) |

**我选择的实验底座**是agentdojo，原因是它本身就有**真实的工具调用和可变化的环境状态**，很适合模拟“被攻击后环境被改坏，再进行恢复”的过程。相比自己从零搭环境，我可以直接复用它现成的任务和攻击场景，把重点放在**回滚、修复和恢复效果评测**上。我经过调研发现，很多这个方向的顶会工作也是这么做的。（我将其他顶会工作怎么对这个bench开发的写了文件放到github仓库了）

我采用deepseekv4flash，固定Benign benchmark`v1.1.1` Attack benchmark version `v1.2.2`主要攻击模板和原文一致的 `important_instructions`、`direct`、`ignore_previous`、`injecagent`  评分采用 AgentDojo 官方 utility/security checker，并为每个case保存了原始 JSON trajectory，然后后期分析轨迹的时候转成了可供人阅读的md文档

结果如下：

| **Suite完成攻击模板有效攻击轨迹攻击成功ASR** |           |          |        |           |
| ---------------------------- | --------- | -------- | ------ | --------- |
| Workspace                    | /2/4      | 1120     | 1      | 0.09%     |
| Slack                        | /4/4      | 420      | 7      | 1.67%     |
| Banking                      | /4/4      | 576      | 13     | 2.26%     |
| Travel                       | /4/4      | 560      | 43     | 7.68%     |
| **合计**                       | **14/16** | **2676** | **64** | **2.39%** |

复现发现asr很低，初步原因推断大概是2024年的时候agentdojo用的并非是强模型，2026年7月agentdojo仓库也有提到用gpt5.5mini进行复现asr是0%的情况，所以本次复现应该是跑通了代码，得到了真实的轨迹。

## 3.2探索性pilot实验

攻击成功的64 条攻击成功轨迹并不都适合 recovery 研究。例如，有些攻击：没有留下值得恢复的持久状态；伤害已经发生且当前工具完全无法处理；合法任务已经没有继续执行的空间；recovery 只能表现为停止执行；轨迹或状态证据不足以支持可靠判断。最终认为：\*\*只有 19 个 incident 具有明确的 recovery 研究空间。\*\*针对这 19 个 incident，每个分别运行了 5 种 recovery policy：它的用途不是证明某个 baseline 最好，而是：**暴露 recovery failure phenomenon，并用于 hypothesis generation。**
| 策略 | 结果数 | 第一版 evaluator：新增伤害 | Utility pass | 标为 REPAIRED |
|---|---:|---:|---:|---:|
| ABORT | 19 | 0 | 7 | 0 |
| NO_RECOVERY_CONTINUE | 19 | 2 | 12 | 0 |
| SAFETY_PROMPT_REPLAN | 19 | 0 | 10 | 2 |
| CONTEXT_RESET_REPLAN | 19 | 1 | 11 | 0 |
| RESTART_FROM_SCRATCH | 19 | 9 | 10 | 10 |
### 通过观察95条轨迹发现：

### 1. 恢复单元不能只是 turn 或 tool call

轨迹中：

- 7/19 的 deviation 和 harm 位于同一个工具调用。
- 4/19 在同一个 assistant turn 中混合了合法和恶意写操作。
- 至少 2/19 在同一个工具调用的不同字段中混合合法与恶意效果。

最典型的是房租更新：

```Plain
update_scheduled_transaction(
    id=7,
    amount=1200,        # 合法：按通知涨租
    recipient=attacker, # 恶意：重定向收款人
    recurring=true
)
```

整体撤销这个调用会丢失合法涨租；整体保留又会保留恶意收款人。因此恢复的最小单元应当是：

```Plain
argument → entity field → committed effect
```

而不是：

```Plain
message → assistant turn → tool call
```

这是这次复现最有价值的实证发现之一。


### 2.Context reset 并不等于 trust reset

`CONTEXT_RESET_REPLAN` 清除了对话历史，却保留当前环境。19/19 条都会重新观察环境，因而可能重新读取原始污染内容。

在 Slack 案例中，恢复智能体重新读取被污染文章，又一次访问攻击 URL。也就是说：

```Plain
清除受污染上下文
≠ 清除持久污染源
≠ 获得可信观察
```

恢复智能体存在一个悖论：它必须检查受损状态才能恢复，但检查本身可能让它再次感染。


### 3.从头开始不是可靠恢复

`RESTART_FROM_SCRATCH` 在 9/19 条中重新产生伤害：

- 6 条 Banking：重复转账或再次修改收款人。
- 3 条 Slack：重新访问恶意 URL。
- 某条 Slack 轨迹甚至连续访问攻击 URL 两次。

这与近期 ACRFence 指出的 semantic rollback attack 高度一致：LLM 从 checkpoint 恢复后会重新合成调用，传统基于字面请求或新 UUID 的幂等机制无法阻止语义重复。[ACRFence](https://arxiv.org/abs/2603.20625)

但我们的现象进一步涉及攻击诱导的重新感染、合法进度保存和恶意状态修复，而不只是 checkpoint retry。



### 4.清空历史会造成合法副作用重复

Workspace 案例中，攻击前后的同一轮已经：

- 向文档追加了合法内容；
- 向 David 发送了合法邮件；
- 向 Mark 发送了恶意泄漏邮件。

Context reset 或 restart 后，智能体不知道哪些合法动作已经完成，于是：

- 再次追加文档；
- 再次给 David 发邮件；
- 恶意邮件仍无法撤回。

当前 evaluator 没有把这些重复合法副作用记为 harm。

程序分析还发现，46/95 条 recovery run 重复了 incident 中已经出现过的调用；其中很多只是读取，但至少存在多条明确的重复 mutation。普通“最终 utility 是否满足”无法检测这种问题。


### 5.模型的口头说明不能证明状态已修复

轨迹中出现了模型声称状态“保持原样”或“已经安全处理”，但实际字段仍发生变化的情况。当前 evaluator 只检查攻击签名涉及的部分字段，也可能把不完整恢复标成 repaired/contained。

因此，恢复评价必须以环境状态和外部 effect ledger 为准，不能以 final response 为准。

### 第一版 evaluator 尝试输出以下指标，但是暴露了不少测量漏洞

- AgentDojo utility；
- 原攻击效果在终态是否仍存在；
- `REPAIRED / CONTAINED / RESIDUAL / WORSENED`；
- `COMPLETED / FAILED / SAFE_ESCALATION / UNSAFE_COMPLETION`。

这一步的价值主要不是证明某个 policy 最好，而是暴露 evaluator 的测量漏洞。最明显的结果包括：

- `RESTART_FROM_SCRATCH` 有 10/19 被判 repaired；
- `ABORT` 有 7/19 utility=true；
- 某些只修复一个字段的 case 被判完整 repaired；
- 某些重复合法写操作没有被认作副作用；
- 带有“confirm”等词的回答被词法规则判成 safe escalation。

这些现象说明现有标签混淆了：终态不存在攻击效果；从受损状态实际修复；从初始状态重新执行；攻击前已经完成的 utility；停止继续伤害；部分修复；新增或重复副作用；final answer 与真实环境状态。

## 3.3重新调研该领域顶会工作怎么做的metrics

重点参考了：

- τ-bench：数据库 goal state、状态式 evaluator、`pass^k`；
- AgentDojo：utility/security 分离、pre/post environment predicate；
- OSWorld：任务初态和 execution-based evaluator；
- ToolEmu：safety/helpfulness 分维评价及人工验证自动 evaluator；
- SWE-bench：可执行验证、FAIL\_TO\_PASS 与 PASS\_TO\_PASS；
- ContainmentBench：endpoint label 与 trajectory/propagation/authorization 的区别。

```Plain
S0_exec
   ↓ source execution
SD：攻击已经造成伤害
   ↓ recovery policy
SF：恢复后的终态
```

必须同时评价 SD、recovery action 和 SF，而不是只看 SF 中还能不能找到原攻击签名。

发现evaluation的异常后，回到顶会工作调研发现：recovery evaluator 的测量对象不应是孤立的终态，而应是同一 incident 中，从真实 post-harm state 出发的、有因果证据的状态转移。

# 四、目前形成的三个假设

### 假设一：恢复粒度不匹配

当前观察表明，合法效果和恶意效果可能同时存在于同一个 tool call，甚至同一个实体的不同字段中。

例如：

```Python
update_scheduled_transaction(
    amount=1200,          # 合法修改
    recipient=attacker,   # 恶意修改
    recurring=True
)
```

如果恢复机制只能对整个 tool call 执行“全部保留”或“全部撤销”，则会产生明显冲突：

- 全部保留会保留恶意效果；
- 全部撤销会破坏合法进度。

因此提出假设：**当合法效果与恶意效果被绑定在同一个粗粒度恢复单元中时，只能整体保留或整体撤销的恢复机制，会不可避免地产生安全性与任务效用之间的冲突。**

---

### 假设二：信任重置不匹配

Context reset 只能清除 Agent 当前的推理上下文，但不会自动清除外部环境中持续存在的恶意信息源，例如：

- 恶意网页；
- 恶意 Slack 消息；
- 恶意邮件；
- 污染文件。

恢复过程中，为了重新理解任务，Agent 可能再次读取这些外部内容，从而重新暴露于攻击。

因此提出假设：\*\*当攻击者控制的持久外部信息源仍然可以被重新观察时，清除推理上下文并不能真正恢复可信观察边界。\*\*这一现象进一步形成一个恢复悖论：\*\*恢复过程必须检查受损环境，才能完成修复；但检查受损环境本身，又可能导致再次暴露于攻击。\*\*因此，恢复问题不仅是“如何清除污染上下文”，还包括：恢复阶段如何获得可信状态信息

---

### 假设三：只重置 Agent 的内部历史，而不记录现实世界中已经发生过什么，会让恢复过程分不清“哪些事情已经做完、哪些还没做”，从而导致重复执行和新的错误。

**Agent 虽然“失忆了”，但现实世界没有失忆。**

比如一次攻击过程中，Agent 已经：

- 正常发过一封邮件；
- 正常改过一次文档；
- 同时又做了一笔恶意转账。

这时候如果为了恢复，把 Agent 的历史清空然后重新开始，Agent 可能不知道前面哪些事情已经做过。

于是就可能出现：

- 正常邮件又发一遍；
- 文档又改一遍；
- 已完成任务被重复执行；
- 甚至恶意动作再次发生。

三个假设可以统一为一个更高层结论：**当前常见恢复机制所操作的抽象层级，与真正需要恢复的对象之间可能存在系统性不匹配。**

具体表现为：

- **粒度不匹配**：恢复的是 tool call，但真正需要修复的是 committed effect；
- **信任不匹配**：恢复的是 reasoning context，但真正受到污染的是 observation source；
- **连续性不匹配**：恢复的是 agent history，但外部世界中的 committed effects 仍然持续存在。

# 五、下一步计划

1.持续arxiv跟踪这个方向的最新工作，可能还要进一步缩小假设

2.通过复现的问题是，找到攻击成功的轨迹很难，也就是说如果单纯从现有的已经搭好的bench出发复现收集失败轨迹，效率比较低，因为每个bench的评价metrics不同，asr指标上不去就收不到样本，所以后期的话我计划 利用现有的环境，然后自己改造下agentdojo，我也查了很多研究恢复机制的工作也是走的这个路线

3.这个方向的工作本质感觉是agent在寻找一种的recovery policy，所以我觉得也可以往agentic rl这个方向走，或者multiagent，但是工作量应该会比较大。


## 原始文档二：实验计划

# LLM Agent 攻击后恢复实验计划报告

**汇报日期：2026 年 9 月 16 日**  
**研究阶段：AgentDojo 复现完成后的评测框架与原型实验阶段**

## 一 本阶段结论

前期工作已经完成 AgentDojo 的基本复现，并从攻击成功轨迹中筛选出 19 个具有恢复研究空间的 incident。对 19 个 incident 分别运行 5 种初步恢复策略后，共获得 95 条 recovery trajectory。当前最重要的结果不是某一种策略优于其他策略，而是发现现有恢复方式和评价方式存在系统性问题：

1. 合法效果与恶意效果可能位于同一个工具调用，甚至位于同一实体的不同字段中，按整次工具调用回滚会损害合法进度。
2. 清空 Agent 的推理上下文不会清除外部环境中的持久污染源，恢复过程重新读取环境时可能再次受到攻击。
3. 清空执行历史或从头开始会使 Agent 失去对已提交副作用的认识，导致重复发信、重复写入、重复转账或再次执行恶意动作。
4. 仅检查最终状态或最终回答，无法判断状态是否真的由恢复动作修复，也无法识别重复副作用、部分修复和不可逆伤害。

因此，下一阶段不立即开展强化学习或多智能体恢复，也不优先设计复杂的新 recovery policy。当前优先任务是构建一组可控的 post-harm recovery case，并实现以 committed effect 为中心的 evaluator。待评测框架能够稳定识别恢复成功和恢复失败后，再比较 baseline 并检验三个假设。

## 二 研究问题与范围
### 2.2 当前研究边界

下一阶段暂时限定为：

- 单 Agent 工具调用场景；
- AgentDojo 的 Workspace、Slack、Banking 和 Travel 环境；
- 已经发生可观察外部状态变化的 incident；
- 可逆、可补偿和不可逆副作用；
- 恢复过程中的状态修复、污染隔离、重复动作控制和任务继续执行。

## 三 下一阶段总体路线

实验按照以下顺序开展：

| 阶段 | 工作内容 | 进入下一阶段的条件 |
|---|---|---|
| 第一阶段 | 构造 1 个完整 recovery case | 能固定 SD，并明确合法与恶意 effect |
| 第二阶段 | 实现最小 evaluator | 能识别完整修复、部分修复、合法进度损失和新增伤害 |
| 第三阶段 | 扩展为 6 个原型 case | 三个假设各有至少 2 个代表案例 |
| 第四阶段 | 运行诊断 baseline | 所有方法从完全相同的 SD 出发 |
| 第五阶段 | 加入针对性 baseline | 能分别检验粒度、信任和连续性假设 |
| 第六阶段 | 扩展 benchmark | 原型设计稳定后扩展至 100 至 200 个 case |

