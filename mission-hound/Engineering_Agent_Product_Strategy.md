# Engineering Agent Product Strategy

> 本文档沉淀一个面向日常研发工作的 Agent 产品构想，覆盖需求分析、任务拆解、Jira/Confluence 自动化、测试自动化、性能/压力测试、Health Checking、Production Support、Issue Investigation 和 Email Draft 等能力。

## 1. 核心判断

这些需求适合做成一个面向研发团队的 Agent 产品，但不建议做成一个不可控的“万能聊天机器人”。

更合适的产品形态是：

```text
Primary Agent + Skills + MCP Tool Layer + Multi-Agent Collaboration + Workflow + Human Approval
```

也就是说：

- Agent 负责理解目标、规划任务、协调工具、生成交付物。
- Skills 负责把特定领域能力模块化，例如需求分析、Jira 创建、测试生成、事故排查。
- MCP 负责连接 Jira、Confluence、GitHub、Gmail、监控平台、日志系统等外部工具。
- Workflow 负责稳定执行、状态流转、失败重试、审计和人工审批。
- Multi-Agent 负责在复杂任务中拆分角色，例如 PM Agent、QA Agent、SRE Agent、Doc Agent。

这个产品不应该只是一个聊天框，而应该是一个带任务状态、产物管理、审批记录、证据链和工具调用记录的研发工作台。

## 2. 产品定位

推荐定位：

```text
从需求到交付的研发执行 Agent
```

或者：

```text
Engineering Operations Agent Platform
```

它的核心对象不是一段对话，而是一个 Work Mission。

例如：

```text
Mission: 实现支付失败重试能力

- Requirement Summary
- Jira Plan
- Confluence Design Page
- Test Plan
- UI/API Test Cases
- Performance Test Plan
- Release Checklist
- Health Checks
- Production Runbook
- Incident Investigation Notes
- Email/Status Updates
```

每个 Mission 下沉淀：

- 用户输入和需求上下文
- Agent 分析过程
- 生成的工程 artifacts
- Jira/Confluence/GitHub 等外部系统链接
- 工具调用记录
- 审批记录
- 执行结果
- 人工反馈
- 后续迭代历史

## 3. 需求可行性拆解

| 需求场景 | Agent 化可行性 | 说明 |
| --- | --- | --- |
| 需求分析 | 高 | LLM 擅长阅读、归纳、补充问题、提炼用户故事和验收标准。 |
| 任务拆解 | 高 | 可以基于需求生成 Epic、Story、Sub-task、技术任务和测试任务。 |
| Jira 创建 | 高 | 适合通过 MCP/API 创建草稿或正式 issue，但建议加入人工审批。 |
| Confluence Page 准备 | 高 | 适合生成设计文档、会议纪要、测试计划、Runbook、RCA。 |
| UI 测试自动化 | 中高 | Agent 负责编排和生成测试，执行层交给 Playwright、Stagehand、TestZeus 等。 |
| API 测试自动化 | 高 | 可从接口定义、用户故事、日志样本生成测试用例和 mock。 |
| 性能测试 | 中高 | Agent 可生成 k6/Locust/JMeter 脚本并分析结果，但执行和指标采集应工具化。 |
| 压力测试 | 中 | 可自动准备脚本和报告，但生产压测需要权限、窗口期和审批。 |
| Health Checking 自动化 | 高 | 适合生成检查项、配置探针、分析健康状态、汇总异常。 |
| Production Support | 中高 | 适合做调查、总结、建议和草稿，不建议早期直接自动修复生产。 |
| Issue Investigation | 高 | 可以读取日志、trace、metrics、部署记录、PR 历史，生成根因假设和排查路径。 |
| Email 填写助手 | 高 | 适合生成邮件草稿、状态更新、事故通知、测试完成说明，但发送动作建议审批。 |

## 4. 推荐 MVP 范围

第一版不建议覆盖所有需求。建议先做一个有价值且可控的闭环：

### 4.1 Requirement Intake Agent

输入：

- PRD
- 会议纪要
- 邮件
- Slack/Teams 消息
- 用户口述需求
- 现有 Confluence 文档

输出：

- 需求摘要
- 用户故事
- 验收标准
- 业务流程
- 关键风险
- 待澄清问题
- 非功能性需求候选项

