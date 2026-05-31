"""
TC-F-004 `with_checkpoint_revise` — 用户对需求 checkpoint 回 revise

成功标准：
- needs/requirements.md 产出
- 用户 revise 请求分享功能后，requirements.md 含"分享"或"微信"
- 继续推进到 QA 阶段（6 阶段产物齐备）
"""
from __future__ import annotations

import pytest


@pytest.mark.e2e_full
async def test_tc_f_004_checkpoint_revise(driver) -> None:
    await driver.say(
        "帮我做个待办清单小网站（增/查/完成/删）。"
        "技术栈 FastAPI + SQLite + 原生 HTML/JS。"
        "**所有细节你直接替我决定，我批准任何合理方案**，请立即 create_project 并起草需求文档。"
    )

    await driver.auto_answer_until(
        condition=lambda: driver.has_event("project_created"),
        condition_label="project_created",
        timeout=1500, max_rounds=5,
    )
    await driver.wait_for_file("needs/requirements.md", timeout=600)

    # 等 Manager 发 checkpoint_request 给用户
    await driver.wait_until(
        driver.bot_asked_for_checkpoint, timeout=600, label="needs-ckpt-1"
    )

    # 用户 revise
    await driver.say("不对，MVP 还要加一个'分享当前任务列表到微信'的按钮。其他都同意。")

    # Manager 应再次产出需求草稿（含分享）或直接推进到产品设计
    await driver.auto_answer_until(
        condition=lambda: (
            "分享" in driver.read_file("needs/requirements.md") if driver.file_exists("needs/requirements.md") else False
        ) or (
            driver.file_exists("design/product_spec.md") and "分享" in driver.read_file("design/product_spec.md")
        ),
        condition_label="分享 in requirements.md or product_spec.md",
        fallback_reply="同意，按此修订后的需求继续推进产品设计。",
        timeout=900, max_rounds=4,
    )

    def _approve() -> str:
        return "同意，请继续推进产品设计。"
    await driver.auto_answer_until(
        condition=lambda: driver.has_event("assigned")
        or driver.file_exists("design/product_spec.md"),
        condition_label="pm-dispatched",
        fallback_reply=_approve,
        timeout=900, max_rounds=3,
    )

    await driver.wait_for_file("design/product_spec.md", timeout=1500)
    await driver.wait_for_file("tech/tech_design.md", timeout=1500)
    await driver.wait_for_file("code/main.py", timeout=1800)
    await driver.wait_for_file("qa/test_plan.md", timeout=1500)

    await driver.auto_answer_until(
        condition=lambda: driver.file_exists("qa/test_report.md")
        or driver.has_event("delivery_requested")
        or driver.has_event("delivery_sent"),
        condition_label="qa-done-or-delivery",
        fallback_reply="同意，继续。",
        timeout=1500, max_rounds=3,
    )

    # 断言：revise 触发 + 6 阶段产物齐备
    for rel in ["needs/requirements.md", "design/product_spec.md", "tech/tech_design.md",
                "code/main.py", "qa/test_plan.md"]:
        assert driver.file_exists(rel), f"缺产物 {rel}"
    # revise 应在至少一处文档体现
    combined = ""
    for rel in ["needs/requirements.md", "design/product_spec.md"]:
        if driver.file_exists(rel):
            combined += driver.read_file(rel)
    assert "分享" in combined or "微信" in combined, \
        f"revise 未体现到 requirements/spec (len={len(combined)})"
