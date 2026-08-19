# 课件：一条命令看懂 Loop 工程的 10 个要素

> 任务命令（本节唯一案例）：
>
> ```bash
> docs-loop run "Clarify the installation section in getting-started." --reset
> ```
>
> 配套框架：自动化代理设计框架（目标 / 触发 / 发现 / 工作空间 / 上下文 / 委托 / 验证 / 预算 / 升级 / 退出）  
> 配套项目：当前仓库 `doc-agent-loop`（Loop Engineering 文档 Agent）

---

## 0. 先说清：这条命令在干什么

**任务目标（业务语言）：**  
让 Agent 打开示例文档仓库，把 `getting-started` 里的 **Install（安装）** 章节写得更清楚；改完后自动验收，通过则留下一份本地 PR 草稿。

**系统动作（技术语言）：**  
启动 **Loop 1（Agent 改文档）+ Loop 2（校验重试）**。  
`--reset` 表示先清掉工作区旧改动，从干净状态开始。

**操作对象：**

- 工作区：`sample_repo/`
- 重点文件：`sample_repo/docs/getting-started.md`（里面有 `## Install`）
- 产出：`data/pull_request_drafts/`、`data/traces/`

> 本节不讲 `serve` / `improve`。只回答：  
> **跑这一条 `docs-loop run ...` 时，黑板里的 10 个要素分别落在哪里？**

---

## 1. 一图总览：10 要素如何嵌进这条命令

```text
docs-loop run "Clarify the installation section in getting-started." --reset
│
├─ [2 触发]  你敲下这条 CLI，系统开始跑
├─ [3 发现]  引号里的句子 = 本次要干的活
├─ [4 工作空间] --reset 清空后，在 sample_repo 安全操作
├─ [5 上下文]  加载 config/harness.json（规则与权限）
├─ [1 目标]  harness 规定：做最小正确的文档改动
│
└─ VerificationLoop.run()
      │
      ├─ [6 委托-Maker]  Agent 用工具改 getting-started
      │     list / search / read / write / inspect_diff
      │
      ├─ [7 验证]  检查「这一轮」干得好不好（还在循环里）
      │     确定性检查 +（可选）LLM Judge
      │     不过 → 反馈回灌 Maker，再试（未退出）
      │     [8 预算]  最多 MAX_VERIFICATION_ATTEMPTS 次（默认 3）
      │
      └─ [10 退出]  检查「整件事」能否彻底结束循环
            ├─ 验证通过 → 写 PR 草稿 + trace，status=succeeded（成功退出）
            └─ 预算用尽仍失败 → status=failed_verification（失败退出）
                  │
                  └─ [9 升级] 本命令不会自动 @人；
                     但留下 traces / 失败报告，供人查看或后续 Loop 4
```

> **验证 vs 退出（务必先分清）：**  
> - ✅ **验证**：看这一步/这一轮好不好；错了就重来，**还在循环里**。  
> - 🚪 **退出**：看整件事是否全部收工；可以成功结束，也可以失败结束，但都是**彻底离开循环**。

---

## 2. 逐要素对照（围绕这一条命令讲）

### ① 目标（Objective）—— Loop 要优化什么？

| 项 | 内容 |
|---|---|
| 黑板示例 | 「保持 CI 绿色」 |
| **本任务目标** | 澄清 getting-started 的安装说明，且改动最小、正确、不越界 |
| **项目体现** | `config/harness.json` 的 system prompt：最小正确改动、只改 Markdown、不编造事实、紧贴请求 |

**讲课一句话：**  
引号里是「这次业务目标」；`harness.json` 是「永远成立的优化原则」。两者合起来才是完整目标。

**代码：** `config/harness.json`、`agent/factory.py`

---

### ② 触发（Trigger）—— 什么时候运行？

