from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure provider keys in `.env` (e.g. DEEPSEEK_API_KEY) are visible to LangChain.
load_dotenv()


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model: str = Field(
        default="openai:gpt-5-nano",
        validation_alias=AliasChoices("MODEL", "model"),
    )
    grader_model: str = Field(
        default="openai:gpt-5-nano",
        validation_alias=AliasChoices("GRADER_MODEL", "grader_model"),
    )
    improvement_model: str = Field(
        default="openai:gpt-5-nano",
        validation_alias=AliasChoices("IMPROVEMENT_MODEL", "improvement_model"),
    )
    workspace_path: Path = Field(
        default=Path("sample_repo"),
        validation_alias=AliasChoices("WORKSPACE_PATH", "workspace_path"),
    )
    data_dir: Path = Field(
        default=Path("data"),
        validation_alias=AliasChoices("DATA_DIR", "data_dir"),
    )
    harness_path: Path = Field(
        default=Path("config/harness.json"),
        validation_alias=AliasChoices("HARNESS_PATH", "harness_path"),
    )
    max_verification_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        validation_alias=AliasChoices(
            "MAX_VERIFICATION_ATTEMPTS",
            "max_verification_attempts",
        ),
    )
    use_llm_judge: bool = Field(
        default=True,
        validation_alias=AliasChoices("USE_LLM_JUDGE", "use_llm_judge"),
    )


class HarnessConfig(BaseModel):
    """The editable agent harness that the hill-climbing loop can improve."""

    version: int = 1
    system_prompt: str
    allowed_extensions: list[str] = Field(default_factory=lambda: [".md", ".mdx"])
    protected_paths: list[str] = Field(default_factory=list)
    learned_rules: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)


class HarnessStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> HarnessConfig:
        if not self.path.exists():
            raise FileNotFoundError(f"Harness configuration not found: {self.path}")
        return HarnessConfig.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, config: HarnessConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(config.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
