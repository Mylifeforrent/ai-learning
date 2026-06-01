# 03. AI Engineering Design Methodology

本方法论面向企业级 AI 项目，核心思想是：不要把系统能力寄托在一个超长 prompt 上，而是用工程结构把模型包起来，让模型在清晰边界内推理、调用工具、写记忆、接受评估和持续改进。

## 1. 需求分析：先判断是否值得做 AI

对应课程：`34.How to evaluate scenario with high ROI`

设计 AI 项目前，先回答四类问题：

| 问题 | 判断标准 |
| --- | --- |
| 这个任务是否有足够不确定性？ | 如果规则代码能稳定解决，不需要 Agent |
| 这个任务是否有可观察价值？ | 能节省时间、提升质量、扩大规模或创造新体验 |
| 这个任务是否有可验收输出？ | 能定义 Ground Truth、人工验收标准或 LLM-as-Judge 标准 |
| 这个任务是否有可控风险？ | 数据、权限、成本、安全边界能被工程化控制 |

推荐使用 5 维评估：

| 维度 | 说明 |
| --- | --- |
| 业务价值 | 是否影响收入、效率、质量或用户体验 |
| AI 适配度 | 是否需要理解、生成、搜索、规划、工具调用 |
| 可评测性 | 是否能构建 eval case 和验收标准 |
| 风险可控性 | 是否能限制权限、数据和外部动作 |
| 迭代空间 | 是否有线上反馈和数据飞轮 |

结论分三档：

| 档位 | 行动 |
| --- | --- |
| 高 ROI | 进入原型和工程设计 |
| 中 ROI | 先做局部自动化或 Workflow，不急于 Agent 化 |
| 低 ROI | 保持人工流程或传统软件方案 |

## 2. 场景建模：先建用户流和输入输出

对应课程：`35.Prototype-requirement to evaluable demo`

先定义三件事：

| 问题 | 产物 |
| --- | --- |
| Who | 用户是谁，使用入口在哪里，谁负责验收 |
| What | AI 输出什么，调用什么工具，改变什么系统状态 |
| How good | 什么叫好，什么叫失败，如何打分 |

场景建模建议输出：

```text
scenario/
  user_story.md
  workflow.md
  input_output_contract.md
  acceptance_criteria.md
  risk_notes.md
  eval_cases_seed.md
```

关键原则：

- 先写用户旅程，再写 Agent。
- 先定义输出契约，再写 prompt。
- 先定义失败样例，再做自动化。
- 先设计验收标准，再做多 Agent 拆分。

## 3. 架构范式选择：Prompt、Workflow、Agent、Multi-Agent

对应课程：`2.AI_Application_Design_Pattern`、`5.AI应用开发工具选型`

| 范式 | 适用场景 | 不适合 |
| --- | --- | --- |
| Prompt Engineering | 单轮、低风险、少工具、输出宽松 | 多步骤、强一致性、可追踪要求高 |
| Workflow | 步骤确定、依赖清晰、可流程化 | 高不确定探索、多工具自由组合 |
| Single Agent | 目标清晰但路径不确定，需要工具探索 | 超长任务、多角色知识冲突 |
| Multi-Agent | 需要专业分工、上下文隔离、并行、互审 | 简单任务，或团队协议尚未设计 |

C.U.P. 决策：

| 维度 | 问法 | 影响 |
| --- | --- | --- |
| Complexity | 任务复杂度多高 | 决定是否拆 workflow / multi-agent |
| Uncertainty | 路径不确定性多高 | 决定是否需要 Agent 自主规划 |
| Performance Constraints | 延迟、成本、稳定性要求多高 | 决定是否收缩 Agent 自由度 |

默认建议：

1. 能用普通代码解决的，不要上 Agent。
2. 能用 Workflow 解决的，不要直接上 Multi-Agent。
3. 能用单 Agent 解决的，不要提前建 Agent Team。
4. 当上下文污染、角色冲突、执行成本、质量验收成为瓶颈时，再拆分多 Agent。

## 4. Agent 角色拆分

对应课程：`8.定义Agent：人设设定`、`25.Team Role...`