| 项 | 内容 |
|---|---|
| 黑板示例 | 每 10 分钟 / CI 失败事件 |
| **本任务触发** | 人工执行 `docs-loop run ...`（CLI 显式触发） |
| **项目体现** | `cli.py` 的 `run` 命令 → 创建 `VerificationLoop` → `loop.run(...)` |

**讲课一句话：**  
这条命令本身就是 Trigger。没有 cron，也没有 webhook；你按下回车，Loop 才开始。

**代码：** `src/loop_engineering/cli.py`（`run_request`）

---

### ③ 发现（Discover）—— 怎么找到要干的活？

| 项 | 内容 |
|---|---|
| 黑板示例 | 读 CI 日志、GitHub Issues |
| **本任务发现** | 任务已经写在参数里：`Clarify the installation section in getting-started.` |
| **项目体现** | 封装为 `DocsRequest(instruction=..., source="cli")`；Agent 再用工具在仓库里「二次发现」具体文件与段落 |

二次发现常用工具：

- `search_documentation("Install")` / `getting-started`
- `read_document("docs/getting-started.md")`
- `list_documentation_files`

**讲课一句话：**  
本项目把「捞任务」简化成命令行参数；Agent 负责「进仓库找该改哪一段」。

**代码：** `schemas.py`（`DocsRequest`）、`tools/docs_tools.py`

---

### ④ 工作空间（Workspace）—— Agent 在哪里安全操作？

| 项 | 内容 |
|---|---|
| 黑板示例 | Git Worktree 隔离 |
| **本任务空间** | 默认 `sample_repo/`；`--reset` = `git reset --hard`，丢掉未提交脏改动 |
| **项目体现** | 只允许写 `.md/.mdx`；禁止碰 `.git` / `data` / `.env`；防路径穿越 |

**讲课一句话：**  
`--reset` 保证每次演示从同一起点开始；安全边界保证 Agent 不能乱改仓库外文件。

**代码：** `cli.py`（`--reset`）、`repository/local.py`、`repository/git.py`  
**配置：** `WORKSPACE_PATH=sample_repo`、`harness.json` 的 `allowed_extensions` / `protected_paths`

---

### ⑤ 上下文（Context）—— 有哪些持久化知识？

| 项 | 内容 |
|---|---|
| 黑板示例 | `SKILL.md`、`CLAUDE.md` |
| **本任务上下文** | 每次 run 都会加载 `config/harness.json` |
| **项目体现** | system prompt + 扩展名白名单 + 保护路径 +（若有）`learned_rules` |

对这条命令而言，Agent「记住」的不是聊天历史，而是：

1. 怎么当文档改进 Agent（system prompt）  
2. 只能改哪些文件类型  
3. 哪些路径碰不得  
4. 过去人审通过的规则（`learned_rules`，可能为空）

**讲课一句话：**  
`harness.json` 就是本项目的持久化知识底座；Loop 4 以后还会往这里「追加学到的规则」。

**代码：** `config/harness.json`、`config.py`、`agent/factory.py`

---

### ⑥ 委托（Delegation）—— 哪个角色做什么？

| 项 | 内容 |
|---|---|
| 黑板示例 | maker-agent vs checker-agent |
| **本任务委托** | Maker 改文档；Checker 验收；二者职责分离 |

| 角色 | 本项目组件 | 在这条命令里做什么 |
|---|---|---|
| Maker | `create_docs_agent` + 5 个工具 | 澄清 Install 章节、写回 md、看 diff |
| Checker（规则） | `DeterministicVerifier` | 有无改动、是否只改 docs、链接、占位符等 |
| Checker（语义） | `LLMScopeJudge`（若 `USE_LLM_JUDGE=true`） | 是否真的「澄清了安装说明」、是否越界 |

**讲课一句话：**  
不是一个模型既当选手又当终审。Maker 负责改；Checker 负责说行不行。

**代码：** `agent/factory.py`、`agent/runner.py`、`verification/deterministic.py`、`verification/llm_judge.py`

---

### ⑦ 验证（Verification）—— 这一轮干得好不好？

