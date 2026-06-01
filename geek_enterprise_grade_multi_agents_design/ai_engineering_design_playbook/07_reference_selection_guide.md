# 07. Reference Selection Guide

本文件回答一个关键问题：以后做新 AI 项目时，只把前 6 个 playbook 文档给 AI 参考够不够？

结论：**前 6 个文档足够约束“怎么思考”，但通常不够约束“工程实现长什么样”。** 如果希望新项目和本课程体系保持高度同源，应按项目类型追加 1-3 个综合项目或对应小节 demo 作为 canonical reference。

## 推荐参考层级

给未来 AI 的参考材料建议分三层，而不是一次性把整个课程目录塞进去。

| 层级 | 给什么 | 作用 |
| --- | --- | --- |
| 第一层：方法论 | `ai_engineering_design_playbook/README.md` 到 `06_agent_long_term_reference.md` | 统一设计原则、项目结构、Harness、Memory、安全和测试思想 |
| 第二层：综合项目 | Project 1-5 中与当前任务最相近的 1-3 个 | 约束工程形态、目录结构、代码组织和真实落地方式 |
| 第三层：小节 demo | `crewai_mas_demo/m*l*` 中和具体能力相关的少量 demo | 解决某个具体机制如何实现，例如 SkillLoader、Hook、Memory、Mailbox |

默认不要全量给所有项目。参考材料过多时，AI 容易混淆阶段目标，把团队协作、安全加固、记忆系统等能力过早堆进 MVP。

## 什么时候只给 playbook 就够

以下场景可以先只给 playbook：

| 场景 | 原因 |
| --- | --- |
| 做方案评审 | 只需要方法论、检查清单和演进路径 |
| 写 PRD / 架构草案 | 不需要复刻具体代码结构 |
| 判断 AI 项目是否值得做 | 重点是 ROI、场景建模和风险判断 |
| 设计目录草图 | `04_reusable_project_template.md` 已足够 |
| 做代码 review 清单 | `03`、`05`、`06` 已覆盖主要风险 |

但一旦进入实际实现，建议至少追加一个综合项目。

## 综合项目选择矩阵

| 新项目类型 | 必选参考 | 可选参考 | 不建议优先参考 |
| --- | --- | --- | --- |
| 普通 AI Web/API 应用 | Project 1 | `crewai_mas_demo/m2l3`、`m2l4`、`m2l5` | Project 4/5，除非明确需要团队或生产加固 |
| 多模态内容生成 | Project 1 | `crewai_mas_demo/m2l6` | Project 4 |
| 飞书 / 企业 IM 助手 | Project 2 | Project 3，如果要长期记忆 | Project 4，除非要多角色协作 |
| 工具型本地工作助手 | Project 2 | `crewai_mas_demo/m2l16`、`m2l10` | Project 1 |
| 长期记忆助手 | Project 3 | `crewai_mas_demo/m3l19`、`m3l20`、`m3l21` | Project 4，除非需要团队 |
| RAG / 知识库助手 | Project 3 | `crewai_mas_demo/m3l21` | Project 1 |
| 多 Agent 团队交付项目 | Project 4 | Project 3、`crewai_mas_demo/m4l26`、`m4l27`、`m4l28` | Project 1 只能作基础参考 |
| 需要 Human checkpoint | Project 4 | `crewai_mas_demo/m4l27` | Project 2 单独不够 |
| 需要自我进化 / 复盘 | Project 4 | `crewai_mas_demo/m4l28` | Project 3 单独不够 |
| 生产级安全加固 | Project 5 | Project 3、`crewai_mas_demo/m5l30`、`m5l31`、`m5l32` | Project 1 |
| 已有 AI 助手要上线 | Project 5 | Project 3 | Project 4，除非要团队化 |

## 三个长期 canonical projects

如果只能长期保留 3 个综合项目给未来 AI 作为主参考，推荐：

| 优先级 | 项目 | 为什么 |
| --- | --- | --- |
| 1 | `22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory` | 最完整体现 Harness、Session、Bootstrap、Memory、Skill、RAG 的单助手架构 |
| 2 | `29.Project4-Agent teams/xiaopaw-team` | 最完整体现 Agent Teams、角色工作区、邮箱、共享区、HITL、自我进化 |
| 3 | `33.Project5-xiaopaw with security enhancement/xiaopaw-v2` | 最完整体现 Hook、Guardrails、Observability、SSOT、E2E、生产加固 |

Project 1 和 Project 2 仍然重要，但更适合作为阶段性参考：

- Project 1：适合从 0 到 1 做第一个 Web/API AI 项目。
- Project 2：适合做 IM 助手、工具助手和 Skills + Sandbox 基础。

