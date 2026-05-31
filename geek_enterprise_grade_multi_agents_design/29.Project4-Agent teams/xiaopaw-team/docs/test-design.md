# XiaoPaw-Team 测试设计文档 v1.1

> **项目**：xiaopaw-team（第 29 课实战项目）
> **依据**：docs/DESIGN.md v1.5 综合版
> **风格参考**：xiaopaw-with-memory/docs/test-design-course22.md
> **创建时间**：2026-04-20
> **v1.1 更新**：对齐 DESIGN.md v1.4 复盘机制重构 + v1.5 skill 命名规范

---

## v1.1 修订记录

基于 DESIGN.md v1.4（对齐 28 课《复盘机制重构》）+ v1.5（skill 规范整洁化）同步更新：

| # | 修订 | 位置 |
|---|---|---|
| v1.1-1 | **T-AP-* 整组改写**：ApplyProposalTool 取消，改为 Agent 自执行机械替换；对应风险 R-F-03/R-F-05/R-L-03 重写 | §2.1 / §2.4 / §3 |
| v1.1-2 | **T-REV-* 重写**：review_proposals(复数/checksum) → review_proposal(单数/分档) | §3 |
| v1.1-3 | **新增 T-SS-* self_score** | §3 |
| v1.1-4 | **新增 T-RET-* retro 邮件流**（retro_report / retro_approved / retro_applied / retro_apply_failed） | §3 |
| v1.1-5 | **Journey / Case 里 sop_selector → list_available_sops** | §7 |
| v1.1-6 | **C-STG6-* 完全重写**：分档审批 + Agent 自执行 | §6.7 |
| v1.1-7 | **build_role_tools 测试点**：Manager tools 数减少（ApplyProposal 去掉）+ shared skill 能被所有 role load | §3.5 T-UI-* |
| v1.1-8 | **L2 schema 测试**：result_quality_estimate 来自 self_score 解析 | §3 T-LOG-* |
| v1.1-9 | **review_* 跨角色消歧测试**：确保 PM load 到 `review_tech_design_from_pm` 而非 `_from_qa` | §3 T-SL-* |

---

## 目录

