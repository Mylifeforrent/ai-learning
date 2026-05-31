"""Unit tests for main.py wiring (non-LLM)."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from xiaopaw_team.main import build_runtime, register_heartbeats


@pytest.mark.asyncio
async def test_build_runtime_starts_cron(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    data_dir = tmp_path / "data"
    ctx_dir = tmp_path / "ctx"
    runner, cron_svc, session_mgr = await build_runtime(
        workspace_root=workspace_root,
        data_dir=data_dir,
        ctx_dir=ctx_dir,
        sandbox_url="http://localhost:8029/mcp",
        sender=None,
    )
    try:
        # 4 heartbeats registered
        tasks_path = data_dir / "cron" / "tasks.json"
        assert tasks_path.exists()
        # agent_fn_map has all 4 roles
        assert set(runner._agent_fn_map.keys()) == {"manager", "pm", "rd", "qa"}
        # Cron service is running
        assert cron_svc._running is True
    finally:
        await cron_svc.stop()


def test_register_heartbeats_stagger(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    register_heartbeats(tasks_path)
    import json

    jobs = json.loads(tasks_path.read_text())["jobs"]
    heartbeats = [j for j in jobs if j["id"].startswith("heartbeat-")]
    assert len(heartbeats) == 4
    # Check stagger: 4 different first-delay values
    next_runs = sorted(j["state"]["next_run_at_ms"] for j in heartbeats)
    spreads = [next_runs[i + 1] - next_runs[i] for i in range(3)]
    # 7000ms gap (allow ±500ms jitter from time.time)
    for s in spreads:
        assert 6500 <= s <= 7500, f"spread={s}ms"