Agent 设计使用 RGB 模型：

| 要素 | 作用 | 写法 |
| --- | --- | --- |
| Role | 激活模型知识域 | “你是资深...”但要具体到行业和任务 |
| Goal | 定义决策偏好 | 说明优先级，例如质量优先、成本优先、安全优先 |
| Backstory | 行为边界和经验背景 | 写工作方法、知识框架、反模式、不做什么 |

拆分角色时不要按“人类组织头衔”硬拆，而按工程收益拆：

| 需要拆分的信号 | 推荐拆法 |
| --- | --- |
| 上下文过长 | 拆成独立 Crew 或 Sub-Agent |
| 专业标准冲突 | 拆为不同角色并做互审 |
| 可并行任务多 | 拆出并行执行角色 |
| 需要验收 | 独立验收 Agent |
| 需要对外接口 | Manager 作为单一接口 |

角色设计反模式：

- 一个 Agent 同时负责需求、执行、验收和复盘。
- Backstory 只有人设，没有行为边界。
- 多个 Agent 技能高度重复，导致记忆污染。
- 没有 Manager 或协议，用户变成消息总线。

## 5. Task 与输出契约

对应课程：`9.定义Task：设定契约`

Task 是 AI 工程里最小的交付契约。每个 Task 至少定义：

| 字段 | 作用 |
| --- | --- |
| description | 输入、背景、约束、不得编造内容 |
| expected_output | 输出结构、格式、验收标准 |
| context | 依赖哪些上游 Task |
| output model | Pydantic 或 JSON schema |
| failure behavior | 工具失败、信息不足、权限不足时怎么返回 |

推荐模式：

```text
tasks.yaml
  task_name:
    agent: role_name
    context: [...]
    description: |
      输入变量:
      - {input_a}
      - {input_b}
      约束:
      - 不得编造
      - 信息不足要显式说明
    expected_output: |
      必须输出可解析 JSON，字段符合 XxxOutput
```

关键原则：

- 不要让 Task 同时控制太多步骤。
- 不要把内部思考当作最终输出。
- 结构化输出必须能被测试解析。
- 对外输出和中间产物要分离。

## 6. Tool / Function / MCP / Skill 设计

对应课程：`12`、`13`、`14`、`15`、`16`

工具设计从 API 思维升级为 Agent-Native 思维：

| 设计点 | API 工具常见问题 | Agent-Native 做法 |
| --- | --- | --- |
| 粒度 | 太原子，Agent 要拼很多步 | 聚合成语义完整动作 |
| I/O | 返回噪音太多 | 只返回决策所需字段 |
| 错误 | 只给状态码 | 给可恢复建议 |
| 参数 | 名称面向程序员 | 描述面向模型决策 |
| 权限 | 默认全开放 | 最小权限、白名单、沙盒 |

工具分层建议：

| 类型 | 适合内容 | 示例 |
| --- | --- | --- |
| Python Tool | 轻量、确定性、低风险、直接被主 Agent 调用 | 中间结果保存、读 inbox、发内部邮件 |
| MCP Tool | 外部系统能力标准化 | 文件、浏览器、邮件、企业 API |
| Reference Skill | 给 Agent 阅读的说明书、SOP、规范 | 产品设计 SOP、工作区规则 |
| Task Skill | 需要独立执行上下文的复杂任务 | PDF 解析、网页浏览、代码生成 |
| Hook Strategy | 与业务无关的横切控制 | 权限、审计、成本、循环检测 |

## 7. Workflow 编排

对应课程：`4`、`11`、`23`

Workflow 先分三类：

| 类型 | 适用 |
| --- | --- |
| Sequential | 输出依赖上一步结果 |
| Parallel + Summary | 多输入独立处理后汇总 |
| Orchestrator | 主 Agent 动态拆任务、委派、验收 |

设计流程时优先传路径或结构化摘要，不传长全文：

```text
bad:
  Agent A 把全部原文塞给 Agent B

good:
  Agent A 写 output/report.md
  Agent B 读取路径并只抽取所需段落
```

流程拆分标准：

