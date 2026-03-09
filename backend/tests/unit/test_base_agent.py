"""
Unit tests for BaseAgent.call_llm()
"""
import pytest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base_agent import BaseAgent


class ConcreteAgent(BaseAgent):
    """Minimal concrete implementation used only in tests."""

    def simulate_response(self, prompt: str) -> str:
        return f"simulated: {prompt}"

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {}


@pytest.mark.asyncio
class TestCallLlmNoApiKey:
    """call_llm falls back to simulate_response when ANTHROPIC_API_KEY is absent."""

    async def test_returns_simulated_response_when_no_key(self):
        agent = ConcreteAgent()
        with patch("app.agents.base_agent.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            result = await agent.call_llm("hello")

        assert result == "simulated: hello"

    async def test_empty_string_api_key_also_falls_back(self):
        agent = ConcreteAgent()
        with patch("app.agents.base_agent.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            result = await agent.call_llm("world")

        assert result == "simulated: world"

    async def test_conversation_history_unchanged_on_fallback(self):
        agent = ConcreteAgent()
        with patch("app.agents.base_agent.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            await agent.call_llm("test prompt")

        assert agent.conversation_history == []


@pytest.mark.asyncio
class TestCallLlmWithApiKey:
    """call_llm makes a real Anthropic request when ANTHROPIC_API_KEY is set."""

    def _make_mock_response(self, text: str):
        content_block = MagicMock()
        content_block.text = text
        response = MagicMock()
        response.content = [content_block]
        return response

    async def test_returns_llm_response_when_key_set(self):
        agent = ConcreteAgent()
        mock_response = self._make_mock_response("LLM answer")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            result = await agent.call_llm("What is 2+2?")

        assert result == "LLM answer"

    async def test_conversation_history_updated_after_successful_call(self):
        agent = ConcreteAgent()
        mock_response = self._make_mock_response("42")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            await agent.call_llm("What is 6x7?")

        assert {"role": "user", "content": "What is 6x7?"} in agent.conversation_history
        assert {"role": "assistant", "content": "42"} in agent.conversation_history

    async def test_system_prompt_passed_to_api(self):
        agent = ConcreteAgent()
        mock_response = self._make_mock_response("ok")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            await agent.call_llm("prompt", system_prompt="Be concise.")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "Be concise."

    async def test_default_system_prompt_used_when_none_given(self):
        agent = ConcreteAgent()
        mock_response = self._make_mock_response("ok")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            await agent.call_llm("prompt")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "You are a helpful AI assistant."

    async def test_falls_back_to_simulate_on_api_exception(self):
        agent = ConcreteAgent()

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=RuntimeError("network error"))

        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"

            result = await agent.call_llm("fail prompt")

        assert result == "simulated: fail prompt"
