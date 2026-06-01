# 05. Harness Engineering Practices

Harness 是课程中最值得迁移的工程思想：LLM 只是推理核心，真正的 AI 系统是围绕它建立的一整套运行环境。这个环境负责接入、隔离、上下文、工具、记忆、安全、观测和评估。

## Harness 的定义

可以把 Harness 理解为：

```text
用户入口
  -> 标准消息
  -> 会话隔离
  -> 上下文构建
  -> Agent 推理
  -> 工具路由
  -> 沙盒执行
  -> 记忆写入
  -> 结果发送
  -> 日志、指标、评测、安全策略
```

课程里的 XiaoPaw 项目说明了一个重要原则：不要让业务入口、工具执行、记忆和安全逻辑互相缠绕。它们应该通过 Harness 分层组合。

## 1. 统一入口和内部消息模型

参考：Project 2/3 的 `InboundMessage`、`Runner`

外部入口可以很多：

- 飞书 WebSocket。
- TestAPI。
- Cron 定时任务。
- CLI。
- 后台事件。

但进入系统后应统一为一个内部消息：

```text
InboundMessage
  routing_key
  content
  msg_id
  root_id
  sender_id
  timestamp
  attachment
  is_cron
```

收益：

| 收益 | 说明 |
| --- | --- |
| 入口解耦 | 新增平台时不改 Agent |
| 会话一致 | 所有入口都能复用 session 逻辑 |
| 测试简单 | TestAPI 可模拟真实入口 |
| 安全统一 | 权限、速率、审计可统一挂载 |

## 2. routing_key 与 Session 隔离

参考：Project 2/3 的 `feishu/session_key.py`、`session/manager.py`

推荐 routing_key 规则：

```text
p2p:{user_id}
group:{chat_id}
thread:{chat_id}:{thread_id}
cron:{job_id}:{target}
team:{role}:{workspace_id}
```

每个 routing_key 应有独立队列：

- 同一路由串行处理，避免历史乱序。
- 不同路由并发处理，提升吞吐。
- session_id 与 routing_key 映射持久化。
- routing_key 不得由模型覆盖。

## 3. Bootstrap：给 Agent 一个可编辑起点

参考：课程 19、Project 3 `memory/bootstrap.py`

Bootstrap 的目标不是塞越多越好，而是给模型一个稳定导航骨架：

```xml
<soul>
身份、风格、长期原则
</soul>

<user_profile>
用户偏好、工作方式、长期约束
</user_profile>

<agent_rules>
工具使用规则、记忆规则、SOP 入口
</agent_rules>

<memory_index>
长期记忆索引摘要
</memory_index>
```

实践建议：

- `soul.md` 写身份和风格。
- `user.md` 写用户长期偏好。
- `agent.md` 写行为规则和工具使用原则。
- `memory.md` 写索引，不写完整历史。
- Bootstrap 只取必要片段，例如 memory 前 200 行。
- 文件更新后下轮自动生效，避免把规则写死在代码里。

## 4. 上下文生命周期：restore、prune、compress、save

参考：课程 19、`crewai_mas_demo/m3l19`

上下文生命周期建议分四步：

| 阶段 | 目标 | 实现 |
| --- | --- | --- |
| restore | 恢复必要历史 | 从 ctx.json 和清洁历史加载 |
| prune | 删除低价值工具结果 | 对长 tool output 做摘要或路径替换 |
| compress | 压缩旧历史 | 超过阈值后生成摘要 |
| save | 保存本轮上下文 | 写 ctx 快照和 raw jsonl |

关键实现原则：

- `before_llm_call` 要 in-place 修改 messages。
- raw 日志和干净历史分开存。
- 工具大输出优先落文件，消息里只留路径和摘要。
- 压缩阈值和保留轮数要配置化。
- token 计数优先使用模型 tokenizer，失败时降级粗估。

## 5. SkillLoader：渐进式披露

参考：课程 16、Project 2/3 `tools/skill_loader.py`

SkillLoader 解决两个问题：

1. 主 Agent 不应一次性看到所有工具手册。
2. 复杂任务应在独立上下文中执行。

推荐两阶段加载：

```text
启动时：
  读取 load_skills.yaml
  注入 name + description + type

调用时：
  读取完整 SKILL.md
  reference skill -> 返回说明书
  task skill -> 构建 Sub-Crew，在沙盒执行
```

Skill 类型：

