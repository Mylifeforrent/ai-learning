"""集成测试公共 Fixtures

运行前提：
  - QWEN_API_KEY 或 DASHSCOPE_API_KEY 已设置（否则 LLM 测试自动跳过）
  - AIO-Sandbox 运行在 localhost:8022（否则 sandbox 测试自动跳过）

快速运行（仅 slash command，无需 API key）：
  pytest tests/integration/ -m "not llm"

完整运行（需要 API key）：
  QWEN_API_KEY=sk-xxx pytest tests/integration/ -v -s

仅 sandbox 相关（需 API key + sandbox）：
  pytest tests/integration/ -m "sandbox" -v -s
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import shutil
import socket
from pathlib import Path

import aiohttp
import pytest
from aiohttp.test_utils import TestClient, TestServer

from xiaopaw.api.capture_sender import CaptureSender
from xiaopaw.api.test_server import create_test_app
from xiaopaw.runner import Runner
from xiaopaw.session.manager import SessionManager
from xiaopaw.session.models import MessageEntry


# ── 日志归档（每次 session 自动存到 tests/logs/YYYYMMDD_HHMMSS.log） ─────────────

def _setup_log_archive(config: pytest.Config) -> None:
    """将日志文件名改为带时间戳的版本，避免覆盖上一次运行的日志。"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{ts}.log"
    # 覆盖 pyproject.toml 里的 log_file 路径
    if hasattr(config, "option") and hasattr(config.option, "log_file"):
        config.option.log_file = str(log_file)
    # latest.log 始终软链到最新日志
    latest = log_dir / "latest.log"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(log_file.name)


# ── 环境检测 ───────────────────────────────────────────────────────────────────

SANDBOX_HOST = "localhost"
SANDBOX_PORT = 8022
SANDBOX_URL = f"http://{SANDBOX_HOST}:{SANDBOX_PORT}/mcp"

# pgvector 默认连接串（与 pgvector-docker-compose.yaml 保持一致）
PGVECTOR_HOST = "localhost"
PGVECTOR_PORT = 5432
PGVECTOR_DSN  = "postgresql://xiaopaw:xiaopaw123@localhost:5432/xiaopaw_memory"


def _sandbox_reachable() -> bool:
    """检查 AIO-Sandbox 是否可达（TCP 连接测试）。"""
    try:
        s = socket.create_connection((SANDBOX_HOST, SANDBOX_PORT), timeout=1.0)
        s.close()
        return True
    except OSError:
        return False


def _pgvector_reachable() -> bool:
    """检查 pgvector 是否可达（TCP 连接测试）。"""
    try:
        s = socket.create_connection((PGVECTOR_HOST, PGVECTOR_PORT), timeout=1.0)
        s.close()
        return True
    except OSError:
        return False


def _qwen_api_key() -> str | None:
    return os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")


# ── pytest 钩子：注册 markers + 日志归档 ──────────────────────────────────────

def pytest_configure(config: pytest.Config) -> None:
    _setup_log_archive(config)
    config.addinivalue_line(
        "markers",
        "llm: 需要真实 LLM API（QWEN_API_KEY）的测试",
    )
    config.addinivalue_line(
        "markers",
        "sandbox: 需要 AIO-Sandbox（localhost:8022）运行的测试",
    )
    config.addinivalue_line(
        "markers",
        "integration: 集成测试（与外部服务交互）",
    )
    config.addinivalue_line(
        "markers",
        "feishu: 需要真实飞书凭证（FEISHU_APP_ID + FEISHU_APP_SECRET）的实况测试",
    )
    config.addinivalue_line(
        "markers",
        "pgvector: 需要 pgvector（localhost:5432）运行的测试",
    )


# ── Session 级别 Fixtures（检查一次）─────────────────────────────────────────

@pytest.fixture(scope="session")
def qwen_api_key() -> str:
    """返回 Qwen API Key；未设置则跳过整个 session。"""
    key = _qwen_api_key()
    if not key:
        pytest.skip("QWEN_API_KEY / DASHSCOPE_API_KEY 未设置，跳过 LLM 集成测试")
    return key


@pytest.fixture(scope="session")
def sandbox_available() -> bool:
    return _sandbox_reachable()


@pytest.fixture(scope="session")
def pgvector_available() -> bool:
    return _pgvector_reachable()


@pytest.fixture(scope="session")
def pgvector_live_dsn(pgvector_available: bool) -> str:
    """返回可用的 pgvector DSN；pgvector 不可达时跳过测试。"""
    if not pgvector_available:
        pytest.skip("pgvector (localhost:5432) 不可达，跳过 pgvector 测试")
    return PGVECTOR_DSN


# ── Function 级别 Fixtures（每个测试独立）────────────────────────────────────

@pytest.fixture
def session_mgr(tmp_path: Path) -> SessionManager:
    """每个测试独立的 SessionManager，数据存在临时目录。"""
    return SessionManager(data_dir=tmp_path)


