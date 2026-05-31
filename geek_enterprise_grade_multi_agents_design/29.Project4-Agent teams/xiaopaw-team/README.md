# xiaopaw-team

> 极客时间《企业级多智能体设计实战》**第 29 课**实战项目。
> 把 25-28 课讲过的 4 个机制（团队角色 / 任务链 / Human as 甲方 / 自我进化）**装配成一个能跑的多智能体团队**，端到端完成一个真实 toC 项目开发。

```
┌──────────────────────────────────────────────────────────────────┐
│   用户（飞书 / TestAPI）                                         │
│                        │                                         │
│                        ▼                                         │
│   ┌──────────────  Manager  ──────────────┐                      │
│   │   (唯一对外接口、SOP 主导者)          │                      │
│   └───┬────────────┬────────────┬─────────┘                      │
│       │ task_assign│ task_assign│ task_assign                    │
│       ▼            ▼            ▼                                │
│    ┌──PM──┐     ┌──RD──┐     ┌──QA──┐                            │
│    │ 产品 │     │ 技术 │     │ 测试 │                            │
│    │ 设计 │     │ 实现 │     │ 执行 │                            │
│    └──┬───┘     └──┬───┘     └──┬───┘                            │
│       └── task_done（邮箱 + 事件流） ──┘                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. 学员你将从这个项目学到什么

- **多 Agent 团队怎么协作**：4 个数字员工通过**文件邮箱 + 事件流 + CronService 自唤醒** 完成 6 阶段流水线，**零 Python orchestrator 编排**
- **Human as 甲方**：单一接口原则（人只和 Manager 对话），checkpoint 机制在关键节点让人审核
- **Skill 生态进化**：Agent 通过"自我复盘 → 改进提案 → 分档审批 → 机械执行"完成自我进化
- **production-ready 工程实践**：8 个 CrewAI Python Tools、37 个 Skill、完整单测+集成测试+E2E 全链路

---

## 2. 项目架构（三层继承）

```
L3 团队协作层（29 课新增）
  ├── 4 个 Role Crew：Manager + PM + RD + QA
  ├── 8 个 Python Tools：SendMail/ReadInbox/MarkDone/
  │                      CreateProject/AppendEvent/SendToHuman/
  │                      ReadShared/WriteShared
  ├── File Mailbox：3 态机（unread→in_progress→done），FileLock 并发安全
  ├── Event Log：append-only events.jsonl，单 writer（Manager）
  ├── feishu_bridge：CheckpointStore + 5 分类 classify()
  └── tasks_store：SendMail 自动 schedule_wake + heartbeat 错峰

L2 记忆层（22 课继承）
  ├── Bootstrap：读 soul/user/agent/memory.md 构造 backstory
  ├── ctx.json / raw.jsonl：跨 session 持久化
  └── pgvector 语义检索（可选）

L1 基础设施层（17 课继承）
  └── FeishuListener + Runner + SkillLoader + Sub-Crew + AIO-Sandbox + CronService
```

**核心契约**（29 课创新点）：

```
SendMailTool._run()
  └→ mailbox.send_mail(...)                    # 写收件角色 json
  └→ tasks_store.schedule_wake(project_id)     # 写 tasks.json 一个 at=now+1s job
       └→ CronService detect mtime change (heat-reload)
            └→ dispatch(InboundMessage routing_key="team:pm")
                 └→ Runner._pick_agent_fn("team:pm")
                      └→ agent_fn_map["pm"](message, ...)
                           └→ PM Agent kickoff 处理 task
