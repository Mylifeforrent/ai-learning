# 02. Project Evolution Path

五个阶段性综合项目构成了一条很清晰的 AI 工程演进路径：先把一个明确任务做成可运行系统，再接入真实工作入口和工具生态，然后引入记忆，扩展为团队，最后做生产安全加固。

## 总览

| 项目 | 核心问题 | 新增能力 | 工程收益 |
| --- | --- | --- | --- |
| Project 1：小红书爆款笔记 | 如何把多 Agent 能力落成一个真实 API 应用 | 多模态、5 Agent、7 Task、三阶段 Flow、FastAPI、Pydantic、日志指标 | 从课程 demo 进入端到端 AI 应用 |
| Project 2：XiaoPaw 飞书助手 | 如何让 Agent 接入真实工作场景和大量工具 | 飞书 WebSocket、Runner、Session、Skills、Sub-Crew、AIO-Sandbox、Cron | 从单次任务变成可交互工作助手 |
| Project 3：XiaoPaw With Memory | 如何让助手跨轮、跨会话保留知识 | Bootstrap、ctx/raw、文件记忆、skill 记忆、pgvector 搜索记忆 | 从无状态工具助手变成长期可成长助手 |
| Project 4：Agent Teams | 如何让多个数字员工完成真实项目 | Manager/PM/RD/QA、邮箱、共享区、事件流、HITL、自我复盘 | 从个人助手变成可协作的数字团队 |
| Project 5：Security Enhancement | 如何让系统可观测、可靠、安全、可测试 | HookRegistry、5+2 事件、Guardrails、SSOT、E2E、Langfuse、审计 | 从可用系统进入生产加固形态 |

## Project 1：小红书爆款笔记

来源：`11.项目实战一：小红书爆款笔记/crewai_mas_demo_m2l7/`

### 解决的问题

Project 1 解决的是“如何把 Agent / Task / Process / Multimodal 做成一个完整 Web 服务”。它不只是跑 CrewAI，而是具备真实工程外壳：

- FastAPI 接收 multipart 表单和图片。
- Service 层做图片保存、压缩、清理。
- Flow 层编排 CrewAI 多阶段任务。
- Pydantic schema 约束输入输出。
- 日志、指标、鉴权、限流、测试、部署目录都已出现。

### Agent 与 Workflow 设计

项目使用 5 个角色：

| Agent | 职责 |
| --- | --- |
| 视觉分析师 | 对图片做平台审美、情绪价值、商业转化分析 |
| 图片编辑师 | 生成轻量、可复现、平台安全的图片编辑方案 |
| 增长策略专家 | 基于用户意图和图片分析生成内容策略简报 |
| 内容撰写师 | 把策略转译为小红书文案 |
| SEO 优化专家 | 优化标题、正文、标签和长尾关键词 |

任务链条是典型的“并发分析 + 汇总 + 串行创作”：

```text
多图视觉分析
  -> 视觉分析总结
  -> 多图编辑方案
  -> 编辑方案总结
  -> 内容策略
  -> 文案撰写
  -> SEO 优化
```

### 设计动机

Project 1 的关键不是“Agent 数量多”，而是把不稳定的智能推理包进稳定边界：

- Agent 人设放在 `crews/config/agents.yaml`，便于迭代。
- Task 模板放在 `crews/config/tasks.yaml`，把动态变量显式化。
- 输出结构用 `schemas/xhs_note.py` 接住，避免文案式返回不可解析。
- 编排逻辑放在 `crews/xhs_note/flows.py`，业务 API 不直接关心 CrewAI 细节。

### 可迁移模式

| 模式 | 可迁移做法 |
| --- | --- |
| YAML + Python 分离 | YAML 存角色和任务文本，Python 存工厂函数和流程编排 |
| 契约先行 | 每个 Task 都映射到结构化输出模型 |
| 多模态引用 | 传图片路径，让 AddImageTool 注入图像，不把图像内容硬塞上下文 |
| 服务层隔离 | API 层只处理 HTTP，Service 层处理业务，Flow 层处理 Agent |

## Project 2：XiaoPaw 飞书本地工作助手

来源：`17.Project2-Xiaopaw-feishu-assistant/xiaopaw/`

### 相比 Project 1 增加的能力

Project 2 从“单次生成报告”升级为“持续交互工作助手”。它新增了：

- 飞书 WebSocket 长连接作为真实入口。
- `Runner` 作为内部执行引擎。
- `SessionManager` 管理 routing_key 和历史。
- `SkillLoaderTool` 做渐进式披露。
- `Sub-Crew` 在沙盒中执行任务型 Skill。
- `CronService` 支持定时任务。
- `CleanupService` 清理文件、会话和 trace。
- 飞书 sender/downloader/listener 把外部平台和内部消息模型解耦。

### 核心数据流

```text
飞书事件
  -> FeishuListener
  -> InboundMessage
  -> Runner per-routing_key queue
  -> SessionManager
  -> Main Agent
  -> SkillLoaderTool
  -> reference skill 或 task skill
  -> Sub-Crew + AIO-Sandbox
  -> FeishuSender
```