## 各综合项目重点读哪些文件

### Project 1：小红书爆款笔记

路径：`11.项目实战一：小红书爆款笔记/crewai_mas_demo_m2l7/`

| 重点文件 | 看什么 |
| --- | --- |
| `README.md` | 项目目标、5 Agent、7 Task、三阶段流程 |
| `src/app/crews/config/agents.yaml` | Agent RGB 人设如何写到工程配置 |
| `src/app/crews/config/tasks.yaml` | Task 契约、变量注入、结构化输出约束 |
| `src/app/crews/xhs_note/flows.py` | 并发视觉分析 + 串行内容创作的 Flow |
| `src/app/schemas/xhs_note.py` | Pydantic 输出模型 |
| `src/app/services/xhs_note_service.py` | API Service 如何调用 Agent Flow |
| `tests/unit/`、`tests/integration/` | AI 项目最小测试分层 |

适合复刻：

- `agents.yaml` / `tasks.yaml` 分离。
- API 层、Service 层、Flow 层分离。
- 多模态路径注入。
- 输出 JSON 契约。

### Project 2：XiaoPaw 飞书助手

路径：`17.Project2-Xiaopaw-feishu-assistant/xiaopaw/`

| 重点文件 | 看什么 |
| --- | --- |
| `DESIGN.md` | 飞书助手整体架构、Runner、Skills、Sandbox |
| `xiaopaw/runner.py` | 内部消息调度和 per-routing_key 队列 |
| `xiaopaw/models.py` | `InboundMessage` 等内部消息模型 |
| `xiaopaw/session/manager.py` | routing_key 到 session 的持久化 |
| `xiaopaw/tools/skill_loader.py` | SkillLoaderTool 渐进式披露 |
| `xiaopaw/agents/main_crew.py` | Main Agent + SkillLoaderTool |
| `xiaopaw/agents/skill_crew.py` | Sub-Crew 如何执行 task skill |
| `xiaopaw/feishu/` | 企业 IM 接入如何和内部 harness 解耦 |
| `xiaopaw/cron/` | 定时唤醒和任务持久化 |

适合复刻：

- 外部入口统一为 `InboundMessage`。
- Runner 只做流程控制，不做智能判断。
- 主 Agent 极简，只通过 SkillLoader 扩展能力。
- 执行类工具放入 AIO-Sandbox。

### Project 3：XiaoPaw With Memory

路径：`22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory/`

| 重点文件 | 看什么 |
| --- | --- |
| `DESIGN.md` | 三层记忆系统和 XiaoPaw 架构 |
| `project_harness_walkthrough.md` | Harness 与 Memory 如何非侵入式接入 |
| `message_lifecycle_map.md` | 消息生命周期和记忆链路 |
| `workspace-init/soul.md` | Agent 身份如何文件化 |
| `workspace-init/user.md` | 用户长期档案如何文件化 |
| `workspace-init/agent.md` | Agent 行为规范和 SOP 入口 |
| `workspace-init/memory.md` | 长期记忆索引 |
| `xiaopaw/memory/bootstrap.py` | Bootstrap 如何构建 system 背景 |
| `xiaopaw/memory/context_mgmt.py` | restore / prune / compress / save |
| `xiaopaw/memory/indexer.py` | 异步索引和 pgvector 写入 |
| `schema.sql` | memories 表和检索字段 |
| `tests/integration/test_memory_*.py` | 记忆系统如何验收 |

适合复刻：

- `workspace-init/*.md` 四件套。
- `MemoryAwareCrew` 形态。
- `@before_llm_call` 上下文治理。
- 文件记忆 + search_memory 的组合。
- 异步索引，不阻塞主回复。

### Project 4：Agent Teams

路径：`29.Project4-Agent teams/xiaopaw-team/`

| 重点文件 | 看什么 |
| --- | --- |
| `docs/DESIGN.md` | 团队架构、角色、事件流、复盘机制 |
| `workspace/shared/team_protocol.md` | 团队通用协议 |
| `workspace/{manager,pm,rd,qa}/agent.md` | 角色 charter 和行为规则 |
| `workspace/{manager,pm,rd,qa}/soul.md` | 角色身份和决策偏好 |
| `xiaopaw_team/tools/mailbox.py` | 结构化邮箱和状态机 |
| `xiaopaw_team/tools/workspace.py` | 共享工作区读写 |
| `xiaopaw_team/tools/event_log.py` | 项目事件流 |
| `xiaopaw_team/tools/team_tools.py` | 团队工具集合 |
| `xiaopaw_team/agents/build.py` | role-scoped Agent 构建 |
| `tests/integration/test_e2e_full_journey.py` | 团队端到端流程验收 |

