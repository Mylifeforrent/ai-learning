# 个人开发者 Vibe Coding 全流程教学文档

## 基于 SDD（Specification-Driven Development，规范驱动开发）· 单人版

> **版本：v1.0**（基于《企业级 Vibe Coding SDD 流程 v2.1》适配）
>
> 本文档与企业版的关系：**流程 100% 保留，执行机制单人化。**
> 18+1 个阶段、4 个 Gate、三条贯穿线（安全/质量/变更）全部保留；
> 变化的是：多角色签核 → 单人角色轮换 + AI 虚拟团队 + 冷却期。
>
> 核心原则：**你不是在省略评审，而是在扮演评审者。**
> 一个人开发最大的风险不是写不动代码，而是没有人对你说"这里不对"。
> 本流程的全部设计，都是为了让你一个人也能获得团队级的纠错能力。

---

# 0. 单人开发适配机制

## 0.1 单人开发的三个特殊风险

企业流程靠"别人"来纠错，单人开发没有"别人"，因此必须正视三个结构性风险：

| 风险 | 表现 | 本流程的对策 |
|---|---|---|
| **自评放水** | 自己评审自己的产出，倾向于"差不多就行" | 冷却期 + Checklist 机械执行 + AI 独立复审（0.4） |
| **流程疲劳** | 一个人既要设计又要写码，容易跳过文档直接 Vibe | 时间盒 + 最小可交付物（0.6），让每个阶段"轻到无法拒绝" |
| **上下文单一** | 所有决策出自同一个大脑，盲区无人挑战 | AI 虚拟团队扮演反对者/评审者（0.5） |

## 0.2 三大适配机制

### 机制一：角色轮换（Role Rotation）

你在不同阶段佩戴不同的"角色帽"，并在 Gate 处强制换帽：

```text
构建者（Builder）          评审者（Reviewer）
═══════════════════        ═══════════════════
写业务模型、写提示词、       只看 Checklist，逐条打勾，
指挥 AI 写代码              不看"我当时怎么想的"
        │                          ↑
        └──── 冷却期（至少一晚）────┘
```

执行要求：

- **冷却期不可省略**：完成产出后至少隔一晚（或切换到无关任务 2 小时以上）再评审。刚写完就评审等于不评审。
- **评审时换物理环境或换文档视角**：把产出导出/打印/换个编辑器看，能有效切断"作者视角"。
- **Checklist 机械执行**：不许"总体感觉可以"，每条必须给出 Pass / Fail / N/A + 证据。

### 机制二：AI 虚拟团队（AI as Virtual Team）

用**独立的新会话**让 AI 扮演团队里的其他角色。关键纪律：

- **评审会话必须全新**：不要把实现会话的上下文带进评审会话。评审 AI 只能看到"设计资产 + 产出物"，不能听到"我当时的意图"——否则它会被你的意图带偏，等于你自己评审自己。
- **一个角色一个会话**：安全评审和产品评审分开开，角色不混。
- **评审 AI 的结论你需要逐条回应**：接受、驳回（写明理由）或转 [TBD-*]，不允许默默忽略。

虚拟团队角色表：

| 虚拟角色 | 启用时机 | 职责 |
|---|---|---|
| 产品负责人 | Gate 1、Stage 5 评审 | 挑战业务规则完整性与范围合理性 |
| 魔鬼代言人 | Explore 阶段（Stage 3-6） | 对每个关键决策提反对意见 |
| 架构评审员 | Gate 2 | 挑战架构与契约设计 |
| 安全评审员 | Gate 3 | 按安全清单审查代码 |
| QA 工程师 | Stage 17 | 生成对抗性测试场景、找边界 |
| 发布经理 | Gate 4 | 核对发布就绪度 |

各角色的完整提示词见附录 B。

### 机制三：时间盒（Time-boxing）

每个阶段设上限，到点必须进入 Gate 评审。**超时不是在追求完美，是在堆积未经评审的债。**

以典型的个人 MVP（2～4 周周期）为例：

| 阶段 | 时间盒 | 最小可交付物（少于此即跳过流程） |
|---|---|---|
| Stage 1-2 环境与规范 | 0.5 天 | 安全基线生效 + project_rules.md 一页 |
| Stage 3-4 市场与竞品 | 0.5~1 天 | 各一份报告，每份 ≤ 3 页 |
| Stage 5 业务建模 | 0.5 天 | BR 清单 + 权限矩阵 + 量化 NFR |
| Stage 6-7 交互与原型 | 1~2 天 | 可点击走通主流程的 Prototype |
| Stage 8-11 工程设计 | 1~2 天 | 边界表 + ER 图 + API 清单 |
| Stage 12-13 PRD 与高保真 | 0.5~1 天 | PRD（含可测试 AC）+ Design Tokens |
| Stage 14 AI 上下文 | 0.5 天 | CLAUDE.md ≤ 300 行 |
| Stage 15-16.5 实现与评审 | 总时间的 40~50% | 代码 + 测试 + Gate 3 记录 |
| Stage 17 联调 E2E | 0.5~1 天 | E2E 报告 + 追溯矩阵 |
| Stage 18 CI/CD 部署 | 0.5~1 天 | 可重复部署 + 回滚方案 |

## 0.3 裁剪对照表

流程可以轻量化，但有些环节**砍掉就意味着退出本流程**。

### 禁止裁剪（单人同样不可豁免）

```text
✖ 密钥/敏感信息红线（Stage 1 安全基线、secret scanning）
✖ Gate 3 代码评审（冷却期自评 + AI 复审 + 自动化检查）
✖ Task Brief 纪律（每次实现会话明确范围，一个模块一个会话）
✖ 冻结资产不私改（发现上游问题必须标记，不得顺手改）
✖ 测试与追溯（BR → AC → TC 链条，可简化但不可断）
✖ 回滚方案（可以不演练多次，但必须演练过一次）
```

### 可以简化（相对企业版）

| 环节 | 企业版 | 单人版 |
|---|---|---|
| Gate 签核 | 产品/技术/设计/安全多人签字 | 本人冷却期自评 + AI 角色复审，记录照填 |
| 变更控制 CCR | 分级评估 + 重走 Gate | 简版三级处理（附录 C），L3 强制隔夜 |
| 文档规模 | 各阶段完整规格 | 满足"最小可交付物"即可，但要素不缺 |
| CI/CD | 多环境多阶段流水线 | 单条 GitHub Actions + dev/prod 两环境 |
| 监控告警 | 指标+告警+接收人体系 | 免费 uptime 监控 + 错误追踪各一 |
| SBOM/安全扫描 | 完整 SBOM + 多工具 | 依赖审计 + secret scan + 一个 SAST |
| PRD | 十要素完整 PRD | 保留要素但篇幅不限，AC 不可省 |

## 0.4 单人 Gate 评审协议

四个 Gate 全部保留（Gate 1 产品冻结 / Gate 2 工程冻结 / Gate 3 代码准入 / Gate 4 发布就绪），单人执行协议：

```text
第一步：构建者自查
  → 对照本阶段"质量门禁"逐条打勾，填写证据

第二步：冷却期
  → 至少一晚。Gate 3（代码）可按 PR 粒度执行，
    但每周至少一次"隔夜全量回顾"

第三步：换帽评审
  → 以评审者身份重读产出物 + Gate Checklist
  → 物理换环境（导出 PDF / 换设备 / 打印均可）

第四步：AI 独立复审
  → 全新会话，使用附录 B 对应角色提示词
  → 输入仅限：冻结资产 + 待评审产出物
  → 逐条回应 AI 的每个问题（接受/驳回+理由/转 TBD）

第五步：填写 Gate 记录归档
  → 参与人栏：本人（构建）/ 本人（评审）/ AI（复审）
  → 结论：APPROVED / CONDITIONAL / REJECTED
```

### Gate 记录模板（单人版）

```markdown
## Gate {编号} Review Record

日期：____
阶段：____
参与人：本人（构建）/ 本人（评审，冷却期 ____ 小时后）/ AI 复审（角色：____）

### 准入条件
- [ ] 本阶段产出物已提交至 docs/ 对应目录
- [ ] 达到最小可交付物标准
- [ ] 冷却期已满

### 检查项
（使用各阶段定义的可度量质量门禁清单）

### AI 复审问题与回应
| # | AI 提出的问题 | 我的回应（接受/驳回+理由/TBD） | 状态 |
|---|---|---|---|
| | | | |

### 问题回溯
| 问题 | 归属阶段 | 级别(L1/L2/L3) | 修改动作 | 状态 |
|---|---|---|---|---|
| | | | | |

### Gate 结论
- [ ] APPROVED：资产冻结，进入下一阶段
- [ ] CONDITIONAL：阻塞问题为 0，非阻塞问题转跟踪
- [ ] REJECTED：回溯到指定阶段
```