```

**这个自驱动循环替代了传统 multi-agent 里的 Python orchestrator**。发邮件 = 自动唤醒对方。

---

## 3. 目录结构

```
xiaopaw-team/
├── README.md                          ← 本文档
├── docs/
│   ├── DESIGN.md                      主设计文档 (v1.5, 3500+ 行)
│   ├── test-cases-e2e.md              E2E 测试用例清单（TC-F-001..007）
│   ├── test-design.md                 测试设计文档（135 用例点）
│   ├── design-modules.md              17/22 课基础模块详设
│   ├── design-data.md                 数据格式详设
│   ├── design-api.md                  飞书接口详设
│   ├── design-observability.md        日志+指标详设
│   └── history/                       版本迭代史
│
├── xiaopaw_team/                      ★ 主代码
│   ├── main.py                        进程入口（build_runtime + 事件循环）
│   ├── runner.py                      Runner：routing_key → agent_fn 分派
│   ├── models.py                      InboundMessage / SenderProtocol
│   ├── agents/
│   │   ├── build.py                   ★ TeamMemoryAwareCrew 工厂
│   │   ├── skill_crew.py              Sub-Crew（沙盒内跑 task skill）
│   │   └── config/                    agents.yaml / tasks.yaml
│   ├── tools/
│   │   ├── team_tools.py              ★ 8 个 Python Tools
│   │   ├── feishu_bridge.py           CheckpointStore + classify
│   │   ├── mailbox.py                 邮箱三态机
│   │   ├── event_log.py               append-only events.jsonl
│   │   ├── workspace.py               权限化读写共享区
│   │   ├── self_score.py              5 维加权自评
│   │   ├── skill_loader.py            RoleScopedSkillLoaderTool（29 课）
│   │   └── _skill_loader_base.py      SkillLoaderTool 基类（22 课）
│   ├── cron/
│   │   ├── service.py                 CronService + mtime hot-reload
│   │   └── tasks_store.py             ★ write-then-rename + FileLock API
│   ├── session/manager.py             Session persistence (22 课)
│   ├── memory/                        Bootstrap + context_mgmt + indexer (22 课)
│   ├── feishu/                        Listener + Sender + Downloader
│   └── api/                           test_server + capture_sender
│
├── workspace/                         ★ 4 个角色的 Skill + 身份文件
│   ├── manager/
│   │   ├── soul.md / agent.md / user.md / memory.md   身份四件套
│   │   └── skills/                                     11 个 skill
│   │       ├── sop_feature_dev/       主 SOP（6 阶段推进规则）
│   │       ├── requirements_guide/    需求 4 维澄清框架
│   │       ├── requirements_write/    起草 needs/requirements.md
│   │       ├── read_project_state/    推断项目阶段
│   │       ├── check_review_criteria/ 评审判据
│   │       ├── handle_checkpoint_reply/ 人类回复分档处理
│   │       ├── team_retrospective/    团队复盘思考框架
│   │       ├── review_proposal/       分档审批提案
│   │       ├── list_available_sops/
│   │       ├── sop_cocreate_guide/    SOP 共创 6 维
│   │       ├── sop_write/             SOP 序列化
│   │       └── mailbox_ops/           （legacy, 22 课沙盒版）
│   ├── pm/    skills/ = product_design + review_tech_design_from_pm + …
│   ├── rd/    skills/ = tech_design + code_impl + review_* + …
│   ├── qa/    skills/ = test_design + test_run + review_* + …
│   └── shared/
│       ├── team_protocol.md           团队通用约定（Bootstrap 时注入）
│       └── skills/self_retrospective + self_score
│
├── tests/
│   ├── unit/                          131 个快速单测
│   │   ├── test_team_tools.py          8 个 Python Tools 覆盖
│   │   ├── test_mailbox.py             三态机 + FileLock
│   │   ├── test_event_log.py           append-only + action 校验
│   │   ├── test_workspace.py           permission + path traversal
│   │   ├── test_feishu_bridge.py       classify + CheckpointStore
│   │   ├── test_tasks_store.py         cron create/wake/dedup
│   │   ├── test_self_score.py          5 维加权
│   │   ├── test_log_query.py           日志 CLI
│   │   ├── test_skill_quality.py       36 个 SKILL.md 静态校验
│   │   └── test_main_bootstrap.py      main.build_runtime
│   ├── integration/                   12 个集成测试（真实 FS, 无 LLM）
│   │   ├── test_runner_routing.py
│   │   ├── test_autonomous_handshake.py  ★ Manager→PM 自驱动
│   │   └── e2e_full/                  ★ 8 个 E2E（真实 Qwen + 沙盒）
│   │       ├── _driver.py             E2EDriver + WorkspaceSafeguard + AccumulatingSender
│   │       ├── test_tc_f_001_happy_path.py   ★ 基线全链路
│   │       ├── test_tc_f_002_review_loop.py  插评审分支
│   │       ├── test_tc_f_003_qa_defect_rd_fix.py  QA defect → RD 修复
│   │       ├── test_tc_f_004_checkpoint_revise.py 用户 revise 需求
│   │       ├── test_tc_f_005_retrospective.py     交付后复盘
│   │       ├── test_tc_f_006_code_fail_recovery.py pytest 失败自愈
│   │       └── test_tc_f_007_sop_cocreate_first.py 先共创 SOP
│   └── fixtures/
│
├── config.yaml.template               配置模板（不含密钥）
├── config.yaml                        ← 本地配置（.gitignore，需自建）
├── sandbox-docker-compose.yaml        AIO-Sandbox 容器定义
├── pytest.ini                         marker 定义（unit / integration / e2e / e2e_full）
└── pyproject.toml                     包定义
```

---

## 4. 快速开始（学员最关心）

### 4.1 环境要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 主语言 |
| Docker + docker-compose | 最新 | AIO-Sandbox 容器 |
| Qwen API Key | Aliyun DashScope | LLM（可替换为其他 CrewAI 兼容 LLM） |
| （可选）pgvector | — | 语义检索；不用可留 `db_dsn=""` |

### 4.2 安装

```bash
# 1. 克隆项目
git clone git@github.com:kid0317/xiaopaw-team.git
cd xiaopaw-team

