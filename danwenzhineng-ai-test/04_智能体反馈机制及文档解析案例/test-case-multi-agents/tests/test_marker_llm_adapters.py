from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from document_parse_agent.agent import configured_parse_options
from document_parse_agent.llm_adapters import resolve_marker_llm_config


class MarkerLLMAdapterTests(unittest.TestCase):
    def test_qianwen_defaults_to_dashscope_vl_flash(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = resolve_marker_llm_config("qianwen")

        self.assertEqual(config.provider, "qianwen")
        self.assertEqual(config.base_url, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.assertEqual(config.model, "qwen3-vl-flash")
        self.assertEqual(config.to_marker_config()["llm_service"], "marker.services.openai.OpenAIService")

    def test_qianwen_can_use_plus_model(self) -> None:
        with patch.dict(os.environ, {"MARKER_QIANWEN_MODEL": "qwen3-vl-plus", "DASHSCOPE_API_KEY": "dash-key"}, clear=True):
            config = resolve_marker_llm_config("qianwen")

        self.assertEqual(config.api_key, "dash-key")
        self.assertEqual(config.model, "qwen3-vl-plus")

    def test_deepseek_uses_project_deepseek_fallbacks(self) -> None:
        with patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "deepseek-key", "DEEPSEEK_MODEL": "deepseek-v4-pro"},
            clear=True,
        ):
            config = resolve_marker_llm_config("deepseek")

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.api_key, "deepseek-key")
        self.assertEqual(config.base_url, "https://api.deepseek.com")
        self.assertEqual(config.model, "deepseek-v4-pro")

    def test_custom_provider_preserves_marker_openai_triplet(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MARKER_OPENAI_API_KEY": "custom-key",
                "MARKER_OPENAI_BASE_URL": "https://custom.example/v1",
                "MARKER_OPENAI_MODEL": "custom-model",
            },
            clear=True,
        ):
            config = resolve_marker_llm_config("custom")

        self.assertEqual(config.provider, "custom")
        self.assertEqual(config.api_key, "custom-key")
        self.assertEqual(config.base_url, "https://custom.example/v1")
        self.assertEqual(config.model, "custom-model")

    def test_configured_options_enable_llm_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            options = configured_parse_options()

        self.assertTrue(options.use_llm)
        self.assertEqual(options.llm_provider, "qianwen")


if __name__ == "__main__":
    unittest.main()