1. [概述](#1-概述)
2. [风险分析](#2-风险分析)
   - [2.1 致命风险（F 级）](#21-致命风险f-级)
   - [2.2 严重风险（H 级）](#22-严重风险h-级)
   - [2.3 中等风险（M 级）](#23-中等风险m-级)
   - [2.4 低风险（L 级）](#24-低风险l-级)
3. [测试点清单](#3-测试点清单)
   - [3.1 基础设施层测试点](#31-基础设施层测试点)
   - [3.2 团队协作层测试点](#32-团队协作层测试点)
   - [3.3 主 Agent × Skill 边界测试点](#33-主-agent--skill-边界测试点)
   - [3.4 进化闭环测试点](#34-进化闭环测试点)
   - [3.5 权限与单一接口测试点](#35-权限与单一接口测试点)
   - [3.6 数据与审计测试点](#36-数据与审计测试点)
4. [可测性评估](#4-可测性评估)
5. [自动化测试方案](#5-自动化测试方案)
   - [5.1 单元测试](#51-单元测试)
   - [5.2 集成测试（无 LLM）](#52-集成测试无-llm)
   - [5.3 E2E 测试（真实 LLM）](#53-e2e-测试真实-llm)
   - [5.4 目录结构](#54-目录结构)
   - [5.5 CI 配置](#55-ci-配置)
6. [功能测试 Case](#6-功能测试-case)
   - [6.1 阶段 0：SOP 共创](#61-阶段-0sop-共创)
   - [6.2 阶段 1：需求澄清](#62-阶段-1需求澄清)
   - [6.3 阶段 2：产品设计](#63-阶段-2产品设计)
   - [6.4 阶段 3：RD 实现](#64-阶段-3rd-实现)
   - [6.5 阶段 4：QA 测试](#65-阶段-4qa-测试)
   - [6.6 阶段 5：交付](#66-阶段-5交付)
   - [6.7 阶段 6：复盘进化](#67-阶段-6复盘进化)
   - [6.8 Tool 级 Case](#68-tool-级-case)
   - [6.9 Skill 级 Case](#69-skill-级-case)
7. [E2E Journey](#7-e2e-journey)
   - [7.1 Smoke Journey](#71-smoke-journey)
   - [7.2 Review Loop Journey](#72-review-loop-journey)
   - [7.3 Evolution Journey](#73-evolution-journey)
8. [测试数据工厂](#8-测试数据工厂)
9. [里程碑验收清单](#9-里程碑验收清单)
10. [已知不可测点 + 人工验证兜底](#10-已知不可测点--人工验证兜底)
- [附录 A：Mock 与 Stub 注册表](#附录-a-mock-与-stub-注册表)
- [附录 B：pytest marker 定义](#附录-b-pytest-marker-定义)
- [附录 C：关键断言辅助函数](#附录-c-关键断言辅助函数)

---

## 1. 概述

### 1.1 测试目标

验证 xiaopaw-team 在真实基础设施上端到端可运行，覆盖以下核心场景：
1. **团队协作链路**：Manager/PM/RD/QA 通过文件邮箱 + 事件流协作，6 阶段 SOP 推进到位
2. **唤醒机制**：飞书入站、邮件 at cron、heartbeat 三路唤醒，去重逻辑正确
3. **权限隔离**：WriteSharedTool 工具层强制，单一接口原则，PM/RD/QA 无法联系用户
4. **自我进化**：复盘提案 → Manager 预审 → 用户 approve → ApplyProposalTool → git commit
5. **可测性边界**：LLM 推理不测（黑盒），只测工具层行为、事件流状态、文件产物

### 1.2 测试层次

| 层次 | 覆盖范围 | LLM | Sandbox | 耗时 |
|------|---------|-----|---------|------|
| **单元** | 纯函数（mailbox 状态机、event_log、workspace 权限、classify、cron 去重）| 不需要 | 不需要 | <1s/用例 |
| **集成（无 LLM）** | 工具链路、邮箱三态、事件流推断、唤醒链、manifest 热重载、session_id 生命周期 | 不需要 | 不需要 | <10s/用例 |
| **集成（有 LLM）** | Manager 澄清 → checkpoint → PM 设计 → 评审 → 各阶段真实 kickoff | 需要 | 需要 | 60-300s/用例 |
| **E2E（全链路）** | 6 阶段完整 Journey，飞书消息文本真实，事件流 + 文件产物全断言 | 需要 | 需要 | 15-60min |

### 1.3 测试覆盖目标

| 指标 | 目标 |
|------|------|
| 工具层函数覆盖 | ≥ 85%（单元测试） |
| 分支覆盖 | ≥ 80% |
| 集成（无 LLM）用例 | ≥ 50 条 |
| E2E Journey | 3 条（smoke / review loop / evolution）|
| 里程碑（M1-M7）验收 | 全部通过 |

### 1.4 不在本文档范围内

- LLM 输出质量（内容合理性）：E2E 只断言关键词 + 文件存在，不断言语义
- AIO-Sandbox 内部机制：视为黑盒，只测 Sub-Crew kickoff 返回值
- 飞书 WebSocket 连通性：用 TestAPI 模拟，不测真实飞书
- 多用户 / 多团队并发（DESIGN.md 附录 E 明确为非目标）

---

## 2. 风险分析

### 2.1 致命风险（F 级）

> 致命：一旦触发，项目卡死或数据损坏，无法自动恢复。

---

#### R-F-01: events.jsonl 并发写入损坏

- **现象**：两个 routing_key（p2p:user + team:manager）同时触发 AppendEventTool，JSON Lines 最后一行部分写入，`read_project_state` 解析失败。
- **致命后果**：事件流为状态真相唯一来源，损坏后 Manager 每次 kickoff 都报错，项目完全卡死。
- **触发条件**：用户在飞书发消息的同时 cron 唤醒 Manager，asyncio.Lock 未覆盖 filelock 外层的并发。
- **缓解手段**：FileLock 保护每次 append；read_project_state 脚本跳过最后一行非合法 JSON（自愈）。
- **覆盖测试点**：T-EL-01, T-EL-02, T-EL-05

---

#### R-F-02: Manager asyncio.Lock 释放时 cron wake 队列积压

- **现象**：Manager 处理飞书消息期间多个 at cron 和 heartbeat 触发，Lock 释放后瞬间积压执行，导致 Manager 对同一 checkpoint 多次 approve。
- **致命后果**：events.jsonl 出现重复 checkpoint_approved，PM/RD/QA 收到重复 task_assign，产物覆写冲突。
- **触发条件**：Manager kickoff 耗时 >30s（heartbeat 周期），多个 cron 在 Lock 等待队列。
- **缓解手段**：cron wake 去重（Runner.dispatch 检查 pending queue 中已有 wake_reason∈{new_mail,heartbeat}）。
- **覆盖测试点**：T-CR-01, T-CR-02, T-RN-01

---

#### R-F-03: retro_approved 执行时 before_text 锚点不匹配（v1.4 改写）

- **现象**：Agent 收到 retro_approved 邮件后执行机械替换，但 target_file 在提案生成到执行之间被并发修改，`before_text` 不能精确 substring 匹配，导致：
  - 要么 Agent 盲目替换失败；
  - 要么更坏：Agent 用模糊匹配产生错位替换，文件局部损坏。
- **致命后果**：角色自身的 SOP/skill 被破坏，下次复盘再出问题 → 进化闭环崩坏。
- **触发条件**：提案产生后用户 approve 前，其它进程（如并发的另一条 retro_apply）修改了同一 target_file。
- **缓解手段**：Agent agent.md 约束"**精确 substring 匹配**（`before_text in content`），匹配失败立刻返回 retro_apply_failed 邮件给 Manager，不做模糊匹配"；Manager 让原提案 Agent 重新产出更精准锚点。
- **覆盖测试点**：T-RET-03, T-RET-04（取代原 T-AP-01/02/04）

---

#### R-F-04: send_mail at cron 写 tasks.json 失败但邮件已写入

- **现象**：SendMailTool 先写 mailbox，后写 tasks.json（at cron），tasks.json 写失败（磁盘满/权限）但 mailbox 写成功，收件人永远不被唤醒。
- **致命后果**：PM/RD/QA 不醒，只能等 30s heartbeat；但若 heartbeat 同时失效，邮件永久积压。
- **触发条件**：磁盘满 / tasks.json FileLock 超时 / 并发写冲突。
- **缓解手段**：SendMailTool 写入顺序保证；tasks.json 写失败需回滚 mailbox 或 raise；heartbeat 作为兜底（30s）。
- **覆盖测试点**：T-MB-01, T-CR-03

---

#### R-F-05: workspace 非 git 仓库时 retro apply 后 subprocess 污染宿主机 git（v1.4 软化）

- **现象**：v1.4 取消 ApplyProposalTool 后，apply 由各角色 agent.md 流程机械替换完成；但 agent.md 末尾"（可选）workspace 若为 git 仓库则 commit"步骤如果在 workspace/.git/ 不存在时**不 soft skip**，直接 `git -C workspace commit` 会向上查找宿主机 .git 并提交。
- **致命后果**：课程代码仓被 LLM 产出的改动污染，git log 脏。
- **触发条件**：workspace 非 git 仓库 + Agent agent.md 流程未 try/except subprocess.CalledProcessError。
- **缓解手段**：v1.4-5 软化——CleanupService 启动时 `check_workspace_git_ready()` 返回 False 时设 `cfg.features.retro_auto_commit = False`；Agent 的 agent.md 只在 `retro_auto_commit=True` 时执行 git commit；`try/except subprocess.CalledProcessError: pass`（soft skip）。
- **覆盖测试点**：T-RET-05, T-BS-03

### 2.2 严重风险（H 级）

> 严重：功能降级或用户体验严重受损，但可自愈或手工干预恢复。

---

#### R-H-01: SkillLoader manifest 热重载清空 _instruction_cache 遗漏

- **现象**：sop_write 写完新 SKILL.md 后，manifest 更新，reload_if_changed 只清 _skill_registry 未清 _instruction_cache，Manager 下次调用新 Skill 仍返回旧 SKILL.md 正文。
- **严重后果**：进化提案写入 workspace 文件但 Agent 仍执行旧 SOP，进化功能失效。
- **触发条件**：apply_proposal 写了新版 SKILL.md 且触发 manifest reload，但 cache 未 invalidate。
- **缓解手段**：reload_if_changed 同时清 _skill_registry 和 _instruction_cache（DESIGN.md §6.2 扩展 4）。
- **覆盖测试点**：T-SL-05, T-SL-06

---

#### R-H-02: task_callback L2 日志 project_id 推断错误

- **现象**：多个历史项目 events.jsonl 都存在，_get_current_project_id 取错项目（取到已 archived 的旧项目），L2 日志写错 project_id。
- **严重后果**：team_retrospective 聚合 L2 数据时分析错误，复盘提案基于错误数据，误导进化方向。
- **触发条件**：events.jsonl 遍历顺序不稳定；尾行判断 action≠"archived" 逻辑有 bug。
- **缓解手段**：_get_current_project_id 遍历所有 events.jsonl 尾行，按 ts 取最新且未 archived 的项目；单元测试覆盖多项目场景。
- **覆盖测试点**：T-LOG-01, T-LOG-02

---

#### R-H-03: feishu_bridge.classify 误判 need_discussion 为 approved

- **现象**：用户回复"这个需求不太对，我们讨论一下" → classify 中 "对" 字触发 approved 关键词匹配，误认为确认。
- **严重后果**：需求阶段 checkpoint 被错误 approve，Manager 进入设计阶段，用户意图被忽略。
- **触发条件**：关键词列表过宽（如包含中文单字"可以" "对"），未做词边界检查。
- **缓解手段**：classify 优先卡片按钮 callback；纯文本做严格词边界匹配（完整词，不含字），其余兜底 need_discussion。
- **覆盖测试点**：T-FB-01, T-FB-02, T-FB-03

---

#### R-H-04: read_inbox 标 in_progress 后崩溃，消息卡在 in_progress 永不处理

- **现象**：角色读取邮件、标记 in_progress 后 LLM 调用超时/崩溃，下次 wake read_inbox 跳过 in_progress 邮件，任务永远卡住。
- **严重后果**：RD/QA 的 task_assign 永久积压，SOP 流程中断。
- **触发条件**：LLM 超时（>300s）/ 沙盒崩溃 / 主进程被 kill。
- **缓解手段**：reset_stale 机制（超过 stale_timeout_sec=900s 的 in_progress 恢复 unread）。本课单进程不启用 reset_stale，但测试需验证超时场景下的兜底行为。
- **覆盖测试点**：T-MB-03, T-MB-04

---

#### R-H-05: SkillLoader owner_role 过滤失效，PM LLM 看到 Manager 专属 Skill

- **现象**：_build_description 未按 owner_role 过滤，PM 的工具 XML 里出现 sop_feature_dev、create_project 等 Manager 专属 Skill。
- **严重后果**：PM 可能误调 Manager 专属 Skill，产生越权行为；对话记录被 Skill 内容污染。
- **触发条件**：扩展 SkillLoader 时忘记加 owner_role 过滤条件。
- **缓解手段**：_build_description 对每条 manifest 条目检查 owner_role：若 owner_role 不是 "any" 且不等于 self._role，则跳过。
- **覆盖测试点**：T-SL-02, T-SL-03

---

#### R-H-06: WriteSharedTool reviews/ 路径正则校验漏洞

- **现象**：reviews/product_design/qa_fix_summary.md 包含"qa"前缀但含额外下划线，正则 `^reviews/[a-z_]+/([a-z]+)_([a-z_]+)\.md$` 通过了，但实际路径不符合约定。
- **严重后果**：权限校验形同虚设，QA 可以写任何 reviews/ 下的文件，包括覆盖 rd_review.md。
- **触发条件**：正则过于宽泛，qa 匹配 group(1) 足够。
- **缓解手段**：正则分组 group(1) == role（严格等于），含 qa 不等于 qa 的情况不通过；补充单元测试覆盖边界路径。
- **覆盖测试点**：T-PERM-01, T-PERM-02, T-PERM-03

---

#### R-H-07: CronService heartbeat 所有 4 角色同时触发，LLM 并发爆炸

- **现象**：4 个 every 30s cron 同相（无 jitter），在同一 tick 同时触发，4 个 agent_fn 同时 kickoff，LLM QPS 超过 Qwen 限流。
- **严重后果**：多条 LLM 请求被限流报错，所有角色 kickoff 失败，SOP 流程中断。
- **触发条件**：main.py 注册 heartbeat 时 jitter_sec=0 或 jitter 不生效。
- **缓解手段**：每角色 jitter_sec=5（±5s 随机偏移，DESIGN.md §7.1），确保 4 个 heartbeat 错峰。
- **覆盖测试点**：T-CR-04, T-CR-05

---

#### R-H-08: pgvector role/project_id metadata 未写入，team_retrospective 跨角色查询返回空

- **现象**：async_index_turn 未传 role/project_id 参数（使用了旧 22 课签名），memories 表新增列值为 NULL，Manager WHERE role IN ('pm','rd','qa') 返回空。
- **严重后果**：team_retrospective 找不到 L3 数据，复盘提案基于空数据，进化失效。
- **触发条件**：29 课扩展了 async_index_turn 签名但调用处未同步更新。
- **缓解手段**：async_index_turn 签名校验 role 和 project_id 非 None；写入后可 SELECT 验证。
- **覆盖测试点**：T-PG-01, T-PG-02

### 2.3 中等风险（M 级）

> 中等：产生错误但系统可继续运行，或用户可通过重试恢复。

---

#### R-M-01: Bootstrap 注入 team_protocol.md 路径不存在时静默跳过

- **现象**：shared/team_protocol.md 缺失，build_bootstrap_prompt 静默跳过，所有角色收不到团队协作约定。
- **后果**：角色不知道"kickoff 两步法"，可能跳过 read_inbox 直接行动，导致邮件积压不处理。
- **覆盖测试点**：T-BS-01, T-BS-02

---

#### R-M-02: {team_standards.X} 变量在 SKILL.md 中未替换，传入 LLM 原始占位符

- **现象**：SkillLoader _get_skill_instructions 替换时 team_standards key 不匹配（大小写/拼写），`{team_standards.pytest_coverage_min}` 原样出现在 LLM 上下文。
- **后果**：RD 收到的 code_impl SKILL 约束条件是字面量 `{team_standards.pytest_coverage_min}` 而非 0.80，LLM 可能忽略。
- **覆盖测试点**：T-SL-04

---

#### R-M-03: CreateProjectTool 创建的目录结构不完整

- **现象**：CreateProjectTool 只 mkdir 几个子目录，遗漏 mailboxes/{manager,pm,rd,qa}.json 初始化，第一个 send_mail 找不到文件直接抛 FileNotFoundError。
- **后果**：阶段 2 第一次 send_mail 失败，需手工创建目录。
- **覆盖测试点**：T-CP-01, T-CP-02

---

#### R-M-04: task skill 在 Sub-Crew 内调用 write_shared 绕过工具层权限

- **现象**：RD code_impl task skill 的 Sub-Crew 通过沙盒 bash 直接写 /workspace/shared/projects/{pid}/design/ 目录，绕过 WriteSharedTool 的 check_write。
- **后果**：RD 可覆盖 PM 的 product_spec.md，破坏设计文档完整性。
- **触发条件**：SKILL.md 中未写明"只能写 tech/ 和 code/ 目录"的约束，LLM 自由发挥。
- **缓解手段**：SKILL.md 中 sandbox_execution_directive 明确禁止写 design/、needs/；Sub-Crew backstory 行为规则。
- **覆盖测试点**：T-WS-01, T-WS-02

---

#### R-M-05: review_max_rounds 超限后 error_alert 未发出，流程无限循环

- **现象**：评审循环计数由 Manager LLM 从 events.jsonl 推断，LLM 推断错误或跳数，循环超过 review_max_rounds=3 但未触发 error_alert。
- **后果**：PM/RD 被无限反复要求修改，资源浪费；用户得不到通知。
- **覆盖测试点**：T-SOP-03, T-REV-01

---

#### R-M-06: MarkDoneTool 顺序错误（先 mark_done 后 append_event）

- **现象**：team_protocol.md 规定"先 append_event 再 mark_done"，但 Agent LLM 执行顺序相反：先 mark_done 邮件，然后 append_event 时因条件未达到而失败，邮件已 mark_done 但事件未记录。
- **后果**：下次 read_project_state 发现邮件已 done 但无对应事件，自愈检查触发，可能重复派发任务。
- **覆盖测试点**：T-MB-05, T-EL-03

---

#### R-M-07: session_id 对 team:{role} 每次 wake 生成新值，ctx.json 无法恢复历史

- **现象**：resolve_session_id 未实现 team:{role} 的固定逻辑，每次 wake 进入 SessionManager.get_active_session_id 获取新 session_id。
- **后果**：角色每次被唤醒都是冷启动，无法通过 ctx.json 恢复上次处理到的进度，多轮协作信息丢失。
- **覆盖测试点**：T-RN-02, T-RN-03

---

#### R-M-08: sop_write 追加 manifest 后格式错误，_build_description 解析失败

- **现象**：sop_write task skill 的 Sub-Crew 追加 load_skills.yaml 条目时缩进错误，YAML 解析报错，触发热重载时 SkillLoader 内部异常，Manager 丢失所有 Skill 描述。
- **后果**：Manager 下次 kickoff 无任何可用 Skill，无法继续推进项目。
- **覆盖测试点**：T-SL-01, T-SL-07

---

#### R-M-09: 多条 retro_proposal 邮件的"收齐规则"推断错误，提前汇报

- **现象**：events.jsonl 的 retro_triggered.to.length 与 proposal_received.count 对比时，LLM 数错了（漏算被 rejected 的提案），判断为"收齐"但实际还差一个。
- **后果**：Manager 提前向用户汇报，遗漏部分角色提案。
- **覆盖测试点**：T-REV-02, T-REV-03

---

#### R-M-10: check_review_criteria 脚本 grep 漏数实体

- **现象**：product_spec.md 中实体用中文标题"### 数据实体"而非英文"### Entity"，grep 正则不匹配，返回实体数=0，Manager 错误判断"不需要插入评审"。
- **后果**：高复杂度产品设计跳过评审，质量风险被遗漏。
- **覆盖测试点**：T-SOP-02

### 2.4 低风险（L 级）

> 低：影响次要功能或非核心体验，不影响主流程。

---

#### R-L-01: FeishuSender send_card 卡片格式在旧飞书版本显示异常

- **现象**：checkpoint_request 卡片的按钮格式（interactive JSON）在低版本飞书 App 不渲染，用户看到纯文本 JSON。
- **后果**：用户无法点按钮，只能发文字回复，走 classify 文本路径（功能降级但可用）。
- **覆盖测试点**：T-FB-04

---

#### R-L-02: L1 日志 send_to_human 写入路径不存在

- **现象**：shared/logs/l1_human/ 目录未被 ensure_workspace_dirs 创建，第一次 send_to_human 写 L1 时 FileNotFoundError。
- **后果**：L1 日志缺失，team_retrospective 无跨项目黄金数据，但主流程不受影响。
- **覆盖测试点**：T-LOG-03

---

#### R-L-03: workspace git 检查软化后 retro_auto_commit feature flag 未生效（v1.4 改写）

- **现象**：v1.4-5 把 workspace git 检查从"禁用 ApplyProposalTool"软化为"设 `cfg.features.retro_auto_commit=False`"；如果 Agent agent.md 流程没读这个 flag，仍会尝试 subprocess git commit。
- **后果**：触发 R-F-05 同类污染。
- **覆盖测试点**：T-BS-03, T-RET-05

---

#### R-L-04: pgvector async_index_turn 与下一轮查询竞态（<3s 窗口）

- **现象**：async_index_turn 用 asyncio.create_task 异步触发，上一轮写入到下一轮 search_memory 查询可能 <3s 未就绪，返回空结果。
- **后果**：连续两轮对话中 search_memory 找不到刚生成的分析结论。
- **覆盖测试点**：T-PG-03

---

#### R-L-05: 四角色 heartbeat 注册顺序决定触发顺序，无 jitter 时 manager 总在最前

- **现象**：main.py 按 [manager, pm, rd, qa] 顺序注册 heartbeat，无 jitter 时 manager 每次先跑，占用 LLM 资源后其他角色 throttle。
- **后果**：其他角色偶尔 kickoff 延迟，不影响最终结果。
- **覆盖测试点**：T-CR-04

---

## 3. 测试点清单

### 3.1 基础设施层测试点

编号前缀：T-SL（SkillLoader）, T-CR（CronService）, T-RN（Runner）, T-BS（Bootstrap）, T-PG（pgvector）

#### SkillLoader

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-SL-01 | manifest YAML 解析成功 | workspace/{role}/skills/load_skills.yaml 合法 YAML | _skill_registry 包含所有 enabled=true 的条目 | `assert len(loader._skill_registry) == N` | R-M-08 |
| T-SL-02 | owner_role 过滤生效 | PM 角色 loader 加载含 owner_role=manager 条目的 manifest | 工具 description XML 不含 owner_role=manager 的 skill | `assert "sop_feature_dev" not in loader.description` | R-H-05 |
| T-SL-03 | owner_role=any 不过滤 | manifest 含 owner_role=any 条目 | 所有角色 loader 都能看到该条目 | `assert "legacy_skill" in loader.description` | R-H-05 |
| T-SL-04 | team_standards 变量替换 | SKILL.md 含 `{team_standards.pytest_coverage_min}`，team_standards={pytest_coverage_min: 0.80} | 返回指令含 "0.80" 而非占位符 | `assert "{team_standards" not in instructions` | R-M-02 |
| T-SL-05 | reload_if_changed 清 _instruction_cache | manifest mtime 变化 | _instruction_cache 清空，_skill_registry 重建 | `cache_was_non_empty; loader.reload_if_changed(); assert len(loader._instruction_cache) == 0` | R-H-01 |
| T-SL-06 | 热重载后新 SKILL 可见 | sop_write 追加新条目到 manifest → 修改 mtime | 新 skill_name 出现在 _skill_registry | `assert "new_skill" in loader._skill_registry` | R-H-01 |
| T-SL-07 | manifest YAML 格式错误时 graceful degradation | manifest 含无效 YAML | _skill_registry 为空但不抛未捕获异常 | `assert loader._skill_registry == {}` | R-M-08 |
| T-SL-08 | reference skill 返回文本，不启 Sub-Crew | skill type=reference | 返回字符串（含 skill_instructions）；build_skill_crew 未被调用 | `result = await loader._arun("sop_feature_dev"); assert isinstance(result, str)` | — |
| T-SL-09 | review_* 命名消歧（v1.5-A2）：PM load 到 from_pm 版 | SkillLoader(role="pm") | description XML 含 `review_tech_design_from_pm`，**不**含 `review_tech_design_from_qa` | `assert "from_pm" in loader.description; assert "from_qa" not in loader.description` | — |
| T-SL-10 | shared skill 所有 role 均可见（v1.5-A1） | SkillLoader(role=任一) | description XML 含 `self_retrospective` / `self_score` | `for role in roles: assert "self_retrospective" in SkillLoader(role).description` | — |
| T-SL-11 | list_available_sops 只返列表不做选择（v1.5-A3） | 调用 list_available_sops 脚本 | 返回 `{sops: [{name, description, kind}], total_count}`；不含 `matched_sop` 字段 | `result = list_sops(); assert "matched_sop" not in result; assert isinstance(result["sops"], list)` | — |
| T-SL-12 | skill_crystallize 名字不与 claude-code 社区 skill-creator 冲突（v1.5-A6） | SkillLoader(role=任一) | description 含 `skill_crystallize` 不含 `skill-creator` | `assert "skill-creator" not in loader.description; assert "skill_crystallize" in loader.description` | — |

#### CronService

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-CR-01 | at cron 1s 触发 Runner | create_job(at=now+1s) | 1.5s 内 Runner 收到 InboundMessage | `asyncio.wait_for(event.wait(), 2.0)` | R-F-02 |
| T-CR-02 | cron wake 去重，重复 heartbeat 被丢弃 | 队列中已有 pending wake_reason=heartbeat | 新 heartbeat 不入队（dispatch 返回不入队） | `assert queue.qsize() == 1` | R-F-02 |
| T-CR-03 | at cron delete_after_run 后不重复触发 | at cron with delete_after_run=True | 只触发一次 | `assert triggered_count == 1` | R-F-04 |
| T-CR-04 | 4 角色 heartbeat 有 jitter，不同相 | 注册 4 × every 30s + jitter 5s | 4 次触发时间差 > 0（非同时） | `timestamps = [t1,t2,t3,t4]; assert max(timestamps) - min(timestamps) > 0` | R-H-07 |
| T-CR-05 | tasks.json mtime 热重载捕获新 job | 外部写 tasks.json 新增一条 | CronService 下一个 tick 后注册新 job | `assert new_job_id in cron._active_timers` | R-F-04 |

#### Runner

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-RN-01 | team:manager routing_key 路由正确 | dispatch(InboundMessage(routing_key="team:manager")) | manager_agent_fn 被调用 | `mock_manager_fn.assert_called_once()` | R-F-02 |
| T-RN-02 | team:{role} session_id 固定 | dispatch team:pm with workspace_id="test-001" | session_id == "team-pm-test-001" | `assert session_id == "team-pm-test-001"` | R-M-07 |
| T-RN-03 | p2p:{open_id} session_id 走 SessionManager | dispatch p2p:ou_abc 两次 | 两次 session_id 相同（复用 active session） | `assert sid1 == sid2` | R-M-07 |
| T-RN-04 | 同 routing_key 消息串行 | 快速发 3 条 team:rd | 3 次 agent_fn 按序执行，不并发 | `order = []; assert order == [0, 1, 2]` | — |

#### Bootstrap

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-BS-01 | 4 文件注入 backstory | soul/user/agent/memory.md 均存在 | backstory 含 `<soul>` `<user_profile>` `<agent_rules>` `<memory_index>` | `for tag in tags: assert tag in backstory` | R-M-01 |
| T-BS-02 | team_protocol.md 可选注入 | shared_protocol 路径不存在 | backstory 无 `<team_protocol>` 节，无异常 | `assert "<team_protocol>" not in backstory` | R-M-01 |
| T-BS-03 | workspace .git 缺失时 cfg.features.retro_auto_commit=False | workspace/.git/ 不存在 | cfg.features.retro_auto_commit == False；启动时 log.warning | `assert cfg.features.retro_auto_commit is False` + `assert "非 git 仓库" in warn_msg` | R-F-05, R-L-03 |

#### pgvector

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-PG-01 | async_index_turn 写入 role/project_id metadata | async_index_turn(role="pm", project_id="proj-001") | memories 表 role="pm", project_id="proj-001" | `SELECT role, project_id FROM memories WHERE session_id=...` | R-H-08 |
| T-PG-02 | Manager 跨角色查询 | 写入 role=pm/rd/qa 各一条 | WHERE role IN ('pm','rd','qa') 返回 3 条 | `assert len(rows) == 3` | R-H-08 |
| T-PG-03 | db_dsn 为空时静默跳过 | MEMORY_DB_DSN 未设置 | async_index_turn 无异常，返回 None | `await async_index_turn(...); assert True` | — |

### 3.2 团队协作层测试点

编号前缀：T-MB（Mailbox）, T-EL（EventLog）, T-FB（FeishuBridge）, T-CP（CreateProject）

#### Mailbox

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-MB-01 | send_mail 写入 mailbox.json + 注册 at cron | send_mail(to="pm", type_="task_assign") | pm.json 含新消息；tasks.json 含 at=now+1s job | `assert any(m["type"]=="task_assign" for m in mailbox)` | R-F-04 |
| T-MB-02 | read_inbox 过滤 unread，标 in_progress | mailbox 含 unread + in_progress + done | 只返回 unread 消息；返回后该消息 status=in_progress | `msgs = read_inbox(); assert all(m["status"]=="in_progress" for m in msgs)` | — |
| T-MB-03 | mark_done 正确完成三态转换 | in_progress 消息 | status 变为 done | `mark_done(msg_id); assert mailbox[msg_id]["status"]=="done"` | R-H-04 |
| T-MB-04 | mark_done 非 in_progress 消息报错 | unread 消息 mark_done | 抛异常或返回错误 | `with pytest.raises(ValueError): mark_done(unread_msg_id)` | R-H-04 |
| T-MB-05 | FileLock 保护并发写 | 两个线程同时 send_mail | 两条消息均写入，无冲突 | `assert len(mailbox) == 2` | R-F-04 |
| T-MB-06 | 空 inbox 返回空列表 | mailbox.json 只有 done/in_progress | read_inbox 返回 [] | `assert read_inbox() == []` | — |

#### EventLog

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-EL-01 | append_event 写入合法 JSON Lines | append_event("project_created", {}) | events.jsonl 新增一行合法 JSON | `line = last_line(path); json.loads(line)` | R-F-01 |
| T-EL-02 | seq 严格递增 | append_event × 3 | seq 依次 1, 2, 3 | `seqs = [e["seq"] for e in events]; assert seqs == sorted(seqs)` | R-F-01 |
| T-EL-03 | 崩溃半写自愈（最后行非合法 JSON）| 手动写入半行 JSON | read_project_state 跳过并告警，不崩溃 | `state = read_project_state(); assert state is not None` | R-F-01 |
| T-EL-04 | archived 项目不被 _get_current_project_id 选中 | events.jsonl 最后行 action="archived" | _get_current_project_id 返回 None 或其他项目 | `assert cid != archived_pid` | R-H-02 |
| T-EL-05 | filelock 并发 append 无损坏 | 两个协程同时 append_event | 两行均合法 JSON | `events = [json.loads(l) for l in lines]; assert len(events) == 2` | R-F-01 |

#### FeishuBridge

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-FB-01 | classify 卡片按钮优先 | feishu_msg 带 action.value.decision="approved" | 返回 "approved" | `assert classify(msg) == "approved"` | R-H-03 |
| T-FB-02 | classify 文本关键词 | text="同意" | 返回 "approved" | `assert classify_text("同意") == "approved"` | R-H-03 |
| T-FB-03 | classify 歧义文本兜底 | text="这个需求不太对，我们再讨论" | 返回 "need_discussion"（不误判） | `assert classify_text("这个需求不太对") == "need_discussion"` | R-H-03 |
| T-FB-04 | recv_human_response 有 pending checkpoint | events.jsonl 含未 approved 的 checkpoint_requested | 写入 checkpoint_response 到 manager.json；返回 "consumed_as_checkpoint" | `result = recv(...); assert result == "consumed_as_checkpoint"` | — |
| T-FB-05 | recv_human_response 无 pending checkpoint | events.jsonl 无 pending | 返回 None，走常规飞书消息路径 | `assert recv(...) is None` | — |

#### CreateProject

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-CP-01 | 创建完整目录结构 | CreateProjectTool("proj-001") | needs/ design/ tech/ code/ qa/ reviews/ mailboxes/ 均存在；mailboxes/manager.json 等 4 文件存在且为空列表 | `for d in dirs: assert (root/d).exists()` | R-M-03 |
| T-CP-02 | events.jsonl 初始化为空文件 | CreateProjectTool("proj-001") | events.jsonl 存在且内容为空 | `assert events_path.stat().st_size == 0` | R-M-03 |
| T-CP-03 | 重复创建幂等 | CreateProjectTool("proj-001") 调用两次 | 不报错；目录结构无损坏 | `create twice; assert dirs same` | — |

### 3.3 主 Agent × Skill 边界测试点

编号前缀：T-WS（WriteShared/ReadShared）, T-RS（ReadShared）, T-SOP（SOP 推进）

#### WriteShared / ReadShared

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-WS-01 | PM 写 design/ 通过 | WriteSharedTool(role="pm", path="design/product_spec.md") | 写入成功 | `assert file.exists()` | — |
| T-WS-02 | PM 写 code/ 被拒 | WriteSharedTool(role="pm", path="code/app.py") | PermissionError | `with pytest.raises(PermissionError)` | R-M-04 |
| T-WS-03 | QA 写 reviews/code/qa_review.md 通过 | WriteSharedTool(role="qa", path="reviews/code/qa_review.md") | 写入成功 | `assert file.exists()` | R-H-06 |
| T-WS-04 | QA 写 reviews/code/rd_review.md 被拒 | WriteSharedTool(role="qa", path="reviews/code/rd_review.md") | PermissionError（文件名 rd_ 前缀） | `with pytest.raises(PermissionError)` | R-H-06 |
| T-WS-05 | reviews/ 路径缺 _topic 被拒 | WriteSharedTool(role="manager", path="reviews/stage/manager.md") | PermissionError（缺下划线+topic） | `with pytest.raises(PermissionError)` | R-H-06 |
| T-RS-01 | ReadShared 任意角色可读 shared 目录 | ReadSharedTool(role="rd", path="design/product_spec.md") | 返回文件内容 | `assert "功能清单" in content` | — |

#### SOP 推进

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-SOP-01 | read_project_state 返回正确摘要 | events.jsonl 含 project_created + assigned(to=pm) | 摘要含 "assigned" "pm" | `assert "pm" in state` | — |
| T-SOP-02 | check_review_criteria 数实体 + 接口 | requirements.md 含 "## 数据实体" + 3 个实体章节 + 7 个 API 行 | 返回 `{entities: 3, apis: 7}` | `result = check_criteria(); assert result["entities"] == 3` | R-M-10 |
| T-SOP-03 | 评审超 max_rounds，流程上报 error_alert | events.jsonl 中 revision_requested.round == 3 + 新 review_done(need_changes) | append_event("error_alert_raised") | `assert events_count("error_alert_raised") >= 1` | R-M-05 |

### 3.4 进化闭环测试点

编号前缀：T-RET（retro 流程，v1.4 替代原 T-AP）, T-REV（评审/分档审批）, T-SS（self_score）, T-LOG（日志）

#### Retro 流程（v1.1 重写，对齐 v1.4 Agent 自执行）

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-RET-01 | self_retrospective 产出 RetroProposal JSON | seed L2（8 task 含 3 个低 quality）+ seed L1（3 条 "时区没说清"） | 产出 `shared/proposals/pm_retro_{date}.json`，含 retrospective_report + ≥1 条 improvement_proposals | `assert json.loads(proposal_file)["improvement_proposals"][0]["root_cause"] in {"sop_gap","prompt_ambiguity","ability_gap","integration_issue"}` | R-M-08 |
| T-RET-02 | 样本不足跳过复盘 | seed L2 仅 3 task（< min_tasks_for_retro=5） | improvement_proposals 为空数组；retrospective_report.summary 含"样本不足" | `assert proposal["improvement_proposals"] == []` | — |
| T-RET-03 | retro_approved 机械执行：锚点匹配 | before_text 在 target_file 中精确存在 | target_file 被替换 after_text；发 retro_applied 回 Manager | `assert after_text in target_file.read_text()` + `assert mail_type("retro_applied") == 1` | R-F-03 |
| T-RET-04 | retro_approved 执行：锚点不匹配 | before_text 在 target_file 中找不到（被并发改过） | 发 retro_apply_failed 邮件回 Manager；target_file 不变 | `assert events_count("retro_apply_failed") == 1` + `assert before_text not in target_file.read_text()` | R-F-03 |
| T-RET-05 | workspace 非 git 时 retro apply 不 commit（soft skip） | cfg.features.retro_auto_commit=False | 文件仍被替换；无 git commit 尝试；无异常抛出 | `assert after_text in target_file.read_text()` + `mock_subprocess_run.assert_not_called()` | R-F-05, R-L-03 |
| T-RET-06 | workspace 是 git 时 retro apply 后自动 commit | cfg.features.retro_auto_commit=True | 文件被替换 + git log 含 `[retro][pm]` commit | `assert "[retro][pm]" in git_log()` | — |

#### 评审与分档审批（v1.1 重写，对齐 v1.4 分档）

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-REV-01 | review_proposal checklist: evidence 非空 | improvement_proposals[0].evidence = [] | 返回 verdict=reject, reject_reason=evidence_empty | `assert review["decisions"][0]["action"] == "reject"` | R-M-09 |
| T-REV-02 | review_proposal checklist: target_file 存在 | target_file="workspace/nonexist/foo.md" | 返回 verdict=reject, reject_reason=target_file_not_exist | `assert review["decisions"][0]["reject_reason"] == "target_file_not_exist"` | R-M-09 |
| T-REV-03 | 档 1 自动批：memory.md 改动 | target_file="workspace/pm/memory.md" + 当天 retro_approved_by_manager count=0 | action=auto_approve，append `retro_approved_by_manager`，直接 send_mail(retro_approved) | `assert events_count("retro_approved_by_manager") == 1` + `assert not send_to_human.called` | — |
| T-REV-04 | 档 1 闸门：当天已 3 条降级到档 2 | target_file=memory.md + 当天 retro_approved_by_manager count=3 | action=tier1_quota_exceeded_fallback_human，进入 pending_human | `assert review["decisions"][0]["action"] == "tier1_quota_exceeded_fallback_human"` | — |
| T-REV-05 | 档 2 转 Human：skills/*.md 改动 | target_file="workspace/pm/skills/product_design/SKILL.md" | action=require_human, send_to_human(proposal_review)，等 checkpoint_response | `assert send_to_human.called with type="proposal_review"` | — |
| T-REV-06 | 档 3 转 Human + risk_flag：soul.md 改动 | target_file="workspace/pm/soul.md" | action=require_human + risk_flag=high | `assert review["decisions"][0]["tier"] == 3` + `assert send_to_human.call_args.kwargs["risk_flag"] == "high"` | — |

#### self_score（v1.1 新增）

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-SS-01 | self_score 5 维加权计算正确 | breakdown={completeness:1.0, self_review:0.9, hard_constraints:1.0, clarity:0.7, timeliness:0.8} | self_score = 0.2+0.27+0.2+0.105+0.12 = 0.895 | `assert abs(computed - 0.895) < 0.01` | — |
| T-SS-02 | 漏调 self_score 时 L2 quality_estimate 为 null | task_done content 缺 self_score 字段 | L2 entry result_quality_estimate=null；result_quality_source=null | `assert l2_entry["result_quality_estimate"] is None` | — |
| T-SS-03 | 下游 need_changes 反馈扣分 | review_received(need_changes)，引用 task_id=t001（其 L2 self_score=0.85）| Manager append task_quality_adjusted(task_id=t001, adjustment=-0.2)；find_low_quality 查询时 final=0.65 | `assert events_count("task_quality_adjusted") == 1` + `assert final_quality(t001) == 0.65` | — |
| T-SS-04 | 硬约束违反扣分强制 | breakdown.hard_constraints=0.9（理应 ≤0.5） | self_score skill 告警 + Manager LLM 可质疑 | Manual check in Journey | — |

#### 日志

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-LOG-01 | task_callback 写 L2 日志含 project_id | kickoff 完成，_get_current_project_id 可推断 | L2 条目 project_id 非 None | `assert l2_entry["project_id"] is not None` | R-H-02 |
| T-LOG-02 | 多项目并存时 L2 写到正确项目 | 两个项目目录，一个 archived | L2 写到未 archived 项目 | `assert l2_entry["project_id"] == active_pid` | R-H-02 |
| T-LOG-03 | l1_human 目录不存在时自动创建 | ensure_workspace_dirs 跳过 l1_human | send_to_human 时创建目录并写入 | `assert l1_dir.exists()` | R-L-02 |
| T-LOG-04 | L2 result_quality_estimate 来自 self_score | task_done content 含 `{self_score: 0.82, breakdown: {...}}` | L2 entry result_quality_estimate=0.82, result_quality_breakdown=含 5 维, result_quality_source="self_score_skill" | `assert l2_entry["result_quality_estimate"] == 0.82` | — |
| T-LOG-05 | L1 entry 含完整 12 字段（v1.3-P0-1 schema） | send_to_human(type=checkpoint_request, ...) | L1 entry 含 ts/action/direction/project_id/user_open_id/role/ck_id/content/artifacts 全字段 | `for k in L1_REQUIRED: assert k in l1_entry` | R-H-11 |

### 3.5 权限与单一接口测试点

编号前缀：T-PERM（权限）, T-UI（单一接口）

#### 权限隔离

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-PERM-01 | check_write OWNER_BY_PREFIX 表完整 | 所有前缀 needs/design/tech/code/qa/ | 各自只允许正确 owner role | `for role, path, ok in cases: assert check_write(role, path) == ok` | R-H-06 |
| T-PERM-02 | reviews/ 正则：role 前缀严格匹配 | reviews/code/qa_fix_notes.md（role=qa） | 通过 | `check_write("qa", "reviews/code/qa_fix.md")` | R-H-06 |
| T-PERM-03 | reviews/ 正则：错误 role 前缀被拒 | reviews/code/pm_notes.md（role=qa） | PermissionError | `with pytest.raises(PermissionError): check_write("qa","reviews/code/pm_notes.md")` | R-H-06 |
| T-PERM-04 | reviews/ 缺 _topic 被拒 | reviews/stage/manager.md | PermissionError | `with pytest.raises(PermissionError): check_write("manager","reviews/stage/manager.md")` | R-H-06 |
| T-PERM-05 | RD 写 design/ 被拒 | check_write("rd", "design/spec.md") | PermissionError | `with pytest.raises(PermissionError)` | R-M-04 |

#### 单一接口

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-UI-01 | build_role_tools(pm) 不含 SendToHumanTool | build_role_tools("pm", cfg, sender=None) | tools 列表无 SendToHumanTool | `assert not any(isinstance(t, SendToHumanTool) for t in tools)` | — |
| T-UI-02 | build_role_tools(rd) 不含 AppendEventTool | build_role_tools("rd", cfg) | tools 列表无 AppendEventTool | `assert not any(isinstance(t, AppendEventTool) for t in tools)` | — |
| T-UI-03 | build_role_tools(manager) 含完整 Manager 工具集（v1.4 取消 ApplyProposalTool） | build_role_tools("manager", cfg, sender=mock_sender) | tools 含 CreateProjectTool/AppendEventTool/SendToHumanTool；**不**含 ApplyProposalTool | `tool_types = {type(t) for t in tools}; assert SendToHumanTool in tool_types; assert not any("ApplyProposal" in type(t).__name__ for t in tools)` | — |
| T-UI-04 | build_role_tools(pm) 不含 Manager 专属工具 | build_role_tools("pm", cfg, sender=None) | tools 不含 CreateProjectTool/AppendEventTool/SendToHumanTool | `assert SendToHumanTool not in tool_types` | R-H-05 |
| T-UI-05 | shared skills 可被所有 role load | SkillLoader(role="pm").list_available() | 返回列表含 self_retrospective + self_score | `assert "self_retrospective" in [s["name"] for s in available]` | — |
| T-UI-04 | build_role_tools(pm) 不传 sender 不报错 | build_role_tools("pm", cfg, sender=None) | 正常返回 6 个工具 | `assert len(tools) == 6` | — |

### 3.6 数据与审计测试点

编号前缀：T-MG（Memory 综合）, T-FL（FeishuListener）

#### Memory 综合

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-MG-01 | ctx.json 跨 wake 恢复（team session 固定 id）| kickoff 1 生成 ctx.json；kickoff 2 新实例 | 第 2 次 @before_llm_call 恢复 ctx.json 历史 | `assert len(messages_at_kick2) > 0` | R-M-07 |
| T-MG-02 | memory.md 截断 200 行 | memory.md = 300 行 | backstory 中 memory_index 节最多 200 行 | `lines = extract_memory_section(backstory); assert len(lines) <= 200` | — |
| T-MG-03 | context > 45% 触发 compress | 构造超阈值 messages | maybe_compress 被调用；ctx.json 更新 | `assert compress_called` | — |

#### FeishuListener

| ID | 测试点 | 输入/前置 | 预期 | 断言方式 | 覆盖风险 |
|----|-------|----------|------|---------|---------|
| T-FL-01 | p2p 消息解析 routing_key | im.message.receive_v1 事件 msg_type=text | routing_key = "p2p:{open_id}" | `assert msg.routing_key == f"p2p:{oid}"` | — |
| T-FL-02 | post 富文本提取纯文本 | msg_type=post | _extract_post_text 返回无 JSON 的干净文本 | `assert "<" not in text` | — |
| T-FL-03 | allowed_chats 白名单过滤 | group 消息，chat_id 不在白名单 | 消息被丢弃，不进 Runner | `assert not runner_received.is_set()` | — |

---

## 4. 可测性评估

### 4.1 高可测组件（纯函数/简单 IO）

| 组件 | 可测性 | 测试策略 |
|------|-------|---------|
| `mailbox.py` 三态状态机 | ★★★★★ | 单元测试：直接调函数，tmp_path 提供文件 |
| `event_log.py` append + filelock | ★★★★★ | 单元测试：mock filelock 或真实 tmp 文件 |
| `workspace.py` check_write | ★★★★★ | 纯函数：参数化路径 × role 组合，无副作用 |
| `feishu_bridge.classify()` | ★★★★★ | 纯函数：覆盖 20+ 输入组合 |
| `create_project.py` | ★★★★☆ | 单元测试：tmp_path，断言目录树 |
| `SkillLoader._build_description` | ★★★★☆ | 单元测试：mock manifest 文件 |
| `SkillLoader.reload_if_changed` | ★★★★☆ | 单元测试：修改 mtime，断言 cache 清空 |
| `bootstrap.build_bootstrap_prompt` | ★★★★★ | 单元测试：tmp workspace 文件，断言 XML 节 |
| `apply_proposal.py` checksum 校验 | ★★★★★ | 单元测试：mock git subprocess，断言文件内容 |
| `runner.resolve_session_id` | ★★★★★ | 单元测试：参数化 routing_key |

### 4.2 中等可测组件（需要异步 / 文件系统协作）

| 组件 | 可测性 | 测试策略 |
|------|-------|---------|
| `CronService` at/every 触发 | ★★★☆☆ | 集成测试：asyncio.sleep(2s)；mock dispatch_fn |
| `Runner.dispatch` cron 去重 | ★★★★☆ | 集成测试：直接调 dispatch，检查 queue size |
| `send_mail` + at cron 联动 | ★★★☆☆ | 集成测试：mock _tasks_store.create_job，验证调用参数 |
| `feishu_bridge.recv_human_response` | ★★★★☆ | 集成测试：构造 mock events.jsonl，验证 mailbox 写入 |
| `async_index_turn` pgvector 写入 | ★★★☆☆ | 集成测试：需要真实 pgvector 容器 |

### 4.3 低可测组件（依赖 LLM 推理）

| 组件 | 可测性 | 测试策略 |
|------|-------|---------|
| Manager LLM kickoff（SOP 推进决策） | ★★☆☆☆ | E2E：不断言决策过程，只断言最终产物（文件存在 + events 事件） |
| Sub-Crew task skill（SKILL.md 执行质量） | ★★☆☆☆ | E2E：不断言 LLM 生成质量，只断言：文件存在、pytest exitcode=0、coverage 数字 |
| self_retrospective 提案质量 | ★☆☆☆☆ | 人工验证 + 结构断言（提案 JSON schema 校验） |

### 4.4 Mock / Stub 清单

| 依赖 | Mock 方式 | 说明 |
|------|----------|------|
| `FeishuSender.send_card` | `MagicMock(return_value="msg-001")` | 集成测试不发真实飞书 |
| `FeishuSender.send` | `MagicMock()` | 同上 |
| AIO-Sandbox Sub-Crew | `mock_build_skill_crew(return skill_result_stub)` | 工具层集成测试不需要真沙盒 |
| LLM（AliyunLLM） | `MagicMock(return_value=AgentFinish(...))` | 单元/集成测试不消耗 API quota |
| `subprocess.run(git ...)` | `MagicMock(returncode=0)` | ApplyProposalTool 单元测试 |
| `_tasks_store.create_job` | `MagicMock()` | SendMailTool 单元测试，验证调用参数 |
| `pgvector` DSN | 环境变量 MEMORY_DB_DSN；未设置时静默 skip | pgvector 相关测试需容器 |
| `filelock.FileLock` | 真实 FileLock（tmp_path）或 `MagicMock` | 并发测试用真实 lock；单元测试可 mock |

---

## 5. 自动化测试方案

### 5.1 单元测试

目标：覆盖所有工具层纯函数，覆盖率 ≥ 85%。不依赖 LLM、沙盒、飞书。

```bash
# 运行单元测试（无外部依赖）
pytest tests/unit/ -v --cov=xiaopaw_team --cov-report=term-missing
```

关键测试模块：

| 文件 | 覆盖模块 | 预期用例数 |
|------|---------|-----------|
| `test_mailbox.py` | tools/mailbox.py | 15 |
| `test_event_log.py` | tools/event_log.py | 10 |
| `test_workspace_permissions.py` | tools/workspace.py | 20 |
| `test_feishu_bridge_classify.py` | tools/feishu_bridge.py classify() | 15 |
| `test_skill_loader.py` | tools/skill_loader.py | 20 |
| `test_bootstrap.py` | memory/bootstrap.py | 10 |
| `test_apply_proposal.py` | tools/apply_proposal.py | 12 |
| `test_session_id.py` | runner.py resolve_session_id | 8 |
| `test_create_project.py` | tools/create_project.py | 8 |

### 5.2 集成测试（无 LLM）

目标：验证组件间联动，不消耗 LLM API。用 TestAPI（`POST /api/test/message`）+ mock agent_fn 驱动。

```bash
# 运行集成测试（无 LLM）
pytest tests/integration/ -m "not llm" -v --timeout=60
```

关键测试文件：

| 文件 | 覆盖场景 | marker |
|------|---------|--------|
| `test_mailbox_chain.py` | send → read → mark 完整三态 + FileLock 并发 | `not llm` |
| `test_project_state.py` | events 推断状态 + 崩溃半写自愈 | `not llm` |
| `test_wake_chain.py` | send_mail → at cron 1s 后 Runner 收消息 | `not llm` |
| `test_cron_dedup.py` | heartbeat 去重 + at cron 不重叠 | `not llm` |
| `test_role_isolation.py` | WriteShared 完整权限矩阵（4 role × 7 path） | `not llm` |
| `test_single_interface.py` | PM/RD/QA build_role_tools 无 feishu 工具 | `not llm` |
| `test_manifest_reload.py` | mtime 变化 → 热重载 → _instruction_cache 清空 | `not llm` |
| `test_feishu_bridge.py` | recv_human_response 两路径（pending/无pending）| `not llm` |
| `test_apply_proposal_chain.py` | checksum 校验 → apply → git commit → stale 测试 | `not llm` |

### 5.3 E2E 测试（真实 LLM）

目标：验证真实 LLM kickoff 下关键路径，仅测结构性断言，不测内容质量。

```bash
# 需要 QWEN_API_KEY + sandbox 容器
export QWEN_API_KEY=sk-xxx
docker compose -f sandbox-docker-compose.yaml up -d
pytest tests/integration/ -m "llm" -v -s --timeout=600
```

| 文件 | 覆盖场景 | 耗时估计 | marker |
|------|---------|---------|--------|
| `test_manager_req_checkpoint.py` | M5：需求澄清 → checkpoint → 确认 | 3-5 min | `llm sandbox` |
| `test_pm_design_cycle.py` | 阶段 2：PM 产品设计 → RD/QA 评审 → checkpoint | 10-15 min | `llm sandbox` |
| `test_rd_code_impl.py` | 阶段 3：RD tech_design + code + pytest PASS | 15-30 min | `llm sandbox` |
| `test_qa_test_run.py` | 阶段 4：QA 代码走查 + 执行测试 | 10-20 min | `llm sandbox` |
| `test_evolution.py` | M7：seed L1/L2 → retro → proposal → apply | 10-15 min | `llm sandbox` |

### 5.4 目录结构

```
tests/
├── unit/
│   ├── conftest.py              # tmp_path fixtures, mock helpers
│   ├── test_mailbox.py
│   ├── test_event_log.py
│   ├── test_workspace_permissions.py
│   ├── test_feishu_bridge_classify.py
│   ├── test_skill_loader.py
│   ├── test_bootstrap.py
│   ├── test_apply_proposal.py
│   ├── test_session_id.py
│   └── test_create_project.py
├── integration/
│   ├── conftest.py              # TestAPI client, seed_events, sandbox check
│   ├── test_mailbox_chain.py
│   ├── test_project_state.py
│   ├── test_wake_chain.py
│   ├── test_cron_dedup.py
│   ├── test_role_isolation.py
│   ├── test_single_interface.py
│   ├── test_manifest_reload.py
│   ├── test_feishu_bridge.py
│   ├── test_apply_proposal_chain.py
│   ├── test_manager_req_checkpoint.py   # llm marker
│   ├── test_pm_design_cycle.py          # llm marker
│   ├── test_rd_code_impl.py             # llm marker
│   ├── test_qa_test_run.py              # llm marker
│   └── test_evolution.py               # llm marker
├── e2e/
│   ├── conftest.py
│   ├── test_smoke_journey.py
│   ├── test_review_loop_journey.py
│   └── test_evolution_journey.py
└── fixtures/
    ├── seed_events.py           # 事件流预置工厂
    ├── seed_mailboxes.py        # 邮箱预置工厂
    ├── fake_feishu_msg.py       # 飞书消息 stub
    └── workspace_templates/    # workspace 初始文件模板
```

### 5.5 CI 配置

```yaml
# .github/workflows/test.yml（简化版）
name: Test
on: [push, pull_request]
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -e ".[test]"
      - run: pytest tests/unit/ -v --cov=xiaopaw_team --cov-fail-under=80

  integration-no-llm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -e ".[test]"
      - run: pytest tests/integration/ -m "not llm" -v --timeout=60

  # LLM + E2E 测试仅在手动触发时运行
  e2e:
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    services:
      sandbox: {image: ghcr.io/agent-infra/sandbox:latest, ports: ["8022:8080"]}
    env:
      QWEN_API_KEY: ${{ secrets.QWEN_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -e ".[test]"
      - run: pytest tests/integration/ -m "llm" -v -s --timeout=600
```

---

## 6. 功能测试 Case

### 6.1 阶段 0：SOP 共创

#### C-STG0-01: 用户发起 SOP 共创，Manager 加载 sop_cocreate_guide（✅ 正常）

- **前置**：workspace 已初始化；manager skills 含 sop_cocreate_guide（reference）；无 active project
- **步骤**：
  1. 用户飞书发 "我们来建一个小功能开发的 SOP 吧，想规范一下从需求到交付的流程"
  2. Manager kickoff：read_inbox（空）→ read_project_state（无项目）→ SkillLoader 匹配 sop_cocreate_guide
  3. Manager 加载 reference skill，获得 5 维对话框架
  4. Manager 调 SendToHumanTool 发第 1 问
- **预期**：
  - Manager 回复含引导性问题（如"这个 SOP 主要用于什么场景？"）
  - 不直接创建文件（仅是对话框架加载）
  - events.jsonl 无新事件（SOP 共创阶段无项目）
- **断言**：
  - `assert "SOP" in reply or "场景" in reply or "流程" in reply`
  - `assert not Path(workspace/"shared/projects").exists() or project_dirs == []`
- **覆盖**：T-SL-01, T-SL-08

---

#### C-STG0-02: 5 维对话完成，调 sop_write 生成 SKILL.md（✅ 正常）

- **前置**：C-STG0-01 已完成；5 维对话（场景/角色/步骤/产物/结束条件）已覆盖
- **步骤**：
  1. 接续 C-STG0-01 的 session，用户回复完成 5 维（目标/角色/步骤/边界/产物）
  2. Manager LLM 判断"5 维覆盖"→ 调 load_skill("sop_write", task_context=摘要)
  3. Sub-Crew 生成 workspace/manager/skills/sop_feature_dev/SKILL.md
  4. Sub-Crew 追加 load_skills.yaml 条目
  5. mtime 热重载触发，SkillLoader _build_description 重跑
  6. Manager 调 SendToHumanTool(type=checkpoint_request)
- **预期**：
  - `workspace/manager/skills/sop_feature_dev/SKILL.md` 存在
  - `load_skills.yaml` 含 `name: sop_feature_dev` 条目
  - SkillLoader `_skill_registry` 热重载后含 sop_feature_dev
  - 飞书收到 checkpoint 卡片
- **断言**：
  - `assert (workspace/"manager/skills/sop_feature_dev/SKILL.md").exists()`
  - `assert any(s["name"]=="sop_feature_dev" for s in yaml.safe_load(manifest)["skills"])`
  - `assert "sop_feature_dev" in loader._skill_registry` (after mtime reload)
- **覆盖**：T-SL-05, T-SL-06, T-CP-01

---

#### C-STG0-03: 用户中途取消 SOP 共创（❌ 异常）

- **前置**：C-STG0-01 已触发对话框架
- **步骤**：
  1. Manager 发出第 1 问后，用户回复"不用了，先做正事"
  2. Manager 读 history，判断用户取消意图
- **预期**：
  - Manager 不继续 SOP 共创流程
  - 不调用 sop_write（无 Sub-Crew 启动）
  - Manager 友好确认
- **断言**：
  - `assert not (workspace/"manager/skills/sop_feature_dev/SKILL.md").exists()`
  - `assert "sop" not in events`（无 sop_created 事件）
- **覆盖**：T-FB-05

### 6.2 阶段 1：需求澄清

#### C-STG1-01: 用户正常发起新需求，Manager 正确初始化项目并澄清（✅ 正常）

- **前置**：workspace 已初始化；sop_feature_dev SKILL.md 存在；无 active project
- **步骤**：
  1. 用户飞书发 "帮我做个宠物日记小网站，能记录多只宠物，每只宠物有日记时间线"
  2. Manager kickoff：read_inbox → read_project_state（无项目）→ 匹配 list_available_sops → 语义匹配 sop_feature_dev
  3. Manager 生成 project_id，调 CreateProjectTool
  4. Manager 调 AppendEventTool(action="project_created")
  5. Manager 加载 requirements_guide（reference），开始四维发问
  6. Manager 调 SendToHumanTool 发第 1 问
- **预期**：
  - `workspace/shared/projects/proj-*/` 目录结构完整（needs/ design/ ... mailboxes/ events.jsonl）
  - `events.jsonl` 含 project_created 事件
  - Manager 回复包含引导性问题（目标/边界/约束/风险之一）
- **断言**：
  - `assert events_count("project_created") == 1`
  - `assert (proj_dir/"mailboxes/pm.json").exists()`
  - `assert (proj_dir/"events.jsonl").exists()`
  - `assert any(kw in reply for kw in ["用户", "功能", "约束", "规模", "什么"])`
- **覆盖**：T-CP-01, T-CP-02, T-EL-01, T-SOP-01

---

#### C-STG1-02: 四维澄清完成，Manager 调 requirements_write 生成需求文档（✅ 正常）

- **前置**：C-STG1-01 已完成；3 轮对话已覆盖目标/边界/约束/风险
- **步骤**：
  1. 用户回答完最后一个问题（"心情字段 happy/normal/sad 三档就好"）
  2. Manager 判断四维覆盖完毕 → 调 load_skill("requirements_write", task_context={...})
  3. Sub-Crew 写入 `shared/projects/{pid}/needs/requirements.md`
  4. Manager AppendEventTool(action="requirements_drafted")
  5. Manager 调 SendToHumanTool(type="checkpoint_request", title="需求文档 v1")
- **预期**：
  - `needs/requirements.md` 存在且非空
  - events.jsonl 含 requirements_drafted + checkpoint_requested(ck-001)
  - 飞书收到 checkpoint 卡片（含 Approve/Reject 按钮文字）
- **断言**：
  - `assert (proj_dir/"needs/requirements.md").stat().st_size > 100`
  - `assert events_count("requirements_drafted") == 1`
  - `assert events_count("checkpoint_requested") == 1`
  - `assert "ck-001" in get_last_checkpoint_id(events)`
- **覆盖**：T-EL-01, T-SOP-01, T-FB-04

---

#### C-STG1-03: 用户确认需求 checkpoint，Manager 进入阶段 2（✅ 正常）

- **前置**：C-STG1-02 已完成，pending checkpoint ck-001 存在
- **步骤**：
  1. 用户飞书回复 "确认" 或点击 Approve 按钮
  2. feishu_bridge.recv_human_response 识别 pending checkpoint → 写 manager.json(checkpoint_response, approved)
  3. SendMailTool 注册 at cron，1s 后 Manager 唤醒
  4. Manager kickoff：read_inbox 看到 checkpoint_response(ck-001, approved)
  5. Manager AppendEventTool(action="checkpoint_approved")
  6. 进入阶段 2（send_mail to pm）
- **预期**：
  - events.jsonl 含 checkpoint_approved(ck-001)
  - pm.json mailbox 收到 task_assign（type=task_assign）
- **断言**：
  - `assert events_count("checkpoint_approved") == 1`
  - `assert any(m["type"]=="task_assign" and m["to"]=="pm" for m in read_mailbox("pm"))`
- **覆盖**：T-FB-01, T-FB-04, T-MB-01, T-EL-01

---

#### C-STG1-04: 用户中途拒绝需求，Manager 重新澄清（❌ 异常）

- **前置**：C-STG1-02 已发出 checkpoint
- **步骤**：
  1. 用户回复 "不对，我不需要多用户，就我自己用"
  2. feishu_bridge.classify → "rejected"
  3. Manager 收 checkpoint_response(ck-001, rejected)
- **预期**：
  - events.jsonl 含 checkpoint_rejected(ck-001)
  - Manager 回复用户，提示修改方向
  - 不进入阶段 2（pm.json 无 task_assign）
- **断言**：
  - `assert events_count("checkpoint_rejected") == 1`
  - `assert all(m["type"] != "task_assign" for m in read_mailbox("pm"))`
- **覆盖**：T-FB-02, T-EL-01

---

#### C-STG1-05: Sub-Crew 沙盒失败，requirements_write 返回错误（❌ 异常）

- **前置**：sandbox 容器不可达
- **步骤**：
  1. Manager 调 load_skill("requirements_write") → Sub-Crew kickoff 失败
  2. Sub-Crew 返回错误信息（sandbox connection refused）
- **预期**：
  - Manager 向用户发 error_alert，告知需求文档生成失败
  - events.jsonl 含 error_alert_raised
  - needs/requirements.md 不存在
- **断言**：
  - `assert events_count("error_alert_raised") >= 1`
  - `assert not (proj_dir/"needs/requirements.md").exists()`
- **覆盖**：T-CP-01

### 6.3 阶段 2：产品设计

#### C-STG2-01: PM 收到任务，完成产品设计并回复 task_done（✅ 正常）

- **前置**：C-STG1-03 完成；pm.json 含 task_assign；sandbox 可达
- **步骤**：
  1. PM 被 at cron 唤醒（wake_reason=new_mail）
  2. PM：read_inbox → task_assign → load_skill("product_design") task
  3. Sub-Crew 生成 `design/product_spec.md`（含所有模板节）
  4. PM 自查通过 → write_shared → send_mail(to="manager", type_="task_done")
  5. Manager 唤醒 → check_review_criteria → 决定是否插评审
- **预期**：
  - `design/product_spec.md` 存在，含"验收标准" "数据实体"等节
  - events.jsonl 含 task_done_received(from=pm)
  - Manager 收到 task_done
- **断言**：
  - `assert (proj_dir/"design/product_spec.md").exists()`
  - `assert events_count("task_done_received") >= 1`
  - `assert events_count("decided_insert_review") >= 1`（3 实体 7 接口 ≥ 阈值）
- **覆盖**：T-MB-01, T-MB-03, T-EL-01, T-SOP-02, T-WS-01

---

#### C-STG2-02: RD 和 QA 并发评审产品文档，Manager 汇总（✅ 正常）

- **前置**：C-STG2-01 完成；events 含 decided_insert_review(reviewers=[rd,qa])
- **步骤**：
  1. Manager 发 review_request 给 RD 和 QA
  2. RD 唤醒 → load_skill("review_product_design") reference → 写 reviews/product_design/rd_review.md → send_mail(review_done, pass)
  3. QA 唤醒 → 同步，发现时区缺失 → send_mail(review_done, need_changes)
  4. Manager 收两条 review_done，汇总：QA need_changes → 发回 PM 修
- **预期**：
  - `reviews/product_design/rd_review.md` 存在
  - `reviews/product_design/qa_review.md` 存在
  - events.jsonl 含 review_received × 2 + revision_requested
  - pm.json 含 task_assign（第 2 轮，subject 含"(第 2 轮)"）
- **断言**：
  - `assert (proj_dir/"reviews/product_design/rd_review.md").exists()`
  - `assert events_count("review_received") == 2`
  - `assert events_count("revision_requested") == 1`
  - `assert "(第 2 轮)" in get_latest_mail(pm_mailbox)["subject"]`
- **覆盖**：T-WS-03, T-REV-01, T-EL-01

---

#### C-STG2-03: 评审循环超 max_rounds，触发 error_alert（❌ 异常）

- **前置**：已发生 revision_requested × 3
- **步骤**：
  1. PM 第 3 次修订仍收到 need_changes（第 4 次评审）
  2. Manager 检测到 revision_requested.round == 3 && 仍 need_changes
- **预期**：
  - Manager 调 SendToHumanTool(type=error_alert)
  - events.jsonl 含 error_alert_raised
  - 不再发 task_assign 给 PM（循环终止）
- **断言**：
  - `assert events_count("error_alert_raised") == 1`
  - `assert events_count("revision_requested") == 3`
- **覆盖**：T-SOP-03, R-M-05

---

#### C-STG2-04: 设计 checkpoint 用户拒绝，Manager 重新发 PM 修（❌ 异常）

- **前置**：两方 pass，Manager 发出 checkpoint 卡片（ck-002）
- **步骤**：
  1. 用户回复 "前端没说移动端，加上移动端适配"
  2. feishu_bridge.classify → "rejected"（或 "need_discussion"，Manager 加载 handle_checkpoint_reply skill）
  3. Manager 分析用户意见，发 pm task_assign（修订要求）
- **预期**：
  - events.jsonl 含 checkpoint_rejected(ck-002)
  - pm.json 含新 task_assign 含移动端描述
- **断言**：
  - `assert events_count("checkpoint_rejected") == 1`
  - `assert "移动端" in get_latest_mail(pm_mailbox)["content"]`
- **覆盖**：T-FB-01, T-FB-02

### 6.4 阶段 3：RD 实现

#### C-STG3-01: RD 完成技术设计 + 代码实现 + 单测（✅ 正常）

- **前置**：C-STG2 checkpoint 通过；rd.json 含 task_assign（技术设计+实现+单测）
- **步骤**：
  1. RD 唤醒 → load_skill("tech_design") task → Sub-Crew 生成 tech/tech_design.md
  2. RD load_skill("code_impl") task → Sub-Crew 写 code/ + pytest（使用 httpx.Client）
  3. Sub-Crew 确认 pytest exitcode=0, coverage ≥ 80%
  4. RD send_mail(to="manager", type_="task_done")
- **预期**：
  - `tech/tech_design.md` 存在
  - `code/` 目录非空（含 requirements.txt、main 模块）
  - events.jsonl 含 rd_delivered
  - Manager 收到 task_done
- **断言**：
  - `assert (proj_dir/"tech/tech_design.md").exists()`
  - `assert len(list((proj_dir/"code").iterdir())) > 0`
  - `assert events_count("rd_delivered") == 1`
- **覆盖**：T-WS-01, T-EL-01

---

#### C-STG3-02: RD pytest 失败 3 轮，发 error_alert（❌ 异常）

- **前置**：rd.json 含 task_assign；代码 bug 无法被 LLM 自修
- **步骤**：
  1. RD code_impl Sub-Crew 第 1-3 轮 pytest 均失败（模拟依赖装不上或逻辑 bug）
  2. 第 3 轮仍失败，Sub-Crew 返回错误信息
  3. RD send_mail(to="manager", type_="error_alert")
- **预期**：
  - 无 rd_delivered 事件
  - manager.json 含 error_alert（from=rd）
  - Manager 向用户发 error_alert 卡片
- **断言**：
  - `assert events_count("rd_delivered") == 0`
  - `assert any(m["type"]=="error_alert" for m in read_mailbox("manager"))`
- **覆盖**：T-EL-01, R-M-05

---

#### C-STG3-03: RD 尝试写 design/ 被 WriteSharedTool 拒绝（❌ 异常）

- **前置**：RD 在 code_impl Sub-Crew 中，因需求模糊尝试写 design/product_spec.md
- **步骤**：
  1. Sub-Crew 的沙盒 bash 命令写 /workspace/shared/projects/{pid}/design/product_spec.md
  2. （如通过 WriteSharedTool）WriteSharedTool.check_write("rd", "design/product_spec.md") 报错
- **预期**：
  - PermissionError 被捕获，写入失败
  - design/product_spec.md 内容不变（PM 的版本不被覆写）
- **断言**：
  - `content_before = read_shared("design/product_spec.md")`
  - `try_write_as_rd()`
  - `assert read_shared("design/product_spec.md") == content_before`
- **覆盖**：T-WS-02, T-PERM-05

### 6.5 阶段 4：QA 测试

#### C-STG4-01: QA 代码走查 → 测试设计 → 执行全通过（✅ 正常）

- **前置**：C-STG3-01 完成；qa.json 含 review_request（代码走查）
- **步骤**：
  1. QA 唤醒 → load_skill("review_code") reference → 走查 code/ → 写 reviews/code/qa_review.md（pass + 2 条非阻塞意见）
  2. QA send_mail(review_done, pass)；Manager 进入 4.2
  3. QA 收 task_assign（测试设计）→ load_skill("test_design") → 写 qa/test_plan.md
  4. QA 收 task_assign（测试执行）→ load_skill("test_run") → bash 跑 pytest → 写 qa/test_report.md
  5. pytest 全 PASS，无阻塞缺陷 → send_mail(task_done)
- **预期**：
  - `reviews/code/qa_review.md` 存在，含 pass 结论
  - `qa/test_plan.md` 存在，含用例清单
  - `qa/test_report.md` 存在，含 PASS 摘要
  - events.jsonl 含 rd_delivered 后无 error_alert
  - Manager 准备发 delivery checkpoint
- **断言**：
  - `assert "pass" in read_review("qa_review.md").lower()`
  - `assert (proj_dir/"qa/test_plan.md").exists()`
  - `assert (proj_dir/"qa/test_report.md").exists()`
  - `assert events_count("error_alert_raised") == 0`
- **覆盖**：T-WS-03, T-EL-01

---

#### C-STG4-02: QA 发现阻塞缺陷，RD 修复后回归（❌ 异常）

- **前置**：QA test_run 发现宠物删除接口返回 500
- **步骤**：
  1. QA 写 qa/defects/bug_01.md（阻塞缺陷）
  2. QA send_mail(to="manager", type_="task_done", content={"blocking_bugs": 1})
  3. Manager 判断有阻塞缺陷 → send_mail(to="rd", 修复 bug_01)
  4. RD 修复 → task_done → Manager 通知 QA 回归
  5. QA 回归 test_run，全 PASS
- **预期**：
  - `qa/defects/bug_01.md` 存在
  - events.jsonl 含 revision_requested(to=rd)
  - 最终 qa/test_report.md 更新为 PASS
- **断言**：
  - `assert (proj_dir/"qa/defects/bug_01.md").exists()`
  - `assert events_count("revision_requested") >= 1`
- **覆盖**：T-EL-01

---

#### C-STG4-03: RD 评审 test_plan 打回（❌ 异常）

- **前置**：QA 写完 test_plan.md，发 task_done；可选流程 Manager 请 RD 评审 test_design
- **步骤**：
  1. Manager 发 review_request 给 RD（评审测试设计）
  2. RD load_skill("review_test_design") → 发现测试用例无边界 case → need_changes
  3. Manager 发回 QA 修订
- **预期**：
  - events.jsonl 含 review_received(reviewer=rd, result=need_changes)
  - events.jsonl 含 revision_requested(to=qa)
- **断言**：
  - `assert get_event("review_received")["result"] == "need_changes"`
  - `assert events_count("revision_requested") >= 1`
- **覆盖**：T-EL-01, T-REV-01

### 6.6 阶段 5：交付

#### C-STG5-01: Manager 发交付 checkpoint，用户 approve（✅ 正常）

- **前置**：QA test_run 全 PASS，无阻塞缺陷
- **步骤**：
  1. Manager AppendEventTool(action="delivery_requested")
  2. Manager SendToHumanTool(type="delivery", summary=交付摘要, artifacts=[code/README.md, qa/test_report.md])
  3. 用户飞书回复 "很好，就这个" 或点 Approve
  4. Manager 收 checkpoint_response(approved) → AppendEventTool(action="delivered")
  5. Manager 进入阶段 6
- **预期**：
  - events.jsonl 含 delivery_requested + delivered
  - 飞书发出 delivery 类型卡片（含产物链接）
- **断言**：
  - `assert events_count("delivery_requested") == 1`
  - `assert events_count("delivered") == 1`
- **覆盖**：T-EL-01, T-FB-01

---

#### C-STG5-02: 用户拒绝交付，Manager 追问并重新迭代（❌ 异常）

- **前置**：Manager 发出 delivery checkpoint
- **步骤**：
  1. 用户回复 "宠物详情页面缺了心情统计图表"
  2. Manager 分析意见（加载 handle_checkpoint_reply skill）
  3. Manager 判断需要 RD 修改 → send_mail(to=rd, 加心情统计图表)
- **预期**：
  - events.jsonl 含 checkpoint_rejected
  - rd.json 含新 task_assign（含"心情统计"）
  - delivered 事件不出现
- **断言**：
  - `assert events_count("checkpoint_rejected") >= 1`
  - `assert events_count("delivered") == 0`
  - `assert "心情" in get_latest_mail("rd")["content"]`
- **覆盖**：T-FB-03

### 6.7 阶段 6：复盘进化

#### C-STG6-01: 团队复盘触发，各角色生成提案，用户 approve，apply 生效（✅ 正常）

- **前置**：C-STG5-01 完成；events.jsonl 含 delivered；L1/L2 日志有内容
- **步骤**：
  1. Manager load_skill("team_retrospective") → 获得瓶颈摘要 + 建议 [pm, rd, qa] 发 retro_trigger
  2. Manager 发 retro_trigger × 3
  3. PM/RD/QA 各自 load_skill("self_retrospective") → 生成提案
  4. 各角色 send_mail(to="manager", type_="retro_proposal")
  5. Manager 收各提案 → load_skill("review_proposals") → 3 条均合规 → 收齐
  6. Manager SendToHumanTool(type="proposals_review", 附 3 条提案)
  7. 用户批准所有提案
  8. Manager 对每条调 ApplyProposalTool → git commit
  9. Manager SendToHumanTool(type="evolution_report")
  10. Manager AppendEventTool(action="evolved") + AppendEventTool(action="archived")
- **预期**：
  - workspace SKILL 文件 version 递增（如 v1.0.0 → v1.1.0）
  - git log 含 3 个 `[proposal-xxx]` commit
  - events.jsonl 含 evolved + archived
- **断言**：
  - `assert events_count("proposal_applied") == 3`
  - `assert events_count("evolved") == 1`
  - `assert events_count("archived") == 1`
  - `log = git_log(workspace); assert log.count("[proposal-") >= 3`
- **覆盖**：T-AP-01, T-AP-03, T-AP-04, T-REV-03, T-LOG-01

---

#### C-STG6-02: evidence 空的提案被 Manager 预审拒绝（❌ 异常）

- **前置**：角色发出 retro_proposal，但提案 evidence 字段为空
- **步骤**：
  1. Manager load_skill("review_proposals") → checklist 发现 evidence=""
  2. Manager AppendEventTool(action="proposal_rejected", reason="evidence 空")
  3. 该角色提案不进汇报
- **预期**：
  - events.jsonl 含 proposal_rejected
  - proposals_review 卡片不含该提案
- **断言**：
  - `assert events_count("proposal_rejected") == 1`
- **覆盖**：T-REV-01

---

#### C-STG6-03: checksum stale 导致 apply 失败（❌ 异常）

- **前置**：提案生成后，目标 SKILL.md 被 skill-creator 修改（checksum 变化）
- **步骤**：
  1. 用户 approve 提案 → Manager 调 ApplyProposalTool
  2. ApplyProposalTool 发现当前文件 SHA256 ≠ checksum_before
  3. 返回 {"status": "stale"}
- **预期**：
  - 文件内容不变（不被错误覆写）
  - Manager 向用户发 error_alert（apply stale）
- **断言**：
  - `result = apply_proposal(...modified_file...); assert result["status"] == "stale"`
  - `assert content_after == content_before`
- **覆盖**：T-AP-02, R-F-03

---

#### C-STG6-04: 用户拒绝所有提案（❌ 异常）

- **前置**：proposals_review 卡片已发出
- **步骤**：
  1. 用户回复 "先不改，这次项目已经够了"（全部拒绝）
- **预期**：
  - events.jsonl 无 proposal_applied
  - Manager 发 evolution_report（0 条改动）
  - events.jsonl 含 archived
- **断言**：
  - `assert events_count("proposal_applied") == 0`
  - `assert events_count("archived") == 1`
- **覆盖**：T-AP-01, T-EL-01

### 6.8 Tool 级 Case

这些 case 聚焦单个 Tool 的行为，不依赖 LLM kickoff，直接调用 Tool 函数。

#### C-TOOL-01: SendMailTool 正常发邮件 + 注册 at cron（✅）

- **步骤**：直接调 `send_mail(to="pm", from_="manager", type_="task_assign", subject="产品设计", ...)`
- **预期**：pm.json 含新消息；tasks.json 含 at=now+1s job；消息 status=unread
- **断言**：`assert mailbox_msg["status"] == "unread"; assert job["schedule"]["kind"] == "at"`

#### C-TOOL-02: ReadInboxTool 空 inbox 返回 []（✅）

- **步骤**：inbox 只有 done 消息；调 read_inbox()
- **预期**：返回 []
- **断言**：`assert result == []`

#### C-TOOL-03: AppendEventTool FileNotFoundError 时自动创建 events.jsonl（✅）

- **步骤**：events.jsonl 不存在；调 append_event("project_created", {})
- **预期**：自动创建文件并写入
- **断言**：`assert path.exists(); assert json.loads(path.read_text().strip())`

#### C-TOOL-04: ApplyProposalTool git commit 消息格式（✅）

- **步骤**：apply_proposal(proposal_id="p001", root_cause="sop_gap", title="加时区规则")
- **预期**：git commit message 含 `[proposal-p001] sop_gap: 加时区规则`
- **断言**：`assert "[proposal-p001] sop_gap" in git_log()`

#### C-TOOL-05: WriteSharedTool 写入 reviews/ 不含 _topic 被拒（❌）

- **步骤**：`write_shared(role="qa", path="reviews/code/qa.md", content="...")`（缺 _topic）
- **预期**：PermissionError
- **断言**：`with pytest.raises(PermissionError)`

#### C-TOOL-06: ReadSharedTool 读不存在的文件返回错误（❌）

- **步骤**：`read_shared("design/nonexistent.md")`
- **预期**：返回错误信息（文件不存在），不崩溃
- **断言**：`result = read_shared("design/nonexistent.md"); assert "not found" in result.lower() or result.startswith("Error")`

#### C-TOOL-07: CreateProjectTool 幂等（重复创建无副作用）（✅）

- **步骤**：CreateProjectTool("proj-001") 调用两次
- **预期**：不报错；目录内容不损坏；mailboxes 文件不被清空
- **断言**：`create_project twice; assert mailbox content == initial`

#### C-TOOL-08: MarkDoneTool 顺序保证（先 append_event 后 mark_done）（✅）

- **步骤**：先 append_event("task_done_received")，再 mark_done(msg_id)
- **预期**：events.jsonl 含事件；mailbox 消息 status=done
- **断言**：`assert events_count("task_done_received") == 1; assert mailbox_msg["status"] == "done"`

### 6.9 Skill 级 Case

这些 case 测试 SkillLoader 加载/执行单个 Skill 的行为，使用 mock LLM 或真实 LLM。

#### C-SKILL-01: sop_feature_dev reference skill 返回完整正文（✅）

- **步骤**：SkillLoader._get_skill_instructions("sop_feature_dev")
- **预期**：返回字符串，包含 "阶段 1" "需求澄清" "阶段 6" "复盘"
- **断言**：`assert "阶段 1" in instructions and "阶段 6" in instructions`

#### C-SKILL-02: requirements_write task skill 产出合法 markdown（✅，需沙盒）

- **步骤**：load_skill("requirements_write", task_context={project_id, summary=...})
- **预期**：Sub-Crew kickoff 成功；needs/requirements.md 存在且含"验收标准"节
- **断言**：`assert "验收标准" in (proj_dir/"needs/requirements.md").read_text()`

#### C-SKILL-03: product_design task skill 自查通过（✅，需沙盒）

- **步骤**：load_skill("product_design", task_context={project_id, requirements_path=...})
- **预期**：design/product_spec.md 存在；skill 返回"自查通过"或正常完成消息
- **断言**：`assert (proj_dir/"design/product_spec.md").exists()`

#### C-SKILL-04: check_review_criteria 数实体与接口（✅）

- **步骤**：构造含 3 个实体 7 个接口的 requirements.md；load_skill("check_review_criteria")
- **预期**：返回 `{entities: 3, apis: 7}`（或含这些数字的文本）
- **断言**：`assert "3" in result and "7" in result`

#### C-SKILL-05: sop_selector task skill 返回可用 SOP 列表（✅）

- **步骤**：manifest 含 sop_feature_dev（kind=sop）；load_skill("sop_selector")
- **预期**：返回包含 sop_feature_dev 的列表
- **断言**：`assert "sop_feature_dev" in result`

#### C-SKILL-06: code_impl 禁止启 uvicorn（✅，需沙盒）

- **步骤**：load_skill("code_impl") → Sub-Crew 执行
- **预期**：code/ 目录下无 uvicorn 相关进程启动命令（grep 验证 SKILL.md 约束生效）
- **断言**：`assert "uvicorn" not in subprocess.check_output(["grep", "-r", "uvicorn", code_dir]).decode()`

#### C-SKILL-07: review_proposals checklist 拒绝 blast_radius 超限（❌）

- **步骤**：构造 blast_radius=10 的提案（超过 team_standards.max_blast_radius=5）
- **预期**：load_skill("review_proposals") 返回 rejected
- **断言**：`assert "blast_radius" in rejection_reason.lower() or "拒绝" in result`

---

## 7. E2E Journey

### 7.1 Smoke Journey

**目标**：验证阶段 0-2 完整流程可达，系统基本通路无阻塞。不测完整代码实现，只验证从需求到产品设计 checkpoint 的链路。

**基础设施要求**：Sandbox + QWEN_API_KEY（无需 pgvector）

**飞书消息序列**：
```
T+0s    用户 → "帮我做个宠物日记小网站，能记录多只宠物，每只宠物有日记时间线"
T+30s   Manager → [checkpoint 澄清问题，如"你希望用户登录，还是公开访问？"]
T+35s   用户 → "不用登录，就我自己用"
T+60s   Manager → [继续澄清问题，如"宠物支持哪些种类？"]
T+65s   用户 → "猫、狗、其他都要，不限种类"
T+90s   Manager → [继续澄清问题，如"心情字段有哪些选项？"]
T+95s   用户 → "心情字段 happy/normal/sad 三档就好"
T+120s  Manager → [澄清完成问题，如"还有其他需求吗？"]
T+125s  用户 → "没了，就这些"
        Manager → [调 requirements_write, 发 checkpoint 卡片]
T+180s  用户 → "确认"  （对 ck-001 需求 checkpoint）
T+181s  Manager 进入阶段 2，发 PM task_assign
T+240s  PM → [产品设计完成，Manager 收 task_done]
T+300s  Manager → [发 checkpoint 卡片 ck-002]
T+305s  用户 → "确认"
```

**关键断言节点**：

| 时间节点 | 事件/文件断言 |
|---------|-------------|
| T+0 → T+180 | events.jsonl 含 project_created + requirements_drafted + checkpoint_requested(ck-001) |
| T+180 | classify("确认") == "approved" |
| T+181 | events.jsonl 含 checkpoint_approved(ck-001) + assigned(to=pm) |
| T+181 → T+300 | `design/product_spec.md` 存在 |
| T+300 | events.jsonl 含 checkpoint_requested(ck-002) |
| T+305 | events.jsonl 含 checkpoint_approved(ck-002) |

**通过判据**：
```python
assert events_count("project_created") == 1
assert Path(proj_dir/"needs/requirements.md").exists()
assert Path(proj_dir/"design/product_spec.md").exists()
assert events_count("checkpoint_approved") >= 2
assert events_count("error_alert_raised") == 0
```

---

### 7.2 Review Loop Journey

**目标**：验证产品设计评审循环（包含 need_changes 分支），验证"循环触发 → PM 修订 → 再评审 → 最终 pass"完整链路。

**基础设施要求**：Sandbox + QWEN_API_KEY（无需 pgvector）

**飞书消息序列**（在 Smoke Journey 基础上继续）：
```
T+0s    [继承 Smoke Journey 的 ck-001 已通过状态]
T+10s   Manager → [发 review_request 给 RD + QA（产品文档有 3 实体 7 接口触发评审）]
T+90s   RD → reviews/product_design/rd_review.md（pass）
T+120s  QA → reviews/product_design/qa_review.md（need_changes: 日期字段无时区说明）
T+121s  Manager → [整理 QA 意见，发 PM task_assign 修订（第 2 轮）]
T+180s  PM → [修订 design/product_spec.md v2，添加时区说明，send_mail task_done]
T+240s  Manager → [发 review_request 给 RD + QA（第 2 轮）]
T+300s  RD → pass；QA → pass（时区问题已解决）
T+301s  Manager → [汇总 pass，发 checkpoint 卡片 ck-002]
T+310s  用户 → "确认"
```

**关键断言节点**：

| 事件节点 | 断言 |
|---------|------|
| 首次 review | events 含 decided_insert_review(reviewers=[rd,qa]) |
| QA 打回 | events 含 review_received(result=need_changes) + revision_requested(round=2) |
| PM subject | get_latest_mail("pm")["subject"] 含 "(第 2 轮)" |
| 第 2 轮全 pass | events 含 review_received × 2（均 pass） |
| checkpoint 通过 | events 含 checkpoint_approved(ck-002) |

**通过判据**：
```python
assert events_count("decided_insert_review") == 1
assert events_count("revision_requested") >= 1
assert get_last_revision_round(events) == 2
assert events_count("checkpoint_approved") >= 1  # ck-002
review_results = get_all_review_results(events)
assert all(r == "pass" for r in review_results[-2:])  # 最后一轮两方都 pass
```

---

### 7.3 Evolution Journey

**目标**：验证项目完结后自我进化全链路：复盘触发 → 提案生成 → 用户 approve → apply 到 workspace → git commit。

**基础设施要求**：Sandbox + QWEN_API_KEY + workspace git 仓库已初始化

**前置状态**（用 seed_events 预置，不重跑前 5 阶段）：
```python
# tests/e2e/test_evolution_journey.py
events = seed_events("proj-evo-001", through_stage="delivered")
seed_l2_logs("proj-evo-001", entries=20)    # 足够触发 retro
seed_l1_logs(entries=5)                     # 5 条人类纠正记录
```

**飞书消息序列**：
```
T+0s    [状态：项目已 delivered，事件流包含完整 L2 日志]
T+10s   Manager load_skill("team_retrospective") → 识别瓶颈（如 PM 产品文档第 1 版缺时区）
T+30s   Manager → [发 retro_trigger 给 pm、rd、qa]
T+90s   PM → [self_retrospective 完成，send_mail retro_proposal：product_design SKILL 加时区规则]
T+150s  RD → [self_retrospective 完成，send_mail retro_proposal：code_impl SKILL 加前端 viewport]
T+210s  QA → [self_retrospective 完成，send_mail retro_proposal：test_design SKILL 加并发 case]
T+211s  Manager → [收齐 3 条，review_proposals 全通过，发 proposals_review 卡片]
T+220s  用户 → "3 条都 approve"
T+221s  Manager → [对每条调 ApplyProposalTool]
T+230s  Manager → [发 evolution_report 卡片]
T+235s  Manager → [append archived]
```

**关键断言节点**：

| 阶段 | 断言 |
|------|------|
| retro 触发 | events 含 retro_triggered(to=[pm,rd,qa]) |
| 提案收齐 | events 含 proposal_received × 3 |
| apply 完成 | events 含 proposal_applied × 3 |
| version 递增 | product_design SKILL frontmatter version 从 1.0.0 → 1.1.0 |
| git commit | git log 含 3 个 [proposal-xxx] commit |
| archived | events 最后一行 action=archived |

**通过判据**：
```python
assert events_count("retro_triggered") == 1
assert events_count("proposal_received") == 3
assert events_count("proposal_applied") == 3
assert events_count("evolved") == 1
assert events_count("archived") == 1
log_lines = git_log_oneline(workspace_root)
assert sum(1 for l in log_lines if "[proposal-" in l) == 3
skill_meta = parse_frontmatter(workspace/"pm/skills/product_design/SKILL.md")
assert skill_meta["version"] != "1.0.0"  # version 已递增
```

---

## 8. 测试数据工厂

### 8.1 seed_events.py

```python
# tests/fixtures/seed_events.py
"""生成 events.jsonl 的预置事件流，模拟项目跑到某阶段的状态"""
from datetime import datetime, timezone
import json
from pathlib import Path

_STAGE_ENDS = {
    "created":           1,
    "requirements":      4,
    "product_design":    9,
    "review_done":      14,
    "rd_delivered":     17,
    "qa_done":          20,
    "delivered":        23,
    "evolved":          28,
    "archived":         29,
}

def make_events_stream(project_id: str, through_stage: str) -> list[dict]:
    """返回模拟事件列表（不写文件）"""
    def evt(seq, action, payload=None):
        return {
            "ts": datetime(2026, 4, 20, 10, 0, seq, tzinfo=timezone.utc).isoformat(),
            "seq": seq,
            "actor": "manager",
            "action": action,
            "payload": payload or {},
        }

    all_events = [
        evt(1, "project_created",            {"project_id": project_id, "sop": "sop_feature_dev"}),
        evt(2, "requirements_discovery_started"),
        evt(3, "requirements_drafted",        {"artifact": "needs/requirements.md"}),
        evt(4, "checkpoint_requested",        {"ck_id": "ck-001", "stage": "requirements"}),
        evt(5, "checkpoint_approved",         {"ck_id": "ck-001"}),
        evt(6, "assigned",                    {"to": "pm", "stage": "product_design"}),
        evt(7, "decided_insert_review",       {"reviewers": ["rd", "qa"]}),
        evt(8, "review_requested",            {"reviewers": ["rd", "qa"], "stage": "product_design"}),
        evt(9, "review_received",             {"reviewer": "rd", "result": "pass"}),
        evt(10, "review_received",            {"reviewer": "qa", "result": "need_changes"}),
        evt(11, "revision_requested",         {"to": "pm", "round": 2}),
        evt(12, "review_requested",           {"reviewers": ["rd", "qa"], "round": 2}),
        evt(13, "review_received",            {"reviewer": "rd", "result": "pass"}),
        evt(14, "review_received",            {"reviewer": "qa", "result": "pass"}),
        evt(15, "checkpoint_requested",       {"ck_id": "ck-002", "stage": "product_design"}),
        evt(16, "checkpoint_approved",        {"ck_id": "ck-002"}),
        evt(17, "assigned",                   {"to": "rd", "stage": "rd_delivery"}),
        evt(18, "rd_delivered",               {"artifacts": ["tech/tech_design.md", "code/"]}),
        evt(19, "task_done_received",         {"from": "qa", "stage": "qa"}),
        evt(20, "task_done_received",         {"from": "qa", "stage": "qa_complete"}),
        evt(21, "delivery_requested",         {"summary": "7接口/14单测/coverage 87%"}),
        evt(22, "checkpoint_requested",       {"ck_id": "ck-003", "stage": "delivery"}),
        evt(23, "delivered",                  {}),
        evt(24, "retro_triggered",            {"to": ["pm", "rd", "qa"]}),
        evt(25, "proposal_received",          {"reviewer": "pm", "proposal_id": "p-pm-01"}),
        evt(26, "proposal_received",          {"reviewer": "rd", "proposal_id": "p-rd-01"}),
        evt(27, "proposal_received",          {"reviewer": "qa", "proposal_id": "p-qa-01"}),
        evt(28, "proposal_applied",           {"proposal_id": "p-pm-01", "commit": "abc123"}),
        evt(28, "evolved",                    {"commits": ["abc123", "def456", "ghi789"]}),
        evt(29, "archived",                   {"final_state": "completed"}),
    ]
    end_idx = _STAGE_ENDS.get(through_stage, len(all_events))
    return all_events[:end_idx]


def write_events_to_file(project_dir: Path, through_stage: str) -> Path:
    """将事件流写入 events.jsonl，返回文件路径"""
    events_path = project_dir / "events.jsonl"
    project_id = project_dir.name
    events = make_events_stream(project_id, through_stage)
    with events_path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return events_path
```

### 8.2 seed_mailboxes.py

```python
# tests/fixtures/seed_mailboxes.py
"""预置邮箱内容"""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

def make_task_assign_msg(from_: str, to: str, subject: str,
                          content: str, project_id: str,
                          status: str = "unread") -> dict:
    return {
        "id": f"msg-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "from": from_,
        "to": to,
        "type": "task_assign",
        "subject": subject,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "processing_since": None,
    }

def seed_mailbox(mailboxes_dir: Path, role: str, messages: list[dict]) -> None:
    """写入 mailboxes/{role}.json"""
    path = mailboxes_dir / f"{role}.json"
    path.write_text(json.dumps(messages, ensure_ascii=False, indent=2))

def seed_pending_task(mailboxes_dir: Path, role: str, project_id: str,
                       subject: str = "产品设计") -> dict:
    """为某角色放置一条 unread task_assign 邮件"""
    msg = make_task_assign_msg("manager", role, subject,
                               f"读 needs/requirements.md，按 {role} SKILL 完成任务。",
                               project_id)
    seed_mailbox(mailboxes_dir, role, [msg])
    return msg
```

### 8.3 fake_feishu_msg.py

```python
# tests/fixtures/fake_feishu_msg.py
"""构造飞书消息 stub，用于 feishu_bridge / classify 测试"""
from dataclasses import dataclass, field
from typing import Optional, Any

@dataclass
class FakeFeishuAction:
    value: dict = field(default_factory=dict)

@dataclass
class FakeFeishuMsg:
    text: str = ""
    action: Optional[FakeFeishuAction] = None
    msg_id: str = "msg-test-001"
    open_id: str = "ou_test_user"

def make_approved_card_msg() -> FakeFeishuMsg:
    """模拟用户点击 Approve 按钮"""
    return FakeFeishuMsg(
        text="",
        action=FakeFeishuAction(value={"kind": "checkpoint_response", "ck_id": "ck-001", "decision": "approved"})
    )

def make_text_msg(text: str) -> FakeFeishuMsg:
    """模拟用户发纯文本"""
    return FakeFeishuMsg(text=text)

def make_ambiguous_text_msg() -> FakeFeishuMsg:
    """模拟歧义文本（不该被误判）"""
    return FakeFeishuMsg(text="这个需求不太对，我们讨论一下")
```

### 8.4 conftest.py 集成 fixtures

```python
# tests/integration/conftest.py
import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from xiaopaw_team.tools.create_project import create_project
from tests.fixtures.seed_events import write_events_to_file
from tests.fixtures.seed_mailboxes import seed_pending_task

@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """创建临时 workspace 目录树"""
    ws = tmp_path / "workspace"
    for role in ["manager", "pm", "rd", "qa"]:
        (ws / role / "skills").mkdir(parents=True)
        for f in ["soul.md", "agent.md", "memory.md", "user.md"]:
            (ws / role / f).write_text(f"# {role} {f}")
    (ws / "shared" / "config").mkdir(parents=True)
    (ws / "shared" / "team_protocol.md").write_text("# team protocol")
    (ws / "shared" / "config" / "team_standards.yaml").write_text(
        "pytest_coverage_min: 0.80\nreview_max_rounds: 3\n"
    )
    return ws


@pytest.fixture
def tmp_project(tmp_workspace: Path) -> tuple[Path, str]:
    """在 tmp_workspace 下初始化一个项目目录，返回 (project_dir, project_id)"""
    project_id = "proj-test-001"
    proj_dir = tmp_workspace / "shared" / "projects" / project_id
    create_project(project_id, tmp_workspace)
    return proj_dir, project_id


@pytest.fixture
def project_at_design_stage(tmp_project: tuple[Path, str]) -> tuple[Path, str]:
    """seed events 到 product_design 阶段"""
    proj_dir, pid = tmp_project
    write_events_to_file(proj_dir, "product_design")
    # 创建 requirements.md
    (proj_dir / "needs").mkdir(exist_ok=True)
    (proj_dir / "needs" / "requirements.md").write_text(
        "# 需求文档\n## 数据实体\n### Pet\n### Diary\n### Photo\n## API\n7个接口\n"
    )
    return proj_dir, pid
```

---

## 9. 里程碑验收清单

对应 DESIGN.md §31.1 里程碑，每个里程碑的具体验收命令和标准如下：

---

### M1：代码骨架 + 4 Agent 启动

**验收命令**：
```bash
python -m xiaopaw_team.main --dry-run   # 或直接启动后 Ctrl+C
pytest tests/unit/test_startup.py -v
```

**验收标准**：
- [ ] `main.py` 启动无 ImportError / AttributeError
- [ ] 4 个 agent_fn 正确注册到 Runner routing 表（team:manager/pm/rd/qa）
- [ ] asyncio.Lock 包裹 Manager agent_fn（测试：并发 dispatch 两条 team:manager，验证串行）
- [ ] `data/cron/tasks.json` 初始化后含 4 × every 30s heartbeat（jitter 不为 0）
- [ ] `workspace/.git/` 存在则 ApplyProposalTool 在 Manager tools 中；不存在则不在

---

### M2：工具层 + 邮箱链路（无 LLM）

**验收命令**：
```bash
pytest tests/unit/ tests/integration/ -m "not llm" -k "mailbox" -v
```

**验收标准**：
- [ ] send_mail → read_inbox（返回 unread 标 in_progress）→ mark_done 三态完整
- [ ] FileLock 并发写 mailbox：两线程同时 send_mail，结果 2 条均在，无损坏
- [ ] at cron 注册：send_mail 后 tasks.json 含 at job
- [ ] 单元测试：`test_mailbox.py` ≥ 15 个用例，全 PASS

---

### M3：事件流推断 state（无 LLM）

**验收命令**：
```bash
pytest tests/unit/test_event_log.py tests/integration/test_project_state.py -v
```

**验收标准**：
- [ ] append_event × N → read_project_state 返回正确摘要（含最后 N 条 actions）
- [ ] 崩溃半写（最后行非合法 JSON）→ read_project_state 跳过、不崩溃、告警日志
- [ ] seq 严格递增验证
- [ ] archived 项目 _get_current_project_id 不选中

---

### M4：唤醒链路（无 LLM）

**验收命令**：
```bash
pytest tests/integration/test_wake_chain.py tests/integration/test_cron_dedup.py -v
```

**验收标准**：
- [ ] send_mail → at cron → Runner 收 team:{role} 消息，1.5s 内（`asyncio.wait_for(event, 2.0)` PASS）
- [ ] heartbeat 去重：队列中已有 pending wake，新 heartbeat 丢弃，`queue.qsize() == 1`
- [ ] 4 个 heartbeat 触发时间不同相（有 jitter 效果）

---

### M5：飞书桥 + Manager 澄清 checkpoint（有 LLM）

**验收命令**：
```bash
export QWEN_API_KEY=sk-xxx
pytest tests/integration/test_manager_req_checkpoint.py -m "llm sandbox" -v -s --timeout=300
```

**验收标准**：
- [ ] 用户发需求 → Manager kickoff → 多轮澄清 → requirements_write → requirements.md 存在
- [ ] Manager 发出 checkpoint_request 卡片（飞书 send_card 被调用）
- [ ] 用户 approve → checkpoint_approved 事件 → pm.json 收到 task_assign
- [ ] 全程无 error_alert 事件

---

### M6：端到端 6 阶段（有 LLM、真代码）

**验收命令**：
```bash
pytest tests/e2e/test_smoke_journey.py -m "llm sandbox" -v -s --timeout=3600
```

**验收标准**：
- [ ] needs/requirements.md 存在
- [ ] design/product_spec.md 存在
- [ ] tech/tech_design.md 存在
- [ ] code/ 目录非空，含 requirements.txt
- [ ] qa/test_report.md 存在，含 PASS 信息
- [ ] events.jsonl 最后含 delivered
- [ ] 全程无未处理异常（error_alert_raised == 0）

---

### M7：复盘 + apply_proposal + git commit

**验收命令**：
```bash
pytest tests/e2e/test_evolution_journey.py -m "llm sandbox" -v -s --timeout=1800
```

**验收标准**：
- [ ] events.jsonl 含 retro_triggered + proposal_received × 3
- [ ] events.jsonl 含 proposal_applied × 3（或 ≥ 1，取决于用户 approve 数量）
- [ ] `git log workspace/` 含 `[proposal-` 字样的 commit
- [ ] 至少 1 个 SKILL.md 的 frontmatter version 递增
- [ ] events.jsonl 最后行 action=archived

---

## 10. 已知不可测点 + 人工验证兜底

### 10.1 不可自动测试的场景

| 不可测点 | 原因 | 人工验证方法 |
|---------|------|------------|
| LLM 推理正确性（SOP 推进决策）| LLM 输出不确定，无法 assert 意图 | 人工审阅 events.jsonl 事件序列是否符合 sop_feature_dev 逻辑 |
| 产品设计文档质量 | 自然语言内容，无可机械验证的"正确" | 人工阅读 design/product_spec.md，对照 requirements.md 验证映射关系 |
| 代码生成质量（RD 自由选型）| 技术栈由 RD 自主决定 | 人工验证 pytest 全 PASS（机械）+ code review（人工） |
| 复盘提案根因识别质量 | self_retrospective 提案内容由 LLM 生成 | 人工验证提案 root_cause 分类是否符合实际问题 |
| 飞书卡片 UI 渲染 | 不同飞书版本渲染可能不同 | 手机 + PC 端各点一次 Approve 按钮，观察 checkpoint 流程是否走通 |
| heartbeat 30s 实际精度 | asyncio timer 在高负载时可能偏移 | 监控日志，验证 30s±10s 内触发 |
| Manager asyncio.Lock 用户体验 | Lock 等待期间用户体验无法量化 | 人工发消息，主观验证响应延迟可接受（<10s 感知） |

### 10.2 人工验证检查表（每次 demo 前）

```
[ ] 1. workspace/.git/ 存在（ApplyProposalTool 前提）
[ ] 2. sandbox 容器 UP：curl http://localhost:8022/health
[ ] 3. QWEN_API_KEY 有效（发一条简单消息验证）
[ ] 4. team_standards.yaml 关键参数正确：
        - pytest_coverage_min: 0.80
        - review_max_rounds: 3
[ ] 5. workspace/manager/skills/load_skills.yaml 含 sop_feature_dev（type=reference, kind=sop）
[ ] 6. 4 × heartbeat cron 已在 data/cron/tasks.json 中（grep "heartbeat"）
[ ] 7. 飞书 Bot 已在线（WebSocket 连接日志）
[ ] 8. 发测试消息"你好"，Manager 正常回复（基础通路验证）
```

### 10.3 已知限制（来自 DESIGN.md 附录 E）

以下局限不纳入自动测试范围，但需文档记录：

1. **项目并发限 1**：多项目需手工检查 _get_current_project_id 逻辑
2. **飞书 checkpoint 无超时**：项目卡住时需手工 `/new` 重置
3. **进化提案质量低**（首次数据少）：首次 demo 提案可能空洞，需人工审阅后再 approve
4. **pgvector 异步窗口**：如连续两轮对话间隔 <3s，search_memory 可能找不到最近一轮，需人工确认后重试

---

## 附录 A：Mock 与 Stub 注册表

| 依赖对象 | Mock 类型 | 使用位置 | 构造示例 |
|---------|---------|---------|---------|
| `FeishuSender.send_card` | `MagicMock(return_value="msg-001")` | 所有不发真实飞书的集成测试 | `sender = MagicMock(); sender.send_card.return_value = "msg-001"` |
| `FeishuSender.send` | `MagicMock()` | 同上 | `sender.send.return_value = None` |
| `AliyunLLM` (LLM 推理) | `MagicMock(return_value=AgentFinish(...))` | 单元/集成测试 | `with patch("xiaopaw_team.llm.aliyun_llm.AliyunLLM") as m` |
| `build_skill_crew` (Sub-Crew) | `MagicMock(return crew_stub)` | 工具层集成测试（不需要真沙盒） | `crew_stub.akickoff = AsyncMock(return_value="task result")` |
| `subprocess.run` (git) | `MagicMock(returncode=0, stdout=b"")` | ApplyProposalTool 单元测试 | `with patch("subprocess.run") as mock_run: mock_run.return_value.returncode = 0` |
| `_tasks_store.create_job` | `MagicMock()` | SendMailTool 单元测试 | `with patch("xiaopaw_team.tools._tasks_store.create_job") as mock_cj` |
| `filelock.FileLock` | 真实 FileLock（tmp_path） | 并发测试 | `lock = FileLock(tmp_path/"test.lock")` |
| pgvector DSN | 环境变量 `MEMORY_DB_DSN` 未设置 → skip | pgvector 测试 | `@pytest.mark.pgvector` + conftest 中 `if not os.getenv("MEMORY_DB_DSN"): pytest.skip(...)` |

---

## 附录 B：pytest marker 定义

```python
# conftest.py (根目录)
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "llm: 需要 QWEN_API_KEY 和真实 LLM 调用")
    config.addinivalue_line("markers", "sandbox: 需要 AIO-Sandbox 容器运行在 localhost:8022")
    config.addinivalue_line("markers", "pgvector: 需要 pgvector 容器和 MEMORY_DB_DSN 环境变量")
    config.addinivalue_line("markers", "slow: 超过 60s 的测试（E2E）")
    config.addinivalue_line("markers", "git: 需要 workspace/.git/ 已初始化")
```

**使用方式**：

```bash
# 只跑无外部依赖的测试（CI 快速通道）
pytest -m "not llm and not sandbox and not pgvector" -v

# 跑需要 LLM 的集成测试
pytest -m "llm" -v -s --timeout=300

# 跑完整 E2E（包含沙盒+pgvector）
pytest -m "llm and sandbox" -v -s --timeout=3600
```

**marker 应用示例**：

```python
@pytest.mark.llm
@pytest.mark.sandbox
def test_manager_req_checkpoint(tmp_workspace):
    ...

@pytest.mark.pgvector
async def test_async_index_with_metadata(db_conn):
    ...
```

---

## 附录 C：关键断言辅助函数

```python
# tests/helpers/event_helpers.py
"""events.jsonl 断言辅助函数"""
import json
from pathlib import Path


def load_events(events_path: Path) -> list[dict]:
    """读取 events.jsonl，跳过非法行"""
    events = []
    for line in events_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # 自愈：跳过崩溃半写行
    return events


def events_count(events_path: Path, action: str) -> int:
    """统计某 action 出现次数"""
    return sum(1 for e in load_events(events_path) if e["action"] == action)


def get_event(events_path: Path, action: str, idx: int = -1) -> dict | None:
    """获取某 action 的第 idx 条事件（默认最后一条）"""
    matches = [e for e in load_events(events_path) if e["action"] == action]
    return matches[idx] if matches else None


def get_last_checkpoint_id(events_path: Path) -> str | None:
    """获取最近一次 checkpoint_requested 的 ck_id"""
    e = get_event(events_path, "checkpoint_requested")
    return e["payload"].get("ck_id") if e else None


def get_last_revision_round(events_path: Path) -> int:
    """获取最近一次 revision_requested 的 round 字段"""
    e = get_event(events_path, "revision_requested")
    return e["payload"].get("round", 1) if e else 0


def assert_no_error_alerts(events_path: Path) -> None:
    """断言无 error_alert_raised 事件"""
    count = events_count(events_path, "error_alert_raised")
    assert count == 0, f"发现 {count} 个 error_alert_raised 事件"


# tests/helpers/mailbox_helpers.py
"""mailbox.json 断言辅助函数"""
import json
from pathlib import Path


def read_mailbox(mailboxes_dir: Path, role: str) -> list[dict]:
    path = mailboxes_dir / f"{role}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def get_latest_mail(mailboxes_dir: Path, role: str,
                    msg_type: str | None = None) -> dict | None:
    msgs = read_mailbox(mailboxes_dir, role)
    if msg_type:
        msgs = [m for m in msgs if m.get("type") == msg_type]
    return msgs[-1] if msgs else None


def assert_mailbox_has_task(mailboxes_dir: Path, role: str,
                             subject_contains: str | None = None) -> None:
    msgs = read_mailbox(mailboxes_dir, role)
    task_msgs = [m for m in msgs if m["type"] == "task_assign"]
    assert len(task_msgs) > 0, f"{role} 邮箱无 task_assign"
    if subject_contains:
        assert any(subject_contains in m["subject"] for m in task_msgs), \
            f"{role} 邮箱无含 '{subject_contains}' 的 task_assign"


# tests/helpers/git_helpers.py
"""git 操作辅助函数"""
import subprocess
from pathlib import Path


def git_log_oneline(workspace_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(workspace_root), "log", "--oneline"],
        capture_output=True, text=True
    )
    return result.stdout.strip().splitlines()


def count_proposal_commits(workspace_root: Path) -> int:
    lines = git_log_oneline(workspace_root)
    return sum(1 for l in lines if "[proposal-" in l)
```
