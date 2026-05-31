"""
TC-F-007 `with_sop_cocreate_first` — 先共创 SOP 再跑功能开发

流程：3-4 轮 SOP 共创对话 → Manager 产出 SOP 草稿 → 接着跑 6 阶段.
成功标准：SOP 共创对话发生 + 功能开发 6 阶段核心产物齐备。
"""
from __future__ import annotations

import pytest


@pytest.mark.e2e_full
async def test_tc_f_007_sop_cocreate_then_feature(driver) -> None:
    # ─── 阶段 A：SOP 共创（3-4 轮） ────────────────────────────────
    await driver.say(
        "我们来定一套 '小功能开发' SOP 吧，请加载 sop_cocreate_guide skill 指引我共创。"
    )
    await driver.wait_until(driver.bot_said_something, timeout=300, label="sop Q1")

    await driver.say(
        "Goal：快速把一个新功能从想法推到上线；"
        "Stages：需求澄清 → 产品设计 → RD 设计+实现 → QA 测试 → 交付 → 复盘。"
    )
    await driver.wait_until(
        lambda: len(driver.sender.messages) >= 2, timeout=300, label="sop Q2"
    )

    await driver.say(
        "Roles：Manager 总负责；PM 产品设计；RD 技术实现；QA 测试。"
        "Artifacts：每阶段在 shared/projects/{pid} 下对应目录产出。"
        "Checkpoints：需求定稿 + 交付验收。"
        "Retrospective：每次交付后触发。"
        "**所有维度都已定，请现在加载 sop_write skill 把 SOP 写入文件**。"
    )

    # 等 Manager 说 "SOP 已写入" 或 "共创完成" 或至少有 3 条 bot msg
    await driver.auto_answer_until(
        condition=lambda: (
            len(driver.sender.messages) >= 3
            and any("sop" in m["content"].lower() or "SOP" in m["content"]
                    or "已写入" in m["content"] or "完成" in m["content"]
                    for m in driver.sender.messages[-4:])
        ),
        condition_label="sop-cocreate-wrapped-up",
        fallback_reply="SOP 6 维已收齐。立即写入并确认完成。",
        timeout=600, max_rounds=3,
    )

    # ─── 阶段 B：跑一个功能 ────────────────────────────────────────
    await driver.say(
        "好，现在按这套 SOP 帮我做个待办清单小网站（增/查/完成/删）。"
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
        condition_label="needs-approved-or-pm-dispatched",
        fallback_reply=_approval_fallback,
        timeout=900, max_rounds=4,
    )

    await driver.wait_for_file("design/product_spec.md", timeout=1500)
    await driver.wait_for_file("tech/tech_design.md", timeout=1500)
    await driver.wait_for_file("code/main.py", timeout=1800)
    await driver.wait_for_file("qa/test_plan.md", timeout=1500)

    await driver.auto_answer_until(
        condition=lambda: driver.file_exists("qa/test_report.md")
        or driver.has_event("delivery_sent")
        or driver.has_event("delivery_requested"),
        condition_label="qa-done-or-delivery",
        fallback_reply="同意，继续。",
        timeout=1500, max_rounds=3,
    )

    # 断言：6 阶段产物齐备
    for rel in ["needs/requirements.md", "design/product_spec.md", "tech/tech_design.md",
                "code/main.py", "qa/test_plan.md"]:
        assert driver.file_exists(rel), f"缺产物 {rel}"
    # SOP 共创阶段至少有 3 轮对话
    assert len(driver.sender.messages) >= 3, f"SOP 共创对话少于 3 轮: {len(driver.sender.messages)}"
