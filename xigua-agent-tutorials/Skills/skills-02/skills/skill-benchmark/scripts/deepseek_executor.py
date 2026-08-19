#!/usr/bin/env python3
"""
DeepSeek Executor Adapter for skill-benchmark
============================================
替代 claude_cli_executor.py，使用 DeepSeek API（OpenAI 兼容接口）执行 benchmark。

接口与 claude_cli_executor.py 完全兼容：
  python deepseek_executor.py \\
    --prompt-file /tmp/.../prompt.json \\
    --model deepseek-chat \\
    --run-kind baseline|with-skill \\
    --skill ./skills/document-summarizer

输出 JSON:
  {
    "output_text": "...",
    "trace_signals": {
      "skill_attempted": bool,
      "skill_triggered": bool,
      "team_mode_attempted": false,
      "team_mode_used": false
    },
    "meta": {...}
  }

Skill 触发判定逻辑（针对 DeepSeek）：
  - with-skill 模式下，系统提示词告知 Agent 可用 Skills
  - 若 LLM 调用 read_file 读取了目标 Skill 的 SKILL.md → skill_attempted = True
  - read_file 成功返回内容（非空/非错误）→ skill_triggered = True
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# --------------------------------------------------------------------------- #
# 依赖：openai（DeepSeek 使用 OpenAI 兼容接口）                               #
# --------------------------------------------------------------------------- #
try:
    from openai import OpenAI
except ImportError:
    print(json.dumps({
        "output_text": "",
        "trace_signals": {"skill_attempted": False, "skill_triggered": False,
                          "team_mode_attempted": False, "team_mode_used": False},
        "meta": {"failed": True, "error": "openai package not installed. Run: pip install openai"},
    }, ensure_ascii=False))
    sys.exit(1)

try:
    from dotenv import load_dotenv
    # 向上两级查找 .env（skills/skill-benchmark/scripts → File/）
    _env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
    else:
        load_dotenv()
except ImportError:
    pass  # dotenv 非必须

# --------------------------------------------------------------------------- #
# 常量                                                                         #
# --------------------------------------------------------------------------- #
DEFAULT_TIMEOUT = 120   # 单次对话最长等待秒数
MAX_TOOL_ROUNDS = 8     # 最多进行几轮工具调用循环（防止死循环）


# --------------------------------------------------------------------------- #
# 工具定义（read_file）                                                        #
# --------------------------------------------------------------------------- #
READ_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read the content of a local file. "
            "Path is relative to the project root (the directory containing skills/). "
            "Use this to read SKILL.md files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path from project root, e.g. skills/document-summarizer/SKILL.md"
                }
            },
            "required": ["file_path"],
        },
    },
}


# --------------------------------------------------------------------------- #
# Skill 扫描（生成与 standalone_agent.py 相同格式的 XML 快照）                #
# --------------------------------------------------------------------------- #
def _scan_skills(skills_dir: Path) -> str:
    """扫描 skills/ 目录，返回 XML 快照（格式同 standalone_agent.py）"""
    import yaml
    skills = []
    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        try:
            content = skill_md.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1])
                    if meta:
                        rel = str(skill_md.relative_to(skills_dir.parent))
                        skills.append({
                            "name": meta.get("name", skill_md.parent.name),
                            "description": meta.get("description", ""),
                            "location": rel,
                        })
        except Exception:
            pass

    lines = ["<available_skills>"]
    for s in skills:
        lines += [
            "  <skill>",
            f"    <name>{s['name']}</name>",
            f"    <description>{s['description']}</description>",
            f"    <location>{s['location']}</location>",
            "  </skill>",
        ]
    lines.append("</available_skills>")
    return "\n".join(lines)


def _build_system_prompt(skills_snapshot: str) -> str:
    return f"""你是一个专业的 AI 助手，拥有工具调用能力。

## 可用技能
{skills_snapshot}

## 技能调用协议
当你需要使用某个技能时，必须：
1. 先使用 read_file 工具读取技能定义文件（location 字段指定的路径）
2. 仔细阅读 SKILL.md 中的执行步骤
3. 根据步骤完成任务