## 0.5 AI 提示词工程规范（与企业版一致）

所有提示词遵循六段式结构：

```text
① 角色与能力边界
② 输入资产（路径 + 权威优先级）
③ 任务与产出（文件路径 + 格式）
④ 约束（必须做 / 禁止做）
⑤ 不确定处理（[TBD-*] / [CONFLICT] 升级，禁止编造）
⑥ 完成前自检（Self-Check 清单）
```

上下文预算规则（单人同样适用，因为限制来自模型而非人数）：

- 单次会话引用文档 ≤ 5 份，其余用路径引用
- 单份超 300 行只传相关章节
- **实现类任务一个模块一个新会话**，以 Task Brief（附录 E）开场
- 项目级 CLAUDE.md ≤ 300 行，细节一律路径引用

## 0.6 个人免费工具栈

| 用途 | 推荐（均有免费额度） |
|---|---|
| Secret 扫描 | gitleaks（本地 pre-commit）+ GitHub Push Protection |
| 依赖审计 | Dependabot / pip-audit / npm audit |
| SAST | semgrep（免费版）/ bandit（Python） |
| CI/CD | GitHub Actions（公开仓库免费，私有仓库有免费额度） |
| 错误追踪 | Sentry 免费档（或先用结构化日志 + 日志告警） |
| 可用性监控 | UptimeRobot 免费档 |
| 部署 | 单 VPS + docker compose，或 PaaS 免费档 |
| 原型 | Figma Make / 同类 AI 原型工具 |

## 0.7 完整流程（与企业版一致，标注时间盒）

```text
Stage 1  基础环境配置（含安全基线）          ┐
Stage 2  项目初始化（规范 + AI 红线）        ┘ 0.5 天
    ↓
Stage 3  市场调研                            ┐
Stage 4  竞品拆解                            ┤ 0.5~1.5 天
Stage 5  业务建模（含 NFR）                  ┘
    ↓
Stage 6  核心交互设计                        ┐
Stage 7  Interactive Prototype              ┘ 1~2 天
    ↓
★ Gate 1：Prototype Review（角色轮换 + AI 产品负责人复审）★
    ↓
Stage 8  架构设计                            ┐
Stage 9  技术框架（依赖审计）                ┤ 1~2 天
Stage 10 数据模型（数据分级）                ┤
Stage 11 API Contract                        ┘
    ↓
★ Gate 2：Architecture & Contract Review（AI 架构评审员复审）★
    ↓（架构 / 数据模型 / API 契约冻结）
 ┌───────────────────────┬───────────────────────┐          ┐
Stage 12 PRD（含可测试 AC）          Stage 13 高保真          ┤ 0.5~1 天
 └───────────────────────┬───────────────────────┘          ┘
                         ↓
Stage 14 CLAUDE.md / AGENTS.md（0.5 天）
                         ↓
               ┌─────────┴─────────┐
        Stage 15 后端 MVP   Stage 16 前端 MVP   ← 占总时间 40~50%
               └─────────┬─────────┘
                         ↓
★ Gate 3：Stage 16.5 代码评审（冷却期自评 + AI 安全评审 + CI 自动检查）★
                         ↓
Stage 17 联调 / E2E（AI QA 工程师生成对抗场景）   0.5~1 天
                         ↓
★ Gate 4：Release Readiness ★
                         ↓
Stage 18 CI/CD 与部署                          0.5~1 天
                         ↓
              监控 / 用户反馈 → 简版变更控制（附录 C）
```

## 0.8 文档目录结构

与企业版一致，个人项目可将早期研究类文档合并存放，但**资产本身不可省略**：

```text
ProjectName/
├── AGENTS.md / CLAUDE.md  # 根目录指令文件（ZCode 用 AGENTS.md，Claude Code 用 CLAUDE.md）；Stage 2 创建初始版，Stage 14 完善
├── docs/
│   ├── 00_setup/project_rules.md                    # 项目规范（含 AI 红线）
│   ├── 01_market_research/market_research_report.md
│   ├── 02_competitor_analysis/competitor_analysis_report.md
│   ├── 03_problem_modeling/business_model.md        # 含 NFR
│   ├── 04_interaction_design/interaction_design_summary.md
│   ├── 05_prototype/
│   │   ├── prototype_review.md                      # Gate 1 记录
│   │   └── prototype_link.md
│   ├── 06_architecture_design/
│   │   ├── frontend_design_spec-v1.0.md
│   │   └── frontend_backend_boundary_spec-v1.0.md
│   ├── 07_backend_design/
│   │   ├── architecture_spec.md
│   │   ├── data_model_spec.md
│   │   ├── api_interface_spec.md
│   │   └── gate2_review.md                          # Gate 2 记录
│   ├── 08_prd/prd_document.md
│   ├── 09_figma_highfi/
│   │   ├── design_tokens.json
│   │   └── component_spec.json
│   ├── 10_ai_context/ai_context_index.md            # 指向根目录 CLAUDE.md / AGENTS.md 的索引与生成说明
│   ├── 11_test/
│   │   ├── test_plan.md
│   │   ├── code_review_report.md                    # Gate 3 记录
│   │   └── e2e_report.md                            # Stage 17 产出（E2E 报告）
│   ├── 12_deployment/
│   │   ├── cicd_pipeline_spec.md
│   │   ├── gate4_review.md                          # Gate 4 记录（发布就绪）
│   │   └── release_checklist.md
│   └── 13_changes/change_log.md
├── frontend/             # 前端源码
├── backend/              # 后端源码（示例：Python 后端可用 uv 管理虚拟环境；.env 管理配置）
├── .env.example          # 只含键名，无真实值
├── .gitignore            # 必须覆盖 .env、密钥、证书
└── README.md
```

---

# Phase 1：基础搭建

## Stage 1：基础环境配置

### 目标

建立 AI 辅助开发基础设施 + 安全基线。个人项目历史上最常见的安全事故就是**把 API Key 提交进公开仓库**，本阶段用 30 分钟永远免除这个风险。

### 个人执行要点

- 时间盒：2 小时
- 你做什么：确认工具选型、检查扫描结果
- AI 做什么：生成配置、跑连通性测试
- 本模板默认接入 LangChain 文档 MCP（docs-langchain + reference-langchain）；不使用 LangChain 的项目，请替换为你所用框架的官方文档 MCP，步骤不变

### 提示词

```text
【角色】你是一位熟悉 AI 工程化与研发安全基线的工程师。

【任务】检查并完善当前项目的 AI Coding 开发环境，完成项目级配置。
所有配置仅作用于当前项目文件夹，不污染全局。

【步骤 1：检查现状】
1. 检查当前项目是否已有 Claude Code / Codex / Cursor 等项目级配置
   （.claude/、.mcp.json、.cursor/ 等）。
2. 列出已存在的 MCP Server 与 Agent 配置，标注哪些在用、哪些闲置。

【步骤 2：接入你所用框架/技术栈的官方文档 MCP（以下以 LangChain 为示例）】
本项目开发中需要查询你所用框架/技术栈的官方文档与 API，请接入其官方
文档 MCP（分别覆盖"概念/how-to"与"API 参考"两类）。

示例（LangChain/LangGraph，接入说明：
https://docs.langchain.com/use-these-docs#connect-with-claude-code）：

  claude mcp add --transport http docs-langchain https://docs.langchain.com/mcp
  claude mcp add --transport http reference-langchain https://reference.langchain.com/mcp

- 概念文档 MCP（示例 docs-langchain）：概念指南 / how-to / 教程（回答"为什么、怎么做"）
- API 参考 MCP（示例 reference-langchain）：类、方法、参数、签名（回答"确切用法"）
- 非 LangChain 项目：替换为你所用技术栈的官方文档 MCP，步骤不变
- 以上命令默认即项目级配置（只写入当前工作目录），不要加 --scope user
- 如使用 Cursor / VS Code 等其他工具，按对应文档中该工具的 JSON 格式接入

【步骤 3：Agent Teams 配置】
启用 claude-code-guide（或当前环境中的官方指南技能），详细了解
Agent Teams 的配置方法，并在当前文件夹完成项目级配置：
- 先根据任务复杂度判断是否需要（简单/确定性任务单 Agent 即可）
- 需要时按指南完成 .claude/ 下的项目级 Agent Teams 配置
- 不需要时明确说明理由并跳过，不产生空配置文件

【步骤 4：连通性测试】
配置完成后逐个测试，并留档证据：
- 执行 claude mcp list，确认每个 server 状态为已连接（✓）
- 对每个 MCP 实际调用一次（如向文档 MCP 提一个真实问题并附回答）
- 连通失败的 MCP：给出排查结论（URL / 网络 / 凭证），修复或移除，
  不留死配置

【不确定处理】
配置或连通结果无法判定时标记 [TBD-INFRA] 并写明原因（URL / 网络 /
凭证 / 工具差异），禁止在无实际调用证据的情况下声称已连通。

【步骤 5：安全基线】
- 校验 .gitignore 覆盖：.env*、*.pem、*.key、credentials*、secrets*
- 配置 gitleaks 及 pre-commit hook
- 开启 GitHub Push Protection（如仓库托管在 GitHub）
- 生成 .env.example（只含键名与注释，禁止写入真实值）
- 全量扫描 Git 历史，如发现已提交的敏感信息立即停止并报告

【产出】
工具 / MCP / Agent 配置清单（含连通性测试证据）+ 安全基线检查报告

【完成前自检】
- [ ] 所用技术栈的文档 MCP（概念类 + API 参考类，示例 docs-/reference-langchain）均连通，附实际调用证据
- [ ] 每个 MCP 有连通性测试证据；失败项已修复或移除
- [ ] Agent Teams 按需配置，无空配置、无任务不需要的 Agent
- [ ] .env.example 无任何真实密钥值
- [ ] secret 全量扫描 0 告警
- [ ] 全部配置为项目级，未污染全局
```

