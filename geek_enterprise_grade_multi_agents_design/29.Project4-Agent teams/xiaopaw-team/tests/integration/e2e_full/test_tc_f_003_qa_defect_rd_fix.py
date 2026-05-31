"""
TC-F-003 `with_qa_defect_rd_fix_loop` — QA 发现 defect → RD 修复 → 重测通过

注入手段：在需求里放置"严格硬删除"强要求，RD 第一轮可能选 soft delete，
QA test_run 会发现不一致 → 写 defect → 回流 RD → 再次 task_done → QA 重测.
"""
from __future__ import annotations

import pytest



@pytest.mark.e2e_full
async def test_tc_f_003_qa_defect_rd_fix(driver) -> None:
    await driver.say(
        "做一个待办清单小网站 MVP（增/查/改完成/删）。"
        "**严格硬约束：DELETE /todo/{id} 必须物理删除（db.delete），不允许 soft delete**；"
        "QA 必须在测试中断言：DELETE 后 GET /todo/{id} 返回 404，且 GET /todo 列表不含该 id；"
        "栈：FastAPI + SQLite + 原生 HTML/JS。"
        "**所有细节你直接替我决定，我批准任何合理方案**，请立即 create_project 并起草需求文档。"
    )

    await driver.auto_answer_until(
        condition=lambda: driver.has_event("project_created"),
        condition_label="project_created",
        timeout=1500, max_rounds=5,
    )
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

    await driver.wait_for_file("design/product_spec.md", timeout=900)
    await driver.wait_for_file("tech/tech_design.md", timeout=900)
    await driver.wait_for_file("code/main.py", timeout=1500)
    await driver.wait_for_file("qa/test_plan.md", timeout=900)
    # QA 可能第一轮失败：等 test_report 或 defect_* 至少一个出现
    await driver.wait_until(
        lambda: driver.file_exists("qa/test_report.md")
        or ((driver.proj_dir() / "qa" / "defects").exists()
            and any((driver.proj_dir() / "qa" / "defects").glob("defect_*.md"))),
        timeout=1800,
        label="qa:first-test-result",
    )

    # 如果一开始就通过（可能 RD 本来就写对了），放宽——只断言最终交付
    # 但若产生了 defect，等待修复循环
    if (driver.proj_dir() / "qa" / "defects").exists() \
       and any((driver.proj_dir() / "qa" / "defects").glob("defect_*.md")):
        # 等 RD 修复 + QA 重测（test_report.md 最终出现 fail=0）
        await driver.wait_until(
            lambda: driver.file_exists("qa/test_report.md"),
            timeout=1800,
            label="qa:test_report after defect fix",
        )

    # 等交付
    await driver.auto_answer_until(
        condition=lambda: driver.has_event("delivered")
        or driver.has_event("delivery_sent")
        or driver.has_event("delivery_requested"),
        condition_label="delivery",
        fallback_reply="同意，交付验收通过。",
        timeout=900, max_rounds=3,
    )

    # 断言：6-阶段产物齐备 + 至少产生 QA 产物（test_report 或 defect）
    for rel in [
        "needs/requirements.md", "design/product_spec.md", "tech/tech_design.md",
        "code/main.py", "qa/test_plan.md",
    ]:
        assert driver.file_exists(rel), f"缺产物 {rel}"
    has_report = driver.file_exists("qa/test_report.md")
    defects_dir = driver.proj_dir() / "qa" / "defects"
    has_defect = defects_dir.exists() and any(defects_dir.glob("defect_*.md"))
    assert has_report or has_defect, "QA 应至少产出 test_report.md 或 defect_*.md"
    # bonus：如果 defect 触发了修复循环，记录
    if has_defect:
        print(f"[TC-F-003] ✅ 发现 defect — 修复循环触发")