### 设计动机

Project 2 的核心是“把真实世界的复杂入口压成统一内部协议”。飞书、测试 API、Cron 最后都变成 `InboundMessage`，然后由 Runner 统一调度。这个设计让后续记忆、加固、团队协作都能挂在同一条消息链路上。

### 工程收益

| 增强点 | 收益 |
| --- | --- |
| routing_key 队列 | 同一会话串行，不同会话并发 |
| SkillLoaderTool | 主 Agent 不需要一次性加载所有工具说明 |
| Sub-Crew | 复杂任务独立上下文执行，降低主上下文污染 |
| AIO-Sandbox | 执行类能力隔离，凭证不进入模型上下文 |
| CronService | Agent 能被定时唤醒，系统从被动响应变成主动执行 |

## Project 3：XiaoPaw With Memory

来源：`22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory/`

### 相比 Project 2 增加的能力

Project 3 在 Project 2 的消息骨架上增加三层记忆：

| 层次 | 落地位置 | 作用 |
| --- | --- | --- |
| 文件层 | `workspace-init/*.md`、运行时 workspace 文件 | 保存身份、用户、行为规范、长期记忆索引 |
| 上下文层 | `data/ctx/{session_id}_ctx.json`、raw jsonl | 保存跨轮上下文快照和原始消息 |
| 搜索层 | `schema.sql`、`memory/indexer.py`、pgvector | 对历史对话和记忆做语义检索 |

### 关键设计

Project 3 的 `project_harness_walkthrough.md` 已经点明核心：记忆不是侵入飞书路由，而是长在 harness 上。

具体表现：

- `main.py` 继续装配外部服务。
- `Runner` 继续做消息调度。
- `SkillLoaderTool` 继续做工具路由。
- 记忆集中在 `xiaopaw/agents/main_crew.py` 和 `xiaopaw/memory/*`。
- `build_bootstrap_prompt()` 每轮读 `soul.md`、`user.md`、`agent.md`、`memory.md`。
- `before_llm_call` 负责 restore、prune、compress。
- 每轮结束后异步索引历史，不阻塞主回复。

### 设计动机

Project 3 解决的是“长期助手不应靠把所有历史塞进 prompt”。它把记忆拆成：

- 当前应该知道什么：Bootstrap。
- 当前不该带什么：prune / compress。
- 需要时再找什么：search_memory。
- 需要长期固化什么：memory-save / skill-creator。

### 工程收益

| 能力 | 收益 |
| --- | --- |
| Bootstrap 四件套 | system 背景可编辑、可迁移、可由 Agent 学习 |
| 文件记忆 | 用户偏好和项目事实可以被长期保存 |
| skill 记忆 | 可把重复 SOP 固化为程序化能力 |
| pgvector 搜索 | 支持跨会话语义召回 |
| 上下文剪枝压缩 | 控制 token、降低 context rot |

## Project 4：Agent Teams

来源：`29.Project4-Agent teams/xiaopaw-team/`

### 相比 Project 3 增加的能力

Project 4 把“一个长期助手”扩展成“一个数字员工团队”。它继承 Project 2/3 的飞书、Runner、Skills、Memory 基础，新增：

- Manager、PM、RD、QA 四角色。
- 每个角色有独立 `agent.md`、`soul.md`、`user.md`、`memory.md`。
- 共享工作区 `workspace/shared/`。
- 团队协议 `team_protocol.md`。
- 邮箱消息机制。
- 项目事件流。
- Human Checkpoint。
- 自我复盘和改进 proposal。

### 核心协作协议

Project 4 的关键不是让所有 Agent 共享同一个上下文，而是用外部协议协作：

| 机制 | 作用 |
| --- | --- |
| 邮箱 | Agent 之间发送结构化消息，支持未读、处理中、已完成状态 |
| 共享工作区 | 文档、需求、设计、代码、测试产物以路径引用传递 |
| 事件流 | 记录项目阶段、决策、复盘和审计证据 |
| Manager 单一接口 | PM/RD/QA 不直接找用户，外部沟通由 Manager 控制 |
| self_score | 每次任务完成前自评质量 |
| retro proposal | 基于日志提出可审查的改进 |

### 设计动机

Project 4 解决的是“复杂项目不能靠一个 Agent 的长上下文硬撑”。当任务变成多角色、多阶段、多天、多产物时，应该引入组织结构，而不是继续堆 prompt。

### 工程收益

| 增强点 | 收益 |
| --- | --- |
| 角色隔离 | 避免记忆污染和能力稀释 |
| 邮箱协议 | 任务交接可审计、可恢复、可异步 |
| 共享工作区 | 传路径不传全文，降低上下文膨胀 |
| HITL | 人类只在需求、方案、风险点介入 |
| 复盘系统 | Agent 可以基于证据改进 memory、skill、agent 规则 |

## Project 5：XiaoPaw With Security Enhancement

来源：`33.Project5-xiaopaw with security enhancement/xiaopaw-v2/`

### 相比 Project 3/4 增加的能力

Project 5 回到 XiaoPaw 飞书助手主线，对 Project 3 的长期记忆助手做生产加固，并吸收课程 30-32 的 Hook、可靠性、安全实践。