| 信号 | 动作 |
| --- | --- |
| 上游结果可复用 | 写到文件或 structured artifact |
| 下游只需要摘要 | 先 summary，不传 raw |
| 多分支互不依赖 | 并行执行 |
| 结果需要质量控制 | 增加 reviewer 或验收 Task |
| 需要人类确认 | 插入 checkpoint，不要让 Agent 继续猜 |

## 8. Memory 设计

对应课程：`18`、`19`、`20`、`21`、Project 3

记忆不是“把历史全塞进去”，而是回答三个问题：

| 问题 | 机制 |
| --- | --- |
| 当前轮必须知道什么 | Bootstrap |
| 当前轮不该带什么 | prune / compress |
| 需要时再找什么 | search_memory / RAG |

推荐三层记忆：

| 层 | 内容 | 存储 |
| --- | --- | --- |
| L1 工作区文件 | 身份、用户、规则、记忆索引、项目文件 | `workspace/*.md` |
| L2 会话上下文 | ctx 快照、清洁历史、raw trace | `data/ctx/`、`data/sessions/` |
| L3 搜索记忆 | 摘要、chunk、embedding、元数据 | pgvector 或其他向量/全文混合索引 |

写记忆要有准入：

| 内容 | 写到哪里 |
| --- | --- |
| 用户长期偏好 | `memory.md` 或用户 profile |
| 项目事实和决策 | 项目工作区 |
| 可复用流程 | `SKILL.md` |
| 短期对话 | session history |
| 可搜索历史 | indexer 入库 |

反模式：

- 冷启动就上复杂 RAG。
- 向量库里塞没有治理的长文本。
- Agent 无限制追加 memory。
- 同一事实多条冲突记忆并存。
- 把凭证、隐私、完整 prompt 写入长期记忆。

## 9. Knowledge / RAG 设计

对应课程：`21.Memory system...`

RAG 是搜索系统，不只是向量搜索。推荐混合检索：

| 检索方式 | 适合 |
| --- | --- |
| grep / 全文扫描 | 小规模、确定关键词 |
| 结构化字段搜索 | 有时间、用户、项目、类型等元数据 |
| 向量语义搜索 | 模糊表达、上次那个、相似主题 |
| 混合检索 | 企业级长期记忆和知识库 |

chunk 设计优先于模型选型：

- 按语义边界切，不按固定字符硬切。
- chunk 保留来源、时间、用户、项目、类型。
- 支持幂等写入和增量更新。
- 搜索 Skill 要说明降级策略。
- 检索结果要压缩成下游可用摘要。

## 10. Guardrails / 安全设计

对应课程：`31`、`32`、Project 5

安全不能只靠 prompt，应分三层：

| 层 | 目标 | 工程实现 |
| --- | --- | --- |
| 沙箱 | 限制执行环境 | AIO-Sandbox、路径限制、网络限制 |
| 权限网关 | 限制可用工具 | PermissionGate、tool allowlist、role policy |
| 身份与凭证 | 限制谁能做什么 | credential injection、审计、API key、routing_key 隔离 |

关键策略：

- 凭证不进 LLM 上下文。
- 工具 schema 不暴露敏感参数。
- BEFORE_TOOL_CALL 做确定性检查。
- 被 deny 的请求也要进入审计和 trace。
- 人类审批只放在高风险节点，不制造审批疲劳。
- 所有安全策略必须有测试用例。

## 11. Observability / 日志 / 调试

对应课程：`30`、`38`

推荐统一到 5+2 事件：

| 事件 | 用途 |
| --- | --- |
| BEFORE_TURN | 记录用户输入、session、routing_key |
| BEFORE_LLM | 记录模型调用上下文摘要 |
| BEFORE_TOOL_CALL | 记录工具调用意图，可做策略 gate |
| AFTER_TOOL_CALL | 记录工具结果、耗时、错误 |
| AFTER_TURN | 记录最终响应、成本、状态 |
| TASK_COMPLETE | 记录任务级完成情况 |
| SESSION_END | flush、审计、尾采样 |

观测分层：

