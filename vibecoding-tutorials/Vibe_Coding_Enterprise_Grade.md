# 企业级 Vibe Coding 全流程教学文档

## 基于 SDD（Specification-Driven Development，规范驱动开发）

> **版本：v2.1**
>
> 说明：本文正文版本为 **v2.1**；仓库文件名 `____Vibe_Coding_SDD________v2.0.md` 为历史归档名，未随正文一并更名，版本口径以本文正文为准。
>
> 本版本在原流程基础上，重新梳理了 **业务建模 → 核心交互设计 → Interactive Prototype → 后端架构/数据/API → PRD → High-Fidelity Figma → CLAUDE.md/AGENTS.md → 前后端 MVP → 代码评审门禁 → 联调 → CI/CD 部署** 的关系。
>
> 核心原则：**先形成可验证的产品设计，再形成可执行的工程规范，最后让 AI 负责实现；AI 可以在探索阶段提出方案，但进入 Gate 后不得擅自改变已冻结的业务规则与交互约束。**

> **v2.1 修订要点**
>
> 1. 新增**三条贯穿线**：安全合规线、质量验证线、变更控制线（见 0.4）。
> 2. 新增 **Gate 1～4 统一门禁体系**与标准签核模板（见 0.5）。
> 3. 新增 **Stage 16.5：AI 代码评审与安全门禁**——AI 生成代码必须通过人类 Review 与自动化扫描后才能进入联调。
> 4. 补齐企业级缺口：非功能需求（NFR）、数据分级、供应链安全、可观测性、CI/CD 流水线。
> 5. 提示词工程规范化：统一**六段式提示词结构**（见 0.6），新增任务级 Task Brief 模板（附录 H）。
> 6. 新增**变更控制流程（CCR）**（附录 F），流程从"纯瀑布"升级为"带反馈回路的阶段门禁"。
> 7. 新增 **AI 生成代码评审 Checklist**（附录 G）。
> 8. 质量门禁全部改为**可度量指标**。

---

# 0. 核心理念与流程总览

## 0.1 开发哲学

> **先定规范，再写代码；先验证产品，再确定工程。**
>
> AI 在探索阶段可以帮助分析、推演和提出候选方案；在收口阶段，AI 是规范的执行者而不是业务决策者。人负责业务和产品的最终判断。

补充三条企业级底线：

1. **AI 生成的代码与人工编写的代码适用同一套质量与安全标准**，不因来源是 AI 而降低要求，也不因"AI 写的看起来对"而豁免评审。
2. **任何进入 Git 仓库的内容都必须可追责**：谁提出的需求、谁冻结的设计、谁评审的代码、AI 在哪个环节参与了什么。
3. **AI 的输出永远视为"未验证输入"**：文档、代码、测试，都必须经过对应 Gate 验证后才成为可信资产。

## 0.2 四层开发模型

```text
┌──────────────────────────────────────────────────────────────┐
│ ① Product Discovery / Business                               │
│    市场研究 → 竞品拆解 → 业务建模（含非功能需求）              │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ ② Product Design                                               │
│    核心交互设计 → Interactive Prototype → 人工评审 / Freeze    │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ ③ Engineering Design                                           │
│    前端规范/前后端边界 → 后端架构 → 技术框架 → 数据模型 → API │
│    同时形成 PRD 与 High-Fidelity Figma Design                 │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ ④ AI Implementation                                            │
│    CLAUDE.md / AGENTS.md → Backend MVP + Frontend MVP        │
│    → 代码评审门禁 → 联调 → CI/CD → 部署 → 监控反馈            │
└──────────────────────────────────────────────────────────────┘

贯穿四层的三条横切关注（三条贯穿线，详见 0.4）：
  安全合规线：安全基线 → 安全架构 → 安全扫描 → 安全回归
  质量验证线：BR → PG → API → TC → E2E 全链可追溯，每个 Gate 均为质量验证点
  变更控制线：任何冻结资产的修改必须走 CCR（见附录 F）
```

## 0.3 完整流程

```text
Stage 1  基础环境配置（含安全基线）
    ↓
Stage 2  项目初始化（规范 + AI 使用红线）
    ↓
Stage 3  市场调研
    ↓
Stage 4  竞品拆解
    ↓
Stage 5  业务建模（含非功能需求 NFR）
    ↓
Stage 6  核心交互设计
    ↓
Stage 7  Interactive Prototype（Figma Make）
    ↓
★ Gate 1：Prototype Review（产品行为冻结）★
    ↓
 ┌───────────────────────┬───────────────────────┐
 ↓                       ↓                       ↓
Stage 8               Stage 12                Stage 13
前端设计规范/           PRD需求文档             Figma High-Fidelity
前后端边界 +                                   UI设计
后端架构设计
 ↓
Stage 9  技术开发框架（含供应链安全）
 ↓
Stage 10 数据模型（含数据分级）
 ↓
Stage 11 API Contract
 ↓
★ Gate 2：Architecture & Contract Review（工程设计冻结）★
 └───────────────────────┬───────────────────────┘
                         ↓
Stage 14 CLAUDE.md / AGENTS.md 项目工程上下文
                         ↓
               ┌─────────┴─────────┐
               ↓                   ↓
Stage 15 后端 MVP          Stage 16 前端 MVP
               └─────────┬─────────┘
                         ↓
★ Gate 3：Stage 16.5 AI 代码评审 + 安全扫描 ★
                         ↓
Stage 17 前后端联调 / E2E 验证（含追溯矩阵）
                         ↓
★ Gate 4：Release Readiness Review ★
                         ↓
Stage 18 CI/CD 与部署
                         ↓
              监控 / 用户反馈
                         ↓
        ┌──── 变更控制（附录 F）────┐
        ↓                            ↓
   L1 直接修正                  L2/L3 回溯到对应阶段
   （文案/样式）               （设计/业务规则变更）
```

### 重要说明

- **Stage 7 Prototype 是产品行为验证，不等于生产代码。**
- **Stage 13 High-Fidelity Figma 是视觉与 Design System 验证，不是重新设计业务。**
- Stage 8～11 是工程设计链，解决系统、数据和接口如何实现。
- Stage 12 PRD 是综合交付文档，不是重新定义业务的上游文档。
- Stage 14 是把人类设计资产转换成 AI Coding Agent 可长期遵循的项目上下文。
- Stage 15/16 可以并行开发，前提是接口契约和工程边界已经冻结。
- **Stage 16.5 是不可跳过的门禁**：AI 生成代码无论看起来多"能跑"，未过 Gate 3 不得进入联调。
- **任何阶段发现上游冻结资产有问题，不得就地修改，必须走附录 F 的变更控制流程。**

## 0.4 三条贯穿线

v2.1 的核心升级：企业级流程不是只有"阶段"，还有贯穿所有阶段的横切关注点。

### 0.4.1 安全合规线

| 阶段 | 安全动作 | 产出 |
|---|---|---|
| Stage 1 | 安全基线：secret scanning、.gitignore 校验、pre-commit hook | 基线配置 |
| Stage 2 | AI 使用红线写入 CONVENTIONS | CONVENTIONS.md |
| Stage 5 | 识别敏感数据与合规要求（个保法/GDPR 等） | NFR + 合规清单 |
| Stage 8 | 安全架构：认证授权模型、加密、越权防护设计 | architecture_spec.md |
| Stage 9 | 依赖审计与 SBOM | 依赖清单 |
| Stage 10 | 数据分级与脱敏策略 | data_model_spec.md |
| Stage 11 | API 安全：鉴权、限流、注入防护 | api_interface_spec.md |
| Stage 16.5 | 自动化安全扫描 + 人工安全评审 | 扫描报告 |
| Stage 17 | 安全回归：越权/注入抽查 | E2E 报告 |
| Stage 18 | 密钥管理（不硬编码）、最小权限部署 | 部署清单 |

**红线（任何阶段适用）：**

- 密钥、Token、证书**永远不得**进入 Git 仓库、提示词、文档或 AI 上下文。
- 发送给 AI 的上下文中**不得包含真实用户数据/生产数据**。
- AI 引入的任何第三方依赖必须经过审计（见 Stage 9）。
- 发现密钥泄露：立即吊销 → 轮换 → 清理 Git 历史 → 复盘，四步缺一不可。

### 0.4.2 质量验证线

每个 Gate 都是质量验证点，且指标必须可度量（见 0.5）。测试资产与设计资产并行产生：

```text
Business Model (BR-xxx)
    → Interaction Design (PG-xxx)
        → API Contract (API-xxx)
            → 验收标准 (AC-xxx)     ← Stage 12 PRD 定义
                → 测试用例 (TC-xxx)   ← Stage 15/16 实现前生成
                    → E2E 场景 (E2E-xxx) ← Stage 17 执行
```

任一 BR 必须能向下追溯到至少一个 AC 与 TC；任一 TC 必须能向上追溯到一个 BR / AC / API。完整追溯矩阵（BR → AC → TC/E2E → 结果）见 Stage 17。

