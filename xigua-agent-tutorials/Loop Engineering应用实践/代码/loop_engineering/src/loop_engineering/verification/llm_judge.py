from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from loop_engineering.schemas import DocsRequest, ScopeVerdict


class LLMScopeJudge:
    """Agentic grader for semantic correctness and diff scope."""

    def __init__(self, model_name: str) -> None:
        model = init_chat_model(model_name)
        self.judge = model.with_structured_output(ScopeVerdict)

    def grade(self, request: DocsRequest, changed_files: list[str], diff: str) -> ScopeVerdict:
        clipped_diff = diff[:35_000]
        return self.judge.invoke(
            [
                SystemMessage(
                    content=(
                        "You are a strict documentation change reviewer. Decide whether the diff "
                        "fully satisfies the request, remains factually grounded in the repository, "
                        "and avoids unrelated edits. A passing score should normally be 80 or above. "
                        "Give concrete, actionable feedback when it fails."
                    )
                ),
                HumanMessage(
                    content=(
                        f"REQUEST:\n{request.instruction}\n\n"
                        f"CHANGED FILES:\n{changed_files}\n\n"
                        f"DIFF:\n{clipped_diff or '[empty diff]'}"
                    )
                ),
            ]
        )