### 4.2 Task Breakdown & Jira Agent

能力：

- 将需求拆解为 Epic、Story、Sub-task、Bug、Test Task。
- 自动生成标题、描述、验收标准、优先级建议、依赖关系。
- 支持创建 Jira 草稿。
- 支持人工确认后批量创建。

建议：

- 早期不要默认自动创建正式 Jira issue。
- 先做 preview + approve。

### 4.3 Confluence Page Agent

能力：

- 生成需求分析页。
- 生成技术设计页。
- 生成测试计划页。
- 生成发布说明。
- 生成 Runbook。
- 生成 RCA 模板。

建议：

- Confluence 也先做 draft。
- 页面模板要产品化，不要只靠 prompt。

### 4.4 QA Automation Agent

能力：

- 根据验收标准生成测试计划。
- 生成 UI 测试用例。
- 生成 Playwright 测试脚本。
- 生成 API 测试用例。
- 识别边界条件和回归范围。
- 分析测试失败日志。

执行层：

- Playwright
- Stagehand
- TestZeus Hercules
- promptfoo

### 4.5 Production Investigation Agent

能力：

- 读取告警内容。
- 查询日志、指标、trace、最近部署、相关 PR。
- 总结影响范围。
- 生成根因假设。
- 推荐下一步排查命令。
- 生成 incident update。
- 生成 RCA 草稿。

建议：

- 初期只做 investigation 和 recommendation。
- 修复动作、扩容动作、回滚动作必须 human approval。

## 5. Agent 架构建议

推荐架构：

```text
User / PM / Dev / QA / SRE
        |
Engineering Agent Console
        |
Primary Orchestrator Agent
        |
Skills Registry
  - requirement-analysis
  - jira-planning
  - confluence-doc
  - ui-test
  - api-test
  - perf-test
  - health-check
  - incident-investigation
  - email-draft
        |
MCP / Tool Layer
  - Jira MCP
  - Confluence MCP
  - GitHub/GitLab MCP
  - Google Workspace/Gmail MCP
  - Browser Automation
  - Observability APIs
  - Test Runners
        |
Execution + Audit + Approval
```

### 5.1 Primary Orchestrator Agent

职责：

- 理解用户目标。
- 判断任务类型。
- 调用合适的 Skill。
- 规划执行步骤。
- 管理上下文和状态。
- 判断是否需要人工审批。
- 汇总结果。

### 5.2 Skills Registry

每个 Skill 应该包含：

- 适用场景
- 输入 schema
- 输出 schema
- 可调用工具
- 风险等级
- 是否需要审批
- 测试集
- 示例任务

示例：

```yaml
skill: jira-planning
description: Convert requirement analysis into Jira issue drafts.
inputs:
  - requirement_summary
  - acceptance_criteria
  - target_project
outputs:
  - epic_draft
  - story_drafts
  - subtask_drafts
tools:
  - jira.search
  - jira.create_issue
approval_required:
  - jira.create_issue
risk_level: medium
```

### 5.3 MCP Tool Layer

MCP 适合作为工具连接层，原因：

- 工具接口标准化。
- Agent 框架可复用。
- 方便给不同外部系统做权限控制。
- 便于审计每一次工具调用。
- 适合企业内部扩展私有系统。

优先支持的 MCP：

- Jira
- Confluence
- GitHub/GitLab
- Google Workspace/Gmail
- Slack/Teams
- Browser
- Observability
- Database Read-only
- CI/CD

### 5.4 Workflow Layer

Workflow 不应该完全被 Agent 替代。

Agent 适合做判断和生成，Workflow 适合做可靠执行。

典型流程：

```text
Analyze Requirement
  -> Generate Jira Drafts
  -> Human Review
  -> Create Jira Issues
  -> Generate Confluence Page
  -> Human Review
  -> Publish Page
  -> Generate Test Plan
  -> Generate Test Scripts
  -> Run Tests
  -> Summarize Results
```

Workflow 层需要支持：

- 状态管理
- 重试
- 超时
- 回滚
- 幂等
- 审批
- 审计
- 定时触发
- Webhook 触发

### 5.5 Human Approval

必须审批的动作：