### 0.4.3 变更控制线

冻结后的资产不是不能改，而是**不能悄悄地改**。详见附录 F：

- L1（文案/样式级）：直接修改并记录，无需重开 Gate。
- L2（局部设计级）：修改 + 相关 Gate 复审 + 通知下游。
- L3（业务规则/契约级）：回到对应上游阶段，全链路影响分析后重走相关 Gate。

## 0.5 Gate 标准与签核

所有 Gate 使用统一模板，不允许"口头通过"。

```markdown
## Gate {编号} Review Record

日期：____
阶段：____
参与人（按角色签核）：
- 产品负责人：____（业务规则、需求范围）
- 技术负责人：____（架构、契约、代码质量）
- 设计负责人：____（交互、视觉，Gate 1/2 适用）
- 安全/合规：____（涉及敏感数据或外部依赖时）

### 准入条件
- [ ] 本阶段全部产出物已提交至 docs/ 对应目录
- [ ] 产出物版本号已更新，变更记录完整

### 检查项
（使用各阶段定义的、可度量的质量门禁清单）

### 问题回溯
| 问题 | 归属阶段 | 变更级别(L1/L2/L3) | 修改动作 | 状态 |
|---|---|---|---|---|
| | | | | |

### Gate 结论
- [ ] APPROVED：资产冻结，进入下一阶段
- [ ] CONDITIONAL：非阻塞问题转 L1 跟踪，阻塞问题为 0
- [ ] REJECTED：回溯到指定阶段

签核人签字：____
```

**四个 Gate 的职责：**

| Gate | 位置 | 冻结对象 | 签核重点 |
|---|---|---|---|
| Gate 1 | Stage 7 后 | 业务规则、交互行为 | 产品行为是否符合预期 |
| Gate 2 | Stage 11 后 | 架构、数据模型、API 契约 | 工程方案可行性、契约完备性 |
| Gate 3 | Stage 15/16 后 | 代码基线 | AI 代码质量与安全（Stage 16.5） |
| Gate 4 | Stage 17 后 | 发布版本 | 是否达到上线标准（Stage 17 末） |

## 0.6 AI 提示词工程规范

本文档中所有阶段提示词遵循统一的**六段式结构**。企业落地时，自建提示词也必须遵循：

```text
① 角色与能力边界   —— 你是谁，你能决定什么、不能决定什么
② 输入资产         —— 文档路径 + 权威优先级（冲突时听谁的）
③ 任务与产出       —— 做什么，输出到哪个文件，什么格式
④ 约束             —— 必须做（Must）/ 禁止做（Must Not）
⑤ 不确定处理       —— 信息不足时用 [TBD-*]/[CONFLICT] 升级，禁止编造（标记规范见附录 D）
⑥ 完成前自检       —— 输出前逐项核对的 Self-Check 清单
```

> 提示词的发散/收敛边界遵循**附录 C（Explore / Freeze 双模式）**：探索阶段允许 AI 提出候选方案，冻结阶段 AI 只能严格执行、发现冲突即停止并标记。

**上下文预算（Context Budget）规则：**

- 单次会话输入给 AI 的引用文档**不超过 5 份**，优先传"权威来源 + 直接上游"，其余用路径引用。
- 单份引用文档超过 300 行时，只传相关章节，并在提示词中注明章节范围。
- 实现类任务（Stage 15/16）**必须一个模块/特性一个新会话**，禁止在超长会话中连续实现多个模块（防止 context rot 导致规范遗忘）。
- 每个实现会话以 **Task Brief（附录 H）** 开场，而不是直接说"开始写代码"。

**提示词资产管理：**

- 阶段提示词纳入项目仓库版本管理（如 `docs/prompts/`），与文档同版本演进。
- 提示词修改需在变更记录中注明动机（哪些幻觉/偏差促使了修改），形成组织级的提示词知识库。

## 0.7 文档目录结构规范

```text
ProjectName/
├── docs/
│   ├── 01_market_research/
│   │   └── market_research_report.md
│   ├── 02_competitor_analysis/
│   │   └── competitor_analysis_report.md
│   ├── 03_problem_modeling/
│   │   └── business_model.md            # 含 NFR 与合规要求
│   ├── 04_interaction_design/
│   │   └── interaction_design_summary.md
│   ├── 05_prototype/
│   │   ├── prototype_spec.md
│   │   ├── prototype_review.md          # Gate 1 记录
│   │   └── prototype_link.md
│   ├── 06_architecture_design/
│   │   ├── frontend_design_spec-v1.0.md
│   │   └── frontend_backend_boundary_spec-v1.0.md
│   ├── 07_backend_design/
│   │   ├── architecture_spec.md         # 含安全架构与可观测性
│   │   ├── data_model_spec.md           # 含数据分级
│   │   ├── api_interface_spec.md
│   │   └── gate2_review.md              # Gate 2 记录
│   ├── 08_prd/
│   │   └── prd_document.md
│   ├── 09_figma_highfi/
│   │   ├── figma_highfi_design_link.md
│   │   ├── design_tokens.json
│   │   └── component_spec.json
│   ├── 10_ai_context/
│   │   ├── claude.md
│   │   └── agents.md
│   ├── 11_test/
│   │   ├── test_plan.md                 # TC 用例，可追溯 BR/API
│   │   ├── code_review_report.md        # Gate 3 记录
│   │   ├── e2e_report.md                # Stage 17 产出（E2E 报告）
│   │   └── gate4_release_readiness.md   # Gate 4 记录（发布就绪评审）
│   ├── 12_deployment/
│   │   ├── cicd_pipeline_spec.md
│   │   ├── docker_compose_spec.md
│   │   └── release_checklist.md
│   ├── 13_changes/
│   │   └── change_log.md                # 全部 CCR 记录
│   └── prompts/                         # 项目自定义提示词资产
├── src/
│   ├── frontend/
│   └── backend/
├── .claude/
│   └── settings.json
├── .env.example                         # 仅含键名与说明，无真实值
├── .gitignore                           # 必须覆盖 .env、密钥、证书
└── README.md
```

---

# Phase 1：基础搭建

## Stage 1：基础环境配置

### 目标

建立 AI 辅助开发的基础设施，包括项目级 Agent 配置、MCP、安全基线和必要的开发工具。

### 原则

**Agent Teams 不是强制基础设施。** 是否使用 Agent Teams，应根据任务复杂度决定：

```text
简单 / 确定性任务 → 单 Agent
并行研究任务     → Sub-Agent
多个独立领域并行 → Agent Teams
```

### 提示词

```text
【角色】你是一位熟悉 AI 工程化与研发安全基线的 DevOps 工程师。
仅负责基础设施与安全基线配置，不做业务或架构决策。

【输入资产】当前项目仓库现状（已有配置文件、.gitignore、Git 历史）；
本项目所选技术栈的官方文档 MCP 接入方式（如使用）。

【任务】请检查当前项目的 AI Coding 开发环境，并完成必要的项目级配置。

【要求】
1. 检查当前项目是否已有 Claude Code / Codex / Cursor 等项目级配置。
2. 按实际任务需要配置 MCP Server，不要为了"完整"而新增无关 MCP。
3. 对每个 MCP Server 完成连通性测试。
4. 如果当前任务不需要 Agent Teams，不要创建 Agent Teams。
5. 完成安全基线配置：
   - 校验 .gitignore 覆盖：.env*、*.pem、*.key、credentials*、secrets*
   - 配置 secret scanning（如 gitleaks）及 pre-commit hook
   - 生成 .env.example（只含键名与注释说明，禁止写入真实值）
   - 校验 Git 历史中不存在已提交的敏感信息，如存在立即停止并报告
6. 输出当前可用的 AI 工具、MCP、Agent 配置清单与安全基线检查报告。

【不确定处理】
- 无法完成连通性测试的 MCP 不得声称"已连通"，标记 [TBD-INFRA] 并给出排查结论（URL/网络/凭证）。
- 环境或凭证信息缺失时标记 [TBD-INFRA]，禁止编造配置或伪造测试证据。

【完成前自检】
- [ ] 每个 MCP 均有实际调用产生的连通性测试证据
- [ ] .env.example 中无任何真实密钥值
- [ ] secret scanning 对当前仓库全量扫描结果为 0 告警
- [ ] 未创建任务不需要的 Agent Teams / MCP
```

> 注意：**MCP 是工具/上下文接入协议，不要把 LangChain 本身表述成"MCP"。** LangChain/LangGraph 属于 LLM/Agent 编排技术。

### 质量门禁

- MCP 连通性测试通过率 100%
- 项目级 AI 配置可读取
- 不存在无必要的 Agent Teams / MCP 配置
- **secret scanning 全量扫描 0 告警**
- **.gitignore 覆盖全部敏感文件模式**

---

## Stage 2：项目初始化

### 目标

建立项目规范、目录结构和 AI Coding 的基本约定。

### 提示词

