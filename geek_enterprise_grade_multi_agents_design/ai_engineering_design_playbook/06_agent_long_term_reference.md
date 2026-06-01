# 06. Agent Long-Term Reference

本文件面向未来的 AI Agent。它把课程和项目中可迁移的规则整理成长期参考，便于 Agent 在新项目中复用结构、避免常见反模式。

## 总原则

1. 不要先写 prompt，先写任务契约。
2. 不要先上 Multi-Agent，先证明单 Agent 或 Workflow 不够。
3. 不要把所有工具暴露给模型，先做最小权限设计。
4. 不要把历史全塞上下文，先设计 Bootstrap、prune、compress 和 search。
5. 不要让 Agent 自己决定安全边界，安全要进入 Hook 和策略层。
6. 不要只看最终答案，必须记录过程、工具、成本、拒绝和异常。
7. 不要让系统上线后停止学习，Eval、Monitoring、Data Flywheel 要持续运行。

## 新项目启动顺序

当你接到一个新的企业级 AI 项目，请按顺序做：

```text
1. 判断 AI 适用性和 ROI
2. 写用户流、输入输出和验收标准
3. 选择 Prompt / Workflow / Single Agent / Multi-Agent
4. 定义 Agent 角色和 Task 契约
5. 设计工具、Skill、MCP、沙盒和权限
6. 设计 Runner、Session、Workspace、Bootstrap
7. 设计 Memory 和 Knowledge 检索
8. 设计 Observability、Guardrails、Eval、CI/CD
9. 再开始实现
```

## Agent 设计模板

```yaml
agent_name:
  role: "{行业/任务} 专家"
  goal: "{清晰目标}，优先级是 {质量/安全/成本/速度/可解释性}"
  backstory: |
    一、身份与背景
    - 你长期处理什么场景。
    - 你服务什么用户或业务。

    二、关键知识与理论
    - 你使用哪些框架、标准、方法。
    - 你如何判断好坏。

    三、工作方法与行为习惯
    - 你先做什么，再做什么。
    - 你如何处理中间结果。
    - 你如何和下游协作。

    四、行为边界
    - 你不做什么。
    - 哪些情况必须请求确认。
    - 哪些内容不得编造。
  verbose: true
  allow_delegation: false
```

检查：

- Role 是否具体，不是泛泛“专家”。
- Goal 是否包含优先级。
- Backstory 是否包含工作方法。
- 是否写了不做什么。
- 是否能和其他 Agent 区分职责。

## Task 设计模板

```yaml
task_name:
  agent: agent_name
  context:
    - upstream_task_name
  description: |
    你要完成：{任务目标}

    输入：
    1. {input_a}
    2. {input_b}

    约束：
    - 必须基于输入，不得编造。
    - 信息不足时输出 missing_info。
    - 工具失败时输出 error 字段和可恢复建议。
    - 大文件或长结果只引用路径和摘要。

    可用工具：
    - {tool_name}: {何时使用}
  expected_output: |
    输出必须是可解析 JSON，符合 {OutputModel}。
    不要使用 Markdown 代码块包裹 JSON。
```

检查：

- 输入变量是否显式。
- 输出结构是否可测试。
- 错误路径是否定义。
- 是否明确禁止编造。
- 是否说明何时用工具。

## Tool 设计清单

设计一个工具前，先回答：

| 问题 | 标准 |
| --- | --- |
| 这个工具是否语义完整？ | Agent 调一次就能完成一个自然动作 |
| 输入是否足够少？ | 参数越少越好，但不能让模型猜 |
| 输出是否足够瘦？ | 只返回决策需要的信息 |
| 错误是否可恢复？ | 错误要告诉 Agent 下一步怎么做 |
| 权限是否最小？ | 默认不开放危险能力 |
| 是否需要沙盒？ | 文件、代码、浏览器、外部系统写操作通常需要 |

工具描述模板：

```text
工具名：动词_名词
用途：在什么情况下使用
输入：每个参数的业务含义、默认值、边界
输出：字段说明和使用建议
错误：常见错误与恢复方式
权限：该工具能做什么、不能做什么
```

## Skill 设计清单

`SKILL.md` 适合保存经验、SOP 和复杂操作手册。

Skill frontmatter 建议：

```yaml
---
name: product_design
description: 当需要把需求转成产品设计文档时使用；提供结构、检查项和输出要求。
type: reference
---
```

正文建议：

```text
# Skill Name

## When To Use
说明触发条件。

## Core Principles
说明为什么这样做。

## Steps
只写关键步骤，不写无关背景。

## Output
说明产物格式。

## Common Pitfalls
列反模式。
```

区分：

| 类型 | 用法 |
| --- | --- |
| reference skill | Agent 读取后自己执行 |
| task skill | 构建 Sub-Crew 或脚本执行 |

## Memory 写入规则

只有满足以下条件才写长期记忆：

- 用户明确表达长期偏好。
- 项目产生稳定事实或决策。
- 某个错误多次出现，需要规则避免。
- 某个流程可复用，适合沉淀为 Skill。
- 记忆对未来任务有明确帮助。

不要写：

- 一次性闲聊。
- 未确认猜测。
- 敏感凭证。
- 完整 prompt。
- 大段工具输出。
- 已经过期或冲突的信息。

写入路径建议：