### 质量门禁

- MCP 连通性测试通过率 100%（所用技术栈的文档 MCP，示例 docs-/reference-langchain，含实际调用证据）
- Agent Teams 配置与任务复杂度匹配（无空配置、无闲置 Agent）
- secret 扫描 0 告警（含 Git 历史）
- .gitignore 覆盖全部敏感文件模式
- 全部配置为项目级，未污染全局

---

## Stage 2：项目初始化

### 目标

建立项目规范与 AI 使用约定。单人项目最容易"规范在脑子里"，三个月后自己就忘了——**规范必须落盘，因为三个月后读代码的"另一个人"就是未来的你。**

### 个人执行要点

- 时间盒：2 小时
- 最小可交付：README + 根目录 AGENTS.md（初始版；采用 Claude Code 则命名为 CLAUDE.md）+ docs/00_setup/project_rules.md（一页纸以内也可以，但要素不缺）
- **本阶段只搭建目录与规范文档，不生成任何前后端代码**

### 提示词

```text
【角色】你是一位有 5 年经验的 Tech Lead。

【输入】（权威优先级从高到低；缺失项按下述规则标记，不臆测）
1. 项目立项信息与技术偏好（如已有）
2. 团队/个人既定的工程约定（如已有）
未提供的输入一律标记 [ASSUMPTION] 并写明假设，不得当作既定事实。

【任务】完成项目的初始化与规范搭建。本阶段只建目录结构与规范文档，
禁止生成任何前后端实现代码。

【步骤 1：规划目录结构】
规划整个项目的目录结构，包括 frontend、backend 以及 docs：
- frontend/：前端源码（本阶段只建目录，不写代码）
- backend/：后端源码（同上）
- docs/：全部设计资产与过程文档的唯一存放地

【步骤 2：建立 docs 分层目录】
在 docs 下按阶段建立分层目录（与 0.8 节一致），依次覆盖：
业务调研（01_market_research）→ 竞品分析（02_competitor_analysis）→
业务问题建模（03_problem_modeling）→ 核心交互链路设计（04_interaction_design）→
产品原型规范（05_prototype）→ 系统架构设计（06_architecture_design）→
数据模型与 API 规范（07_backend_design）→ PRD（08_prd）→
高保真设计（09_figma_highfi）→ AI 上下文（10_ai_context）→
前端/后端实现与联调测试（11_test）→ 发布和部署（12_deployment）→
变更记录（13_changes）
另建 00_setup 存放项目规范。每个目录放一个 README.md，
一句话说明该目录存放什么、由哪个阶段产出。

【步骤 3：创建根目录 AGENTS.md（初始版）】
在项目根目录创建 AGENTS.md（ZCode 读取的是 AGENTS.md；采用 Claude Code 则同步生成同名 CLAUDE.md），写明：
- frontend、backend、docs 三者的职责边界
- 后端统一使用 .env 管理配置（.env 不入库，.env.example 只含键名）
- 后端依赖与虚拟环境用你所选语言的标准工具管理（示例：Python 用 uv）
- 所有 Agent Team 阶段都要有明确的输出文件（路径 + 格式）
- 复杂任务必须先 Plan 再实施
- 不超过 300 行，细节一律路径引用（见 0.5 节）
（本阶段只写工程规则；设计资产约束由 Stage 14 补充完善）

【步骤 4：生成 docs/00_setup/project_rules.md】
内容至少包含：
- 代码命名规范
- 目录组织规范
- Git 分支策略与 Commit 规范（Conventional Commits）
- AI 生成代码 Review Checklist（引用附录 D）
- 测试与验证要求
- AI 使用红线：
  · 禁止将密钥、生产数据、用户隐私数据提供给 AI
  · 禁止 AI 静默修改已冻结的设计资产
  · 禁止提交未运行验证的 AI 生成代码
  · 禁止 AI 自行引入未审计的第三方依赖

【产出】
1. README.md
2. AGENTS.md（根目录，初始版）
3. docs/00_setup/project_rules.md
4. .claude/settings.json（仅采用 Claude Code 时创建；ZCode 无此文件，无需创建）

【要求】
- 技术栈按项目需求推荐并说明理由（个人项目优先选择你最熟悉的栈，
  而非"最流行"的栈——单人没有学习新栈的团队缓冲）
- 规范必须可执行，避免"尽量""建议"等模糊表述
- 不新增业务功能，不生成任何前后端实现代码
- 跨项目通用偏好（语言、审阅风格等）写入 ~/.zcode/AGENTS.md（个人级）；项目根 AGENTS.md 只放本项目规则

【不确定处理】
规范未定或输入不足处标记 [TBD-*]（如 [TBD-INFRA] / [TBD-BIZ]），
并写明需谁在何阶段确认，禁止臆造规则或补全不存在的约定。

【完成前自检】
- [ ] frontend / backend / docs 目录结构完整，docs 分层与 0.8 节一致
- [ ] 根目录 AGENTS.md 包含：职责边界、.env 与依赖/虚拟环境管理约定（示例：uv）、
      阶段输出文件要求、复杂任务 Plan 优先规则
- [ ] project_rules.md 每条规范有明确判定标准，AI 红线逐条可执行
- [ ] 本阶段未生成任何前后端代码
```

### 质量门禁

- 项目目录完整（frontend / backend / docs 分层齐全）
- 根目录 AGENTS.md 已创建且包含全部约定项
- AI 使用红线已写入 project_rules.md

---

# Phase 2：Product Discovery / Business Design

## Stage 3：市场调研

### 个人执行要点

- 时间盒：半天。**个人项目的调研目标是"验证这件事值得做"，不是写行业白皮书。**
- AI 做主力检索与起草；你负责验证关键数据来源的真实性（AI 会编造数字，这是幻觉高发区）
- 探索阶段启用"魔鬼代言人"（附录 B.2），让它专门挑战你的立项理由

### 提示词

```text
【角色】你是一位有 5 年经验的行业分析师。

【任务】针对【{项目领域}】完成市场调研报告。

【产出】docs/01_market_research/market_research_report.md（≤ 3 页）

【必须包含】
1. 目标用户画像与核心痛点
2. 主要使用场景
3. 市场规模与趋势（简要）
4. 市场机会与风险
5. 明确回答：为什么是现在？为什么是我来做？

【约束】
- 所有外部数据必须标注来源和时间
- 无法验证的数据标记 [TBD-RESEARCH]
- 区分事实、推测和结论
- 不添加与当前项目无关的扩展建议

【完成前自检】
- [ ] 每个关键数字都有来源与时间（我已抽查至少 2 个来源的真实性）
- [ ] "为什么是我"的回答具体，而非"因为市场很大"
```

### 质量门禁

- 关键数据 100% 有来源，且你人工抽查过至少 2 处
- 立项理由能经受魔鬼代言人 AI 的一轮挑战

---

## Stage 4：竞品拆解

### 个人执行要点

- 时间盒：半天到一天
- 竞品 2~3 个即可，重点是"它们没解决什么"——那是你的生存空间

### 提示词

```text
【角色】你是一位有 5 年经验的产品与 AI 应用架构专家。

【输入】docs/01_market_research/market_research_report.md

【产出】docs/02_competitor_analysis/competitor_analysis_report.md（≤ 3 页）

【竞品范围】【{竞品A}、{竞品B}、{竞品C}】

【每个竞品至少分析】
1. 产品定位与核心功能
2. 核心用户流程
3. AI 使用场景（如有）
4. 商业模式
5. 用户评价中的高频抱怨（应用商店/社区/评论区，注明来源）
6. 最值得借鉴的设计
7. 它们没解决什么（空白点）

【约束】
- 区分"公开事实"和"推测"，推测必须标记
- 最后提供横向对比矩阵
- 结论必须回答：我的差异化切入点是什么

【完成前自检】
- [ ] "高频抱怨"来自真实用户反馈来源，非 AI 臆测
- [ ] 差异化切入点具体、可被后续业务建模直接采用
```

