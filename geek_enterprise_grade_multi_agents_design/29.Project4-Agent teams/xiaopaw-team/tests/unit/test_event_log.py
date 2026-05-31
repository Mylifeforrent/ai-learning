"""
event_log.py 单元测试（T-EL-*）

对齐 DESIGN.md §11.4 append-only JSON Lines + 附录 A 事件枚举 + 自愈检查。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from xiaopaw_team.tools.event_log import (
    append_event,
    read_events,
    init_events,
    tail_events,
    iter_events,
)


@pytest.fixture
def events_path(tmp_path: Path) -> Path:
    p = tmp_path / "events.jsonl"
    init_events(p)
    return p


def test_append_event_assigns_seq_starting_from_1(events_path: Path) -> None:
    append_event(events_path, action="project_created",
                 payload={"project_id": "p1", "sop": "sop_feature_dev",
                          "user_open_id": "ou_x", "created_at": "2026-04-20T00:00:00+00:00"})
    events = read_events(events_path)
    assert len(events) == 1
    assert events[0]["seq"] == 1
    assert events[0]["actor"] == "manager"
    assert events[0]["action"] == "project_created"
    assert events[0]["ts"].endswith("+00:00")


def test_append_event_increments_seq_monotonically(events_path: Path) -> None:
    for i in range(5):
        append_event(events_path, action="requirements_discovery_started",
                     payload={})
    events = read_events(events_path)
    assert [e["seq"] for e in events] == [1, 2, 3, 4, 5]


def test_append_event_rejects_unknown_action(events_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown action"):
        append_event(events_path, action="totally_fake_action", payload={})


def test_read_events_skips_corrupt_last_line(events_path: Path) -> None:
    """半写场景：最后一行是无效 JSON，read_events 应 skip 并返回之前的有效事件（v1.3 §11.4.1）."""
    # 先写 2 条合法事件
    append_event(events_path, action="project_created",
                 payload={"project_id": "p1", "sop": "x", "user_open_id": "u",
                          "created_at": "2026-04-20T00:00:00+00:00"})
    append_event(events_path, action="requirements_discovery_started", payload={})
    # 追加一行损坏 JSON
    with events_path.open("a") as f:
        f.write('{"broken":true,"seq"')  # 未闭合
    events = read_events(events_path)
    assert len(events) == 2, "破损行必须 skip，不抛异常"


def test_tail_events_returns_last_n(events_path: Path) -> None:
    for i in range(10):
        append_event(events_path, action="requirements_discovery_started", payload={})
    last3 = tail_events(events_path, n=3)
    assert len(last3) == 3
    assert [e["seq"] for e in last3] == [8, 9, 10]


def test_iter_events_is_generator(events_path: Path) -> None:
    for _ in range(3):
        append_event(events_path, action="requirements_discovery_started", payload={})
    gen = iter_events(events_path)
    first = next(gen)
    assert first["seq"] == 1


def test_concurrent_append_preserves_seq_uniqueness(events_path: Path) -> None:
    """并发 append 必须用 FileLock 保证 seq 唯一."""
    import threading

    def worker(i: int) -> None:
        append_event(events_path, action="requirements_discovery_started",
                     payload={"idx": i})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    events = read_events(events_path)
    assert len(events) == 20
    seqs = [e["seq"] for e in events]
    assert sorted(seqs) == list(range(1, 21)), "seq 必须严格递增且唯一"
