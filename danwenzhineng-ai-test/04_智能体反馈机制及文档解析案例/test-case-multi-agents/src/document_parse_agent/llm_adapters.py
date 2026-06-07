"""Provider adapters for Marker LLM configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
QIANWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QIANWEN_MODEL = "qwen3-vl-flash"

'''
`@dataclass(frozen=True)` 是 Python 里的一个类装饰器，用来把普通类快速变成“数据类”，并且让实例创建后不可修改。

来自标准库：

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    age: int
```

它主要做两件事：

1. `@dataclass`
   自动生成一些常用方法，比如：

```python
__init__
__repr__
__eq__
```

所以你可以直接写：

```python
u = User("Alice", 18)
print(u)  # User(name='Alice', age=18)
```

2. `frozen=True`
   表示对象是“冻结”的，字段不能再被修改：

```python
u.age = 19
# dataclasses.FrozenInstanceError: cannot assign to field 'age'
```

所以它常用于表示不可变配置、值对象、消息、状态快照等：

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int
```

简单说：`@dataclass(frozen=True)` = 自动生成数据类方法 + 实例不可变。
'''

@dataclass(frozen=True)
class MarkerLLMConfig:
    """Resolved OpenAI-compatible LLM settings for Marker."""

    provider: str
    api_key: str | None
    base_url: str | None
    model: str | None
    llm_service: str = "marker.services.openai.OpenAIService"

    def to_marker_config(self) -> dict[str, str]:
        """Return Marker ConfigParser keys."""
        config: dict[str, str] = {"llm_service": self.llm_service}
        if self.api_key:
            config["openai_api_key"] = self.api_key
        if self.base_url:
            config["openai_base_url"] = self.base_url
        if self.model:
            config["openai_model"] = self.model
        return config


class MarkerLLMProviderAdapter:
    """Base class for Marker LLM provider adapters."""

    provider = "custom"

    def resolve(self) -> MarkerLLMConfig:
        """Resolve provider settings from the environment."""
        raise NotImplementedError


class DeepSeekMarkerLLMAdapter(MarkerLLMProviderAdapter):
    """DeepSeek OpenAI-compatible Marker LLM adapter."""

    provider = "deepseek"

    def resolve(self) -> MarkerLLMConfig:
        """Resolve DeepSeek settings from environment variables."""
        return MarkerLLMConfig(
            provider=self.provider,
            api_key=os.getenv("MARKER_DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("MARKER_DEEPSEEK_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or DEEPSEEK_BASE_URL,
            model=os.getenv("MARKER_DEEPSEEK_MODEL") or os.getenv("DEEPSEEK_MODEL") or DEEPSEEK_MODEL,
        )


class QianwenMarkerLLMAdapter(MarkerLLMProviderAdapter):
    """Alibaba Cloud Bailian Qwen-VL OpenAI-compatible Marker LLM adapter."""

    provider = "qianwen"

    def resolve(self) -> MarkerLLMConfig:
        """Resolve Qianwen/DashScope settings from environment variables."""
        return MarkerLLMConfig(
            provider=self.provider,
            api_key=os.getenv("MARKER_QIANWEN_API_KEY") or os.getenv("QWEN_API_KEY"),
            base_url=os.getenv("MARKER_QIANWEN_BASE_URL") or QIANWEN_BASE_URL,
            model=os.getenv("MARKER_QIANWEN_MODEL") or QIANWEN_MODEL,
        )


class CustomOpenAIMarkerLLMAdapter(MarkerLLMProviderAdapter):
    """Generic OpenAI-compatible Marker LLM adapter."""

    provider = "custom"

    def resolve(self) -> MarkerLLMConfig:
        """Resolve generic OpenAI-compatible settings from legacy variables."""
        return MarkerLLMConfig(
            provider=self.provider,
            api_key=os.getenv("MARKER_OPENAI_API_KEY"),
            base_url=os.getenv("MARKER_OPENAI_BASE_URL"),
            model=os.getenv("MARKER_OPENAI_MODEL"),
        )


def resolve_marker_llm_config(provider: str | None) -> MarkerLLMConfig:
    """Resolve Marker LLM settings for a provider name."""
    normalized = (provider or "qianwen").strip().lower()
    adapters: dict[str, MarkerLLMProviderAdapter] = {
        "deepseek": DeepSeekMarkerLLMAdapter(),
        "qianwen": QianwenMarkerLLMAdapter(),
        "qwenvl": QianwenMarkerLLMAdapter(),
        "dashscope": QianwenMarkerLLMAdapter(),
        "custom": CustomOpenAIMarkerLLMAdapter(),
        "openai": CustomOpenAIMarkerLLMAdapter(),
    }
    return adapters.get(normalized, CustomOpenAIMarkerLLMAdapter()).resolve()