### 质量门禁

- 每个结论有事实/证据或明确标记为推测
- 差异化切入点明确

---

## Stage 5：业务建模

### 目标

把调研收敛为结构化业务模型。**这是全流程最重要的资产，个人项目同样不例外**——它是你三个月后判断"AI 写得对不对"的唯一标尺。

### 个人执行要点

- 时间盒：半天
- NFR 按个人项目现实设定（例："支持 100 并发""核心接口 P95 < 500ms"），但必须量化
- 写完后用 AI 产品负责人角色（附录 B.1）做一轮挑战

### 提示词

```text
【角色】你是一位有 5 年经验的业务架构师。

【输入】（权威优先级从高到低）
1. docs/01_market_research/market_research_report.md
2. docs/02_competitor_analysis/competitor_analysis_report.md

【产出】docs/03_problem_modeling/business_model.md

【必须包含】
1. 业务目标
2. 核心业务流程（Mermaid，标注人工/系统节点、输入/处理/输出/异常）
3. 核心业务实体及关系
4. 角色与权限矩阵
5. 状态模型
6. 业务规则清单（BR-001...）
7. 非功能需求（NFR-001...）：性能 / 容量 / 安全合规 / 数据保留，
   全部量化
8. MVP 范围
9. Out of Scope（个人项目尤其要狠：列得越多，做完的概率越大）

【硬性规则】
- 这是业务收口文档，不得自行新增业务规则
- 无法确定的内容标记 [TBD-BIZ]
- 不用"等""相关""类似"等模糊描述代替具体规则
- NFR 必须量化，禁止"高性能""高可用"式表述

【完成前自检】
- [ ] 每条 BR 有唯一编号且无歧义
- [ ] 每条 NFR 有量化指标
- [ ] Out of Scope 清单长度 ≥ MVP 范围清单的一半
  （个人项目范围失控是头号死因）
```

### 质量门禁

- BR 编号连续、无歧义
- NFR 全部量化
- 通过 AI 产品负责人角色的一轮挑战并逐条回应

---

# Phase 3：Product Design

## Stage 6：核心交互设计

### 个人执行要点

- 时间盒：0.5~1 天
- 状态矩阵（每页 9 类状态）是个人项目最容易偷懒的地方，也是用户感知最强的地方——不许省

### 提示词

```text
【角色】你是一位有 5 年经验的交互设计师。

【输入】docs/03_problem_modeling/business_model.md（唯一业务权威来源）

【产出】docs/04_interaction_design/interaction_design_summary.md

【必须包含】
1. 信息架构：页面清单（PG-001...）/ 用途 / 信息层级 / 导航关系
2. 核心任务流：用户操作 → 系统响应 → 页面变化（主流程 + 异常流程）
3. 交互规则：表单校验 / 操作反馈 / 确认撤销 / 防重复提交 / 权限表现
4. 页面状态矩阵：每页判定 Default / Loading / Empty / No Result /
   Error / No Permission / Editing / Submitting / Success-Failure
5. 响应式行为（Desktop 1440px + Mobile 375px）

【硬性规则】
- Business Model 是业务规则的唯一权威来源
- 不得创造输入文档不存在的业务能力
- 业务规则不足以支持交互决策时标记 [TBD-BIZ]
- 每个核心交互可追溯至 BR-xxx

【完成前自检】
- [ ] 每页 9 类状态逐一判定，不适用需说明理由
- [ ] 异常流程与主流程一一对应
```

### 质量门禁

- 状态矩阵完整
- 交互规则全部可追溯至 BR

---

## Stage 7：Interactive Prototype

### 个人执行要点

- 时间盒：0.5~1 天（AI 原型工具使这步非常快）
- 保真度目标：本阶段要**行为保真**（流程可走通、状态齐全、反馈正确），不是视觉保真；视觉保持中性即可，最终视觉决策属于 Stage 13
- **单人版独特建议**：如果可能，找 1~2 个真实用户（朋友也行）点击试用 10 分钟并观察——这是任何 AI 评审都替代不了的"第二双眼睛"。做不到就用 AI UX 审计兜底。

### 7.1 Figma Make 启动 Prompt

```text
【角色】你是本产品的交互原型构建师。

【输入】（权威优先级从高到低）
1. docs/03_problem_modeling/business_model.md（业务规则）
2. docs/04_interaction_design/interaction_design_summary.md（流程与交互）

【任务】把已确定的业务和交互转换为可点击、可演示的 Prototype。
你的任务不是重新设计业务或交互。

【规则优先级】
Business Model > Interaction Design > Prototype UI 表现

【禁止新增】业务功能 / 用户角色 / 业务规则 / 页面核心能力 / 数据字段 / 状态

【视觉要求】保持中性、接近组件库默认风格；允许合理的布局决策，
但不做品牌与最终视觉决策（属于 Stage 13），且不得改变业务行为。

【必须】
1. 覆盖核心页面，跑通核心用户主流程
2. 支持页面跳转，展示核心成功/失败反馈
3. 展示关键 Loading / Empty / Error / Permission 状态
4. 危险操作提供确认流程
5. Desktop 1440px 优先，Mobile 375px 适配

【不要】生成生产代码；先主流程完整，再补状态

【完成前自检】
- [ ] 主流程从入口到完成可完整点击走通
- [ ] 无输入文档之外的业务能力
```

### 7.2 迭代方式

**Round 1：主流程** → 只实现核心主流程，确保完整点击走通。

**Round 2：状态补全** → 不修改已确认主流程，逐页补充适用状态，不创造新业务状态。

**Round 3：UX Audit**

```text
请检查当前 Prototype：
1. 核心流程是否可完整走通
2. 是否存在无反馈操作 / 无法继续的状态
3. 是否缺少关键错误/空状态
4. 是否存在危险操作无确认
5. Desktop / Mobile 是否存在核心任务断裂

先列出问题清单（按严重程度排序），经我确认后再修复。
不得新增业务能力。
```

### 7.3 Gate 1：Prototype Review（单人协议）

按 0.4 节五步协议执行，AI 复审使用**产品负责人角色**（附录 B.1）。检查项：

```markdown
- [ ] 页面流转与 Interaction Design 一致
- [ ] 核心任务 100% 可走通，无断点
- [ ] 核心状态已覆盖（对照状态矩阵）
- [ ] 权限差异有体现
- [ ] 危险操作有明确确认
- [ ] Desktop / Mobile 核心流程完整
- [ ] （如执行）真实用户试用发现的问题已处理或记录
```

记录归档至 `docs/05_prototype/prototype_review.md`。**Gate 1 通过后业务与交互冻结，之后修改走附录 C。**

---

# Phase 4：Engineering Design

## Stage 8：架构设计（前端规范 + 前后端边界 + 后端架构）

### 个人执行要点

- 时间盒：0.5~1 天
- 个人项目架构第一原则：**选你能独立运维的最简方案**。单体优先于微服务，BaaS 优先于自建中间件——你的运维人力是 1 个人。
- 前置条件：Gate 1 = APPROVED

### 产出与要素

**8.1 前端设计规范** `docs/06_architecture_design/frontend_design_spec-v1.0.md`：页面清单（与 PG 编号一致）/ 结构层次 / 跳转关系 / 前端职责 / 响应式 / 与 Prototype 对应关系。

**8.2 前后端边界** `frontend_backend_boundary_spec-v1.0.md`：

| 功能/操作 | 用户动作 | 前端职责 | 后端职责 | 输入 | 输出 | 状态变化 |
|---|---|---|---|---|---|---|

另明确：哪些数据由后端提供 / 哪些逻辑只能后端决定 / 哪些操作必须调 API / 成功条件以后端为准 / 网络·权限·业务错误的边界。

**8.3 后端架构** `docs/07_backend_design/architecture_spec.md`：

- 服务边界与模块划分（个人项目默认单体 + 清晰分层）
- **安全架构**：认证方式、授权模型、越权防护、传输与存储加密
- **可观测性（最简版）**：结构化日志字段约定 + 至少 3 个核心指标（错误率/延迟/关键业务量）
- 每条 NFR 的架构承载方案

### 冲突优先级

```text
Business Model > Interaction Design > Prototype > Architecture > Figma
```

不确定项标记 [CONFLICT] / [TBD-*]，不自行裁决。

### 质量门禁

- 页面与 Prototype 一一对应
- 每条 NFR 有架构承载方案
- 认证授权与最简可观测性方案已定义

### 提示词