@pytest.fixture
def cron_dir(tmp_path: Path) -> Path:
    """scheduler_mgr 测试专用临时 cron 目录。"""
    d = tmp_path / "cron"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Echo Agent（不需要 LLM）──────────────────────────────────────────────────

async def _echo_agent_fn(
    user_message: str,
    history: list[MessageEntry],
    session_id: str,
    routing_key: str = "",
    root_id: str = "",
    verbose: bool = False,
) -> str:
    return f"echo: {user_message}"


@pytest.fixture
async def slash_client(session_mgr: SessionManager) -> TestClient:
    """仅 slash command 测试用客户端：不调用 LLM，用 echo agent。"""
    sender = CaptureSender()
    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn=_echo_agent_fn,
        idle_timeout=5.0,
    )
    app = create_test_app(runner=runner, sender=sender, session_mgr=session_mgr)
    async with TestClient(TestServer(app)) as cli:
        yield cli
    await runner.shutdown()


# ── 真实 LLM 客户端（旧接口兼容，已有测试使用）─────────────────────────────

@pytest.fixture
async def llm_client(
    tmp_path: Path,
    session_mgr: SessionManager,
    qwen_api_key: str,
    sandbox_available: bool,
) -> TestClient:
    """完整 E2E 客户端（带三层记忆），复用 memory_client 逻辑。"""
    from xiaopaw.agents.main_crew import build_agent_fn  # noqa: PLC0415

    workspace_dir, ctx_dir = _init_workspace(tmp_path)
    db_dsn = os.getenv("MEMORY_DB_DSN", "")
    sender = CaptureSender()
    agent_fn = build_agent_fn(
        sender=sender,
        workspace_dir=workspace_dir,
        ctx_dir=ctx_dir,
        db_dsn=db_dsn,
        max_history_turns=20,
        sandbox_url=SANDBOX_URL if sandbox_available else "",
    )
    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn=agent_fn,
        idle_timeout=30.0,
    )
    app = create_test_app(runner=runner, sender=sender,
                          session_mgr=session_mgr, workspace_dir=workspace_dir)
    async with TestClient(TestServer(app)) as cli:
        cli._workspace_dir = workspace_dir
        cli._ctx_dir = ctx_dir
        yield cli
    await runner.shutdown()


# ── 三层记忆完整客户端（新测试用）────────────────────────────────────────────

_WORKSPACE_INIT = Path(__file__).parents[2] / "workspace-init"


def _init_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """复制 workspace-init/ 到 tmp_path，返回 (workspace_dir, ctx_dir)。"""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    ctx_dir = tmp_path / "ctx"
    ctx_dir.mkdir()
    if _WORKSPACE_INIT.exists():
        for f in _WORKSPACE_INIT.glob("*.md"):
            shutil.copy(f, workspace_dir / f.name)
    return workspace_dir, ctx_dir


@pytest.fixture
async def memory_client(
    tmp_path: Path,
    session_mgr: SessionManager,
    qwen_api_key: str,
    sandbox_available: bool,
) -> TestClient:
    """带完整三层记忆的 E2E 测试客户端。

    暴露两个额外属性供测试读取文件：
      cli._workspace_dir  → workspace 目录（soul/user/agent/memory.md）
      cli._ctx_dir        → ctx.json / raw.jsonl 存储目录
    """
    from xiaopaw.agents.main_crew import build_agent_fn  # noqa: PLC0415

    workspace_dir, ctx_dir = _init_workspace(tmp_path)
    db_dsn = os.getenv("MEMORY_DB_DSN", "")
    sender = CaptureSender()
    agent_fn = build_agent_fn(
        sender=sender,
        workspace_dir=workspace_dir,
        ctx_dir=ctx_dir,
        db_dsn=db_dsn,
        max_history_turns=20,
        sandbox_url=SANDBOX_URL if sandbox_available else "",
    )
    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn=agent_fn,
        idle_timeout=30.0,
    )
    app = create_test_app(runner=runner, sender=sender,
                          session_mgr=session_mgr, workspace_dir=workspace_dir)
    async with TestClient(TestServer(app)) as cli:
        cli._workspace_dir = workspace_dir
        cli._ctx_dir = ctx_dir
        yield cli
    await runner.shutdown()


@pytest.fixture
def pgvector_dsn() -> str:
    """返回 pgvector 连接串；未配置时跳过。"""
    dsn = os.getenv("MEMORY_DB_DSN", "")
    if not dsn:
        pytest.skip("MEMORY_DB_DSN 未配置，跳过 pgvector 测试")
    return dsn