主要新增：

- `hook_framework/`：HookRegistry、HookLoader、CrewAdapter。
- `shared_hooks/`：structured_log、langfuse_trace、sandbox_guard、permission_gate、audit_logger、cost_guard、loop_detector、retry_tracker。
- `docs/ssot/`：locks、tasks、ports、feature-flags、threats。
- `docs/01-15*.md`：架构、模块、数据、API、并发、安全、部署、测试、加固设计。
- `tests/e2e/`：15 个 E2E 场景加 persona 测试。
- `config/`：安全配置、feature flag、配置校验。
- `observability/`：trace、PII mask、安全日志、metrics。

### Hook 分层

Project 5 的 `shared_hooks/hooks.yaml` 展示了一个可复用的加固范式：

```text
观测层 hooks
  BEFORE_TURN / BEFORE_LLM / BEFORE_TOOL_CALL / AFTER_TOOL_CALL
  AFTER_TURN / TASK_COMPLETE / SESSION_END

策略层 strategies
  audit_logger
  sandbox_guard
  permission_gate
  cost_guard
  loop_detector
  retry_tracker
```

观测层 fire-and-forget，不阻断业务；策略层走 `dispatch_gate`，可以 deny 工具调用或终止风险路径。

### 设计动机

Project 5 解决的是“Prompt 无法管理生产风险”。安全、可靠性和观测不能只写在提示词里，必须进入确定性工程层：

- 输入消毒不靠模型自觉。
- 工具权限不靠模型承诺。
- 凭证不进入 LLM 上下文。
- 成本和循环检测必须实时阻断。
- Trace 必须覆盖 deny、error、session end。
- 已知风险要有对应测试。

### 工程收益

| 加固点 | 收益 |
| --- | --- |
| 5+2 事件体系 | 统一观测、可靠性和安全策略挂载点 |
| 两层 YAML 配置 | 全局策略和 workspace 策略可组合 |
| SSOT 清单 | 降低文档和实现漂移 |
| E2E 场景矩阵 | 覆盖真实交互路径和已知风险 |
| PII mask / audit | 支持企业安全合规 |
| cost / loop guard | 防止 Agent Loop 失控 |

## 通用演进路径

从五个项目可以抽象出一条通用路径：

```text
1. 明确单任务价值
   -> 2. 用 Agent / Task / Process 做可解释编排
   -> 3. 接入真实渠道与工具生态
   -> 4. 用 Harness 管理 session、workspace、context、sandbox
   -> 5. 引入 memory 和 search，形成长期能力
   -> 6. 拆分角色和协作协议，形成团队
   -> 7. 用 Hook、Eval、CI/CD、Monitoring 加固为生产系统
```

## 能力增强矩阵

| 能力维度 | Project 1 | Project 2 | Project 3 | Project 4 | Project 5 |
| --- | --- | --- | --- | --- | --- |
| 用户入口 | HTTP API | 飞书 / TestAPI / Cron | 继承 Project 2 | 飞书 + 团队唤醒 | 飞书 + 加固 TestAPI |
| Agent 形态 | 多 Agent 流程 | 主 Agent + Sub-Crew | MemoryAware 主 Agent | Manager + PM + RD + QA | 主 Agent + Hook 加固 |
| 工具体系 | 本地 Tool | Skills + MCP + Sandbox | Skills + Memory Skills | Role-scoped Skills | Skills + 权限策略 |
| 上下文 | 单次任务上下文 | Session history | Bootstrap + prune + compress | 角色工作区 + 事件流 | 加固上下文和 token 计数 |
| 记忆 | 无长期记忆 | 清洁历史 | 文件记忆 + 搜索记忆 | 角色记忆 + 复盘记忆 | 安全隔离的长期记忆 |
| 协作 | 固定流程 | 主从 Crew | 单助手长期演进 | 邮箱 + 共享区 + HITL | 侧重生产可靠性 |
| 观测 | structlog / metrics | 日志 / metrics / trace | 记忆链路可测 | 三层日志 | Langfuse + structured_log |
| 安全 | API Key / 限流 | Sandbox / 凭证隔离 | search 隔离 | 单一接口和权限边界 | Guardrails / 审计 / PII |
| 测试 | unit + integration | unit + integration | memory integration | team E2E | unit + integration + E2E |

## 迁移判断

新项目可以用以下问题判断当前该走到哪一层：

| 问题 | 如果答案是“是” | 下一步 |
| --- | --- | --- |
| 是否只有一个清晰输出任务？ | 是 | 从 Project 1 模式开始 |
| 是否需要接入企业 IM、文件、浏览器、日历等工具？ | 是 | 采用 Project 2 的 Runner + Skills + Sandbox |
| 是否需要跨天、跨会话记住用户和项目？ | 是 | 引入 Project 3 的三层记忆 |
| 是否需要多个专业角色共同交付？ | 是 | 引入 Project 4 的团队协议 |
| 是否要上线给真实用户长期使用？ | 是 | 引入 Project 5 的 Hook、Guardrails、Eval、Monitoring |