```text
【角色】你是一位有 5 年经验的 Tech Lead，熟悉 AI 辅助开发的团队协作模式。
只搭建目录与规范文档，本阶段不生成任何前后端实现代码。

【输入资产】项目基本信息（项目目标、目标技术栈方向）；本文档 0.7 节目录结构规范。

【任务】请为当前项目完成初始化。

【产出】
1. README.md
2. .claude/settings.json（如项目采用 Claude Code）
3. docs/CONVENTIONS.md

【CONVENTIONS 至少包含】
- 代码命名规范
- 目录组织规范
- Git 分支策略与 Commit 规范（Conventional Commits）
- PR 规范：AI 生成代码必须在 PR 描述中标注；禁止无评审直接合入主干
- 文档版本管理规范
- AI 生成代码 Review Checklist（引用附录 G）
- 测试与验证要求
- AI 使用红线：
  · 禁止将密钥、生产数据、用户隐私数据提供给 AI
  · 禁止 AI 静默修改已冻结的设计资产
  · 禁止提交未运行验证的 AI 生成代码
  · 禁止 AI 自行引入未审计的第三方依赖

【要求】
- 技术栈根据项目需求推荐，并说明理由
- 规范必须可执行，避免"尽量""建议"等模糊表述
- 不新增业务功能

【不确定处理】
- 项目信息不足以确定的规范项标记 [TBD-*] 并写明需谁提供，禁止臆造规则或假定技术栈。

【完成前自检】
- [ ] 每条规范都有明确的判定标准（能回答"违反它会怎样"）
- [ ] AI 使用红线逐条可执行、可检查
- [ ] 目录结构与本文档 0.7 节一致
```

### 质量门禁

- 项目目录完整（对照 0.7）
- 技术栈经过确认
- AI Coding 规范已形成，且 AI 使用红线写入 CONVENTIONS

---

# Phase 2：Product Discovery / Business Design

## Stage 3：市场调研

### 目标

明确市场、用户、痛点和机会，为后续竞品和业务建模提供外部事实依据。

### 提示词

```text
【角色】你是一位有 5 年经验的行业分析师。
你可在本阶段发散检索与推演（Explore 模式，见附录 C），但事实与推测必须分离。

【输入资产】项目领域与目标方向【{项目领域}】；可公开检索的市场信息（须标注来源）。

【任务】针对【{项目领域}】完成市场调研报告。

【产出】docs/01_market_research/market_research_report.md

【必须包含】
1. 市场规模与趋势
2. 目标用户画像
3. 核心用户痛点
4. 主要使用场景
5. 市场机会与风险

【约束】
- 所有外部数据必须标注来源和时间
- 无法验证的数据标记为 [TBD-RESEARCH]
- 区分事实、推测和结论（使用"事实：""推测：""结论："前缀）
- 不添加与当前项目无关的扩展建议

【完成前自检】
- [ ] 每个关键数字都有来源与时间
- [ ] 事实/推测/结论三类表述无混用
- [ ] 用户画像可直接支撑后续业务建模的角色定义
```

### 质量门禁

- 关键数据 100% 有来源与时间标注
- 用户画像得到业务方确认
- 未验证信息 100% 标记 [TBD-RESEARCH]

---

## Stage 4：竞品拆解

### 目标

从竞品中提取可借鉴的产品模式、AI 模式、技术模式和风险。

### 提示词

```text
【角色】你是一位有 5 年经验的产品与 AI Agent 架构专家。

【输入】docs/01_market_research/market_research_report.md

【任务】完成竞品分析。

【产出】docs/02_competitor_analysis/competitor_analysis_report.md

【竞品范围】【{竞品A}、{竞品B}、{竞品C}】

【每个竞品至少分析】
1. 产品定位
2. 核心功能
3. 核心用户流程
4. AI 使用场景
5. Prompt / Agent / Skill / MCP / Tool（公开可验证时才分析）
6. 技术架构推测（明确证据来源）
7. 商业模式
8. 用户评价
9. 最值得借鉴的设计
10. 最需要规避的坑

【约束】
- 区分"公开事实"和"源码/公开资料推测"
- 源码级分析只有在有源码证据时进行
- 不要把推测写成事实
- 最后提供横向对比矩阵

【完成前自检】
- [ ] 每个竞品 10 个分析项无遗漏，无证据项标记 [TBD-RESEARCH]
- [ ] 横向对比矩阵覆盖全部竞品与关键维度
- [ ] "可借鉴项"与"风险项"均可执行（能转化为设计输入，而非泛泛评价）
```

### 质量门禁

- 竞品范围确认
- 每个结论有事实/证据或明确标记为推测
- 可借鉴项与风险项具体可执行

---

## Stage 5：业务建模

### 目标

把市场和竞品洞察收敛为结构化的业务模型。**本阶段同时定义非功能需求（NFR），这是企业级交付物与玩具项目的分水岭。**

### 提示词

```text
【角色】你是一位有 5 年经验的业务架构师。

【输入】（权威优先级从高到低）
1. docs/01_market_research/market_research_report.md
2. docs/02_competitor_analysis/competitor_analysis_report.md

【产出】docs/03_problem_modeling/business_model.md

【必须包含】
1. 业务目标
2. 核心业务流程
3. 核心业务实体及关系
4. 角色与权限矩阵
5. 状态模型
6. 业务规则清单（BR-001...）
7. 非功能需求（NFR-001...）：
   - 性能目标（如核心接口 P95 响应时间、页面加载目标）
   - 容量目标（预期用户量、并发量、数据量级）
   - 可用性目标（如 99.9%）
   - 安全与合规要求（敏感数据识别、数据保留策略、适用法规）
   - 可访问性要求（如 WCAG 2.1 AA 的关键项）
8. MVP 范围（如当前项目已有明确范围）
9. Out of Scope（如已有明确排除项）

【业务流程要求】
- 使用 Mermaid
- 每个节点标注输入、处理、输出和异常（无异常分支的节点需显式注明"无异常"）
- 标明人工节点和系统节点

【硬性规则】
- 这是业务收口文档，不得自行新增业务规则
- 无法确定的内容标记 [TBD-BIZ]
- 不用"等""相关""类似"等模糊描述代替具体规则
- NFR 必须量化，禁止"高性能""高可用"这类无量词的表述；
  无法量化的标记 [TBD-BIZ] 并说明需要谁提供

【完成前自检】
- [ ] 每条 BR 有唯一编号且表述无歧义
- [ ] 每条 NFR 有量化指标或可度量的验收方式
- [ ] 权限矩阵覆盖全部角色 × 全部核心操作
- [ ] 敏感数据已全部识别并标注分级建议
```

### 质量门禁

- 业务流程、实体关系、权限矩阵经业务方确认
- BR 清单编号连续、无歧义
- **NFR 全部量化或可度量，敏感数据识别完整**

---

# Phase 3：Product Design

## Stage 6：核心交互设计

### 目标

将业务模型转换成用户可执行的交互模型，为 Prototype 提供直接输入。

### 提示词

```text
【角色】你是一位有 5 年经验的交互设计师。

【输入】docs/03_problem_modeling/business_model.md（唯一业务权威来源）

【产出】docs/04_interaction_design/interaction_design_summary.md

【必须包含】
1. 信息架构
   - 页面清单（PG-001...）
   - 页面用途
   - 信息层级
   - 页面之间的导航关系

2. 核心任务流
   - 用户操作 → 系统响应 → 页面变化
   - 主流程与异常流程

3. 交互规则
   - 表单校验
   - 操作反馈
   - 确认/撤销
   - 防重复提交
   - 权限表现

4. 页面状态
   - Default / Loading / Empty / No Result / Error
   - No Permission / Editing / Submitting / Success / Failure
   - Partial Success（仅业务需要时）

5. 响应式行为

6. 可访问性基本要求
   - 键盘可达性、焦点顺序、关键操作的无鼠标路径
   - 色彩对比度与信息不依赖单一颜色传达

【硬性规则】
- Business Model 是业务规则的唯一权威来源
- 不得创造输入文档不存在的业务能力
- 如果发现业务规则不足以支持交互决策，标记 [TBD-BIZ]
- 每个核心交互必须能追溯到业务实体、状态或规则（BR-xxx / NFR-xxx）

【完成前自检】
- [ ] 每个页面 9 类状态逐一判定"适用/不适用"，不适用需说明理由
- [ ] 每条交互规则可追溯至 BR 编号
- [ ] 异常流程与主流程一一对应，无"只设计了 happy path"
```

### 质量门禁

- 页面清单完整，核心任务可走通
- 状态矩阵完整（每页 × 9 类状态有明确判定）
- 业务规则与交互规则一致，追溯关系明确

---

## Stage 7：Interactive Prototype（Figma Make）

### 定位

**Stage 7 是产品行为验证阶段。**

Prototype 的职责是：

```text
业务模型 + 核心交互设计
        ↓
可视化、可点击、可验证的 Prototype
        ↓
人工验证"产品是否这样工作"
```

Prototype 不是生产代码，也不是最终视觉设计稿。