| 内容 | 位置 |
| --- | --- |
| 用户偏好 | `workspace/user.md` 或 `memory.md` |
| Agent 行为规则 | `workspace/agent.md` |
| 项目事实 | `workspace/shared/projects/{id}/` |
| 可复用 SOP | `skills/{name}/SKILL.md` |
| 历史检索材料 | 向量库 + 元数据 |

## Context 管理规则

每次 LLM 调用前：

1. 恢复必要 session。
2. 注入 Bootstrap。
3. 删除或摘要过长工具结果。
4. 压缩旧历史。
5. 保留最近关键轮次。
6. 确认 token 预算。

不要：

- 把 raw jsonl 全部塞回模型。
- 把图片、PDF、网页全文直接塞进 prompt。
- 把所有搜索结果原样返回给下游。
- 把不相关历史留在当前任务里。

## Workflow 设计规则

优先使用以下结构：

```text
固定流程：
  Task A -> Task B -> Task C

并发流程：
  Task A1 / A2 / A3 -> Summary -> Final

Orchestrator：
  Manager 规划 -> Sub-Agent 执行 -> Reviewer 验收 -> 汇总

团队：
  Manager -> PM -> RD -> QA -> Manager -> Human
```

选择标准：

| 情况 | 选择 |
| --- | --- |
| 步骤稳定 | Workflow |
| 路径不确定 | Single Agent |
| 可并行 | Parallel |
| 专业视角不同 | Multi-Agent |
| 长周期交付 | Agent Team |

## Team 协作规则

当项目使用 Agent Team 时，必须遵守：

- Manager 是唯一用户接口。
- 每个角色有独立 workspace 和 memory。
- 共享区只放项目产物、SOP、事件和共享 Skill。
- 角色之间通过 mailbox 通信。
- 邮件只传路径、状态和摘要，不复制长文档。
- 每条消息处理完必须 mark_done。
- 所有关键事件写 event log。
- 人类 checkpoint 必须可审计。
- 复盘改动必须有 evidence。

邮件类型建议：

```text
task_assign
task_done
review_request
review_done
clarification_request
clarification_answer
checkpoint_response
retro_trigger
retro_report
retro_approved
retro_rejected
retro_applied
error_alert
```

## Safety 规则

任何 Agent 都不能仅凭 prompt 获得以下能力：

- 读取任意文件。
- 执行任意 shell。
- 访问任意网络。
- 使用任意凭证。
- 搜索其他用户记忆。
- 修改自身核心规则。
- 绕过审批。

安全能力必须由工程层控制：

| 风险 | 控制 |
| --- | --- |
| 路径穿越 | SandboxGuard |
| 工具越权 | PermissionGate |
| 凭证泄漏 | Credential injection |
| 成本失控 | CostGuard |
| 无限循环 | LoopDetector |
| 高风险变更 | Human approval |
| 敏感日志 | PII mask |

## Observability 规则

必须记录：

- turn 开始和结束。
- LLM 调用摘要。
- tool call 输入摘要和结果摘要。
- 错误、deny、retry、timeout。
- 成本和 token。
- session end。
- 人类审批。
- 记忆写入。
- search_memory 命中来源。

不要记录：

- 明文凭证。
- 未脱敏 PII。
- 完整超长 prompt。
- 无必要的全量文件内容。

## Eval 规则

每个项目至少准备：

```text
evals/
  cases/
    happy_path.jsonl
    missing_info.jsonl
    tool_failure.jsonl
    memory_recall.jsonl
    safety_attack.jsonl
  judges/
    quality_judge.md
    safety_judge.md
  reports/
```

每个 eval case 应包含：

| 字段 | 说明 |
| --- | --- |
| id | 唯一编号 |
| input | 用户输入 |
| setup | 需要的文件、记忆、配置 |
| expected_behavior | 期望行为 |
| must_include | 必须包含 |
| must_not_include | 不得包含 |
| scoring | 评分方式 |

## 反模式速查

| 反模式 | 替代方案 |
| --- | --- |
| 超长万能 prompt | Agent + Task + Skill + Memory 分层 |
| 一个 Agent 做所有事 | 按专业、上下文、验收拆分 |
| 所有工具全开放 | SkillLoader + 权限白名单 |
| 工具返回完整原文 | 返回路径和摘要 |
| 无限制写 memory | 准入、分类、去重、GC |
| 冷启动上 RAG | 先文件记忆，再混合检索 |
| 用户充当消息总线 | Manager 单一接口 |
| 安全靠提示词 | Hook + Guardrail + Audit |
| 只做人工体验测试 | Unit + Integration + E2E + Eval |
| 上线后不看数据 | Monitoring + Data Flywheel |

## 开工前最终检查

在实现前，确认以下问题都有答案：

- 这个项目为什么需要 AI。
- 用户入口和主要工作流是什么。
- 成功和失败如何判断。
- 使用哪种架构范式。
- 有哪些 Agent，每个 Agent 不做什么。
- 每个 Task 的输出契约是什么。
- 哪些工具需要沙盒。
- 哪些能力适合 Skill。
- session 如何隔离。
- Bootstrap 从哪些文件构建。
- 记忆写入和搜索如何治理。
- 观测事件有哪些。
- 安全策略挂在哪个 hook。
- Eval case 覆盖哪些风险。
- CI/CD 如何阻止坏变更上线。