| 类型 | 行为 |
| --- | --- |
| reference | 只返回知识、SOP、规范，主 Agent 自己执行 |
| task | 创建临时专家 Agent / Sub-Crew，调用 MCP / Sandbox 完成任务 |

治理建议：

- `SKILL.md` 保持单一职责。
- description 要包含触发条件、能力、产出。
- 超过 500 行应拆分。
- 引用链不要超过两层。
- 外部来源 Skill 要审查。

## 6. Sub-Crew 与沙盒执行

参考：课程 15/16、Project 2/3

适合进入 Sub-Crew 的任务：

- 文件解析。
- 网页浏览。
- 代码运行。
- 多步骤工具操作。
- 需要独立上下文的长任务。

沙盒原则：

| 原则 | 做法 |
| --- | --- |
| 最小挂载 | 只挂载任务所需目录 |
| 凭证隔离 | 凭证写入沙盒配置，不进入 prompt |
| 工具白名单 | task skill 只能看到需要的 MCP tools |
| 输出路径化 | 大结果写文件，主 Agent 读取路径 |
| 超时控制 | Sub-Crew 运行必须有 timeout |

## 7. 文件系统记忆

参考：课程 20、Project 3

文件记忆分两类：

| 类型 | 内容 | 工具 |
| --- | --- | --- |
| 语义记忆 | 用户偏好、事实、项目规则 | `memory-save` |
| 程序记忆 | 可复用 SOP、流程、操作手册 | `skill-creator` 或 `skill_crystallize` |

`memory-save` 四步：

1. 准入控制：判断是否值得长期保存。
2. 分类路由：决定写到用户、项目、主题还是全局。
3. 写入前检查：避免重复和冲突。
4. 更新或追加：优先更新旧事实，而不是无限追加。

记忆治理：

- 定期 GC。
- 合并重复事实。
- 标记过期信息。
- 删除敏感内容。
- 将成熟流程沉淀为 Skill。

## 8. 搜索记忆与知识库

参考：课程 21、Project 3

索引流水线：

```text
session raw
  -> 清洗
  -> 摘要
  -> chunk
  -> embedding
  -> 写入 pgvector + 元数据
```

搜索策略：

| 查询类型 | 策略 |
| --- | --- |
| 精确事实 | 关键词 / 字段过滤 |
| 历史表达模糊 | 向量搜索 |
| 企业项目检索 | 向量 + 标量混合 |
| 失败降级 | 返回全文 grep 或提示未索引 |

最佳实践：

- 写入异步化，不阻塞用户回复。
- 索引要幂等。
- search_memory 由 Agent 按需调用，不要每轮自动检索。
- 检索结果要带来源和时间。
- 对跨用户、跨 workspace 查询做强隔离。

## 9. Agent Teams Harness

参考：课程 24-28、Project 4

团队 Harness 由四部分组成：

| 组成 | 作用 |
| --- | --- |
| role workspace | 每个角色独立 soul / agent / memory / skills |
| shared workspace | 项目文档、SOP、事件和共享 skill |
| mailbox | 结构化异步消息 |
| event log | 审计、复盘、进度追踪 |

团队协议示例：

- Manager 是唯一外部接口。
- PM/RD/QA 不直接联系用户。
- 每次唤醒先识别 project_id。
- 每次读 inbox 后处理消息并 mark_done。
- task_done 只传路径和 self_score，不复制长文档。
- 收到 retro_approved 后做机械替换，不重新判断。

## 10. Human Checkpoint

参考：课程 27、Project 4

人类介入点建议只放在高风险节点：

| 节点 | 目的 |
| --- | --- |
| 需求确认 | 防止方向错 |
| 方案确认 | 防止关键设计风险 |
| 高风险执行 | 防止外部副作用 |
| 复盘改动 | 防止 Agent 自改过度 |

原则：

- 人类在循环之上，不在每一步循环中。
- Manager 统一联系人类。
- 介入必须有审计记录。
- 审批分级，避免审批疲劳。
- 任何拒绝都要转成可执行反馈。

## 11. Hook Framework

参考：课程 30-32、Project 5

Hook 框架用于横切能力：

```text
HookRegistry
  dispatch      -> 观测类 handler，fire-and-forget
  dispatch_gate -> 策略类 handler，可 deny

HookLoader
  读取 shared_hooks/hooks.yaml
  加载 handler 和 strategy

CrewAdapter
  将 CrewAI 生命周期映射为 5+2 事件
```

事件设计：