**保真度说明**：本阶段要求的是**行为保真**（流程可走通、状态齐全、反馈正确），而不是**视觉保真**。在 Figma Make 等 AI 原型工具中，视觉保持中性、接近组件库默认风格即可，不要投入视觉打磨；色彩、字体、品牌等最终视觉决策属于 Stage 13。

### 7.1 Prototype 输入

建议将以下内容整理为 Make 的输入：

```text
business_model.md
interaction_design_summary.md
```

并由 AI 在进入 Figma Make 前生成一个轻量的：

```text
ui_brief.md
page_inventory.md
component_inventory.md
state_matrix.md
```

> UI Brief 不需要成为新的"产品设计阶段"，它只是把业务/交互设计转换成 Figma Make 易消费的结构化输入。

### 7.2 Figma Make 启动 Prompt

```text
【角色】你是本产品的交互原型构建师。

【输入】（权威优先级从高到低）
1. docs/03_problem_modeling/business_model.md（业务规则）
2. docs/04_interaction_design/interaction_design_summary.md（流程与交互）

【任务】把已经确定的业务和交互转换为可点击、可演示的 Prototype。
你的任务不是重新设计业务，也不是重新设计核心交互。

【规则优先级】
Business Model（业务规则）> Interaction Design（流程与交互）> Prototype UI 表现

【禁止新增】
- 业务功能 / 用户角色 / 业务规则
- 页面核心能力 / 数据字段 / 状态

允许做合理的布局决策，但视觉保持中性（接近组件库默认风格），不做品牌与最终视觉决策（属于 Stage 13）；任何情况下不得改变业务行为。

【必须】
1. 覆盖核心页面
2. 跑通核心用户主流程
3. 支持页面跳转
4. 展示核心成功/失败反馈
5. 展示关键 Loading / Empty / Error / Permission 状态
6. 对危险操作提供确认流程
7. Desktop 1440px 优先，并提供 Mobile 375px 适配

【不要】
- 不要生成生产代码
- 先确保主流程完整，再补状态

【不确定处理】业务规则或交互不足以支撑某处原型决策时，标记 [TBD-BIZ]/[TBD-UX] 并停在该处，禁止自行新增业务能力或臆造流程。

【完成前自检】
- [ ] 核心主流程从入口到完成可完整点击走通
- [ ] 每个页面的关键状态与 state_matrix.md 一致
- [ ] 无输入文档之外的业务能力
```

### 7.3 迭代方式

**Round 1：主流程**

```text
只实现核心用户主流程。
不要扩展边缘能力。
确保从入口到任务完成可以完整点击走通。
```

**Round 2：状态补全**

```text
基于当前 Prototype，不修改已确认的主流程。
逐页补充适用的 Loading、Empty、No Result、Error、No Permission、Submitting、Success、Failure 状态。
不要创造新的业务状态。
```

**Round 3：UX Audit**

```text
请检查当前 Prototype：
1. 核心流程是否可完整走通
2. 是否存在无反馈操作
3. 是否存在无法继续的状态
4. 是否缺少关键错误/空状态
5. 是否存在危险操作无确认
6. Desktop / Mobile 是否存在核心任务断裂

先列出问题清单（按严重程度排序），经确认后再修复 Prototype。
不得新增业务能力。
```

### 7.4 Prototype Review Gate（Gate 1）

使用 0.5 节统一 Gate 模板，检查项如下：

```markdown
### 核心检查
- [ ] 页面流转与 Interaction Design 一致
- [ ] 核心任务可以完整走通（100% 主流程无断点）
- [ ] 核心状态已覆盖（对照 state_matrix.md）
- [ ] 权限差异有体现
- [ ] 危险操作有明确确认
- [ ] 空数据/错误/加载状态合理
- [ ] Desktop 核心流程完整
- [ ] Mobile 核心流程完整

### Gate
- [ ] APPROVED：Prototype Freeze
- [ ] REJECTED：回溯 Business Model / Interaction Design / Prototype
```

### 质量门禁

- Gate 1 评审记录归档至 docs/05_prototype/prototype_review.md
- 未解决的阻塞问题为 0
- Prototype Freeze 完成后，方可进入工程设计

---

# Phase 4：Engineering Design

## Stage 8：架构设计（前端规范 + 前后端边界 + 后端架构）

### 目标

把已经通过 Prototype Review 的产品设计转换为工程设计输入。

### 前置条件

- Gate 1 = APPROVED

### 8.1 前端设计规范

输出：`docs/06_architecture_design/frontend_design_spec-v1.0.md`

至少包含：

- 页面清单（编号与 Interaction Design 一致）
- 页面结构层次
- 页面跳转关系
- 前端负责的 UI / 页面状态 / 本地交互
- 核心交互实现要求
- 响应式行为
- 与 Prototype 的对应关系

### 8.2 前后端边界

输出：`docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md`

至少包含：

| 功能/操作 | 用户动作 | 前端职责 | 后端职责 | 输入 | 输出 | 状态变化 |
|---|---|---|---|---|---|---|

另外明确：

- 哪些数据由后端提供
- 哪些逻辑只能由后端决定
- 哪些逻辑属于前端 UI
- 哪些操作必须调用 API
- 哪些成功条件以后端结果为准
- 网络错误 / 权限错误 / 业务错误的边界

### 8.3 后端架构设计

输出：`docs/07_backend_design/architecture_spec.md`

至少包含：

- 服务边界
- 模块划分
- 领域层 / 应用层 / 基础设施层职责
- 外部依赖
- **安全架构**：认证方式、授权模型（RBAC/ABAC）、越权防护、传输与存储加密
- **可观测性设计**：日志（结构化字段约定）、关键指标（Metrics）、链路追踪（如适用）、告警点
- 核心业务流程在后端的承载位置
- NFR 的架构承载方案（每条 NFR-xxx 对应到架构决策）

### 冲突优先级

**不要让 Figma 覆盖业务规则。**

```text
Business Model（业务规则）
        ↓
Interaction Design（业务交互）
        ↓
Prototype（行为验证）
        ↓
Architecture（工程实现）
        ↓
Figma High-Fidelity（视觉规范）
```

如果冲突：

- 业务规则冲突 → Business Model 优先
- 交互流程冲突 → Interaction Design 优先
- 页面视觉/布局冲突 → Figma 优先
- 不确定项 → 使用 [CONFLICT] / [TBD-*] 标记，不自行裁决

### 质量门禁

- 页面与 Prototype 一一对应
- 前后端职责无明显重叠
- 核心流程有工程承载方案
- **每条 NFR 有明确的架构承载方案**
- **认证授权模型、可观测性方案已定义**
- 未出现新的业务能力

---

## Stage 9：技术开发框架

### 目标

冻结项目采用的前后端技术栈和工程基础，并完成依赖供应链安全评估。

### 提示词

```text
【角色】你是一位有 5 年经验的技术架构师。

【输入】（权威优先级从高到低）
1. docs/06_architecture_design/frontend_design_spec-v1.0.md
2. docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
3. docs/07_backend_design/architecture_spec.md

【任务】确定并冻结技术栈。

【必须确定】
1. 前端框架
2. UI 组件方案
3. 状态管理
4. 后端框架
5. ORM / 数据访问方式
6. API 风格
7. 测试框架（单元 / 接口 / E2E 各一）
8. 构建与部署方式

【供应链安全要求】
- 每个核心依赖注明：版本（锁定策略）、License、维护活跃度、已知高危 CVE 情况
- 输出依赖清单（SBOM 雏形），放入 architecture_spec.md 附录
- License 与项目商业用途冲突的依赖必须标记 [CONFLICT]

【约束】
- 只确定实现所必需的技术
- 每项技术说明选择理由（含被淘汰的候选及原因）
- 不允许为了"看起来完整"而添加无实际需求的组件

【完成前自检】
- [ ] 每个技术选型有理由、有弃选方案对比
- [ ] 全部核心依赖通过漏洞扫描（0 个未处置的高危/严重 CVE）
- [ ] License 清单无商业冲突
```

### 质量门禁

- 技术栈冻结
- 核心依赖明确且通过漏洞扫描（高危/严重 CVE = 0 未处置）
- 无不必要的技术组件

---

## Stage 10：数据模型

### 目标

将业务实体转换成后端持久化数据模型，并完成数据分级。

### 提示词

```text
【角色】你是一位有 5 年经验的数据架构师。

【输入】（权威优先级从高到低）
1. docs/03_problem_modeling/business_model.md
2. docs/07_backend_design/architecture_spec.md

【产出】docs/07_backend_design/data_model_spec.md

【必须包含】
1. ER 图
2. 表清单
3. 字段定义
4. 主键/外键
5. 唯一约束
6. 索引
7. 状态字段
8. 数据生命周期
9. 数据分级：每个含敏感数据的表/字段标注分级
   （公开 / 内部 / 敏感 / 高敏），高敏字段注明加密与脱敏策略
10. 数据迁移要求（如适用）

【约束】
- 数据模型必须能承载 Business Model 中已经定义的实体和规则
- 不新增未经确认的业务实体
- 无法确定的内容标记 [TBD-BE]
- 不把"页面字段"直接等同于"数据库字段"
- 审计字段（created_at / updated_at / created_by 等）为必填设计项，
  不适用时需说明理由

【完成前自检】
- [ ] Business Model 中每个实体都有对应表或有明确的不落库说明
- [ ] 每条涉及数据约束的 BR 有对应的数据库约束或应用层校验
- [ ] 敏感字段 100% 完成分级标注
```

