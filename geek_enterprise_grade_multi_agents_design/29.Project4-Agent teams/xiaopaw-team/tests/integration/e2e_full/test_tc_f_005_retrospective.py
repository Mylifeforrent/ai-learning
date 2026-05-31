"""
TC-F-005 `with_retrospective_and_evolution` — 交付后复盘 + 进化

执行策略：
1. 先跑完 happy path (压缩版)
2. 用户发"团队复盘" → Manager team_retrospective → proposals
3. 等 retro_* 事件出现
"""
from __future__ import annotations

import pytest


@pytest.mark.e2e_full
async def test_tc_f_005_retrospective_evolution(driver) -> None:
    # ─── 阶段 A：先跑完一次 happy path（压缩版） ────────────────────
    await driver.say(
        "帮我做个最小的'待办清单'小网站（增/查/完成/删）。"
        "栈 FastAPI+SQLite+HTML/JS。"
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
        condition_label="needs-approved-or-design-started",
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

    # ─── 阶段 B：复盘 ────────────────────────────────────────────────
    await driver.say("现在做一次团队复盘，总结本次交付能固化的改进。")

    # 等任一 retro_* 事件出现（memory auto-approve 或 proposal_review_sent 都算）
    await driver.auto_answer_until(
        condition=lambda: any(e["action"].startswith("retro_") or e["action"] == "proposal_review_sent"
                              for e in driver.events())
        or any("复盘" in m["content"] for m in driver.sender.messages[-5:]),
        condition_label="retro_*  or proposal_review or 复盘消息",
        fallback_reply="请立即加载 team_retrospective skill 开始复盘，产出 improvement_proposals。",
        timeout=1200, max_rounds=4,
    )

    actions = [e["action"] for e in driver.events()]
    has_retro = any(a.startswith("retro_") or a == "proposal_review_sent" for a in actions)
    has_retro_msg = any("复盘" in m["content"] or "proposals" in m["content"].lower()
                        for m in driver.sender.messages)
    assert has_retro or has_retro_msg, f"events/msgs 无 retro_* : {actions[-10:]}"
