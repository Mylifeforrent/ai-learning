"""Unit tests for xiaopaw_team.tools.team_tools (8 Python Tools)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from xiaopaw_team.tools.team_tools import (
    AppendEventTool,
    CreateProjectTool,
    MarkDoneTool,
    ReadInboxTool,
    ReadSharedTool,
    SendMailTool,
    SendToHumanTool,
    WriteSharedTool,
)


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    (tmp_path / "shared" / "projects").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def cron_path(tmp_path: Path) -> Path:
    return tmp_path / "data" / "cron" / "tasks.json"


@pytest.fixture
def pid() -> str:
    return "pawdiary-001"


@pytest.fixture
def created_project(workspace_root: Path, pid: str) -> Path:
    tool = CreateProjectTool(workspace_root=workspace_root)
    out = json.loads(tool._run(project_id=pid, project_name="Demo", needs_content="# needs\n"))
    assert out["errcode"] == 0
    return workspace_root / "shared" / "projects" / pid


class TestCreateProjectTool:
    def test_creates_directory_tree(self, workspace_root: Path, pid: str) -> None:
        tool = CreateProjectTool(workspace_root=workspace_root)
        out = json.loads(tool._run(project_id=pid, project_name="X", needs_content="# n"))
        assert out["errcode"] == 0
        proj = workspace_root / "shared" / "projects" / pid
        for d in ["needs", "design", "tech", "code", "qa", "qa/defects", "reviews", "mailboxes", "logs/l2_task"]:
            assert (proj / d).is_dir(), f"missing {d}"
        assert (proj / "events.jsonl").exists()
        assert (proj / "needs" / "requirements.md").read_text() == "# n"

    def test_rejects_invalid_project_id(self, workspace_root: Path) -> None:
        tool = CreateProjectTool(workspace_root=workspace_root)
        out = json.loads(tool._run(project_id="Bad!ID", project_name="x", needs_content=""))
        assert out["errcode"] == 1

    def test_idempotent(self, workspace_root: Path, pid: str) -> None:
        tool = CreateProjectTool(workspace_root=workspace_root)
        out1 = json.loads(tool._run(project_id=pid, project_name="X", needs_content="# a"))
        out2 = json.loads(tool._run(project_id=pid, project_name="X", needs_content="# b"))
        assert out1["errcode"] == 0 and out2["errcode"] == 0


class TestSendMailTool:
    def test_send_writes_mailbox_and_cron(
        self, workspace_root: Path, cron_path: Path, created_project: Path, pid: str
    ) -> None:
        tool = SendMailTool(
            workspace_root=workspace_root, cron_tasks_path=cron_path, from_role="manager"
        )
        out = json.loads(
            tool._run(
                to="pm", type="task_assign", subject="产品设计 (第 1 轮)",
                content={"task": "design"}, project_id=pid,
            )
        )
        assert out["errcode"] == 0
        assert out["msg_id"].startswith("msg-")
        # inbox has one unread
        inbox = created_project / "mailboxes" / "pm.json"
        messages = json.loads(inbox.read_text())
        assert len(messages) == 1 and messages[0]["status"] == "unread"
        # cron has at wake
        jobs = json.loads(cron_path.read_text())["jobs"]
        assert any(j["payload"]["routing_key"] == "team:pm" for j in jobs)

    def test_invalid_type(
        self, workspace_root: Path, cron_path: Path, created_project: Path, pid: str
    ) -> None:
        tool = SendMailTool(workspace_root=workspace_root, cron_tasks_path=cron_path, from_role="manager")
        out = json.loads(tool._run(
            to="pm", type="bogus", subject="x", content="y", project_id=pid
        ))
        assert out["errcode"] == 1


class TestReadInboxTool:
    def test_read_empty(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        tool = ReadInboxTool(workspace_root=workspace_root, role="pm")
        out = json.loads(tool._run(project_id=pid))
        assert out["errcode"] == 0 and out["count"] == 0

    def test_read_and_markdone(
        self, workspace_root: Path, cron_path: Path, created_project: Path, pid: str
    ) -> None:
        send = SendMailTool(workspace_root=workspace_root, cron_tasks_path=cron_path, from_role="manager")
        json.loads(send._run(to="pm", type="task_assign", subject="s (第 1 轮)", content="x", project_id=pid))
        read = ReadInboxTool(workspace_root=workspace_root, role="pm")
        out = json.loads(read._run(project_id=pid))
        assert out["count"] == 1
        msg_id = out["messages"][0]["id"]
        # now mark_done
        mark = MarkDoneTool(workspace_root=workspace_root, role="pm")
        mout = json.loads(mark._run(project_id=pid, msg_id=msg_id))
        assert mout["errcode"] == 0
        # re-read should be 0
        out2 = json.loads(read._run(project_id=pid))
        assert out2["count"] == 0


class TestAppendEventTool:
    def test_append(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        tool = AppendEventTool(workspace_root=workspace_root)
        out = json.loads(tool._run(
            project_id=pid, action="assigned",
            payload={"to": "pm", "msg_id": "msg-abcd1234"},
        ))
        assert out["errcode"] == 0 and out["seq"] >= 1

    def test_rejects_unknown_action(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        tool = AppendEventTool(workspace_root=workspace_root)
        out = json.loads(tool._run(project_id=pid, action="nonsense", payload={}))
        assert out["errcode"] == 1


class TestReadWriteSharedTool:
    def test_write_and_read(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        w = WriteSharedTool(workspace_root=workspace_root, role="pm")
        out = json.loads(w._run(project_id=pid, rel_path="design/product_spec.md", content="# spec"))
        assert out["errcode"] == 0
        r = ReadSharedTool(workspace_root=workspace_root, role="pm")
        ro = json.loads(r._run(project_id=pid, rel_path="design/product_spec.md"))
        assert ro["errcode"] == 0 and ro["content"] == "# spec"

    def test_write_permission_denied(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        w = WriteSharedTool(workspace_root=workspace_root, role="rd")
        out = json.loads(w._run(project_id=pid, rel_path="design/product_spec.md", content="x"))
        assert out["errcode"] == 1 and "permission" in out["errmsg"]

    def test_write_reviews_reviewer_check(
        self, workspace_root: Path, created_project: Path, pid: str
    ) -> None:
        w = WriteSharedTool(workspace_root=workspace_root, role="qa")
        # qa writes qa-prefixed review → OK
        out_ok = json.loads(w._run(
            project_id=pid, rel_path="reviews/product_design/qa_clarity.md", content="ok"
        ))
        assert out_ok["errcode"] == 0
        # qa tries to write pm_xx.md → rejected
        out_bad = json.loads(w._run(
            project_id=pid, rel_path="reviews/product_design/pm_x.md", content="no"
        ))
        assert out_bad["errcode"] == 1


class TestSendToHumanTool:
    def test_info_no_sender(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        tool = SendToHumanTool(workspace_root=workspace_root, sender=None)
        out = json.loads(tool._run(
            routing_key="p2p:abc", message="hi", kind="info", project_id=pid,
        ))
        assert out["errcode"] == 0
        # event appended
        events = (workspace_root / "shared" / "projects" / pid / "events.jsonl").read_text().strip().splitlines()
        # first is project_created
        actions = [json.loads(l)["action"] for l in events]
        assert "info_sent" in actions

    def test_checkpoint_requires_checkpoint_id(
        self, workspace_root: Path, created_project: Path, pid: str
    ) -> None:
        tool = SendToHumanTool(workspace_root=workspace_root, sender=None)
        out = json.loads(tool._run(
            routing_key="p2p:abc", message="m", kind="checkpoint_request", project_id=pid,
        ))
        assert out["errcode"] == 1

    def test_invalid_kind(self, workspace_root: Path, created_project: Path, pid: str) -> None:
        tool = SendToHumanTool(workspace_root=workspace_root, sender=None)
        out = json.loads(tool._run(routing_key="p2p:abc", message="m", kind="weird"))
        assert out["errcode"] == 1
