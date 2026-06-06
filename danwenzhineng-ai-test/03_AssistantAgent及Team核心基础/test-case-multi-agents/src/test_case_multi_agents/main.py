"""Run a multi-agent test case workflow with AutoGen AgentChat.

Flow:
1. TestCaseWriter generates test cases from requirements.
2. TestCaseReviewer reviews the generated test cases.
3. HumanReviewer confirms or requests changes.
4. The latest writer output is saved as the final test cases after approval.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
from pathlib import Path
from typing import Callable

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, SourceMatchTermination, TextMentionTermination
from autogen_agentchat.messages import (
    ModelClientStreamingChunkEvent,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
)
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv


APPROVAL_TOKEN = "HUMAN_APPROVED"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_MAX_MESSAGES = 12
PROJECT_ROOT = Path(__file__).resolve().parents[2]
HumanInputFunc = Callable[[str, object | None], str]


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


def load_project_environment() -> None:
    """Load environment variables from a stable project-level .env path."""
    explicit_env_path = os.getenv("DEEPSEEK_ENV_PATH")
    if explicit_env_path:
        load_dotenv(explicit_env_path)
        return

    load_dotenv(PROJECT_ROOT / ".env")


def load_requirements(path: Path) -> str:
    """Read the requirement document used by the test-case writer agent."""
    if not path.exists():
        raise FileNotFoundError(f"Requirement file does not exist: {path}")
    return path.read_text(encoding="utf-8").strip()


async def count_chinese_characters(text: str) -> int:
    """统计中文字符个数。"""
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def build_task(requirements: str) -> str:
    """Build the task prompt sent to the multi-agent team."""
    return f"""
Create high-quality software test cases from the following requirements.

The workflow must follow this order:
1. TestCaseWriter writes a complete test case set.
2. TestCaseReviewer reviews the test cases and gives concrete feedback.
3. HumanReviewer either asks for changes or approves the final version.
4. If changes are requested, TestCaseWriter revises the test cases.

When writing or revising the test cases, use this format:

# Final Test Cases

| ID | Title | Type | Priority | Preconditions | Steps | Expected Result |
| --- | --- | --- | --- | --- | --- | --- |