| 项 | 内容 |
|---|---|
| 黑板示例（思想） | 测试 / 检查 / 独立评审 |
| **核心含义** | 检查**这一轮尝试**的质量；不过就反馈重试，**人还在循环里** |
| **本任务验证** | Maker 改完 `getting-started` 后立刻跑验证栈 |

对本命令，「这一轮算过关」至少意味着：

1. 工作区真有文档改动  
2. 没有改到非文档文件  
3. 相对链接（如 `configuration.md`）仍有效  
4. 没有留下 TODO/FIXME 之类占位符  
5. （可选）LLM Judge 认为满足 “Clarify the installation section...”

两种去向（注意：验证本身不结束整次 run）：

| 验证结果 | 下一步 | 是否还在循环里 |
|---|---|---|
| 不过 | 报告变成 feedback → 回灌 Maker 再改 | ✅ 还在 |
| 通过 | 把「可以收工」信号交给退出条件 | 交给 ⑩ 退出 |

**讲课一句话：**  
验证问的是「这一步好不好」；错了就重来。它管质量门，不负责宣布整件事结束。

**代码：** `verification/loop.py`、`verification/deterministic.py`、`verification/llm_judge.py`

---

### ⑧ 预算（Budget）—— 何时停止？

| 项 | 内容 |
|---|---|
| 黑板示例 | 最大轮数、Token 上限、时间限制 |
| **本任务预算** | 默认最多验证重试 **3** 次（`.env` 里 `MAX_VERIFICATION_ATTEMPTS`） |

循环形态：

```text
第 1 次：Maker 改 → 验证
失败 → 第 2 次：带 feedback 再改 → 验证
失败 → 第 3 次：再改 → 验证
仍失败 → 停止，标记 failed_verification
```

**讲课一句话：**  
即使安装说明一直改不对，系统也会停——不会无限烧模型。

**代码：** `config.py`、`verification/loop.py`、`.env`

---

### ⑨ 升级（Escalation）—— 什么时候通知人类？

| 项 | 内容 |
|---|---|
| 黑板示例 | 三次失败 → 建 Issue 并 @ 负责人 |
| **本任务升级** | **弱实现（教学简化）**：不会自动建 Issue / 发通知 |

这条 `docs-loop run` 里，人类相关边界是：

| 情况 | 系统行为 | 人类怎么介入 |
|---|---|---|
| 成功 | 写本地 PR 草稿 | 人去看草稿，决定要不要当真合并 |
| 失败用尽 | 写 trace + `failed_verification` | 人看 `data/traces/` 诊断 |
| 改 harness | 本命令不改 | 需另跑 `improve` + `approve`（强制人审） |

**讲课一句话：**  
要素在，但「告警通道」没接满。课堂要讲清：生产里这里应接 Issue / 值班；本项目用 traces + 本地草稿代替。

**代码：** `observability/tracing.py`、`repository/pull_request.py`；（完整人审在）`improvement/apply.py`

---

### ⑩ 退出（Exit）—— 整件事能否彻底结束？

| 项 | 内容 |
|---|---|
| 黑板示例 | 独立评估器模型判断 |
| **核心含义** | 检查**整次 run** 是否可以收工；一旦退出，就**彻底离开** Maker↔验证循环 |
| **本任务退出** | 成功退出或失败退出，两种都算「结束」 |

| 退出类型 | 条件 | 系统动作 |
|---|---|---|
| 成功退出 | 验证通过（确定性全过 + Judge 通过或未启用） | `status=succeeded`；写 PR 草稿；存 trace |
| 失败退出 | 预算用尽仍未通过验证 | `status=failed_verification`；存 trace；不写成功 PR |

成功退出时额外做：

1. 发布本地 PR 草稿到 `data/pull_request_drafts/`  
2. 终端打印本次 run 的 JSON（完成信号）

**和验证的对比（讲课必讲）：**

