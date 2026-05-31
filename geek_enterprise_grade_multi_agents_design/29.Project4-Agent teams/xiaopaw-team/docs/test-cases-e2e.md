# xiaopaw-team E2E 测试用例清单（v2）

> 对齐 DESIGN.md v1.5 阶段 0-6。**所有 E2E 都走完整 6 阶段全链路**（需求澄清 → 产品设计 → 技术方案 → 代码实现 → QA 测试 → 交付，可选进入复盘）。
> 异常分支**不是单独写短路测试**，而是**在全链路中注入场景，让 LLM 真实遭遇异常**并按设计自愈/上报。
>
> 唯一非-LLM 测试是 Tool 层的契约快速校验（已经在 `test_team_tools.py` / `test_mailbox.py` / `test_workspace.py` 里覆盖；本文档不再重列）。

---

## 编号约定
- `TC-F-*` — Full Journey E2E（pytest `-m e2e_full`，真实 Qwen + 真实沙盒，每条 15-60 min）
- 每条 TC-F 都是一次完整的 6 阶段跑完。"变体"通过前置输入不同来制造不同的分支路径。

---

## 一、TC-F-001 `happy_path_crud_site` — 基线全链路

**场景描述**：用户一次性给出非常清晰的极简需求，全程不插评审、不出 defect、不走澄清，跑完 6 阶段到交付。

**用户输入（飞书消息）**：
```
帮我做个超简单的"待办清单"小网站（MVP 只要添加/列出/完成/删除 4 功能）。
技术栈后端 FastAPI + SQLite，前端单文件 HTML+JS。
所有细节你直接替我决定，我批准任何合理方案。
请先产出 needs/requirements.md，然后按 SOP 推进到 QA 交付。
一次只问一个最关键的问题；否则直接推进。
```

**期望路径（6 阶段全走）**：
1. Manager classify=new_requirement → `requirements_guide`
2. 一轮或零轮澄清 → `requirements_write` → `create_project` + `needs/requirements.md` + `send_to_human(kind=checkpoint_request)`
3. 用户 approve（测试驱动注入 "同意"）→ `handle_checkpoint_reply` → task_assign to PM
4. PM `product_design` → `design/product_spec.md` → task_done + self_score ≥ 0.8
5. Manager `check_review_criteria` threshold_met=false → task_assign to RD
6. RD `tech_design` → `tech/tech_design.md` → task_done
7. Manager → task_assign to RD for code
8. RD `code_impl`（沙盒）→ 单测 pass → task_done
9. Manager → task_assign to QA for test_design
10. QA `test_design` → `qa/test_plan.md` → task_done
11. Manager → task_assign to QA for test_run
12. QA `test_run` → 全 pass → `qa/test_report.md` → task_done
13. Manager → `send_to_human(kind="delivery")` + `CheckpointStore.register`
14. 用户 approve → events `delivered`

**成功断言**：
- [ ] 产物齐：`needs/requirements.md`, `design/product_spec.md`, `tech/tech_design.md`, `code/main.py`, `code/tests/test_*.py`, `code/requirements.txt`, `qa/test_plan.md`, `qa/test_report.md`
- [ ] events 含：`project_created`, `requirements_drafted`, `assigned` ×N, `task_done_received` ×N, `delivery_sent`, `delivered`
- [ ] 沙盒内 `pytest code/` 最终通过
- [ ] Manager 给用户 ≥ 2 条消息（需求 checkpoint + 交付汇报）
- [ ] 所有 task_done content 含 self_score 字段
- [ ] CheckpointStore.pending() 最终为空

**超时**：60 min

---

## 二、TC-F-002 `with_low_self_score_review_loop` — 插评审 + revise 分支

**场景描述**：通过注入 PM 故意打低分（系统层注入 self_score=0.55），触发评审判据 2（self_score < 0.70），Manager 必须走评审插入 + revise 流程。

**注入手段**：在 PM agent.md 里加一句指示："本次需求有 1 个关键决策你没有把握，self_score 评分时在 self_review 维度打 0.5，整体 self_score 应 < 0.6。"。或者直接用 fixture 在发 task_done 前把 self_score override 为 0.55。

**期望分支路径**（相对 TC-F-001 新增）：
1. Manager 收到 PM task_done content.self_score=0.55
2. `check_review_criteria` threshold_met=true → events `decided_insert_review`
3. Manager 发 review_request × 2（RD 用 `review_product_design_from_rd` / QA 用 `review_product_design_from_qa`）
4. RD / QA 各自产出 review_done + reviews/ 文件
5. 至少一份 verdict=revise
6. Manager 发 task_assign to PM subject="产品设计 (第 2 轮)"
7. PM 第二轮修改，self_score 提上来
8. check_review_criteria 通过 → 继续往下推进 tech_design

**成功断言**（相对 TC-F-001 附加）：
- [ ] events 含 `review_requested` ×2 + `review_received` ×2
- [ ] `reviews/product_design/rd_feasibility.md` 和 `reviews/product_design/qa_testability.md` 存在
- [ ] 至少有一封 task_assign subject 匹配 `^.*第 2 轮\)$`
- [ ] 第二轮 PM task_done self_score > 0.7

