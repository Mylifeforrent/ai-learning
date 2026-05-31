"""Unit tests for xiaopaw_team.cron.tasks_store."""
from __future__ import annotations

import json
import time
from pathlib import Path

from xiaopaw_team.cron import tasks_store


def test_create_at_job_default_delay(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    job_id = tasks_store.create_job(
        p, name="w", routing_key="team:pm", message="hi"
    )
    assert job_id.startswith("job-")
    data = json.loads(p.read_text())
    assert data["version"] == 1 and len(data["jobs"]) == 1
    j = data["jobs"][0]
    assert j["schedule"]["kind"] == "at"
    assert j["schedule"]["at_ms"] is not None
    assert j["delete_after_run"] is True


def test_schedule_wake(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    job_id = tasks_store.schedule_wake(p, role="pm", reason="new_mail", delay_ms=500)
    jobs = tasks_store.list_jobs(p)
    assert len(jobs) == 1
    j = jobs[0]
    assert j["id"] == job_id
    assert j["payload"]["routing_key"] == "team:pm"
    assert j["payload"]["message"].startswith("__wake__:new_mail")


def test_schedule_wake_with_project_id(tmp_path: Path) -> None:
    """wake message 拼 project_id 让 Agent 直接知道读哪个邮箱."""
    p = tmp_path / "tasks.json"
    tasks_store.schedule_wake(p, role="pm", reason="new_mail", project_id="todo-mvp")
    jobs = tasks_store.list_jobs(p)
    assert jobs[0]["payload"]["message"] == "__wake__:new_mail:todo-mvp"


def test_schedule_heartbeat_replaces_existing(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    tasks_store.schedule_heartbeat(p, role="pm", interval_ms=30000, first_delay_ms=0)
    tasks_store.schedule_heartbeat(p, role="pm", interval_ms=60000, first_delay_ms=7000)
    jobs = tasks_store.list_jobs(p)
    hb = [j for j in jobs if j["id"] == "heartbeat-pm"]
    assert len(hb) == 1
    assert hb[0]["schedule"]["every_ms"] == 60000


def test_delete_job(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    jid = tasks_store.create_job(p, name="x", routing_key="team:rd", message="")
    assert tasks_store.delete_job(p, job_id=jid) is True
    assert tasks_store.delete_job(p, job_id=jid) is False
    assert tasks_store.list_jobs(p) == []


def test_create_job_invalid_kind(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    import pytest

    with pytest.raises(ValueError):
        tasks_store.create_job(p, name="x", routing_key="team:pm", message="", schedule_kind="weekly")


def test_create_every_requires_every_ms(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    import pytest

    with pytest.raises(ValueError):
        tasks_store.create_job(
            p, name="x", routing_key="team:pm", message="",
            schedule_kind="every", every_ms=None,
        )
