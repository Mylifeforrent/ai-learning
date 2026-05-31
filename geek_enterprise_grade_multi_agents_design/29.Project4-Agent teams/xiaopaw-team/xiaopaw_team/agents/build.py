"""
build.py — 29 课多角色 Agent 工厂

对齐 DESIGN.md v1.5 §30.3：`build_role_tools(role, cfg, sender=None) -> list[BaseTool]`
和 `build_team_agent_fn(role, ...) -> AgentFn`。

设计决策（MVP 版）：
- MemoryAwareCrew 直接用 22 课原版（_main_crew_base），workspace_dir 按 role 分
- SkillLoaderTool 换成 role-scoped 版本（tools/skill_loader.py）
- 最小 `build_role_tools` 只构造 SkillLoader + IntermediateTool（团队协作工具后续迭代进 agent tools）
- Manager 并发保护（asyncio.Lock）在 runner 层处理
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.hooks import LLMCallHookContext, before_llm_call
from crewai.project import CrewBase, agent, crew, task
import yaml

from xiaopaw_team.agents.models import MainTaskOutput
from xiaopaw_team.llm.aliyun_llm import AliyunLLM
from xiaopaw_team.memory.bootstrap import build_bootstrap_prompt
from xiaopaw_team.memory.context_mgmt import (
    append_session_raw,
    load_session_ctx,
    maybe_compress,
    prune_tool_results,
    save_session_ctx,
)
from xiaopaw_team.memory.indexer import async_index_turn
from xiaopaw_team.models import SenderProtocol
from xiaopaw_team.runner import AgentFn
from xiaopaw_team.session.models import MessageEntry
from xiaopaw_team.tools.intermediate_tool import IntermediateTool
from xiaopaw_team.tools.skill_loader import RoleScopedSkillLoaderTool
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

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / "config"
_DEFAULT_MAX_HISTORY_TURNS = 20


def build_role_tools(
    *,
    role: str,
    workspace_root: Path,
    cron_tasks_path: Path,
    sender: SenderProtocol | None = None,
) -> list:
    """构造单个角色的 Python Tools 集合（不含 SkillLoader / Intermediate）.

    Manager 额外拥有 CreateProject / AppendEvent / SendToHuman.
    其他角色仅拥有共享 5 件：SendMail / ReadInbox / MarkDone / ReadShared / WriteShared.
    """
    common: list = [
        SendMailTool(
            workspace_root=workspace_root,
            cron_tasks_path=cron_tasks_path,
            from_role=role,
        ),
        ReadInboxTool(workspace_root=workspace_root, role=role),
        MarkDoneTool(workspace_root=workspace_root, role=role),
        ReadSharedTool(workspace_root=workspace_root, role=role),
        WriteSharedTool(workspace_root=workspace_root, role=role),
    ]
    if role == "manager":
        return common + [
            CreateProjectTool(workspace_root=workspace_root),
            AppendEventTool(workspace_root=workspace_root),
            SendToHumanTool(workspace_root=workspace_root, sender=sender),
        ]
    return common


def _load_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _format_history(history: list[MessageEntry], max_turns: int = _DEFAULT_MAX_HISTORY_TURNS) -> str:
    if not history:
        return "（无历史记录）"
    recent = history[-max_turns:] if len(history) > max_turns else history
    role_map = {"user": "用户", "assistant": "助手"}
    return "\n".join(f"{role_map.get(e.role, e.role)}: {e.content}" for e in recent)


@CrewBase
class TeamMemoryAwareCrew:
    """29 课 role-scoped MemoryAwareCrew。

    每 kickoff 一个新实例（防状态污染）。
    """

    def __init__(
        self,
        *,
        role: str,
        workspace_root: Path,
        session_id: str,
        user_message: str,
        routing_key: str,
        ctx_dir: Path,
        db_dsn: str,
        history_all: list,
        sandbox_url: str,
        cron_tasks_path: Path | None = None,
        sender: SenderProtocol | None = None,
        verbose: bool = False,
        step_callback: Any | None = None,
        prune_keep_turns: int = 10,
    ) -> None:
        self.role = role
        self.session_id = session_id
        self.user_message = user_message
        self.routing_key = routing_key
        self._workspace_root = workspace_root
        self._role_workspace = workspace_root / role
        logger.debug(
            "TeamMemoryAwareCrew init: role=%r routing_key=%r session_id=%r",
            role, routing_key, session_id,
        )
        self._skills_dir = self._role_workspace / "skills"
        self._sandbox_skills_mount = f"/workspace/{role}/skills"
        self._ctx_dir = ctx_dir
        self._db_dsn = db_dsn
        self._step_callback = step_callback
        self._verbose = verbose
        self._history_all = history_all
        self._sandbox_url = sandbox_url
        self._prune_keep_turns = prune_keep_turns
        self._cron_tasks_path = cron_tasks_path
        self._sender = sender

        self._session_loaded = False
        self._last_msgs: list[dict] = []
        self._history_len = 0
        self._turn_start_ts = int(time.time() * 1000)

    @agent
    def orchestrator(self) -> Agent:
        cfg = dict(_load_yaml(_CONFIG_DIR / "agents.yaml")["orchestrator"])

        # Bootstrap：读 workspace/{role}/{soul,agent,memory,user}.md + shared/team_protocol.md
        shared_protocol = self._workspace_root / "shared" / "team_protocol.md"
        bootstrap = build_bootstrap_prompt(self._role_workspace)
        # v1.3-P1-15 team_protocol 注入
        if shared_protocol.exists():
            protocol_text = shared_protocol.read_text(encoding="utf-8")
            bootstrap = f"{bootstrap}\n\n<team_protocol>\n{protocol_text}\n</team_protocol>"
        cfg["backstory"] = bootstrap

        loader_kwargs = {
            "role": self.role,
            "skills_dir": self._skills_dir,
            "sandbox_skills_mount": self._sandbox_skills_mount,
            "session_id": self.session_id,
            "routing_key": self.routing_key,
            "history_all": self._history_all,
        }
        if self._sandbox_url:
            loader_kwargs["sandbox_url"] = self._sandbox_url

        tools = [
            RoleScopedSkillLoaderTool(**loader_kwargs),
            IntermediateTool(),
        ]
        # 注入团队协作 Python Tools（SendMail / ReadInbox / ... / Manager 独占 3 件）
        if self._cron_tasks_path is not None:
            tools.extend(build_role_tools(
                role=self.role,
                workspace_root=self._workspace_root,
                cron_tasks_path=self._cron_tasks_path,
                sender=self._sender,
            ))
        return Agent(
            **cfg,
            llm=AliyunLLM(model="qwen3.6-max-preview", region="cn", temperature=0.3),
            tools=tools,
            verbose=self._verbose,
        )

    @task
    def main_task(self) -> Task:
        task_cfg = dict(_load_yaml(_CONFIG_DIR / "tasks.yaml")["main_task"])
        return Task(
            **task_cfg,
            agent=self.orchestrator(),
            output_pydantic=MainTaskOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self._verbose,
            step_callback=self._step_callback,
        )

    @before_llm_call
    def before_llm_hook(self, context: LLMCallHookContext) -> bool | None:
        if not self._session_loaded:
            self._restore_session(context)
            self._session_loaded = True
        self._last_msgs = context.messages
        prune_tool_results(context.messages, keep_turns=self._prune_keep_turns)
        maybe_compress(context.messages, context)
        return None

    def _restore_session(self, context: LLMCallHookContext) -> None:
        history = load_session_ctx(self.session_id, ctx_dir=self._ctx_dir)
        if not history:
            self._history_len = 0
            return
        current_system = [m for m in context.messages if m.get("role") == "system"]
        current_user = next(
            (m for m in reversed(context.messages) if m.get("role") == "user"), {}
        )
        hist_conv = [
            m for m in history
            if m.get("role") != "system" or "<context_summary>" in str(m.get("content", ""))
        ]
        self._history_len = len(current_system) + len(hist_conv)
        context.messages.clear()
        context.messages.extend(current_system)
        context.messages.extend(hist_conv)
        if current_user:
            context.messages.append(current_user)

    async def run_and_index(self) -> str:
        result = await self.crew().akickoff(
            inputs={
                "user_message": self.user_message,
                "history": _format_history(self._history_all),
                "routing_key": self.routing_key or "",
            }
        )

        if self._last_msgs:
            new_msgs = list(self._last_msgs)[self._history_len:]
            append_session_raw(self.session_id, new_msgs, ctx_dir=self._ctx_dir)
            save_session_ctx(self.session_id, list(self._last_msgs), ctx_dir=self._ctx_dir)

        reply = result.raw or str(result)
        if result.pydantic and hasattr(result.pydantic, "reply"):
            reply = str(result.pydantic.reply)

        if self._db_dsn:
            _task = asyncio.create_task(  # noqa: RUF006
                async_index_turn(
                    session_id=self.session_id,
                    routing_key=self.routing_key,
                    user_message=self.user_message,
                    assistant_reply=reply,
                    turn_ts=self._turn_start_ts,
                    db_dsn=self._db_dsn,
                )
            )
        return reply


def build_team_agent_fn(
    *,
    role: str,
    workspace_root: Path,
    ctx_dir: Path,
    sender: SenderProtocol | None = None,
    db_dsn: str = "",
    sandbox_url: str = "",
    cron_tasks_path: Path | None = None,
) -> AgentFn:
    """为指定角色构造 agent_fn（团队版）.

    Args:
        role: manager / pm / rd / qa
        workspace_root: workspace/ 根目录（内部会按 role 找子目录）
        ctx_dir: ctx.json / raw.jsonl 存储根
        sender: 飞书 Sender（仅 Manager 需要注入，其他角色传 None 保持单一接口原则）
        cron_tasks_path: cron tasks.json 路径；提供后 Agent 获得完整 team tools
    """
    ctx_dir.mkdir(parents=True, exist_ok=True)

    async def agent_fn(
        user_message: str,
        history: list[MessageEntry],
        session_id: str,
        routing_key: str = "",
        root_id: str = "",
        verbose: bool = False,
    ) -> str:
        crew_instance = TeamMemoryAwareCrew(
            role=role,
            workspace_root=workspace_root,
            session_id=session_id,
            user_message=user_message,
            routing_key=routing_key,
            ctx_dir=ctx_dir,
            db_dsn=db_dsn,
            history_all=history,
            sandbox_url=sandbox_url,
            cron_tasks_path=cron_tasks_path,
            sender=sender if role == "manager" else None,
            verbose=verbose,
        )
        return await crew_instance.run_and_index()

    return agent_fn


# ── 全局 asyncio.Lock：所有 4 角色 crew 串行化 ─────────────────────────
#
# **为什么不是只锁 Manager**：
# CrewAI 的 @before_llm_call hook 通过全局 event bus 注册，
# 4 个 TeamMemoryAwareCrew 实例并发跑时所有 hook 都会 fire on every LLM call，
# 导致 session_id / role_workspace 串台（PR A 的 system prompt 里出现 PR B 的 soul.md）。
# 简单的正确做法：全 team 串行。
#
# 代价：失去"PM 和 QA 并行"这种微并行（但 Manager 本来就是单实例串行；
# 且本项目 demo 项目体量小，串行不构成吞吐瓶颈）。

def wrap_with_lock(agent_fn: AgentFn, lock: asyncio.Lock | None = None) -> AgentFn:
    """把 agent_fn 套入 lock。如果 lock=None（保持向后兼容），为该 agent 单独新建。

    💡 修复 C2：锁不再模块级缓存（之前绑定到首个 event loop，多次 asyncio.run 会失败）.
    """
    if lock is None:
        lock = asyncio.Lock()

    async def wrapped(user_message, history, session_id,
                      routing_key="", root_id="", verbose=False) -> str:
        async with lock:
            return await agent_fn(user_message, history, session_id,
                                  routing_key, root_id, verbose)

    return wrapped


__all__ = [
    "TeamMemoryAwareCrew",
    "build_team_agent_fn",
    "wrap_with_lock",
    "build_role_tools",
]