| | ✅ 验证 | 🚪 退出 |
|---|---|---|
| 看什么 | **这一轮**干得好不好 | **整件事**是否全部收工 |
| 失败后 | 带反馈重试 | （失败退出时）不再重试 |
| 循环状态 | **还在循环里** | **彻底结束循环** |
| 本项目信号 | `attempt.verification.passed` | `run.status` = `succeeded` / `failed_verification` |

**讲课一句话：**  
退出问的是「整件事能不能收工」。Agent 自己说做完了不算；要以验证结果 + 预算边界为准，成功或失败都可以退出。

**代码：** `verification/loop.py`（成功/失败收尾）、`repository/pull_request.py`

---

## 3. 用「安装章节」故事串一遍（建议照读）

1. **触发：** 讲师执行上述命令。  
2. **发现：** 系统拿到指令——澄清 getting-started 安装部分。  
3. **工作空间：** `--reset` 后进入干净的 `sample_repo`。  
4. **上下文：** 戴上 `harness.json` 这顶「行为帽子」。  
5. **目标：** 最小改动，把 Install 讲清楚，不乱改别的。  
6. **委托：** Maker 去读 `docs/getting-started.md`，改 Install；Checker 在旁边验货。  
7. **验证：** 看**这一轮**好不好——链接还在吗？是不是只改了文档？语义上算不算「clarify」？不过就重来，还在循环里。  
8. **预算：** 最多三轮；防止永远验不过。  
9. **退出：** 看**整件事**能否收工——通过则成功退出并留 PR 草稿；轮次用尽则失败退出。两种都离开循环。  
10. **升级：** 若失败或要改规则，交给人看 traces / 走 approve（本命令本身不自动喊人）。

---

## 4. 课堂观察清单（跑完命令后对照）

| 观察点 | 去哪里看 | 对应要素 |
|---|---|---|
| 命令是否启动 | 终端开始输出 JSON/日志 | 触发 |
| 改了哪个文件 | `sample_repo/docs/getting-started.md` | 发现 / 目标 |
| 是否从干净状态开始 | 跑前 `--reset` | 工作空间 |
| 行为约束从哪来 | `config/harness.json` | 上下文 |
| 谁在写、谁在验 | traces 里的 attempt + verification | 委托 / 验证 |
| 某一轮过没过（还在循环） | 单次 `attempt.verification.passed` | 验证 |
| 试了几次 | `attempts` 数组长度 | 预算 |
| 整次 run 结束了没（已离循环） | 顶层 `status`、`pull_request` | 退出 |
| 失败给人看什么 | `data/traces/`、`data/pull_request_drafts/` | 升级（弱） |

---

## 5. 教学提醒：这条命令覆盖了哪些 Loop？

| Loop | 本命令是否覆盖 |
|---|---|
| Loop 1 Agent | ✅ 覆盖 |
| Loop 2 验证重试 | ✅ 覆盖 |
| Loop 3 事件驱动 | ❌ 未覆盖（要用 `docs-loop serve`） |
| Loop 4 爬山改进 | ❌ 未覆盖（要用 `improve` / `approve`） |

所以讲课时应说：

> 这一条 `docs-loop run`，把 10 要素里的 **核心执行链路**（目标→触发→发现→空间→上下文→委托→验证→预算→退出）跑通了；  
> **升级**在本命令里是「留痕迹给人」；完整的「改 harness 必须人批」要到 Loop 4 才强体现。

---

## 6. 一句话收束

> **`docs-loop run "Clarify the installation section in getting-started." --reset`  
> = 用一次「澄清安装文档」的任务，把 Loop 工程 10 要素从黑板落到可运行代码里。**

目标决定优化方向，触发启动闭环，发现给出任务，工作空间保证安全，上下文提供持久规则，委托拆开写与验；**验证管「这一轮好不好、错了重来」**，预算防止失控，升级留给人类关键决策；**退出管「整件事能否收工、彻底结束循环」**（成功或失败都可以退出）。
