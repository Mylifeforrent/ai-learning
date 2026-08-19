# 课件：用 doc-agent-loop 看懂 Loop 工程的 10 个设计要素

> 配套项目：[doc-agent-loop](https://github.com/lf-achyutpkl/doc-agent-loop)  
> 理论来源：LangChain [The Art of Loop Engineering](https://www.langchain.com/blog/the-art-of-loop-engineering)  
> 框架参考：自动化代理设计框架（目标 / 触发 / 发现 / 工作空间 / 上下文 / 委托 / 验证 / 预算 / 升级 / 退出）

---

## 0. 本节课要解决什么问题

学员学完应能回答：

1. Loop 工程不是「多写几个 Agent」，而是围绕任务把 **闭环要素设计清楚**。
2. 本项目如何把黑板里的 **10 个要素**落到代码里。
3. 哪些要素是 **完整实现**，哪些是 **教学简化**（知道差距才能做生产）。

---

## 1. 项目一句话定位

这是一个 **文档改进 Agent**：接收「文档要怎么改」的指令，在隔离仓库里改 Markdown，校验通过后写本地 PR 草稿，并能从运行痕迹提出 harness 改进建议。

四层闭环（复习）：

| 层 | 含义 | 本项目入口 |
|---|---|---|
| Loop 1 | Agent 调工具干活 | `create_docs_agent` + `DocsAgentRunner` |
| Loop 2 | 校验失败则重试 | `VerificationLoop` |
| Loop 3 | 外部事件触发 | `POST /events/docs-request` |
| Loop 4 | 从 traces 改进 harness | `docs-loop improve` / `approve` |

> 记忆口诀：**1 干活 → 2 验货 → 3 接单 → 4 进化**  
> 10 个要素是「设计清单」；4 个 Loop 是「运行结构」。要素会散落在不同 Loop 里。

---

## 2. 总览：10 要素 × 本项目对照表

| # | 要素 | 设计问题 | 本项目怎么体现 | 完整度 |
|---|---|---|---|---|
| 1 | 目标 | Loop 要优化什么？ | 最小正确的文档改动 | ★★★ |
| 2 | 触发 | 什么时候运行？ | CLI / HTTP 事件显式触发 | ★★☆ |
| 3 | 发现 | 怎么找到要干的活？ | 请求里的 `instruction` | ★★☆ |
| 4 | 工作空间 | 在哪里安全操作？ | 隔离 clone + 路径封禁 | ★★★ |
| 5 | 上下文 | 有哪些持久化知识？ | `harness.json` + learned rules | ★★★ |
| 6 | 委托 | 谁做什么？ | 写作 Agent vs 校验器/Judge | ★★☆ |
| 7 | 验证 | 怎么判断做对了？ | 确定性检查 + LLM Judge | ★★★ |
| 8 | 预算 | 何时停止？ | `MAX_VERIFICATION_ATTEMPTS` | ★★☆ |
| 9 | 升级 | 何时通知人类？ | Loop 4 人审 approve | ★★☆ |
| 10 | 退出 | 怎么知道完成了？ | 校验通过 → 写 PR 草稿 | ★★★ |

---

## 3. 逐要素讲解（可直接照讲）

### 要素 1：目标（Objective）

**设计问题：** Loop 要优化什么？

**黑板示例：** 「保持 CI 绿色」

**本项目目标：**

> 用最小、正确、范围受控的文档改动，满足用户的文档改进请求。

体现在 `config/harness.json` 的 system prompt：

- 先检查仓库再改
- 只改 Markdown / MDX
- 不编造命令与 API
- diff 要紧贴请求，不做无关清理

**讲师点拨：**  
目标要写成「可验证的优化方向」，而不是「帮忙写点文档」。后面的验证、退出都围绕这个目标设计。

**代码位置：** `config/harness.json`、`agent/factory.py`

---

### 要素 2：触发（Trigger）

**设计问题：** 什么时候运行？

**黑板示例：** 每 10 分钟 / CI 失败事件

**本项目触发方式：**

| 方式 | 命令 / 接口 | 启动的闭环 |
|---|---|---|
| CLI | `docs-loop run "..."` | Loop 1 + 2 |
| HTTP | `POST /events/docs-request` | Loop 3 → 2 → 1 |
| 手动爬山 | `docs-loop improve` | Loop 4（不自动跟单次请求绑死） |

**讲师点拨：**

- 本项目是 **显式触发**，没有 cron、没有监听 CI。
- 生产里可把 Trigger 换成：Slack 频道、Issue 标签、文档过期定时任务等。
- **不要**把 Loop 4 和每次请求绑在一起自动跑——爬山需要多条 traces + 人审。

**代码位置：** `cli.py`、`events/api.py`

---

### 要素 3：发现（Discover）

**设计问题：** 怎么找到要干的活？

**黑板示例：** 读 CI 日志、GitHub Issues

**本项目怎么做：**

活不是 Agent 自己去「捞」的，而是请求载荷直接带上：

```json
{
  "source": "slack",
  "instruction": "Improve the getting-started guide..."
}
```

- `instruction`：要干的活（最少 5 个字符）
- `source` / `event_id` / `requested_by`：来源元数据

Agent 进仓库后，再用工具 **二次发现细节**：

- `list_documentation_files`
- `search_documentation`
- `read_document`

**讲师点拨：**  
「发现」分两层——**任务发现**（谁下达任务）和 **现场发现**（进仓库找文件）。本项目任务发现被简化成 API/CLI 入参；现场发现由工具完成。

**代码位置：** `schemas.py`（`DocsRequest`）、`tools/docs_tools.py`、`scripts/demo_request.json`

---

### 要素 4：工作空间（Workspace）

**设计问题：** Agent 在哪里安全操作？

**黑板示例：** Git Worktree 隔离

**本项目怎么做：**

1. **CLI 模式**：在 `WORKSPACE_PATH`（默认 `sample_repo`）上操作  
2. **事件模式**：每个 run 克隆到 `data/workspaces/<run_id>/`，互不污染  
3. **安全边界**：
   - 只允许 `.md` / `.mdx`
   - 禁止路径穿越
   - 保护 `.git`、`data`、`.env` 等路径

**讲师点拨：**  
没有安全工作空间，Agent 就不是「自动化」，是「自动化事故」。先隔离，再给工具。

**代码位置：** `events/service.py`（`clone_local`）、`repository/local.py`、`repository/git.py`

---

### 要素 5：上下文（Context）

**设计问题：** 有哪些持久化知识？

**黑板示例：** `SKILL.md`、`CLAUDE.md`

**本项目等价物：**

| 知识 | 文件 | 作用 |
|---|---|---|
| 系统提示词 | `config/harness.json` → `system_prompt` | 行为宪法 |
| 权限策略 | `allowed_extensions` / `protected_paths` | 能改什么、不能碰什么 |
| 学到的规则 | `learned_rules` | Loop 4 人审后写入，下次注入 prompt |
| 改进历史 | `history` | 谁批准了什么 |

`create_docs_agent` 会把 `learned_rules` 拼进 system prompt：

```text
Learned rules from reviewed traces:
- ...
```

**讲师点拨：**  
上下文不是聊天窗口里的临时话，而是 **可版本化、可审批、可回放** 的 harness。本项目的 `harness.json` 就是「项目级 SKILL」。

**代码位置：** `config/harness.json`、`config.py`、`agent/factory.py`、`improvement/apply.py`

---

### 要素 6：委托（Delegation）

**设计问题：** 哪个 Agent 做什么？

**黑板示例：** maker-agent vs checker-agent

**本项目角色分工：**

| 角色 | 组件 | 职责 |
|---|---|---|
| Maker | `documentation-improvement-agent` | 读/搜/写文档、看 diff |
| Checker（确定性） | `DeterministicVerifier` | 有无改动、是否只改 docs、链接、占位符等 |
| Checker（语义） | `LLMScopeJudge` | 是否满足请求、范围是否过大 |
| Meta（可选） | `HarnessImprovementAnalyzer` | 分析 traces，提出规则改进 |

注意：Checker **不一定是另一个 Agent**——确定性检查是普通代码；Judge 才是独立模型调用。

**讲师点拨：**  
委托的本质是 **职责隔离**：写的人不能自己说了算。生产里可以升级成两个 Agent；教学项目用「Agent + Verifier」已经足够说明思想。

**代码位置：** `agent/factory.py`、`verification/deterministic.py`、`verification/llm_judge.py`、`improvement/analyzer.py`

---

### 要素 7：验证（Verification）

**设计问题：** 怎么判断做对了？

**黑板示例（思想）：** 测试、检查清单、独立评审

**本项目验证栈：**

1. **确定性检查**（快、可解释、不烧 Token）
   - 是否有改动
   - 是否只改文档
   - `git diff --check`
   - 相对链接是否可解析
   - 是否出现 TODO/TBD/FIXME
2. **LLM Judge**（可选，语义层）
   - 是否满足请求
   - 是否 grounded
   - 是否无关改动过多
3. **失败反馈回灌**
   - `feedback_text()` → 下一轮 `DocsAgentRunner.run(..., feedback)`

**讲师点拨：**  
验证要「分层」：能确定性解决的别交给 LLM；LLM 只做语义与范围判断。这是 Loop 2 的核心。

**代码位置：** `verification/loop.py`、`verification/deterministic.py`、`verification/llm_judge.py`

---

### 要素 8：预算（Budget）

**设计问题：** 何时停止？

**黑板示例：** 最大轮数、Token 上限、时间限制

**本项目预算：**

- 环境变量 `MAX_VERIFICATION_ATTEMPTS`（默认 3，范围 1–10）
- `VerificationLoop` 用 `for attempt_number in range(1, max + 1)` 控制重试
- 用尽仍失败 → `status = "failed_verification"`

尚未做成硬预算（演示简化）：

- 单次 Token 上限
- 墙钟时间限制
- 费用熔断

**讲师点拨：**  
没有预算的 Loop 会「体面地烧钱」。先设轮数，再逐步加 Token / 时间 / 费用。

**代码位置：** `.env.example`、`config.py`、`verification/loop.py`

---

### 要素 9：升级（Escalation）

**设计问题：** 什么时候通知人类？

**黑板示例：** 三次重试失败 → 创建 Issue 并 @ 负责人

**本项目人类介入点：**

| 场景 | 行为 | 是否自动通知 |
|---|---|---|
| 校验多次失败 | 写 trace，状态 `failed_verification` | 否（需人看 traces） |
| Loop 4 改 harness | 只生成 proposal，必须 `approve` | 是（强制人审） |
| 发布到 GitHub | 刻意不做，只写本地 PR 草稿 | 把「合并」留给人 |

```bash
docs-loop improve
docs-loop approve data/harness_proposals/xxx.json --approved-by "学员名"
```

**讲师点拨：**  
升级不是「失败了打个日志」，而是 **明确哪些决策不能自动化**。本项目最强的升级点是：harness 变更必须人批。

**代码位置：** `improvement/apply.py`、`observability/tracing.py`、`repository/pull_request.py`

---

### 要素 10：退出（Exit）

**设计问题：** 怎么知道完成了？

**黑板示例：** 独立评估器模型判断

**本项目完成条件（同时满足）：**

1. 确定性检查全部通过  
2. 若启用 Judge，则 Judge 判定通过  
3. 发布本地 PR 草稿到 `data/pull_request_drafts/`  
4. run 状态变为 `succeeded`

退出产物：

- `data/pull_request_drafts/*.md`：给人审阅的变更说明 + diff  
- `data/traces/*.json`：给 Loop 4 用的结构化痕迹  

**讲师点拨：**  
「模型自己说做完了」不算退出；**独立检查通过 + 留下可审产物** 才算退出。Judge 就是黑板里的「独立评估器」。

**代码位置：** `verification/loop.py`（成功分支）、`repository/pull_request.py`

---

## 4. 把 10 要素嵌回一次真实请求

用一条命令串起来讲：

```bash
docs-loop run \
  "Improve the getting-started guide. State the Python requirement, add the pip installation command, and keep the link to the configuration guide." \
  --reset
```

请求生命周期：

```text
[触发] CLI run
   ↓
[发现] instruction = 要改 getting-started
   ↓
[工作空间] sample_repo（或隔离 clone）
   ↓
[上下文] 加载 harness.json（含 learned_rules）
   ↓
[委托-Maker] Agent 调 5 个文档工具改文件          ← Loop 1
   ↓
[验证] 确定性检查 + LLM Judge                     ← Loop 2
   ├─ 失败 → [预算] 未超 3 次？带 feedback 重回 Maker
   └─ 成功 → [退出] 写 PR 草稿 + trace
   ↓
（另一次课 / 多次运行后）
[升级] 人执行 improve → 审 proposal → approve     ← Loop 4
   ↓
[上下文更新] learned_rules 写入 harness，影响下次 Loop 1
```

---

## 5. 课堂演示建议（30–45 分钟）

### Demo A：看 Loop 1 + 2（15 分钟）

1. 打开 `sample_repo/docs/getting-started.md`  
2. 跑上面的 `docs-loop run ... --reset`  
3. 打开 `data/pull_request_drafts/` 与 `data/traces/`  
4. 对照讲解：目标、工作空间、委托、验证、预算、退出  

### Demo B：看触发与发现（5 分钟）

1. `docs-loop serve --reload`  
2. 发送 `scripts/demo_request.json`  
3. 轮询 `/runs/{run_id}`  
4. 强调：Trigger ≠ 自动发现生产问题，而是「事件入口」  

### Demo C：看上下文与升级（10 分钟）

1. `docs-loop improve --offline`（无 Key 也能演示结构）  
2. 打开 `data/harness_proposals/`  
3. 说明：没有 `approve`，harness **不会变**  
4. （可选）approve 后对比 `config/harness.json` 的 `learned_rules`  

### 讨论题（5–10 分钟）

1. 如果把目标改成「自动合并 PR」，哪些要素必须加强？  
2. 本项目的「发现」够不够生产用？缺什么？  
3. Maker 和 Checker 共用一个模型，会有什么风险？  

---

## 6. 诚实边界：教学版 vs 生产版

讲课结尾务必说清——**符合 Loop 思想，不等于生产全量**：

| 要素 | 教学版现状 | 生产常补齐 |
|---|---|---|
| 触发 | CLI / 本地 FastAPI | 签名 webhook、cron、队列 |
| 发现 | 人写 instruction | Issue/CI/文档监控自动建单 |
| 工作空间 | 本地 clone | 容器 / worktree / 最小权限凭证 |
| 预算 | 主要是重试次数 | Token、费用、超时、并发上限 |
| 升级 | approve + 本地草稿 | 告警、建 Issue、@oncall、审批流 |
| 退出 | 本地 PR 草稿 | 真 PR + CI 门禁 + 人工合并策略 |

---

## 7. 学员课后练习

1. **改目标：** 在 `harness.json` 增加一条规则「禁止修改 README.md」，跑一次请求，观察验证是否挡住越界改动。  
2. **压预算：** 把 `MAX_VERIFICATION_ATTEMPTS=1`，故意给模糊指令，观察失败状态与 trace。  
3. **做人审：** 跑两次失败任务 → `improve --offline` → 阅读 proposal → 决定批或不批，并说明理由。  
4. **画图：** 用一张图把「10 要素」标注到「一次 `docs-loop run`」的时序上（交作业）。  

---

## 8. 一句话收束

> **Loop 工程 = 把目标、触发、发现、空间、上下文、委托、验证、预算、升级、退出这 10 件事设计清楚，并让它们在 1→2→3→4 的闭环里反复运转。**  
> 本项目是这套思想的可运行教案：能跑通、能对照、能指出简化点——这正是学习 Loop 工程最好的起点。

---

## 附录：关键代码索引

| 主题 | 路径 |
|---|---|
| CLI 入口 | `src/loop_engineering/cli.py` |
| Agent 构建 | `src/loop_engineering/agent/factory.py` |
| Agent 执行 | `src/loop_engineering/agent/runner.py` |
| 工具 | `src/loop_engineering/tools/docs_tools.py` |
| 校验循环 | `src/loop_engineering/verification/loop.py` |
| 确定性检查 | `src/loop_engineering/verification/deterministic.py` |
| LLM Judge | `src/loop_engineering/verification/llm_judge.py` |
| 事件 API | `src/loop_engineering/events/api.py` |
| 隔离工作区 | `src/loop_engineering/events/service.py` |
| Harness | `config/harness.json` |
| 改进与批准 | `src/loop_engineering/improvement/` |
| 示例请求 | `scripts/demo_request.json` |
