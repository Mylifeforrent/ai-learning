"""Unit tests for build_role_tools factory in agents.build."""
from __future__ import annotations

from pathlib import Path

from xiaopaw_team.agents.build import build_role_tools


def _tool_names(tools) -> set[str]:
    return {t.name for t in tools}


def test_non_manager_has_5_common(tmp_path: Path) -> None:
    tools = build_role_tools(role="pm", workspace_root=tmp_path, cron_tasks_path=tmp_path / "t.json")
    names = _tool_names(tools)
    assert names == {"send_mail", "read_inbox", "mark_done", "read_shared", "write_shared"}


def test_manager_has_8(tmp_path: Path) -> None:
    tools = build_role_tools(role="manager", workspace_root=tmp_path, cron_tasks_path=tmp_path / "t.json")
    names = _tool_names(tools)
    assert names == {
        "send_mail", "read_inbox", "mark_done", "read_shared", "write_shared",
        "create_project", "append_event", "send_to_human",
    }


def test_rd_and_qa(tmp_path: Path) -> None:
    for role in ["rd", "qa"]:
        tools = build_role_tools(role=role, workspace_root=tmp_path, cron_tasks_path=tmp_path / "t.json")
        names = _tool_names(tools)
        assert "create_project" not in names
        assert "append_event" not in names
        assert "send_to_human" not in names
        assert "send_mail" in names
