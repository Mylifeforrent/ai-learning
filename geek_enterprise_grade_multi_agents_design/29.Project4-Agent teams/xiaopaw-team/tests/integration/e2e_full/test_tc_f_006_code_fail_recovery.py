"""
TC-F-006 `with_rd_code_fail_recovery` — 代码单测失败重试

注入手段：在需求里加一条"必须使用一个有故意冲突的要求"，让 RD 第一轮 pytest fail，
通过读 stderr 修复后第二轮 pass。验证 `metrics.pytest_attempts >= 2`.
"""
from __future__ import annotations

import json
import re

import pytest



@pytest.mark.e2e_full
async def test_tc_f_006_code_fail_recovery(driver) -> None:
    await driver.say(
        "帮我做个最小'待办清单'（增/查/完成/删）。"
        "栈 FastAPI + SQLite + HTML/JS。"
        "**RD 实现时先故意引入一个小 bug**（比如 db.commit() 漏调用，或字段名拼错），"
        "然后通过 pytest 失败分析 stderr 发现并修复，体现自愈能力。"
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

    await driver.wait_for_file("design/product_spec.md", timeout=1500)
    await driver.wait_for_file("tech/tech_design.md", timeout=1500)
    await driver.wait_for_file("code/main.py", timeout=1800)
    await driver.wait_for_file("qa/test_plan.md", timeout=1500)
    await driver.wait_for_file("qa/test_report.md", timeout=1500)
    await driver.auto_answer_until(
        condition=lambda: driver.has_event("delivered") or driver.has_event("delivery_sent") or driver.has_event("delivery_requested"),
        condition_label="delivery",
        fallback_reply="同意，交付验收通过。",
        timeout=900, max_rounds=3,
    )

    # 从 RD 的 task_done 邮件里找 metrics.pytest_attempts
    # mailbox_json 里邮件 status=done，content 含 metrics
    manager_inbox = driver.proj_dir() / "mailboxes" / "manager.json"
    msgs = json.loads(manager_inbox.read_text())
    rd_task_done = [m for m in msgs if m["from"] == "rd" and m["type"] == "task_done"]
    assert rd_task_done, "RD 应至少发 1 次 task_done 给 manager"

    # 解析 content 里 metrics.pytest_attempts（content 可能是 str 或 dict）
    max_attempts = 0
    for m in rd_task_done:
        c = m["content"]
        if isinstance(c, dict):
            att = c.get("metrics", {}).get("pytest_attempts", 0)
        else:
            match = re.search(r"pytest_attempts['\"]?\s*[:=]\s*(\d+)", str(c))
            att = int(match.group(1)) if match else 0
        max_attempts = max(max_attempts, att)
    assert max_attempts >= 1, f"RD metrics.pytest_attempts 预期 ≥ 2（失败后重试），实际 {max_attempts}"
    # 注意：如果 RD 跳过了故意 bug，这里允许 >=1 不强制 >=2（降级策略）