适合复刻：

- Manager 单一接口。
- PM/RD/QA 独立工作区。
- 邮箱传路径，不传长文。
- 共享区 + 事件流。
- self_score、retro_report、retro_approved。
- Human checkpoint 和分档审批。

### Project 5：XiaoPaw Security Enhancement

路径：`33.Project5-xiaopaw with security enhancement/xiaopaw-v2/`

| 重点文件 | 看什么 |
| --- | --- |
| `DESIGN.md` | v2/v3 总体加固路线 |
| `docs/01-architecture.md` | 信任边界和数据流 |
| `docs/05-concurrency.md` | 锁、队列、任务生命周期 |
| `docs/06-observability.md` | trace、metrics、日志 |
| `docs/07-security.md` | 威胁模型和安全策略 |
| `docs/10-testing.md` | 测试分层 |
| `docs/12-hook-hardening.md` | Hook 框架和加固层 |
| `docs/ssot/*.md` | locks、tasks、ports、flags、threats 权威清单 |
| `xiaopaw/hook_framework/` | HookRegistry、HookLoader、CrewAdapter |
| `shared_hooks/hooks.yaml` | 观测层和策略层声明式配置 |
| `shared_hooks/*.py` | structured_log、permission_gate、cost_guard 等策略 |
| `tests/e2e/` | 15 场景 E2E 验收 |

适合复刻：

- 5+2 Hook 事件体系。
- dispatch 和 dispatch_gate 分离。
- 观测 handler 与阻断策略分层。
- SSOT 文档。
- 已知风险测试和 E2E 场景矩阵。

## 按能力选择 demo

| 需要实现的能力 | demo | 重点文件 |
| --- | --- | --- |
| 理解 ReAct 和 Agent Loop | `crewai_mas_demo/m1l2` | `m1l2_raw_agent.py`、`m1l2_agent.py` |
| Multi-Agent 基础协作 | `crewai_mas_demo/m1l3` | `m1l3_multi_agent.py` |
| LLM 接入 | `crewai_mas_demo/m2l2` | `m2l2_llm_openai.py`、`llm/aliyun_llm.py` |
| Agent 人设 | `crewai_mas_demo/m2l3` | `m2l3_agent.py` |
| Task 契约 | `crewai_mas_demo/m2l4` | `m2l4_task.py` |
| Process 编排 | `crewai_mas_demo/m2l5` | `m2l5_crew.py` |
| 多模态 | `crewai_mas_demo/m2l6` | `m2l6_agent.py`、`tools/add_image_tool_local.py` |
| Hook 拦截和多租户路径 | `crewai_mas_demo/m2l8` | `m2l8_context.py`、`m2l8_tools_call.py` |
| MCP | `crewai_mas_demo/m2l9`、`14.MCP协议.../fastapi_mcpserver_base` | `m2l9_mcp.py`、MCP server docs |
| AIO-Sandbox | `crewai_mas_demo/m2l10` | `m2l10_sandbox.py` |
| Skills | `crewai_mas_demo/m2l16` | `m2l16_skills.py`、`skills/load_skills.yaml` |
| 上下文生命周期 | `crewai_mas_demo/m3l19` | `m3l19_context_mgmt.py` |
| 文件记忆 | `crewai_mas_demo/m3l20` | `m3l20_file_memory.py`、`workspace/*.md` |
| 搜索记忆 | `crewai_mas_demo/m3l21` | `indexer.py`、`m3l21_search_memory.py` |
| Orchestrator | `crewai_mas_demo/m4l23` | `m4l23_orchestrator.py` |
| 团队角色 | `crewai_mas_demo/m4l25` | `run_manager.py`、`run_dev.py` |
| 邮箱协作 | `crewai_mas_demo/m4l26` | `tools/mailbox_ops.py`、`main.py` |
| Human checkpoint | `crewai_mas_demo/m4l27` | `human_cli.py`、`main.py` |
| 自我进化 | `crewai_mas_demo/m4l28` | `log_query.py`、`schemas.py` |
| Observability | `crewai_mas_demo/m5l30` | `hook_framework/`、`shared_hooks/` |
| Reliability | `crewai_mas_demo/m5l31` | `cost_guard.py`、`loop_detector.py`、`retry_tracker.py` |
| Security | `crewai_mas_demo/m5l32` | `sandbox_guard.py`、`permission_gate.py` |

## 给未来 AI 的参考包组合

### 组合 A：最小新项目