```text
结合你的目录，`05_prototype` 设为可选参考即可；核心输入应以 `03_problem_modeling` 和 `04_interaction_design` 为准。

# 后端架构设计 Agent Team Prompt

请创建一个 Agent Team，为本项目产出后端架构设计文档。当前阶段仅允许阅读资料、进行必要的官方技术调研、设计与撰写架构文档。严禁编写实际后端代码、数据库迁移、部署配置或调用真实业务系统。

## 项目资料目录

先扫描并读取 `docs/` 下实际存在的 Markdown、图片和链接资料，按以下目录理解其定位：

- `docs/00_setup/`：项目背景、术语、目标、范围、已有技术与环境约束
- `docs/01_market_research/`：市场研究，理解目标用户、场景和价值主张
- `docs/02_competitor_analysis/`：竞品能力、差异化、可借鉴与应避免的设计
- `docs/03_problem_modeling/`：后端设计的核心事实来源，包括领域对象、业务规则、流程、角色、问题边界
- `docs/04_interaction_design/`：用户操作流程、页面状态、异常反馈、审核交互和前后端协作线索
- `docs/05_prototype/`：可选参考。若存在 Figma 链接、截图或原型说明，只用于核对关键交互和状态；若为空或不可读取，不得阻塞架构设计，也不得自行补造原型文档
- `docs/06_architecture_design/architecture.md`：已有架构文档。若存在，先阅读并评估，保留其中仍有效的内容；不要未经说明地覆盖有效结论

优先级规则：

1. 已确认的 `03_problem_modeling` 业务规则优先。
2. `04_interaction_design` 用于补充用户操作、状态和异常路径。
3. 原型仅为辅助验证材料，不能替代业务规则或成为后端设计的唯一依据。
4. 资料冲突、缺失或表述不清时，记录为待确认项，不得自行虚构。

## 阶段门禁

### 阶段一：只读分析与计划

此阶段不得修改任何文件。

1. 列出实际读取的文件。
2. 建立输入追溯表：已确认事实、假设、冲突、缺失项及其架构影响。
3. 输出 Agent Team 的工作计划、分工、预期文档列表和关键待决策项。
4. 等待用户明确批准计划。

### 阶段二：架构草案

仅在用户批准阶段一计划后执行。

允许修改范围仅限：

`docs/06_architecture_design/`

所有文档在用户最终确认前必须标记为 `Draft`。不得把任何结论标记为已批准，也不得进入实现阶段。

## Agent Team 分工

### Agent A：领域与服务架构师

基于 `03_problem_modeling` 和 `04_interaction_design`，设计：

- 系统边界、模块边界与服务职责
- 核心领域实体、关系、生命周期和状态机
- 业务命令、查询、异步任务、事件与一致性要求
- 文件上传、任务状态、审核对象、审核记录等能力的服务职责
- 幂等、审计、失败恢复、并发冲突等关键业务规则

输出：`docs/06_architecture_design/01_domain-and-service-architecture.md`

### Agent B：接口、任务与审核工作流架构师

设计：

- 前后端接口边界、请求/响应原则、错误模型和权限边界
- 同步请求、异步任务、进度查询、通知和重试机制
- 审核流程的状态、角色、操作、撤回、退回、修改、重新提交、超时与审计
- 前端页面状态与后端状态的映射关系

仅当资料明确存在 Agent 工作流、人工审批中断恢复或模型工具调用需求时，才评估 LangGraph HITL 或 MCP；否则明确说明不采用及理由。

输出：`docs/06_architecture_design/02_api-workflow-and-review.md`

### Agent C：安全、可靠性与运行架构师

设计：

- 身份认证、授权、角色/组织/租户隔离
- 文件安全、数据分级、隐私、保留与审计
- 性能、容量、可用性、备份、恢复、限流、监控、日志与告警
- 外部系统集成、部署边界、成本与运维风险
- 缺失的非功能性需求，以及其对架构的影响

输出：`docs/06_architecture_design/03_security-reliability-and-operations.md`

### Agent D：架构审查员

不重复设计。审查前三位成员的结果，检查：

- 每项关键设计是否可追溯至现有资料
- 业务状态、接口、权限、数据与异常处理是否一致
- 是否遗漏幂等、并发、失败恢复、审计或数据泄露风险
- 是否存在为了技术而引入 MCP、Agent 或复杂工作流
- 是否存在不可验证的假设或未说明的技术取舍

输出：`docs/06_architecture_design/04_architecture-review.md`

## 官方技术调研规则

只围绕明确待决策问题进行调研，优先使用官方一手资料。每条调研结论必须包含：问题、官方链接、结论、对本项目的影响、采用或不采用的理由。

- 涉及 MCP：查阅 Model Context Protocol 官方规范，关注 host/client/server 边界、tools/resources/prompts、权限和安全。
- 涉及人工审核中断与恢复：查阅 LangGraph 官方 HITL、interrupt、checkpoint、resume、幂等与失败恢复文档。
- 普通的文件上传、任务状态或审核查询不默认引入 MCP、LangChain 或 LangGraph。

调研日志输出到：

`docs/06_architecture_design/00_research-and-input-traceability.md`

## Lead 职责

Lead 负责整合，而不是机械汇总：

1. 消解各专题文档的冲突。
2. 为关键取舍给出推荐方案与替代方案。
3. 删除无业务依据的复杂技术设计。
4. 更新或重写 `docs/06_architecture_design/architecture.md`，形成唯一的集成架构草案。
5. 为每项不可轻易逆转的决策建立 ADR，存放在 `docs/06_architecture_design/adr/`。
6. 在所有文档中保留来源、假设、风险和待确认项。

`architecture.md` 至少包含：

- 架构目标、范围与非目标
- 输入追溯与关键假设
- 系统上下文与模块职责
- 核心领域模型、状态机和数据流
- API、异步任务、事件和前后端协作原则
- 审核与人工介入设计
- 数据、安全、可靠性、可观测性与运维策略
- 技术调研结论，以及 MCP/HITL 的采用或不采用理由
- ADR 摘要、风险、开放问题和验证计划

## 最终输出要求

完成后仅汇报：

1. 实际读取的输入资料及关键缺失项。
2. 新增或更新的 `docs/06_architecture_design/` 文档路径。
3. 推荐架构方向与三项最重要的决策。
4. MCP、LangGraph HITL 是否需要引入，以及理由。
5. 需要用户确认的开放问题。

不要输出或编写实际后端代码。
```

---

## Stage 9：技术开发框架

### 个人执行要点

- 时间盒：2 小时。**个人项目技术选型的最高原则是"熟练度 > 流行度"。**
- 依赖审计用免费工具即可（Dependabot / npm audit / pip-audit）

### 提示词

```text
【角色】你是一位有 5 年经验的技术架构师。

【输入】docs/06/07 的三份架构文档

【任务】确定并冻结技术栈：前端框架 / UI 组件方案 / 状态管理 /
后端框架 / ORM / API 风格 / 测试框架 / 构建部署方式。

【约束】
- 只确定实现所必需的技术
- 每项说明选择理由；个人项目优先我熟练的技术栈
- 每个核心依赖注明：锁定版本、License、维护活跃度、高危 CVE 情况
- 不允许为"看起来完整"添加无实际需求的组件

【完成前自检】
- [ ] 全部核心依赖通过漏洞扫描（高危/严重 CVE = 0 未处置）
- [ ] 每个选型是我能独立运维的
```

### 质量门禁

- 技术栈冻结，核心依赖通过漏洞扫描

---

## Stage 10：数据模型

### 个人执行要点

- 时间盒：半天
- 个人项目常犯的错：敏感字段（邮箱、手机号、token）明文落库且日志乱打。数据分级这一步不许跳。

### 提示词

```text
【角色】你是一位有 5 年经验的数据架构师。

【输入】
1. docs/03_problem_modeling/business_model.md
2. docs/07_backend_design/architecture_spec.md

【产出】docs/07_backend_design/data_model_spec.md

【必须包含】
1. ER 图、表清单、字段定义、主外键、唯一约束、索引、状态字段
2. 数据生命周期
3. 数据分级：敏感字段标注分级（公开/内部/敏感/高敏），
   高敏字段注明加密与脱敏策略
4. 审计字段（created_at / updated_at 等）
5. 数据迁移要求

【约束】
- 必须承载 Business Model 全部实体和规则，不新增未确认实体
- 不把"页面字段"直接等同于"数据库字段"
- 无法确定的内容标记 [TBD-BE]

【完成前自检】
- [ ] 每个业务实体有对应表或不落库说明
- [ ] 敏感字段 100% 完成分级标注
```

### 质量门禁

- 核心实体可落库，敏感字段分级覆盖率 100%

---

## Stage 11：API Contract

### 个人执行要点

- 时间盒：半天
- API Contract 是前后端并行开发（哪怕都是你+AI 并行）的前提，契约冻结后 Stage 15/16 才能互不干扰

### 提示词