Requirements:
{requirements}
""".strip()


def human_review_input(prompt: str = "", cancellation_token: object | None = None) -> str:
    """Collect human feedback or approval from the console."""
    _ = cancellation_token
    if prompt:
        print(prompt)
    print()
    print("Human review: type revision feedback, or type HUMAN_APPROVED to approve and stop.")
    return input("> ")


def create_team(
    model_client: OpenAIChatCompletionClient,
    max_messages: int,
    human_input_func: HumanInputFunc = human_review_input,
) -> RoundRobinGroupChat:
    """Create the writer, reviewer, and human-reviewer team."""
    writer = AssistantAgent(
        "TestCaseWriter",
        model_client=model_client,
        model_client_stream=True,#如果不希望用户看到stream输出，只要最终结果，那就给他改为false
        system_message=(
            "You are a principal QA test architect responsible for converting product "
            "requirements into production-ready manual test cases. Your test cases must "
            "be clear enough that another tester can execute them without extra context. "
            "Analyze the requirements for business rules, user flows, validation rules, "
            "state transitions, error handling, security/privacy risks, accessibility, "
            "and non-functional expectations. Produce a balanced suite that includes "
            "happy paths, negative paths, boundary values, permission/session cases, "
            "data validation, recovery behavior, and regression-sensitive scenarios. "
            "Every test case must have a unique ID, concise title, test type, priority, "
            "explicit preconditions, executable steps, and observable expected results. "
            "Avoid vague steps such as 'verify it works'. Do not invent requirements; "
            "if an assumption is necessary, mark it clearly in the test case wording. "
            "When reviewer or human feedback is provided, revise and return the full "
            "test case table, incorporating the feedback directly instead of only "
            "describing what should change."
        ),
    )

    reviewer = AssistantAgent(
        "TestCaseReviewer",
        model_client=model_client,
        model_client_stream=True,
        system_message=(
            "You are a senior QA review lead and quality gatekeeper. Review only the "
            "latest test cases from TestCaseWriter against the provided requirements. "
            "Assess requirement traceability, scenario coverage, priority accuracy, "
            "step clarity, expected-result observability, independence of cases, "
            "duplicate or overlapping coverage, missing edge cases, and whether the "
            "suite is practical to execute. Be especially alert to gaps around negative "
            "validation, boundary values, authorization/session behavior, security "
            "information leakage, accessibility, performance expectations, and recovery "
            "from failure states. If the suite is not ready, provide a concise review "
            "with specific blocking issues and concrete revision instructions grouped "
            "by severity. Do not rewrite the whole suite yourself; your role is to "
            "drive the writer to fix it. If the suite is ready for human confirmation, "
            "start your response with REVIEW_READY, then give a brief approval summary "
            "and call out any low-risk assumptions that the human should double-check."
        ),
    )

    human_reviewer = UserProxyAgent(
        "HumanReviewer",
        input_func=human_input_func,
        description=(
            f"Human reviewer. Type feedback to request revisions, or type {APPROVAL_TOKEN} "
            "to approve and stop the workflow."
        ),
    )

    termination = TextMentionTermination(APPROVAL_TOKEN, sources=["HumanReviewer"]) | MaxMessageTermination(
        max_messages
    )
    return RoundRobinGroupChat(
        [writer, reviewer, human_reviewer],
        termination_condition=termination,
    )


def create_writer_reviewer_team(
    model_client: OpenAIChatCompletionClient,
    max_messages: int = DEFAULT_MAX_MESSAGES,
) -> RoundRobinGroupChat:
    """Create a web-friendly team that stops before human approval."""
    writer = AssistantAgent(
        "TestCaseWriter",
        model_client=model_client,
        model_client_stream=True,
        system_message=(
            "You are a principal QA test architect responsible for converting product "
            "requirements into production-ready manual test cases. Your test cases must "
            "be clear enough that another tester can execute them without extra context. "
            "Analyze requirements for business rules, user flows, validation rules, "
            "state transitions, error handling, security/privacy risks, accessibility, "
            "and non-functional expectations. Return the full revised test case table "
            "whenever feedback is provided."
        ),
    )

    reviewer = AssistantAgent(
        "TestCaseReviewer",
        model_client=model_client,
        model_client_stream=True,
        system_message=(
            "You are a senior QA review lead and quality gatekeeper. Review the latest "
            "TestCaseWriter output against the requirements and any human feedback. "
            "Assess traceability, coverage, priority, clarity, observability, duplicate "
            "coverage, missing edge cases, security, accessibility, performance, and "
            "recovery behavior. If ready for human confirmation, start with REVIEW_READY. "
            "If not ready, list blocking issues and concrete revision instructions."
        ),
    )

    return RoundRobinGroupChat(
        [writer, reviewer],
        termination_condition=SourceMatchTermination(["TestCaseReviewer"]) | MaxMessageTermination(max_messages),
    )


def create_counter_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Create an agent that counts Chinese characters through a tool call."""
    return AssistantAgent(
        "TestCaseCounter",
        model_client=model_client,
        system_message=(
            "通过调用工具统计测试用例中的中文字符个数。必须调用 count_chinese_characters 工具，"
            "不要自己估算。输出一句简洁中文总结，例如：测试用例中的中文字符总数为：235 字。"
        ),
        tools=[count_chinese_characters],
        reflect_on_tool_use=False,
        model_client_stream=True,
    )


