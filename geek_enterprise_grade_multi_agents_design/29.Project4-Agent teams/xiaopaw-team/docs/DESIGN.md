# XiaoPaw-Team 综合设计文档

> **项目**：xiaopaw-team（极客时间《企业级多智能体设计实战》第 29 课实战项目）
> **继承基础**：xiaopaw-with-memory（第 17 课工具篇 + 第 22 课记忆篇）
> **定位**：把 17/22 课的单 Agent 工作助手扩展为 Manager+PM+RD+QA 四角色数字员工团队，装配 25-28 课的所有机制，端到端做完一个真实 toC 项目 + 自我进化一次
> **版本**：v1.5 综合版（v1.4 + skill-creator 规范 review 修订）
> **最后更新**：2026-04-20
> **关联文档**：
> - [docs/design-modules.md](./design-modules.md) — 基础模块详设（17/22 课继承）
> - [docs/design-data.md](./design-data.md) — 数据格式详设
> - [docs/design-api.md](./design-api.md) — 飞书接口详设
> - [docs/design-observability.md](./design-observability.md) — 日志与指标详设
> - [docs/history/](./history/) — 版本迭代历史（v0.2 架构 / v0.3 流程 / v1.1 纯团队层）

---

## v1.5 修订记录（skill-creator 规范 review 吸收）

基于 v1.4 用 SKILL.md 通用规范（frontmatter 三要素 / 单一职责 / 可复用性 / 触发清晰）逐个 review 32 个 skill，本次改动主要是 P0 级的 4 条工程整洁化（不改架构，只改命名和归属）：

| # | 修订点 | 位置 |
|---|---|---|
| v1.5-A1 | **self_retrospective 抽到 shared**：PM/RD/QA 三份高度重复（70% 内容一致），挪到 `workspace/shared/skills/self_retrospective/`（owner_role=any），角色差异留在 agent.md 补一句 | §4 / §16.2-4 / §16.6 / §30.3 |
| v1.5-A2 | **review_* 跨角色命名消歧**：RD / QA / PM 同名不同视角。改名规则："{artifact} review by {perspective}" → `review_product_design_from_rd` / `review_product_design_from_qa` / `review_tech_design_from_pm` / `review_tech_design_from_qa`；仅角色独有的（RD `review_test_design` / QA `review_code`）保持原名 | §16.2-4 / §13.2 sop_feature_dev / §阶段 2.6-2.7 / §阶段 8 / §30 |
| v1.5-A3 | **sop_selector 改名 list_available_sops**：原名"selector"像 reference 决策型但实际是 task（扫目录），改为动词+名词更准确 | §16.1 / §13.1 / §阶段 1.3 / §30.2 |
| v1.5-A4 | **3 个 reference skill description 补触发源**：`read_project_state` / `handle_checkpoint_reply` / `review_proposal` 加入"被什么触发"的明示 | §16.1 |
| v1.5-A5 | **附录 C 补 description 三要素规范**：触发源 + 能力 + 产出暗示 | 附录 C |
| v1.5-A6 | **22 课 legacy skill-creator 改名 skill_crystallize**：避免和 claude-code 社区的 skill-creator 同名混淆 | §16.6 |

数量变化：

| 前 | 后 |
|----|----|
| Manager 11 + PM 4 + RD 6 + QA 7 + shared 1 + legacy 5 = **34** | Manager 11 + PM 3 + RD 5 + QA 6 + shared 2 + legacy 5 = **32**（但 legacy 仍算系统基建，本课新增实际 **27 - 2(self_retrospective 移位) + 1(shared 增) = 26**） |

更核心的是"skill 分布更合理"：shared/ 下放真正跨角色的（self_score / self_retrospective）；role/skills/ 下只放角色特异 skill；review_* 命名明确区分视角。

---

## v1.4 修订记录（对齐 28 课《复盘机制重构》）

28 课原设计被大幅重构，复盘机制从"流水线脚本"改成"Agent 思考框架 + 统一 CLI + 自执行"。xiaopaw-team 对应章节全部对齐：

| # | 修订点 | 位置 | 破坏性改动？ |
|---|---|---|---|
| v1.4-1 | **Skill = 思考框架**：self_retrospective / team_retrospective SKILL.md 不再规定脚本调用顺序，只给"5 个递进问题"+ root_cause 枚举 + 输出格式 | §16.1 / §16.2-4 / §阶段 6.2 | 是 |
| v1.4-2 | **统一 CLI 入口 `tools/log_query.py`**：替代 v1.3 的 stats_l2 / find_low_quality / read_l3 / search_l1 分立脚本；一个入口多个子命令（stats / tasks / steps / l1 / all-agents） | §30.3 新文件 + §25 日志 + 附录 G | 是 |
| v1.4-3 | **RetroProposal schema 重构**：取消 `checksum_before` / `blast_radius`（不符合 28 课新设计），改成 retrospective_report + improvement_proposals 两段式；改动用 `before_text` / `after_text` 锚点而非 checksum | 附录 A2 重写 | 是 |
| v1.4-4 | **取消 ApplyProposalTool**：28 课新设计下 apply 由提案 Agent 自己机械执行（读文件→找锚点→替换→写回）；xiaopaw-team 相应去掉 Manager 专属 Tool，改成 PM/RD/QA 的 agent.md 里加一条"收到 retro_approved 后的执行流程" | §15.2 / §阶段 6.5 / §15.3 砍掉列表 | 是 |
| v1.4-5 | **workspace 不再强制是 git 仓库**：ApplyProposalTool 没了就不需要宿主机 git commit；但仍建议保留 git 用作版本追溯（每次 `retro_applied` 后自动 commit 留审计轨迹），检查改成 soft warn | §7.2 / §28.3 | 否（宽松化） |
| v1.4-6 | **review_proposal 分档审批**：v1.3 "accept/reject 二分"改为 28 课"按改动深度分档"：memory 自动批（3条/天硬闸门）+ skill/agent 转 Human + soul 标高风险 | §16.1 / §16.1.3 / §阶段 6.3-6.4 | 是 |
| v1.4-7 | **Skill 改名对齐 28 课**：`review_proposals`（复数）→ `review_proposal`（单数，每次审一条）；skill 名 + 事件名 + 邮件 subject 都同步改 | §16.1 / 附录 A 事件 / 附录 B | 是 |
| v1.4-8 | **新增事件**：`retro_report_received` / `retro_approved_by_manager` / `retro_approved_by_human` / `retro_rejected_by_human` / `retro_applied_by_{role}`；对应 v1.3 的 proposal_applied / proposal_rejected 系列被替换 | 附录 A | 是 |
| v1.4-9 | **新增邮件 type**：`retro_report`（角色→Manager）/ `retro_approved`（Manager→角色）/ `retro_rejected`（Manager→角色）/ `retro_applied`（角色→Manager 确认执行完）| 附录 B | 是 |
| v1.4-10 | **PM/RD/QA agent.md 补"收到 retro_approved 后机械执行"流程**：读文件 → 找 before_text 锚点 → 替换 after_text → 写回 → 可选 git commit → 发 retro_applied 回 Manager | §10.4 / §16.2-4 | 是 |
| v1.4-11 | **proposals 存储路径**：`shared/proposals/{agent_id}_retro_{date}.json`（28 课原路径）| §11.1 / 附录 A2 | 是 |
| v1.4-12 | **seed_logs 时间戳问题**：E2E / demo 前执行 `python3 seed_logs.py` 重新生成基于当前时刻的过去 7 天日志；README 补说明 | §25 末尾 + §31 里程碑 | 否（演示配套） |
| v1.4-13 | **新增 self_score skill**（共享 reference）：补齐 L2 `result_quality_estimate` 字段的来源——Agent 在 task_done 前自评 5 维加权分数，写入 send_mail content，task_callback 读取写 L2 | §16.5 新增 + §25.2 L2 schema + §16.2-4 各角色 skill 表 + 附录 C2 | 是 |

保留 v1.3 原有修订。

---

## v1.3 修订记录（测试驱动反向 review 吸收，20 条）

v1.2 综合版写完后，基于 `docs/test-design.md` 做了一轮 **test-driven design review**——发现测试用例要能落地，设计里必须把隐含契约显性化。v1.3 吸收了该轮 P0 × 6 + P1 × 8 + P2 × 6：

| # | 修订点 | 位置 |
|---|---|---|
| v1.3-P0-1 | **定义 L1 / L2 日志 entry schema** | §25 + 附录 H 新增 |
| v1.3-P0-2 | **定义 RetroProposal schema + review_proposals 返回值** | 附录 A2 新增 |
| v1.3-P0-3 | **proposals_approve 卡片按钮 → approved_ids[] 完整路径** | §12.1.1 + §12.2 + §阶段 6.5 |
| v1.3-P0-4 | **Manager 阈值判断机械化**：check_review_criteria 直接返回 threshold_met bool | §16.1 + §阶段 2.4 |
| v1.3-P0-5 | **ApplyProposalTool 禁用机制统一**：方案 B 宽容——无 workspace/.git 时 build_role_tools skip + log WARNING，附录 G assert 改为 warn | §7.2 / §15.2 / §28.3 / 附录 G |
| v1.3-P0-6 | **统一 timestamp 时区规范**：全项目统一 ISO 8601 UTC 带 `+00:00` 后缀 | 附录 A / 附录 B / §11.3 |
| v1.3-P1-7 | **新增 3 个结构化决策事件**：requirements_coverage_assessed / retro_quorum_checked / checkpoint_reply_classified | 附录 A |
| v1.3-P1-8 | **task skill 返回值约定**：强制 JSON 字符串含 status/artifacts/metrics/errors | 附录 C2 新增 |
| v1.3-P1-9 | **requirements_guide 四维明确定义**：goal/boundary/constraint/risk | §16.1 |
| v1.3-P1-10 | **subject grammar**：regex `^.*\(第 (\d+) 轮\)$` | §阶段 2.8 + §13.2 sop_feature_dev |
| v1.3-P1-11 | **classify 词边界匹配**：改用 `text.strip()` 完全匹配 + 词白名单 set | §12.1.1 |
| v1.3-P1-12 | **CronService every jitter 首次偏移语义 + heartbeat 错峰** | §7.1 / 附录 G |
| v1.3-P1-13 | **L3 路径统一**：`ctx_dir/{session_id}_raw.jsonl`，删除 §25 旧路径 | §8.3 / §25 |
| v1.3-P1-14 | **CreateProjectTool 完整目录/文件清单** | §15.2 |
| v1.3-P2-15 | **§29 单一接口 checklist 表**（3 重保证对应校验点） | §29.1 |
| v1.3-P2-16 | **§11.2 权限校验测试矩阵表** | §11.2 |
| v1.3-P2-17 | **附录 A 每条 action payload required/optional 标注** | 附录 A |
| v1.3-P2-18 | **修 §9.3.2 死链**：原文指向的章节重命名为 §11.4.1 | §11.4.1 |
| v1.3-P2-19 | **code_impl SKILL 返回值 metrics**：pytest_attempts / coverage / pytest_final_status | §16.3 + 附录 C2 |
| v1.3-P2-20 | **修 reviews/ 正则贪婪匹配漏洞**：改为显式角色白名单 | §11.2 |

---

## v1.2 修订记录（第三轮 architect review 吸收）

v1.1 综合版经第三轮 review 后做了以下修订（全文 P0 7 条 + 关键 P1/P2）：

| # | 修订点 | 位置 |
|---|---|---|
| P0-1 | **SKILL 物理路径与沙盒挂载一致化**：29 课 role-scoped SKILL 在 `workspace/{role}/skills/`，挂到沙盒 `/workspace/{role}/skills/`；22 课公共 skill 保持挂 `/mnt/skills` 但源路径改为 `workspace/shared/legacy_skills/` | §4 / §6.2 / §7.3 / §28.2 |
| P0-2 | **CronService 不改 API**：at wake 通过 `_tasks_store.create_job()` 函数级 API 写入 `data/cron/tasks.json`（22 课 mtime 热重载会捕获），不新增 `register_job` 方法 | §7.1 / §13.4 |
| P0-3 | **task_callback project_id 来源**：每个角色 MemoryAwareCrew 实例持有 `current_project_id` 闭包字段，由 Manager 在 create_project 后广播，其他角色从 `shared/projects/*/events.jsonl` 推断最新 active | §15.4 / §8.3.1 |
| P0-4 | **feishu_bridge.classify() 规则**：先查飞书卡片 callback.value，回退关键词规则；兜底 need_discussion | §12.1.1 |
| P0-5 | **session 工作区路径语义澄清**：22 课 session 工作区落在 `data/workspace/sessions/`（与 xiaopaw-with-memory 一致）；29 课团队共享区在 `workspace/` 根目录（独立 git 仓库，挂载到沙盒）；两者并存不冲突 | §4 / §7.2 / §28.4 |
| P0-6 | **SkillLoader 扩展签名明示**：给出完整 `__init__(role, skills_dir, sandbox_skills_mount, team_standards, ...)` 签名 | §6.2 |
| P0-7 | **正文去历史化**：§11.4 / §6.1 / §17.1 的"相对 v0.3 / 22 课教义"对比话术搬到附录 F | §6.1 / §11.4 / §17.1 / 附录 F |
| P1-8 | **附录 G 新增 main.py 骨架伪代码**（~50 行 Python） | 附录 G |
| P1-9 | **每角色 session_id 生命周期**：固定 `team-{role}-{workspace_id}`，跨 wake 持久化 | §8.3.1 |
| P1-10 | **build_role_tools(role, cfg) 工厂函数说明** | §30.2 |
| P1-11 | **SkillLoader 热重载时清 `_instruction_cache`** | §6.2 |
| P1-13 | **附录 A 事件枚举按流程剧本重写 + 每条附 payload 示例** | 附录 A |
| P1-14 | **"如何阅读子文档"指引** | §4 末 |
| P2-16 | **§10.4 agent.md / soul.md 分工细化**：决策偏好在 soul.md，agent.md 只写 Role Charter + 名册（与 25 课对齐） | §10.4 |
| P2-19 | **附录 E 补 "task skill 一次性执行限制"** | 附录 E |

---

## 目录

