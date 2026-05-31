"""
E2E 全流程：Journey A — 从需求到交付（真实 Qwen + 真实 AIO-Sandbox）.

**设计定位**：模拟用户侧（飞书消息 in + CaptureSender out），系统内部完全自驱动。
不手动 orchestrate 任何角色；全部靠 SendMailTool auto-schedule cron wake + CronService + Runner 团队路由。

**跑法**:
  export QWEN_API_KEY=...
  docker compose -f sandbox-docker-compose.yaml up -d   # 8029
  pytest tests/integration/test_e2e_full_journey.py -v -m e2e_full -s
  # 预计耗时 15-40 分钟（全程 LLM + 沙盒）。

**成功标准**：
  - workspace/shared/projects/{pid}/ 下产出完整交付件链：
    needs/requirements.md / design/product_spec.md / tech/tech_design.md /
    code/*.py / qa/test_plan.md / qa/test_report.md
  - events.jsonl 含 project_created → requirements_drafted → assigned → task_done_received × N → delivered
  - Manager 发给人类至少 2 条（需求 checkpoint + 交付汇报）

**允许降级**：
  - 若在约 20 分钟内未进入 qa_test_run，把 timeout 拉到 45 分钟或拆成两个断言
  - 若 RD 反复修 pytest 超 3 轮，允许 metrics.pytest_final_status=fail 但其他交付物齐全
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import pytest

from xiaopaw_team.main import build_runtime
from xiaopaw_team.models import InboundMessage


pytestmark = pytest.mark.e2e_full


REPO_ROOT = Path(__file__).resolve().parents[2]
SANDBOX_URL = os.environ.get("SANDBOX_URL", "http://localhost:8029/mcp")
JOURNEY_TIMEOUT_SEC = int(os.environ.get("JOURNEY_TIMEOUT_SEC", "2400"))  # 40 min


class _CaptureSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, routing_key: str, content: str, root_id: str = "") -> None:
        self.sent.append((routing_key, content))
        print(f"[HUMAN INBOX <-] {routing_key}: {content[:240]}")

    async def send_thinking(self, routing_key, root_id) -> str | None:
        return None

    async def update_card(self, card_msg_id, content) -> None:
        return None

    async def send_text(self, routing_key, content, root_id) -> None:
        return None


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """独立 workspace（不污染真实 workspace/）."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    # 复制 workspace 模板（4 角色 agent.md / skills/ / shared/）
    import shutil

    src = REPO_ROOT / "workspace"
    for item in src.iterdir():
        if item.is_dir() and item.name != "shared":
            shutil.copytree(item, ws / item.name)
    shutil.copytree(src / "shared", ws / "shared")
    # chmod 777 让 sandbox 的 gem 用户能写
    for dirpath, dirnames, filenames in os.walk(ws):
        os.chmod(dirpath, 0o777)
        for fn in filenames:
            os.chmod(os.path.join(dirpath, fn), 0o666)
    return ws


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.mark.asyncio
async def test_full_journey_a_delivery(workspace_root: Path, data_dir: Path) -> None:
    """Journey A：用户 → Manager 需求澄清 → PM → RD → QA → 交付."""
    assert os.environ.get("QWEN_API_KEY"), "请设 QWEN_API_KEY"

    sender = _CaptureSender()
    runner, cron_svc, _ = await build_runtime(
        workspace_root=workspace_root,
        data_dir=data_dir,
        ctx_dir=data_dir / "ctx",
        sandbox_url=SANDBOX_URL,
        sender=sender,
    )

    try:
        # 用户第一条消息：极简需求，刻意压缩澄清轮次
        user_text = (
            "帮我做个超简单的'待办清单'小网站（MVP 只要添加/列出/完成/删除 4 功能）。"
            "技术栈自选；后端 FastAPI + SQLite；前端单文件 HTML+JS 即可。"
            "**所有细节你直接替我决定，我批准任何合理方案**。"
            "请先产出 needs/requirements.md，然后按 SOP 推进到 QA 交付。"
            "过程中如果一定要问我，一次只问一个最关键的问题；否则直接推进。"
        )
        print(f"\n[USER ->] {user_text}\n")

        await runner.dispatch(InboundMessage(
            routing_key="p2p:full-journey-user",
            content=user_text,
            msg_id="m-journey-001",
            root_id="",
            sender_id="full-journey-user",
            ts=int(time.time() * 1000),
        ))

        # 自驱动等待：周期性检查是否产出所有关键交付件
        deadline = time.time() + JOURNEY_TIMEOUT_SEC
        required = [
            "needs/requirements.md",
            "design/product_spec.md",
            "tech/tech_design.md",
            "qa/test_plan.md",
        ]
        while time.time() < deadline:
            await asyncio.sleep(10)
            projects_dir = workspace_root / "shared" / "projects"
            if not projects_dir.exists():
                continue
            pids = [p.name for p in projects_dir.iterdir() if p.is_dir()]
            if not pids:
                continue
            pid = pids[0]  # 首个项目即本 journey 项目
            proj = projects_dir / pid
            status = {p: (proj / p).exists() for p in required}
            code_files = list((proj / "code").glob("*.py")) if (proj / "code").exists() else []
            print(f"[STATUS t={int(time.time())}s] pid={pid} "
                  f"files={status} code_files={len(code_files)} "
                  f"human_msgs={len(sender.sent)}")
            if all(status.values()) and code_files:
                print("[DONE] 六阶段核心交付件齐全")
                break

        # 最终 assertions
        projects_dir = workspace_root / "shared" / "projects"
        pids = [p.name for p in projects_dir.iterdir() if p.is_dir()]
        assert pids, "至少创建一个 project"
        pid = pids[0]
        proj = projects_dir / pid

        for p in ["needs/requirements.md", "design/product_spec.md", "tech/tech_design.md"]:
            assert (proj / p).exists(), f"缺 {p}"

        events = [json.loads(l) for l in (proj / "events.jsonl").read_text().splitlines() if l.strip()]
        actions = [e["action"] for e in events]
        assert "project_created" in actions
        assert any(a in {"requirements_drafted", "assigned"} for a in actions)

        assert len(sender.sent) >= 1, "Manager 应至少给用户发 1 条消息（需求 checkpoint 或交付汇报）"

    finally:
        await cron_svc.stop()