| 层 | 指标 |
| --- | --- |
| 系统层 | CPU、内存、队列、延迟、错误率 |
| 成本层 | token、单次成本、预算消耗率 |
| Agent 执行层 | turn、tool call、retry、loop、deny |
| 质量层 | eval score、self_score、用户修正 |
| 业务层 | 完成率、转化率、节省时间 |
| 安全合规层 | PII、权限拒绝、审计事件 |

## 12. Harness / CI/CD / 工程化

对应课程：`18`、`37`、Project 5

Harness 是包在 LLM 外面的工程外壳，负责：

- 接入外部消息。
- 统一内部消息模型。
- 管理 session 和 routing_key。
- 注入 Bootstrap。
- 裁剪和压缩上下文。
- 路由 Skill 和 Tool。
- 隔离沙盒执行。
- 写入记忆和索引。
- 上报日志、指标和 trace。
- 执行安全和可靠性策略。

AI CI/CD 与传统 CI/CD 的不同点在于版本对象更多：

| 版本对象 | 示例 |
| --- | --- |
| 代码 | Python 模块、API、Runner |
| Prompt / Agent 配置 | `agents.yaml`、`tasks.yaml`、`agent.md` |
| Skills | `SKILL.md`、脚本、load_skills.yaml |
| Memory / Knowledge | `memory.md`、向量索引、知识库 |
| Eval cases | 测试集、judge prompt、bad cases |
| Model / runtime | 模型名、temperature、context window、sandbox 镜像 |

CI gate 建议：

1. 静态规则检查。
2. 单元测试。
3. 关键 workflow 回归。
4. Eval 回归。
5. 成本与性能检查。
6. 安全扫描。
7. 人工审核高风险变更。

## 13. 测试与评估

对应课程：`36`、Project 5 `tests/`

测试分层：

| 层 | 测什么 |
| --- | --- |
| Unit | 工具、schema、解析、权限、hook handler |
| Integration | Runner、Session、SkillLoader、Memory、Sandbox |
| E2E | 用户入口到最终回复 |
| Eval | 输出质量、行为模式、事实性、安全性 |
| Regression | 已知 bad case 不复发 |

Eval 四环节：

1. 建设评测集。
2. 执行被测系统。
3. 打分，规则、人类或 LLM-as-Judge。
4. 汇总结论，产出 bad case 和改进项。

验收标准必须覆盖：

- 正常路径。
- 信息不足。
- 工具失败。
- 权限拒绝。
- 超时。
- 成本超限。
- 多轮上下文。
- 记忆召回。
- 安全攻击。

## 14. 部署与运维

部署时至少设计：

| 项目 | 要求 |
| --- | --- |
| 配置 | `.env` 注入凭证，`config.yaml` 存非密配置 |
| 健康检查 | `/health` 或 metrics server |
| 指标 | Prometheus / Langfuse / structured log |
| 数据 | workspace、sessions、ctx、vector db 的备份策略 |
| 沙盒 | 镜像版本、挂载目录、权限、网络 |
| 灰度 | feature flag、模型切换、prompt 版本 |
| 回滚 | 代码、配置、Skill、Memory、索引的回滚路径 |
| 合规 | PII 脱敏、审计日志、凭证轮换 |

上线后用数据飞轮持续迭代：

```text
线上行为和反馈
  -> 信号采集
  -> bad case 聚类
  -> 定位 prompt / tool / memory / workflow / safety 问题
  -> 生成修复方案
  -> Eval 和 CI/CD gate
  -> 灰度上线
```

## 15. 最小可用到生产级的推进节奏

| 阶段 | 目标 | 不做什么 |
| --- | --- | --- |
| MVP | 单任务闭环可用，输出可验收 | 不急于团队化和复杂 RAG |
| Tools | 接入真实工具和沙盒 | 不暴露全量权限 |
| Context | 管理 session、Bootstrap、剪枝压缩 | 不把历史全塞 prompt |
| Memory | 保存偏好、项目事实、可搜索历史 | 不允许无治理追加 |
| Teams | 建角色、邮箱、共享区和 HITL | 不让用户当消息总线 |
| Stability | Hook、Guardrails、Eval、CI/CD、Monitoring | 不把安全写成提示词承诺 |

