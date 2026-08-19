from __future__ import annotations

from typing import Any

from loop_engineering.schemas import DocsRequest


class DocsAgentRunner:
    def __init__(self, agent: Any) -> None:
        self.agent = agent

    def run(self, request: DocsRequest, verification_feedback: str | None = None) -> str:
        prompt = self._build_task_prompt(request, verification_feedback)
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={
                "tags": ["loop-1-agent", f"source:{request.source}"],
                "metadata": {
                    "event_id": request.event_id or "",
                    "requested_by": request.requested_by or "",
                },
            },
        )
        return self._message_text(result["messages"][-1].content)

    @staticmethod
    def _build_task_prompt(request: DocsRequest, feedback: str | None) -> str:
        sections = [
            "Documentation improvement request:",
            request.instruction,
            "",
            "Complete the change directly in the repository using the available tools.",
        ]
        if feedback:
            sections.extend(
                [
                    "",
                    "A previous attempt failed verification. Correct the existing working tree; do not",
                    "start unrelated work. Here is the verifier feedback:",
                    feedback,
                ]
            )
        return "\n".join(sections)

    @staticmethod
    def _message_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "\n".join(part for part in parts if part)
        return str(content)