| 事件 | 应挂载内容 |
| --- | --- |
| BEFORE_TURN | trace_id、routing_key、输入摘要 |
| BEFORE_LLM | prompt 摘要、token 预算 |
| BEFORE_TOOL_CALL | 权限、安全、审计、工具 trace |
| AFTER_TOOL_CALL | 工具结果、错误、耗时、loop 检测 |
| AFTER_TURN | 成本、最终状态、质量信号 |
| TASK_COMPLETE | 任务级汇总 |
| SESSION_END | flush、尾采样、审计收尾 |

## 12. 可靠性策略

参考：课程 31

| 策略 | 触发点 | 行为 |
| --- | --- | --- |
| retry_tracker | AFTER_TOOL_CALL | 统计重试、限制最大次数 |
| loop_detector | AFTER_TOOL_CALL / AFTER_TURN | 对重复状态 hash 触发 deny |
| cost_guard | BEFORE_TOOL_CALL / AFTER_TURN | 实时预算检查，超限阻断 |

实践建议：

- Agent 场景重试最多 2-3 次，特殊情况单独配置。
- loop 检测应区分工具输入 hash 和结果 hash。
- 成本必须实时算，不只事后统计。
- 被阻断要给用户可理解解释。

## 13. 安全策略

参考：课程 32、Project 5

安全策略建议挂到 BEFORE_TOOL_CALL：

| 策略 | 检查 |
| --- | --- |
| sandbox_guard | 路径穿越、命令注入、环境变量读取、危险 shell 模式 |
| permission_gate | 当前角色是否允许调用该工具 |
| credential_inject | 执行时注入凭证，schema 和 prompt 不暴露 |
| audit_logger | 记录 allow / deny / ask / error |

安全红线：

- 不让模型决定自己能不能越权。
- 不把凭证当参数交给模型。
- 不把未知来源内容直接作为工具指令。
- 不让 task skill 获得不必要工具。
- 不让不同 routing_key 的记忆互相搜索。

## 14. Observability 与 Monitoring

参考：课程 30、38

最低观测要求：

| 项 | 说明 |
| --- | --- |
| trace_id | 贯穿 turn、tool、LLM、sender |
| structured log | JSON，便于搜索和聚合 |
| metrics | 请求量、错误、延迟、token、成本、deny |
| Langfuse / Trace | 查看 Agent 思考路径和工具链路 |
| audit log | 安全事件、权限拒绝、人类确认 |

监控指标六层：

1. 系统层。
2. 成本层。
3. Agent 执行层。
4. 质量层。
5. 业务层。
6. 安全合规层。

## 15. Eval 与 CI/CD

参考：课程 36-37

AI 系统 CI/CD 应检查：

- 代码单测。
- Prompt / Skill 静态规则。
- 核心 workflow 回归。
- 历史 bad case 回归。
- LLM-as-Judge 质量评分。
- 成本和延迟阈值。
- 安全攻击样例。
- 文档和 SSOT 一致性。

推荐 gate：

```text
fast checks:
  lint / unit / static prompt rules / schema tests

medium checks:
  integration / memory / tool sandbox / hook chain

slow checks:
  e2e / eval / security attack / cost regression

manual checks:
  high-risk prompt, skill, memory, permission changes
```

## 16. Data Flywheel

参考：课程 39

上线不是结束，真正的 AI 工程需要数据飞轮：

```text
用户行为
  -> 显式反馈 / 隐式信号
  -> bad case 聚类
  -> 定位问题类型
  -> 修复 prompt / tool / memory / workflow / safety
  -> Eval 回归
  -> CI/CD gate
  -> 灰度发布
```

信号分类：

| 信号 | 示例 |
| --- | --- |
| 显式 | 点赞、差评、人工修改、用户纠错 |
| 隐式 | 反复追问、撤回、超时、跳出、工具失败 |
| 系统 | token 超限、循环、deny、retry |
| 业务 | 完成率、节省时间、转化、留存 |

## 17. Harness 自检清单

- 外部入口是否已统一为内部消息。
- routing_key 是否强隔离。
- 同一 session 是否串行处理。
- Bootstrap 是否从可编辑文件构建。
- 上下文是否有 prune / compress / save。
- 大工具结果是否用路径传递。
- Skill 是否渐进式披露。
- task skill 是否沙盒执行。
- 记忆写入是否有准入和治理。
- search_memory 是否按需触发并隔离。
- Hook 是否覆盖 5+2 事件。
- deny 是否可观测、可审计、可测试。
- Eval 和 CI/CD 是否覆盖 prompt、skill、memory、model 变更。