### 质量门禁

- 核心业务实体可落库
- 数据约束与业务规则一致
- 敏感字段分级覆盖率 100%
- 无冗余业务实体

---

## Stage 11：API Contract（接口契约设计）

### 目标

建立前后端共同遵循的接口契约。

### 提示词

```text
【角色】你是一位有 5 年经验的后端架构师。

【输入】（权威优先级从高到低）
1. docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
2. docs/07_backend_design/architecture_spec.md
3. docs/07_backend_design/data_model_spec.md

【产出】docs/07_backend_design/api_interface_spec.md

【必须包含】
1. API 清单（API-001...）
2. Method + Path
3. Request Schema
4. Response Schema
5. 错误码（唯一、分段、含语义）
6. 鉴权要求（每个端点明确：匿名/登录/角色）
7. 幂等要求（适用时）
8. 分页/排序/筛选规范（适用时）
9. 限流与防滥用策略（适用时）
10. API 版本策略
11. 核心调用时序图

【约束】
- API 只能来自前后端边界文档中已经定义的功能能力
- 不得新增业务 API
- 前端与后端的字段契约必须明确
- 返回结构不得泄露敏感字段（对照数据分级逐一核对）
- 如果是 FastAPI 项目，同时给出 Pydantic Schema 设计建议，
  但不要生成业务实现代码

【完成前自检】
- [ ] 边界文档中每个"必须调用 API"的操作都有对应 API-xxx
- [ ] 每个端点的鉴权要求与权限矩阵一致
- [ ] 错误码全局唯一
- [ ] 所有 Response 不含敏感/高敏未脱敏字段
```

### 质量门禁

- 前后端边界中的能力均有对应 API 或明确不需要 API
- 错误码唯一
- Request/Response 字段明确
- **鉴权要求与权限矩阵 100% 一致**
- API Contract 可直接作为前后端并行开发契约

### Gate 2：Architecture & Contract Review

Stage 8～11 完成后，使用 0.5 节统一模板执行 Gate 2 评审，记录归档至 `docs/07_backend_design/gate2_review.md`。**Gate 2 通过后，架构、数据模型、API 契约冻结；之后的修改必须走附录 F 变更控制。**

---

# Phase 5：产品交付资产

## Stage 12：PRD / 产品需求文档

### 定位

PRD 在本流程中不是最上游的"需求唯一来源"，而是将已经形成的业务、交互、Prototype 和工程信息整理成面向产品、研发、测试和业务方的综合交付文档。

### 提示词

```text
【角色】你是一位有 5 年经验的产品经理。

【输入】（均为已冻结资产，权威优先级按附录 B）
- docs/03_problem_modeling/business_model.md
- docs/04_interaction_design/interaction_design_summary.md
- docs/05_prototype/prototype_review.md
- docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
- docs/07_backend_design/api_interface_spec.md

【产出】docs/08_prd/prd_document.md

【必须包含】
1. 需求背景
2. 用户与业务目标
3. 功能清单
4. 核心业务流程
5. 关键交互
6. 状态与异常
7. 权限
8. 数据与接口关联
9. 验收标准（AC-xxx，每条必须可测试、可判定通过/失败，
   并标注关联的 BR-xxx / API-xxx）
10. 明确 Out of Scope

【约束】
- 这是综合交付文档，不得重新定义业务
- 如果发现上游文档冲突，标记 [CONFLICT]，不要自行裁决
- 验收标准禁止"体验良好""响应迅速"式表述，必须可测量

【完成前自检】
- [ ] 每条 AC 可执行二元判定（Pass/Fail）
- [ ] 每条 BR 至少被一条 AC 覆盖
- [ ] 与所有上游文档无冲突，或冲突已标记 [CONFLICT]
```

### 质量门禁

- PRD 与 Business Model、Interaction Design 一致
- API 编号可追溯
- **每条 BR 至少被一条可测试的 AC 覆盖**
- 不新增业务功能

---

## Stage 13：Figma High-Fidelity 产品 UI 设计

### 定位

**Stage 13 负责"这个产品最终长什么样"。**

与 Stage 7 的区别：

```text
Stage 7 Prototype
= 验证"产品怎么工作"

Stage 13 High-Fidelity
= 确定"产品最终长什么样"
```

### 13.1 高保真设计输入

- Stage 7 Prototype
- Stage 12 PRD
- Stage 8 Frontend Design Spec

### 13.2 Design System 要求

至少形成：

- Color Tokens
- Typography Tokens
- Spacing Tokens
- Radius Tokens
- Component Variants
- Component States

### 13.3 Figma 设计原则

- 优先组件复用
- 优先 Auto Layout
- 适合的组件使用 Variants
- Desktop + Mobile 关键流程均可验证
- 核心状态齐全
- 避免无意义的视觉装饰

### 13.4 组件规格

可以由 AI 辅助生成：`docs/09_figma_highfi/component_spec.json`

要求：

- 与 Frontend Design Spec 保持一致
- 只定义实际使用的组件
- 定义关键 variants 和 states
- 不为了"覆盖所有可能情况"而扩展组件

### 13.5 Design Tokens

输出：`docs/09_figma_highfi/design_tokens.json`

要求：

- Figma 与前端实现共享同一套设计变量
- 不要求把每一个视觉参数都人工写成文档
- 以 Design Token / Component System 作为 AI Coding 的主要视觉约束

### 13.6 高保真走查

```markdown
## Figma High-Fidelity Review

- [ ] 页面与 Prototype 一致
- [ ] 核心流程完整
- [ ] 关键组件复用一致
- [ ] 核心状态完整
- [ ] Desktop / Mobile 均可验证
- [ ] Design Tokens 已形成
- [ ] 组件规格与前端设计规范一致
- [ ] 不存在明显视觉/交互冲突
```

### Gate

- [ ] APPROVED：进入 AI Implementation
- [ ] REJECTED：修改 Figma / Prototype / Interaction Design（走附录 F 变更控制）

---

# Phase 6：AI Implementation Preparation

## Stage 14：CLAUDE.md / AGENTS.md 项目工程上下文构建

### 这是整个 AI Coding 流程的关键阶段

Stage 14 的目标不是再写一份普通项目说明，而是：

> **把前面的设计资产"编译"为 AI Coding Agent 可以持续遵循的工程上下文。**

### 输入

```text
Business Model
Interaction Design
Prototype Review
Frontend Design Spec
Frontend/Backend Boundary
Backend Architecture
Data Model
API Contract
PRD
High-Fidelity Figma / Design Tokens
```

### 输出

```text
项目级 CLAUDE.md / AGENTS.md          # 全局规则
src/frontend/CLAUDE.md（可选）         # 前端模块上下文
src/backend/CLAUDE.md（可选）          # 后端模块上下文
```

### 上下文分层原则

```text
项目级（全局、稳定、长期有效）
  └─ 目标、技术栈、架构边界、红线、冲突处理规则

模块级（frontend / backend 各自上下文）
  └─ 目录约定、模块内规范、常用命令、该模块特有约束

任务级（每次会话的 Task Brief，附录 H）
  └─ 本次实现范围、相关契约编号、验收标准、禁止事项
```

**上下文预算：项目级 CLAUDE.md / AGENTS.md 控制在 300 行以内。** 超出时优先下沉到模块级；具体业务细节一律用文档路径引用，不复制全文。

### 提示词

```text
【角色】你是一位负责 AI 工程化的资深 Tech Lead。

【输入】当前项目已经冻结的设计资产：
- docs/03_problem_modeling/business_model.md
- docs/04_interaction_design/interaction_design_summary.md
- docs/06_architecture_design/frontend_design_spec-v1.0.md
- docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
- docs/07_backend_design/architecture_spec.md
- docs/07_backend_design/data_model_spec.md
- docs/07_backend_design/api_interface_spec.md
- docs/08_prd/prd_document.md
- docs/09_figma_highfi/design_tokens.json

【任务】把稳定且需要长期遵守的规则提炼为 AI Coding Agent 的项目上下文。

【产出】项目级 CLAUDE.md / AGENTS.md

【必须包含】
1. 项目目标
2. 目录结构
3. 技术栈
4. 架构边界
5. 前后端职责
6. API 约束（含鉴权与错误码约定）
7. 数据层约束（含敏感数据处理红线）
8. UI / Design Token 约束
9. 测试要求
10. 运行/构建/部署方式
11. 禁止行为（含 AI 使用红线：不改冻结资产、不引未审计依赖、
    不提交密钥、不跳过验证）
12. 规范冲突处理规则（引用附录 B）

【约束】
- 不把所有文档全文复制进 CLAUDE.md / AGENTS.md
- 只保留稳定、长期有效、高频需要遵守的规则
- 具体业务细节使用文档路径引用
- 不新增设计文档中没有定义的业务规则
- 全文控制在 300 行以内

【完成前自检】
- [ ] 一个新加入的 Agent 仅凭此文件 + 引用路径即可正确工作
- [ ] 无一次性细节、无大段复制的文档原文
- [ ] 全部禁止行为表述为可判定的祈使句
```