def create_deepseek_model_client(model: str, base_url: str) -> OpenAIChatCompletionClient:
    """Create an AutoGen model client for DeepSeek's OpenAI-compatible API."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "DEEPSEEK_API_KEY is not set. Add it to the project .env file, export it in your shell, "
            "or set DEEPSEEK_ENV_PATH to the env file path."
        )

    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": True,
        },
    )


def extract_latest_writer_output(result: TaskResult) -> str:
    """Return the latest test case content produced by TestCaseWriter."""
    return extract_latest_source_output(result=result, source="TestCaseWriter")


def extract_latest_source_output(result: TaskResult, source: str) -> str:
    """Return the latest text content produced by a specific message source."""
    for message in reversed(result.messages):
        if getattr(message, "source", None) == source:
            content = getattr(message, "content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()
    sources = [str(getattr(message, "source", "unknown")) for message in result.messages]
    raise RuntimeError(
        f"No {source} output was found in the team result. "
        f"stop_reason={result.stop_reason!r}; message_sources={sources}"
    )


async def run_team_stream(team: RoundRobinGroupChat, task: str) -> TaskResult:
    """Run the team stream and render events according to their concrete type."""
    result: TaskResult | None = None
    streamed_sources: set[str] = set()
    active_stream_source: str | None = None

    async for event in team.run_stream(task=task):
        if isinstance(event, ModelClientStreamingChunkEvent):
            source = getattr(event, "source", "unknown")
            if source != active_stream_source:
                if active_stream_source is not None:
                    print()
                print(f"\n[{source} streaming]")
                active_stream_source = source
                streamed_sources.add(source)
            print(event.content, end="", flush=True)
            continue

        if isinstance(event, TextMessage):
            source = event.source
            if active_stream_source is not None:
                print()
                active_stream_source = None
            if source in streamed_sources:
                print(f"[{source} complete]")
            else:
                print(f"\n[{source}]\n{event.content}")
            continue

        if isinstance(event, TaskResult):
            if active_stream_source is not None:
                print()
                active_stream_source = None
            result = event
            print(f"\n[TaskResult] stop_reason={event.stop_reason}")
            print(f"[TaskResult] total_messages={len(event.messages)}")
            continue

        print(f"\n[{event.__class__.__name__}]\n{event}")

    if result is None:
        raise RuntimeError("AutoGen stream finished without returning a TaskResult.")
    return result


async def run_team_silently(team: RoundRobinGroupChat, task: str) -> TaskResult:
    """Run the team stream without printing intermediate events."""
    result: TaskResult | None = None
    async for event in team.run_stream(task=task):
        if isinstance(event, TaskResult):
            result = event

    if result is None:
        raise RuntimeError("AutoGen stream finished without returning a TaskResult.")
    return result


def message_to_payload(message: object) -> dict[str, str]:
    """Convert an AutoGen message/event object into a JSON-friendly trace item."""
    content = getattr(message, "content", "")
    if not isinstance(content, str):
        content = str(content)
    return {
        "source": str(getattr(message, "source", "unknown")),
        "content": content,
        "type": message.__class__.__name__,
    }


def extract_count_from_tool_results(results: object) -> int | None:
    """Extract the integer count from AutoGen function execution results."""
    if not isinstance(results, list):
        return None

    for result in results:
        content = getattr(result, "content", None)
        if isinstance(content, int):
            return content
        if isinstance(content, str):
            text = content.strip()
            if text.isdigit():
                return int(text)
            match = re.search(r"\d+", text)
            if match:
                return int(match.group(0))
    return None


async def run_counter_agent(
    model_client: OpenAIChatCompletionClient,
    test_cases: str,
) -> dict[str, object]:
    """Run the counter agent and collect tool-call events."""
    counter_agent = create_counter_agent(model_client=model_client)
    trace: list[dict[str, str]] = []
    summary = ""
    count: int | None = None

    task = f"""统计下面测试用例中的中文字符个数：

{test_cases}
"""

    async for event in counter_agent.run_stream(task=task):
        if isinstance(event, ToolCallRequestEvent):
            trace.append(message_to_payload(event))
            continue

        if isinstance(event, ToolCallExecutionEvent):
            trace.append(message_to_payload(event))
            extracted_count = extract_count_from_tool_results(getattr(event, "content", None))
            if extracted_count is not None:
                count = extracted_count
            continue

        if isinstance(event, ToolCallSummaryMessage):
            trace.append(message_to_payload(event))
            content = getattr(event, "content", "")
            if isinstance(content, str):
                summary = content
            extracted_count = extract_count_from_tool_results(getattr(event, "results", None))
            if extracted_count is not None:
                count = extracted_count
            continue

        if isinstance(event, TaskResult):
            for message in event.messages:
                payload = message_to_payload(message)
                if payload not in trace:
                    trace.append(payload)
            if event.messages:
                content = getattr(event.messages[-1], "content", "")
                if isinstance(content, str):
                    summary = content
            continue

    return {
        "chinese_character_count": count,
        "counter_summary": summary,
        "counter_trace": trace,
    }


async def run_counter_agent_safely(
    model_client: OpenAIChatCompletionClient,
    test_cases: str,
) -> dict[str, object]:
    """Run the counter agent without failing the whole review cycle."""
    try:
        return await run_counter_agent(model_client=model_client, test_cases=test_cases)
    except Exception as exc:
        return {
            "chinese_character_count": None,
            "counter_summary": f"Chinese character counter failed: {exc}",
            "counter_trace": [
                {
                    "source": "TestCaseCounter",
                    "content": str(exc),
                    "type": exc.__class__.__name__,
                }
            ],
        }


async def stream_counter_agent_events(
    model_client: OpenAIChatCompletionClient,
    test_cases: str,
):
    """Stream counter-agent tool events and emit a final counter result event."""
    counter_agent = create_counter_agent(model_client=model_client)
    trace: list[dict[str, str]] = []
    summary = ""
    count: int | None = None

    task = f"""统计下面测试用例中的中文字符个数：