- 创建或修改正式 Jira issue
- 发布 Confluence 页面
- 发送邮件
- 合并 PR
- 触发生产压测
- 修改生产配置
- 执行生产修复
- 回滚部署
- 关闭 incident

可以自动执行的动作：

- 生成草稿
- 查询文档
- 查询日志
- 查询 metrics
- 查询 trace
- 分析测试结果
- 生成建议
- 创建本地临时 artifacts

## 6. 技术栈建议

| 层 | 推荐选型 |
| --- | --- |
| Frontend | Next.js + TypeScript |
| Backend API | Node.js/NestJS 或 FastAPI |
| Agent Framework | LangGraph, Mastra, VoltAgent, CrewAI |
| Workflow Engine | Temporal, Inngest, Conductor |
| Tool Protocol | MCP |
| Browser Automation | Playwright, Stagehand, browser-use, Skyvern |
| UI Testing | Playwright, TestZeus Hercules |
| API Testing | Playwright API, Postman/Newman, pytest |
| Performance Testing | k6, Locust, JMeter |
| Agent Evaluation | promptfoo, Giskard, TruLens |
| Vector Store | pgvector, Qdrant, Milvus |
| Database | Postgres |
| Queue | Redis, Kafka, RabbitMQ |
| Observability | OpenTelemetry, Prometheus, Grafana, HyperDX |
| Auth | OAuth2/OIDC, enterprise SSO |
| Permission | RBAC + per-tool authorization |

## 7. 参考开源项目

### 7.1 软件工程 Agent 产品

#### OpenHands

GitHub: https://github.com/OpenHands/OpenHands

参考价值：

- 软件工程 Agent 产品形态。
- Workspace、文件系统、终端、浏览器、代码修改能力。
- 面向真实开发任务的执行闭环。

适合学习：

- 如何把 Agent 包装成产品。
- 如何处理任务执行记录。
- 如何让 Agent 和代码环境协作。

#### SWE-agent

GitHub: https://github.com/SWE-agent/SWE-agent

参考价值：

- 将 GitHub issue 转化为代码修复任务。
- Agent-computer interface 设计。
- 软件工程 benchmark 和任务执行流程。

适合学习：

- Issue to fix 的执行路径。
- 工具接口如何约束 Agent 行为。

### 7.2 Agent Framework

#### LangGraph

GitHub: https://github.com/langchain-ai/langgraph

参考价值：

- 复杂 Agent 状态机。
- 多步骤任务。
- Human-in-the-loop。
- 失败恢复。
- Agent + Workflow 混合模式。

#### Mastra

GitHub: https://github.com/mastra-ai/mastra

参考价值：

- TypeScript 优先。
- Agents、workflows、RAG、MCP、human-in-the-loop。
- 适合构建 TS 技术栈的 Agent 产品。

#### VoltAgent

GitHub: https://github.com/VoltAgent/voltagent

参考价值：

- TypeScript Agent Engineering Platform。
- Memory、RAG、tools、MCP、workflow、observability。
- 适合参考 Agent 平台工程化设计。

#### CrewAI

GitHub: https://github.com/crewAIInc/crewAI

参考价值：

- 多角色 Agent。
- PM Agent、QA Agent、SRE Agent、Doc Agent 这类角色分工可参考。

#### Microsoft AutoGen

GitHub: https://github.com/microsoft/autogen

参考价值：

- 多 Agent 对话。
- Handoff。
- Agent 协作协议。

### 7.3 Tool Integration / MCP

#### Composio

GitHub: https://github.com/ComposioHQ/composio

参考价值：

- Agent 工具集成层。
- Python/TypeScript SDK。
- 连接 Gmail、Slack、GitHub、Notion 等应用。

#### Arcade MCP

GitHub: https://github.com/ArcadeAI/arcade-mcp

参考价值：

- MCP 工具开发。
- OAuth。
- 授权。
- 按用户执行工具调用。

#### Atlassian MCP Server

GitHub: https://github.com/atlassian/atlassian-mcp-server

参考价值：

- Jira/Confluence 官方 MCP 方向。
- 适合参考 Atlassian 生态连接方式。

#### mcp-atlassian

GitHub: https://github.com/sooperset/mcp-atlassian

参考价值：

