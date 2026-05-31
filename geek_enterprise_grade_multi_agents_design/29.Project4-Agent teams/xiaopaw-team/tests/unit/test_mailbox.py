"""
mailbox.py 单元测试（T-MB-*）

对齐 test-design.md §3.2 团队协作层测试点 T-MB-01 ~ T-MB-06：
- send_mail / read_inbox / mark_done / reset_stale
- FileLock 并发保护
- 三态状态机（unread → in_progress → done）
- project_id 字段
- timestamp ISO 8601 UTC +00:00 格式
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from xiaopaw_team.tools.mailbox import (
    send_mail,
    read_inbox,
    mark_done,
    reset_stale,
    init_mailboxes,
)


@pytest.fixture
def mbox_dir(tmp_path: Path) -> Path:
    """初始化一个完整的 mailboxes 目录，4 个空 json。"""
    mdir = tmp_path / "mailboxes"
    init_mailboxes(mdir, roles=["manager", "pm", "rd", "qa"])
    return mdir


# ---------- T-MB-01: send_mail 基础 ----------


def test_send_mail_basic_fields(mbox_dir: Path) -> None:
    msg_id = send_mail(
        mbox_dir,
        to="pm",
        from_="manager",
        type_="task_assign",
        subject="产品设计",
        content="请读 needs/ 写 design/",
        project_id="proj-test-0001",
    )
    assert re.match(r"^msg-[0-9a-f]{8}$", msg_id), "id 格式 msg-{8hex}"

    data = json.loads((mbox_dir / "pm.json").read_text())
    assert len(data) == 1
    m = data[0]
    # 必填字段全齐
    for k in ("id", "project_id", "from", "to", "type", "subject", "content",
              "timestamp", "status", "processing_since"):
        assert k in m, f"missing {k}"
    assert m["id"] == msg_id
    assert m["from"] == "manager"
    assert m["to"] == "pm"
    assert m["type"] == "task_assign"
    assert m["status"] == "unread"
    assert m["processing_since"] is None
    # timestamp: ISO 8601 UTC +00:00 (v1.3-P0-6)
    assert m["timestamp"].endswith("+00:00")
    # 能 round-trip 解析
    ts = datetime.fromisoformat(m["timestamp"])
    assert ts.tzinfo is not None


def test_send_mail_appends_not_overwrites(mbox_dir: Path) -> None:
    """同一 inbox 多次 send_mail append 不覆盖。"""
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="a", content="x", project_id="p1")
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="b", content="y", project_id="p1")
    data = json.loads((mbox_dir / "pm.json").read_text())
    assert len(data) == 2
    assert [m["subject"] for m in data] == ["a", "b"]


def test_send_mail_rejects_invalid_role(mbox_dir: Path) -> None:
    with pytest.raises(ValueError, match="invalid"):
        send_mail(mbox_dir, to="stranger", from_="manager", type_="task_assign",
                  subject="x", content="y", project_id="p1")


# ---------- T-MB-02: read_inbox 三态机 ----------


def test_read_inbox_marks_unread_to_in_progress(mbox_dir: Path) -> None:
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="s", content="c", project_id="p1")
    unread = read_inbox(mbox_dir, role="pm")
    assert len(unread) == 1
    # 返回快照，status 已是 in_progress（供 LLM 判断使用）
    assert unread[0]["status"] == "in_progress"
    # 文件里也是 in_progress
    data = json.loads((mbox_dir / "pm.json").read_text())
    assert data[0]["status"] == "in_progress"
    assert data[0]["processing_since"] is not None
    assert data[0]["processing_since"].endswith("+00:00")


def test_read_inbox_second_call_returns_empty(mbox_dir: Path) -> None:
    """第二次读不该重复拿到 in_progress 的消息（只取 unread）。"""
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="s", content="c", project_id="p1")
    read_inbox(mbox_dir, role="pm")
    second = read_inbox(mbox_dir, role="pm")
    assert second == []


def test_read_inbox_returns_snapshot_not_reference(mbox_dir: Path) -> None:
    """返回快照：调用方修改返回值不影响磁盘内容。"""
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="original", content="c", project_id="p1")
    unread = read_inbox(mbox_dir, role="pm")
    unread[0]["subject"] = "tampered"
    on_disk = json.loads((mbox_dir / "pm.json").read_text())
    assert on_disk[0]["subject"] == "original"


# ---------- T-MB-03: mark_done ----------


def test_mark_done_transitions_in_progress_to_done(mbox_dir: Path) -> None:
    msg_id = send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
                      subject="s", content="c", project_id="p1")
    read_inbox(mbox_dir, role="pm")  # 转到 in_progress
    mark_done(mbox_dir, role="pm", msg_id=msg_id)
    data = json.loads((mbox_dir / "pm.json").read_text())
    assert data[0]["status"] == "done"


def test_mark_done_requires_in_progress_state(mbox_dir: Path) -> None:
    """对 unread 状态 mark_done 应该拒绝或 no-op，不能跳过 read_inbox。"""
    msg_id = send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
                      subject="s", content="c", project_id="p1")
    with pytest.raises(ValueError, match="not in_progress"):
        mark_done(mbox_dir, role="pm", msg_id=msg_id)


def test_mark_done_on_nonexistent_id_raises(mbox_dir: Path) -> None:
    with pytest.raises(KeyError):
        mark_done(mbox_dir, role="pm", msg_id="msg-deadbeef")


# ---------- T-MB-04: reset_stale ----------


def test_reset_stale_recovers_timeouted_in_progress(mbox_dir: Path, monkeypatch) -> None:
    """processing_since 超过 timeout_sec 的 in_progress → 恢复为 unread。"""
    msg_id = send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
                      subject="s", content="c", project_id="p1")
    read_inbox(mbox_dir, role="pm")  # to in_progress
    # 伪造 processing_since 远在过去
    data = json.loads((mbox_dir / "pm.json").read_text())
    data[0]["processing_since"] = "2020-01-01T00:00:00+00:00"
    (mbox_dir / "pm.json").write_text(json.dumps(data))

    reset_count = reset_stale(mbox_dir, role="pm", timeout_sec=60)
    assert reset_count == 1
    data = json.loads((mbox_dir / "pm.json").read_text())
    assert data[0]["status"] == "unread"
    assert data[0]["processing_since"] is None


def test_reset_stale_keeps_recent_in_progress(mbox_dir: Path) -> None:
    """processing_since 还没超时 → 不动。"""
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="s", content="c", project_id="p1")
    read_inbox(mbox_dir, role="pm")
    count = reset_stale(mbox_dir, role="pm", timeout_sec=900)
    assert count == 0
    data = json.loads((mbox_dir / "pm.json").read_text())
    assert data[0]["status"] == "in_progress"


# ---------- T-MB-05: FileLock 保护（并发用线程模拟）----------


def test_concurrent_send_mail_no_message_loss(mbox_dir: Path) -> None:
    """并发 send_mail 的 last-write-wins 必须被 FileLock 防护。"""
    import threading

    N = 20

    def sender(i: int) -> None:
        send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
                  subject=f"m{i}", content="c", project_id="p1")

    threads = [threading.Thread(target=sender, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    data = json.loads((mbox_dir / "pm.json").read_text())
    assert len(data) == N, "并发写必须全部入列"
    # 每条 subject 都是唯一的
    subjects = sorted([m["subject"] for m in data])
    assert subjects == sorted([f"m{i}" for i in range(N)])


# ---------- T-MB-06: project_id 过滤（基础）----------


def test_mailbox_preserves_project_id_per_message(mbox_dir: Path) -> None:
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="p1 task", content="c", project_id="proj-A")
    send_mail(mbox_dir, to="pm", from_="manager", type_="task_assign",
              subject="p2 task", content="c", project_id="proj-B")
    data = json.loads((mbox_dir / "pm.json").read_text())
    assert {m["project_id"] for m in data} == {"proj-A", "proj-B"}