{test_cases}
"""

    try:
        async for event in counter_agent.run_stream(task=task):
            if isinstance(event, ToolCallRequestEvent):
                payload = message_to_payload(event)
                trace.append(payload)
                yield {"event": "tool_call_request", **payload}
                continue

            if isinstance(event, ToolCallExecutionEvent):
                payload = message_to_payload(event)
                trace.append(payload)
                extracted_count = extract_count_from_tool_results(getattr(event, "content", None))
                if extracted_count is not None:
                    count = extracted_count
                yield {"event": "tool_call_execution", **payload}
                continue

            if isinstance(event, ToolCallSummaryMessage):
                payload = message_to_payload(event)
                trace.append(payload)
                content = getattr(event, "content", "")
                if isinstance(content, str):
                    summary = content
                extracted_count = extract_count_from_tool_results(getattr(event, "results", None))
                if extracted_count is not None:
                    count = extracted_count
                yield {"event": "tool_call_summary", **payload}
                continue

            if isinstance(event, TaskResult):
                for message in event.messages:
                    payload = message_to_payload(message)
                    if payload not in trace:
                        trace.append(payload)
                if event.messages:
                    content = getattr(event.messages[-1], "content", "")
                    if isinstance(content, str):
                        summary = content
                continue
    except Exception as exc:
        trace.append(
            {
                "source": "TestCaseCounter",
                "content": str(exc),
                "type": exc.__class__.__name__,
            }
        )
        summary = f"Chinese character counter failed: {exc}"

    yield {
        "event": "counter_result",
        "source": "TestCaseCounter",
        "type": "CounterResult",
        "content": summary,
        "chinese_character_count": count,
        "counter_summary": summary,
        "counter_trace": trace,
    }


def task_result_to_payload(result: TaskResult, final_content: str) -> dict[str, object]:
    """Build a JSON-serializable response for API and UI clients."""
    messages = [message_to_payload(message) for message in result.messages]

    return {
        "final_test_cases": final_content,
        "stop_reason": result.stop_reason,
        "messages": messages,
    }


def build_revision_task(
    requirements: str,
    previous_test_cases: str,
    reviewer_comments: str,
    human_feedback: str,
) -> str:
    """Build a revision prompt for the web reject-with-feedback loop."""
    return f"""
Revise the test cases using the original requirements, reviewer comments, and human feedback.

Return the complete updated test case table in the required format. Do not only explain changes.

Original requirements:
{requirements}

Previous test cases:
{previous_test_cases}

Reviewer comments:
{reviewer_comments}