- Jira/Confluence 自托管 MCP 实现。
- 适合本地或企业私有环境参考。

### 7.4 Browser Automation

#### browser-use

GitHub: https://github.com/browser-use/browser-use

参考价值：

- AI 浏览器自动化。
- 适合网页后台、表单、邮件、无 API 系统。

#### Stagehand

GitHub: https://github.com/browserbase/stagehand

参考价值：

- Playwright + AI。
- 支持更工程化的浏览器操作。
- 适合 UI 测试和网页任务自动化。

#### Skyvern

GitHub: https://github.com/Skyvern-AI/skyvern

参考价值：

- 真实网页工作流自动化。
- 表单填写。
- 数据提取。
- 后台系统操作。

### 7.5 Testing Agent / Agent Evaluation

#### TestZeus Hercules

GitHub: https://github.com/test-zeus-ai/testzeus-hercules

参考价值：

- AI testing agent。
- UI、API、安全、可访问性、视觉测试。

#### promptfoo

GitHub: https://github.com/promptfoo/promptfoo

参考价值：

- Prompt、Agent、RAG 测试。
- 回归测试。
- 红队测试。
- CI/CD 集成。

#### Giskard

GitHub: https://github.com/Giskard-AI/giskard

参考价值：

- LLM/Agent 安全和质量评估。
- 适合评估 Agent 输出稳定性和安全性。

### 7.6 Performance / Load Testing

#### k6

GitHub: https://github.com/grafana/k6

参考价值：

- 现代性能测试。
- JS 脚本。
- CI/CD 友好。

#### Locust

GitHub: https://github.com/locustio/locust

参考价值：

- Python 压测。
- 场景表达灵活。

#### JMeter

GitHub: https://github.com/apache/jmeter

参考价值：

- 经典压测工具。
- 协议覆盖广。
- 企业环境常见。

### 7.7 Health Check / Monitoring

#### Uptime Kuma

GitHub: https://github.com/louislam/uptime-kuma

参考价值：

- 服务可用性监控。
- HTTP/TCP/Ping/证书监控。
- 适合参考 health check 产品体验。

#### Healthchecks

GitHub: https://github.com/healthchecks/healthchecks

参考价值：

- Cron job 和后台任务心跳监控。
- 适合自动化任务健康检查。

### 7.8 Production Support / Incident Investigation

#### OpenSRE

GitHub: https://github.com/Tracer-Cloud/opensre

参考价值：

- AI SRE。
- 告警分析。
- 根因定位。

#### IncidentFox

GitHub: https://github.com/incidentfox/incidentfox

参考价值：

- Incident investigation agent。
- 自动调查告警和生成上下文。

#### Coroot

GitHub: https://github.com/coroot/coroot

参考价值：

- Observability。
- Service map。
- APM。
- Root cause analysis。

#### HyperDX

GitHub: https://github.com/hyperdxio/hyperdx

参考价值：

- Logs、metrics、traces、session replay。
- 适合为 Production Support Agent 提供观测数据底座。

### 7.9 Human Approval

#### HumanLayer

GitHub: https://github.com/humanlayer/humanlayer

参考价值：

- Human-in-the-loop。
- 高风险工具调用审批。
- Slack/Email 反馈。
- 企业 Agent 可控执行。

## 8. 核心产品模块

### 8.1 Mission Console

核心页面：

- Mission 列表
- Mission 详情
- Agent 执行时间线
- Artifacts 面板
- 工具调用记录
- 审批面板
- 外部系统链接
- 人工反馈入口

### 8.2 Artifact Management

Artifact 类型：

- Requirement Summary
- Jira Drafts
- Confluence Draft
- Test Plan
- Test Cases
- Test Scripts
- Performance Report
- Health Check Report
- Incident Summary
- RCA Draft
- Email Draft

Artifact 需要版本化。

### 8.3 Approval Center

审批对象：

- 工具调用
- 文档发布
- Jira 创建
- 邮件发送
- 生产操作
- 测试执行

审批信息：

- 谁发起
- 谁审批
- 为什么需要审批
- 输入是什么
- 预期影响是什么
- 回滚方式是什么

### 8.4 Skill Marketplace

内部 Skill 市场可以包括：

