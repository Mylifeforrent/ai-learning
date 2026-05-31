"""
Runner 路由 + wake 去重 集成测试（无 LLM）

对齐 DESIGN.md §5.3 / §13.3 / T-RN-*。
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from xiaopaw_team.models import InboundMessage, SenderProtocol
from xiaopaw_team.runner import Runner, _pick_agent_fn
from xiaopaw_team.session.manager import SessionManager


class _StubSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, routing_key: str, content: str, root_id: str = "") -> None:
        self.sent.append((routing_key, content))

    async def send_thinking(self, routing_key, root_id) -> str | None: return None
    async def update_card(self, card_msg_id, content) -> None: return None
    async def send_text(self, routing_key, content, root_id) -> None: return None


async def _stub_agent(role_label: str):
    async def fn(user_msg, history, session_id, routing_key="", root_id="", verbose=False):
        return f"[{role_label}] reply to: {user_msg}"
    return fn


def _make_msg(routing_key: str, text: str, wake: str | None = None) -> InboundMessage:
    meta = {"wake_reason": wake} if wake else {}
    return InboundMessage(
        routing_key=routing_key, content=text,
        msg_id="m1", root_id="", sender_id="ou_x", ts=0,
        meta=meta,
    )


# ---------- _pick_agent_fn 单元逻辑 ----------


def test_pick_agent_fn_team_prefix_routes_to_role() -> None:
    pm_fn = lambda *a, **kw: None  # noqa: E731
    mgr_fn = lambda *a, **kw: None  # noqa: E731
    fn = _pick_agent_fn("team:pm", {"pm": pm_fn, "manager": mgr_fn}, None)
    assert fn is pm_fn


def test_pick_agent_fn_p2p_routes_to_manager() -> None:
    mgr_fn = lambda *a, **kw: None  # noqa: E731
    pm_fn = lambda *a, **kw: None  # noqa: E731
    fn = _pick_agent_fn("p2p:ou_123", {"pm": pm_fn, "manager": mgr_fn}, None)
    assert fn is mgr_fn


def test_pick_agent_fn_unknown_team_role_raises() -> None:
    with pytest.raises(ValueError, match="no agent_fn"):
        _pick_agent_fn("team:unknown", {"manager": lambda *a, **kw: None}, None)


# ---------- Runner.dispatch wake 去重 ----------


@pytest.mark.asyncio
async def test_wake_dedup_drops_duplicate(tmp_path: Path) -> None:
    """相同 routing_key 已有 pending wake → 第二条 wake 被丢弃."""
    sender = _StubSender()
    session_mgr = SessionManager(tmp_path / "sessions")

    agent_calls: list[str] = []

    async def slow_agent(user_msg, history, session_id,
                         routing_key="", root_id="", verbose=False) -> str:
        agent_calls.append(user_msg)
        # 故意慢：让 wake 消息在 queue 里堆
        await asyncio.sleep(0.3)
        return "ok"

    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn_map={"pm": slow_agent, "manager": slow_agent},
        idle_timeout=1.0,
    )

    # 先发一个 wake（会入队并立即被 worker 取走，开始 sleep 0.3s）
    await runner.dispatch(_make_msg("team:pm", "[wake] new mail 1", wake="new_mail"))
    # 短暂 sleep 让 worker 进入处理状态
    await asyncio.sleep(0.05)
    # 再发两个 wake——此时 worker 正在 sleep，队列可能为空（因为 worker get 完）
    # 所以第 2 条可能真入队，第 3 条应被去重
    await runner.dispatch(_make_msg("team:pm", "[wake] new mail 2", wake="new_mail"))
    await runner.dispatch(_make_msg("team:pm", "[wake] new mail 3", wake="new_mail"))

    # 等所有 task 完成
    await asyncio.sleep(1.5)

    # 第 3 条应被去重（第 2 条已在队列里）→ agent 最多被调 2 次
    assert len(agent_calls) <= 2, f"wake 去重失效：agent 被调 {len(agent_calls)} 次"


@pytest.mark.asyncio
async def test_non_wake_message_not_dedup(tmp_path: Path) -> None:
    """非 wake 消息（飞书用户消息）不去重."""
    sender = _StubSender()
    session_mgr = SessionManager(tmp_path / "sessions")

    count = 0
    async def agent_fn(user_msg, history, session_id,
                       routing_key="", root_id="", verbose=False) -> str:
        nonlocal count
        count += 1
        return f"ack {count}"

    runner = Runner(
        session_mgr=session_mgr, sender=sender,
        agent_fn_map={"manager": agent_fn}, idle_timeout=1.0,
    )

    for i in range(3):
        await runner.dispatch(_make_msg("p2p:ou_x", f"msg {i}"))
    await asyncio.sleep(1.0)

    assert count == 3, "飞书消息不应被去重"


# ---------- Runner 按 routing_key 路由到对应 agent ----------


@pytest.mark.asyncio
async def test_runner_routes_p2p_to_manager(tmp_path: Path) -> None:
    sender = _StubSender()
    session_mgr = SessionManager(tmp_path / "sessions")

    received: dict[str, list[str]] = {"manager": [], "pm": []}

    def make_fn(role: str):
        async def fn(user_msg, history, session_id,
                     routing_key="", root_id="", verbose=False) -> str:
            received[role].append(user_msg)
            return f"{role} reply"
        return fn

    runner = Runner(
        session_mgr=session_mgr, sender=sender,
        agent_fn_map={"manager": make_fn("manager"), "pm": make_fn("pm")},
        idle_timeout=1.0,
    )

    await runner.dispatch(_make_msg("p2p:ou_xiaohan", "帮我做个小网站"))
    await runner.dispatch(_make_msg("team:pm", "[wake]", wake="new_mail"))

    await asyncio.sleep(0.5)

    assert received["manager"] == ["帮我做个小网站"]
    assert received["pm"] == ["[wake]"]


@pytest.mark.asyncio
async def test_runner_does_not_send_reply_for_team_wake(tmp_path: Path) -> None:
    """team:{role} wake 消息处理完不应回复到飞书（无 sender.send 调用）."""
    sender = _StubSender()
    session_mgr = SessionManager(tmp_path / "sessions")

    async def fn(user_msg, history, session_id,
                 routing_key="", root_id="", verbose=False) -> str:
        return "internal ack"

    runner = Runner(
        session_mgr=session_mgr, sender=sender,
        agent_fn_map={"pm": fn}, idle_timeout=1.0,
    )
    await runner.dispatch(_make_msg("team:pm", "[wake]", wake="new_mail"))
    await asyncio.sleep(0.5)

    # team wake 不回飞书
    assert sender.sent == []


@pytest.mark.asyncio
async def test_runner_sends_reply_for_p2p(tmp_path: Path) -> None:
    sender = _StubSender()
    session_mgr = SessionManager(tmp_path / "sessions")

    async def fn(user_msg, history, session_id,
                 routing_key="", root_id="", verbose=False) -> str:
        return f"reply to {user_msg}"

    runner = Runner(
        session_mgr=session_mgr, sender=sender,
        agent_fn_map={"manager": fn}, idle_timeout=1.0,
    )
    await runner.dispatch(_make_msg("p2p:ou_x", "hi"))
    await asyncio.sleep(0.5)

    assert sender.sent == [("p2p:ou_x", "reply to hi")]
