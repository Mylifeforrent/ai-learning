"""
E2E Smoke — 真实 Qwen + 真实 AIO-Sandbox + 团队装配

目标：Journey A smoke（极简版）
  - 用户飞书发 "帮我做个待办清单小网站"
  - Manager kickoff
  - Manager 能加载 sop_feature_dev + mailbox_ops skill
  - Manager 调 bash（通过 mailbox_cli.py）发 task_assign 邮件给 PM
  - 验证 workspace/shared/projects/{pid}/mailboxes/pm.json 里有新邮件

前置：
  - AIO-Sandbox 容器跑在 http://localhost:8022/mcp
  - 环境变量 QWEN_API_KEY 已设
  - workspace/ 模板已放置
  - data/ctx 目录（运行时创建）

跑法：`pytest tests/integration/test_e2e_smoke.py -v -m e2e -s`
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import pytest

from xiaopaw_team.agents.build import build_team_agent_fn, wrap_with_lock
from xiaopaw_team.models import InboundMessage
from xiaopaw_team.runner import Runner
from xiaopaw_team.session.manager import SessionManager
from xiaopaw_team.tools.workspace import init_project_tree


pytestmark = pytest.mark.e2e


class _CaptureSender:
    """收集 Manager 回复到用户的消息，不实际发飞书."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, routing_key: str, content: str, root_id: str = "") -> None:
        self.sent.append((routing_key, content))

    async def send_thinking(self, routing_key, root_id) -> str | None: return None
    async def update_card(self, card_msg_id, content) -> None: return None
    async def send_text(self, routing_key, content, root_id) -> None: return None


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = REPO_ROOT / "workspace"
SANDBOX_URL = os.environ.get("SANDBOX_URL", "http://localhost:8029/mcp")


@pytest.fixture
def project_id(tmp_path_factory) -> str:
    """为 smoke 创建一个独立 project，避免污染 workspace 根."""
    import os
    pid = f"proj-smoke-{int(time.time())}"
    # 注意：这里把 project 建到真实 workspace（因为沙盒挂载点是 workspace/）
    init_project_tree(WORKSPACE_ROOT, project_id=pid)
    # 沙盒内 bash 以 gem 用户运行，宿主机 root 创建的目录 gem 写不进去 → 放宽权限
    proj_dir = WORKSPACE_ROOT / "shared" / "projects" / pid
    for dirpath, dirnames, filenames in os.walk(proj_dir):
        os.chmod(dirpath, 0o777)
        for fn in filenames:
            os.chmod(os.path.join(dirpath, fn), 0o666)
    yield pid
    # 不清理——留痕供 debug


@pytest.fixture
def ctx_dir(tmp_path_factory) -> Path:
    """每个 smoke run 独立的 ctx 目录."""
    d = tmp_path_factory.mktemp("ctx")
    return d


@pytest.mark.asyncio
async def test_smoke_manager_dispatches_task_to_pm(
    project_id: str,
    ctx_dir: Path,
) -> None:
    """
    Manager 收到飞书消息 → 加载 sop_feature_dev + mailbox_ops →
    在沙盒里跑 bash 发邮件到 pm.json。
    """
    assert os.environ.get("QWEN_API_KEY"), "请设 QWEN_API_KEY 环境变量"

    sender = _CaptureSender()
    session_mgr = SessionManager(ctx_dir / "sessions")

    # 装配 4 agent_fn（RD/QA 我们暂时不触发，但装配在 runner map 里备用）
    agent_fns = {
        role: build_team_agent_fn(
            role=role,
            workspace_root=WORKSPACE_ROOT,
            ctx_dir=ctx_dir,
            sender=sender if role == "manager" else None,
            sandbox_url=SANDBOX_URL,
        )
        for role in ("manager", "pm", "rd", "qa")
    }
    agent_fns["manager"] = wrap_with_lock(agent_fns["manager"])

    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn_map=agent_fns,
        idle_timeout=60.0,
    )

    # 构造用户飞书消息：需求已澄清（smoke 不走澄清轮），要求直接派 PM
    user_text = (
        f"帮我做个待办清单小网站。"
        f"【需求已完全明确，不需要再澄清任何细节，请直接进入产品设计阶段】\n"
        f"- 核心功能：添加任务、标记完成、删除任务（硬删除）、列出所有任务\n"
        f"- 技术栈：FastAPI + SQLite + 原生 HTML+JS\n"
        f"- 不做：登录、分享、多端同步、筛选\n\n"
        f"**执行指令（必须严格按这个顺序）**：\n"
        f"1. 加载 mailbox_ops skill\n"
        f"2. 调用 send 子命令给 PM 发 task_assign 邮件（from=manager, to=pm, type=task_assign）：\n"
        f"   - project_id 参数填：{project_id}\n"
        f"   - subject：'产品设计：待办清单小网站'\n"
        f"   - content：把上面的需求总结给 PM\n"
        f"3. 确认返回 errcode=0 后，给我回复：'已派给 PM 产品设计，完成后推给你确认。'\n\n"
        f"不要再问我任何问题，不要做需求澄清，直接执行。"
    )

    await runner.dispatch(InboundMessage(
        routing_key="p2p:ou_xiaohan",
        content=user_text,
        msg_id="m-smoke-001",
        root_id="",
        sender_id="ou_xiaohan",
        ts=int(time.time() * 1000),
    ))

    # 等 Manager 跑完（真实 LLM 需要 30s-2min）
    for _ in range(240):  # 最多 4 分钟
        await asyncio.sleep(1)
        pm_inbox = WORKSPACE_ROOT / "shared" / "projects" / project_id / "mailboxes" / "pm.json"
        msgs = json.loads(pm_inbox.read_text() or "[]")
        if msgs:
            break

    # 验收
    pm_inbox = WORKSPACE_ROOT / "shared" / "projects" / project_id / "mailboxes" / "pm.json"
    assert pm_inbox.exists(), f"PM inbox 不存在：{pm_inbox}"
    msgs = json.loads(pm_inbox.read_text() or "[]")
    print(f"\n=== PM 收到 {len(msgs)} 封邮件 ===")
    for m in msgs:
        print(json.dumps(m, ensure_ascii=False, indent=2))
    print(f"\n=== Manager 回给用户 {len(sender.sent)} 条消息 ===")
    for rk, content in sender.sent:
        print(f"--> {rk}: {content[:300]}")

    assert len(msgs) >= 1, "Manager 应至少给 PM 发 1 封 task_assign"
    assert msgs[0]["type"] == "task_assign"
    assert msgs[0]["from"] == "manager"
    assert msgs[0]["to"] == "pm"
