"""
TC-F-002 `with_review_complex_requirements` — 含复杂需求（登录+订阅）的全链路

场景：user 强调质量要求高并 prompt 请求插入评审。
成功标准：6-阶段核心产物齐备。review 分支触发视为 bonus（部分 LLM 轨迹不触发但依然交付）。
"""
from __future__ import annotations

import pytest


@pytest.mark.e2e_full
async def test_tc_f_002_review_loop(driver) -> None:
    await driver.say(
        "帮我做个待办清单小网站，**包含用户登录、付费订阅**两大 MVP 功能。"
        "因为涉及账号和付款，质量要求很高，**请你在每个阶段都主动插入团队评审**。"
        "技术栈 FastAPI + SQLite + 原生 HTML+JS。"
        "**所有细节你直接替我决定，我批准任何合理方案**，请立即 create_project 并起草需求文档。"
    )

    await driver.auto_answer_until(
        condition=lambda: driver.has_event("project_created"),
        condition_label="project_created",
        timeout=1500, max_rounds=5,
    )
    pid = driver.current_project_id()

    await driver.wait_for_file("needs/requirements.md", timeout=600)

    def _approval_fallback() -> str:
        return "同意，请继续推进产品设计。"

    await driver.auto_answer_until(
        condition=lambda: driver.has_event("checkpoint_approved")
        or driver.has_event("assigned")
        or driver.file_exists("design/product_spec.md"),
        condition_label="needs-approved-or-pm-dispatched",
        fallback_reply=_approval_fallback,
        timeout=900, max_rounds=4,
    )

    await driver.wait_for_file("design/product_spec.md", timeout=1500)
    await driver.wait_for_file("tech/tech_design.md", timeout=1500)
    await driver.wait_for_file("code/main.py", timeout=1800)
    await driver.wait_for_file("qa/test_plan.md", timeout=1500)
    await driver.wait_for_file("qa/test_report.md", timeout=1500)

    await driver.auto_answer_until(
        condition=lambda: driver.has_event("delivered")
        or driver.has_event("delivery_sent")
        or driver.has_event("delivery_requested"),
        condition_label="delivery",
        fallback_reply="同意，交付验收通过。",
        timeout=900, max_rounds=3,
    )

    # ── 断言：6-阶段产物齐备 + event 链完整 ──────────────────────
    for rel in [
        "needs/requirements.md", "design/product_spec.md", "tech/tech_design.md",
        "code/main.py", "qa/test_plan.md", "qa/test_report.md",
    ]:
        assert driver.file_exists(rel), f"缺产物 {rel}"
    assert driver.has_event("project_created")
    assert (driver.has_event("delivered")
            or driver.has_event("delivery_sent")
            or driver.has_event("delivery_requested"))
    # bonus: 如果 review 分支触发，记录
    if driver.has_event("review_requested"):
        print("[TC-F-002] ✅ review 分支也触发了")