```text
【角色】你是一位有 5 年经验的后端架构师。

【输入】（权威优先级从高到低）
1. docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
2. docs/07_backend_design/architecture_spec.md
3. docs/07_backend_design/data_model_spec.md

【产出】docs/07_backend_design/api_interface_spec.md

【必须包含】
1. API 清单（API-001...）/ Method + Path
2. Request / Response Schema
3. 错误码（唯一、分段、含语义）
4. 鉴权要求（每个端点：匿名/登录/角色）
5. 幂等 / 分页 / 排序 / 筛选规范（适用时）
6. 限流策略（至少覆盖登录与敏感操作端点）

【约束】
- API 只能来自前后端边界文档，不得新增业务 API
- 返回结构不得泄露敏感字段（对照数据分级核对）
- FastAPI 项目给出 Pydantic Schema 设计建议，但不生成实现代码

【完成前自检】
- [ ] 边界文档中每个"必须调 API"的操作都有对应 API-xxx
- [ ] 每个端点鉴权要求与权限矩阵一致
- [ ] 错误码全局唯一，Response 无敏感字段泄露
```

### 质量门禁

- 边界能力 100% 有 API 或明确不需要
- 鉴权与权限矩阵 100% 一致

### Gate 2：Architecture & Contract Review（单人协议）

按 0.4 节五步协议执行，AI 复审使用**架构评审员角色**（附录 B.3），记录归档至 `docs/07_backend_design/gate2_review.md`。**通过后架构、数据模型、API 契约冻结。**

---

# Phase 5：产品交付资产

## Stage 12：PRD

### 个人执行要点

- 时间盒：2~4 小时
- 个人版 PRD 可以短，但**验收标准（AC）一条都不能少**——它是 Stage 17 测试用例的来源，也是你判断"做完没有"的唯一标准

### 提示词

```text
【角色】你是一位有 5 年经验的产品经理。

【输入】全部已冻结资产（business_model / interaction_design /
prototype_review / boundary / api_interface_spec）

【产出】docs/08_prd/prd_document.md

【必须包含】
1. 需求背景与用户目标
2. 功能清单（关联 BR-xxx）
3. 核心流程与关键交互
4. 状态与异常、权限
5. 数据与接口关联（API-xxx）
6. 验收标准（AC-xxx）：每条可测试、可二元判定，
   标注关联的 BR-xxx / API-xxx
7. Out of Scope

【约束】
- 综合交付文档，不得重新定义业务
- 上游冲突标记 [CONFLICT]，不自行裁决
- AC 禁止"体验良好""响应迅速"式表述

【完成前自检】
- [ ] 每条 AC 可执行 Pass/Fail 判定
- [ ] 每条 BR 至少被一条 AC 覆盖
```

### 质量门禁

- BR → AC 覆盖率 100%

---

## Stage 13：Figma High-Fidelity UI 设计

### 个人执行要点

- 时间盒：0.5~1 天
- 个人项目强烈建议**直接使用成熟组件库（如 shadcn/ui、Ant Design）的默认 Design Tokens 做裁剪**，不要从零设计视觉系统——你的竞争力在产品逻辑，不在像素
- 产出底线：design_tokens.json + component_spec.json，高保真稿可只覆盖关键页面

### 要求（与企业版一致，规模可缩）

- Design Tokens：Color / Typography / Spacing / Radius
- 组件规格：只定义实际使用的组件及其 variants/states
- 关键页面 Desktop + Mobile 可验证
- 视觉不重新设计业务；与 Prototype 冲突时按附录优先级裁决

### 质量门禁

- design_tokens.json 与 component_spec.json 形成
- 关键页面高保真稿与 Prototype 无业务行为冲突

---

# Phase 6：AI Implementation Preparation

## Stage 14：CLAUDE.md / AGENTS.md 项目工程上下文

### 目标

把设计资产"编译"为 AI Coding Agent 可持续遵循的工程上下文。**对单人开发者，这份文件还有第二个作用：它是你每次新开会话时无需重复解释项目背景的原因。**

### 提示词

```text
【角色】你是负责 AI 工程化的资深 Tech Lead。

【输入】当前项目全部已冻结设计资产（路径引用，不复制全文）

【任务】在 Stage 2 创建的根目录 AGENTS.md 初始版基础上，
补充设计资产约束，生成完善版 CLAUDE.md / AGENTS.md。

【必须包含】
1. 项目目标与目录结构
2. 技术栈与架构边界
3. 前后端职责、API 约束（鉴权与错误码约定）
4. 数据层约束（含敏感数据处理红线）
5. UI / Design Token 约束
6. 测试要求、运行/构建/部署方式
7. 禁止行为（不改冻结资产 / 不引未审计依赖 / 不提交密钥 /
   不跳过验证）
8. 规范冲突处理规则

【约束】
- 只保留稳定、长期有效、高频需要遵守的规则
- 具体业务细节使用文档路径引用
- 不新增设计文档中没有的业务规则
- 全文 ≤ 300 行

【完成前自检】
- [ ] 全新会话仅凭此文件 + 引用路径即可正确开始工作
- [ ] 全部禁止行为为可判定的祈使句
```

### 质量门禁

- CLAUDE.md ≤ 300 行
- 新开空白会话实测：AI 能正确说出项目边界与红线

---

# Phase 7：AI Implementation

## Stage 15：后端 MVP 源码构建

### 实现纪律（单人版同样不可豁免）

1. **一个模块一个新会话**，以 Task Brief（附录 E）开场
2. 每个 API 同步生成测试用例（TC-xxx），关联 API/BR 编号，汇入 `docs/11_test/test_plan.md`
3. 小步提交，Conventional Commits
4. 每完成一个模块即运行自动化验证

### 提示词

```text
【角色】你是资深后端工程师，严格按契约实现，不做设计决策。

【输入】（权威优先级从高到低）
1. CLAUDE.md / AGENTS.md
2. docs/07_backend_design/api_interface_spec.md（本次范围见 Task Brief）
3. docs/07_backend_design/data_model_spec.md
4. docs/07_backend_design/architecture_spec.md
5. docs/03_problem_modeling/business_model.md（仅相关 BR 章节）

【任务】实现后端 MVP（本次会话范围：【{模块/API 编号}】）。

【要求】
1. 严格按 data_model_spec 实现数据层，按 api_interface_spec 实现 API
2. 业务规则只能来自 business_model.md
3. 完成错误处理、鉴权和日志基础能力
4. 每个 API 同步生成测试用例（TC-xxx）并关联编号
5. 完成迁移脚本
6. 完成后执行自动化验证并输出结果

【禁止】
- 不新增 API / 实体 / 业务规则 / 未审计依赖
- 不硬编码密钥与连接串
- 不静默吞异常；TODO 必须关联跟踪

【冲突处理】发现规范冲突：停止修改，报告 [CONFLICT] 及冲突条款。

【完成前自检】
- [ ] 范围内 API 全部实现且接口测试通过
- [ ] 迁移可正向执行、可回滚
- [ ] 无规范外产出，输出实现报告（范围/测试证据/偏离/遗留）
```

### 质量门禁

- 范围内 API Contract 验证通过率 100%
- 核心 BR 测试全部通过

---

## Stage 16：前端 MVP 源码构建

### 提示词

```text
【角色】你是资深前端工程师，严格按规范实现，不做产品决策。

【输入】（权威优先级从高到低）
1. CLAUDE.md / AGENTS.md
2. docs/06_architecture_design/frontend_design_spec-v1.0.md
3. docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
4. docs/07_backend_design/api_interface_spec.md
5. docs/09_figma_highfi/design_tokens.json + component_spec.json

【任务】实现前端 MVP（本次会话范围：【{页面编号}】，见 Task Brief）。

【要求】
1. 页面与 frontend_design_spec 一一对应
2. 使用 design_tokens.json 的 Tokens，禁止硬编码颜色/字号/间距
3. 使用 component_spec.json 的共享组件
4. Loading / Empty / Error / No Permission / Submitting 状态必须实现
5. 按 api_interface_spec 对接 API，区分网络/权限/业务错误
6. 完成组件和页面级验证

【禁止】
- 不新增规范外的页面、功能、业务规则
- 不在前端做权限最终判定（判定以后端为准）
- 不绕过共享组件自行实现

【完成前自检】
- [ ] 关键状态全部实现且可演示
- [ ] 视觉值 100% 来自 Tokens
- [ ] API 字段与 Contract 完全一致
- [ ] 输出实现报告
```

### 质量门禁

- 核心状态完整，API 对接符合 Contract
- 无硬编码样式字面值

---

## Stage 16.5：代码评审门禁（Gate 3）——单人版最重要的 Gate

### 为什么单人更不能省

企业里 AI 代码至少还有同事看一眼；单人项目里，**如果你不看，就是没人看**。本 Gate 用三层替代"同事"：