- Requirement Analysis Skill
- Jira Planning Skill
- Confluence Doc Skill
- UI Test Skill
- API Test Skill
- Performance Test Skill
- Health Check Skill
- Incident Investigation Skill
- Email Draft Skill

每个 Skill 都应该有：

- 描述
- 输入输出
- 示例
- 权限要求
- 风险等级
- 测试覆盖
- 版本号

## 9. 安全与可靠性原则

### 9.1 分级执行

| 等级 | 类型 | 示例 | 策略 |
| --- | --- | --- | --- |
| L0 | 只读 | 搜索文档、查询日志、读取 Jira | 可自动执行 |
| L1 | 本地生成 | 生成草稿、生成测试脚本 | 可自动执行 |
| L2 | 非生产写入 | 创建 Jira、创建 Confluence 草稿 | 需要确认或可配置审批 |
| L3 | 外部通信 | 发送邮件、发 Slack 公告 | 默认审批 |
| L4 | 生产影响 | 回滚、扩容、生产压测、改配置 | 强制审批 |

### 9.2 证据链

Agent 的每个结论都应该尽量绑定证据：

- 源需求文本
- 相关 Jira
- 相关 Confluence 页面
- 相关日志
- 相关 trace
- 相关 metric
- 相关 PR/commit
- 相关测试报告

### 9.3 可回放

每个 Mission 应该可以回放：

- 用户输入
- Agent 计划
- 工具调用
- 中间输出
- 最终 artifacts
- 审批记录
- 错误和重试

### 9.4 可测试

Agent 本身也要测试：

- Prompt regression
- Tool calling regression
- Output schema validation
- Golden dataset
- Red team cases
- Permission boundary tests
- Human approval tests

推荐使用 promptfoo/Giskard/TruLens 这类工具。

## 10. 建议路线图

### Phase 1: 文档与 Jira 闭环

目标：

- 用户输入需求。
- Agent 输出需求摘要、验收标准、任务拆解。
- 生成 Jira drafts。
- 生成 Confluence draft。
- 人工审批后创建。

核心价值：

- 立即提升 PM/Tech Lead/BA/QA 的效率。
- 风险较低。
- 产物可见。

### Phase 2: 测试自动化闭环

目标：

- 从验收标准生成测试计划。
- 生成 Playwright/API 测试。
- 执行测试。
- 分析失败。
- 回写 Jira/Confluence。

核心价值：

- 连接需求和质量。
- 给 QA 和开发带来直接收益。

### Phase 3: Health Check 与 Release Readiness

目标：

- 自动生成发布检查清单。
- 自动配置或检查 health checks。
- 生成 release readiness report。

核心价值：

- 减少上线遗漏。
- 给 release manager 和 SRE 提供辅助。

### Phase 4: Production Support

目标：

- 读取告警。
- 自动收集证据。
- 生成 incident summary。
- 推荐排查步骤。
- 生成 RCA 草稿。

核心价值：

- 降低 MTTR。
- 提升事故复盘质量。

### Phase 5: 更强的自动执行

目标：

- 在明确权限和审批机制下执行更多动作。
- 支持自动创建 PR。
- 支持自动补充测试。
- 支持自动更新 Runbook。
- 支持可控的生产操作建议。

## 11. 需要避免的坑

- 不要把所有能力都塞进一个超长 prompt。
- 不要只做聊天框，没有任务状态和 artifacts。
- 不要一开始就允许自动生产操作。
- 不要缺少审批和审计。
- 不要忽视权限边界。
- 不要依赖浏览器自动化替代所有 API。
- 不要让 Agent 直接相信单一数据源。
- 不要把 workflow 全交给 LLM 自由发挥。
- 不要缺少 Agent 测试和回归集。

## 12. 推荐的第一版系统边界

第一版建议只承诺：

```text
帮助研发团队把需求转化为结构化交付计划和工程产物草稿。
```

第一版能力：

- 需求分析
- 任务拆解
- Jira draft
- Confluence draft
- 测试计划 draft
- Email/status update draft
- 人工审批
- 工具调用审计

暂不承诺：

- 全自动修复生产问题
- 全自动发送对外邮件
- 全自动执行生产压测
- 全自动合并代码
- 全自动关闭 incident

这个边界更容易交付，也更容易获得企业用户信任。

