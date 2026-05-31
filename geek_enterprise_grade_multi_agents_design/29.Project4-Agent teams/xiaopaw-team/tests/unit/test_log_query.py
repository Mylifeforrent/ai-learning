"""
log_query.py 单元测试（T-LQ-*）

对齐 DESIGN.md §16.6 self_retrospective 的 CLI 工具：`tools/log_query.py`
子命令：stats / tasks / steps / l1 / all-agents

产出 JSON 到 stdout，被 self_retrospective Sub-Crew 通过 bash 调用。
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from xiaopaw_team.tools.log_query import (
    query_stats,
    query_tasks,
    query_l1,
    query_all_agents,
)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


@pytest.fixture
def seeded_logs(tmp_path: Path) -> Path:
    """在 tmp_path 下造一组 L1 + L2 日志模拟 1 周工作数据。"""
    now = datetime.now(timezone.utc)
    l2_dir = tmp_path / "shared" / "projects" / "proj-A" / "logs" / "l2_task"
    l2_dir.mkdir(parents=True)
    l1_dir = tmp_path / "shared" / "logs" / "l1_human"
    l1_dir.mkdir(parents=True)

    # PM 8 个任务（3 个低质量）
    l2_file = l2_dir / "2026-04-20.jsonl"
    pm_tasks = [
        ("t001", "pm", 0.40, "用户登录功能产品设计文档"),
        ("t002", "pm", 0.85, "资料页设计"),
        ("t003", "pm", 0.42, "产品设计文档v2（用户登录）"),
        ("t004", "pm", 0.80, "列表页设计"),
        ("t005", "pm", 0.75, "搜索功能设计"),
        ("t006", "pm", 0.38, "用户注册设计迭代（移动端）"),
        ("t007", "pm", 0.90, "帮助页设计"),
        ("t008", "pm", 0.78, "仪表盘设计"),
    ]
    with l2_file.open("w") as f:
        for i, (tid, role, q, desc) in enumerate(pm_tasks):
            ts = (now - timedelta(days=6 - i // 2)).isoformat(timespec="seconds")
            entry = {
                "ts": ts,
                "project_id": "proj-A",
                "role": role,
                "session_id": f"team-{role}-ws001",
                "task_id": tid,
                "trigger": {"source_msg_id": "m", "wake_reason": "new_mail"},
                "duration_ms": 42000,
                "tokens": {"prompt": 3000, "completion": 800, "total": 3800},
                "tools_used": ["skill_loader", "write_shared", "send_mail"],
                "skills_invoked": [{"name": "product_design", "type": "task", "result_status": "success"}],
                "artifacts_produced": ["design/product_spec.md"],
                "self_review_passed": q > 0.7,
                "result_quality_estimate": q,
                "result_quality_breakdown": {
                    "completeness": 1.0, "self_review": q,
                    "hard_constraints": 1.0, "clarity": q, "timeliness": 0.8,
                },
                "result_quality_source": "self_score_skill",
                "errors": [],
                # 给 read_l3_steps 用
                "task_desc": desc,
            }
            f.write(json.dumps(entry) + "\n")

    # QA 5 任务（都正常）
    qa_tasks = [
        ("q001", "qa", 0.82, "测试执行"),
        ("q002", "qa", 0.75, "测试执行"),
        ("q003", "qa", 0.88, "测试设计"),
        ("q004", "qa", 0.70, "代码走查"),
        ("q005", "qa", 0.85, "测试设计"),
    ]
    with l2_file.open("a") as f:
        for i, (tid, role, q, desc) in enumerate(qa_tasks):
            ts = (now - timedelta(days=5 - i)).isoformat(timespec="seconds")
            entry = {
                "ts": ts,
                "project_id": "proj-A",
                "role": role,
                "session_id": f"team-{role}-ws001",
                "task_id": tid,
                "trigger": {"source_msg_id": "m", "wake_reason": "new_mail"},
                "duration_ms": 30000,
                "tokens": {"prompt": 2500, "completion": 600, "total": 3100},
                "tools_used": ["skill_loader"],
                "skills_invoked": [{"name": "test_run", "type": "task", "result_status": "success"}],
                "artifacts_produced": ["qa/test_report.md"],
                "self_review_passed": True,
                "result_quality_estimate": q,
                "result_quality_breakdown": None,
                "result_quality_source": "self_score_skill",
                "errors": [],
                "task_desc": desc,
            }
            f.write(json.dumps(entry) + "\n")

    # L1: 3 条人类纠正（关键词"移动端"）
    l1_file = l1_dir / "2026-04.jsonl"
    with l1_file.open("w") as f:
        for i in range(3):
            ts = (now - timedelta(days=5 - i)).isoformat(timespec="seconds")
            entry = {
                "ts": ts,
                "action": "checkpoint_response_received",
                "direction": "inbound",
                "project_id": "proj-A",
                "user_open_id": "ou_x",
                "role": "manager",
                "ck_id": f"ck-req-00{i}",
                "content": {
                    "user_text": f"不对，移动端适配漏了第 {i} 处",
                    "classified_as": "rejected",
                },
                "artifacts": [],
            }
            f.write(json.dumps(entry) + "\n")

    return tmp_path


# ---------- stats ----------


def test_query_stats_pm_7days(seeded_logs: Path) -> None:
    result = query_stats(seeded_logs, agent_id="pm", days=7)
    assert result["task_count"] == 8
    assert result["failure_count"] == 3  # q < 0.5
    assert 0.6 < result["avg_quality"] < 0.8
    assert result["agent_id"] == "pm"


def test_query_stats_empty_when_no_data(seeded_logs: Path) -> None:
    result = query_stats(seeded_logs, agent_id="rd", days=7)  # RD 无数据
    assert result["task_count"] == 0
    assert result["avg_quality"] is None


# ---------- tasks ----------


def test_query_tasks_sort_quality_asc_top3(seeded_logs: Path) -> None:
    result = query_tasks(seeded_logs, agent_id="pm", days=7,
                         sort="quality_asc", limit=3)
    tasks = result["tasks"]
    assert len(tasks) == 3
    assert tasks[0]["task_id"] == "t006"   # 0.38 最低
    assert tasks[1]["task_id"] == "t001"   # 0.40
    assert tasks[2]["task_id"] == "t003"   # 0.42
    # 每条有关键字段
    assert "result_quality_estimate" in tasks[0]
    assert "task_desc" in tasks[0]


def test_query_tasks_no_sort_preserves_order(seeded_logs: Path) -> None:
    result = query_tasks(seeded_logs, agent_id="pm", days=7)
    assert len(result["tasks"]) == 8
    # 默认按 ts asc
    tss = [t["ts"] for t in result["tasks"]]
    assert tss == sorted(tss)


# ---------- l1 ----------


def test_query_l1_by_keyword(seeded_logs: Path) -> None:
    result = query_l1(seeded_logs, days=7, keyword="移动端")
    assert len(result["entries"]) == 3
    assert all("移动端" in e["content"]["user_text"] for e in result["entries"])


def test_query_l1_no_keyword(seeded_logs: Path) -> None:
    result = query_l1(seeded_logs, days=7)
    assert len(result["entries"]) == 3


def test_query_l1_no_match(seeded_logs: Path) -> None:
    result = query_l1(seeded_logs, days=7, keyword="不存在的关键词")
    assert result["entries"] == []


# ---------- all-agents ----------


def test_query_all_agents_summary(seeded_logs: Path) -> None:
    result = query_all_agents(seeded_logs, days=7)
    assert set(result["per_agent"].keys()) >= {"pm", "qa"}
    pm_stats = result["per_agent"]["pm"]
    assert pm_stats["task_count"] == 8
    # bottleneck 应该是 PM（平均质量低）
    assert "bottleneck" in result
    assert result["bottleneck"] == "pm"


# ---------- CLI 入口 ----------


def test_log_query_cli_json_output(seeded_logs: Path) -> None:
    """通过 subprocess 运行 CLI 拿到 JSON."""
    proc = subprocess.run(
        [sys.executable, "-m", "xiaopaw_team.tools.log_query",
         "stats", "--agent-id", "pm", "--days", "7",
         "--logs-root", str(seeded_logs)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(proc.stdout)
    assert data["task_count"] == 8
    assert data["agent_id"] == "pm"