# 2. 创建虚拟环境 + 装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. 复制配置模板，按需填写飞书凭证（smoke 可跳过飞书）
cp config.yaml.template config.yaml
# 编辑 config.yaml 填入 feishu.app_id / app_secret（或留空用 --no-feishu）

# 4. 设环境变量
export QWEN_API_KEY=sk-xxxxxxxxxxxx     # 必需
export SANDBOX_URL=http://localhost:8029/mcp  # 可选，默认值

# 5. 启动 AIO-Sandbox（后台跑）
docker-compose -f sandbox-docker-compose.yaml up -d

# 6. 验证沙盒健康
curl http://localhost:8029/  # 期望返回 200
```

### 4.3 跑起来（两种模式）

#### Mode A：仅跑 Cron + 不接飞书（最简单，推荐首次）

```bash
python -m xiaopaw_team.main --no-feishu
```

进程启动后不会做任何事——**等用户通过 TestAPI 发消息**（或等 heartbeat）。
可通过 `tests/integration/test_autonomous_handshake.py` 直接 dispatch 消息进来观察行为。

#### Mode B：完整生产模式（接飞书）

```bash
# 确保 config.yaml.feishu.app_id/secret 已填
python -m xiaopaw_team.main
```

进程会：
1. 启 4 role agent_fn + Manager 全局 Lock
2. 启 CronService（heartbeat 4 role 错峰 0/7/14/21s，默认 30s 间隔）
3. 启 FeishuListener（WebSocket，无需公网 IP）
4. 等用户 @机器人

---

## 5. 跑测试

### 5.1 快测（非-LLM，< 20s）

```bash
pytest tests/unit tests/integration -m "not e2e and not e2e_full" -v
# 预期：143 passed, 9 deselected
```

### 5.2 E2E 基线：TC-F-001（真实 Qwen + 沙盒，约 13 min）

```bash
# 前置：沙盒跑着 + QWEN_API_KEY 设好
pytest tests/integration/e2e_full/test_tc_f_001_happy_path.py -v -m e2e_full -s
# 预期：1 passed in ~13:00
# 产出：workspace/shared/projects/todo-mvp/ 下的完整 6 阶段产物
```

跑完后你会看到：
- `needs/requirements.md`（Manager 起草）
- `design/product_spec.md`（PM 写）
- `tech/tech_design.md`（RD 写）
- `code/*.py`（RD 实现 + 单测）
- `qa/test_plan.md` + `qa/test_report.md`（QA）
- `events.jsonl` 完整事件链
- `mailboxes/{manager,pm,rd,qa}.json` 邮件历史

**注意**：测试跑完后 `WorkspaceSafeguard` 会**自动还原 workspace/** 到初始状态，防止污染。若想看产物，可在测试过程中 `cat` 对应文件，或在 test 结束前加断点。

### 5.3 E2E 变体（6 个分支场景）

```bash
# 全部跑（约 60-90 min，真实 LLM + 沙盒）
pytest tests/integration/e2e_full/ -v -m e2e_full -s

# 单独跑
pytest tests/integration/e2e_full/test_tc_f_002_review_loop.py -v -m e2e_full -s
```

| 变体 | 测试目标 | 实测结果（真实 Qwen + 沙盒 8029） |
|------|---------|---------------------------------|
| `tc_f_001_happy_path` | 基线：6 阶段全链路产出 | ✅ **PASSED**（qwen3-max, 13min）|
| `tc_f_002_review_loop` | PM 产品设计插入团队评审分支 | 🟡 深入：2 轮 `decided_insert_review` 触发 + 4 份 review 文件，code 阶段超时 |
| `tc_f_003_qa_defect_rd_fix` | QA 发现 defect → RD 修复循环 | 🟡 深入：完整 21 文件代码 + 前端，QA 阶段超时 |
| `tc_f_004_checkpoint_revise` | 用户对需求 checkpoint 回 "revise" | 🟡 深入：PM 2 轮设计（含分享功能）+ QA review + QA→RD 回归 |
| `tc_f_005_retrospective` | 交付后复盘 + 进化分档审批 | 🟡 深入：代码 + qa/test_plan 完成，retro 阶段超时 |
| `tc_f_006_code_fail_recovery` | RD pytest 失败 → 读 stderr 自愈 | 🟡 深入：17 failed pytest 成功触发（符合设计）|
| `tc_f_007_sop_cocreate_first` | 先与用户共创 SOP 再跑功能开发 | ✅ **PASSED**（qwen3.6-max-preview）|

**两个稳定 PASS 基线**：
- TC-F-001（`qwen3-max`）：基线 happy path
- TC-F-007（`qwen3.6-max-preview`）：最复杂路径（SOP 共创 + 6 阶段）

**关于其他 5 个变体的说明**：
- 所有 5 个变体在 qwen3.6-max-preview 下都**完整产出核心 6 阶段产物**（requirements → product_spec → tech_design → code 树 → qa/test_plan + 部分 reviews），只是最终 `qa/test_report.md` 或 `delivered` 事件来不及在测试 timeout（60-90min）内完成
- 每个测试跑约 40-60min，一轮全跑约 5-6 小时
- 失败点集中在 "Manager 派 QA 执行测试" 或 "交付 checkpoint 最终 approve" 的 LLM 决策上（LLM 偶尔在长对话后只回复确认文字而不调工具）
- 重跑一次通常能让其中 1-2 个过；若要全 PASS 建议配合更强模型（GPT-4o / Opus 4.5）

### 5.4 单独跑自驱动 handshake（最快验证系统 wiring）

```bash
pytest tests/integration/test_autonomous_handshake.py -v
# 5s 内完成，不用 LLM，验证 Manager → PM 通过 SendMail + Cron 自动唤醒能否跑通
```

---

## 6. 课堂代码演示学习指南

### 整体架构一览

```
用户（飞书 / TestAPI）
     │
     ▼
FeishuListener / TestAPI
     │  InboundMessage
     ▼
Runner._pick_agent_fn(routing_key)
     │
     ├─ "p2p:*"    → Manager
     ├─ "team:pm"  → PM
     ├─ "team:rd"  → RD
     └─ "team:qa"  → QA
     │
     ▼
TeamMemoryAwareCrew(role=X)
     │  Bootstrap: soul/user/agent/memory.md + team_protocol.md
     │  @before_llm_call: Session 恢复 → 剪枝 → 压缩
     │
     ├─ RoleScopedSkillLoaderTool（渐进式披露）
     │     Phase 1: XML "菜单"
     │     Phase 2: 完整 SKILL.md → Sub-Crew / 直接返回
     │
     ├─ 8 个 Python Tools（宿主机直接执行）
     │     SendMail → mailbox.send_mail + tasks_store.schedule_wake
     │     ReadInbox / MarkDone / CreateProject / AppendEvent
     │     SendToHuman / ReadShared / WriteShared
     │
     └─ Sub-Crew（AIO-Sandbox，代码执行类 Skill 专用）
           sandbox_execute_code / sandbox_execute_bash
           sandbox_file_operations
```

### 学习路线

---

#### 第一步：理解零编排的自驱动循环

**阅读文件**：`xiaopaw_team/tools/team_tools.py`（搜索 `SendMailTool`）+ `xiaopaw_team/cron/tasks_store.py`（搜索 `schedule_wake`）

```
SendMailTool._run()
  → mailbox.send_mail()            # 写收件方 JSON
  → tasks_store.schedule_wake()    # 注册 at=now+1s 定时任务
      → CronService 检测 mtime 变化（热加载）
          → dispatch(InboundMessage routing_key="team:pm")
              → PM Agent kickoff
```

**理解要点**：没有中心化 Python orchestrator。"发邮件 = 自动唤醒对方"——这个闭环替代了传统编排器。四个接缝（邮箱、事件流、CronService、tasks_store）协作完成驱动。

---

#### 第二步：看邮箱三态机

**阅读文件**：`xiaopaw_team/tools/mailbox.py`

```
unread ──ReadInbox──→ in_progress ──MarkDone──→ done
  │                      │
  └─ FileLock 保护 ──────┘
```

| 方法 | 行为 | 并发安全 |
|------|------|---------|
| `send_mail()` | 追加到收件方 JSON（状态 unread） | FileLock |
| `read_inbox()` | 原子读取 unread → 批量标记 in_progress | FileLock |
| `mark_done()` | in_progress → done | FileLock |

**理解要点**：三态设计防止重复消费——Agent 读取后立即标记 `in_progress`，即使被重复唤醒也不会重读同一封邮件。所有读-改-写操作用 `FileLock` 保护。

---

#### 第三步：看事件流与共享工作空间

**阅读文件**：`xiaopaw_team/tools/event_log.py` + `workspace.py`

| 机制 | 文件 | 写权限 | 作用 |
|------|------|--------|------|
| 事件流 | `events.jsonl` | Manager only | 追踪项目进度（action 枚举校验） |
| 共享区 | `needs/` `design/` `tech/` `code/` `qa/` | Owner-by-prefix ACL | 角色间产出传递 |

```python
OWNER_BY_PREFIX = {
    "needs/":   {"manager"},
    "design/":  {"pm"},
    "tech/":    {"rd"},
    "code/":    {"rd"},
    "qa/":      {"qa"},
}
```

**理解要点**：事件流是单 writer（只有 Manager 能写），保证事件链可信。共享工作空间用前缀 ACL 实现写权限隔离——PM 不能改 code/，RD 不能改 design/。Reviews 目录例外：`reviews/{stage}/{reviewer}_{topic}.md` 按 reviewer 字段校验。

---

#### 第四步：看四个角色的身份设计

**阅读文件**：`workspace/manager/` `pm/` `rd/` `qa/` 下的 `soul.md` + `agent.md`

| 角色 | 身份四件套 | 独占工具 | Skill 数 |
|------|-----------|---------|---------|
| Manager | 项目协调者，唯一对外接口 | CreateProject / AppendEvent / SendToHuman | 13 |
| PM | 产品设计师 | — | 5 |
| RD | 技术开发者 | — | 7 |
| QA | 测试工程师 | — | 8 |

**理解要点**：
- 每个角色有独立的 `soul.md`（决策偏好 + NEVER 清单）——soul 是不可变的核心价值观
- `agent.md` 定义工具清单、团队花名册、工作空间约定
- `team_protocol.md` 在 Bootstrap 时注入所有角色——"全局通用约定"
- Manager 的三个独占工具体现了"单一接口原则"——只有 Manager 能对外发消息、创建项目、写事件

---

#### 第五步：看 RoleScopedSkillLoaderTool（29 课修复）

**阅读文件**：`xiaopaw_team/tools/skill_loader.py` + `_skill_loader_base.py`

| 对比 | 22 课 SkillLoaderTool | 29 课 RoleScopedSkillLoaderTool |
|------|----------------------|-------------------------------|
| `skills_dir` | 模块级全局变量 | 实例级私有属性 `self._skills_dir` |
| `sandbox_mount` | 模块级全局变量 | 实例级私有属性 `self._sandbox_mount_desc` |
| 并发安全 | 4 角色并发时全局变量竞争 | 每个角色持有独立实例，无竞争 |

**理解要点**：这是从单 Agent → 多 Agent 的关键修复。22 课只有 1 个 Agent，全局变量没问题；29 课 4 个角色并发运行，必须消除全局状态。

---

#### 第六步：看 Runner 路由与并发控制

**阅读文件**：`xiaopaw_team/runner.py`

| routing_key 模式 | 目标 | 并发模型 |
|-----------------|------|---------|
| `p2p:<open_id>` | Manager | asyncio.Lock（全局串行） |
| `team:pm` | PM | asyncio.Lock（全局串行） |
| `team:rd` | RD | asyncio.Lock（全局串行） |
| `team:qa` | QA | asyncio.Lock（全局串行） |

**理解要点**：为什么全局 Lock？因为 CrewAI 的 `@before_llm_call` Hook 注册在全局事件总线上——如果两个角色并发执行，Session/Bootstrap 会交叉污染。全局 Lock 确保同一时刻只有一个角色在执行 LLM 调用。

---

#### 第七步：看六阶段 SOP

**阅读文件**：`workspace/manager/skills/sop_feature_dev/SKILL.md`

| 阶段 | 产出 | 谁执行 | Human Checkpoint |
|------|------|--------|-----------------|
| 1. 需求 | `needs/requirements.md` | Manager | ✅ 用户确认 |
| 2. 产品设计 | `design/product_spec.md` | PM | 可选评审 |
| 3. 技术设计+代码 | `tech/tech_design.md` + `code/*.py` | RD | 可选评审 |
| 4. 测试设计+执行 | `qa/test_plan.md` + `qa/test_report.md` | QA | 可选评审 |
| 5. 交付 | `delivery_sent` 事件 | Manager | ✅ 用户验收 |
| 6. 复盘 | 各角色改进提案 | 全员 | 按分档审批 |

**理解要点**：SOP 是 Skill（文本），不是代码。Manager 读取 `sop_feature_dev` 后按文本指令推进，阶段间的"推进"就是 `send_mail(to=下一角色, type="task_assign")`。

---

#### 第八步：看 Human as 甲方机制

**阅读文件**：`xiaopaw_team/tools/feishu_bridge.py`（搜索 `classify` 和 `CheckpointStore`）

| 分类 | 触发条件 | 处理 |
|------|---------|------|
| `checkpoint_response` | 有 pending checkpoint | approve / revise / reject |
| `new_requirement` | 无 pending，新需求 | 走 SOP 阶段1 |
| `clarification_answer` | Manager 主动追问后的回复 | 补充信息 |
| `sop_cocreate` | "共创"/"定制工作流" | 先共创 SOP |
| `need_discussion` | 不确定类别 | Manager 自行判断 |

**理解要点**：`CheckpointStore` 用 JSONL 持久化 pending checkpoint，跨唤醒生存。用户回复 "revise" 时，Manager 能找到对应的 checkpoint 上下文，而不是重新问用户"你要改什么"。

---

#### 第九步：看自我进化（复盘→提案→分档→执行）

**阅读文件**：`workspace/shared/skills/self_retrospective/SKILL.md` + `workspace/manager/skills/review_proposal/SKILL.md`

| 步骤 | 执行者 | 产出 |
|------|--------|------|
| retro_trigger | Manager → 各角色 | 触发复盘 |
| self_retrospective | 各角色自省 | improvement_proposals（含 before_text / after_text） |
| review_proposal | Manager | 分档：memory(自动) / skill·agent(人审) / soul(高危人审) |
| 机械执行 | Manager | 纯文本替换（`str.replace(before_text, after_text)`） |

**理解要点**：改进提案必须带 `before_text` 和 `after_text` 锚点——机械执行不用 LLM 判断"改哪里"，直接做文本替换。这保证了可重复性和可审计性。

---

#### 第十步：看 5 维自评分机制

**阅读文件**：`xiaopaw_team/tools/self_score.py`

| 维度 | 权重 | 含义 |
|------|------|------|
| completeness | 0.20 | 模板字段全填 |
| self_review | 0.30 | 自查清单通过率 |
| hard_constraints | 0.20 | SKILL.md 硬约束合规 |
| clarity | 0.15 | 下游可用性 |
| timeliness | 0.15 | 时间/重试次数 |

**理解要点**：自评分嵌入 `task_done` 邮件中，Manager 可据此决定是否插入团队评审。`check_review_criteria` Skill 用 5 个 OR 条件判断是否需要评审（分数低 OR 首轮 OR 用户要求 OR 变更大 OR 角色请求）。

---

#### 第十一步：运行验证

```bash
# 1. 单测（131 个，<20s，无需 LLM）
pytest tests/unit -v

# 2. 自驱动 handshake（验证 Manager→PM 邮件唤醒，5s，无需 LLM）
pytest tests/integration/test_autonomous_handshake.py -v

# 3. E2E 基线（TC-F-001，真实 Qwen + 沙盒，~13min）
pytest tests/integration/e2e_full/test_tc_f_001_happy_path.py -v -m e2e_full -s
```

---

### 学习检查清单

- [ ] 零编排的"自驱动循环"是什么？（SendMail → schedule_wake → CronService → dispatch → Agent kickoff）
- [ ] 四个接缝分别是什么？（文件邮箱、事件流、CronService、tasks_store）
- [ ] 邮箱三态机为什么需要 `in_progress` 状态？（防止重复消费——Agent 被重复唤醒时不会重读已处理邮件）
- [ ] Manager 为什么有三个独占工具？（单一接口原则——只有 Manager 能对外发消息、创建项目、写事件）
- [ ] RoleScopedSkillLoaderTool 解决了什么问题？（全局变量在多角色并发时导致 skills_dir 竞争）
- [ ] 为什么用全局 asyncio.Lock？（CrewAI 的 Hook 注册在全局事件总线，并发执行会交叉污染 Session）
- [ ] 自我进化为什么用"机械执行"？（before_text/after_text 纯文本替换，不依赖 LLM 判断，可重复可审计）
- [ ] Owner-by-prefix ACL 的规则？（needs/ → Manager, design/ → PM, tech/+code/ → RD, qa/ → QA）
- [ ] CheckpointStore 为什么用 JSONL 持久化？（跨唤醒生存——Manager 被唤醒时还能找到之前 pending 的 checkpoint）

---

## 7. 看懂流程——关键路径补充

### 新需求进来，会发生什么

1. **用户飞书发消息**："帮我做个 TODO 网站"
2. **FeishuListener** → 封装成 `InboundMessage(routing_key="p2p:<open_id>", content="帮我做个...")` → `runner.dispatch()`
3. **Runner** → 按 routing_key 找 agent_fn：`p2p:*` 固定走 Manager
4. **Manager agent_fn**（TeamMemoryAwareCrew with role=manager）→ Bootstrap 读 manager/soul/user/agent/memory.md 注入 backstory → CrewAI kickoff
5. **Manager LLM 决策**：加载 `sop_feature_dev` skill + `requirements_guide` skill → 4 维评估 → 调用 Python Tools：
   - `create_project(project_id="todo-mvp", ...)` → 创建 workspace/shared/projects/todo-mvp/ 目录树
   - `append_event("requirements_drafted", ...)`
   - `send_to_human(kind="checkpoint_request", message="需求摘要...")`
   - `send_mail(to="pm", type="task_assign", subject="产品设计 (第 1 轮)", ...)`
6. **SendMailTool 内部**：写 pm.json + `tasks_store.schedule_wake(role="pm", project_id="todo-mvp")` 一个 at=now+1s job
7. **CronService** 下一轮 tick（50ms 周期）检测 tasks.json mtime 变了 → reload → 发现 at 到期 → `dispatch(InboundMessage(routing_key="team:pm", content="__wake__:new_mail:todo-mvp"))`
8. **PM agent_fn** 被唤醒 → `read_inbox("todo-mvp")` 读 task_assign → 加载 `product_design` skill → `write_shared("design/product_spec.md", ...)` → `send_mail(to="manager", type="task_done", ...)`
9. **回到 Manager**，按 SOP 推进到 RD → QA → 交付

**全程没有任何中心化 Python orchestrator 驱动**。Cron + SendMail 的闭环就是驱动引擎。

---

## 8. 常见问题

### Q: Manager 不夹带任务给 PM，只给用户回文字？

Manager LLM 偶现"只说不做"（回复"已分派"但不实际调 send_mail）。应对：
1. 查 `workspace/manager/skills/sop_feature_dev/SKILL.md` 是否仍在 critical rules 里说"必须调 send_mail 工具而非只回复文字"
2. 查 `workspace/shared/team_protocol.md` 是否包含"防只说不做"约束
3. 若仍然不稳定，重跑一次（LLM 变率）；或切换到 Opus / GPT-4 等更指令遵循的 LLM

### Q: 怎么看 Manager 当前在干啥？

运行时产物都在 `workspace/shared/projects/{project_id}/`：
- `events.jsonl` — 事件流（Manager 写）
- `mailboxes/*.json` — 4 个角色邮箱
- `needs/` `design/` `tech/` `code/` `qa/` `reviews/` — 产物目录

会话记录在 `data/ctx/s-*.jsonl`（每次 LLM turn 的完整 raw messages）。

### Q: 沙盒为什么不用 local Python 就跑？

Code_impl 和 test_run 这两个 task skill 需要运行 bash + pytest，必须隔离环境（防止污染开发机 + 支持任意依赖 pip install）。普通写文件类 skill（product_design / tech_design / test_design / review_*）用 host 端 Python Tools，不走沙盒。

### Q: E2E 测试会污染我的 workspace 吗？

不会。`WorkspaceSafeguard` 在 test setup 时 rsync 整目录到 `tmp_path/workspace_backup`，teardown 时清空 workspace 后再从备份 rsync 回来。即使测试过程中 Agent 误改了 skill 文件也会被还原。

### Q: `OpenAI API call failed: 401` 一直在 log 里刷？

那是 CrewAI 的 `_summarize_chunk`（上下文压缩功能）默认调 OpenAI。我们用 Qwen 不影响主流程，是良性噪声。可通过设置 `OPENAI_API_KEY=<valid_key>` 消除或把 `context_mgmt.py` 里的 `_summarize_chunk` 替换为 Qwen 实现。

---

## 9. 设计文档

进阶阅读：
- **[docs/DESIGN.md](./docs/DESIGN.md)** — 主设计文档 v1.5（3500+ 行，完整架构 + 32 skill 清单 + 6 阶段流程详解）
- **[docs/test-cases-e2e.md](./docs/test-cases-e2e.md)** — E2E 测试用例设计（7 个变体 + 覆盖矩阵）
- **[docs/test-design.md](./docs/test-design.md)** — 测试设计（风险分析 F×5/H×8/M×10/L×5, 135 测试点）

---

## 10. 相关项目

- [xiaopaw-with-memory](../xiaopaw-with-memory/) — 17/22 课单 Agent 版本，本项目基础
- [crewai_mas_demo](../crewai_mas_demo/) — 25-28 课概念演示代码