### 质量门禁

- 项目级 AI Context 可独立理解项目规则，且 ≤ 300 行
- 没有把大量一次性细节堆进 CLAUDE.md / AGENTS.md
- AI 使用红线与冲突处理规则已写入
- Frontend / Backend Agent 可以根据上下文工作

---

# Phase 7：AI Implementation

## Stage 15：后端 MVP 源码构建

### 输入

- CLAUDE.md / AGENTS.md
- architecture_spec.md
- data_model_spec.md
- api_interface_spec.md
- frontend_backend_boundary_spec.md

### 实现纪律（先于提示词的约定）

1. **一个模块一个新会话**，以 Task Brief（附录 H）开场。
2. **测试先行或并行**：每个 API 的测试用例（TC-xxx）在实现时同步生成，汇入 `docs/11_test/test_plan.md`，编号关联 API-xxx / BR-xxx。
3. **小步提交**：每个逻辑完整的单元一个 commit，遵循 Conventional Commits。
4. **每完成一个模块即运行自动化验证**，不攒到最后。

### 提示词

```text
【角色】你是一位资深后端工程师，严格按契约实现，不做设计决策。

【输入】（权威优先级从高到低）
1. CLAUDE.md / AGENTS.md（项目红线与约定）
2. docs/07_backend_design/api_interface_spec.md（本次实现的 API-xxx 范围）
3. docs/07_backend_design/data_model_spec.md
4. docs/07_backend_design/architecture_spec.md
5. docs/03_problem_modeling/business_model.md（仅 BR-xxx 相关章节）

【任务】实现后端 MVP（本次会话范围：【{模块/API 编号清单}】，见 Task Brief）。

【要求】
1. 严格遵守 CLAUDE.md / AGENTS.md
2. 严格按照 data_model_spec 实现数据层
3. 严格按照 api_interface_spec 实现 API
4. 业务规则只能来自 business_model.md
5. 完成错误处理、鉴权和日志基础能力
6. 每个 API 同步生成测试用例（TC-xxx），关联 API/BR 编号
7. 完成迁移脚本
8. 实现完成后执行自动化验证并输出结果

【禁止】
- 不新增 API / 数据库实体 / 业务规则
- 不引入未在 Stage 9 清单中的依赖
- 不硬编码任何密钥、连接串、环境特定值
- 不静默吞掉异常；不允许无跟踪的 TODO（必须关联 issue 或标记 [TBD-BE]）

【冲突处理】
如发现规范冲突：停止修改业务，报告 [CONFLICT] 并说明冲突的两份资产与具体条款。

【完成前自检】
- [ ] 本次范围内 API 全部实现且通过接口测试
- [ ] 迁移脚本可正向执行、可回滚
- [ ] 核心业务规则有对应测试且全部通过
- [ ] 无规范外 API、无新依赖、无硬编码敏感信息
- [ ] 输出实现报告：实现范围 / 测试证据 / 偏离说明 / 遗留问题
```

### 质量门禁

- API Contract 验证通过率 100%（本次范围）
- 数据迁移可执行、可回滚
- 核心业务规则测试全部通过
- 无规范外 API、无未审计依赖

---

## Stage 16：前端 MVP 源码构建

### 输入

- CLAUDE.md / AGENTS.md
- frontend_design_spec-v1.0.md
- frontend_backend_boundary_spec-v1.0.md
- api_interface_spec.md
- design_tokens.json
- component_spec.json
- Figma High-Fidelity Design

### 实现纪律

与 Stage 15 相同：一个页面组一个新会话、Task Brief 开场、小步提交、组件/页面级验证随做随跑。

### 提示词

```text
【角色】你是一位资深前端工程师，严格按规范实现，不做产品决策。

【输入】（权威优先级从高到低）
1. CLAUDE.md / AGENTS.md
2. docs/06_architecture_design/frontend_design_spec-v1.0.md
3. docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
4. docs/07_backend_design/api_interface_spec.md
5. docs/09_figma_highfi/design_tokens.json + component_spec.json
6. Figma High-Fidelity Design（视觉权威来源）

【任务】实现前端 MVP（本次会话范围：【{页面编号清单}】，见 Task Brief）。

【要求】
1. 严格遵守 CLAUDE.md / AGENTS.md
2. 页面与 frontend_design_spec 一一对应
3. 关键页面布局与 Figma High-Fidelity Design 一致
4. 使用 design_tokens.json 中定义的 Design Tokens，
   禁止在组件中硬编码颜色/字号/间距字面值
5. 使用 component_spec.json 中定义的共享组件
6. Loading / Empty / Error / No Permission / Submitting 等关键状态必须实现
7. 按 api_interface_spec 对接 API，错误处理区分网络/权限/业务错误
8. 完成前端组件和页面级验证

【禁止】
- 不新增规范之外的页面、功能或业务规则
- 不绕过组件库自行实现已有共享组件
- 不在前端做权限的最终判定（前端只做表现，判定以后端为准）

【完成前自检】
- [ ] 本次范围页面的关键状态全部实现且可演示
- [ ] 全部视觉值来自 Design Tokens
- [ ] API 对接字段与 Contract 完全一致
- [ ] 响应式关键流程通过
- [ ] 输出实现报告：实现范围 / 验证证据 / 偏离说明 / 遗留问题
```

### 质量门禁

- 页面与 Figma 高保真设计一致
- 核心状态完整
- API 对接符合 Contract
- 响应式关键流程通过
- 视觉值 100% 来自 Design Tokens（无硬编码样式字面值）

---

## Stage 16.5：AI 代码评审与安全门禁（Gate 3）

### 定位

**AI 生成代码不因其"能跑"而获得信任。** 本阶段是企业级 AI Coding 与"Vibe 完直接上线"的本质区别。

Gate 3 由两层组成：

```text
第一层：自动化门禁（CI 执行，客观、可重复）
  lint → 类型检查 → 单元/接口测试 → 覆盖率阈值
  → 安全扫描（SAST + 依赖 CVE + secret scanning）

第二层：人工评审（主观判断不可替代）
  按附录 G 的 AI 生成代码评审 Checklist 执行
  重点：AI 是否忠实于冻结资产，而非"代码看起来好不好"
```

### 自动化门禁提示词（生成检查脚本/配置时）

```text
【角色】你是 CI 质量工程师。

【任务】为当前项目配置 Gate 3 自动化检查，输出可执行的检查配置与脚本。

【必须覆盖】
1. Lint 与格式检查（0 error 方可通过）
2. 静态类型检查（如 mypy / tsc，0 error）
3. 单元测试 + 接口测试全部通过
4. 覆盖率：核心业务规则路径 100% 有用例覆盖；整体行覆盖率 ≥ 【{团队阈值，例如 80%}】（阈值一经确定即写入 CI 配置强制执行）
5. 安全扫描：
   - SAST（如 bandit / semgrep）：高危与严重 = 0
   - 依赖 CVE 扫描：高危与严重未处置 = 0
   - secret scanning：告警 = 0
6. 契约一致性：实现的 API 与 api_interface_spec.md 比对，
   无多余端点、无缺失端点

【约束】以项目实际技术栈为准，工具仅为示例（mypy/tsc/bandit/semgrep 等按实际语言替换），不引入无关工具。

【不确定处理】阈值或工具选择未定时标记 [TBD-INFRA] 并说明需谁确认，禁止擅自设定放松阈值。

【完成前自检】
- [ ] 每一类检查均有对应可执行配置/脚本，且在本仓库实测可运行
- [ ] 任一检查失败均能阻断流水线（无"仅告警不阻断"的软门禁）
- [ ] 覆盖率、安全扫描阈值均为可度量数值，已写入配置
```

### 人工评审提示词（评审者使用 AI 辅助时）

```text
【角色】你是严格的代码评审者，代表技术负责人执行 Gate 3。

【输入】
1. 本次 PR 的代码变更
2. docs/07_backend_design/api_interface_spec.md
3. docs/03_problem_modeling/business_model.md（BR 相关章节）
4. 附录 G 评审 Checklist

【任务】按 Checklist 逐项审查，输出评审报告至 docs/11_test/code_review_report.md。

【评审视角优先级】
1. 忠实性：实现是否与冻结资产一致（最重要）
2. 安全性：注入、越权、敏感信息、依赖风险
3. 正确性：边界条件、并发、事务、错误处理
4. 可维护性：命名、结构、重复代码

【禁止】
- 不以"AI 生成的，大差不差"为由跳过任何检查项
- 不在评审中顺手修改业务规则；发现资产问题标记 [CONFLICT]

【输出】
- 每项 Checklist 的判定（Pass / Fail / N/A + 证据）
- 问题清单（按阻塞/严重/建议分级）
- 结论：APPROVED / CHANGES REQUESTED
```

