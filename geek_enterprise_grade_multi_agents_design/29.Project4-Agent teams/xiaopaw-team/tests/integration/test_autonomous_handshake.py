"""
集成测试：Cron-driven autonomous handshake (**非 LLM**).

目的：证明整个系统的"单接口 + 自驱动"契约成立：
- SendMailTool 写邮箱后自动 schedule_wake(team:<to>)
- CronService 检测 tasks.json 变更 → 触发 dispatch(team:<to>) InboundMessage
- Runner 路由到对应角色 agent_fn

不依赖 LLM：我们注入一个 stub agent_fn，它做和真实 agent 相同的"kickoff: read_inbox + 按规则回信 + mark_done"动作，
但逻辑是硬编码的 Python（非 LLM 推理）。这样我们能在单测时间内验证 production wiring 本身。

成功标准：
1. 注入一条 test:boot 消息给 Manager stub
2. Manager stub：read_inbox → send_mail to pm（SendMailTool 自动 schedule_wake）
3. CronService 触发 team:pm wake
4. PM stub：read_inbox → send_mail task_done to manager
5. CronService 触发 team:manager wake
6. Manager stub 最终记录 "完成"

整个流程内部完全无显式 orchestrator 编排，全靠 SendMailTool + CronService 自驱动。
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Callable

import pytest

from xiaopaw_team.cron import tasks_store
from xiaopaw_team.cron.service import CronService
from xiaopaw_team.models import InboundMessage, SenderProtocol
from xiaopaw_team.runner import Runner
from xiaopaw_team.session.manager import SessionManager
from xiaopaw_team.session.models import MessageEntry
from xiaopaw_team.tools import mailbox, workspace
from xiaopaw_team.tools.team_tools import (
    MarkDoneTool,
    ReadInboxTool,
    SendMailTool,
)


pytestmark = pytest.mark.integration


class _CaptureSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, routing_key: str, content: str, root_id: str = "") -> None:
        self.sent.append((routing_key, content))

    async def send_thinking(self, routing_key, root_id) -> str | None:
        return None

    async def update_card(self, card_msg_id, content) -> None:
        return None

    async def send_text(self, routing_key, content, root_id) -> None:
        return None


def _make_stub_agent_fn(
    role: str,
    workspace_root: Path,
    cron_tasks_path: Path,
    project_id: str,
    trace: list[dict],
    rules: Callable[[list[dict]], list[dict]],
) -> Callable:
    """构造一个 stub agent_fn：kickoff 读邮箱、按 rules 计算要发哪些邮件，然后发送。"""
    read_inbox = ReadInboxTool(workspace_root=workspace_root, role=role)
    send_mail = SendMailTool(
        workspace_root=workspace_root,
        cron_tasks_path=cron_tasks_path,
        from_role=role,
    )
    mark_done = MarkDoneTool(workspace_root=workspace_root, role=role)

    async def agent_fn(
        user_message: str,
        history: list[MessageEntry],
        session_id: str,
        routing_key: str = "",
        root_id: str = "",
        verbose: bool = False,
    ) -> str:
        # 1. read_inbox
        inbox_json = read_inbox._run(project_id=project_id)
        inbox = json.loads(inbox_json)
        messages = inbox.get("messages", [])
        trace.append({"role": role, "step": "read_inbox", "count": len(messages)})

        # 2. rules → list of outbound dicts
        outbound = rules(messages)

        # 3. send each
        for o in outbound:
            r = json.loads(send_mail._run(
                to=o["to"], type=o["type"], subject=o["subject"],
                content=o["content"], project_id=project_id,
            ))
            trace.append({"role": role, "step": "send_mail", "to": o["to"], "type": o["type"], "msg_id": r.get("msg_id")})

        # 4. mark_done
        for m in messages:
            mark_done._run(project_id=project_id, msg_id=m["id"])
            trace.append({"role": role, "step": "mark_done", "msg_id": m["id"]})

        return f"{role}: processed {len(messages)} inbound, sent {len(outbound)} outbound."

    return agent_fn


@pytest.mark.asyncio
async def test_autonomous_handshake_manager_pm(tmp_path: Path) -> None:
    """Manager(stub) → PM(stub) → Manager(stub) 三段自驱动 handshake."""
    workspace_root = tmp_path / "workspace"
    data_dir = tmp_path / "data"
    cron_tasks_path = data_dir / "cron" / "tasks.json"
    (workspace_root / "shared" / "projects").mkdir(parents=True)
    cron_tasks_path.parent.mkdir(parents=True)

    project_id = "autonotest"
    workspace.init_project_tree(workspace_root, project_id=project_id)

    # 需求已由 "人类" 写入（模拟 Manager 的 create_project 步骤）
    workspace.write_shared(
        workspace_root, project_id=project_id, role="manager",
        rel_path="needs/requirements.md", content="# needs\n..."
    )

    trace: list[dict] = []

    def manager_rules(inbox: list[dict]) -> list[dict]:
        """Manager：看到 boot_request 发 task_assign 给 PM；看到 task_done 就完成。"""
        outbound: list[dict] = []
        for m in inbox:
            ctype = m["type"]
            if ctype == "error_alert":  # 我们用 error_alert 承载 boot 触发
                outbound.append({
                    "to": "pm", "type": "task_assign",
                    "subject": "产品设计 (第 1 轮)",
                    "content": {"needs_path": "needs/requirements.md"},
                })
            elif ctype == "task_done":
                # 收到 PM 的 task_done，不再 forward（终止）
                trace.append({"role": "manager", "step": "final_ack", "from": m["from"]})
        return outbound

    def pm_rules(inbox: list[dict]) -> list[dict]:
        """PM：看到 task_assign 就写 design 并发 task_done 回 Manager。"""
        outbound: list[dict] = []
        for m in inbox:
            if m["type"] == "task_assign":
                # 假装写 design
                workspace.write_shared(
                    workspace_root, project_id=project_id, role="pm",
                    rel_path="design/product_spec.md",
                    content="# spec\n... stub ...",
                )
                outbound.append({
                    "to": "manager", "type": "task_done",
                    "subject": m["subject"],  # 回原 subject
                    "content": {
                        "artifacts": ["design/product_spec.md"],
                        "self_score": 0.85,
                        "breakdown": {"completeness": 1, "self_review": 0.9, "hard_constraints": 1, "clarity": 0.7, "timeliness": 0.8},
                    },
                })
        return outbound

    # 装配 4 agent_fn
    agent_fn_map = {
        "manager": _make_stub_agent_fn("manager", workspace_root, cron_tasks_path, project_id, trace, manager_rules),
        "pm": _make_stub_agent_fn("pm", workspace_root, cron_tasks_path, project_id, trace, pm_rules),
        "rd": _make_stub_agent_fn("rd", workspace_root, cron_tasks_path, project_id, trace, lambda _: []),
        "qa": _make_stub_agent_fn("qa", workspace_root, cron_tasks_path, project_id, trace, lambda _: []),
    }

    sender = _CaptureSender()
    session_mgr = SessionManager(data_dir=data_dir)
    runner = Runner(session_mgr=session_mgr, sender=sender, agent_fn_map=agent_fn_map, idle_timeout=3.0)

    cron_svc = CronService(data_dir=data_dir, dispatch_fn=runner.dispatch, tick_interval=0.05)
    await cron_svc.start()

    # 模拟"人类发起需求，由 Manager 负责 bootstrap"：给 Manager 收件箱塞一条 boot 消息
    # （真实场景下 boot = 飞书 routing_key p2p:* 入站；这里简化成一条 error_alert mail）
    mailbox.send_mail(
        workspace_root / "shared" / "projects" / project_id / "mailboxes",
        to="manager", from_="human", type_="error_alert",
        subject="boot", content={"trigger": "start"}, project_id=project_id,
    )
    tasks_store.schedule_wake(cron_tasks_path, role="manager", delay_ms=200)

    # 等 handshake 自驱动完成：Manager → PM → Manager final_ack
    for _ in range(200):
        await asyncio.sleep(0.1)
        if any(e.get("step") == "final_ack" for e in trace):
            break

    await cron_svc.stop()

    # Assertions
    steps = [(e["role"], e["step"]) for e in trace]
    assert ("manager", "read_inbox") in steps, f"Manager 第一轮没 read_inbox: trace={trace}"
    assert ("pm", "read_inbox") in steps, "PM 没被自动唤醒"
    # Manager 发 task_assign 给 pm
    assert any(e for e in trace if e.get("role") == "manager" and e.get("step") == "send_mail" and e.get("to") == "pm"), trace
    # PM 发 task_done 给 manager
    assert any(e for e in trace if e.get("role") == "pm" and e.get("step") == "send_mail" and e.get("to") == "manager"), trace
    # Manager 最终 ack
    assert any(e for e in trace if e.get("step") == "final_ack"), trace
    # 产物
    assert (workspace_root / "shared" / "projects" / project_id / "design" / "product_spec.md").exists()