### 一、基础部分
1. [项目概述](#1-项目概述)
2. [课程继承与职责](#2-课程继承与职责)
3. [系统架构总览](#3-系统架构总览)
4. [代码目录结构](#4-代码目录结构)

### 二、基础设施层（继承 17/22 课）
5. [FeishuListener + Runner + Sender](#5-feishulistener--runner--sender)
6. [Main Agent + SkillLoaderTool + Sub-Crew](#6-main-agent--skillloadertool--sub-crew)
7. [CronService + CleanupService + AIO-Sandbox](#7-cronservice--cleanupservice--aio-sandbox)
8. [记忆层：Bootstrap / ctx.json / pgvector](#8-记忆层bootstrap--ctxjson--pgvector)

### 三、团队协作层（29 课新增）
9. [核心设计原则](#9-核心设计原则)
10. [四角色与四层框架](#10-四角色与四层框架)
11. [协作机制：邮箱 + 共享区 + 事件流](#11-协作机制邮箱--共享区--事件流)
12. [飞书桥与单一接口](#12-飞书桥与单一接口)
13. [唤醒机制](#13-唤醒机制)
14. [沙盒与执行隔离](#14-沙盒与执行隔离)

### 四、Tools 与 Skills
15. [Tools 清单](#15-tools-清单)
16. [Skills 清单（按角色）](#16-skills-清单按角色)
17. [SOP 作为 reference skill + Skill 类型边界](#17-sop-作为-reference-skill--skill-类型边界)

### 五、完整业务流程
18. [阶段 0：SOP 共创](#阶段-0sop-共创可选一次性)
19. [阶段 1：需求澄清与确认](#阶段-1需求澄清与确认)
20. [阶段 2：产品设计](#阶段-2产品设计含可选团队评审)
21. [阶段 3：RD 设计 + 实现 + 单测](#阶段-3rd-设计--实现--单测)
22. [阶段 4：QA 走查 + 测试设计 + 执行](#阶段-4qa-走查--测试设计--执行)
23. [阶段 5：交付](#阶段-5交付)
24. [阶段 6：团队复盘与进化](#阶段-6团队复盘与进化)

### 六、日志、进化、运维
25. [三层日志](#25-三层日志)
26. [三档 HITL 与 ApplyProposalTool](#26-三档-hitl-与-applyproposaltool)
27. [配置与环境](#27-配置与环境)
28. [运维与部署](#28-运维与部署)
29. [安全设计](#29-安全设计)
30. [对 xiaopaw-with-memory 的改动清单](#30-对-xiaopaw-with-memory-的改动清单)
31. [测试与里程碑](#31-测试与里程碑)

### 附录
- [附录 A · 事件流 events.jsonl 结构](#附录-a--事件流-eventsjsonl-结构)
- [附录 B · 邮箱消息 type 枚举](#附录-b--邮箱消息-type-枚举)
- [附录 C · Skill frontmatter 规范](#附录-c--skill-frontmatter-规范)
- [附录 D · 每个数字员工的完整清单](#附录-d--每个数字员工的完整清单)
- [附录 E · 非目标与已知局限](#附录-e--非目标与已知局限)
- [附录 F · 版本迭代历史](#附录-f--版本迭代历史)
- [附录 G · main.py 骨架伪代码](#附录-g--mainpy-骨架伪代码p1-8-新增)

---

# 一、基础部分

## 1. 项目概述

### 1.1 定位

**xiaopaw-team** 是模块四的实战收官项目。它**不是**从头造一个新系统，而是一次**工程装配练习**——在 17/22 课单 Agent 工作助手（xiaopaw-with-memory）的基础上，扩展出 Manager + PM + RD + QA 四角色数字员工团队，装配 25-28 课讲过的所有机制（角色体系、任务链协作协议、Human as 甲方、自我进化），配一个真实 toC 项目需求，端到端跑一遍，最后完成一轮团队自我进化。

**课程价值不在于新发明，在于验证一件事**：当 17/22/25-28 课的机制同时在线跑，它们是否真能协作解决一个真实问题，中间有哪些接缝需要额外补齐。装配过程中需要补的接缝（team_protocol、event log、团队唤醒、单沙盒协同、SOP 作为 Skill）就是本课工程增量。

### 1.2 Demo 项目：**"小爪子日记"**（PawDiary）

toC 宠物日记单页网站。选它的理由：
- 呼应 xiaopaw 品牌叙事
- CRUD + 列表 + 时间线，功能量足以让 RD 写分层代码
- 前后端都真实、有清晰可测性
- 规模适中，一周可做完

**实体**：
- `Pet`: id, name, species, birthday, avatar_url, created_at
- `Diary`: id, pet_id, date, content, mood (happy/normal/sad), photos[], created_at

**后端 REST API**：Pets CRUD × 5 接口 + Diaries CRUD × 3 接口

**前端**：index.html（宠物列表卡片 + 添加按钮） + pets/{id}.html（详情 + 日记时间线）

**技术栈**：FastAPI + SQLAlchemy 2.0 + SQLite + 原生 HTML/JS/CSS + pytest + httpx。**不是硬约束**，而是 RD 的 `tech_design` skill 里的推荐栈；如任务需要 RD 可自主偏离，只要满足硬约束（pytest 全 PASS / coverage ≥ 80% / 分层清晰 / 前端无构建工具 / 禁止启长期进程如 uvicorn）。

---

## 2. 课程继承与职责

### 2.1 各课程贡献内容

| 课程 | 贡献内容 | 本项目继承方式 |
|------|---------|---------------|
| **第 17 课（工具篇）** | 基础框架：FeishuListener / SessionRouter / Runner / FeishuSender / Main Agent + SkillLoaderTool / Sub-Crew + AIO-Sandbox / CronService / CleanupService / TestAPI；MVP Skills（pdf/docx/pptx/xlsx/feishu_ops/scheduler_mgr/baidu_search/web_browse/history_reader） | **完全复用 + 小扩展**（见 §30 改动清单） |
| **第 22 课（记忆篇）** | 三层记忆架构：Bootstrap 文件注入（L19）+ ctx.json/raw.jsonl 上下文压缩（L19）+ pgvector 语义搜索（L21）+ 4 个记忆 Skills（memory-save / skill-creator / memory-governance / search_memory） | **完全复用 + 扩展第五文件 team_protocol.md + pgvector 加 role/project_id metadata** |
| **第 25 课（团队角色体系）** | 四层框架（soul + agent + memory + user）；三维隔离判断法；NEVER 清单；中心协调模式 | **原样应用**，每个角色一个 workspace/{role}/ 目录 |
| **第 26 课（任务链与协作协议）** | 共享工作区；文件邮箱（JSON + filelock + 三态状态机：unread→in_progress→done）；workspace-rules | **原样应用 + 扩展 project_id 字段** |
| **第 27 课（Human as 甲方）** | 需求澄清 / 设计确认 / 异常兜底三个介入点；单一接口原则；checkpoint 机制 | **架构硬约束：飞书只通 Manager** |
| **第 28 课（数字员工自我进化）** | 三层日志（L1/L2/L3）；复盘六步漏斗；三档 HITL；RetroProposal schema；apply_proposal 机械应用 | **完整应用 + L2 钩子用 task_callback 不是 after_llm_call** |
| **第 29 课（本课实战）** | 把以上装配成团队：team_protocol.md / sop_feature_dev SKILL / events.jsonl 事件流 / feishu_bridge 飞书桥 / 团队唤醒机制 | **唯一纯新增层** |

### 2.2 基础框架速查

17/22 课基础内容不在本文档重复展开，关键组件对照见下表，完整详设见 `docs/design-*.md`：

| 组件 | 所在文件 | 职责 | 本课扩展 | 详设文档 |
|------|---------|------|---------|---------|
| FeishuListener | `xiaopaw_team/feishu/listener.py` | 维护飞书 WebSocket，解析事件为 InboundMessage | 无（完全复用） | [design-modules.md §1](./design-modules.md) |
| SessionRouter | `xiaopaw_team/feishu/session_key.py` | 把 p2p/group/thread 映射成 routing_key | 无 | [design-modules.md §2](./design-modules.md) |
| Runner | `xiaopaw_team/runner.py` | per-routing_key 串行队列 + Slash 拦截 + Agent 调度 | **增加 `team:{role}` routing_key 路由；cron wake 去重；InboundMessage.meta.wake_reason** | [design-modules.md §3](./design-modules.md) |
| Main Agent + SkillLoaderTool | `xiaopaw_team/agents/main_crew.py` + `tools/skill_loader.py` | 极简主 Agent（22 课原则是唯一 SkillLoaderTool），渐进式披露 Skills | **29 课扩展：除 SkillLoaderTool 外还有 8 个团队协作 Tool；4 份 manifest（每角色一份）+ `kind`/`owner_role` frontmatter + `{team_standards.X}` 变量替换 + manifest mtime 热重载** | [design-modules.md §4](./design-modules.md) |
| Sub-Crew | `xiaopaw_team/agents/skill_crew.py` | 任务型 Skill 触发时动态构建隔离 Sub-Crew，接入 AIO-Sandbox MCP | 无 | [design-modules.md §5](./design-modules.md) |
| CronService | `xiaopaw_team/cron/service.py` | asyncio 精确 timer + mtime 热重载 tasks.json + fake 消息进 Runner | **团队 wake：注册 `at=now+1s` one-shot + 每角色 `every 30s+jitter` heartbeat** | [design-modules.md §6](./design-modules.md) |
| CleanupService | `xiaopaw_team/cleanup/service.py` | 双触发（启动 + 每日 3:00）清理过期文件 | **增加团队工作区初始化 + workspace git 状态检查** | [design-modules.md §8](./design-modules.md) |
| FeishuSender | `xiaopaw_team/feishu/sender.py` | 按 routing_key 类型选 API，幂等 + 重试 | **新增 `send_card(type, title, summary, artifacts)` 支持 6 种卡片类型** | [design-modules.md §7](./design-modules.md) |
| memory/bootstrap | `xiaopaw_team/memory/bootstrap.py` | 读 workspace 4 文件（soul/user/agent/memory.md）构建 Agent backstory | **扩展：可选读第 5 文件 `shared/team_protocol.md`** | [design-modules.md §10](./design-modules.md) |
| memory/context_mgmt | `xiaopaw_team/memory/context_mgmt.py` | prune/compress + ctx.json/raw.jsonl 持久化 | 无 | [design-modules.md §11](./design-modules.md) |
| memory/indexer | `xiaopaw_team/memory/indexer.py` | 每轮结束异步提取摘要 + 向量化 + 写入 pgvector | **扩展：async_index_turn 增加 role + project_id 参数；pgvector 表增加两列 metadata** | [design-modules.md §12](./design-modules.md) |

---

## 3. 系统架构总览

### 3.1 三层分层模型

```
┌─────────────────────────────────────────────────────────────┐
│  L3: 团队协作层 (29 课新增)                                  │
│  ─ 4 Agent 实例（Manager/PM/RD/QA），每个有自己的 workspace  │
│  ─ team_protocol.md 共享协议 + team_standards.yaml 集中阈值  │
│  ─ 文件邮箱 + events.jsonl 事件流 + feishu_bridge 飞书桥     │
│  ─ SkillLoader 按角色 manifest 加载 + heartbeat/wake cron    │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  L2: 记忆层 (22 课)                                          │
│  ─ Bootstrap 注入 workspace 4 文件（+ 29 课第 5 文件）       │
│  ─ ctx.json 压缩快照 + raw.jsonl 审计日志（跨 session 恢复） │
│  ─ pgvector 语义搜索（+ 29 课 role/project_id metadata）     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  L1: 基础设施层 (17 课)                                      │
│  ─ FeishuListener/Sender（WebSocket + REST + 卡片）          │
│  ─ Runner（per-routing_key 串行队列 + Slash 拦截）           │
│  ─ Main Agent + SkillLoaderTool（渐进披露）                  │
│  ─ Sub-Crew + AIO-Sandbox（MCP 沙盒执行）                    │
│  ─ CronService（精确 timer + tasks.json 热重载）             │
│  ─ CleanupService（双触发清理）                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 整体架构图

```
┌────── 用户（飞书）──────┐
│    晓寒（ou_d683...）    │
└──────────┬───────────────┘
           │ WebSocket  (routing_key = p2p:ou_d683...)
           ▼
┌──── xiaopaw-team 单进程 ─────────────────────────────────────┐
│                                                                │
│  FeishuListener ──► feishu_bridge.recv ──► Runner             │
│                                              │                 │
│    routing_key = p2p:ou_xxx ────────────────► Manager Agent   │
│    routing_key = team:manager ──────────────► Manager Agent   │
│    routing_key = team:pm ────────────────────► PM Agent       │
│    routing_key = team:rd ────────────────────► RD Agent       │
│    routing_key = team:qa ────────────────────► QA Agent       │
│                                                                │
│    Manager agent_fn 外包 asyncio.Lock（跨 routing_key 串行）  │
│                                                                │
│  CronService                                                   │
│    每角色 every 30s+jitter ─► 构造 team:{role} wake 消息       │
│    SendMailTool 内部 ─► 注册 at=now+1s one-shot wake           │
│    cron wake 去重：dispatch 前检查队列是否有 pending wake     │
│                                                                │
│  每个 Agent = MemoryAwareCrew + SkillLoaderTool + 协作工具     │
│    LLM kickoff → SkillLoader.description 选 skill             │
│    → ref skill 返回文本 / task skill 启动 Sub-Crew 在沙盒      │
│                                                                │
│  FeishuSender ◄─ 只注入 Manager Agent（单一接口原则）          │
└────────────────────────────────────────────────────────────────┘
               ↕ 文件系统（挂载）
┌─── 单 AIO-Sandbox ──────────────────────────────────────┐
│  /workspace/                                            │
│    ├── manager/ pm/ rd/ qa/  ← 每角色 workspace         │
│    │     └── {soul,agent,memory,user}.md + skills/     │
│    ├── shared/                                          │
│    │   ├── team_protocol.md  ← 所有角色共用协作约定    │
│    │   ├── config/team_standards.yaml ← 集中阈值       │
│    │   ├── sop/              ← 预留：跨项目共享 SOP    │
│    │   ├── projects/{pid}/                              │
│    │   │   ├── needs/ design/ tech/ code/ qa/           │
│    │   │   ├── reviews/{stage}/{reviewer}_{topic}.md    │
│    │   │   ├── mailboxes/{role}.json                    │
│    │   │   ├── events.jsonl  ← append-only 事件流      │
│    │   │   └── logs/l2_task/*.jsonl                     │
│    │   └── logs/l1_human/*.jsonl ← 跨项目永久          │
│    └── .config/feishu.json + baidu.json                 │
└─────────────────────────────────────────────────────────┘
                ↕
┌─── pgvector 容器 ─────────────────────────────┐
│  memories 表：session_id/summary/tags/vec      │
│              + role + project_id (29 扩展)    │
└────────────────────────────────────────────────┘
```

### 3.3 消息流向时序

一条飞书消息的完整处理路径（22 课时序图的 29 课扩展版）：

```
用户在飞书发消息
  │
  ├─► FeishuListener 收 WebSocket 事件
  │     │
  │     ├─► 解析 routing_key (p2p:ou_xxx)
  │     │
  │     └─► feishu_bridge.recv_human_response
  │           ├─ 查 events.jsonl 有无 pending checkpoint
  │           │   ├─ 有 → 写 manager.json 作为 checkpoint_response
  │           │   │       → SendMail 内部注册 at=now+1s cron
  │           │   │       → 走 team:manager 路径（见下）
  │           │   └─ 无 → 构造 InboundMessage(routing_key=p2p:ou_xxx) → Runner
  │           │           同时兜底 notify_role("manager") 避免等 30s heartbeat
  │
  ├─► Runner.dispatch
  │     │
  │     ├─► routing_key 路由表匹配 agent_fn：
  │     │    p2p:* → Manager agent_fn（外包 asyncio.Lock）
  │     │    team:{role} → 对应角色 agent_fn
  │     │
  │     ├─► 入 per-routing_key 队列（串行）
  │     │
  │     └─► cron wake 去重（相同 routing_key 已有 pending wake → 丢弃）
  │
  ├─► Agent.kickoff
  │     │
  │     ├─► Bootstrap 注入 backstory（4 个 workspace 文件 + 29 课第 5 文件 team_protocol.md）
  │     │
  │     ├─► @before_llm_call hook（22 课）
  │     │     ├─ 首次：ctx.json 恢复历史
  │     │     ├─ 每次：prune 旧 tool results
  │     │     └─ 每次：context > 45% 则 compress
  │     │
  │     ├─► LLM ReAct 循环
  │     │     ├─ Thought（推理）
  │     │     ├─ Action（调用 Tool）：
  │     │     │   ├─ SkillLoaderTool → reference（返回文本）/ task（启动 Sub-Crew）
  │     │     │   ├─ SendMailTool → 写邮箱 + 注册 at wake + mark_done 自己上条邮件
  │     │     │   ├─ ReadInboxTool → 读 unread 标 in_progress 返回快照
  │     │     │   ├─ SendToHumanTool (仅 Manager) → 发飞书卡片 + append event + L1 log
  │     │     │   ├─ AppendEventTool (仅 Manager) → events.jsonl filelock append
  │     │     │   └─ ApplyProposalTool (仅 Manager，在宿主机 Python 进程)
  │     │     │
  │     │     └─ Final Answer
  │     │
  │     ├─► task_callback → L2 日志
  │     │
  │     └─► async_index_turn（asyncio.create_task 异步）
  │           → 提取摘要 + embed + upsert pgvector（含 role/project_id）
  │
  └─► 如果是飞书触发 → FeishuSender 回复用户
```

---

## 4. 代码目录结构

```
xiaopaw-team/
├── pyproject.toml
├── config.yaml.template
├── sandbox-docker-compose.yaml
├── pgvector-docker-compose.yaml        ← 22 课原样复用（可选启动）
├── docs/
│   ├── DESIGN.md                       ← 本文档
│   ├── design-modules.md               ← 基础模块详设（继承 22 课）
│   ├── design-data.md                  ← 数据格式详设
│   ├── design-api.md                   ← 飞书接口详设
│   ├── design-observability.md         ← 日志与指标详设
│   └── history/                        ← 版本迭代历史
│       ├── v0.2-architecture.md
│       ├── v0.3-detailed-flow.md
│       └── v1.1-team-only.md
├── README.md                           ← 项目 README + workspace git 初始化说明
├── xiaopaw_team/
│   ├── main.py                         ← 进程入口：装配 4 Agent + CronService + Runner
│   ├── runner.py                       ← 22 课 Runner + team:{role} 路由 + cron wake 去重
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── build.py                    ← build_agent_fn(workspace, tools, shared) 工厂
│   │   ├── main_crew.py                ← 22 课 MemoryAwareCrew + task_callback 挂载
│   │   └── skill_crew.py               ← 22 课原样
│   ├── tools/                          ← 协作原子工具
│   │   ├── skill_loader.py             ← 22 课 + v1.1 扩展（见 §30）
│   │   ├── mailbox.py                  ← send_mail / read_inbox / mark_done / reset_stale（26 课算法）
│   │   ├── event_log.py                ← 写 events.jsonl（append-only + filelock）
│   │   ├── project_state.py            ← read_project_state 脚本入口（task skill 用）
│   │   ├── workspace.py                ← read_shared / write_shared + 权限校验
│   │   ├── feishu_bridge.py            ← send_to_human / recv_human_response
│   │   ├── create_project.py           ← CreateProject 工具（仅 mkdir + 空邮箱 + 空 events.jsonl）
│   │   ├── apply_proposal.py           ← ApplyProposalTool（宿主机 git subprocess）
│   │   ├── log_hooks.py                ← task_callback (L2) + L1 自动注入
│   │   ├── add_image_tool_local.py     ← 22 课原样
│   │   ├── baidu_search_tool.py        ← 22 课原样
│   │   └── intermediate_tool.py        ← 22 课原样
│   ├── feishu/                         ← 22 课原样（listener / downloader / sender + send_card）
│   ├── session/                        ← 22 课原样
│   ├── cron/                           ← 22 课原样
│   ├── memory/                         ← 22 课 + indexer 扩展
│   ├── cleanup/                        ← 22 课 + 团队初始化
│   ├── observability/                  ← 22 课原样
│   ├── api/                            ← 22 课 TestAPI 原样
│   └── llm/                            ← 22 课 AliyunLLM 原样
├── workspace/                          ← 挂载到沙盒，独立 git 仓库
│   ├── .git/                           ← apply_proposal 依赖
│   ├── manager/
│   │   ├── soul.md agent.md memory.md user.md
│   │   └── skills/
│   │       ├── load_skills.yaml        ← Manager 专属 manifest
│   │       ├── sop_cocreate_guide/SKILL.md              ← reference
│   │       ├── sop_write/SKILL.md + scripts/            ← task
│   │       ├── list_available_sops/SKILL.md + scripts/    ← task（v1.5-A3 从 sop_selector 改名）
│   │       ├── sop_feature_dev/SKILL.md                 ← reference, kind=sop
│   │       ├── requirements_guide/SKILL.md              ← reference
│   │       ├── requirements_write/SKILL.md + scripts/   ← task
│   │       ├── read_project_state/SKILL.md + scripts/   ← task
│   │       ├── check_review_criteria/SKILL.md + scripts/← task
│   │       ├── handle_checkpoint_reply/SKILL.md         ← reference
│   │       ├── team_retrospective/SKILL.md + scripts/   ← task
│   │       └── review_proposal/SKILL.md                 ← reference（v1.4 改名）
│   ├── pm/
│   │   └── skills/
│   │       ├── product_design/                          ← task
│   │       └── review_tech_design_from_pm/              ← reference（v1.5-A2 改名）
│   ├── rd/
│   │   └── skills/
│   │       ├── tech_design/                             ← task
│   │       ├── code_impl/                               ← task
│   │       ├── review_product_design_from_rd/           ← reference（v1.5-A2 改名）
│   │       └── review_test_design/                      ← reference（仅 RD 有，不需消歧）
│   ├── qa/
│   │   └── skills/
│   │       ├── review_product_design_from_qa/           ← reference（v1.5-A2 改名）
│   │       ├── review_tech_design_from_qa/              ← reference（v1.5-A2 改名）
│   │       ├── review_code/                             ← reference（仅 QA 有）
│   │       ├── test_design/                             ← task
│   │       └── test_run/                                ← task
│   └── shared/
│       ├── team_protocol.md            ← 所有角色共用元规则
│       ├── config/team_standards.yaml  ← 集中阈值
│       ├── skills/                     ← v1.5 新增 shared 目录（本课）
│       │   ├── self_retrospective/     ← task（v1.5-A1 从 PM/RD/QA 挪入）
│       │   └── self_score/             ← reference（v1.4-13）
│       ├── legacy_skills/              ← 22 课公共 skill
│       │   ├── search_memory/ memory-save/ memory-governance/ history_reader/
│       │   └── skill_crystallize/      ← v1.5-A6 从 skill-creator 改名
│       ├── sop/                        ← 预留：跨角色共享 SOP
│       ├── projects/                   ← 运行时创建
│       ├── proposals/                  ← v1.4 复盘 JSON 产出
│       └── logs/l1_human/              ← 跨项目永久
├── data/                               ← 运行时数据（gitignore）
│   ├── sessions/ traces/ cron/ logs/
└── tests/
    ├── unit/
    └── integration/
```

### 4.1 如何阅读子文档（P1-14 新增）

`docs/design-modules.md` / `design-data.md` / `design-api.md` / `design-observability.md` 是从 22 课原样继承的详设，**未对 29 课做全面修订**。读这些文档时请带以下映射：

| 子文档描述 | 29 课实际含义 |
|------------|---------------|
| session 工作区 `workspace/sessions/{sid}/` | 改为 `data/workspace/sessions/{sid}/`（§7.2 两套路径并存） |
| 全局单份 `load_skills.yaml` | 改为 4 份（每角色 `workspace/{role}/skills/load_skills.yaml`，§6.2 扩展 2） |
| Agent tools 只有 SkillLoaderTool | 改为 SkillLoaderTool + 团队协作工具（§6.1 / §15） |
| `/mnt/skills` 沙盒挂载 | 改为 `/workspace/{role}/skills` 每角色挂载 + `/workspace/shared/legacy_skills` 公共 legacy skill（§7.3） |
| memories 表无 role/project_id | 加两列（§8.4） |
| `build_bootstrap_prompt(workspace_dir)` | 改为 `build_bootstrap_prompt(workspace_dir, shared_protocol=None)`（§8.2） |
| `@after_llm_call` 做 L2（注：22 课明确警示其会破坏 tool dispatch） | 改用 `task_callback`（§15.4） |

**其他细节以 DESIGN.md 为准**；子文档不保证与 DESIGN.md 29 课扩展一一对应。

---

# 二、基础设施层（继承 17/22 课）

本章对 17/22 课框架的每个组件做精要说明 + 29 课扩展点。各组件的完整内部实现见 `docs/design-modules.md`；数据格式见 `docs/design-data.md`；外部接口见 `docs/design-api.md`。

## 5. FeishuListener + Runner + Sender

### 5.1 FeishuListener（17 课 · 无本课改动）

维护飞书 WebSocket 长连接，基于 `lark-oapi` 的 ws.Client 订阅 `im.message.receive_v1` 和 `im.chat.member.bot.added_v1` 事件。

- 单进程单连接，不负责文件下载（延迟到 Runner session 确定后）
- 支持 `allowed_chats` 白名单（p2p 始终放行，群消息按白名单过滤）
- 支持 `on_bot_added` 回调（入群欢迎）

详见 [design-modules.md §1](./design-modules.md#1-feishulistener-模块)。

### 5.2 SessionRouter / routing_key（17 课 + 29 课扩展）

| routing_key 格式 | 来源 | 说明 |
|-----------------|------|------|
| `p2p:{open_id}` | 飞书私聊 | 原 17 课格式 |
| `group:{chat_id}` | 飞书群聊 | 原 17 课格式 |
| `thread:{chat_id}:{thread_id}` | 话题群 | 原 17 课格式 |
| `team:{role}` | 29 课新增 | 团队内角色唤醒（cron/wake 触发），role ∈ {manager, pm, rd, qa} |

### 5.3 Runner（17 课 + 29 课扩展）

核心职责（17 课原样）：
- **per-routing_key 串行队列**：同 routing_key 消息严格串行，不同 routing_key 并行
- **Slash Command 拦截**：`/new` `/verbose` `/help` `/status` 在进 Agent 前处理
- **Agent 调度**：调用 agent_fn(message, history, session_id, routing_key, root_id, verbose)
- **queue 空闲超时**：默认 300s 后释放 worker

29 课扩展：
- **多 agent_fn 路由**：Runner 持有 `{role: agent_fn}` 映射，dispatch 时按 `team:{role}` 前缀选角色，`p2p:*` → manager
- **cron wake 去重**：dispatch 前检查队列是否已有 `meta.wake_reason ∈ {new_mail, heartbeat}` 的 pending 消息，重复则丢弃，避免 at cron + heartbeat 同时触发导致 Agent 空跑
- **InboundMessage.meta 扩展**：新增 `wake_reason` 字段（`feishu` / `new_mail` / `heartbeat`），Agent LLM 在 heartbeat + inbox 空时可直接返回 noop

详见 [design-modules.md §3](./design-modules.md#3-runner-模块)。

### 5.4 FeishuSender（17 课 + 29 课扩展）

17 课核心：
- 按 routing_key 类型选 API：p2p/group 用 CreateMessage；thread 用 ReplyMessage with `reply_in_thread=True`
- 幂等（uuid 传入飞书 message_id）
- 指数退避重试（默认 3 次，backoff [1,2,4]s）
- 三种发送接口：`send()` 发主回复（interactive 卡片 lark_md）/ `send_thinking()` 发加载卡片 / `update_card()` PATCH 更新卡片

29 课扩展：
- **`send_card(type, title, summary, artifacts)`**：按 type 构造卡片模板。type 枚举：
  - `info`：普通通知（无按钮）
  - `checkpoint_request`：Approve/Reject 按钮
  - `proposals_review`：多条提案逐条 approve
  - `delivery`：交付摘要 + 产物链接
  - `evolution_report`：git diff 摘要
  - `error_alert`：告警（醒目色）

**单一接口原则**（27 课硬约束）：`FeishuSender` 实例**只注入 Manager Agent** 的 Crew 构造器。PM/RD/QA 的 Crew 构造器不接受 `feishu_sender` 参数——架构层保证，不是 LLM 自律。

详见 [design-modules.md §7](./design-modules.md#7-feishusender-模块) + [design-api.md](./design-api.md)。

---

## 6. Main Agent + SkillLoaderTool + Sub-Crew

### 6.1 Main Agent（22 课 · 本课每角色一个）

22 课设计："Main Agent has exactly one tool: SkillLoaderTool"——极简主 Agent + 丰富 Skill 生态。

29 课每个角色的 Main Agent 除 SkillLoaderTool 外，还持有**团队协作基础设施 Tool**（SendMail/ReadInbox/MarkDone/ReadShared/WriteShared/SendToHuman/AppendEvent/CreateProject/ApplyProposal）。理由：
- 发一封邮件如果走 task skill + Sub-Crew，每次几秒开销 + 额外 LLM 调用
- 多轮对话主 Agent 需要"发问"的原子能力，SkillLoader 不提供
- 每次 read_inbox 启 Sub-Crew 毫无意义

详细 Tool 清单见 §15；Skill 类型边界见 §17.1；迭代背景见附录 F。

### 6.2 SkillLoaderTool（22 课 + 29 课四项扩展）

**22 课核心机制**（源码在 `xiaopaw_team/tools/skill_loader.py`）：

**渐进式披露**：
- **阶段 1**（`__init__` → `_build_description`）：读 `load_skills.yaml` manifest，对每个 enabled skill 只解析 SKILL.md 的 YAML frontmatter（`name` + `description`），构建轻量 XML 注入工具 description
- **阶段 2**（`_get_skill_instructions`）：调用时才读完整 SKILL.md 正文，剥离 frontmatter，拼接 sandbox_execution_directive。结果写入 `_instruction_cache`

**参考型 vs 任务型分流**（`_execute_skill_async`）：
```python
if skill_info["type"] == "reference":
    return f"<skill_instructions>\n{instructions}\n</skill_instructions>"   # 直接返回文本

# task: 启动 Sub-Crew
crew = build_skill_crew(skill_name, skill_instructions, session_id, sandbox_url)
return str(await crew.akickoff(inputs={task_context, skill_name, ...}))
```

**异步双通道**：`_arun`（FastAPI akickoff 主路径）+ `_run`（ThreadPoolExecutor 同步 fallback）。

**29 课四项扩展**（`skill_loader.py` 总改动 ~130 行）：

#### 扩展 1：参数化 skills_dir + sandbox_skills_mount（P0-1 / P0-6）

22 课 skill_loader 硬编码 `_SKILLS_DIR = parents[2] / "xiaopaw" / "skills"` 和 `_SANDBOX_SKILLS_MOUNT = "/mnt/skills"`。29 课改为构造参数：

```python
class SkillLoaderTool(BaseTool):
    _role: str = PrivateAttr(default="")
    _skills_dir: Path = PrivateAttr()
    _sandbox_skills_mount: str = PrivateAttr(default="/mnt/skills")
    _team_standards: dict = PrivateAttr(default_factory=dict)

    def __init__(
        self,
        role: str,                              # 29 课新增：角色名
        skills_dir: Path,                       # 29 课新增：宿主机 SKILL 目录
        sandbox_skills_mount: str,              # 29 课新增：沙盒侧对应挂载路径
        session_id: str = "",
        sandbox_url: str = "",
        routing_key: str = "",
        history_all: list | None = None,
        team_standards: dict | None = None,     # 29 课新增：集中阈值字典
    ) -> None:
        ...
        self._role = role
        self._skills_dir = skills_dir
        self._sandbox_skills_mount = sandbox_skills_mount
        self._team_standards = team_standards or {}
        self._build_description()
```

main.py 按角色构造：
- Manager：`skills_dir=workspace/manager/skills/`，`sandbox_skills_mount=/workspace/manager/skills`
- PM：`skills_dir=workspace/pm/skills/`，`sandbox_skills_mount=/workspace/pm/skills`
- RD / QA 同理

**22 课公共 skills 的保留**：`feishu_ops` / `baidu_search` / `web_browse` / `history_reader` 等 22 课 MVP skills 继续挂载原路径 `/mnt/skills`。物理位置从 `xiaopaw_team/skills/`（源码仓）挪到 `workspace/shared/legacy_skills/`（工作区共享），所有角色的 manifest 都可以 enable 这些 legacy skill。

#### 扩展 2：4 份 manifest（每角色一份）

从全局单份 `skills/load_skills.yaml` 拆成每角色一份 `workspace/{role}/skills/load_skills.yaml`。manifest 条目新增两字段：

```yaml
skills:
  - name: sop_feature_dev
    type: reference
    enabled: true
    kind: sop                    # 29 课新增：sop | base
    owner_role: manager          # 29 课新增：filter 用
```

`_build_description` 按当前 Agent 角色过滤，跨角色 SKILL 不进工具 XML——PM 的 LLM 看不到 owner_role=manager 的条目。

#### 扩展 3：`{team_standards.X}` 变量替换

`_get_skill_instructions` 在剥离 frontmatter 后、转义 `{}` 前先做一遍替换：

```python
for key, val in self._team_standards.items():
    stripped = stripped.replace(f"{{team_standards.{key}}}", str(val))
```

让 SKILL.md 能写 `coverage >= {team_standards.pytest_coverage_min}` 这类引用。

#### 扩展 4：manifest mtime 热重载（P1-11）

新增方法：

```python
def reload_if_changed(self) -> bool:
    """检测 manifest mtime 变化则重跑 _build_description，
    同时清空 _instruction_cache（防止旧 SKILL 正文残留）。"""
    manifest_path = self._skills_dir / "load_skills.yaml"
    mtime = manifest_path.stat().st_mtime
    if mtime != self._last_manifest_mtime:
        self._skill_registry.clear()
        self._instruction_cache.clear()    # ← 关键：apply_proposal 后必须让下次 load 看到新版 SKILL
        self._build_description()
        self._last_manifest_mtime = mtime
        return True
    return False
```

main.py 的 `_monitor_loop` 协程每 5s 调 `reload_if_changed()`。

### 6.3 Sub-Crew + AIO-Sandbox（22 课 · 本课复用不改）

`build_skill_crew(skill_name, skill_instructions, session_id, sandbox_mcp_url)` 每次返回新实例（防状态污染）。

Sub-Crew Agent 连接 AIO-Sandbox MCP，开放**全部沙盒工具**（22 课移除了 `create_static_tool_filter` 白名单）：
- `sandbox_execute_bash` / `sandbox_execute_code` / `sandbox_file_operations` / `sandbox_str_replace_editor` / `sandbox_convert_to_markdown`
- `browser_*` 系列 20+ 工具（web_browse Skill 用）
- `sandbox_get_context` / `sandbox_get_packages`

工具约束通过 **Agent backstory 行为规则** 在 skill 层面表达，而非 MCP 接口级白名单。这样同一沙盒能支持文件处理、网页浏览、代码执行等多样 Skill。

29 课场景下 Sub-Crew **一次性跑完就退出**——这是 task skill 无法和用户多轮对话的根本原因（详见 §17.1）。

### 6.4 session 安全

22 课原设计（本课原样保留）：
- **session_id 从不进 LLM context**：SkillLoaderTool 用 `_session_id: str = PrivateAttr`，只把**实际路径字符串**注入到工具 description，LLM 无法读取或篡改
- **history_reader 内联处理**：SkillLoaderTool 构造时接 `history_all`，`history_reader` skill 不进沙盒，直接在 Python 里分页返回

### 6.5 AIO-Sandbox（17 课 · 本课扩展为单沙盒多角色）

详见 §14 "沙盒与执行隔离"。

---

## 7. CronService + CleanupService + AIO-Sandbox

### 7.1 CronService（17 课 + 29 课扩展）

17 课核心：
- `asyncio` 精确 timer（不是轮询），tick 间隔 50ms
- `tasks.json` 持久化 + mtime+size 双重检测热重载
- 三种 schedule 类型：
  - `at`：一次性（指定 timestamp_ms，触发后 `enabled=false` 或 `delete_after_run=true`）
  - `every`：固定间隔（`interval_sec` + `jitter_sec`）
  - `cron`：cron 表达式（用 croniter 解析 + 时区）
- 触发时调 `dispatch_fn(InboundMessage)` 进 Runner 管道（fake 消息）

29 课关键用法（**不改 CronService 公开 API**，只用文件级写入）：

CronService 22 课就是"mtime + size 热重载 `data/cron/tasks.json`"的架构——没有 `register_job` 方法。29 课不添加新方法，而是通过 `xiaopaw_team/tools/_tasks_store.py` 的函数级 API 原子写 tasks.json，让 CronService 的下一个 tick 自然捕获：

```python
# xiaopaw_team/tools/_tasks_store.py  (22 课 scheduler_mgr 已有的工具)
def create_job(job_dict: dict, tasks_json_path: Path) -> str:
    """原子写入：读 → 追加 → 写临时文件 → rename。FileLock 保护。"""
    ...
```

29 课两种 wake 都走这个函数：

- **heartbeat cron（P1-12 错峰）**：main.py 启动时对 4 角色**显式错峰首次偏移**（避免首次 tick 同相导致 4 LLM 并发），4 个 role 的 `first_delay_sec` 分别用 `[0, 7, 14, 21]`（间隔 7s 把 4 个 wake 均匀分散在 30s 周期内）；interval_sec=30、jitter_sec=5（每次触发 ±5s 随机偏移）。

  **jitter_sec 语义明文**：每次 tick 触发时在 `[interval_sec - jitter_sec, interval_sec + jitter_sec]` 内均匀随机（不是"首次触发才偏移"），使得 4 个 cron 在长时间运行后仍保持相位错开。
  
  ```python
  for idx, role in enumerate(["manager", "pm", "rd", "qa"]):
      create_job({
          "id": f"heartbeat-{role}",
          "schedule": {
              "kind": "every",
              "interval_sec": 30,
              "jitter_sec": 5,
              "first_delay_sec": idx * 7,  # 错峰：0, 7, 14, 21
          },
          "payload": {"routing_key": f"team:{role}",
                      "text": "[wake] heartbeat",
                      "meta": {"wake_reason": "heartbeat"}},
      }, cfg.cron_tasks_path)
  ```
- **at one-shot wake**：`SendMailTool` 内部：
  ```python
  from xiaopaw_team.tools._tasks_store import create_job
  create_job({
      "id": f"wake-once-{uuid4()}",
      "schedule": {"kind":"at","timestamp_ms":now_ms()+1000,"delete_after_run":True},
      "payload": {"routing_key":f"team:{to}","text":"[wake] 新邮件到达","meta":{"wake_reason":"new_mail"}},
  }, tasks_json_path=cfg.cron_tasks_path)
  ```
  写完后最迟 50ms 内（CronService tick 间隔）+ 1s 延迟触发 Runner 处理。

**wake 去重**：见 §5.3 Runner 的 dispatch 层去重（相同 routing_key 已有 pending wake 则丢弃本次）。

详见 [design-modules.md §6](./design-modules.md#6-cronservice-模块)。**注意子文档未修订：CronService 对 29 课扩展的承载方式是文件级写入而非新 API，子文档的"mtime 热重载"机制保持不变。**

### 7.2 CleanupService（17 课 + 29 课扩展）

17 课核心（双触发）：
- **启动时**：`sweep()` 处理异常退出遗留
- **每日 3:00**（独立协程 `_daily_cleanup_loop`）：同样 sweep

**本课有两套工作区路径并存，不冲突**（P0-5 澄清）：

| 路径 | 用途 | 生命周期 | 挂载点 |
|------|------|---------|-------|
| `data/workspace/sessions/{sid}/uploads,outputs,tmp,traces` | 22 课用户 session 工作区（飞书附件落盘、trace 输出等） | 按类型滚动 | 挂到沙盒 `/data-workspace/sessions/{sid}/`（或 CleanupService 内部管理，不直接暴露给 Skill） |
| `workspace/manager, pm, rd, qa, shared/projects/{pid}/` | 29 课团队工作区（角色 skill 目录 + 共享项目产物 + events.jsonl） | 永久（workspace 是独立 git 仓库） | 挂到沙盒 `/workspace/`（§28.2） |

两套路径在**沙盒内分别挂载**，sessions 仓专门服务 22 课 session 概念、workspace 仓专门服务 29 课团队协作——互不覆盖。

**清理策略**（22 课原样保留，作用于 `data/workspace/sessions/` 而非新 `workspace/` 根）：
- `tmp/` → 1 天；`uploads/` → 7 天；`outputs/` → 30 天；`traces/` → 30 天；`sessions/*.jsonl` → 365 天

**29 课工作区的清理策略**（新增作用于 `workspace/shared/projects/`）：
- `shared/projects/{pid}/` 项目归档后 90 天清理（events.jsonl 最后 action="archived"）
- `shared/logs/l1_human/` **永久保留**

启动时 CleanupService 还负责：
- 凭证写入：`write_feishu_credentials()` + `write_baidu_credentials()` → `/data-workspace/.config/*.json`（credentials 不进 LLM）
- `ensure_workspace_dirs()`：创建必需目录（data/ 和 workspace/ 各一次）
- **29 课 workspace git 状态检查（v1.4 从"禁用 ApplyProposalTool"软化为"提示 commit 可选"）**：v1.4 取消了 ApplyProposalTool，进化 apply 由提案角色自己执行；workspace 是否 git 仓库**不影响主流程**，只影响"改动后是否自动 commit 留审计轨迹"：
  - CleanupService 启动时 `check_workspace_git_ready(cfg.workspace.root) -> bool`
  - 返回 True → `cfg.features.retro_auto_commit = True`：各角色 agent.md 里"收到 retro_approved 后"流程末尾会尝试 `git commit`
  - 返回 False → `cfg.features.retro_auto_commit = False` + `log.warning("workspace 非 git 仓库，复盘进化改动不会自动 commit（仍然会写文件）。如需审计轨迹，参考 README §28.3 初始化")`
  - 进程正常继续，`retro_approved / retro_applied` 链路不受影响
- **29 课新增团队工作区初始化**：启动时 mkdir `workspace/shared/projects/` / `workspace/shared/logs/l1_human/`，若不存在则创建

### 7.3 AIO-Sandbox（17 课 + 29 课挂载扩展）

- 基于 `ghcr.io/agent-infra/sandbox:latest` 镜像
- 通过 MCP 协议暴露沙盒能力
- **挂载方式（29 课修订）**：
  - `./workspace:/workspace:rw` — 29 课团队工作区，角色 SKILL 在 `/workspace/{role}/skills/`，共享项目产物在 `/workspace/shared/projects/{pid}/`，22 课公共 skill 挪到 `/workspace/shared/legacy_skills/` 继续用
  - `./data/workspace:/data-workspace:rw` — 22 课 session 工作区（session/uploads, outputs, tmp, traces 和 `.config/feishu.json`）
  - 原 22 课挂载 `./xiaopaw_team/skills:/mnt/skills:ro` **取消**，公共 skill 全部挪到 `workspace/shared/legacy_skills/`
- credentials 文件 `/data-workspace/.config/feishu.json` 由 CleanupService 启动时写入，Skill 脚本直接读文件使用

**角色 SKILL 路径矩阵**：

| 角色 | 宿主机 skills_dir | 沙盒侧 sandbox_skills_mount |
|------|------------------|------------------------------|
| Manager | `workspace/manager/skills/` | `/workspace/manager/skills` |
| PM | `workspace/pm/skills/` | `/workspace/pm/skills` |
| RD | `workspace/rd/skills/` | `/workspace/rd/skills` |
| QA | `workspace/qa/skills/` | `/workspace/qa/skills` |
| 全员共享（legacy） | `workspace/shared/legacy_skills/` | `/workspace/shared/legacy_skills` |

本课**单沙盒 + 目录隔离**策略详见 §14。

---

## 8. 记忆层：Bootstrap / ctx.json / pgvector

### 8.1 三层记忆架构（22 课原样）

| 层级 | 实现 | 解决的问题 |
|------|------|-----------|
| **L19 上下文层** | `MemoryAwareCrew @CrewBase` + `@before_llm_call` hook | 每次 LLM 调用前：首次恢复 ctx.json 历史；每次 prune 旧 tool results；每次 context > 45% 则 compress |
| **L20 文件层** | 4 个 workspace 文件（soul/user/agent/memory.md）+ 4 个记忆 Skills（memory-save / skill-creator / memory-governance / search_memory 写） | 结构化积累"语义记忆 + 程序记忆"，Bootstrap 注入 Agent backstory |
| **L21 搜索层** | pgvector `memories` 表（dim=1024）+ async_index_turn | 每轮对话异步提取摘要 + 向量化 + BM25+vector 混合检索 |

详见 [design-modules.md §10-12](./design-modules.md)。

### 8.2 Bootstrap（22 课 + 29 课第 5 文件扩展）

`xiaopaw_team/memory/bootstrap.py` 的 `build_bootstrap_prompt(workspace_dir)`：

**22 课原逻辑**：读 4 个文件，拼成 XML backstory：

```python
<soul>     ← 读 workspace/{role}/soul.md（决策偏好 + NEVER 清单）
<user_profile>  ← 读 user.md（服务对象画像）
<agent_rules>   ← 读 agent.md（Role Charter + 团队名册）
<memory_index>  ← 读 memory.md（历史积累，截至 200 行防膨胀）
```

**29 课扩展**：新增**可选第 5 文件** `shared/team_protocol.md`，存在则注入：

```python
<soul> → <user_profile> → <agent_rules> → <team_protocol> → <memory_index>
```

位置选择在 `agent_rules` 之后、`memory_index` 之前，因为其性质更接近 agent.md（跨角色通用约定）。

`build_bootstrap_prompt` 新增参数 `shared_protocol: Path | None = None`，main.py 启动时统一传入。

### 8.3 ctx.json / raw.jsonl 双存储（22 课原样，P1-13 路径统一）

两个文件都在 `data/ctx_dir/` 下，文件名用 `{session_id}` 前缀，**全项目唯一**：

- `ctx.json`：每轮覆盖写的压缩快照，用于跨 session 恢复（路径 `data/ctx_dir/{session_id}_ctx.json`）
- `raw.jsonl`：append-only 完整审计日志（路径 `data/ctx_dir/{session_id}_raw.jsonl`）——这也是 **L3 日志**（见 §25）

通过 `@before_llm_call` hook 自动维护。详见 `memory/context_mgmt.py`。

**统一说明（v1.3-P1-13）**：v1.2 曾在 §25 出现另一种路径 `{role}/sessions/{sid}_raw.jsonl`，那是历史描述残留。v1.3 统一：L3 raw.jsonl **只在 `data/ctx_dir/` 下**，`team:{role}` 的固定 session_id（如 `team-pm-xiaopaw-team-001`）已 encode 了角色，不另起目录结构。

### 8.3.1 每角色 session_id 生命周期（P1-9 新增）

29 课有两套 routing_key 共存，对应两套 session_id 策略：

| routing_key | session_id 分配策略 | 生命周期 |
|-------------|---------------------|---------|
| `p2p:{open_id}` / `group:{chat_id}` / `thread:...` | 22 课原逻辑：SessionManager 维护 `sessions/index.json`，每个 routing_key 对应 active_session_id；`/new` slash 触发新 session | 用户在飞书发 `/new` 前持续复用 |
| `team:{role}` | **固定 session_id = `team-{role}-{workspace_id}`**（从 config.workspace.id 拼接），四个角色各一个、永久固定 | 永久（跨 wake 持续） |

**为什么 team session 要固定**：
- 每次 wake 都是 MemoryAwareCrew 新实例，`@before_llm_call` hook 的首次 `_session_loaded=False` 会从 ctx.json 恢复上一次处理到的上下文
- 如果每次 wake 换新 session_id，ctx.json 每次都是空的 → 角色永远在"冷启动"状态，跨 wake 记不住自己刚做过什么
- 固定 session_id 让 PM/RD/QA 在同一项目内的多次 wake 能复用压缩后的历史（pgvector 另做跨项目语义检索）

**SessionRouter 扩展**（runner.py 小改）：
```python
def resolve_session_id(routing_key: str, workspace_id: str, session_mgr) -> str:
    if routing_key.startswith("team:"):
        role = routing_key.split(":", 1)[1]
        return f"team-{role}-{workspace_id}"   # 固定
    return session_mgr.get_active_session_id(routing_key)   # 22 课原逻辑
```

**ctx.json 文件分布**：
- `ctx_dir/team-manager-xiaopaw-team-001_ctx.json`
- `ctx_dir/team-pm-xiaopaw-team-001_ctx.json`
- `ctx_dir/team-rd-xiaopaw-team-001_ctx.json`
- `ctx_dir/team-qa-xiaopaw-team-001_ctx.json`
- `ctx_dir/{user_session_id}_ctx.json`（每用户对话 session）

**已知限制**：async_index_turn 是 asyncio.create_task 异步触发，上一轮写 pgvector 到下一轮查询可能 <3s 未就绪（见附录 E）。

### 8.4 pgvector（22 课 + 29 课 metadata 扩展）

22 课 `memories` 表 schema：
```sql
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    routing_key TEXT,
    turn_ts TIMESTAMPTZ,
    summary TEXT,
    tags TEXT[],
    summary_vec vector(1024),
    message_vec vector(1024)
);
```

29 课扩展（见 §30.4）：
```sql
ALTER TABLE memories ADD COLUMN role VARCHAR(16);        -- manager / pm / rd / qa
ALTER TABLE memories ADD COLUMN project_id VARCHAR(64);  -- 关联到哪个项目
CREATE INDEX idx_memories_role_project ON memories(role, project_id);
```

`async_index_turn` 签名同步扩展：
```python
async def async_index_turn(session_id, role, project_id, routing_key, ...)
```

Manager 可以跨项目检索：`WHERE role='manager' AND project_id IN (...)`；也可以做团队级分析：`WHERE role IN ('pm','rd','qa')`。

---

# 三、团队协作层（29 课新增）

## 9. 核心设计原则

### 9.1 单一接口原则（27 课硬约束）

**人永远只和 Manager 沟通**。三重架构保证：
- 飞书入站：FeishuListener 把消息路由给 Manager agent_fn
- 飞书出站：`SendToHumanTool` 只注入 Manager 的 Crew 构造器
- PM/RD/QA 的 Crew 构造器**不接受** `feishu_sender` 参数——Python 对象层面传不进去

任何"团队内角色想跟用户说话"的场景，只能发邮件给 Manager，由 Manager 翻译成飞书卡片。

### 9.2 零 Python 编排原则

**流程推进逻辑 100% 写在 SKILL.md 里，Python 代码不做业务流程决策**。代码只做 5 件事：
1. **启动**：main.py 构造 4 个 MemoryAwareCrew
2. **路由**：Runner 根据 InboundMessage.routing_key 分派 agent_fn
3. **工具**：Python 函数作为 CrewAI Tool 暴露
4. **沙盒**：调用 AIO-Sandbox 执行 task 型 Skill 脚本
5. **唤醒**：CronService 把时间/事件转成 InboundMessage

**严禁的反模式**：
- ❌ `if stage == "product_design" then next = "product_design_review"`
- ❌ `if reviewer_count == 2 then advance()`
- ❌ 预定义的 stages 列表
- ❌ `if skill_name.startswith("sop_"):`（靠命名约定识别 skill 类型）

### 9.3 Agent = Crew + SkillLoaderTool + 四层框架（25 课）

每个角色：1 个 `MemoryAwareCrew @CrewBase` + 1 个 `SkillLoaderTool` + 若干协作工具。backstory 由 `build_bootstrap_prompt(workspace/{role}/)` 从四层文件 + team_protocol.md 拼接。

### 9.4 状态共享 vs 任务触发（26 课）

- **共享工作区**（文件持久化状态）：需求、设计、代码、测试报告
- **文件邮箱**（JSON 结构化事件）：task_assign / task_done / review_done
- 邮件只传路径引用，**绝不**复制文档正文

### 9.5 SOP 驱动 + 事件流推断 state（v1.1 关键）

**没有**预定义 stages 列表。项目状态真相来自两处：
- **append-only 事件流** `shared/projects/{pid}/events.jsonl`
- **文件系统痕迹**（produce/design/code/reviews/qa/ 下有哪些文件）

Manager 每次 kickoff 第一步调 `load_skill("read_project_state")`，脚本 tail events.jsonl 尾部 + ls 关键目录 + 交叉校验 → 返回状态摘要。由 LLM 根据 sop_feature_dev SKILL 决定下一步，**不是 Python 决定**。

### 9.6 进化闭环（28 课）

一次项目跑完触发一次复盘。提案严格分档 HITL。本课只演示到"列出提案 + apply 到 workspace 文件 + git commit"。

### 9.7 不自建调度，复用 CronService

每角色注册 1 个 `every 30s + jitter 5s` heartbeat；发邮件由 `SendMailTool` 注册 `at=now+1s` one-shot；三类触发源（飞书、邮件唤醒、cron 兜底）对 Agent LLM 统一是"醒来"。

---

## 10. 四角色与四层框架

四角色全部使用 25 课的四层框架（soul + agent + memory + user）。

### 10.1 角色清单

| 角色 | role | 决策偏好 | NEVER 清单 | 负责 | 不负责 |
|------|------|---------|-----------|------|--------|
| Manager | 项目经理 | 全局视野 / 可审计 / 不越级 / 甲方视角 | 不写代码 / 不改需求 / 不跳过任务拆解 / 不让执行层联系用户 | 需求澄清、任务分配、验收、checkpoint 转发、复盘、apply_proposal | 产品设计、代码、测试 |
| PM | 产品经理 | 用户价值优先 / 文档清晰度 / 决策可追溯 | 不写代码 / 不跳过验收标准 / 不联系用户 | 产品设计文档、验收标准定义 | 代码、测试、进度管理 |
| RD | 研发工程师 | 技术实现优雅 / 测试优先 / 可维护性 | 不修改需求 / 不跳过单元测试 / 不提交未 PASS 的代码 | 后端 API + 前端页面 + 单元测试 | 产品设计、集成测试 |
| QA | 质量工程师 | 风险覆盖 / 边界 case / 缺陷可复现 | 不放过失败测试 / 不改代码 / 不接受无验收标准的任务 | 集成测试用例、测试执行、缺陷报告 | 代码实现 |

### 10.2 四层文件的差异化与共性（P2-16 细化与 25 课对齐）

25 课原教义：**soul=决策偏好 + NEVER；agent=Role Charter + 团队名册**。本课严格遵循：

| 层 | 内容 | 本课处理 |
|---|---|---|
| `soul.md` | 决策偏好 + NEVER 清单 | 角色差异化（各不相同） |
| `agent.md` | Role Charter（我负责/我不负责）+ 团队名册（有哪些同事）| **只写身份与分工**，**不写**流程指令（如"收到 task 先 load 哪个 skill"），**不写**决策偏好（那是 soul.md 的职责） |
| `memory.md` | 跨 session 积累（≤200 行，Bootstrap 自动截断） | 角色差异化 |
| `user.md` | 服务对象画像 | **Manager=晓寒本人（动态，memory-save 可更新）；PM/RD/QA=Manager 这个"内部甲方"（静态模板，不接受 memory-save 写入）** |
| `shared/team_protocol.md` | 跨角色通用协作约定（kickoff 两步法 / wake_reason / 邮件约束 / mark_done 顺序） | 全员共享，Bootstrap 自动注入 |

### 10.3 team_protocol.md 示例内容

```markdown
# 团队协作通用约定

## kickoff 两步法
每次你被唤醒（飞书、邮件、heartbeat），第一步都是同样两件事：
1. 读 inbox：ReadInboxTool 看有没有 unread 邮件
2. 如你是 Manager：再 load_skill("read_project_state") 推断当前项目在哪个阶段

不要跳过这两步。所有后续动作都基于它们的输出。

## wake_reason 处理规则
消息 meta.wake_reason ∈ {feishu, new_mail, heartbeat}
- feishu: 用户说了什么，按 SOP / 意图处理
- new_mail: 有邮件要处理
- heartbeat + inbox 空: 可直接回复 "no_op"，不调用其他工具（省 token）

## 邮件发送约束
- 消息 type 必须是标准枚举（见附录 B）
- content 只写路径引用，不复制文档全文
- 发完调 mark_done 标记自己上一条 task_assign 已完成
- mark_done 顺序：如果同时要 append_event，必须先 append_event 再 mark_done
  （反过来会造成崩溃半写，下次 read_project_state 无法自愈）

## 任务结束前必做：self_score 自评（v1.4-13）
在即将发送 send_mail(type=task_done) 之前，**无条件**调 load_skill("self_score") →
按其 5 维框架打分 → 把 `{self_score, breakdown, rationale}` 作为 task_done content 的字段之一一并发出。
（task_callback 会从你的产出里解析 self_score 写入 L2 日志）

## 收到 retro_approved 邮件后（v1.4，对齐 28 课）
对邮件 content 里的每条 improvement_proposal 机械执行：
1. 读 target_file 当前内容
2. 在文件里**精确匹配** before_text 锚点
3. 找到 → 替换为 after_text → 写回；找不到 → 发 retro_apply_failed 给 Manager
4. （可选）workspace 若为 git 仓库，本地 git commit 留审计轨迹
5. 发 retro_applied 确认邮件给 Manager

**这一步不需要 LLM 决策**——纯文本替换，越机械越好。
```

### 10.4 agent.md 示例（PM）

```markdown
# PM Role Charter

## 我负责
产品设计文档、验收标准定义

## 我不负责
代码、集成测试、进度管理（Manager）、直接联系用户（单一接口原则）

## 团队名册
- Manager（上级甲方）：我的所有产出 task_done 给他
- RD：我的产品设计要让他能技术落地
- QA：我的验收标准要让他能机械验证
```

对应的 PM `soul.md` 示例（决策偏好 + NEVER 在这里）：

```markdown
# PM Soul

## 决策偏好（遇到开放选择时倾向）
- 用户价值 > 技术方便度
- 验收标准要可机械检查（能写 assert 的才写）
- 模糊边界宁愿列"明确不做"也不留给 RD 猜

## NEVER
- 绝不亲自写代码
- 绝不跳过验收标准
- 绝不联系用户（单一接口原则，只能给 Manager 发邮件）
```

**关键**：agent.md **只写身份与分工**，**不写**决策偏好（那是 soul.md），**不写**路由表（那由 SkillLoader description 驱动）。这样 25 课的"soul / agent / memory / user"四层职责清晰不重叠。

---

## 11. 协作机制：邮箱 + 共享区 + 事件流

### 11.1 共享工作区

```
/workspace/shared/projects/{project_id}/
├── needs/requirements.md       ← Manager 写，全员读
├── design/product_spec.md      ← PM 写，Manager/RD/QA 读
├── tech/tech_design.md         ← RD 写
├── code/                       ← RD 写（沙盒内）
├── qa/                         ← QA 写（test_plan、test_report、defects/）
├── reviews/{stage}/{reviewer}_{topic}.md  ← 任意角色写自己的评审
├── mailboxes/{manager,pm,rd,qa}.json     ← 团队内邮箱
├── events.jsonl                ← append-only 事件流（仅 Manager 写）
└── logs/l2_task/*.jsonl        ← L2 任务级日志

/workspace/shared/proposals/              ← v1.4 新增：复盘产出
├── pm_retro_2026-04-20.json
├── rd_retro_2026-04-20.json
└── qa_retro_2026-04-20.json
```

### 11.2 权限边界（工具层强制，P2-20 修贪婪匹配）

`tools/workspace.py` 内 `OWNER_BY_PREFIX`：

```python
ROLE_WHITELIST = {"manager", "pm", "rd", "qa"}

OWNER_BY_PREFIX = {
    "needs/":   {"manager"},
    "design/":  {"pm"},
    "tech/":    {"rd"},
    "code/":    {"rd"},
    "qa/":      {"qa"},
}

# P2-20：显式角色白名单 + 强制 topic 后缀，避免 [a-z]+ 贪婪匹配
REVIEWS_PATTERN = re.compile(
    r"^reviews/([a-z_]+)/(manager|pm|rd|qa)_([a-z0-9_]+)\.md$"
)

def check_write(role: str, rel_path: str):
    if rel_path.startswith("reviews/"):
        m = REVIEWS_PATTERN.match(rel_path)
        if not m:
            raise PermissionError(
                f"reviews 文件名必须匹配 reviews/{{stage}}/{{reviewer}}_{{topic}}.md"
                f"，{{reviewer}} 必须是 manager|pm|rd|qa，{{topic}} 必填小写字母/数字/下划线"
            )
        stage, reviewer, topic = m.groups()
        if reviewer != role:
            raise PermissionError(f"{role} 不能以 reviewer={reviewer} 身份写评审文件")
        return
    owners = OWNER_BY_PREFIX.get(prefix_of(rel_path))
    if not owners or role not in owners:
        raise PermissionError(f"{role} cannot write {rel_path}")
```

### 11.2.1 权限测试矩阵（P2-16）

覆盖写操作的完整矩阵：

| rel_path 示例 | manager | pm | rd | qa |
|---------------|---------|----|----|----|
| `needs/requirements.md` | ✅ | ❌ | ❌ | ❌ |
| `design/product_spec.md` | ❌ | ✅ | ❌ | ❌ |
| `tech/tech_design.md` | ❌ | ❌ | ✅ | ❌ |
| `code/backend/main.py` | ❌ | ❌ | ✅ | ❌ |
| `qa/test_plan.md` | ❌ | ❌ | ❌ | ✅ |
| `qa/defects/bug_1.md` | ❌ | ❌ | ❌ | ✅ |
| `reviews/product_design/rd_review.md` | ❌ | ❌ | ✅ | ❌ |
| `reviews/product_design/qa_acceptance_check.md` | ❌ | ❌ | ❌ | ✅ |
| `reviews/product_design/manager.md`（缺 topic） | ❌ | ❌ | ❌ | ❌ |
| `reviews/code/pm_review.md` | ❌ | ❌ | ❌ | ❌ |
| `reviews/product_design/pm_qa_review.md`（reviewer=pm，但名字误含 qa）| ❌ | ✅ | ❌ | ❌ |
| `mailboxes/pm.json` | 🚫（只能经 SendMailTool）| 🚫 | 🚫 | 🚫 |
| `events.jsonl` | 🚫（只能经 AppendEventTool）| 🚫 | 🚫 | 🚫 |

**测试点溯源**：此矩阵对应 test-design.md T-PERM-01 ~ T-PERM-13。每行至少有 1 ✅ + 3 ❌ 可测。

### 11.3 文件邮箱（26 课原样 + project_id 字段）

邮箱位置：`shared/projects/{pid}/mailboxes/{role}.json`

消息 schema：
```json
{
  "id": "msg-...",
  "project_id": "proj-pawdiary-0001",
  "from": "manager",
  "to": "pm",
  "type": "task_assign",
  "subject": "产品设计",
  "content": "...（只写路径引用）",
  "timestamp": "2026-04-20T02:00:00+00:00",
  "status": "unread",
  "processing_since": null
}
```

**字段精确定义（P0-6 时区 + P2-17 required/optional）**：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | str | ✅ | 格式 `^msg-[0-9a-f]{8}$`（uuid4 前 8 位 hex） |
| `project_id` | str | ✅ | 格式 `^proj-[a-z][a-z0-9_-]{2,40}$`（LLM 生成时约束） |
| `from` | str | ✅ | `manager|pm|rd|qa|human|feishu_bridge` 枚举 |
| `to` | str | ✅ | `manager|pm|rd|qa` 枚举（team 内部） |
| `type` | str | ✅ | 见附录 B 10 种枚举 |
| `subject` | str | ✅ | 非空；revision 场景含 `(第 N 轮)` 格式（§13.2 硬约束）|
| `content` | str\|dict | ✅ | 路径引用字符串；checkpoint_response 时为 dict |
| `timestamp` | str | ✅ | **ISO 8601 UTC**，`+00:00` 后缀，**不**允许 naive 时间或 `+08:00` |
| `status` | str | ✅ | `unread`\|`in_progress`\|`done` 三态 |
| `processing_since` | str\|null | ⚠️ optional | 进入 in_progress 时的 UTC timestamp，未来 reset_stale 用；本课可留 null |

**FileLock 保护**：
- `send_mail`：锁内 `读 → 追加 → 写`
- `read_inbox`：锁内 `读 → 过滤 unread → 标 in_progress → 写`，返回快照
- `mark_done`：锁内 `in_progress → done`
- `reset_stale`：定期把超时 in_progress 恢复 unread（本课单进程不启用）

type 枚举见附录 B。

### 11.4.1 崩溃恢复自愈（§阶段 6 / 附录 A 引用，P2-18 修死链）

**半写场景**：
1. JSON Lines 半写（events.jsonl 最后一行不完整）：`read_project_state` 脚本按行 `json.loads` try-except，遇到非法行 skip + log WARNING，并在摘要顶部加一条 "⚠️ 跳过 N 条非法行"
2. mailbox 已 done 但 events.jsonl 缺 checkpoint_approved：`read_project_state` 交叉校验后 **自动 append `recovered_checkpoint_response` event**（payload 含 `recovered_from: mailbox`），后续流程无感
3. Manager kickoff 中途崩溃（事件写了但 mailbox 没 mark_done）：下次 wake 再次 read_inbox 会**重复处理**——这需要 handle_checkpoint_reply 做幂等：如果 events.jsonl 已经有对应 ck_id 的 checkpoint_approved，直接 mark_done 不重复处理

告警路径：**所有自愈/异常都走 `logger.warning(...)` + 必要时 append `error_alert_raised` event**，不主动发 send_to_human（避免对用户噪音），但在下一次 send_to_human(evolution_report / delivery) 的 summary 里提一句"本次项目发生 N 次自愈"。

### 11.4 事件流 events.jsonl（v1.1 关键设计）

**append-only JSON Lines**，每行一个事件。仅 Manager 有权写（`AppendEventTool` 注入给 Manager only）。

**写入规则**：
- FileLock 保护 append（防 agent_fn 并发写）
- 每条事件至少含 `ts / seq / actor / action / payload`
- 崩溃时 JSON Lines 最后一行可能部分写入 → read_project_state 跳过非法行并告警

**读取规则**：
- `read_project_state` 脚本 tail 最后 N 条（默认 `team_standards.event_tail_window=100`）
- 加 ls 目录做文件系统盘点
- 自愈检查：对每条 status=done 的 checkpoint_response 邮件查 events.jsonl 是否有对应 approved/rejected，缺失则补齐 "recovered_checkpoint_response" 事件

**优点**：无 schema 硬编码（stages 列表随 SOP 事件自然生长）、演化友好（新 SOP 只需新 action type 不改代码）、审计完整（append-only 不丢历史）。迭代历史（为什么不用 state.json）见附录 F。

完整结构见附录 A。

### 11.5 read_project_state 脚本输出

脚本只负责"事件流摘要 + 文件系统盘点"，**不做 stage 映射**——stage 语义由 Manager LLM 对照 sop_feature_dev SKILL 推断。

示例输出：
```
## 事件流摘要（最后 100 条）
project_id: proj-pawdiary-0001
sop: sop_feature_dev
事件统计:
  - project_created: 1
  - assigned: 1 (to=pm)
  - task_done_received: 1 (from=pm)
  - review_requested: 1 (reviewers=[rd, qa])
  - review_received: 2 (rd=pass, qa=need_changes)
  - revision_requested: 1 (to=pm, round=2)

最后 5 条动作（倒序）:
  2026-04-20 11:05:30  revision_requested  to=pm round=2
  ...

## 自愈检查
- mailbox 有 done 状态的 checkpoint_response(ck-001) ✅ 对应事件存在
- 无待补齐事件

## 已有产物
- needs/requirements.md
- design/product_spec.md (v2)
- reviews/product_design/rd_review.md
- reviews/product_design/qa_review.md

## 挂起 checkpoint
- 无

## 进行中的评审
- stage=product_design; reviewers_received=[rd, qa]; one is need_changes → 需要回 PM 修
```

---

## 12. 飞书桥与单一接口

### 12.1 入站：feishu_bridge.recv_human_response

```python
def recv_human_response(feishu_msg, routing_key):
    # 1. 检查最近 events.jsonl 有无 pending checkpoint
    pending_ck = find_pending_checkpoint_from_events(routing_key)
    if pending_ck:
        # 作为 checkpoint_response 写 manager.json
        send_mail(to="manager", from_="human",
                  type_="checkpoint_response",
                  project_id=pending_ck["project_id"],
                  content={"ck_id": pending_ck["id"],
                           "text": feishu_msg.text,
                           "decision": classify(feishu_msg.text)})
        # SendMail 内部已 at cron 唤醒 Manager
        return "consumed_as_checkpoint"
    # 常规飞书对话：Runner 按 p2p:{open_id} 路由到 Manager agent_fn
    # Runner.dispatch 自身已经会把消息投进 per-routing_key 队列并触发 worker，
    # 所以 p2p 路径不需要额外 wake cron（Runner 自带消费机制）
    return None
```

### 12.1.1 classify() 实现（P0-4 补齐）

用户对 checkpoint 的回复可能来自两种渠道：

**方式 A：飞书交互式卡片按钮**
```python
# 飞书卡片 send_card(type="checkpoint_request") 时带 Approve/Reject 按钮
# 按钮定义：
{"tag": "button", "text": {"tag":"plain_text","content":"Approve"}, 
 "value": {"kind":"checkpoint_response", "ck_id":"ck-001", "decision":"approved"}}
# 按钮定义（reject）同理 decision="rejected"
# 用户点按钮后，飞书推送事件里 event.action.value 即为上述 value dict
```

**方式 B：纯文本回复**
- 用户直接在对话框回复"确认 / 同意 / approve / ok" → decision="approved"
- 回复"拒绝 / 否 / reject / no / 不行" → decision="rejected"
- 其他 → decision="need_discussion"（由 Manager LLM 的 handle_checkpoint_reply skill 兜底处理）

**classify 完整逻辑（v1.3-P1-11 改词边界匹配，P0-3 加 proposals 分支）**：

```python
# 严格白名单集合（完全匹配 / 词边界，不做 `in` 子串判断）
APPROVED_TOKENS = {
    "approve", "approved", "同意", "确认", "ok", "可以", "好的",
    "yes", "y", "嗯", "是的", "继续", "没问题"
}
REJECTED_TOKENS = {
    "reject", "rejected", "拒绝", "否", "不行", "no", "n",
    "不同意", "有问题", "回去", "不可以"
}

def classify(feishu_msg) -> dict:
    """返回 {decision: str, approved_ids: list[str]|None, raw_text: str}
    
    decision ∈ {"approved", "rejected", "need_discussion", "proposals_partial"}
    approved_ids 仅 proposals 按钮场景下有值
    """
    # 1. 卡片按钮 callback 优先（结构化、零歧义）
    if hasattr(feishu_msg, "action") and isinstance(feishu_msg.action.value, dict):
        v = feishu_msg.action.value
        kind = v.get("kind")
        # 1a. 常规 checkpoint
        if kind == "checkpoint_response":
            return {"decision": v["decision"], "approved_ids": None, "raw_text": ""}
        # 1b. 多选提案（见附录 C2 卡片按钮结构约定）
        if kind == "proposals_approve":
            approved = v.get("approved_ids", [])
            rejected = v.get("rejected_ids", [])
            if approved and not rejected:
                return {"decision": "approved", "approved_ids": approved, "raw_text": ""}
            if rejected and not approved:
                return {"decision": "rejected", "approved_ids": [], "raw_text": ""}
            return {"decision": "proposals_partial", "approved_ids": approved, "raw_text": ""}
    
    # 2. 纯文本：完全匹配 + 分词白名单（不用 `in` 子串匹配，避免"不确认"误判 approved）
    text = (feishu_msg.text or "").strip().lower()
    # 2a. 整句完全匹配
    if text in APPROVED_TOKENS:
        return {"decision": "approved", "approved_ids": None, "raw_text": text}
    if text in REJECTED_TOKENS:
        return {"decision": "rejected", "approved_ids": None, "raw_text": text}
    # 2b. 词边界匹配（用正则 \b 或中文标点分词）
    tokens = set(re.split(r"[\s，。！？、,.!?]+", text))
    if tokens & APPROVED_TOKENS and not (tokens & REJECTED_TOKENS):
        return {"decision": "approved", "approved_ids": None, "raw_text": text}
    if tokens & REJECTED_TOKENS and not (tokens & APPROVED_TOKENS):
        return {"decision": "rejected", "approved_ids": None, "raw_text": text}
    
    # 3. 兜底
    return {"decision": "need_discussion", "approved_ids": None, "raw_text": text}
```

**关键设计决策**：
- **词边界匹配**：用正则 `\b` 或分词后 set 交集，绝不用朴素 `in` 子串——避免"我不确认"被当成 approved（"确认"是"不确认"的子串）
- **双 token 冲突 → need_discussion**：同时出现"同意"和"否"的句子降级到人工解释
- **返回 dict**：之前版本返回 str，v1.3 改成 dict 让 `approved_ids` 透传到 recv_human_response 写 `manager.json`

`decision="need_discussion"` 或 `"proposals_partial"` 时，Manager LLM 加载 `handle_checkpoint_reply` skill 读原文 + 上下文，自主决定处理方式。两种 decision 都会触发新 event `checkpoint_reply_classified`（见附录 A）。

### 12.2 出站：SendToHumanTool

```python
def send_to_human(project_id, type_, title, summary, artifacts=None, proposals=None):
    """
    proposals 仅 type_="proposals_review" 时使用，格式 list[{id: str, title: str, root_cause: str}]
    """
    # 1. 追加 events.jsonl: action=f"{type_}_sent"
    event_id = append_event(project_id, action=f"{type_}_sent", payload={
        "title": title, "artifacts": artifacts or [], "proposals": proposals or []
    })
    # 2. 飞书卡片（见下 12.2.1 按钮结构）
    card = build_card(type_, title, summary, artifacts, proposals)
    msg_id = feishu_sender.send_card(user_open_id, card)
    # 3. L1 日志（schema 见附录 H）
    log_l1(action=f"{type_}_sent", project_id=project_id, role="manager", 
           user_text=None, summary=summary, artifacts=artifacts or [])
    return event_id
```

卡片 type 枚举：`info` / `checkpoint_request` / `proposals_review` / `delivery` / `evolution_report` / `error_alert`

### 12.2.1 proposals_review 卡片按钮结构（P0-3 补齐）

`proposals_review` 是**本课唯一允许多选的 checkpoint**。卡片布局：

```
┌────────────────────────────────────────┐
│ 🔧 本次项目产生 3 条改进提案            │
│ ────────────────────────────────────── │
│ ☐ [提案 p001] PM 加日期时区规则         │
│ ☐ [提案 p002] RD 加前端 viewport       │
│ ☐ [提案 p003] QA 加并发 case 默认       │
│ ────────────────────────────────────── │
│ [全部 Approve]  [全部 Reject]  [提交]   │
└────────────────────────────────────────┘
```

**按钮 value 约定**（`action.value` 字段）：

| 按钮 | value 结构 |
|------|-----------|
| 提案复选框（切换状态，不立即提交） | `{"kind": "proposal_toggle", "proposal_id": "p001", "checked": true}` |
| 全部 Approve | `{"kind": "proposals_approve", "approved_ids": ["p001","p002","p003"], "rejected_ids": []}` |
| 全部 Reject | `{"kind": "proposals_approve", "approved_ids": [], "rejected_ids": ["p001","p002","p003"]}` |
| 提交（用户自选状态后点） | `{"kind": "proposals_approve", "approved_ids": [...已勾选的...], "rejected_ids": [...未勾选的...]}` |

飞书卡片状态跟踪由飞书平台自身提供（checkbox 状态前后保留），提交按钮触发时把最终状态打包进 `approved_ids` / `rejected_ids`。

**feishu_bridge.recv_human_response** 收到 `kind=proposals_approve` 后：
```python
# 写 manager.json 的 checkpoint_response
send_mail(to="manager", from_="human",
          type_="checkpoint_response",
          project_id=pending_ck["project_id"],
          content={"ck_id": pending_ck["id"],
                   "type": "proposals_approve",    # 区分常规 checkpoint
                   "approved_ids": v["approved_ids"],
                   "rejected_ids": v["rejected_ids"]})
```

Manager LLM 读到 checkpoint_response 后按 `content["approved_ids"]` 逐条调 `ApplyProposalTool(proposal_id)`（见 §阶段 6.5）。

### 12.3 单一接口的架构保证

`build_role_tools(role, cfg)` 只给 `role == "manager"` 注入 `feishu_sender`。其他角色的 SkillLoaderTool 里没注册 `send_to_human`，LLM 调用会报 "Tool not found"。架构级保证。

---

## 13. 唤醒机制

### 13.1 三条唤醒路径

| 来源 | 触发方式 | 目的 |
|------|---------|------|
| 飞书用户消息 | FeishuListener → Runner (`p2p:{open_id}`) | 用户发起新任务或回复 checkpoint |
| SendMailTool 内部 | 注册 `at=now+1s` one-shot cron | 即时唤醒收件人（主路径） |
| 每角色 every 30s+jitter | CronService heartbeat | 兜底：异常后恢复、手工干预后补偿 |

### 13.2 InboundMessage.meta 扩展

```python
@dataclass
class InboundMessage:
    routing_key: str
    text: str
    meta: dict    # v1.1 新增 wake_reason
    # wake_reason ∈ {"feishu", "new_mail", "heartbeat"}
```

### 13.3 cron wake 去重

Runner.dispatch 对 `routing_key=team:{role}` 且 `meta.wake_reason ∈ {new_mail, heartbeat}` 的消息做入队去重：

```python
async def dispatch(self, inbound):
    if inbound.routing_key.startswith("team:") and inbound.meta.get("wake_reason") in {"new_mail", "heartbeat"}:
        queue = self._queues.get(inbound.routing_key)
        if queue:
            for pending in list(queue._queue):
                if pending.meta.get("wake_reason") in {"new_mail", "heartbeat"}:
                    return   # 丢弃本次
    await self._enqueue(inbound)
```

### 13.4 SendMailTool 联动

SendMailTool 内部使用 `_tasks_store.create_job()` 函数级 API 写 tasks.json（见 §7.1，不调 CronService 方法）：

```python
from xiaopaw_team.tools._tasks_store import create_job

def send_mail(to, type_, subject, content, project_id, from_, tasks_json_path):
    mailbox_ops.send_mail(...)    # FileLock 三态写入邮箱
    # 注册 at cron 唤醒收件人
    create_job({
        "id": f"wake-once-{uuid4()}",
        "schedule": {"kind": "at", "timestamp_ms": now_ms() + 1000, "delete_after_run": True},
        "payload": {
            "routing_key": f"team:{to}",
            "text": f"[wake] 新邮件到达",
            "meta": {"wake_reason": "new_mail"},
        },
    }, tasks_json_path=tasks_json_path)
```

CronService 下次 tick（≤50ms）会通过 mtime 热重载捕获这条 job，1s 后触发 Runner.dispatch。

### 13.5 Manager 并发保护

Manager 可能被两个 routing_key 触发（`p2p:{open_id}` 飞书，`team:manager` cron wake）。外包 `asyncio.Lock`：

```python
MANAGER_LOCK = asyncio.Lock()

async def manager_agent_fn(text, history, session_id, routing_key, root_id, verbose):
    async with MANAGER_LOCK:
        return await _original_manager_agent_fn(...)
```

副作用：用户发消息时，cron wake 会短暂等待几秒，对体验几乎无感。

---

## 14. 沙盒与执行隔离

### 14.1 为什么单沙盒

生产场景应每角色独立沙盒（隔离、可伸缩），但本课演示机通常跑不起 4 个容器。v1.1 选择单沙盒 + 目录隔离 + 工具层权限校验。

### 14.2 目录隔离

```
/workspace/
├── manager/ pm/ rd/ qa/           ← 角色私有目录
└── shared/projects/{pid}/
    ├── needs/ design/ tech/ code/ qa/ reviews/
    ├── mailboxes/
    ├── events.jsonl
    └── logs/
```

权限靠 `WriteSharedTool` 在工具层强制（见 §11.2）。

### 14.3 禁止启动长期进程

**所有 HTTP 接口测试必须用 `httpx.Client(app=fastapi_app)` 直连**（FastAPI TestClient 模式），不允许 `uvicorn ... &` / `python -m http.server &` 等启动后台进程。

理由：
- RD 和 QA 共享同一沙盒，同时跑 uvicorn 会占用同一端口（8080）
- TestClient 模式更快（无 HTTP 开销），pytest 用例间也干净
- SQLite 每个测试用独立 tmpfile（`tempfile.NamedTemporaryFile`），避免 RD 单测库和 QA 集成测试库冲突

写在 `code_impl` 和 `test_run` SKILL 的硬约束里。

---

# 四、Tools 与 Skills

## 15. Tools 清单

### 15.1 共享工具（全员注入）

| Tool | 功能 |
|------|------|
| `SkillLoaderTool` | 22 课基础 + v1.1 三项扩展（4 份 manifest、kind/owner_role、变量替换、热重载） |
| `SendMailTool` | 发邮件 + 内部 at cron 唤醒收件人 |
| `ReadInboxTool` | 读自己的 unread → 标 in_progress，返回快照 |
| `MarkDoneTool` | in_progress → done |
| `ReadSharedTool` | 读 `shared/projects/{pid}/` 下任意文件 |
| `WriteSharedTool` | 写自己 Owner 目录 + 自己的 reviews 条目 |

### 15.2 Manager 专属工具（v1.4 取消 ApplyProposalTool）

| Tool | 功能 | 执行位置 |
|------|------|---------|
| `CreateProjectTool` | 初始化 `shared/projects/{pid}/` 完整目录树 + 5 个空文件；project_id 由 LLM 传入 | 主进程 Python |
| `AppendEventTool` | append 一条事件到 events.jsonl（filelock） | 主进程 Python |
| `SendToHumanTool` | 发飞书卡片 + append event + L1 log | 主进程 Python |

**v1.4 取消 `ApplyProposalTool`**——对齐 28 课《复盘机制重构》，apply 由 **提案角色自己** 执行（读 target_file → 精确匹配 `before_text` → 替换为 `after_text` → 写回），不需要 Manager 侧的机械应用工具。Manager 只做：预审分档 → 发 `retro_approved` 邮件给对应角色 → 收 `retro_applied` 回执。

这个改动让"进化"真正落在产生提案的 Agent 自己身上（"谁提案谁执行"），闭环感更强，也无需宿主机 git 权限。若要保留版本追溯，可在角色 agent.md 里加"执行完在 workspace 内 `git commit -am '[retro][pm] {proposed_change_summary}'`"的建议动作（非强制，workspace 是否 git 仓库都可）。

#### CreateProjectTool 完整清单（P1-14 补齐）

调用签名：`create_project(project_id: str, sop: str, user_open_id: str) -> dict`

**必须创建的目录**（共 9 个）：
```
shared/projects/{pid}/
├── needs/                    # Manager 写产物目录
├── design/                   # PM 写产物目录
├── tech/                     # RD 写产物目录
├── code/                     # RD 写产物目录
├── qa/                       # QA 写产物目录
├── qa/defects/               # QA 缺陷报告子目录
├── reviews/                  # 各角色评审目录
├── mailboxes/                # 团队内邮箱目录
└── logs/l2_task/             # L2 日志目录
```

**必须创建的文件**（共 6 个，内容按约定初始化）：
```
mailboxes/manager.json        # "[]"（空 JSON 数组）
mailboxes/pm.json             # "[]"
mailboxes/rd.json             # "[]"
mailboxes/qa.json             # "[]"
events.jsonl                  # ""（空文件）
state.lock                    # 空文件（作为 FileLock target）
```

初始化完成后立即 append 第 1 条事件：
```python
append_event(project_id, actor="manager",
             action="project_created",
             payload={"project_id": project_id, "sop": sop, "user_open_id": user_open_id,
                      "created_at": iso_utc_now()})
```

CreateProjectTool 返回：
```json
{"project_id": "...", "status": "success", "created_dirs": 9, "created_files": 6}
```

#### ApplyProposalTool 设计细节

- 需要对 workspace/ 做 `git commit`，沙盒内装 git 操作挂载目录有权限/进程交叉问题
- `workspace/` 挂载到沙盒（`./workspace:/workspace`），宿主机和沙盒共享文件系统——宿主机 Python 进程对 workspace 有完整读写权限
- ApplyProposalTool 作为 Manager 主 Agent 的 Tool（不走 Sub-Crew / 沙盒），在主进程直接 `subprocess.run(["git", "-C", workspace_root, ...])`
- **`workspace/` 必须是独立的 git 仓库**（见 §28.3 初始化步骤）
- **v1.3-P0-5 禁用策略**：启动时 `check_workspace_git_ready()` 返回 False 时，`build_role_tools(role="manager", cfg)` 不注册此 Tool；Manager LLM 看不到，调用不会误发（见 §7.2）
- **stale 后路径**：checksum mismatch 时 ApplyProposalTool 返回 `{status: "stale", errcode: 2, errmsg: "target 文件已被修改"}`，Manager LLM 收到后**自动 append `proposal_apply_failed` event** + 在汇总的 evolution_report 里标记此条失败（不 send_to_human(error_alert)——因为用户已经 approve 过，stale 是内部状态问题，不需要重新打扰）

### 15.3 不暴露 / 砍掉的

- ❌ `NotifyRoleTool`：仅 `SendMailTool` 内部用，不暴露给 LLM
- ❌ `UpdateSopProgressTool`：用 `AppendEventTool` 代替
- ❌ `ReadSopProgressTool`：用 `read_project_state` skill 代替
- ❌ `ListSkillsTool`：SkillLoader 自带能力
- ❌ `ApplyProposalTool`（**v1.4 取消**）：对齐 28 课——apply 由提案角色自己机械执行（读 target_file / 匹配 before_text / 替换 after_text / 写回），不需要 Manager Tool

### 15.4 task_callback（不是 Tool，是 Crew 级 hook）

每个 Agent kickoff 完成时自动触发，写 L2 日志（P0-3：project_id 注入方案）：

**设计**：MemoryAwareCrew 实例在构造时持有 `_role: str` 字段，不持有 project_id（因为一个角色可能服务多个历史项目）；project_id 通过**运行时推断**获得：

```python
class MemoryAwareCrew(CrewBase):
    def __init__(self, role: str, workspace_root: Path, ...):
        self._role = role
        self._workspace_root = workspace_root
        self._current_project_id: str | None = None   # 闭包字段

    def _get_current_project_id(self) -> str | None:
        """运行时推断当前 active project：
        扫 workspace/shared/projects/ 下所有 events.jsonl 尾行 action≠'archived' 的那个"""
        if self._current_project_id:
            return self._current_project_id
        for proj_dir in (self._workspace_root / "shared" / "projects").iterdir():
            events_path = proj_dir / "events.jsonl"
            if not events_path.exists(): continue
            last_line = tail(events_path, 1)
            if last_line and json.loads(last_line).get("action") != "archived":
                self._current_project_id = proj_dir.name
                return proj_dir.name
        return None

    def _l2_task_callback(self, task_output: TaskOutput):
        # result_quality_estimate 来源：从 task_output.raw 或 task_output.json_output
        # 里解析 Agent 调 self_score skill 后写入的 {self_score, breakdown} 字段
        # 若缺失（Agent 漏调 self_score skill）→ 默认 null，find_low_quality_tasks 会跳过此条
        quality, breakdown = extract_self_score(task_output)
        write_l2_entry(
            project_id=self._get_current_project_id(),
            role=self._role,
            task_id=task_output.task_id,
            duration_ms=...,
            result_quality_estimate=quality,             # float 0.0-1.0 或 null
            result_quality_breakdown=breakdown,          # dict: 5 维各自分数，便于复盘追溯
            result_quality_source="self_score_skill",    # 枚举，未来可加 "manager_review"
            tools_used=[...],
            ...
        )
```

task_callback 在 Crew 构造时注入：`Crew(tasks=..., task_callback=self._l2_task_callback)`。

**self_score 字段的 downstream 反馈修正**（v1.4-13 配套）：
- L2 写入时只记录 **self_score**（Agent 自评）
- 当 Manager 后续收到 `review_received(need_changes)` 或用户 `checkpoint_rejected` 时，Manager 调 `AppendEventTool` 追加 `task_quality_adjusted` 事件（含原 task_id + adjustment 数值），复盘时 find_low_quality_tasks 会读这两个数据源合并：`final_quality = self_score - sum(adjustments)`
- 这样保证"自评可能虚高"被下游信号自动纠正，同时不需要 Manager 直接写 L2（L2 仍由各角色 task_callback 负责）

**并发**：`_current_project_id` 的推断结果在 Agent 本次 wake 期间缓存一次；下次 wake 新实例重新推断（本课单项目并发=1，缓存不会失效）。

**限制**：本课**同时只支持单项目活跃**（见附录 E）。多项目并发需扩展 Manager 在 send_mail 时把 project_id 塞进 inputs，所有角色 MemoryAwareCrew 从 inputs 读取。

**关键**：L2 写入用 `task_callback`，**不**用 `@after_llm_call`（22 课 main_crew.py 明确警示后者会破坏 CrewAI 的 tool dispatch）。

---

## 16. Skills 清单（按角色）

所有 Skills frontmatter 符合附录 C 规范。每个 SKILL.md 的 `description` 字段必须含**关键触发词**，以便 LLM 通过 SkillLoader 自动匹配。

### 16.1 Manager（11 个 Skill）

| Skill | 类型 | description 关键词 | 作用 |
|-------|------|---|------|
| `sop_cocreate_guide` | **reference** | "建立 SOP 对话框架, 5 维发问, 制定流程" | 主 Agent 加载后获得 5 维对话框架。**主 Agent 用 SendToHumanTool 多轮发问**，不写文件 |
| `sop_write` | task | "固化 SOP, 按对话摘要生成 SKILL.md" | Sub-Crew 接收 `{sop_name, 五维对话摘要}` → 沙盒生成 `workspace/manager/skills/sop_{name}/SKILL.md` + 追加 manifest 条目 |
| `list_available_sops` | **task** | "列出可用 SOP。**Manager 收到飞书新任务且 read_project_state 显示无 active project 时加载**；Sub-Crew 跑 list_sops.py 扫 kind=sop SKILL 返回 `{name, description, kind}` 数组——不做自动选择，Manager LLM 据此与 user_text 做语义匹配" | v1.5-A3 从 sop_selector 改名；职责不变但名字更准确（动词 + 复数名词） |
| `sop_feature_dev` | **reference** | "小功能开发主流程" | 核心 SOP（见 §17），frontmatter `kind=sop` |
| `requirements_guide` | **reference** | "需求澄清四维发问, 目标边界约束风险" | **四维 = {goal, boundary, constraint, risk}**（见 §16.1.1 明示）；Manager 基于框架多轮 SendToHuman 发问；四维覆盖完后 append `requirements_coverage_assessed` event |
| `requirements_write` | task | "写需求文档, 按澄清对话摘要生成 requirements.md" | Sub-Crew 接收 `{project_id, dimensions: {goal, boundary, constraint, risk}}` → 沙盒生成 `needs/requirements.md` → 返回附录 C2 约定的 task 返回值 JSON |
| `read_project_state` | task | "**每次 Manager kickoff 第一步必调**（恢复多轮 wake 间的状态）。读项目事件流 + 交叉校验 + 生成摘要；返回 `{latest_action, event_count, has_pending_checkpoint, self_healed_events}`" | v1.5-A4 补触发源 |
| `check_review_criteria` | task | "数实体, 数接口, 评审判据, 阈值判断" | **v1.3 修订：直接返回 `{entities: N, apis: M, thresholds: {...}, threshold_met: bool, reason: str}`**（见 §16.1.2），Manager LLM 只读 threshold_met 不自己做阈值比对 |
| `handle_checkpoint_reply` | reference | "处理用户 checkpoint 回复的分类决策框架。**收到 type=checkpoint_response 邮件时加载**；按 content.classified_as ∈ {approved/rejected/need_discussion/proposals_partial} 分支决策；加载后 Manager 必须先 append `checkpoint_reply_classified` 事件再后续动作" | v1.5-A4 补触发源 |
| `team_retrospective` | task | "团队复盘, 识别瓶颈, 跨 Agent 模式, 触发自我复盘" | v1.4 对齐 28 课：Agent 自行用 log_query CLI 查"全员统计 / 全量 L1 / 单 Agent 任务列表"，思考框架 4 问（谁是瓶颈 / 有无跨 Agent 模式 / 协作接口健康吗 / 上周改进生效了吗），产出团队级 RetroProposal（target_file 可跨 Agent）+ 触发瓶颈 Agent 的 self_retrospective |
| `review_proposal` | **reference** | "审批复盘提案的分档决策框架。**收到 type=retro_report 邮件时加载**；按每条 improvement_proposal 的 target_file 分档（档 1 memory.md 自动批 3/天 / 档 2 skill+agent 转 Human / 档 3 soul 标高风险转 Human）；**强制输出 §16.1.3 规定的 JSON 格式**"（v1.4 重写 + v1.5-A4 补触发源） |

### 16.1.1 四维定义（P1-9）

`requirements_guide` SKILL.md 里明示**四维 = {goal, boundary, constraint, risk}**：

| 维度 | key | 问什么 | 示例问法 |
|------|-----|--------|---------|
| **目标** | `goal` | 任务成功的标准是什么？做给谁用？达到什么效果算好？ | "你期望这个小网站能帮你做什么？每天大概用来干什么？" |
| **边界** | `boundary` | 必须做的是什么？明确不做的是什么？ | "宠物日记里要记哪些字段？文字、图片、心情？外部分享要不要？" |
| **约束** | `constraint` | 时间、资源、技术栈、部署环境、合规有什么限制？ | "是自己用还是要给朋友看？需要登录吗？数据存本地还是云端？" |
| **风险** | `risk` | 哪些决策需要提前确认，避免 PM/RD 自行猜？ | "移动端也要用吗？心情字段希望几档？历史日记删除支持吗？" |

结束条件：四维各至少有一个**明确回答**（不是"我不知道"、"你看着来"），触发：
```
append_event(action="requirements_coverage_assessed",
             payload={"dimensions": {"goal": "...", "boundary": "...", "constraint": "...", "risk": "..."},
                      "covered": 4, "complete": true})
```

### 16.1.2 check_review_criteria 返回值契约（P0-4）

脚本签名：
```python
def check_review_criteria(artifact_path: str, stage: str, thresholds: dict) -> dict:
    """
    artifact_path: /workspace/shared/projects/{pid}/design/product_spec.md
    stage: "product_design" | "tech_design" | "test_plan"
    thresholds: 从 team_standards.yaml 读取的对应 stage 的阈值
    返回契约（JSON）:
        {
            "entities": int,          # grep '^## 实体' 或 '^## Entity' 或 '^### 数据模型' 的节数
            "apis": int,              # grep '^- `POST ' / '^- `GET ' 的行数（匹配 markdown 接口表）
            "thresholds": dict,       # echo 入参，便于审计
            "threshold_met": bool,    # entities>=min_entities AND apis>=min_apis
            "reason": str,            # 人类可读原因，如 "entities=3>=3 AND apis=7>=7 → true"
            "status": "success" | "failed",
            "errors": list[str]
        }
    """
```

**Manager LLM 只读 `threshold_met` 字段决策，不自己做任何比对**。Manager 调用后立即 append 结构化事件（含全部入参出参）：
```
append_event(action="review_criteria_checked",
             payload={"stage": "product_design",
                      "metrics": {"entities": 3, "apis": 7},
                      "thresholds": {"min_entities": 3, "min_apis": 7},
                      "threshold_met": true, "reason": "...",
                      "insert_review": true})
```

**明文规定产品/技术/测试文档必含的 markdown 标题**，避免中英/格式差异：

| stage | 必含标题（requirements.md / product_spec.md / tech_design.md / test_plan.md）|
|-------|---------|
| product_design | `## 数据模型`（数实体用）+ `## 接口契约`（数 API 用，每条接口 `^- \`(POST\|GET\|PUT\|DELETE)` 格式）|
| tech_design | `## 后端设计` + `## 数据库设计` + `## 接口实现要点` |
| test_plan | `## 用例清单` + 每条用例 `^\| \|\d+\|` 表格行 |

这些标题写进每个对应 task skill 的 SKILL.md 模板硬约束里，check_review_criteria 的 grep 模式就能机械匹配。

### 16.1.3 review_proposal 分档审批（v1.4 重写，对齐 28 课）

**核心改动**：v1.3 的"accept/reject 二分 + 汇总后一次性找用户全选/全弃"改成 **28 课"按改动深度分档"** 决策模型。Manager 每收到一条 `retro_report` 邮件（内含多条 improvement_proposals）就分档处理。

#### A. 触发

邮件 type=`retro_report`（proposer_role → Manager）；content 含一个 JSON 文件路径（`shared/proposals/{agent_id}_retro_{date}.json`，结构见附录 A2）。

#### B. 预审步骤（Manager LLM 按 review_proposal SKILL 指引）

1. 读 proposals JSON 文件
2. **对每条 improvement_proposal 单独评估**，不做"全局 accept/reject"判断
3. 预审合规性 checklist（每条必过）：
   - `evidence` 非空（至少 1 个 task_id）
   - `target_file` 存在于 workspace 下且可写
   - `root_cause` 在 {sop_gap, prompt_ambiguity, ability_gap, integration_issue} 内
   - `before_text` / `after_text` 都非空
   - `proposed_change` 是人类可读的变更描述
   合规失败 → append `retro_proposal_invalid`（payload 含 proposal_id 和失败原因），继续下一条
4. **按 target_file 路径分档**（核心决策）：

| 档位 | target_file 模式 | 处理 | HITL |
|------|-----------------|------|------|
| **档 1（自动）** | `workspace/{role}/memory.md` | 直接 approve，硬闸门：当天超 3 条则降级到档 2 | 不打扰 |
| **档 2（需 Human）** | `workspace/{role}/agent.md` 或 `workspace/{role}/skills/*.md` | 合并后发 `send_to_human(type=proposal_review)` 卡片，用户逐条点 approve/reject | 必须 |
| **档 3（高风险）** | `workspace/{role}/soul.md` | 同档 2 但卡片标红 + 附"soul 改动会影响该 Agent 所有后续判断"警告 | 必须 + 强 warn |

5. 对档 1 的每条 → 直接产出 `retro_approved` 邮件发给 proposer_role，内含该条 proposal；append `retro_approved_by_manager` 事件
6. 档 2/3 的提案**聚合后**发一张卡片给用户；用户回复后按 approved/rejected 产生 `retro_approved_by_human` / `retro_rejected_by_human` 事件，然后给 proposer_role 分别发 `retro_approved` / `retro_rejected` 邮件

#### C. review_proposal SKILL.md 强制输出模板

Manager LLM 读完 proposals 后必须产出以下 JSON（供 Manager 后续工具调用解析）：

```json
{
  "agent_id": "pm",
  "retro_date": "2026-04-20",
  "proposals_count": 3,
  "decisions": [
    {
      "proposal_id": "p001",   // 数组下标或 hash，用于后续追踪
      "target_file": "workspace/pm/memory.md",
      "tier": 1,               // 1/2/3
      "action": "auto_approve",
      "reason": null
    },
    {
      "proposal_id": "p002",
      "target_file": "workspace/pm/skills/product_design/SKILL.md",
      "tier": 2,
      "action": "require_human",
      "reason": null
    },
    {
      "proposal_id": "p003",
      "target_file": "workspace/pm/memory.md",
      "tier": 1,
      "action": "tier1_quota_exceeded_fallback_human",
      "reason": "当天档 1 已批 3 条，此条降级"
    }
  ],
  "tier1_quota_today_used": 3,
  "tier1_quota_today_limit": 3
}
```

#### D. Manager 基于决策的后续动作

```
for d in decisions:
  if d.action == "auto_approve":
      append_event("retro_approved_by_manager", {proposal_id, tier: 1})
      send_mail(to=proposer_role, type="retro_approved", content=提案详情)
  elif d.action in {"require_human", "tier1_quota_exceeded_fallback_human"}:
      加入 pending_human_approval 列表

if pending_human_approval:
    send_to_human(type="proposal_review", title="PM 提交 N 条复盘提案",
                  proposals=pending_human_approval, risk_flag=有无 tier=3)
    （等用户逐条 approve → recv_human_response → 再 send_mail 给对应角色）
```

#### E. 分档 vs v1.3 proposals_approve 的关系

v1.3 的 proposals_review 卡片还在用，但**只出现在档 2/3 场景**。档 1 不打扰用户——这是比 v1.3 更"宽松"的设计（memory 改动本就是小条目，不需要每次打扰）。

档 1 的硬闸门（3 条/天）由 Manager LLM 读当天 events.jsonl 里 `retro_approved_by_manager` 计数实现（LLM 只读 count，不自己计算阈值）。

### 16.2 PM（3 个私有 Skill + 2 个 shared，v1.5-A1/A2 改名）

| Skill | 类型 | 归属 | description（v1.5 补三要素） | 作用 |
|-------|------|------|---|------|
| `product_design` | task | `pm/skills/` | "产品设计文档（PM 写）。收到 type=task_assign 且 content 指向 needs/requirements.md 时加载；按模板写 product_spec.md + 机械自查，返回 metrics" | 按模板写 + 自查 |
| `review_tech_design_from_pm` | reference | `pm/skills/` | "评审技术方案（PM 视角）。收到 type=review_request 且 target=tech/tech_design.md 时加载；**只审产品意图映射**，不审技术选型；返回 checklist + 结论" | v1.5 改名消歧 |
| `self_retrospective`（共享） | task | `shared/skills/` | 见 §16.6 | PM 调用时传 `agent_id=pm` |
| `self_score`（共享） | reference | `shared/skills/` | 见 §16.6 | task_done 前无条件调用 |

### 16.3 RD（4 个私有 Skill + 2 个 shared，v1.5-A1/A2 改名）

| Skill | 类型 | 归属 | description（v1.5 补三要素） |
|-------|------|------|---|
| `tech_design` | task | `rd/skills/` | "技术方案（RD 写）。收到 type=task_assign 且 content 指向 design/product_spec.md 时加载；按模板写 tech_design.md + 自查" |
| `code_impl` | task | `rd/skills/` | "代码实现（RD 写）。收到 type=task_assign 且 content 指向 tech/tech_design.md 时加载；沙盒内写代码 + pytest + 自查；禁 uvicorn" |
| `review_product_design_from_rd` | reference | `rd/skills/` | "评审产品文档（RD 视角）。收到 type=review_request 且 target=design/product_spec.md 时加载；审**可实现性 / 性能 / 数据一致性 / 接口完整性**" **v1.5 改名** |
| `review_test_design` | reference | `rd/skills/` | "评审 QA 的测试设计（RD 视角）。收到 type=review_request 且 target=qa/test_plan.md 时加载；**只审用例期望 vs 代码实际行为的一致性**" |
| `self_retrospective`（共享） | task | `shared/skills/` | 见 §16.6 |
| `self_score`（共享） | reference | `shared/skills/` | 见 §16.6 |

### 16.4 QA（5 个私有 Skill + 2 个 shared，v1.5-A1/A2 改名）

| Skill | 类型 | 归属 | description（v1.5 补三要素） |
|-------|------|------|---|
| `review_product_design_from_qa` | reference | `qa/skills/` | "评审产品文档（QA 视角）。收到 type=review_request 且 target=design/product_spec.md 时加载；审**可测性 / 验收标准可机械检查 / 边界 case 覆盖 / 错误契约完整**" **v1.5 改名** |
| `review_tech_design_from_qa` | reference | `qa/skills/` | "评审技术方案（QA 视角）。收到 type=review_request 且 target=tech/tech_design.md 时加载；审**可测性 / 日志点 / 可观测性 / 错误分支暴露**" **v1.5 改名** |
| `review_code` | reference | `qa/skills/` | "代码走查（QA 视角）。收到 type=review_request 且 target=code/ 时加载；审**难测路径 / 错误分支 / 边界 case / 日志埋点**；QA 唯一此类 skill，不消歧" |
| `test_design` | task | `qa/skills/` | "测试设计（QA 写）。收到 type=task_assign 且 subject 含'测试设计'时加载；按模板产 qa/test_plan.md" |
| `test_run` | task | `qa/skills/` | "测试执行（QA 跑）。收到 type=task_assign 且 subject 含'测试执行'时加载；跑 pytest + 写 report + 写 defects" |
| `self_retrospective`（共享） | task | `shared/skills/` | 见 §16.6 |
| `self_score`（共享） | reference | `shared/skills/` | 见 §16.6 |

### 16.5 self_score（全员共享 reference，v1.4-13 新增）

**定位**：补齐 L2 `result_quality_estimate` 字段的来源——**Agent 在 task_done 前自评** task 质量分数（0.0-1.0）。

**归属**：共享 skill，挂 `workspace/shared/skills/self_score/SKILL.md`，4 个角色的 manifest 都 enable。

**使用时机**：每次 Agent 即将发 `send_mail(task_done, ...)` 之前、**无条件**调一次：

```
Agent kickoff 末尾 → load_skill("self_score") → 按 SKILL.md 框架 5 维自评 → 
→ send_mail(to=manager, type=task_done, content={..., self_score: 0.82, breakdown: {...}})
```

task_callback（§15.4）读 task_output 解析 self_score 写入 L2。Agent **如果漏调** self_score，`result_quality_estimate=null`，find_low_quality_tasks 查询时此条会被 skip（不排序进 top-k）——这是对"漏调"的软惩罚，不报错。

**SKILL.md 主要内容**（简述）：

```markdown
# self_score

## 你的任务
在 task_done 之前，对本次任务产出做 5 维自评，输出 self_score (0.0-1.0)。

## 5 个评估维度（加权）

| 维度 | 权重 | 打分标准 (0-1) |
|------|------|---------------|
| 1. 产物完整性 | 20% | 所有模板必填字段都填了？产物文件非空、size >= 基线？ |
| 2. 自查通过率 | 30% | self_review checklist 过了几项 / 总项；RD 的 pytest 是否 pass + coverage 达标 |
| 3. 硬约束合规 | 20% | 是否违反了 SKILL.md 里的 "硬约束"（如禁 uvicorn / evidence 非空 / 时区必填 等）|
| 4. 清晰度 | 15% | 产出对后续角色易懂度（PM 写的设计 RD 能直接开发？RD 写的代码 QA 能直接测？） |
| 5. 时效 | 15% | 耗时是否在预期内；重试次数是否 ≤ 1 |

## 输出格式（必须严格遵守）

```json
{
  "self_score": 0.82,
  "breakdown": {
    "completeness": 1.0,
    "self_review": 0.9,
    "hard_constraints": 1.0,
    "clarity": 0.7,
    "timeliness": 0.8
  },
  "rationale": "产物完整 + 自查全过 + 硬约束合规；清晰度略扣是因为 spec 里 edge case 描述偏简；时效接近上限但未超"
}
```

总分公式：`self_score = 0.2*completeness + 0.3*self_review + 0.2*hard_constraints + 0.15*clarity + 0.15*timeliness`

## 约束

- **严禁虚高**：任何一维分数 >0.9 时，rationale 必须明确解释"为什么满分"，避免"感觉不错"
- **硬约束扣分不可赦免**：若违反任何硬约束（如 RD 起 uvicorn / PM 验收标准不可测），hard_constraints 必 <= 0.5
- **self_score 计算精确到 2 位小数**，四舍五入
```

**下游修正**（§15.4 已描述）：Manager 后续若收到 `review_received(need_changes)` / `checkpoint_rejected`，调 `AppendEventTool(action="task_quality_adjusted", payload={task_id, adjustment: -0.2, reason})`；复盘时合并计算 `final_quality`。

### 16.6 shared/skills/（全员可 load，owner_role=any）

v1.5-A1 把 self_retrospective 从 PM/RD/QA 角色目录挪到 `workspace/shared/skills/`，避免 3 份重复。现有 shared skill：

| Skill | 类型 | 作用 |
|-------|------|------|
| `self_retrospective` | task | **v1.5 挪入 shared**。Agent 调用时通过 task_context 传入 `agent_id`（== 当前 role）+ `days: 7`；Sub-Crew 在沙盒内用 log_query CLI 查自己的数据做分析，产 `shared/proposals/{agent_id}_retro_{date}.json`。角色差异（如 RD 额外关注 pytest_attempts，QA 关注 defects_count）在 agent.md 补一句"你在 self_retrospective 时应特别关注 {your 维度}"即可，**不需要** PM/RD/QA 各自维护 SKILL.md |
| `self_score` | reference | v1.4-13 新增（§16.5）；task_done 前无条件调用，5 维自评 |

**设计理由**：
- self_retrospective 的思考框架（5 问 + 4 种 root_cause）对所有角色相同
- Sub-Crew 启动时主 Agent 传 agent_id，Sub-Crew 用这个参数过滤 log_query 只查本角色数据
- 跨角色共性 = shared；角色特异 = 私有 agent.md 补充说明

### 16.7 复用 22 课 Skills（Legacy，全员按需）

挂在 `workspace/shared/legacy_skills/`：

| Skill | 类型 | 备注 |
|-------|------|------|
| `search_memory` | task | 22 课原样 |
| `memory-save` | task | 22 课原样 |
| `skill_crystallize` | task | **v1.5-A6 改名自 22 课 skill-creator**：项目内把 SOP 固化为 SKILL.md，与 everything-claude-code 社区的 skill-creator 概念不同，改名避免混淆 |
| `memory-governance` | task | 22 课原样 |
| `history_reader` | reference | 22 课原样（内联处理，不走沙盒） |

---

## 17. SOP 作为 reference skill + Skill 类型边界

### 17.1 三种动作载体的能力边界（v1.1 核心章节）

29 课 skill 设计的核心原则：三种"动作载体"各有能力边界，不能混用：

| 载体 | 能做 | 不能做 | 典型用途 |
|------|------|--------|---------|
| **reference skill** | 把 SKILL.md 正文塞回主 Agent 上下文，主 Agent 基于指令推理 | 不能操作文件；不能跑代码；不能对用户发消息；不能多轮等回复 | **对话框架** / 评审 checklist / 主流程 SOP / 决策树 |
| **task skill** | 启动独立 Sub-Crew + AIO-Sandbox；可读写文件、跑 bash/python | **中途不能等用户回复**（一次 kickoff 就退出）；看不到主 Agent 的飞书 session；看不到主 Agent 已有对话历史（除非 inputs 显式传入） | **一次性生成长文档** / 跑 pytest / 机械数据处理 |
| **主 Agent 直接 Tool** | 原子动作：发邮件、收邮箱、发飞书卡片、读/写 markdown、追加 event、git commit | 复杂逻辑（如"按模板生成 2000 字文档"）不适合，会污染主 Agent 上下文 | 团队协作基础设施 |

**为什么 29 课主 Agent 必须有直接 Tool**：

22 课教义："Main Agent 只有 SkillLoaderTool"——当时场景是"用户 → 主 Agent → 调 skill 完成 → 回复用户"的单轮流程。29 课场景不同：主 Agent（尤其 Manager）要维持项目状态、发多种邮件、跟多角色协作、主动推送飞书。如果全走 skill：
- 发一封邮件启动 task skill ~ 几秒 + 额外 LLM 调用 → 开销爆炸
- 多轮对话发下一个问题 SkillLoader 不提供"发问题"的原子能力
- 每次 read_inbox 启 Sub-Crew 毫无意义

所以 29 课把**"团队协作基础设施"下沉到主 Agent 的直接 Tool**，SkillLoaderTool 仍然是**"领域能力"的扩展入口**（对话框架、SOP、复杂文件生成、复盘）。工具和 skill 职责清晰分层。

### 17.2 "对话 + 写入"类 skill 的标准拆分模板

凡是**"需要多轮对话 + 对话结束后写长文档"**的场景，都按此模板拆两个 skill：

```
xxx_guide  (reference)
├─ 提供对话框架、发问策略、结束条件判据
├─ 主 Agent 加载后：反复 SendToHuman → ReadInbox → 判断是否结束
└─ 结束时 → 调 xxx_write

xxx_write  (task)
├─ 输入：{对话摘要 / 关键参数}（主 Agent 从自己对话历史摘要传入）
├─ Sub-Crew 在沙盒内按模板生成长文档
└─ 返回：文件路径
```

本课按此模板拆分的 skill：
- `sop_cocreate_guide` + `sop_write`（SOP 共创）
- `requirements_guide` + `requirements_write`（需求澄清）

本课**不**按此拆分的对话场景：
- **需求修订**：用户驳回 checkpoint 后的修订不是新一轮澄清，是 Manager 直接 send_mail 给 PM 附修改意见
- **handle_checkpoint_reply**：主 Agent 根据回复做分类决策，不需要对话框架

### 17.3 SOP 为什么是 reference skill

**SOP = reference skill + frontmatter `kind: sop`**：

- **不能是 task**：task 是"一次性 Sub-Crew 跑完返回"，而 SOP 是"主 Agent 持续参考的指令文档"——每次 Manager 被唤醒做决策前都需要看 SOP 的推进规则。语义上只能是 reference
- **不能是普通共享文件**：如果 SOP 放在 `shared/sop/xxx.md` 让主 Agent 用 ReadShared 读，SkillLoaderTool 的工具 description XML 里看不到 SOP 的存在，Manager LLM 不知道有哪些 SOP 可选，sop_selector 也无法枚举
- **reference + kind=sop 两全其美**：SkillLoader 枚举（可见）+ sop_selector 过滤（可选）+ reference 语义（持续参考）

新 SOP 被 SkillLoader 注册的方式：
- `sop_write` 任务除了写 SKILL.md，还追加一条到 `workspace/manager/skills/load_skills.yaml`
- main.py 监听 manifest 文件 mtime 变化，触发 SkillLoader 重跑 `_build_description()`
- 下次 Manager kickoff 就能看到新 SOP

### 17.4 sop_feature_dev SKILL.md（本课核心文档节选）

```markdown
---
name: sop_feature_dev
description: 小功能开发项目主流程。收到新开发任务后加载此 Skill，按其步骤推动项目。
type: reference
kind: sop
owner_role: manager
version: 1.0.0
---

# SOP: 小功能开发

你是 Manager。收到用户新开发需求后，按以下推进规则执行。

## 阶段清单（6 主阶段）

| # | 阶段 | Owner | 产物 | 用户 Checkpoint | 可选团队评审 |
|---|------|-------|------|----------------|-------------|
| 1 | 需求澄清 | Manager | needs/requirements.md | ✅ | —— |
| 2 | 产品设计 | PM | design/product_spec.md | ✅ | 可插入 RD+QA |
| 3 | 技术设计+实现+单测 | RD | tech/tech_design.md, code/ | —— | 可插入 PM+QA |
| 4 | 代码走查+测试+执行 | QA | qa/test_plan.md, qa/test_report.md | —— | 代码走查 by QA 强制 |
| 5 | 交付 | Manager | —— | ✅ | —— |
| 6 | 复盘进化 | Manager | proposals/* | ✅（逐条 approve） | —— |

## 推进规则总则

每次被唤醒，先：
1. load_skill("read_project_state") → 拿到当前状态摘要
2. read_inbox() → 看邮件
3. 根据两者决定下一步

## 阶段详细规则

### 阶段 1 推进（需求澄清）
- 生成 project_id（LLM 决定），调 CreateProjectTool 初始化工作区
- append_event(action="project_created")
- load_skill("requirements_guide") ← reference，获得四维发问框架
- 基于框架调 SendToHumanTool 发问；等用户回复后继续
- 四维覆盖完 → load_skill("requirements_write", task_context={project_id, 摘要}) ← task
- Sub-Crew 返回后：append_event(action="requirements_drafted")
- send_to_human(checkpoint_request, summary=需求摘要)

### 阶段 2 推进（产品设计）
- send_mail(to=pm, type=task_assign, subject="产品设计", content="读 needs/... 写 design/...")
- append_event(action="assigned", to=pm)
- 收到 pm task_done 后：
  - 基础抽检（文件存在、非空、含模板必要节）
  - load_skill("check_review_criteria") → 脚本数实体/API 返回数字
  - 比对 team_standards.yaml 阈值（by LLM）→ 决定是否插入评审
- 评审子流程（见下）
- 两方都 pass → send_to_human(checkpoint_request, summary=设计摘要)

### 阶段 3 推进（RD 交付）
- send_mail(to=rd, type=task_assign, subject="技术设计+实现+单测", content="按 tech_design SKILL 和 code_impl SKILL...")
- 收到 rd task_done(code) → 进阶段 4

### 阶段 4 推进（QA）
- 4a 代码走查（强制）：send_mail(to=qa, type=review_request, subject="代码走查")
- 4b 测试设计：send_mail(to=qa, type=task_assign, subject="测试设计")
- 4c 测试执行：send_mail(to=qa, type=task_assign, subject="测试执行")
- 无阻塞缺陷 → 进阶段 5；有阻塞 → 发回 rd 修 + qa 回归

### 阶段 5 推进（交付）
- send_to_human(type=delivery, summary=..., artifacts=[code/README.md, qa/test_report.md])
- approved → 进阶段 6

### 阶段 6 推进（复盘进化）
- load_skill("team_retrospective") → 识别瓶颈 + 对谁发 retro_trigger
- 对每个瓶颈角色 send_mail(type=retro_trigger)
- 收到各角色 retro_proposal → load_skill("review_proposals") → 按 checklist 预审
- 收齐 N 条后 send_to_human(type=proposals_review, 附提案列表)
- 用户 approve → 对每条 approved 调 ApplyProposalTool(proposal_id)
- 全部应用 → send_to_human(type=evolution_report, 附 git diff 摘要)

## 评审子流程
- 发 review_request 给两方 / 一方
- 等两份 review_done
- 汇总：两方都 pass → 通过；有 need_changes → 发回产出角色修
- **轮次写进 subject（P1-10 grammar）**：发回修改时 subject 必须匹配正则 `^.*\(第 (\d+) 轮\)$`（全角括号和空格均不可替换，N 必为阿拉伯数字）。例："产品设计修订 (第 2 轮)" ✅；"产品设计修订（第二轮）" ❌；"Round 2 revision" ❌。SendMailTool 在写邮箱前校验 subject，违反 grammar 的情况 raise ValueError 不写入
- 循环上限 team_standards.review_max_rounds（默认 3），超过 → error_alert

## 硬约束
- 每次动作前 read_project_state，每次动作后 append_event
- 你从不写代码 / 设计 / 测试
- 你从不让 PM/RD/QA 联系用户
- 评审循环不可超上限
- 所有 checkpoint 必须等用户回复后才能推进
```

---

# 五、完整业务流程剧本

## 阶段 0：SOP 共创（可选，一次性）

### 场景
用户第一次用 xiaopaw-team、或需要新类型 SOP 时触发。本课 demo 视情况决定是否演示——推荐在开场演示一次，后续项目跑预置 SOP。

### 流程（v1.1 guide + write 两 skill 模式）

1. 用户飞书："**我们来建一个开发的 SOP 吧**" → FeishuListener → recv_human_response（无 pending checkpoint） → Runner(p2p:ou_xxx) → Manager kickoff
2. Manager 按 team_protocol：read_inbox（无邮件）→ read_project_state（无 project）
3. Manager LLM 看 user_text 含"SOP / 流程 / 标准"，通过 SkillLoader description 匹配到 `sop_cocreate_guide`
4. **第一步（reference）**：`load_skill("sop_cocreate_guide")` → 返回 5 维对话框架 + 结束条件判据给主 Agent 上下文
5. **对话阶段**（主 Agent 用直接 Tool，不再调 skill）：
   - Manager LLM 调 `SendToHumanTool(type=info, ...)` 发第 1 问
   - 主 Agent kickoff 结束
   - 用户回复 → 下次 kickoff，飞书 history 自动注入 backstory
   - Manager LLM 判断：5 维未覆盖完 → 继续 SendToHuman；覆盖完 → 进第二步
   - 循环 3-5 轮
6. **第二步（task）**：`load_skill("sop_write", task_context={sop_name: "feature_dev", 五维摘要: {...}})` 
   - Sub-Crew 在沙盒启动，按模板生成完整 SKILL.md，写 `workspace/manager/skills/sop_{name}/SKILL.md`
   - Sub-Crew 追加 `workspace/manager/skills/load_skills.yaml` 条目
7. **manifest 热重载**：main.py 的 mtime 监听发现 load_skills.yaml 变了 → 触发 SkillLoader `_build_description()` 重跑
8. Manager LLM 调 `SendToHumanTool(type=checkpoint_request, ...)` 等用户确认
9. 用户 approve → Manager append_event(action="sop_created") → 完成

### 产物
`workspace/manager/skills/sop_feature_dev/SKILL.md`（或 `sop_{name}/`）被固化。后续项目复用。

---

## 阶段 1：需求澄清与确认

### 1.1 用户发起

用户："**帮我做个宠物日记小网站，能记录多只宠物，每只宠物有日记时间线。**"

### 1.2 消息路径
- FeishuListener → feishu_bridge.recv_human_response（无 pending checkpoint）
- Runner(p2p:ou_d683...) → Manager agent_fn（外层 asyncio.Lock）

### 1.3 Manager kickoff
- 按 team_protocol：先 read_inbox（无邮件）
- load_skill("read_project_state") → "无 active project"
- Manager LLM 看到是"新开发需求"，通过 SkillLoader description 匹配到 `list_available_sops`（v1.5-A3 改名）
- `load_skill("list_available_sops")` → 脚本返回所有 kind=sop 的 SKILL 的 `{name, description}` 数组
- Manager LLM 读数组与 user_text 做**语义匹配**（比如 user 说"做个小网站"→ description 含"小功能开发"命中 sop_feature_dev）
- `load_skill("sop_feature_dev")` → 返回主流程 SOP，Manager LLM 进入阶段 1 推进

### 1.4 加载 requirements_guide（reference）

Manager LLM 按阶段 1 指令：
1. 生成 project_id（LLM 决定，如 `proj-pawdiary-{timestamp}`）
2. 调 `CreateProjectTool(project_id)` → mkdir + 空邮箱 + 空 events.jsonl
3. 调 `AppendEventTool(action="project_created", payload={...})`
4. `load_skill("requirements_guide")` ← reference，返回四维发问框架

### 1.5 多轮对话阶段（主 Agent 用直接 Tool）

- Manager LLM 基于四维框架，调 SendToHumanTool 发第 1 问
- 用户回复 → Manager 再次 kickoff（对话 history 自动注入）→ 判断是否四维覆盖完 → 继续 SendToHuman
- 每轮可选 AppendEventTool 记录进展
- **主 Agent 不反复 load requirements_guide**（reference 内容已在上下文），**不启 Sub-Crew**

### 1.6 对话充分 → 调 requirements_write（task）

Manager LLM 判断"四维都说清楚了"：
- `load_skill("requirements_write", task_context={project_id, 四维摘要})` 
- Sub-Crew 启动，在沙盒内按模板生成 `requirements.md`，写到 `/workspace/shared/projects/{pid}/needs/requirements.md`
- Sub-Crew 返回路径

主 Agent：
- AppendEventTool(action="requirements_drafted", artifact="needs/requirements.md")
- 进 1.7

### 1.7 Checkpoint
`SendToHumanTool(type="checkpoint_request", title="需求文档 v1", summary=摘要)`
- 内部：append_event(action="checkpoint_requested", ck_id="ck-001")
- 飞书卡片推送

### 1.8 用户确认
- feishu_bridge.recv_human_response → 找到 pending ck-001 → 写 manager.json checkpoint_response(ck-001, approved)
- SendMailTool at cron → Manager 1s 后唤醒
- Manager kickoff → read_inbox 看到 approved → append_event(action="checkpoint_approved") → 进阶段 2

---

## 阶段 2：产品设计（含可选团队评审）

### 2.1 Manager 发 PM 任务
```
send_mail(to="pm", type_="task_assign", project_id=pid, subject="产品设计",
  content="读 needs/requirements.md, 按 product_design SKILL 写 design/product_spec.md。自查通过后发 task_done")
```
内部：at cron 唤醒 PM。append_event(action="assigned", to="pm", stage="product_design")

### 2.2 PM 醒来
- PM agent_fn（routing_key=team:pm, wake_reason=new_mail）
- 按 team_protocol：read_inbox → 看到 task_assign
- PM agent.md 里没有硬路由表，LLM 读 task_assign 的 content，看到"写产品设计" → SkillLoader 匹配 `product_design`
- 可选：load_skill("search_memory") 查历史同类（CRUD / 时间线）经验
- `load_skill("product_design")` task，Sub-Crew 启动

### 2.3 product_design SKILL（task）
- 模板字段：概述 / 用户场景 / 功能清单 / 数据模型 / 接口契约 / 交互流程 / 验收标准 / 约束 / 风险
- 每节必填（没内容写"无"）
- 验收标准必须可机械检查
- 自查 checklist 每项附验证命令（grep 等）——**自查不允许"主观打钩"**
- 自查通过 → write_shared → send_mail(task_done)

### 2.4 Manager 验收 + 决定是否插评审（P0-4 机械化）
- Manager 被唤醒 → read_project_state → 最近动作是 pm task_done
- read_inbox → task_done
- read_shared design/product_spec.md 做基础抽检（文件存在 + 非空 + 含 `## 数据模型` `## 接口契约` 必要节）
- 调 `load_skill("check_review_criteria", task_context={"artifact_path": "/workspace/shared/projects/{pid}/design/product_spec.md", "stage": "product_design", "thresholds": cfg.team_standards.review_insert_product_design})`
- 脚本返回 `{entities: 3, apis: 7, threshold_met: true, reason: "entities>=3 AND apis>=7"}`
- Manager LLM **只读 `threshold_met` 字段**决策，不自己数数字不自己比阈值
- append_event(action="review_criteria_checked", payload={stage: "product_design", metrics: {entities: 3, apis: 7}, thresholds: {...}, threshold_met: true, reason: "..."})
- if threshold_met: append_event(action="decided_insert_review", payload={reviewers: ["rd","qa"]}); else: 直接进 checkpoint（不插评审）

### 2.5 并发发 RD/QA 评审
```
send_mail(to="rd", type_="review_request", subject="评审产品文档",
  content="从 RD 视角评审 design/product_spec.md。按 review_product_design SKILL。输出 reviews/product_design/rd_review.md")
send_mail(to="qa", ...)
```
内部 at cron 分别唤醒 RD 和 QA。append_event(action="review_requested", reviewers=["rd","qa"])

### 2.6 RD 评审
- read_inbox → review_request
- load_skill("review_product_design") reference → 获得 checklist（可实现性 / 性能 / 数据一致性 / 接口完整性）
- read_shared design/product_spec.md
- 按 checklist 写评审
- write_shared `reviews/product_design/rd_review.md`（权限校验通过）
- send_mail(to="manager", type_="review_done", content={conclusion: "pass", path: "..."})
- mark_done 自己的 review_request

### 2.7 QA 评审
并行同上。假设发现 "日期字段时区未规定" → 结论 = need_changes。

### 2.8 Manager 汇总
- Manager 分别被两条 review_done 唤醒
- 首条（RD pass）：append_event(action="review_received", reviewer="rd", result="pass") → 继续等
- 次条（QA need_changes）：两方都到 → 整理 QA 意见发回 PM
```
send_mail(to="pm", type_="task_assign", subject="产品设计修订 (第 2 轮)",
  content="QA 评审发现 2 个问题：...。按 review 修订")
```
append_event(action="revision_requested", round=2)

### 2.9 PM 修订 + 再评审循环
- subject 必须匹配正则 `^.*\(第 (\d+) 轮\)$`（见 §13.2 硬约束）
- 上限 team_standards.review_max_rounds（3）

### 2.10 都 pass → checkpoint
```
send_to_human(type="checkpoint_request", title="产品设计 v2",
  summary="3 实体/7 接口/含移动端适配。RD pass, QA pass",
  artifacts=["design/product_spec.md", "reviews/.../rd_review.md", "reviews/.../qa_review.md"])
```

---

## 阶段 3：RD 设计 + 实现 + 单测

### 3.1 Manager 发 RD 任务
```
send_mail(to="rd", type_="task_assign", subject="技术设计+实现+单测",
  content="""
按 tech_design SKILL 先写 tech/tech_design.md，
再按 code_impl SKILL 实现 code/ + pytest。
硬约束:
- pytest 全 PASS, coverage >= {team_standards.pytest_coverage_min}
- 所有测试用 httpx.Client(app=app), 禁止启 uvicorn
- 前端单文件无构建工具
完成后 task_done 回我。
""")
```
append_event(action="assigned", to="rd", stage="rd_delivery")

### 3.2 RD 技术设计
- read_inbox → task_assign
- load_skill("tech_design") task
- Sub-Crew 沙盒内按模板写 `tech/tech_design.md`（含推荐栈 + 偏离理由 + 分层设计 + 数据库 schema + 接口实现要点 + 依赖 + 风险 + 开放决策回答）
- 自查通过，write_shared

### 3.3 RD 代码实现
load_skill("code_impl") task：
- Sub-Crew 沙盒内 `/workspace/shared/projects/{pid}/code/`：
  - 建目录树（routers/services/models/schemas）
  - **TDD 顺序**：先写 pytest 用例
  - 写 schemas/models/services/routers
  - bash 跑 pytest + coverage → 失败就修（最多 3 轮，超出 error_alert）
  - 前端单文件 HTML+JS+CSS
  - requirements.txt + README.md
- 机械自查：pytest 退出码 0 / coverage 数字 / 每接口 ≥ 1 条单测 / grep 确认无 uvicorn 长期进程

### 3.4 send_mail(task_done)
```
send_mail(to="manager", type_="task_done", content="""
tech/tech_design.md 完成
code/ 完成: 14 单测 PASS, coverage 87%
启动: 仅测试用 httpx.Client(app), 不启后台进程
自查 8 项全过
""")
```
Manager 收到后 append_event(action="rd_delivered")

---

## 阶段 4：QA 走查 + 测试设计 + 执行

### 4.1 代码走查（强制）
```
send_mail(to="qa", type_="review_request", subject="代码走查",
  content="从测试视角走查 code/. 按 review_code SKILL. 重点: 难测路径 / 错误分支 / 边界 case / 日志点. 输出 reviews/code/qa_review.md")
```
QA load_skill("review_code") reference → 按 checklist 走查 → write_shared → send_mail(review_done, conclusion=pass + 非阻塞意见)
Manager 收到：阻塞 → 回 RD 改；非阻塞 → 进 4.2

### 4.2 测试设计
```
send_mail(to="qa", type_="task_assign", subject="测试设计",
  content="读 needs + design + tech_design + code, 产出 qa/test_plan.md. 按 test_design SKILL.")
```
QA load_skill("test_design") task → 按模板（范围 / 策略 / 用例清单 / 数据一致性 / 性能底线）→ 自查（每功能至少 2 用例：正常+异常）→ write_shared

### 4.3 测试执行
```
send_mail(to="qa", type_="task_assign", subject="测试执行",
  content="按 qa/test_plan.md 执行。使用 httpx TestClient，每用例独立 SQLite tmpfile。发现缺陷写 qa/defects/bug_N.md。汇总写 qa/test_report.md")
```
QA load_skill("test_run") task → bash 跑 pytest 集成测试（TestClient 不启 uvicorn）→ 对比 actual vs expected → 缺陷归档 → 写 report

### 4.4 缺陷处理
- 有阻塞缺陷 → Manager 发 RD 修 → QA 回归
- 只有非阻塞 → 记录到 memory，进阶段 5
- 无缺陷 → 进阶段 5

---

## 阶段 5：交付

```
send_to_human(type="delivery", title="项目交付",
  summary="""
✅ 后端 7 接口 / 14 单测 / coverage 87%
✅ QA 15 用例 / 全 PASS / 0 阻塞 / 3 非阻塞建议
✅ 启动: httpx.Client(app=main.app) 直接测试
产物: code/, qa/test_report.md, reviews/
""", artifacts=["code/README.md", "qa/test_report.md"])
```
append_event(action="delivery_requested")
用户 approve → append_event(action="delivered") → 进阶段 6

---

## 阶段 6：团队复盘与进化

### 6.1 团队复盘触发
- `load_skill("team_retrospective")` task → Sub-Crew 读 L1/L2 聚合，返回瓶颈摘要 + "建议对 [pm, rd, qa] 发 retro_trigger"
- Manager 按建议对每角色 send_mail(type=retro_trigger)
- append_event(action="retro_triggered", to=[...])

### 6.2 各角色 self_retrospective（v1.4 对齐 28 课思考框架）
- 醒来 → load_skill("self_retrospective") task
- Sub-Crew 用 `tools/log_query.py` CLI **按需**查询（非固定顺序）：
  ```bash
  python3 tools/log_query.py stats --agent-id pm --days 7
  python3 tools/log_query.py tasks --agent-id pm --days 7 --sort quality_asc --limit 5
  python3 tools/log_query.py steps --task-id t001 --only-failed
  python3 tools/log_query.py l1 --days 7 --keyword "时区"
  ```
- 按 SKILL 的**五个递进问题**分析：
  1. 哪些任务做得差？（看 stats + tasks）
  2. 差在哪一步？（steps 下钻）
  3. 人类怎么看？（l1 交叉验证）
  4. 根因是什么类型？（4 种枚举之一）
  5. 改哪个文件的哪一段？（写 before_text / after_text 锚点）
- 写结构化 JSON 到 `shared/proposals/{agent_id}_retro_{date}.json`（见附录 A2）
- send_mail(to="manager", type_="retro_report", content={path: "shared/proposals/pm_retro_2026-04-20.json", proposals_count: 3})

例：PM 发现 3 条任务都因"日期时区"被退回 → root_cause=sop_gap → target_file=workspace/pm/skills/product_design/SKILL.md → before_text+after_text 给出锚点替换

### 6.3 Manager 预审分档（v1.4 对齐 28 课分档审批）
- Manager 收到 `retro_report` 邮件 → read_inbox → load_skill("review_proposal") reference → 按 §16.1.3 **分档决策** JSON 输出
- 对 improvement_proposals 每条按 target_file 分档：
  - **档 1（memory.md）** → `action=auto_approve`，直接 send_mail(to=proposer_role, type=retro_approved, content={proposal}) + append `retro_approved_by_manager`；每天最多 3 条（硬闸门）
  - **档 2（agent.md / skills/*.md）** → `action=require_human`，加入 pending 列表
  - **档 3（soul.md）** → `action=require_human` + risk_flag=high，加入 pending
- 对档 1 合规失败或超 3 条闸门的提案 → 降级为档 2 等 Human
- 档 2/3 全部 append_event 后汇总：`send_to_human(type="proposal_review", title="..", proposals=pending_list, risk_flag=has_tier3)`

### 6.4 用户逐条审批（档 2/3）
- 飞书卡片按 §12.2.1 结构（每个 proposal 一个复选框 + 全部 Approve / 全部 Reject / 提交）
- 用户回复 → recv_human_response → classify → 写 manager.json 的 checkpoint_response：
  ```json
  {"type": "checkpoint_response", "content": {
      "ck_id": "ck-proposal-2026-04-20",
      "type": "proposals_approve",
      "approved_ids": ["p001", "p002"],
      "rejected_ids": ["p003"]
  }}
  ```
- Manager 被 at cron 唤醒 → 对每个 approved_ids/rejected_ids 分别处理：
  - approved → append `retro_approved_by_human`；send_mail(to=proposer_role, type=retro_approved, content={proposal})
  - rejected → append `retro_rejected_by_human`；send_mail(to=proposer_role, type=retro_rejected, content={proposal, review_notes})

### 6.5 Agent 自行执行改动（v1.4 对齐 28 课，取消 ApplyProposalTool）
提案角色（PM/RD/QA）收到 `retro_approved` 邮件后，按各自 `agent.md` 里的"收到 retro_approved 后"流程**机械执行**（不涉及 LLM 决策）：

```python
# 伪代码（执行体在 Agent kickoff 内）
for proposal in approved_proposals:
    target_path = workspace_root / proposal["target_file"]
    content = target_path.read_text()
    anchor = proposal["before_text"]
    if anchor not in content:
        # 锚点找不到 → 发回 Manager 让提案 Agent 重新产出
        send_mail(to="manager", type_="retro_apply_failed",
                  content={proposal_id, reason: "before_text not found",
                           target_file: proposal["target_file"]})
        continue
    new_content = content.replace(anchor, proposal["after_text"])
    target_path.write_text(new_content)
    # 可选：workspace 若为 git 仓库则 commit
    try:
        subprocess.run(["git", "-C", workspace_root, "add", proposal["target_file"]], check=True)
        subprocess.run(["git", "-C", workspace_root, "commit",
                        "-m", f"[retro][{self._role}] {proposal['proposed_change']}"],
                       check=True)
    except subprocess.CalledProcessError:
        pass  # workspace 非 git 仓库，soft skip
    send_mail(to="manager", type_="retro_applied",
              content={proposal_id, target_file, applied_at})

append_event 由 Manager 收到 retro_applied 后追加："retro_applied_by_{role}"
```

**关键点**：
- **提案角色自己执行**（"谁提案谁执行"）
- **锚点失败**不静默吞——发回 Manager，让提案 Agent 下次复盘时产出更精准的锚点
- **git commit 是可选步骤**（v1.4-5）：workspace 是 git 仓库则自动 commit 留审计轨迹；不是 git 仓库则 soft skip，只写文件

### 6.6 总结
```
send_to_human(type="evolution_report", summary="""
3 条提案 apply:
- PM product_design v1.0 → v1.1.0 [commit abc1]
- RD code_impl v1.0 → v1.1.0 [commit def2]
- QA test_design v1.0 → v1.1.0 [commit ghi3]
下次同类项目将使用新版 SKILL.
""")
```
append_event(action="evolved")。项目归档：events.jsonl 最后一行 action="archived"。

---

# 六、日志、进化、运维

## 25. 三层日志

| 层 | 路径 | 写入 | 生命周期 | 用途 |
|---|---|---|---|---|
| L1（人类纠正） | `workspace/shared/logs/l1_human/{YYYY-MM}.jsonl` | `feishu_bridge.send_to_human()` / `recv_human_response()` 自动 | **跨项目永久** | 最稀缺黄金数据 |
| L2（任务摘要） | `workspace/shared/projects/{pid}/logs/l2_task/{YYYY-MM-DD}.jsonl` | CrewAI `task_callback` hook（§15.4） | 项目结束 +90 天 | 识别瓶颈 |
| L3（ReAct 步骤） | `data/ctx_dir/{session_id}_raw.jsonl` | 22 课 `append_session_raw` 原样 | 滚动 30 天 | 下钻分析 |

**路径唯一性（v1.3-P1-13）**：L3 采用 22 课原样 `ctx_dir/{session_id}_raw.jsonl`（team:{role} 的固定 session_id 已 encode 在 session_id 里，见 §8.3.1），**不**再用 `{role}/sessions/` 形式——两个写法在 v1.2 冲突，v1.3 统一到 `data/ctx_dir/`。

**原则**：
- L1 **只**捕获飞书通道（manager↔human），不包含团队内邮件
- L2 用 `task_callback`，**不**用 `@after_llm_call`
- L2 按 project 分目录，按日切分文件
- L1 跨项目统一目录（累积长期信号）

### 25.1 L1 entry schema（v1.3-P0-1 必填字段）

```json
{
  "ts": "2026-04-20T02:20:00+00:00",
  "action": "checkpoint_request_sent | info_sent | delivery_sent | evolution_report_sent | error_alert_sent | checkpoint_response_received",
  "direction": "outbound | inbound",
  "project_id": "proj-pawdiary-0001",
  "user_open_id": "ou_d683002237d9c5f320cb39af53adff78",
  "role": "manager",
  "ck_id": "ck-001",
  "content": {
    "title": "...",
    "summary": "...",
    "user_text": "确认",
    "classified_as": "approved"
  },
  "artifacts": ["needs/requirements.md"]
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | str | ✅ | ISO 8601 UTC (`+00:00`) |
| `action` | str | ✅ | 枚举见上 |
| `direction` | str | ✅ | `outbound`（Manager→人）\| `inbound`（人→Manager）|
| `project_id` | str\|null | ⚠️ | SOP 共创等没有 project 的场景可为 null |
| `user_open_id` | str | ✅ | 飞书侧 open_id |
| `role` | str | ✅ | 固定 `manager`（单一接口原则） |
| `ck_id` | str\|null | ⚠️ | checkpoint 场景必填 |
| `content` | dict | ✅ | 含 `title` / `summary` / `user_text` / `classified_as` 等上下文字段 |
| `artifacts` | list[str] | ⚠️ | 涉及文件的场景必填 |

### 25.2 L2 entry schema（v1.3-P0-1 必填字段）

```json
{
  "ts": "2026-04-20T02:30:00+00:00",
  "project_id": "proj-pawdiary-0001",
  "role": "pm",
  "session_id": "team-pm-xiaopaw-team-001",
  "task_id": "cb0a1234",
  "trigger": {
    "source_msg_id": "msg-a1b2c3d4",
    "wake_reason": "new_mail"
  },
  "duration_ms": 42357,
  "tokens": {"prompt": 3421, "completion": 896, "total": 4317},
  "tools_used": ["skill_loader", "write_shared", "send_mail"],
  "skills_invoked": [
    {"name": "product_design", "type": "task", "result_status": "success"}
  ],
  "artifacts_produced": ["design/product_spec.md"],
  "self_review_passed": true,
  "result_quality_estimate": 0.82,
  "errors": []
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | str | ✅ | ISO 8601 UTC |
| `project_id` | str\|null | ⚠️ | 同 L1 |
| `role` | str | ✅ | `manager`\|`pm`\|`rd`\|`qa` |
| `session_id` | str | ✅ | 本次 kickoff 的 session_id（§8.3.1） |
| `task_id` | str | ✅ | CrewAI TaskOutput.task_id 或自生成 UUID 前 8 位 |
| `trigger` | dict | ✅ | 触发源：`source_msg_id` 或 `source_wake_id`，`wake_reason` ∈ {feishu, new_mail, heartbeat}|
| `duration_ms` | int | ✅ | kickoff 总耗时 |
| `tokens` | dict | ✅ | LLM token 用量 |
| `tools_used` | list[str] | ✅ | 本轮调用的主 Agent Tool name 列表（去重） |
| `skills_invoked` | list[dict] | ⚠️ | 本轮通过 SkillLoader 加载的 skill 列表 + 结果 |
| `artifacts_produced` | list[str] | ⚠️ | 本轮产出的 shared/ 下文件相对路径 |
| `self_review_passed` | bool | ⚠️ | 自查型 skill 有值（product_design/tech_design/code_impl/test_design/test_run） |
| `result_quality_estimate` | float\|null | ⚠️ | 0.0-1.0，**来源为 Agent 的 self_score skill**（§16.5）；Agent 漏调 skill 时为 null，find_low_quality_tasks 会 skip 此条 |
| `result_quality_breakdown` **v1.4-13** | dict\|null | ⚠️ | 5 维各自分数 `{completeness, self_review, hard_constraints, clarity, timeliness}`，便于复盘 find_low_quality 定位扣分维度 |
| `result_quality_source` **v1.4-13** | str | ✅ | 固定 `self_score_skill`（未来扩展支持 `manager_review`） |
| `errors` | list[str] | ✅ | 空列表表示无错；有错时 Manager 按 sop 决定是否 retry |

可观测性完整规范见 [design-observability.md](./design-observability.md)。

---

## 26. 三档 HITL 与 ApplyProposalTool

复用 28 课三档 + 本课 demo 演示档 1+2：

| 档 | 对象 | 处理 |
|---|---|---|
| 档 1 | memory.md 小条目 | 自动 apply + 硬闸门（`team_standards.tier1_daily_limit` 3/天 / 200 行上限）|
| 档 2 | skill / SOP 模板 | Manager LLM 预审 → 飞书卡片用户 approve → 机械 apply |
| 档 3 | soul.md / 代码 | 本课**不自动**，只列出提案供用户手工决定 |

ApplyProposalTool 执行位置：**宿主机**（主进程 Python，不走沙盒，不走 SkillLoader），理由：
- 要对 workspace/ 做 git commit，沙盒内操作挂载目录有权限/进程交叉问题

---

## 27. 配置与环境

### 27.1 config.yaml（扩展自 22 课）

```yaml
# 22 课基础配置
workspace:
  id: xiaopaw-team-001
  name: "XiaoPaw Team Default"
  root: ./workspace
  shared_protocol: ./workspace/shared/team_protocol.md
  team_standards: ./workspace/shared/config/team_standards.yaml

feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
  user_open_id: ou_d683002237d9c5f320cb39af53adff78    # 本课绑定单个甲方

agent:
  model: qwen3-max
  max_iter: 50
  sub_agent_max_iter: 20
  timeout_s: 300

sandbox:
  shared:
    image: aio-sandbox:latest
    url: http://localhost:8022/mcp
    mount: ./workspace:/workspace
    timeout_s: 120

session:
  max_history_turns: 20

runner:
  queue_idle_timeout_s: 300
  max_queue_size: 10

sender:
  max_retries: 3
  retry_backoff: [1, 2, 4]

debug:
  enable_test_api: false
  test_api_port: 9090

# 29 课新增
team:
  roles: [manager, pm, rd, qa]
  wake_cron_interval_sec: 30
  wake_cron_jitter_sec: 5
  stale_timeout_sec: 900       # reset_stale 本课不启用
```

### 27.2 team_standards.yaml（v1.1 集中阈值）

```yaml
pytest_coverage_min: 0.80
review_max_rounds: 3
review_insert_product_design:
  min_entities: 3
  min_apis: 7
review_insert_tech_design:
  min_lines_estimated: 500
review_test_plan_threshold:
  min_cases: 10
max_blast_radius: 5
tier1_daily_limit: 3
tier1_size_limit_lines: 200
min_tasks_for_retro: 5
self_repair_max_rounds: 3       # RD pytest 自修上限
event_tail_window: 100          # read_project_state 默认 tail
```

SKILL.md 通过变量引用：`{team_standards.pytest_coverage_min}` → 加载时替换为实际值。

### 27.3 pgvector-docker-compose.yaml（22 课原样）

```yaml
services:
  pgvector:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: xxx
    ports:
      - "5432:5432"
    volumes:
      - ./data/pgvector:/var/lib/postgresql/data
```

---

## 28. 运维与部署

### 28.1 部署架构（扩展 22 课）

```
主机
├── xiaopaw-team/          ← 主进程（Python）
│   ├── data/              ← 持久化数据（挂载给 Docker）
│   └── workspace/         ← 独立 git 仓库（挂载给 Docker + 宿主机 apply_proposal）
└── docker-compose.yml

Docker 容器
├── aio-sandbox            ← AIO-Sandbox MCP Server
│   └── /workspace         ← 挂载自主机 xiaopaw-team/workspace/
└── pgvector               ← 22 课 memories 表
```

### 28.2 sandbox-docker-compose.yaml（扩展 17 课）

```yaml
services:
  aio-sandbox:
    image: ghcr.io/agent-infra/sandbox:latest
    ports:
      - "8022:8080"
    volumes:
      - ./xiaopaw_team/skills:/mnt/skills:ro
      - ./workspace:/workspace:rw            # 整体 workspace 挂载
      - ./data/cron:/workspace/.cron:rw
    restart: unless-stopped
```

### 28.3 启动命令

**首次安装**（一次性）：
```bash
# 1. 沙盒
docker-compose -f sandbox-docker-compose.yaml up -d

# 2. pgvector（可选，启动后建表）
docker-compose -f pgvector-docker-compose.yaml up -d

# 3. workspace 初始化为独立 git 仓库（apply_proposal 需要）
cd workspace
git init
git add .
git commit -m "workspace baseline v1.0"
cd ..

# 4. 启动主进程
python -m xiaopaw_team.main
```

**日常启动**：
```bash
docker-compose -f sandbox-docker-compose.yaml up -d
python -m xiaopaw_team.main
```

main.py 启动序列：
1. 加载 config + team_standards
2. **校验 workspace/.git/ 存在**（apply_proposal 要求）——缺失时 log.warning 并设置 `cfg.features.apply_proposal_enabled=False`，进程继续启动（§7.2 详述）
3. 构造 4 agent_fn（含 asyncio.Lock 包裹的 Manager）
4. 注册 4 × every 30s heartbeat cron
5. 启 FeishuListener + Runner + CronService + CleanupService + metrics
6. 事件循环

### 28.4 存储清理策略（扩展 22 课）

22 课原策略（workspace/sessions/ 下 tmp/uploads/outputs）+ 29 课新增：
- `shared/projects/{pid}/` 在项目归档（events.jsonl 最后 action=archived）后 90 天清理 project 子目录
- `shared/logs/l1_human/` **永久保留**
- `shared/projects/{pid}/logs/l2_task/` 随 project 90 天

---

## 29. 安全设计

（扩展自 22 课 §9 安全设计）

| 原则 | 17/22 课 | 29 课补充 |
|------|---------|---------|
| Credentials 不进模型 | ✓ | 无新增 |
| 沙盒工具约束 | ✓（backstory 行为约束）| workspace 目录权限在工具层强制（见 §11.2） |
| Session 隔离 | ✓ | **多角色 session**：每角色独立 session_id（p2p:ou_xxx 是用户 session，team:{role} 是团队系统 session） |
| 文件目录隔离 | ✓ | 按 OWNER_BY_PREFIX 表在工具层校验 |
| Bot 回复不走 Skill | ✓ | FeishuSender 只注入 Manager，不注入其他角色 |
| 幂等发送 | ✓（uuid）| events.jsonl 用 seq 严格递增；邮箱三态状态机防重复处理 |
| 测试 API 隔离 | ✓ | 同 |

### 29.1 单一接口架构保证（P2-15 checklist）

**3 重架构保证** 每一重都可以写成一条测试：

| # | 保证点 | 代码位置 | 测试断言 |
|---|--------|---------|---------|
| 1 | FeishuListener 入站路由 | `feishu/listener.py` + `feishu_bridge.recv_human_response` | 飞书消息的 routing_key 只能 resolve 成 `p2p:{open_id}`（Manager 接管），绝不 resolve 成 `team:pm/rd/qa` |
| 2 | FeishuSender 实例注入 | `main.py` → `build_role_tools(role="manager", sender=sender)` vs `build_role_tools(role="pm/rd/qa", sender=None)` | `assert all("feishu_sender" not in inspect.signature(build_role_tools).bind(role=r, cfg=cfg).arguments for r in ["pm","rd","qa"])` |
| 3 | SendToHumanTool 只在 Manager 工具列表 | `build_role_tools()` 内 `if role == "manager": tools.append(SendToHumanTool(...))` | `assert any(isinstance(t, SendToHumanTool) for t in manager_tools)`；`assert not any(isinstance(t, SendToHumanTool) for t in pm_tools/rd_tools/qa_tools)` |

**逆向试探**（test-design T-UI-04 对应）：
- PM LLM 试图调用 `send_to_human(...)` → CrewAI 报 "Tool not found: send_to_human"（因为工具 XML 里根本没有）
- PM 试图直接拿 `feishu_sender.send_card(...)` → Python `AttributeError: 'NoneType' object has no attribute 'send_card'`（构造器根本没传 sender）

架构级保证，不是 LLM 自律——没有"希望 LLM 不会绕过"的信念，只有"对象层面传不进去"的物理保证。

### 29.2 workspace 权限保证

`WriteSharedTool` 在写入前 check_write(role, rel_path)：
- 按 prefix 判断 Owner（见 §11.2 表）
- reviews/ 目录用正则校验文件名必须以自己 role 开头
- 违规 → PermissionError

---

## 30. 对 xiaopaw-with-memory 的改动清单

### 30.1 完全复用（0 改动）

- `feishu/` 全部（listener / downloader / session_key）
- `session/` 全部
- `memory/context_mgmt.py`
- `cleanup/service.py` 核心逻辑（扩展初始化但不改核心）
- `observability/` 全部
- `api/test_server.py`
- `llm/aliyun_llm.py`
- `agents/skill_crew.py`

### 30.2 改动清单（本课修订）

| 模块 | 改动 | 行数估计 |
|------|------|---------|
| `runner.py` | `team:{role}` routing_key 路由；cron wake 去重；InboundMessage.meta.wake_reason；Runner.__init__ 新增 `agent_fn_map: dict[str, AgentFn] \| None` 参数；dispatch 按前缀查表；`resolve_session_id` 对 team:{role} 返回固定 id | ~60 |
| `feishu/sender.py` | 新增 `send_card(type, title, summary, artifacts)` 6 种卡片类型 | ~60 |
| `main.py` | 从 config 构造 4 agent_fn + asyncio.Lock + 4 heartbeat cron（写 tasks.json）+ team_standards 加载 + workspace git 检查 + SkillLoader mtime 监控协程 | ~120 |
| `agents/main_crew.py` | MemoryAwareCrew 构造加 `role` / `workspace_root` / `extra_tools: list[BaseTool]` 参数；tools 列表 = `[SkillLoaderTool(...), *extra_tools]`；task_callback 挂载 L2 写入钩子；`_get_current_project_id` 推断 | ~80 |
| `tools/skill_loader.py` | 四项扩展（~130 行）：参数化 skills_dir+sandbox_skills_mount / 4 份 manifest (kind+owner_role) / `{team_standards.X}` 变量替换 / mtime 热重载 + cache invalidate | ~130 |
| `memory/indexer.py` | `async_index_turn` 新增 role + project_id 参数 | ~40 |
| `memory/bootstrap.py` | `build_bootstrap_prompt(workspace_dir, shared_protocol=None)` 扩展支持可选第 5 文件注入 | ~15 |
| `session/manager.py` | `resolve_session_id` 对 team:{role} 返回固定 id（或 runner.py 内处理） | ~10 |

### 30.3 全新文件

- `xiaopaw_team/tools/mailbox.py` / `event_log.py` / `workspace.py` / `feishu_bridge.py` / `create_project.py` / `log_hooks.py`（≈ 600 LOC，**v1.4 删 apply_proposal.py**）
- `xiaopaw_team/tools/log_query.py` **v1.4 新增**：28 课复盘的统一查询 CLI，子命令 `stats / tasks / steps / l1 / all-agents`；各角色 self_retrospective Sub-Crew 内通过 `sandbox_execute_bash` 调用（~200 LOC）
- `xiaopaw_team/tools/proposal_ops.py` **v1.4 新增**：读写 `shared/proposals/{agent_id}_retro_{date}.json` + 对 `improvement_proposals` 做基础 schema 校验（~100 LOC）
- `xiaopaw_team/agents/build.py`（agent_fn 工厂 + Manager 锁包装，~120 LOC）
- **`xiaopaw_team/tools/build_role_tools.py`**（~80 LOC）：按 role 和 cfg 组装 tools 列表
  ```python
  def build_role_tools(role: str, cfg: Config, 
                       sender: FeishuSender | None, 
                       tasks_json_path: Path) -> list[BaseTool]:
      tools = [
          SkillLoaderTool(role=role, 
                          skills_dir=cfg.workspace.root / role / "skills",
                          sandbox_skills_mount=f"/workspace/{role}/skills",
                          team_standards=cfg.team_standards),
          SendMailTool(tasks_json_path),        # 内部写 at cron
          ReadInboxTool(),
          MarkDoneTool(),
          ReadSharedTool(cfg.workspace.root),
          WriteSharedTool(role=role, workspace_root=cfg.workspace.root),
      ]
      if role == "manager":
          assert sender is not None, "manager 必须注入 feishu_sender"
          tools.extend([
              CreateProjectTool(cfg.workspace.root),
              AppendEventTool(),
              SendToHumanTool(sender=sender, user_open_id=cfg.feishu.user_open_id),
              ApplyProposalTool(workspace_root=cfg.workspace.root),
          ])
      return tools
  ```
  非 Manager 角色**不接受 sender 参数**，从对象层面防止单一接口泄漏。
- 4 × `workspace/{role}/{soul,agent,memory,user}.md`（文档模板）
- `workspace/shared/team_protocol.md`
- `workspace/shared/config/team_standards.yaml`
- 4 份 `workspace/{role}/skills/load_skills.yaml`（manifest）
- **v1.4 共 27 个 SKILL.md**（Manager 11 / PM 4 / RD 6 / QA 7 + shared self_score × 1）+ task 型 skill 的 scripts

### 30.4 pgvector 表结构变更

```sql
ALTER TABLE memories ADD COLUMN role VARCHAR(16);
ALTER TABLE memories ADD COLUMN project_id VARCHAR(64);
CREATE INDEX idx_memories_role_project ON memories(role, project_id);
```

`async_index_turn(session_id, role, project_id, routing_key, ...)` 写入时带 metadata。Manager 查询可 `WHERE role IN (...) AND project_id IN (...)`。

---

## 31. 测试与里程碑

### 31.1 里程碑

| M | 目标 | 验收 |
|---|---|---|
| M1 | 代码骨架 + 4 Agent 启动 | main.py 启动无报错；asyncio.Lock 正确；4 个 heartbeat cron 注册 |
| M2 | 工具层 + 邮箱链路（无 LLM） | test_mailbox_chain.py：send → read → mark 无锁冲突 |
| M3 | 事件流推断 state（无 LLM） | test_project_state.py：append 不同 event → read_project_state 摘要正确；崩溃半写自愈生效 |
| M4 | 唤醒链路（无 LLM） | test_wake_chain.py：send_mail 后 1s 内 Runner 收 team:{role}；heartbeat 去重生效 |
| M5 | 飞书桥 + Manager 澄清 checkpoint（有 LLM） | 发任务 → 澄清 → 写需求 → checkpoint → 用户确认 全过 |
| M6 | 端到端 6 阶段（有 LLM、真代码） | test_end_to_end.py：模拟用户 → 跑完 6 阶段 → pawdiary pytest 全 PASS |
| M7 | 复盘 + apply_proposal + git commit | test_evolution.py：seed L1/L2 → 提案 → approve → workspace git diff |

### 31.2 关键集成测试

- test_project_state.py：事件流推断鲁棒性
- test_cron_dedup.py：at + heartbeat 同时到不多跑
- test_role_isolation.py：权限表（PM 写 code/ 被拒、QA 写 reviews/code/rd_* 被拒）
- test_single_interface.py：PM/RD/QA 的 Crew 构造器不能注入 feishu_sender
- test_manifest_reload.py：sop_write 写 SKILL.md + 追加 manifest → 热重载 → Manager 下次看到

---

# 附录

## 附录 A · 事件流 events.jsonl 结构

`shared/projects/{pid}/events.jsonl` 是 **append-only** JSON Lines。

### A.1 通用字段（每条事件都有）

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `ts` | str | ✅ | **ISO 8601 UTC `+00:00` 后缀**（v1.3-P0-6），绝不用 naive 时间或 `+08:00` |
| `seq` | int | ✅ | 从 1 起严格递增，不重复、不跳号 |
| `actor` | str | ✅ | 固定 `"manager"`（单一写入者，§11.4） |
| `action` | str | ✅ | 枚举见 A.2 |
| `payload` | dict | ✅ | 可为 `{}`（无内容事件），但字段必须存在 |

### A.2 示例

```json
{"ts":"2026-04-20T02:00:00+00:00","seq":1,"actor":"manager","action":"project_created","payload":{"project_id":"proj-pawdiary-0001","sop":"sop_feature_dev","user_open_id":"ou_d683...","created_at":"2026-04-20T02:00:00+00:00"}}
{"ts":"2026-04-20T02:00:05+00:00","seq":2,"actor":"manager","action":"requirements_discovery_started","payload":{}}
{"ts":"2026-04-20T02:05:00+00:00","seq":3,"actor":"manager","action":"requirements_coverage_assessed","payload":{"dimensions":{"goal":"...","boundary":"...","constraint":"...","risk":"..."},"covered":4,"complete":true}}
{"ts":"2026-04-20T02:07:00+00:00","seq":4,"actor":"manager","action":"requirements_drafted","payload":{"artifact":"needs/requirements.md","skill_used":"requirements_write"}}
{"ts":"2026-04-20T02:07:05+00:00","seq":5,"actor":"manager","action":"checkpoint_requested","payload":{"ck_id":"ck-001","stage":"requirements","title":"需求文档 v1","artifacts":["needs/requirements.md"]}}
{"ts":"2026-04-20T02:12:00+00:00","seq":6,"actor":"manager","action":"checkpoint_reply_classified","payload":{"ck_id":"ck-001","user_text":"确认","classified_as":"approved","classify_source":"text_exact_match"}}
{"ts":"2026-04-20T02:12:01+00:00","seq":7,"actor":"manager","action":"checkpoint_approved","payload":{"ck_id":"ck-001","decision":"approved"}}
...
{"ts":"2026-04-20T03:30:00+00:00","seq":N,"actor":"manager","action":"archived","payload":{"final_state":"delivered+evolved","summary":"..."}}
```

### A.3 action 枚举完整表（v1.3-P2-17 标注 required/optional）

**R** = required，**O** = optional。未列字段默认不允许出现。

#### 项目生命周期
| action | payload 字段 |
|--------|-------------|
| `project_created` | `project_id`(R), `sop`(R), `user_open_id`(R), `created_at`(R) |
| `archived` | `final_state`(R), `summary`(O), `total_events`(O) |

#### 需求阶段（§阶段 1）
| action | payload 字段 |
|--------|-------------|
| `requirements_discovery_started` | `{}` |
| `requirements_coverage_assessed` **🆕 P1-7** | `dimensions.{goal,boundary,constraint,risk}`(R), `covered`(R int), `complete`(R bool) |
| `requirements_drafted` | `artifact`(R), `skill_used`(O) |

#### checkpoint（全流程通用）
| action | payload 字段 |
|--------|-------------|
| `checkpoint_requested` | `ck_id`(R), `stage`(R), `title`(O), `artifacts`(O list), `summary`(O) |
| `checkpoint_reply_classified` **🆕 P1-7** | `ck_id`(R), `user_text`(R), `classified_as`(R enum: approved/rejected/need_discussion/proposals_partial), `classify_source`(R enum: button_callback/text_exact_match/token_set_match), `approved_ids`(O list, proposals 场景), `rejected_ids`(O list) |
| `checkpoint_approved` | `ck_id`(R), `decision`(R, 固定 "approved") |
| `checkpoint_rejected` | `ck_id`(R), `decision`(R, 固定 "rejected"), `reason`(O) |

#### 任务流转
| action | payload 字段 |
|--------|-------------|
| `assigned` | `to`(R enum), `stage`(R), `msg_id`(R), `subject`(O) |
| `task_done_received` | `from`(R enum), `artifact`(O str\|list), `result_summary`(O), `metrics`(O dict) |
| `revision_requested` | `to`(R), `round`(R int ≥ 2), `stage`(R), `comments`(O list) |
| `rd_delivered` | `artifacts`(R list), `code_impl_metrics`(O dict containing pytest_attempts/coverage/pytest_final_status) |

#### 评审
| action | payload 字段 |
|--------|-------------|
| `review_criteria_checked` **🆕 P0-4** | `stage`(R), `metrics`(R dict), `thresholds`(R dict), `threshold_met`(R bool), `reason`(R), `insert_review`(R bool) |
| `decided_insert_review` | `reviewers`(R list), `stage`(R) |
| `review_requested` | `reviewers`(R list), `stage`(R) |
| `review_received` | `reviewer`(R enum), `result`(R enum: pass/need_changes), `path`(R) |

#### 交付
| action | payload 字段 |
|--------|-------------|
| `delivery_requested` | `summary`(R), `artifacts`(R list) |
| `delivered` | `{}` |

#### 复盘进化（§阶段 6，v1.4 对齐 28 课重写）
| action | payload 字段 |
|--------|-------------|
| `retro_triggered` | `to`(R list) |
| `retro_report_received` **🆕 v1.4** | `from`(R, proposer_role), `proposals_path`(R), `proposals_count`(R int) |
| `retro_proposal_invalid` **🆕 v1.4** | `proposal_idx`(R int), `reason`(R enum: evidence_empty/target_file_not_exist/root_cause_not_enum/before_text_empty/after_text_empty), `detail`(O) |
| `retro_approved_by_manager` **🆕 v1.4** | `proposer_role`(R), `proposal_idx`(R), `tier`(R int 1-3), `target_file`(R) |
| `retro_approved_by_human` **🆕 v1.4** | `proposer_role`(R), `proposal_idx`(R), `tier`(R int 2-3), `target_file`(R) |
| `retro_rejected_by_human` **🆕 v1.4** | `proposer_role`(R), `proposal_idx`(R), `tier`(R int 2-3), `review_notes`(O) |
| `retro_applied_by_{role}` **🆕 v1.4** | `proposal_idx`(R), `target_file`(R), `commit_sha`(O str\|null) |
| `retro_apply_failed` **🆕 v1.4** | `proposer_role`(R), `proposal_idx`(R), `reason`(R, 固定"before_text_not_found"), `target_file`(R) |
| `task_quality_adjusted` **🆕 v1.4-13** | `task_id`(R), `role`(R), `adjustment`(R float), `reason`(R, 如"checkpoint_rejected"/"review_need_changes") |
| `evolved` | `approved_count`(R int), `applied_count`(R int), `failed_count`(O int), `summary`(O) |

**取消的事件（相对 v1.3）**：`proposal_received` / `proposal_rejected` / `proposal_applied` / `proposal_apply_failed` / `proposal_rejected_by_user` / `retro_quorum_checked`——这些都基于 v1.3 的 accept/reject 二分模型，v1.4 改用分档事件替代。

#### 异常与自愈
| action | payload 字段 |
|--------|-------------|
| `error_alert_raised` | `source_role`(R), `error_type`(R), `msg`(R), `recoverable`(O bool) |
| `recovered_checkpoint_response` | `ck_id`(R), `recovered_from`(R, 固定 "mailbox") |

---

## 附录 A2 · RetroProposal schema（v1.4 重写，对齐 28 课）

角色 self_retrospective 或 Manager team_retrospective 产出的结构化复盘文件，存储路径：

```
workspace/shared/proposals/{agent_id}_retro_{YYYY-MM-DD}.json
```

整体由 **retrospective_report**（本周分析总结）+ **improvement_proposals**（最多 3 条改动提案）两段构成：

```json
{
  "retrospective_report": {
    "agent_id": "pm",
    "period": "2026-04-13 ~ 2026-04-20",
    "generated_at": "2026-04-20T03:20:00+00:00",
    "summary": "本周 PM 8 个任务平均 0.68，3 个 checkpoint 被退回，主因都是 product_spec 漏了日期字段时区说明",
    "findings": [
      {
        "pattern": "产品文档缺日期时区约束",
        "evidence_task_ids": ["t001", "t003", "t006"],
        "l1_corroboration": "shared/logs/l1_human/2026-04.jsonl#L127 用户三次反馈'时区没说清'"
      }
    ]
  },
  "improvement_proposals": [
    {
      "root_cause": "sop_gap",
      "target_file": "workspace/pm/skills/product_design/SKILL.md",
      "current_behavior": "当前 product_design SKILL 的数据模型章节没要求日期字段声明时区",
      "proposed_change": "在数据模型章节加一条硬约束：'所有日期字段必须标注时区（默认 UTC +00:00）'",
      "before_text": "## 4. 数据模型\n### 实体 1: Pet\n| 字段 | 类型 | 必填 |",
      "after_text": "## 4. 数据模型\n\n**硬约束**：所有日期/时间字段必须标注时区（默认 UTC +00:00）。\n\n### 实体 1: Pet\n| 字段 | 类型 | 必填 |",
      "expected_improvement": "product_spec checkpoint 通过率 60% → 90%",
      "evidence": ["t001", "t003", "t006"]
    }
  ]
}
```

### A2.1 retrospective_report 字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `agent_id` | str | ✅ | 枚举 pm / rd / qa / manager（team_retrospective 用 manager） |
| `period` | str | ✅ | 格式 `YYYY-MM-DD ~ YYYY-MM-DD`，默认过去 7 天 |
| `generated_at` | str | ✅ | ISO 8601 UTC `+00:00` |
| `summary` | str | ✅ | 一句话总结本期主要问题 |
| `findings` | list[dict] | ✅ | 非空；每条含 `pattern` / `evidence_task_ids` / `l1_corroboration` |

### A2.2 improvement_proposals 字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `root_cause` | str | ✅ | 枚举：`sop_gap` / `prompt_ambiguity` / `ability_gap` / `integration_issue` |
| `target_file` | str | ✅ | 相对仓库根的路径；限定在 `workspace/{own_role}/` 下（team_retrospective 可跨 Agent） |
| `current_behavior` | str | ✅ | 人类可读的当前行为描述 |
| `proposed_change` | str | ✅ | 人类可读的变更描述 |
| `before_text` | str | ✅ | **用于在 target_file 内定位的锚点原文**（不要整个文件，只要那段） |
| `after_text` | str | ✅ | 替换后的**完整文本**（包括保留的上下文） |
| `expected_improvement` | str | ✅ | 预期指标变化（如 "checkpoint 通过率 60% → 90%"）|
| `evidence` | list[str] | ✅ 非空 | task_id 列表（来自 L2 / L3 日志） |

### A2.3 约束（与 28 课一致）

- **improvement_proposals 数量 ≤ 3**：聚焦最重要的改进，避免一次性大改动
- **evidence 非空**：每条提案至少 1 个 task_id 支撑
- **target_file 限 own 文件**：self_retrospective 只能改 `workspace/{agent_id}/...`（agent.md / soul.md / memory.md / skills/*.md）；team_retrospective 可跨 Agent 但要标注依据
- **样本不足则跳过**：task_count < `team_standards.min_tasks_for_retro`（默认 5）→ 只产出 `retrospective_report`，improvement_proposals 为空数组
- **不自己执行**：Agent 只产出方案，Manager 审批通过后 Agent **再自己**机械替换执行（不是 Manager 帮 apply）

### A2.4 root_cause 枚举 → target_file 对应关系

| root_cause | 含义 | 对应改动对象 |
|------------|------|-------------|
| `sop_gap` | 流程/SOP 缺步骤 | agent.md 或 skills/*.md |
| `prompt_ambiguity` | 提示词/决策偏好模糊 | soul.md |
| `ability_gap` | 知识/经验不足 | memory.md |
| `integration_issue` | 与其他 Agent 协作问题 | agent.md（团队名册/协作章节） |

Agent 在 self_retrospective 中必须**根据 root_cause 选对 target_file**（提示 Agent：`root_cause=prompt_ambiguity` 的提案不该改 memory.md，会被 review_proposal 预审拒绝）。

### A2.5 **取消**的字段（相对 v1.3）

以下字段 v1.3 有但 v1.4 删除（对齐 28 课新设计）：
- `proposal_id`（不再需要，每条提案在数组下标就能唯一标识）
- `proposer_role`（文件名 `{agent_id}_retro_{date}.json` 已含）
- `title`（合并到 `proposed_change`）
- `checksum_before`（取消 SHA256 校验，改成 before_text 锚点）
- `blast_radius`（每条提案固定只改 1 个 target_file，不需要这个字段）
- `generated_at`（移到 retrospective_report 层）

### A2.6 apply 路径（v1.4 改用 before_text 锚点）

没有 checksum 校验，执行时：
1. Agent 读 target_file 当前内容
2. 用 `before_text` 在文件里做**精确匹配**定位（字符串完全相等）
3. 找到 → 替换为 `after_text` → 写回
4. 找不到 → 报错给 Manager，Manager 要 Agent 重新产出提案

这比 checksum 更适合"Agent 自己复盘自己执行"的场景：不需要提前算 hash、不需要防并发写（Agent 自己在单独 kickoff 里操作自己的文件）。缺点是对"文件中途被别的进程改过"不敏感，但 29 课单进程场景下 target_file 的 Owner 只有 Agent 自己，这个缺点不存在。

---

## 附录 B · 邮箱消息 type 枚举

| type | 发起方 | 接收方 | 说明 |
|------|-------|-------|------|
| `task_assign` | Manager | PM / RD / QA | 分配任务 |
| `task_done` | PM / RD / QA | Manager | 任务完成回执 |
| `review_request` | Manager | PM / RD / QA | 请求评审某产出 |
| `review_done` | PM / RD / QA | Manager | 评审完成（content 含 `{conclusion: pass\|need_changes, path}`） |
| `clarification_request` | PM / RD / QA | Manager | 对任务有疑问请 Manager 澄清 |
| `clarification_answer` | Manager | PM / RD / QA | 回答疑问 |
| `error_alert` | 任意角色 | Manager | 异常上报 |
| `checkpoint_response` | feishu_bridge（特殊 from） | Manager | 用户飞书回复自动写入；content 为 dict 含 `{ck_id, type, text \| approved_ids, classified_as}` |
| `retro_trigger` | Manager | PM / RD / QA | 触发自我复盘 |
| `retro_report` **v1.4** | PM / RD / QA | Manager | 上报自我复盘结果；content = `{proposals_path, proposals_count, summary}` |
| `retro_approved` **v1.4** | Manager | PM / RD / QA | 通知某条 improvement_proposal 已通过审批，可以机械执行；content = `{proposal}` (单条) |
| `retro_rejected` **v1.4** | Manager | PM / RD / QA | 通知某条提案被拒；content = `{proposal, review_notes}` |
| `retro_applied` **v1.4** | PM / RD / QA | Manager | 执行完毕确认；content = `{proposal_idx, target_file, commit_sha \| null, applied_at}` |
| `retro_apply_failed` **v1.4** | PM / RD / QA | Manager | 机械执行失败（before_text 锚点不匹配）；content = `{proposal_idx, target_file, reason}` |

**取消（相对 v1.3）**：`retro_proposal`（单条提案邮件）被 `retro_report`（一次性发包含多条的 JSON 文件路径）替代；v1.4 改成"一次复盘一个文件一封邮件"。

**from 字段完整枚举**（v1.3-P0-6）：
- `manager` / `pm` / `rd` / `qa`：团队角色
- `human`：用户本人（暂未用，`checkpoint_response` 统一用 `feishu_bridge` 代表）
- `feishu_bridge`：系统组件代表用户侧入站消息（唯一非角色 from）

**timestamp 字段**（v1.3-P0-6）：统一 ISO 8601 UTC 带 `+00:00` 后缀，示例 `"2026-04-20T02:00:00+00:00"`。

**id 字段格式**：`^msg-[0-9a-f]{8}$`，由 SendMailTool 内部调 `uuid4().hex[:8]` 生成。

---

## 附录 C · Skill frontmatter 规范

```yaml
---
name: <skill_name>                       # 与目录名一致
description: <一句话含触发关键词>         # SkillLoader 汇总进工具描述
type: reference | task                   # reference=返回文本；task=启动 Sub-Crew
kind: sop | base                         # v1.1 新增：sop 标识主流程 SKILL
version: 1.0.0                           # apply_proposal 自动 +0.1 minor
owner_role: manager | pm | rd | qa | any # v1.1 新增：限定哪些角色可加载
---
```

`owner_role` 让 SkillLoader 在构造工具描述时按角色过滤——PM LLM 根本看不到 owner_role=manager 的 description 条目。

### C.1 description 三要素规范（v1.5-A5）

每个 SKILL.md 的 `description` 字段必须含以下三要素（缺一不可）：

| 要素 | 作用 | 写法 |
|------|------|------|
| **触发源/场景** | 让主 Agent 一眼知道"什么时候该用"；是 SkillLoader 自动匹配的关键信号 | "收到 type=X 的邮件时"、"被问到 Y 时"、"kickoff 第一步必调"、"task_done 前无条件调用" |
| **能力描述（动词+名词）** | 说清"做什么" | "评审产品文档"、"生成 requirements.md"、"查询事件流"、"5 维自评打分" |
| **产出暗示** | 让主 Agent 知道"调完能拿到什么"，便于串联 | "返回 JSON `{entities, apis, threshold_met}`"、"返回文本 checklist + 结论模板"、"写 `needs/requirements.md` + 返回产物路径" |

**正例**：

✅ `"评审产品文档（QA 视角）。收到 type=review_request 且 target=design/product_spec.md 时加载；审可测性 / 验收标准可机械检查 / 边界 case / 错误契约；返回 checklist + conclusion(pass|need_changes)"`

**反例**：

❌ `"评审产品文档, 可测性"`（只有关键词，不说何时触发、不说产出格式）
❌ `"处理用户 checkpoint 回复"`（缺触发源、缺产出）
❌ `"帮用户解决问题"`（三要素全无）

### C.2 长度约束

- description 建议 ≤200 字符（SkillLoader 会在超长时截断到 200 + `...`）
- 若含代码示例 / 多行模板，放 SKILL.md 正文，不放 frontmatter
- 中英文混合不受惩罚，但**触发词用中文英文都行**（SkillLoader 对 LLM 匹配用两种都可）

### C.3 命名规范

- skill 目录名 = frontmatter `name` = snake_case 英文
- 动词 + 名词（preferred）：`list_available_sops`、`write_product_design`、`review_code`
- 名词 only（仅单一产物时）：`sop_feature_dev`、`user_profile_fetcher`
- **禁止**：选择性 / 判断性名词表达 task 型行为（例：`sop_selector` 暗示"选择"但其实只是"列出"——v1.5-A3 已修）
- **跨角色同名 skill**（如 review_*）必须带视角后缀消歧：`review_{artifact}_from_{perspective}`（v1.5-A2 已修）

---

## 附录 C2 · task skill 返回值约定（v1.3-P1-8 新增）

**所有 task 型 skill 的 Sub-Crew.kickoff 必须返回 JSON 字符串**（不是自由文本）。主 Agent 收到后 `json.loads(result)` 拿到结构化数据做决策。

### C2.1 通用字段（每个 task skill 返回都必含）

```json
{
  "status": "success" | "partial" | "failed",
  "artifacts": [
    {"path": "design/product_spec.md", "kind": "doc", "size_bytes": 2341}
  ],
  "metrics": {...},
  "errors": []
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | str | ✅ | success / partial（部分产物）/ failed（完全失败） |
| `artifacts` | list[dict] | ✅ | 每条含 `path`(相对 workspace) + `kind`(doc/code/report) + `size_bytes` |
| `metrics` | dict | ✅ | task 专属指标（见下） |
| `errors` | list[str] | ✅ | 空列表表示无错；非空时 status 应为 partial 或 failed |

### C2.2 按 skill 特化的 metrics 字段

| skill | metrics 必填字段 |
|-------|-----------------|
| `requirements_write` | `word_count`, `dimensions_covered`(4) |
| `product_design` | `word_count`, `entities`, `apis`, `self_review_passed`(bool), `self_review_checklist`(dict) |
| `tech_design` | `word_count`, `self_review_passed`, `tech_stack`(dict), `deviation_from_default`(bool) |
| `code_impl` **P2-19** | `pytest_attempts`(int), `pytest_final_status`(pass/fail), `coverage`(float), `lines_added`(int), `files_written`(int), `self_review_passed`(bool) |
| `test_design` | `test_cases_count`(int), `self_review_passed` |
| `test_run` | `cases_passed`, `cases_failed`, `defects_count`(含 blocking/non-blocking 拆分), `coverage` |
| `self_retrospective` **v1.4** | `proposals_path`(str), `findings_count`(int), `proposals_count`(int), `root_causes`(dict count by type), `sample_size_task_count`(int), `skipped_due_to_low_sample`(bool) |
| `team_retrospective` **v1.4** | `bottleneck_roles`(list), `cross_agent_patterns`(list[str]), `next_actions`(list: 对哪些 role 发 retro_trigger), `proposals_path`(str\|null, 如果 Manager 自己也产出了跨 Agent 提案) |
| `check_review_criteria` | `entities`, `apis`, `threshold_met`(bool), `reason` |
| `sop_write` | `sop_name`, `skill_md_path`, `manifest_updated`(bool) |
| `list_available_sops` **v1.5** | `sops`(list of `{name, description, kind}`), `total_count`(int) — 不含选择结果，Manager LLM 自己做语义匹配 |
| `read_project_state` | `latest_action`, `event_count`, `has_pending_checkpoint`(bool), `self_healed_events`(int) |

### C2.3 Manager 解析失败的兜底

如果 Sub-Crew 返回不是合法 JSON（极少见，LLM 漂移）：
- 主 Agent 代码层 try/except `json.JSONDecodeError`
- 降级：把原始字符串当 `{"status": "unknown", "errors": ["non-json"], "raw": "<str>"}` 处理
- append `error_alert_raised` 事件（source_role=当前 role, error_type=skill_result_not_json）

---

## 附录 D · 每个数字员工的完整清单

### Manager

**Skills**（11，v1.5 命名对齐）：sop_cocreate_guide (ref) / sop_write (task) / **list_available_sops** (task) / sop_feature_dev (ref, kind=sop) / requirements_guide (ref) / requirements_write (task) / read_project_state (task) / check_review_criteria (task) / handle_checkpoint_reply (ref) / team_retrospective (task) / **review_proposal** (ref)

**Tools**（10）：SkillLoaderTool / SendMailTool / ReadInboxTool / MarkDoneTool / ReadSharedTool / WriteSharedTool（限 needs/ + reviews/manager_*.md）/ CreateProjectTool / AppendEventTool / SendToHumanTool / ApplyProposalTool

**Memory**：四层 + team_protocol 注入 + pgvector (role=manager 可跨 project 查)；user.md = 晓寒（动态）

### PM（v1.5 新计数）

**私有 Skills**（2）：product_design / review_tech_design_from_pm

**共享 Skills**（2）：self_retrospective（shared）/ self_score（shared）

**Tools**（6）：SkillLoaderTool / SendMailTool / ReadInboxTool / MarkDoneTool / ReadSharedTool / WriteSharedTool（限 design/ + reviews/{stage}/pm_*.md）

**Memory**：四层 + team_protocol；user.md = Manager（内部甲方，静态）；pgvector (role=pm)

### RD（v1.5 新计数）

**私有 Skills**（4）：tech_design / code_impl / review_product_design_from_rd / review_test_design

**共享 Skills**（2）：self_retrospective / self_score

**Tools**：同 PM 基础 + 在 task skill Sub-Crew 内获得 AIO-Sandbox 全套（bash / file_ops / editor / execute_code）；WriteSharedTool 限 tech/ + code/ + reviews/{stage}/rd_*.md

**Memory**：四层 + team_protocol；user.md = Manager；pgvector (role=rd)

### QA（v1.5 新计数）

**私有 Skills**（5）：review_product_design_from_qa / review_tech_design_from_qa / review_code / test_design / test_run

**共享 Skills**（2）：self_retrospective / self_score

**Tools**：同 RD 基础 + Sub-Crew 沙盒；WriteSharedTool 限 qa/ + reviews/{stage}/qa_*.md

**Memory**：四层 + team_protocol；user.md = Manager；pgvector (role=qa)

### Shared（v1.5 新增角色条目）

**Shared Skills**（2 本课新 + 5 legacy）：
- `self_retrospective`（task，v1.5 从 PM/RD/QA 挪入）
- `self_score`（reference，v1.4-13 新增）
- Legacy：`search_memory` / `memory-save` / `skill_crystallize`（原 skill-creator，v1.5-A6 改名）/ `memory-governance` / `history_reader`

每角色 manifest 必须 enable 这 7 个 shared skill 才能正常工作。

---

## 附录 E · 非目标与已知局限

### 非目标

- 不做 SOP 共创演示外的 SOP 新建（一次演示即可）
- 不做多用户/多团队并发
- 不做档 3 soul/code 级自动 apply
- 不做生产部署 / CI-CD / 前端构建工具链
- 不做多沙盒生产方案（README 说明升级路径）
- 不做 reset_stale（单进程下非必要）
- 不做第二次跑相同任务对比进化效果（git diff 作为证据）

### 已知局限

- 项目并发限 1（多项目需扩展 events.jsonl 的项目选择逻辑 + `_get_current_project_id` 改从 inputs 读）
- 飞书 checkpoint 无自动超时（用户长时间不回 → 项目卡住）
- heartbeat 30s 是兜底；飞书入站走 Runner 常规消费（无额外 at wake），邮件驱动走 at cron 即时唤醒
- 自我进化的提案质量受 L2/L3 日志信息丰富度影响，首次项目数据少时提案可能偏空
- asyncio.Lock 释放瞬间的 pgvector 异步索引窗口：上一轮 async_index_turn 到下一轮查询有 < 3s 窗口（对本课不致命）
- events.jsonl 单进程写入用 filelock 保护，未上 optimistic version；未来多实例部署需加版本校验
- 崩溃半写自愈：§9.3.2 自愈检查只处理 mailbox vs events 不一致；events.jsonl 最后一行部分写入需 skip 非法行
- review_base 共性未抽取：PM/RD/QA 的 review_* skill 各自 checklist 有 40%-60% 共性，v1.2 暂保留重复
- **task skill 一次性执行限制**（P2-19 新增）：Sub-Crew 在 `crew.akickoff()` 返回即退出，不维持状态，也无法接收飞书消息。"多轮对话 + 最终写入" 场景**必须**拆成 `xxx_guide` (reference) + `xxx_write` (task)；见 §17.2
- **reference skill 无执行能力**：reference skill 返回文本给主 Agent 上下文后就结束——sandbox_execution_directive 对主 Agent 是摆设（主 Agent 没沙盒 MCP 连接），主 Agent 只能靠自己的直接 Tool 操作文件

---

## 附录 F · 版本迭代历史

完整迭代轨迹见 `docs/history/`：

| 版本 | 文件 | 核心变化 | 触发点 |
|------|------|---------|-------|
| v0.2 | [history/v0.2-architecture.md](./history/v0.2-architecture.md) | 取消所有 Python 编排代码；每角色 1 Crew + SkillLoader；单沙盒目录隔离；Tools/Skills 重新划分 | 用户指出"流程应 LLM 调度，无代码编排" |
| v0.3 | [history/v0.3-detailed-flow.md](./history/v0.3-detailed-flow.md) | 14 阶段超细粒度展开；每角色完整 Skills/Tools/Memory 清单；state.json 结构 | 用户要求"最细粒度示例步骤图 + 角色清单" |
| v1.0 | （合并到 v1.1） | 合并为单一真理源；吸收 architect review P0 × 10 + P1 × 10 + 关键 P2 | 第一轮 architect review |
| v1.0 final | [history/v1.1-team-only.md](./history/v1.1-team-only.md) | apply_proposal 改 Tool；SkillLoader 扩展量写实；代码仓清理；event log 鲁棒性；check_review_criteria 新增；workspace git 初始化 | 第二轮 architect review |
| v1.1 team-only | [history/v1.1-team-only.md](./history/v1.1-team-only.md) | Skill 类型边界修订：凡"对话+写入"的 skill 拆成 `_guide` (ref) + `_write` (task)；sop_cocreate 和 requirements_discovery 拆成两 skill；新增 review_proposals；SOP 明确为 reference + kind=sop；sop_selector 从 ref 改 task | 用户指出 task skill 无法多轮对话、reference skill 无法操作文件的能力错配 |
| v1.1 综合版 | (被 v1.2 替代) | 合并 17/22 基础 + 29 团队扩展为单一权威文档。消除 v1.1 team-only 对 22 课基础的外部依赖 | 用户要求"完整构建本项目的文档" |
| **v1.2 综合版**（当前） | 本文档 | 第三轮 review 吸收：SKILL 物理路径与沙盒挂载一致化；CronService 不改 API 走文件写入；task_callback project_id 推断方案；classify 实现；每角色固定 session_id；build_role_tools 工厂；manifest 热重载 invalidate cache；main.py 骨架；附录 A 事件枚举重写；soul/agent 分工回归 25 课 | 第三轮 architect review（完备性/精简度/原则贯彻/子文档一致性/迭代痕迹清理） |

### 早期设计决策的历史注记

**为什么不用 state.json 预定义 schema**（v0.3 → v1.0 取消）：v0.3 曾用 state.json 预填 13 个 stage 列表，这是对 sop_feature_dev 的硬编码（换 SOP 就要改 CreateProjectTool），违反"零 Python 编排"原则。append-only 事件流无 schema 硬编码，演化友好。

**为什么 Main Agent 有直接 Tool**（v1.0 → v1.1 team-only 正式说明）：22 课教义是"Main Agent 只有 SkillLoaderTool"，对应单轮用户对话场景。29 课团队场景下，主 Agent 要多轮发邮件、跟多角色协作、主动推送飞书，全走 skill 会每次启 Sub-Crew 几秒开销 + 额外 LLM 调用，所以把"团队协作基础设施"下沉到主 Agent 的直接 Tool；SkillLoaderTool 仍是**领域能力**（对话框架、SOP、复杂文件生成、复盘）的扩展入口。

**为什么统一 routing_key=team:manager 方案被拒绝**（v0.3 → v1.0 取消）：v0.3 曾建议飞书入站改成 team:manager routing_key 以解决 Manager 并发问题，但这会导致 22 课原 p2p:{open_id} 的 session 语义（每用户独立对话历史）丢失、pgvector 用户视角和团队视角记忆混入同一 session、session_id 分配混乱。v1.0 改用 asyncio.Lock 外包 Manager agent_fn 解决并发，保留 p2p 语义。

---

## 附录 G · main.py 骨架伪代码（P1-8 新增）

给新开发者最小可启动的代码参考（~50 行，省略 import / 异常处理）：

```python
# xiaopaw_team/main.py

async def async_main():
    cfg = load_config("config.yaml")
    team_standards = load_yaml(cfg.workspace.team_standards)

    # 1. 检查 workspace 是独立 git 仓库（ApplyProposalTool 依赖）
    # workspace git 检查：缺失不 abort，只警告并禁用 ApplyProposalTool
    cfg.features.apply_proposal_enabled = (cfg.workspace.root / ".git").exists()
    if not cfg.features.apply_proposal_enabled:
        logger.warning("workspace/.git 缺失 → ApplyProposalTool 禁用；参考 README §28.3 初始化")

    # 2. 初始化基础服务（22 课原样）
    setup_logging(cfg.data_dir / "logs")
    session_mgr = SessionManager(cfg.data_dir / "sessions")
    sender = FeishuSender(app_id=cfg.feishu.app_id, app_secret=cfg.feishu.app_secret)
    cron_service = CronService(cfg.data_dir, dispatch_fn=None)  # dispatch_fn 待 Runner 设
    cleanup_svc = CleanupService(cfg.data_dir, cfg.workspace.root)
    await cleanup_svc.sweep()   # 启动时清理 + 写 credentials + 团队工作区初始化

    # 3. 按角色构造 agent_fn
    agent_fns: dict[str, AgentFn] = {}
    for role in ["manager", "pm", "rd", "qa"]:
        tools = build_role_tools(
            role=role,
            cfg=cfg,
            sender=sender if role == "manager" else None,   # 单一接口
            tasks_json_path=cfg.data_dir / "cron" / "tasks.json",
            team_standards=team_standards,
        )
        ws_role = cfg.workspace.root / role
        shared_protocol = cfg.workspace.root / "shared" / "team_protocol.md"
        crew_factory = partial(
            MemoryAwareCrew,
            role=role,
            workspace_root=cfg.workspace.root,
            bootstrap_dir=ws_role,
            shared_protocol=shared_protocol,
            extra_tools=tools,
        )
        agent_fns[role] = build_agent_fn(crew_factory, cfg=cfg)

    # Manager 并发保护
    agent_fns["manager"] = wrap_with_lock(agent_fns["manager"], asyncio.Lock())

    # 4. 构造 Runner（扩展版：按 routing_key 前缀派发）
    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn_map=agent_fns,   # 29 课新参数
        resolve_session_id=make_session_resolver(cfg.workspace.id, session_mgr),
    )
    cron_service._dispatch_fn = runner.dispatch   # 回填

    # 5. 写 4 条 heartbeat cron（文件级 API，错峰首次触发）
    from xiaopaw_team.tools._tasks_store import create_job
    for idx, role in enumerate(["manager", "pm", "rd", "qa"]):
        create_job({
            "id": f"heartbeat-{role}",
            "schedule": {
                "kind": "every", "interval_sec": 30, "jitter_sec": 5,
                "first_delay_sec": idx * 7,   # P1-12：4 role 错峰 0/7/14/21s
            },
            "payload": {
                "routing_key": f"team:{role}",
                "text": "[wake] heartbeat",
                "meta": {"wake_reason": "heartbeat"},
            },
        }, cfg.data_dir / "cron" / "tasks.json")

    # 6. SkillLoader manifest 热重载监控协程
    async def _manifest_monitor():
        while True:
            for role in ["manager", "pm", "rd", "qa"]:
                agent_fns[role].skill_loader.reload_if_changed()
            await asyncio.sleep(5)
    asyncio.create_task(_manifest_monitor())

    # 7. 启动 Listener + Runner + CronService + metrics
    await cron_service.start()
    listener = FeishuListener(cfg.feishu, runner.dispatch, 
                              on_receive_preprocess=feishu_bridge.recv_human_response)
    await run_forever(listener, metrics_port=cfg.observability.metrics_port)


if __name__ == "__main__":
    asyncio.run(async_main())
```

**关键启动检查**：
- `workspace/.git/` 存在——否则 ApplyProposalTool 被禁用但进程仍可跑（demo 场景可接受）
- 4 份 `workspace/{role}/skills/load_skills.yaml` 存在
- 4 份 `workspace/{role}/{soul,agent,memory,user}.md` 存在
- `workspace/shared/team_protocol.md` 存在
- `workspace/shared/config/team_standards.yaml` 存在
- 沙盒容器可访问（`http://localhost:8022/mcp` 通）

---

---

## 附录 H · L1 / L2 日志 entry schema 速查（v1.3-P0-1 补齐）

详细字段定义见 §25.1（L1）+ §25.2（L2），此处给速查示例。

### H.1 L1 示例（outbound + inbound 各一条）

```json
{"ts":"2026-04-20T02:05:00+00:00","action":"checkpoint_request_sent","direction":"outbound","project_id":"proj-pawdiary-0001","user_open_id":"ou_d683...","role":"manager","ck_id":"ck-001","content":{"title":"需求文档 v1","summary":"3 实体 7 接口..."},"artifacts":["needs/requirements.md"]}
{"ts":"2026-04-20T02:12:00+00:00","action":"checkpoint_response_received","direction":"inbound","project_id":"proj-pawdiary-0001","user_open_id":"ou_d683...","role":"manager","ck_id":"ck-001","content":{"user_text":"确认","classified_as":"approved"},"artifacts":[]}
```

### H.2 L2 示例

```json
{"ts":"2026-04-20T02:15:00+00:00","project_id":"proj-pawdiary-0001","role":"pm","session_id":"team-pm-xiaopaw-team-001","task_id":"cb0a1234","trigger":{"source_msg_id":"msg-a1b2c3d4","wake_reason":"new_mail"},"duration_ms":42357,"tokens":{"prompt":3421,"completion":896,"total":4317},"tools_used":["skill_loader","write_shared","send_mail"],"skills_invoked":[{"name":"product_design","type":"task","result_status":"success"}],"artifacts_produced":["design/product_spec.md"],"self_review_passed":true,"result_quality_estimate":0.82,"errors":[]}
```

### H.3 L1 / L2 读取接口

**L1 按月分文件**：`shared/logs/l1_human/2026-04.jsonl`、`2026-05.jsonl`……按 `ts` 的月份归档。跨月查询扫多个文件。

**L2 按天分文件**：`shared/projects/{pid}/logs/l2_task/2026-04-20.jsonl`。复盘时默认读项目整个生命周期所有 `l2_task/*.jsonl` 合并。

### H.4 保留策略

- L1：**永久**（不写清理规则，容量是黄金数据的代价）
- L2：项目 `events.jsonl` 最后 action="archived" 后 **+90 天** 归档清理
- L3：滚动 **30 天**（22 课原样）

---

**文档状态**：v1.5 综合版（v1.4 + skill-creator 规范 review 修订）。相对 v1.4 做了 6 条工程整洁化：

**v1.5 新增**：
- self_retrospective 从 3 份角色私有挪到 1 份 shared（§16.6）
- review_* 跨角色命名消歧：`review_product_design_from_{rd|qa}` / `review_tech_design_from_{pm|qa}`
- sop_selector 改名 `list_available_sops`（动词 + 名词）
- 3 个 reference skill description 补触发源（read_project_state / handle_checkpoint_reply / review_proposal）
- 附录 C 补 description 三要素规范（触发源 / 能力 / 产出暗示）
- 22 课 skill-creator legacy 改名 `skill_crystallize`（避免与 claude-code 社区 skill-creator 混淆）

---

**v1.4 综合版（对齐 28 课《复盘机制重构》）**：相对 v1.3 做了 13 条结构性改动：
1. 复盘 SKILL = 思考框架（非脚本管线）
2. 统一 `tools/log_query.py` CLI 替代 v1.3 分立脚本
3. RetroProposal schema 重写：改动用 before_text/after_text 锚点（无 SHA256 checksum）
4. **取消 ApplyProposalTool**：apply 由提案角色自己机械执行
5. workspace git 从硬约束软化为"可选 commit 审计"
6. review_proposal 分档审批（memory 自动 / skill+agent 转 Human / soul 标高风险）
7-11. 事件 / 邮件 type 全部对齐新流程
12. seed_logs demo 时间戳修复
13. **新增 self_score shared skill** 补齐 L2 `result_quality_estimate` 字段的来源

同时保留 v1.3 所有修订。现在 SKILL 设计哲学与 28 课正文一致，下一步用 skill-creator 的规范系统 review 所有 SKILL 是否合规。
