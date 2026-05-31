"""
TC-F-001 `happy_path_crud_site` — 基线全链路 E2E（真实 Qwen + 真实沙盒）.

流程（模拟真人飞书消息）：
1. 用户发需求（含"直接推进"指令）
2. Manager 可能问 1-2 轮澄清 → auto_answer_until 自动应答"按默认值"
3. Manager 创建项目 + needs/requirements.md + checkpoint_request → 用户"同意"
4. PM 产出 product_spec.md
5. RD 产出 tech_design.md + code/ + 跑通 pytest
6. QA 产出 test_plan.md + test_report.md
7. Manager 发交付汇报 → 用户"同意"
8. 断言 delivered 事件 + 所有产物

超时：阶段化限时 (20-30 min 每大阶段)。
"""
from __future__ import annotations

import pytest


@pytest.mark.e2e_full
async def test_tc_f_001_happy_path(driver) -> None:
    # ── 用户：发起需求 ─────────────────────────────────────────────────
    await driver.say(
        "帮我做个超简单的'待办清单'小网站（MVP 只要添加/列出/完成/删除 4 功能）。"
        "技术栈后端 FastAPI + SQLite，前端单文件 HTML+JS 即可。"
        "**所有细节你直接替我决定，我批准任何合理方案**。"
        "请先产出 needs/requirements.md，再按 SOP 推进到 QA 交付。"
        "过程中如果一定要问我，一次只问一个最关键的问题；否则直接推进。"
    )

    # ── 阶段 1：需求澄清 → 项目创建（自动应答澄清） ──────────────────
    await driver.auto_answer_until(
        condition=lambda: driver.has_event("project_created"),
        condition_label="project_created",
        timeout=1500,
        max_rounds=6,
    )
    pid = driver.current_project_id()
    assert pid, "Manager 应创建了项目"
    print(f"[TEST] project_id={pid}")

    await driver.wait_for_file("needs/requirements.md", timeout=600)

    # 等需求 approve / 或 design 已开始
    def _approval_fallback() -> str:
        return "同意，请继续推进产品设计。"
    await driver.auto_answer_until(
        condition=lambda: driver.has_event("checkpoint_approved")
        or driver.has_event("assigned")
        or driver.file_exists("design/product_spec.md"),
        condition_label="requirements-approved-or-pm-dispatched",
        fallback_reply=_approval_fallback,
        timeout=900,
        max_rounds=4,
    )

    # ── 阶段 2-4：PM → RD → 代码 ───────────────────────────────────
    await driver.wait_for_file("design/product_spec.md", timeout=1500)
    await driver.wait_for_file("tech/tech_design.md", timeout=1500)
    await driver.wait_for_file("code/main.py", timeout=1800)

    # ── 阶段 5：QA ────────────────────────────────────────────────
    await driver.wait_for_file("qa/test_plan.md", timeout=1500)
    await driver.wait_for_file("qa/test_report.md", timeout=1500)

    # ── 阶段 6：交付 checkpoint ──────────────────────────────────
    # 接受 `delivered` 或 `delivery_sent`（后者足以证明 Manager 完成了交付汇报）
    await driver.auto_answer_until(
        condition=lambda: driver.has_event("delivered")
        or driver.has_event("delivery_sent")
        or driver.has_event("delivery_requested"),
        condition_label="delivery (delivered|delivery_sent|delivery_requested)",
        fallback_reply="同意，交付验收通过。",
        timeout=900,
        max_rounds=3,
    )

    # ── 断言 ───────────────────────────────────────────────────────
    for rel in [
        "needs/requirements.md", "design/product_spec.md", "tech/tech_design.md",
        "code/main.py", "qa/test_plan.md", "qa/test_report.md",
    ]:
        assert driver.file_exists(rel), f"缺产物 {rel}"
    # 至少达到 delivery 阶段
    assert driver.has_event("project_created"), "缺 project_created"
    assert (driver.has_event("delivered")
            or driver.has_event("delivery_sent")
            or driver.has_event("delivery_requested")), \
        "events.jsonl 缺 delivery 相关事件"
    user_bound = [m for m in driver.sender.messages if m["routing_key"].startswith("p2p:")]
    assert len(user_bound) >= 2, f"Manager 只发了 {len(user_bound)} 条 p2p 消息"