**超时**：70 min

---

## 三、TC-F-003 `with_qa_defect_rd_fix_loop` — QA 发现 defect → RD 修复分支

**场景描述**：通过在 requirements 里注入一条"DELETE 必须真删除，不是软删除"的强要求，同时 RD 在 tech_design/code_impl 阶段可能选择软删除默认，触发 QA test_run 发现 defect → 发 task_assign 给 RD → RD 修复 → 再次 task_done → QA 重测。

**注入手段**：在 TC-F-001 的需求里追加：
```
严格要求：DELETE /todo/{id} 必须物理删除，不能用 soft delete；
QA 必须验证删除后 GET /todo/{id} 返回 404，且 GET /todo 不再包含该 id。
```
RD 第一轮 LLM 可能选 soft delete（业界常见 default），QA 就会发现问题。

**期望分支路径**（在 QA 阶段分叉）：
1. TC-F-001 1-11 步正常
2. QA `test_run` 发现 DELETE 实际是 soft delete → 写 `qa/defects/defect_c-delete.md`
3. QA 顺手发 `task_assign to rd subject="修复缺陷 (第 2 轮)"`
4. RD 改 `services/todo.py` 把 soft delete 换成 `db.delete()`
5. RD 再发 task_done "修复完成"
6. Manager 转发 → QA `task_assign subject="测试执行 (第 2 轮)"`
7. QA 重跑 → 全 pass → `qa/test_report.md`
8. 正常交付

**成功断言**：
- [ ] `qa/defects/` 至少 1 个 defect_*.md
- [ ] 至少 1 封 RD 收到的 task_assign subject 含 "修复"
- [ ] 最终 test_report.md 里 `fail=0`
- [ ] events 序列：`task_done_received` (QA 有 defect) → `assigned` (to RD) → `task_done_received` (RD 修复) → `assigned` (to QA) → `task_done_received` (重测 pass) → `delivered`

**超时**：80 min

---

## 四、TC-F-004 `with_checkpoint_revise` — 用户对需求 checkpoint 回 revise

**场景描述**：用户第一次看到 requirements.md 后回"不对，我还要加分享功能"，触发 Manager 更新需求 → 再发 checkpoint。

**用户消息序列**：
1. 同 TC-F-001 初始需求
2. Manager 发需求 checkpoint 后，用户回：`"加上'分享到微信'功能，其他都同意"`
3. Manager 更新 requirements.md 追加分享功能 + 再发 checkpoint_request
4. 用户：`"同意"` → 继续推进

**期望分支路径**：
1. 正常进入需求阶段，Manager 产出 requirements.md v1 + 发 checkpoint
2. 用户回 revise 类消息
3. classify=checkpoint_response，`handle_checkpoint_reply` 判 reply_class=revise
4. Manager `read_shared(requirements.md)` → 追加 "分享到微信" → `write_shared`
5. 再 `send_to_human(kind=checkpoint_request)` + 再 register
6. 用户 approve → 继续 PM 产品设计
7. 其余同 TC-F-001

**成功断言**：
- [ ] events 至少含 2 次 `checkpoint_request_sent` + 1 次 `checkpoint_approved` + 1 次"revise"类表征（如 `checkpoint_reply_classified` payload.reply_class="revise"）
- [ ] requirements.md 内容含 "分享"
- [ ] product_spec.md 覆盖分享功能
- [ ] 最终交付 delivered

**超时**：70 min

---

## 五、TC-F-005 `with_retrospective_and_evolution` — 交付后复盘 + 进化

**场景描述**：TC-F-001 完成交付后，用户再发"团队复盘"，触发 team_retrospective + 各角色 self_retrospective + 分档审批 + 机械执行。

**用户消息序列**：
1. 同 TC-F-001 走到 `delivered` 事件
2. 用户发：`"现在做一次团队复盘"`
3. Manager team_retrospective → 产出 proposals（至少 1 条 memory + 1 条 skill）
4. memory depth → 自动批 → 角色执行 → retro_applied
5. skill depth → proposal_review card 给用户 → 用户回 `"同意"` → Manager 发 retro_approved → 角色机械执行 → retro_applied

**期望分支路径**：
1. TC-F-001 全链路完成
2. 用户 "团队复盘" → classify（兜底走 handle/team retrospective）
3. Manager 加载 `team_retrospective` → 可选分派 retro_trigger 给 PM/RD/QA
4. 至少 1 个角色自我复盘 → retro_report
5. Manager 加载 `review_proposal` → 分档
6. memory depth 直批，角色执行替换 → retro_applied_by_{role} 事件
7. skill/agent depth 转人类 → 用户 approve → 执行 → retro_applied

**成功断言**：
- [ ] events 含：`retro_triggered`, `retro_report_received`, `retro_approved_by_manager` 或 `retro_approved_by_human`, `retro_applied_by_{role}`
- [ ] 至少 1 个 target_file 内容已变（before_text → after_text 替换成功）
- [ ] 对 skill depth，Manager 发过 `proposal_review_sent` + CheckpointStore.register