```text
第一层：CI 自动化检查（机器评审，每次 push）
  lint → 类型检查 → 测试 → 覆盖率 → 安全扫描 → 契约比对

第二层：冷却期自评（换帽评审）
  代码写完至少隔夜，按附录 D Checklist 逐条审查自己的代码
  ——用 diff 视图而不是 IDE，你会更客观

第三层：AI 独立复审（全新会话）
  附录 B.4 安全评审员角色；输入仅限代码 diff + 冻结资产
  它会抓到你"看顺眼了"的问题
```

### CI 自动化检查配置提示词

```text
【角色】你是 CI 质量工程师。

【任务】为当前项目配置 GitHub Actions 质量流水线。

【必须覆盖】
1. Lint 与格式检查（0 error）
2. 静态类型检查（0 error）
3. 单元 + 接口测试全部通过
4. 覆盖率：核心 BR 路径有用例；整体行覆盖率 ≥ 70%（个人项目阈值）
5. 安全扫描：SAST（高危/严重 = 0）+ 依赖 CVE + gitleaks
6. 契约一致性：实现端点与 api_interface_spec 比对，无多余/缺失

【约束】以项目实际技术栈为准，单条 workflow 文件，不引入无关工具。
```

### 质量门禁（全部可度量）

- CI 全绿（lint/type/test = 0 error，覆盖率达标）
- 安全扫描高危/严重 = 0，secret 告警 = 0
- 契约比对多余/缺失端点 = 0
- 附录 D Checklist 自评完成（冷却期后）
- AI 复审问题逐条回应完毕
- 记录归档 `docs/11_test/code_review_report.md`

---

# Phase 8：验证与交付

## Stage 17：前后端联调 / E2E 验证

### 个人执行要点

- 时间盒：0.5~1 天
- 先用 **AI QA 工程师角色**（附录 B.5）生成对抗性测试场景清单（并发、重复提交、异常输入、越权尝试），再逐条执行——单人最大的测试盲区是"只测自己想到的路径"

### 提示词

```text
【角色】你是资深测试架构师。

【输入】全部冻结资产 + docs/11_test/test_plan.md

【任务】执行端到端联调验证，输出 docs/11_test/e2e_report.md。

【验证范围】
1. 核心业务流程（对照 AC-xxx 逐条）
2. 权限（对照权限矩阵逐角色）
3. 正常/异常状态、API Contract 一致性
4. 数据一致性、并发/重复提交边界
5. 安全回归抽查：越权、注入、敏感字段泄露
6. 性能冒烟：核心接口对照 NFR-xxx 目标

【追溯要求】
- E2E 场景编号（E2E-xxx）关联 AC/BR/API
- 输出追溯矩阵：BR → AC → TC/E2E → 结果，BR 无覆盖即阻塞

【问题处理】
标记归属：Business / Interaction / Frontend / Backend / API Contract /
Infrastructure。不直接修改上游业务规则，走附录 C 变更控制。
```

### 质量门禁

- 核心流程通过率 100%，阻塞/严重缺陷 = 0
- 追溯矩阵完整（BR 覆盖率 100%）

### Gate 4：Release Readiness（单人协议）

按 0.4 节五步协议执行，AI 复审使用**发布经理角色**（附录 B.6）。核对：全部资产齐套 / 测试报告归档 / 遗留问题有处置计划 / 回滚方案就绪。记录归档至 `docs/12_deployment/gate4_review.md`。

---

## Stage 18：CI/CD 与部署

### 个人执行要点

- 时间盒：0.5~1 天
- 个人版目标：**一条命令能部署，一条命令能回滚，出事了有人（监控）告诉你**——做到这三点即达标

### 提示词

```text
【角色】你是资深 DevOps 工程师。

【输入】项目实际结构、Stage 9 技术栈、architecture_spec 可观测性设计。

【产出】
- docs/12_deployment/cicd_pipeline_spec.md
- docs/12_deployment/release_checklist.md
- 实际部署配置文件

【必须包含】
1. CI/CD：push 触发 Gate 3 全部自动化检查 → 构建 → 部署，
   prod 部署前需我手动确认（GitHub Actions environment 保护）
2. Dockerfile / docker-compose.yml（或 PaaS 配置）
3. 环境变量清单：敏感值走平台密钥管理，禁止硬编码入库
4. 健康检查（liveness / readiness）
5. 结构化日志 + 至少一个免费可用性监控（如 UptimeRobot）
   + 错误追踪（如 Sentry 免费档）
6. 数据持久化与备份策略（至少每日自动备份 + 恢复验证过一次）
7. 回滚方案（含数据库迁移回滚路径）
8. 发布前检查清单（release_checklist.md）

【约束】以实际代码为准，不假设不存在的服务，敏感信息零硬编码。

【完成前自检】
- [ ] 从零环境可完整部署
- [ ] 回滚在测试环境实际演练过一次
- [ ] 备份恢复实际验证过一次
- [ ] 监控告警能真实触达我（发过一次测试告警）
```

### 质量门禁

- 一键部署、一键回滚均真实验证过
- 备份恢复演练通过
- 测试告警成功触达

---

# 附录 A：阶段职责速查（单人版）

| 阶段 | 你戴的帽子 | AI 的角色 | 最小可交付 |
|---|---|---|---|
| 1-2 环境规范 | DevOps | 配置执行者 | 安全基线 + project_rules |
| 3-4 调研竞品 | 创始人 | 分析师 + 魔鬼代言人 | 两份 ≤3 页报告 |
| 5 业务建模 | 产品负责人 | 业务架构师 | BR + NFR + 权限矩阵 |
| 6-7 交互原型 | 交互设计师 | 原型构建师 | 可走通的 Prototype |
| 8-11 工程设计 | 架构师 | 设计起草者 | 边界表 + ER + API 清单 |
| 12-13 PRD/视觉 | 产品经理 | 文档整理者 | PRD(AC) + Tokens |
| 14 AI 上下文 | Tech Lead | 编译者 | CLAUDE.md ≤300 行 |
| 15-16 实现 | 技术负责人 | 实现者（你评审） | 代码 + 测试 |
| 16.5 评审 | **评审者（换帽）** | 安全评审员 | Gate 3 记录 |
| 17 联调 | QA 负责人 | QA 工程师 | E2E 报告 + 追溯矩阵 |
| 18 部署 | SRE | 配置执行者 | 可部署可回滚可监控 |

---

# 附录 B：AI 虚拟团队提示词集

> 使用纪律：**全部在全新会话中运行**；输入仅限"冻结资产 + 待评审产出物"；
> 不告诉评审 AI"我的意图是什么"；结论逐条回应。

## B.1 产品负责人（Gate 1 / Stage 5 评审用）

```text
【角色】你是挑剔的产品负责人，为业务结果负责。你不认识提交者，
只根据以下资产判断。

【输入】docs/03_problem_modeling/business_model.md
（评审 Prototype 时附加 interaction_design_summary.md 与原型说明）

【任务】以挑剔视角评审：
1. 业务规则是否有漏洞：哪些场景没有 BR 覆盖？哪些 BR 互相矛盾？
2. 权限矩阵是否有越权缝隙？
3. MVP 范围是否过大？哪些功能砍掉后产品仍成立？
4. NFR 是否与业务规模匹配（过高是浪费，过低是风险）？

【输出】问题清单，每条标注：严重程度（阻塞/严重/建议）+ 理由 +
建议动作。不确定处标记 [TBD-BIZ]，禁止替我做业务决策。
```

## B.2 魔鬼代言人（Stage 3-6 探索阶段用）

```text
【角色】你是专门唱反调的魔鬼代言人。你的职责不是鼓励我，
而是在我投入数周开发前，找出这个项目最可能失败的原因。

【输入】{当前阶段产出物}

【任务】从以下角度逐一攻击：
1. 需求真实性：这个痛点是真实的还是我臆想的？证据够吗？
2. 竞争：为什么现有方案不能被"够用"地使用？
3. 个人可行性：以一人之力，这个范围现实的完成概率多大？
4. 可持续性：做完之后，谁会用？怎么让人知道？

【输出】按杀伤力排序的反对意见清单。每条最后附一个
"如果能回答这个问题，反对即失效"的检验点。
```

## B.3 架构评审员（Gate 2 用）

```text
【角色】你是严格的架构评审员，以个人项目可运维性为最高标准。

【输入】architecture_spec.md / data_model_spec.md /
api_interface_spec.md / business_model.md（NFR 章节）

【任务】评审：
1. 每条 NFR 是否有可信的架构承载方案？
2. 是否存在过度设计：单人运维不了的组件、用不到的抽象层？
3. 契约完备性：前后端边界中的能力是否 100% 有 API 或明确豁免？
4. 安全缝隙：未鉴权端点、敏感字段泄露、缺失的幂等保护？
5. 数据模型能否承载全部 BR？

【输出】问题清单（阻塞/严重/建议 + 证据 + 建议动作）。
发现资产间矛盾标记 [CONFLICT]，禁止自行裁决。
```