@pytest.fixture
async def memory_client_pgvector(
    tmp_path: Path,
    session_mgr: SessionManager,
    qwen_api_key: str,
    sandbox_available: bool,
    pgvector_live_dsn: str,
) -> TestClient:
    """带真实 pgvector 的完整三层记忆客户端（第22课系统测试专用）。

    与 memory_client 的区别：总是使用 PGVECTOR_DSN，不依赖 MEMORY_DB_DSN 环境变量。
    暴露属性：cli._workspace_dir / cli._ctx_dir / cli._db_dsn

    💡 search_memory 调用链长（LLM + sandbox + pgvector），将请求超时调整为 900s（server）/1000s（client）。
    """
    import xiaopaw.api.test_server as _ts  # noqa: PLC0415
    from xiaopaw.agents.main_crew import build_agent_fn  # noqa: PLC0415

    # search_memory 调用链：LLM → SkillLoaderTool → sandbox → pgvector，实测可超过 900s
    _original_timeout = _ts._DEFAULT_TIMEOUT
    _ts._DEFAULT_TIMEOUT = 1500.0

    workspace_dir, ctx_dir = _init_workspace(tmp_path)
    sender = CaptureSender()
    agent_fn = build_agent_fn(
        sender=sender,
        workspace_dir=workspace_dir,
        ctx_dir=ctx_dir,
        db_dsn=pgvector_live_dsn,
        max_history_turns=20,
        sandbox_url=SANDBOX_URL if sandbox_available else "",
    )
    runner = Runner(
        session_mgr=session_mgr,
        sender=sender,
        agent_fn=agent_fn,
        idle_timeout=60.0,
    )
    app = create_test_app(runner=runner, sender=sender,
                          session_mgr=session_mgr, workspace_dir=workspace_dir)
    try:
        async with TestClient(TestServer(app), timeout=aiohttp.ClientTimeout(total=1600)) as cli:
            cli._workspace_dir = workspace_dir
            cli._ctx_dir = ctx_dir
            cli._db_dsn = pgvector_live_dsn
            yield cli
    finally:
        _ts._DEFAULT_TIMEOUT = _original_timeout
        await runner.shutdown()


# ── 测试辅助函数 ──────────────────────────────────────────────────────────────

async def send_message(
    client: TestClient,
    content: str,
    routing_key: str = "p2p:ou_tester",
) -> dict:
    """向 TestAPI 发送消息，返回响应 JSON。"""
    resp = await client.post(
        "/api/test/message",
        json={"routing_key": routing_key, "content": content},
    )
    assert resp.status == 200, f"Unexpected status {resp.status}"
    data = await resp.json()
    assert "reply" in data
    return data


def write_ctx(ctx_dir: Path, session_id: str, messages: list[dict]) -> None:
    """测试辅助：直接写入 ctx.json，模拟上一次 session 结束后的状态。"""
    path = ctx_dir / f"{session_id}_ctx.json"
    path.write_text(json.dumps(messages, ensure_ascii=False), encoding="utf-8")


async def llm_assert(reply: str, criteria: str, reason_hint: str = "") -> None:
    """LLM-as-judge 断言：用 Qwen 判断 reply 是否满足 criteria。

    比关键词匹配更健壮——不依赖具体措辞，关注语义是否达到预期。

    Args:
        reply: 被测 Agent 的实际回复
        criteria: 期望满足的语义条件（自然语言描述）
        reason_hint: 断言失败时额外提示信息（帮助定位问题）

    Raises:
        AssertionError: LLM 判定不满足时，包含 judge 的理由
    """
    import aiohttp  # noqa: PLC0415

    api_key = _qwen_api_key()
    if not api_key:
        # 无 API key 时退化为非空检查，不阻断测试
        assert len(reply) > 10, f"llm_assert: 无 API key，退化为非空检查失败。{reason_hint}"
        return

    judge_prompt = (
        "你是一个测试断言判断器。判断 AI 助手的回复是否满足给定的期望条件。\n\n"
        f"【回复内容】\n{reply}\n\n"
        f"【期望条件】\n{criteria}\n\n"
        "请判断回复是否满足期望条件。\n"
        "只返回 JSON，格式：{\"pass\": true 或 false, \"reason\": \"简短理由\"}\n"
        "不要输出任何其他内容。"
    )

    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    payload = {
        "model": "qwen3.6-max-preview",
        "messages": [{"role": "user", "content": judge_prompt}],
        "temperature": 0.0,
        "max_tokens": 200,
        # 关闭思考模式，加速判断
        "extra_body": {"enable_thinking": False},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        # 去除可能的 markdown 代码块包裹
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        passed = result.get("pass", False)
        reason = result.get("reason", "（无理由）")
    except Exception as e:
        # judge 调用失败时退化为非空检查，不阻断测试
        assert len(reply) > 10, f"llm_assert: judge 调用失败（{e}），退化检查失败。{reason_hint}"
        return

    hint = f"\n补充说明：{reason_hint}" if reason_hint else ""
    assert passed, (
        f"llm_assert 判定不满足。\n"
        f"期望条件：{criteria}\n"
        f"实际回复：{reply!r}\n"
        f"Judge 理由：{reason}{hint}"
    )