适合：单一 AI Web/API、内部小工具、PoC。

```text
ai_engineering_design_playbook/
11.项目实战一：小红书爆款笔记/crewai_mas_demo_m2l7/
crewai_mas_demo/m2l3/
crewai_mas_demo/m2l4/
crewai_mas_demo/m2l5/
```

要求 AI：

- 复用 `agents.yaml` / `tasks.yaml` 思路。
- 保留 API / Service / Flow 分层。
- 不引入 Agent Team 和复杂 Hook，除非明确要求。

### 组合 B：企业工作助手

适合：飞书、企业微信、Slack、本地文件/浏览器/日历助手。

```text
ai_engineering_design_playbook/
17.Project2-Xiaopaw-feishu-assistant/xiaopaw/
crewai_mas_demo/m2l16/
crewai_mas_demo/m2l10/
```

要求 AI：

- 复用 Runner、InboundMessage、SessionManager、SkillLoaderTool。
- 执行能力走 Sandbox。
- 凭证不进 LLM 上下文。

### 组合 C：长期记忆助手

适合：个人助手、项目助手、知识工作助手。

```text
ai_engineering_design_playbook/
22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory/
crewai_mas_demo/m3l19/
crewai_mas_demo/m3l20/
crewai_mas_demo/m3l21/
```

要求 AI：

- 复用 `workspace-init/*.md` 四件套。
- 复用 Bootstrap、prune、compress、ctx/raw 分层。
- 记忆写入必须有准入和治理。
- search_memory 必须有用户/session/workspace 隔离。

### 组合 D：Agent Team

适合：多角色项目交付、产品/RD/QA 协作、长周期任务。

```text
ai_engineering_design_playbook/
29.Project4-Agent teams/xiaopaw-team/
22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory/
crewai_mas_demo/m4l26/
crewai_mas_demo/m4l27/
crewai_mas_demo/m4l28/
```

要求 AI：

- Manager 是唯一外部接口。
- 角色通过 mailbox 和 shared workspace 协作。
- 产物以路径引用传递。
- HITL 节点必须可审计。
- 自我进化必须通过 proposal 和审批。

### 组合 E：生产加固

适合：已有 AI 助手上线前加固，或企业级生产系统。

```text
ai_engineering_design_playbook/
33.Project5-xiaopaw with security enhancement/xiaopaw-v2/
22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory/
crewai_mas_demo/m5l30/
crewai_mas_demo/m5l31/
crewai_mas_demo/m5l32/
```

要求 AI：

- 先建立 Hook 事件体系，再加策略。
- 观测层和策略层分离。
- deny 必须可观测、可审计、可测试。
- SSOT 清单必须维护。
- E2E 覆盖安全、记忆、工具、路由、并发和成本风险。

## 给 AI 的使用指令模板

以后可以把下面这段放进任务提示词：

```text
请先阅读 ai_engineering_design_playbook/ 下的文档，作为方法论约束。
然后根据当前项目类型，额外参考以下 canonical projects / demos：

- {project_or_demo_path_1}
- {project_or_demo_path_2}
- {project_or_demo_path_3}

实现时必须遵守：
1. 不要脱离 playbook 自创架构。
2. 优先复用参考项目中的目录结构、模块边界、命名风格和测试分层。
3. 如果参考项目之间存在冲突，以当前项目阶段最接近的综合项目为准。
4. 不要把高阶段能力过早引入低阶段项目。
5. 对所有偏离参考项目的设计，说明原因和收益。
```

## 避免参考污染

| 风险 | 表现 | 处理 |
| --- | --- | --- |
| 参考过多 | AI 同时引入 Team、Memory、Hook，MVP 变臃肿 | 限制最多 1-3 个综合项目 |
| 阶段错配 | 简单 API 项目复刻 Project 5 全套加固 | 先判断项目阶段 |
| 只读 demo | 做出来像小脚本，不像工程项目 | 至少追加一个综合项目 |
| 只读 Project 5 | 过度安全和文档化，忽略基础业务 flow | 补 Project 1/2/3 |
| 只读 playbook | 方法论正确但代码风格漂移 | 追加 canonical project |

## 最终建议

长期保存这套参考策略：

```text
默认：
  playbook 7 文档

实现单助手：
  + Project 3

实现团队：
  + Project 3 + Project 4

实现生产级：
  + Project 3 + Project 5

实现生产级团队：
  + Project 3 + Project 4 + Project 5

具体机制不会写：
  + 对应 crewai_mas_demo 小节
```

这样可以让未来 AI 既知道“为什么这么设计”，也能看到“课程体系里真实项目长什么样”。