禁止直接猜测技能用法，必须先读取文件！"""


def _build_baseline_system_prompt() -> str:
    return "你是一个专业的 AI 助手。请直接回答用户问题，不要调用任何工具。"


# --------------------------------------------------------------------------- #
# 文件读取（工具实现）                                                         #
# --------------------------------------------------------------------------- #
def _execute_read_file(file_path: str, base_dir: Path) -> str:
    """安全地读取项目内文件，返回内容字符串。超出沙箱或不存在时返回错误信息。"""
    try:
        normalized = file_path.replace("\\", "/").lstrip("./")
        full = (base_dir / normalized).resolve()
        if not str(full).startswith(str(base_dir.resolve())):
            return "Error: path escapes project root"
        if not full.exists():
            return f"Error: file not found: {file_path}"
        content = full.read_text(encoding="utf-8")
        if len(content) > 10000:
            content = content[:10000] + "\n...[truncated]"
        return content
    except Exception as e:
        return f"Error: {e}"


# --------------------------------------------------------------------------- #
# 核心对话循环（支持工具调用）                                                 #
# --------------------------------------------------------------------------- #
def _run_chat(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_text: str,
    base_dir: Path,
    target_skill_root: str,
    target_skill_name: str,
    enable_tools: bool,
) -> dict:
    """
    执行一次完整的 LLM 对话（含工具调用循环）。
    返回:
      {
        "output_text": str,
        "skill_attempted": bool,
        "skill_triggered": bool,
      }
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_text},
    ]
    tools = [READ_FILE_TOOL] if enable_tools else []

    skill_attempted = False
    skill_triggered = False
    output_text = ""

    for _round in range(MAX_TOOL_ROUNDS):
        kwargs: dict = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        # 解析 finish_reason
        finish_reason = choice.finish_reason  # "stop" | "tool_calls" | ...

        # 收集文本输出
        if msg.content:
            output_text = msg.content

        # 没有工具调用，结束
        if finish_reason != "tool_calls" or not msg.tool_calls:
            break

        # 处理每个工具调用
        # 将 assistant 消息序列化为 plain dict 再放入 messages
        # （避免将 openai Pydantic 对象直接塞回下一轮 create() 导致序列化错误）
        asst_dict: dict = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            asst_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(asst_dict)  # assistant message with tool_calls

        tool_results = []
        for tc in msg.tool_calls:
            if tc.function.name == "read_file":
                args = json.loads(tc.function.arguments or "{}")
                fp = args.get("file_path", "")
                # 判断是否命中目标 Skill
                if target_skill_root and target_skill_root in fp:
                    skill_attempted = True
                elif target_skill_name and target_skill_name in fp:
                    skill_attempted = True

                result_text = _execute_read_file(fp, base_dir)

                # 读取成功且命中 → skill_triggered
                if skill_attempted and not result_text.startswith("Error"):
                    skill_triggered = True

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })
            else:
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "Tool not available.",
                })

        messages.extend(tool_results)
        # 继续循环，让 LLM 基于工具结果生成最终回复

    return {
        "output_text": output_text,
        "skill_attempted": skill_attempted,
        "skill_triggered": skill_triggered,
    }


# --------------------------------------------------------------------------- #
# 主流程                                                                       #
# --------------------------------------------------------------------------- #
def run(prompt_file: Path, model: str, run_kind: str, skill: str | None) -> dict:
    t0 = time.monotonic()

    # 读取 prompt JSON
    prompt = json.loads(prompt_file.read_text(encoding="utf-8"))
    user_text = prompt.get("text", "")

    # API 配置（从环境变量读取）
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    base_url = (
        os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "https://api.deepseek.com"
    )

    if not api_key:
        return _error_result("API key not found. Set DEEPSEEK_API_KEY in .env", model, run_kind)

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 确定 base_dir（项目根目录）和 skills_dir
    base_dir = Path(__file__).parent.parent.parent.parent.resolve()
    skills_dir = base_dir / "skills"

    # 解析 Skill 路径
    target_skill_root = ""
    target_skill_name = ""
    if skill:
        sp = Path(skill)
        target_skill_root = str(sp)
        target_skill_name = sp.name

    # 构建系统提示词
    if run_kind == "baseline":
        system_prompt = _build_baseline_system_prompt()
        enable_tools = False
    else:
        skills_snapshot = _scan_skills(skills_dir)
        system_prompt = _build_system_prompt(skills_snapshot)
        enable_tools = True

    # 执行对话
    try:
        result = _run_chat(
            client=client,
            model=model,
            system_prompt=system_prompt,
            user_text=user_text,
            base_dir=base_dir,
            target_skill_root=target_skill_root,
            target_skill_name=target_skill_name,
            enable_tools=enable_tools,
        )
    except Exception as exc:
        return _error_result(str(exc), model, run_kind)

    elapsed = round(time.monotonic() - t0, 2)

    return {
        "output_text": result["output_text"],
        "trace_signals": {
            "skill_attempted": result["skill_attempted"],
            "skill_triggered": result["skill_triggered"],
            "team_mode_attempted": False,
            "team_mode_used": False,
        },
        "meta": {
            "model": model,
            "run_kind": run_kind,
            "executor": "deepseek_executor",
            "elapsed_seconds": elapsed,
            "failed": False,
            "timed_out": False,
            "returncode": 0,
            "stderr_tail": "",
            "stream_stdout_tail": [],
            "stream_stderr_tail": [],
        },
    }


def _error_result(error_msg: str, model: str, run_kind: str) -> dict:
    return {
        "output_text": f"[executor error: {error_msg}]",
        "trace_signals": {
            "skill_attempted": False,
            "skill_triggered": False,
            "team_mode_attempted": False,
            "team_mode_used": False,
        },
        "meta": {
            "model": model,
            "run_kind": run_kind,
            "executor": "deepseek_executor",
            "failed": True,
            "timed_out": False,
            "returncode": 1,
            "error": error_msg,
            "stderr_tail": error_msg,
            "stream_stdout_tail": [],
            "stream_stderr_tail": [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DeepSeek executor adapter for skill-benchmark (drop-in for claude_cli_executor)."
    )
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--run-kind", required=True, choices=["baseline", "with-skill"])
    parser.add_argument("--skill", default="")
    args = parser.parse_args()

    data = run(Path(args.prompt_file), args.model, args.run_kind, args.skill or None)
    print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