### 质量门禁（全部可度量）

- 自动化检查全绿：lint/type/test = 0 error
- 覆盖率达标（核心 BR 路径 100% 有用例，整体 ≥ 团队阈值）
- 安全扫描：高危/严重 = 0，secret 告警 = 0
- 契约比对：多余/缺失端点 = 0
- 人工评审报告归档，阻塞/严重问题清零
- **Gate 3 记录归档至 docs/11_test/code_review_report.md**

---

# Phase 8：验证与交付

## Stage 17：前后端联调 / E2E 验证

### 目标

验证真实系统是否仍然符合资产链：

```text
Business Model
↓
Interaction Design
↓
Prototype
↓
API Contract
↓
Production Code
```

### 提示词

```text
【角色】你是一位资深的测试架构师。

【输入】（权威优先级按附录 B）
- docs/03_problem_modeling/business_model.md
- docs/04_interaction_design/interaction_design_summary.md
- docs/05_prototype/prototype_review.md
- docs/06_architecture_design/frontend_backend_boundary_spec-v1.0.md
- docs/07_backend_design/api_interface_spec.md
- docs/08_prd/prd_document.md
- docs/11_test/test_plan.md

【任务】执行端到端联调验证，输出 docs/11_test/e2e_report.md。

【验证范围】
1. 核心业务流程（对应 PRD 验收标准 AC-xxx）
2. 权限（对照权限矩阵逐角色验证）
3. 正常/异常状态
4. API Contract 一致性
5. 前端页面行为
6. 数据一致性
7. 并发/重复提交等边界场景
8. Prototype 与真实产品的关键流程一致性
9. 安全回归抽查：越权访问、注入、敏感字段泄露
10. 性能冒烟：核心接口 P95 对照 NFR-xxx 目标

【追溯要求】
- 每个 E2E 场景编号（E2E-xxx）并关联 AC-xxx / BR-xxx / API-xxx
- 输出追溯矩阵：BR → AC → TC/E2E → 结果，
  任一 BR 无覆盖即为阻塞问题

【问题处理】
发现问题时，标记问题归属：
- Business / Interaction / Frontend / Backend / API Contract / Infrastructure

不要直接修改上游业务规则；归属上游的问题走附录 F 变更控制。

【完成前自检】
- [ ] 每条 AC-xxx 均有对应 E2E 场景且已执行（Pass/Fail 有明确结论）
- [ ] 追溯矩阵完整，任一 BR 无覆盖即标记为阻塞问题
- [ ] 安全回归抽查与性能冒烟均已执行，未达标项已记录并标注归属
- [ ] 所有缺陷标注归属层级，无"就地擅改上游"的动作
```

### 质量门禁

- 核心业务流程通过率 100%
- 阻塞/严重缺陷 = 0
- API Contract 一致
- 追溯矩阵完整（BR 覆盖率 100%）
- 安全回归抽查无发现
- 性能冒烟达到 NFR 目标（或偏差已记录并签核）

### Gate 4：Release Readiness Review

使用 0.5 节统一模板，核对：Gate 4 前所有资产、测试报告（`docs/11_test/e2e_report.md`）、遗留问题清单（全部有 owner 与处置计划）、回滚方案。评审记录归档至 `docs/11_test/gate4_release_readiness.md`。**Gate 4 = APPROVED 后方可部署。**

---

## Stage 18：CI/CD 与部署

### 目标

建立可复现、可回滚、可观测的交付方案。

### 提示词

```text
【角色】你是一位资深的 DevOps / SRE 工程师。

【输入】当前已经完成的前后端项目实际结构、Stage 9 技术栈、
docs/07_backend_design/architecture_spec.md（可观测性设计）。

【产出】
- docs/12_deployment/cicd_pipeline_spec.md
- docs/12_deployment/docker_compose_spec.md
- docs/12_deployment/release_checklist.md

【CI/CD Pipeline 必须包含】
1. 触发策略（分支/标签）
2. 质量阶段：lint → typecheck → 单元测试 → 接口测试
   → 安全扫描（SAST + 依赖 + secret）→ 构建
   （任一阶段失败即阻断，对应 Gate 3 的自动化部分）
3. 环境分层：dev → staging → prod，prod 部署需人工审批
4. 制品管理与版本标记

【部署必须包含】
1. Dockerfile
2. docker-compose.yml
3. 环境变量清单（全部经 .env.example 管理，敏感值走密钥管理服务，
   禁止硬编码、禁止入库）
4. 健康检查（liveness / readiness）
5. 日志策略（结构化、级别、轮转，对接 architecture_spec 的可观测性设计）
6. 监控与告警：核心指标（错误率、延迟、饱和度）+ 告警阈值与接收人
7. 数据持久化与备份策略
8. 基础资源限制
9. 重启策略
10. 回滚方案（含数据库迁移的回滚路径）
11. 部署前检查清单（release_checklist.md）

【约束】
- 以实际代码和配置为准
- 不假设不存在的服务
- 敏感信息不得硬编码

【完成前自检】
- [ ] pipeline 从零环境可完整跑通
- [ ] 回滚方案经过演练验证（至少在 staging 演练一次）
- [ ] 监控告警有明确的接收人与响应约定
- [ ] 全部敏感值不存在于仓库与镜像中
```

### 质量门禁

- Pipeline 全阶段可重复通过
- 回滚方案经 staging 演练验证
- 监控告警生效（告警可触达接收人）
- 敏感信息零硬编码（镜像与仓库扫描通过）

---

# 附录 A：阶段之间的职责边界

| 阶段 | 核心问题 | 主要产出 | Gate |
|---|---|---|---|
| 市场研究 | 市场和用户是什么情况？ | Market Research | — |
| 竞品拆解 | 别人怎么解决？ | Competitor Analysis | — |
| 业务建模 | 系统中的业务是什么？约束是什么？ | Business Model + NFR | — |
| 交互设计 | 用户怎么使用？ | Interaction Design | — |
| Prototype | 产品是否真的这样工作？ | Interactive Prototype + Review | **Gate 1** |
| 前端规范/边界 | 前端怎么承接？前后端怎么分工？ | Frontend Spec + Boundary | — |
| 后端架构 | 后端系统怎么组织？如何安全、可观测？ | Architecture Spec | — |
| 技术框架 | 采用什么技术？供应链是否安全？ | Tech Stack + SBOM | — |
| 数据模型 | 数据怎么存？敏感数据怎么管？ | Data Model | — |
| API Contract | 前后端怎么通信？ | API Spec | **Gate 2** |
| PRD | 如何把设计汇总成团队可读交付文档？ | PRD（含可测试 AC） | — |
| High-Fidelity Figma | 最终视觉怎么统一？ | Figma + Tokens | — |
| CLAUDE.md / AGENTS.md | AI 应该长期遵守什么？ | AI Context | — |
| Frontend MVP | 前端怎么实现？ | Frontend Code | — |
| Backend MVP | 后端怎么实现？ | Backend Code | — |
| 代码评审门禁 | AI 的代码可信吗？ | Review Report | **Gate 3** |
| 联调/E2E | 最终行为是否正确？ | Test Report + 追溯矩阵 | **Gate 4** |
| CI/CD 与部署 | 如何稳定、可回滚、可观测地交付？ | Pipeline + Deployment | — |

---

# 附录 B：规范优先级

发生冲突时，不允许简单地"以后产生的文档覆盖以前的文档"。应该根据冲突类型判断权威来源：

```text
业务规则：
Business Model
    ↓
Interaction Design

交互行为：
Interaction Design
    ↓
Prototype Review

工程职责：
Frontend/Backend Boundary
    ↓
Architecture

数据与接口：
Data Model
    ↓
API Contract

视觉表现：
High-Fidelity Figma
    ↓
Design Tokens / Component Spec

AI 执行约束：
CLAUDE.md / AGENTS.md
    ↓
引用上述权威设计资产
```

如果无法明确归属：

```text
[CONFLICT]
[TBD-BIZ]
[TBD-UX]
[TBD-FE]
[TBD-BE]
[TBD-INFRA]
```

禁止 AI 默默选择一个方案。

---

# 附录 C：Explore / Freeze 双模式

不是所有阶段都应该禁止 AI 发散。

## Explore

适用于：

- 市场研究
- 竞品拆解
- 早期业务分析
- 早期交互设计

AI 可以：

- 提出候选方案
- 比较不同设计
- 暴露潜在问题
- 提出需要人工确认的事项

## Freeze

适用于：

- Prototype Review 通过后
- Architecture Review 通过后
- API Contract 冻结后
- High-Fidelity Figma 冻结后
- **全部代码实现与验证阶段**

AI 必须：

