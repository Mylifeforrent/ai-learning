from __future__ import annotations

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from loop_engineering.config import HarnessConfig, Settings


def create_docs_agent(settings: Settings, harness: HarnessConfig, tools: list):
    """Loop 1: create the model + tools agent harness."""
    model = init_chat_model(settings.model)
    learned = "\n".join(f"- {rule}" for rule in harness.learned_rules)
    effective_prompt = harness.system_prompt
    if learned:
        effective_prompt += "\n\nLearned rules from reviewed traces:\n" + learned
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=effective_prompt,
        name="documentation-improvement-agent",
    )
