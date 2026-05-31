"""Unit tests for feishu_bridge classify + CheckpointStore."""
from __future__ import annotations

from pathlib import Path

from xiaopaw_team.tools.feishu_bridge import (
    CheckpointStore,
    classify,
)


def _rk() -> str:
    return "p2p:abc123"


# ── CheckpointStore ─────────────────────────────────────────────────────────


def test_register_and_pending(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "pending.jsonl")
    cid = store.register(
        routing_key=_rk(), project_id="p1", kind="checkpoint_request", question="q?"
    )
    pend = store.pending()
    assert len(pend) == 1 and pend[0].checkpoint_id == cid
    pend_rk = store.pending_for_routing_key(_rk())
    assert len(pend_rk) == 1


def test_resolve_removes_from_pending(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "pending.jsonl")
    cid = store.register(routing_key=_rk(), project_id="p1", kind="info", question="q")
    assert store.resolve(cid) is True
    assert store.pending() == []
    # double resolve returns False
    assert store.resolve(cid) is False


def test_resolve_missing(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "pending.jsonl")
    assert store.resolve("ckpt-missing") is False


# ── classify ────────────────────────────────────────────────────────────────


def test_classify_callback_value_wins(tmp_path: Path) -> None:
    cat, cid = classify("irrelevant", callback_value={"checkpoint_id": "ckpt-12345678"})
    assert cat == "checkpoint_response" and cid == "ckpt-12345678"


def test_classify_new_requirement() -> None:
    cat, cid = classify("帮我做一个小爪子日记CRUD网站")
    assert cat == "new_requirement" and cid is None


def test_classify_sop_keywords() -> None:
    cat, _ = classify("我们来聊下 SOP 流程吧")
    assert cat == "sop_cocreate"


def test_classify_explicit_ckpt_id_in_text(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "p.jsonl")
    cid = store.register(routing_key=_rk(), project_id="p1", kind="cr", question="q")
    pend = store.pending_for_routing_key(_rk())
    cat, matched = classify(f"同意 {cid}", pending_for_rk=pend)
    assert cat == "checkpoint_response" and matched == cid


def test_classify_approval_binds_to_latest_pending(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "p.jsonl")
    store.register(routing_key=_rk(), project_id="p1", kind="cr", question="q1")
    cid2 = store.register(routing_key=_rk(), project_id="p1", kind="cr", question="q2")
    pend = store.pending_for_routing_key(_rk())
    cat, matched = classify("同意", pending_for_rk=pend)
    assert cat == "checkpoint_response" and matched == cid2


def test_classify_fallback() -> None:
    cat, _ = classify("你好")
    assert cat == "need_discussion"


def test_classify_empty() -> None:
    cat, _ = classify("")
    assert cat == "need_discussion"