**超时**：30 min（假设前置 TC-F-001 产物已缓存）

---

## 六、TC-F-006 `with_rd_code_fail_recovery` — 代码单测失败重试

**场景描述**：tech_design 故意让 RD 遭遇一次 pytest 失败（例如注入 "Pydantic v2 语法，但 requirements 未明确版本"），触发 code_impl 的失败重试循环。

**注入手段**：在 `tech_design.md` 阶段完成后，测试代码 monkey-patch 一次，让第一次 `pytest` 故意 fail（通过在 tech_design 模板里加一句"请使用 `from pydantic.v1 import BaseModel`"，但 FastAPI 0.115 不兼容 v1）。RD 按照指令写，第一次 pytest 失败 → 读 stderr → 修复（去掉 v1）→ 第二次 pytest 通过。

**期望分支路径**：
1. 前 3 阶段正常
2. RD `code_impl` 第一次 pytest 失败（`ImportError: cannot import name 'BaseModel' from 'pydantic.v1'`）
3. RD 读 stderr → 改 `from pydantic import BaseModel` → 重跑
4. 通过 → task_done `metrics.pytest_attempts=2`
5. 其余同 TC-F-001

**成功断言**：
- [ ] RD task_done content `metrics.pytest_attempts >= 2`
- [ ] 最终 `pytest_final_status="pass"`
- [ ] 最终交付完整

**超时**：80 min

---

## 七、TC-F-007 `with_sop_cocreate_first` — 先共创 SOP 再跑功能开发

**场景描述**：从完全空白开始，先和用户对话 3 轮共创 SOP（6 维覆盖），用户 approve 后触发 sop_draft 落盘，然后用户立即发新需求开始跑 TC-F-001。

**用户消息序列**：
1. `"我们来定一套小功能开发流程吧"`
2. Manager 问 Goal/Stages → 用户回答
3. Manager 问 Roles/Artifacts → 用户回答
4. Manager 问 Checkpoints/Retrospective → 用户回答
5. Manager 生成 SOP 草稿 + 发 checkpoint_request
6. 用户 approve
7. 用户接着发 TC-F-001 的需求
8. 完整跑 6 阶段

**期望分支路径**：
1. SOP 共创完成，产出 `needs/sop_draft.md`（或同等路径）
2. 新需求触发 requirements 阶段
3. 后续同 TC-F-001

**成功断言**：
- [ ] 有 ≥ 1 个 sop_* 草稿文件
- [ ] 紧接着有完整的 project_created 事件序列
- [ ] Manager `send_to_human` 至少 5 次（SOP 3+ 轮 + 需求 checkpoint + 交付）

**超时**：100 min

---

## 八、覆盖矩阵

| 分支 | 用例 |
|------|------|
| 正常 6 阶段 | TC-F-001 |
| 评审插入 + revise | TC-F-002 |
| QA 发现 defect + RD 修复 | TC-F-003 |
| Checkpoint revise（需求阶段） | TC-F-004 |
| Checkpoint reject（交付阶段） | 在 TC-F-003 末尾可变体，暂合并 |
| 复盘 + 进化（memory auto + skill human） | TC-F-005 |
| 代码单测失败自愈 | TC-F-006 |
| SOP 共创先行 | TC-F-007 |
| 澄清上行（PM → Manager → 用户 → PM） | 作为 TC-F-002/004 的副产品观察 |
| Tool 权限/合同校验 | 已在 `tests/unit/test_team_tools.py`、`test_workspace.py`、`test_mailbox.py` 覆盖 |
| Manager 并发 Lock / Cron wake 去重 | 已在 `tests/integration/test_autonomous_handshake.py` + 单元测试覆盖 |

---

## 九、跑法

```bash
# 1. 前置
export QWEN_API_KEY=xxx
docker compose -f sandbox-docker-compose.yaml up -d   # 8029

# 2. 所有非-LLM 测试（快，<20s）
pytest tests/unit tests/integration -m "not e2e_full" -v

# 3. 单个 Full Journey
pytest tests/integration/e2e_full/test_tc_f_001_happy_path.py -v -m e2e_full -s

# 4. 全部 Full Journey（可能 5+ 小时）
pytest tests/integration/e2e_full/ -v -m e2e_full -s

# 5. 只跑异常变体
pytest tests/integration/e2e_full/ -v -m e2e_full -s -k "review or defect or revise or fail"
```

## 十、Skip 策略

- 环境变量 `QWEN_API_KEY` 缺失 → 所有 `e2e_full` 跳过，pytest skip 标注原因
- 沙盒 http://localhost:8029/ 不通 → 跳过（fixture 前置 readiness 探测）
- `pytest.ini` 的 `-m "not e2e_full"` 保持作为默认快测

## 十一、数据清理

每个 `TC-F-*` 用 `tmp_path` 构造独立 workspace，运行结束后留痕（pytest 默认保留最近 3 次），便于失败复盘。不主动 cleanup。