Human feedback:
{human_feedback}
""".strip()


async def generate_review_cycle_for_web(
    requirements: str,
    previous_test_cases: str | None = None,
    reviewer_comments: str | None = None,
    human_feedback: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    max_messages: int = DEFAULT_MAX_MESSAGES,
) -> dict[str, object]:
    """Generate or revise test cases and stop before human approval."""
    load_project_environment()
    selected_model = model or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
    selected_base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)

    if human_feedback:
        if not previous_test_cases or not reviewer_comments:
            raise ValueError("previous_test_cases and reviewer_comments are required for revision.")
        task = build_revision_task(
            requirements=requirements,
            previous_test_cases=previous_test_cases,
            reviewer_comments=reviewer_comments,
            human_feedback=human_feedback,
        )
    else:
        task = build_task(requirements)

    model_client = create_deepseek_model_client(model=selected_model, base_url=selected_base_url)
    try:
        team = create_writer_reviewer_team(model_client=model_client, max_messages=max_messages)
        result = await run_team_silently(team=team, task=task)
        draft = extract_latest_source_output(result=result, source="TestCaseWriter")
        review = extract_latest_source_output(result=result, source="TestCaseReviewer")
        counter_result = await run_counter_agent_safely(model_client=model_client, test_cases=draft)
        payload = task_result_to_payload(result=result, final_content=draft)
        payload.update(
            {
                "draft_test_cases": draft,
                "review": review,
                "awaiting_human_review": True,
                "approved": False,
                **counter_result,
            }
        )
        return payload
    finally:
        await model_client.close()


async def stream_review_cycle_for_web(
    requirements: str,
    previous_test_cases: str | None = None,
    reviewer_comments: str | None = None,
    human_feedback: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    max_messages: int = DEFAULT_MAX_MESSAGES,
):
    """Stream a web review cycle as JSON-serializable events."""
    load_project_environment()
    selected_model = model or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
    selected_base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)

    if human_feedback:
        if not previous_test_cases or not reviewer_comments:
            raise ValueError("previous_test_cases and reviewer_comments are required for revision.")
        task = build_revision_task(
            requirements=requirements,
            previous_test_cases=previous_test_cases,
            reviewer_comments=reviewer_comments,
            human_feedback=human_feedback,
        )
    else:
        task = build_task(requirements)

    model_client = create_deepseek_model_client(model=selected_model, base_url=selected_base_url)
    result: TaskResult | None = None
    try:
        team = create_writer_reviewer_team(model_client=model_client, max_messages=max_messages)
        yield {
            "event": "status",
            "source": "system",
            "type": "Status",
            "content": "Starting TestCaseWriter and TestCaseReviewer.",
        }

        async for event in team.run_stream(task=task):
            if isinstance(event, ModelClientStreamingChunkEvent):
                yield {"event": "chunk", **message_to_payload(event)}
                continue

            if isinstance(event, TextMessage):
                yield {"event": "message", **message_to_payload(event)}
                continue

            if isinstance(event, TaskResult):
                result = event
                yield {
                    "event": "team_result",
                    "source": "system",
                    "type": "TaskResult",
                    "content": str(event.stop_reason),
                    "stop_reason": event.stop_reason,
                    "message_count": len(event.messages),
                }
                continue

        if result is None:
            raise RuntimeError("AutoGen stream finished without returning a TaskResult.")

        draft = extract_latest_source_output(result=result, source="TestCaseWriter")
        review = extract_latest_source_output(result=result, source="TestCaseReviewer")

        yield {
            "event": "status",
            "source": "TestCaseCounter",
            "type": "Status",
            "content": "Counting Chinese characters with count_chinese_characters.",
        }
        counter_result: dict[str, object] = {}
        async for counter_event in stream_counter_agent_events(model_client=model_client, test_cases=draft):
            yield counter_event
            if counter_event.get("event") == "counter_result":
                counter_result = counter_event

        payload = task_result_to_payload(result=result, final_content=draft)
        payload.update(
            {
                "draft_test_cases": draft,
                "review": review,
                "awaiting_human_review": True,
                "approved": False,
                "chinese_character_count": counter_result.get("chinese_character_count"),
                "counter_summary": counter_result.get("counter_summary", ""),
                "counter_trace": counter_result.get("counter_trace", []),
            }
        )
        yield {"event": "final", "source": "system", "type": "FinalPayload", "content": "Review cycle complete.", **payload}
    finally:
        await model_client.close()


def write_final_test_cases(content: str, output_path: Path) -> None:
    """Persist the final test case markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")


async def run_workflow(args: argparse.Namespace) -> None:
    """Run the AutoGen team and save the final approved test cases."""
    load_project_environment()

    requirements = load_requirements(args.requirements)
    model = args.model or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
    base_url = args.base_url or os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)

    model_client = create_deepseek_model_client(model=model, base_url=base_url)
    try:
        team = create_team(model_client=model_client, max_messages=args.max_messages)
        result = await run_team_stream(team=team, task=build_task(requirements))

        final_content = extract_latest_writer_output(result)
        write_final_test_cases(final_content, args.output)

        print()
        print(f"Stop reason: {result.stop_reason}")
        print(f"Final test cases saved to: {args.output}")
    finally:
        await model_client.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate, review, human-approve, and save final test cases with AutoGen agents."
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        default=PROJECT_ROOT / "requirements" / "sample_requirement.md",
        help="Path to the requirement markdown file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "final_test_cases.md",
        help="Where to save the final approved test cases.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"DeepSeek model name. Defaults to DEEPSEEK_MODEL or {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=f"DeepSeek OpenAI-compatible base URL. Defaults to DEEPSEEK_BASE_URL or {DEFAULT_DEEPSEEK_BASE_URL}.",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=DEFAULT_MAX_MESSAGES,
        help="Safety stop for the team if human approval is not provided.",
    )
    return parser.parse_args()


def cli() -> None:
    """CLI entrypoint."""
    asyncio.run(run_workflow(parse_args()))


if __name__ == "__main__":
    cli()