- 严格遵循输入规范
- 不新增业务能力
- 不偷偷修改上游设计
- 发现冲突即停止并标记

---

# 附录 D：通用防 AI 幻觉规则

推荐统一使用结构化标记，而不是"标红"：

```text
[TBD-BIZ]       待业务确认
[TBD-UX]        待交互确认
[TBD-FE]        待前端确认
[TBD-BE]        待后端确认
[TBD-DESIGN]    待设计确认
[TBD-INFRA]     待基础设施确认
[CONFLICT]      上游文档冲突
[ASSUMPTION]    当前仅为假设
```

同时遵循：

- 外部数据必须有来源
- 推测必须明确标记
- 不将未知内容包装成事实
- 不因为"文档完整性"而创造业务规则
- 不添加"未来可扩展"的无关设计
- **任何被标记的条目必须进入跟踪清单并指派确认人，不允许标记后无人认领**

---

# 附录 E：版本管理建议

```text
文档版本：v{major}.{minor}.{patch}

major：业务模型或核心领域规则发生变化
minor：新增/修改页面、核心交互、架构、API 等设计能力
patch：文案、示例、非行为性细节修正
```

每次变更记录：

| 版本 | 日期 | 修改内容 | 影响范围 | 责任人 |
|---|---|---|---|---|
| | | | | |

---

# 附录 F：变更控制流程（CCR）

冻结资产不等于永久资产，但修改必须显式、可追溯。

## F.1 变更分级

| 级别 | 定义 | 示例 | 处理 |
|---|---|---|---|
| L1 | 不影响行为的修正 | 文案、注释、样式微调、文档笔误 | 直接修改，记入 change_log.md |
| L2 | 局部设计变更 | 单个页面交互调整、非破坏性 API 字段新增 | 修改 + 相关 Gate 复审 + 通知下游 |
| L3 | 业务规则/契约变更 | BR 修改、权限模型调整、破坏性 API 变更 | 回到对应上游阶段，影响分析后重走相关 Gate |

## F.2 变更流程

```text
1. 发起：任何人在 docs/13_changes/change_log.md 登记变更请求
   （变更原因 / 变更资产及版本 / 变更级别初判 / 影响范围）
2. 评估：技术负责人 + 产品负责人确认级别与影响面
   - 影响哪些下游资产？（用附录 B 的权威链向下找）
   - 需要重走哪些 Gate？
   - AI 上下文（CLAUDE.md）是否需要同步更新？
3. 执行：修改资产并升级版本号（附录 E）
4. 回归：受影响的下游资产同步更新，相关 Gate 复审
5. 关闭：变更记录补全"实际影响范围"与"回归结果"
```

## F.3 AI 相关特别条款

- AI 在 Freeze 阶段发现资产问题时，**唯一合法动作是停止并标记 [CONFLICT]**，由人发起 CCR。
- 因 AI 实现偏差发现的"规范不合理"，同样走 CCR，不允许 AI 在实现中"顺手优化规范"。
- 每次 L2/L3 变更关闭后，必须检查 CLAUDE.md / AGENTS.md 是否同步，防止 AI 上下文与最新资产漂移。

---

# 附录 G：AI 生成代码评审 Checklist（Gate 3 人工评审用）

## G.1 忠实性（最重要）

- [ ] 实现的功能范围与 Task Brief 完全一致，无擅自扩展
- [ ] API 实现与 api_interface_spec 逐字段一致
- [ ] 业务规则实现与 BR-xxx 一致，无"AI 的理解性改写"
- [ ] 无幽灵产物：未在规范中的端点、实体、组件、配置项

## G.2 安全性

- [ ] 无硬编码密钥、Token、连接串
- [ ] 全部外部输入有校验（防注入、防 XSS）
- [ ] 鉴权与权限检查与权限矩阵一致，无前端单方面判定
- [ ] 敏感字段不泄露于 API 响应与日志
- [ ] 无新增的未审计依赖

## G.3 正确性

- [ ] 边界条件处理（空值、极限值、并发、重复提交）
- [ ] 事务完整性（多步写入有原子性保障或补偿）
- [ ] 异常不被静默吞掉，错误信息不含敏感内部细节
- [ ] 无无跟踪的 TODO / FIXME

## G.4 质量与一致性

- [ ] 测试覆盖本次变更且全部通过
- [ ] 命名、结构符合 CONVENTIONS
- [ ] 无大段重复代码、无死代码
- [ ] 前端视觉值全部来自 Design Tokens
- [ ] Commit 粒度合理、信息符合规范

## G.5 AI 特有的幻觉信号（逐项排查）

- [ ] 引用的依赖、API、配置项全部真实存在（非编造）
- [ ] 注释与文档链接真实有效
- [ ] 测试断言的是真实行为而非"为了过测试而写"
- [ ] 无被注释掉的大段"失败尝试"代码残留

---

# 附录 H：任务级 Task Brief 模板

每次 AI 实现会话的开场提示词（由人填写，作为该会话的置顶约束）：

```text
【Task Brief】
任务编号：TASK-xxx
日期：____
执行者：{人类负责人} + AI

## 本次范围（Only）
- 实现：{API-003, API-004 / PG-002}
- 关联契约：{引用文件路径#章节}
- 关联验收标准：{AC-xxx}

## 不在本次范围（明确排除）
- {相邻但本次不做的内容}

## 输入资产（按优先级）
1. CLAUDE.md
2. {本次直接相关的规范文件，不超过 3 份}

## 完成定义（Definition of Done）
- [ ] {可执行的验证命令，如 pytest tests/api/test_xxx.py 全绿}
- [ ] {其他判定标准}

## 禁止事项
- 不触碰范围外文件
- 不修改任何冻结资产
- 发现冲突输出 [CONFLICT] 并停止

## 会话结束输出
- 实现摘要（做了什么）
- 验证证据（测试/命令输出）
- 偏离与遗留（与 Brief 的任何偏差）
```

---

# 附录 I：快速参考——各阶段一句话总结

| Stage | 一句话 | 关键产出 | Gate |
|---|---|---|---|
| 1 | 搭建 AI 开发环境与安全基线 | AI/MCP 配置 + 安全基线 | — |
| 2 | 建立项目规范与 AI 红线 | README / CONVENTIONS | — |
| 3 | 看市场 | 市场研究 | — |
| 4 | 拆竞品 | 竞品分析 | — |
| 5 | 建立业务世界与非功能约束 | Business Model + NFR | — |
| 6 | 定义用户怎么操作 | Interaction Design | — |
| 7 | 让人直接体验产品流程 | Interactive Prototype | **Gate 1** |
| 8 | 定义工程边界与安全/观测方案 | Frontend Spec + Boundary + Architecture | — |
| 9 | 定技术栈并审计供应链 | Tech Stack + SBOM | — |
| 10 | 定数据与分级 | Data Model | — |
| 11 | 定接口 | API Contract | **Gate 2** |
| 12 | 汇总成团队交付文档 | PRD（可测试 AC） | — |
| 13 | 定最终视觉 | High-Fidelity Figma + Tokens | — |
| 14 | 把设计编译成 AI 上下文 | CLAUDE.md / AGENTS.md | — |
| 15 | 实现后端 | Backend MVP | — |
| 16 | 实现前端 | Frontend MVP | — |
| 16.5 | 验证 AI 代码是否可信 | Review Report | **Gate 3** |
| 17 | 验证完整系统与追溯链 | E2E Report + 追溯矩阵 | **Gate 4** |
| 18 | 稳定、可回滚、可观测地交付 | CI/CD + Deployment | — |

---

# 最终原则

```text
竞品研究
   ↓
业务建模（含 NFR）
   ↓
核心交互设计
   ↓
Interactive Prototype
   ↓
★★★★★ Gate 1：人工 Product Gate
   ↓
工程设计
   ├── 前端规范 / 前后端边界
   ├── 后端架构（安全 + 可观测性）
   ├── 数据模型（数据分级）
   └── API Contract
   ↓
★★★★★ Gate 2：Architecture & Contract Freeze
   ↓
产品交付资产
   ├── PRD（可测试验收标准）
   └── High-Fidelity Figma
   ↓
AI Context
   └── CLAUDE.md / AGENTS.md（分层 + 上下文预算）
   ↓
AI Coding（Task Brief 驱动，一个模块一个会话）
   ├── Frontend
   └── Backend
   ↓
★★★★★ Gate 3：AI 代码评审 + 安全扫描
   ↓
Integration / E2E（BR→AC→TC 全链追溯）
   ↓
★★★★★ Gate 4：Release Readiness
   ↓
CI/CD + Deployment（可回滚、可观测）
   ↓
监控反馈 → 变更控制（CCR）→ 回到对应阶段
```

> **核心思想不是"让 AI 一次性生成整个项目"，而是把整个项目拆成一组有明确输入、输出、权威关系和质量 Gate 的设计资产，再让 AI 在这些资产的约束下完成实现——并用与人类工程师相同的标准（评审、扫描、测试、追溯）验证 AI 的每一份产出。**