## B.4 安全评审员（Gate 3 用）

```text
【角色】你是安全评审员。你不知道这段代码是谁写的，
也不知道作者的意图，只根据代码与规范判断。

【输入】本次代码变更（diff）+ api_interface_spec.md +
business_model.md（权限矩阵章节）

【任务】逐项审查：
1. 硬编码密钥 / Token / 连接串
2. 注入风险（SQL / XSS / 命令注入）
3. 越权：每个端点的鉴权检查是否与权限矩阵一致；
   是否存在仅靠前端隐藏、后端无校验的操作
4. 敏感字段是否出现在 API 响应或日志中
5. 外部输入是否全部校验
6. 异常处理是否泄露内部细节
7. 新增依赖是否陌生（可能为幻觉依赖）

【输出】按严重程度排序的问题清单 + 具体位置 + 修复建议。
```

## B.5 QA 工程师（Stage 17 用）

```text
【角色】你是以"搞坏系统"为乐的 QA 工程师。你只测试作者
没想到的路径。

【输入】prd_document.md（AC 清单）+ api_interface_spec.md +
权限矩阵

【任务】生成对抗性测试场景清单：
1. 每个 AC 的边界变体（空值、极限值、非法格式）
2. 并发与重复：双击、刷新重提、并发修改同一资源
3. 权限绕过尝试：直接访问无权限 URL、篡改 ID 访问他人数据
4. 状态陷阱：流程中途断网/关页面后的恢复
5. 数据一致性：多步操作部分失败

【输出】编号场景清单（关联 AC/BR），每条含：前置条件 / 操作 /
预期结果 / 实际结果（留空待执行）。
```

## B.6 发布经理（Gate 4 用）

```text
【角色】你是保守的发布经理，只对"线上不出事"负责。

【输入】e2e_report.md + 全部 Gate 记录 + release_checklist.md +
遗留问题清单

【任务】核对发布就绪度：
1. Gate 1-3 记录是否齐套且结论为 APPROVED/CONDITIONAL
2. 追溯矩阵是否完整（BR 覆盖率 100%）
3. 遗留问题是否全部有处置计划（没有"先上线再说"的阻塞项）
4. 回滚方案是否经过演练、备份恢复是否验证过
5. 监控告警是否真实触达

【输出】GO / NO-GO 结论 + 风险清单。任何一项不满足即 NO-GO，
不得通融。
```

---

# 附录 C：简版变更控制（单人 CCR）

冻结资产要改时，执行以下流程。**核心目的：阻止"顺手改"——顺手改是 SDD 流程崩溃的开端。**

| 级别 | 定义 | 处理 |
|---|---|---|
| L1 | 不影响行为（文案/注释/样式微调） | 直接改，记入 change_log.md |
| L2 | 局部设计（单页交互/非破坏性 API 字段新增） | 登记 → 自问三问 → 改 → 同步下游 |
| L3 | 业务规则/契约（BR 修改/破坏性 API 变更） | 登记 → **强制隔夜** → 影响分析 → 改 → 受影响 Gate 复审 |

**L2/L3 自问三问：**

1. 这个变更影响哪些下游资产？（沿权威链向下找：契约 → 代码 → 测试 → CLAUDE.md）
2. 需要重走哪个 Gate？
3. CLAUDE.md / AGENTS.md 要不要同步？（最容易遗忘的一项）

**登记格式**（docs/13_changes/change_log.md）：

```markdown
| 日期 | 级别 | 变更内容 | 影响资产 | 回归动作 | 状态 |
|---|---|---|---|---|---|
```

---

# 附录 D：AI 生成代码评审 Checklist（冷却期自评 + AI 复审共用）

## D.1 忠实性

- [ ] 实现范围与 Task Brief 完全一致，无擅自扩展
- [ ] API 与 api_interface_spec 逐字段一致
- [ ] 业务规则与 BR-xxx 一致，无"AI 理解性改写"
- [ ] 无幽灵产物：规范外的端点、实体、组件、配置

## D.2 安全性

- [ ] 无硬编码密钥/Token/连接串
- [ ] 外部输入全部校验（注入/XSS）
- [ ] 鉴权与权限矩阵一致，无前端单方面判定
- [ ] 敏感字段不出现在响应与日志
- [ ] 无未审计的新依赖

## D.3 正确性

- [ ] 边界条件（空值/极限/并发/重复提交）
- [ ] 多步写入有事务或补偿
- [ ] 异常不静默吞掉，错误信息不泄露内部细节
- [ ] 无无跟踪的 TODO

## D.4 质量

- [ ] 测试覆盖本次变更且通过
- [ ] 命名结构符合 project_rules.md，无死代码
- [ ] 视觉值全部来自 Design Tokens
- [ ] Commit 粒度合理、信息规范

## D.5 AI 幻觉信号

- [ ] 引用的依赖/API/配置全部真实存在
- [ ] 注释与链接真实有效
- [ ] 测试断言的是真实行为，非"为过测试而写"
- [ ] 无被注释掉的失败尝试代码残留

---

# 附录 E：任务级 Task Brief 模板

```text
【Task Brief】
任务编号：TASK-xxx
日期：____

## 本次范围（Only）
- 实现：{API-003, API-004 / PG-002}
- 关联契约：{文件路径#章节}
- 关联验收标准：{AC-xxx}

## 不在本次范围
- {相邻但本次不做的内容}

## 输入资产（按优先级）
1. CLAUDE.md
2. {直接相关规范，≤ 3 份}

## 完成定义（DoD）
- [ ] {可执行验证命令，如 pytest tests/xxx 全绿}

## 禁止事项
- 不触碰范围外文件
- 不修改任何冻结资产
- 发现冲突输出 [CONFLICT] 并停止

## 会话结束输出
- 实现摘要 / 验证证据 / 偏离与遗留
```

---

# 附录 F：防幻觉标记速查

```text
[TBD-BIZ] 待业务确认    [TBD-UX] 待交互确认    [TBD-FE] 待前端确认
[TBD-BE]  待后端确认    [TBD-INFRA] 待基础设施  [CONFLICT] 资产冲突
[ASSUMPTION] 仅为假设
```

规则：外部数据必须有来源；推测必须标记；不为"文档完整"编造内容；
**标记条目必须进入跟踪清单并有确认计划，不允许标记后无人认领（单人项目里"认领人"就是未来的你，请对他负责）。**

---

# 快速参考：各阶段一句话总结

| Stage | 一句话 | Gate |
|---|---|---|
| 1 | 环境 + 安全基线，30 分钟免除密钥泄露风险 | — |
| 2 | 规范落盘，给三个月后的自己看 | — |
| 3-4 | 验证值得做，找到差异化 | — |
| 5 | 业务世界 + 量化 NFR + 狠心砍范围 | — |
| 6-7 | 让用户（或 AI 审计）先体验产品 | **Gate 1** |
| 8-11 | 工程四件套：边界/栈/数据/契约 | **Gate 2** |
| 12-13 | PRD 重 AC，视觉用现成组件库 | — |
| 14 | 设计编译成 AI 上下文，≤300 行 | — |
| 15-16 | Task Brief 驱动，一个模块一个会话 | — |
| 16.5 | 没人看你的代码，所以三层评审 | **Gate 3** |
| 17 | AI 扮 QA 专测你想不到的路径 | **Gate 4** |
| 18 | 一键部署、一键回滚、出事有人喊 | — |

---

# 最终原则

```text
调研（AI 主力，你验证，魔鬼代言人挑战）
   ↓
业务建模（BR + 量化 NFR + 狠心砍范围）
   ↓
交互设计 → Prototype
   ↓
★ Gate 1：冷却期 + 换帽 + AI 产品负责人复审
   ↓
工程四件套（选你能独立运维的最简方案）
   ↓
★ Gate 2：AI 架构评审员复审
   ↓
PRD（AC 不可省）+ Tokens（用现成组件库）
   ↓
CLAUDE.md（≤300 行，新会话的通行证）
   ↓
实现（Task Brief + 一个模块一个会话 + 小步提交）
   ↓
★ Gate 3：CI 机器评审 + 隔夜换帽自评 + AI 安全复审
   ↓
E2E（AI 扮 QA 专测你想不到的路径）+ 追溯矩阵
   ↓
★ Gate 4：AI 发布经理保守把关
   ↓
部署（一键部署 / 一键回滚 / 出事有人喊）
   ↓
反馈 → 简版 CCR（L3 强制隔夜）→ 回到对应阶段
```

> **企业流程的本质不是"人多"，而是"决策有依据、变更有痕迹、质量有第三方"。单人开发用三样东西补齐：冷却期替代"别人的时间"，AI 虚拟团队替代"别人的视角"，Checklist 机械执行替代"别人的责任心"。流程一步不省，只是每一步都轻到你愿意做。**
