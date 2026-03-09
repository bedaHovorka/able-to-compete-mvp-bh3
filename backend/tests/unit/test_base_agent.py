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


@pytest.mark.asyncio
class TestCallLlmApiParameters:
    """Verify exact parameters passed to the Anthropic API call."""

    def _make_mock_client(self, response_text="real response"):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_text)]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls
        return mock_anthropic_module, mock_client

    async def test_max_tokens_is_1024(self):
        """API call must use max_tokens=1024."""
        mock_anthropic_module, mock_client = self._make_mock_client()
        agent = ConcreteAgent()

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"
            await agent.call_llm("test prompt")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 1024

    async def test_model_from_settings_used(self):
        """API call must use self.model (from settings.LLM_MODEL at agent creation)."""
        mock_anthropic_module, mock_client = self._make_mock_client()

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.LLM_MODEL = "claude-opus-4-6"
            agent = ConcreteAgent()  # model set from patched settings
            await agent.call_llm("test prompt")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-6"

    async def test_conversation_history_included_in_messages(self):
        """Existing conversation history must be included in the messages sent to API."""
        mock_anthropic_module, mock_client = self._make_mock_client()
        agent = ConcreteAgent()
        agent.add_to_history("user", "previous question")
        agent.add_to_history("assistant", "previous answer")

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"
            await agent.call_llm("new question")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert any(m["content"] == "previous question" for m in messages)
        assert any(m["content"] == "previous answer" for m in messages)
        assert messages[-1]["content"] == "new question"

    async def test_history_not_updated_on_exception(self):
        """Conversation history must NOT be updated when API call fails."""
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=RuntimeError("API down"))
        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls

        agent = ConcreteAgent()
        history_before = len(agent.conversation_history)

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"
            result = await agent.call_llm("test prompt")

        assert len(agent.conversation_history) == history_before
        assert result.startswith("simulated:")


@pytest.mark.asyncio
class TestCallLlmAnthropicExceptions:
    """Test fallback behavior for anthropic-specific exception types."""

    def _make_mock_with_error(self, error):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=error)
        mock_async_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AsyncAnthropic = mock_async_anthropic_cls
        return mock_anthropic_module

    async def test_api_error_falls_back_to_simulate(self):
        """anthropic.APIError should be caught and fall back to simulate."""
        mock_anthropic_module = self._make_mock_with_error(Exception("APIError: overloaded"))
        agent = ConcreteAgent()

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"
            result = await agent.call_llm("test prompt")

        assert result.startswith("simulated:")

    async def test_auth_error_falls_back_to_simulate(self):
        """Authentication errors (bad key) should fall back to simulate."""
        mock_anthropic_module = self._make_mock_with_error(
            Exception("AuthenticationError: invalid key")
        )
        agent = ConcreteAgent()

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-bad-key"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"
            result = await agent.call_llm("test prompt")

        assert result.startswith("simulated:")

    async def test_rate_limit_error_falls_back_to_simulate(self):
        """Rate limit errors should fall back to simulate."""
        mock_anthropic_module = self._make_mock_with_error(
            Exception("RateLimitError: too many requests")
        )
        agent = ConcreteAgent()

        with patch("app.agents.base_agent.settings") as mock_settings, \
             patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            mock_settings.ANTHROPIC_API_KEY = "sk-ant-test"
            mock_settings.LLM_MODEL = "claude-sonnet-4-6"
            result = await agent.call_llm("test prompt")

        assert result.startswith("simulated:")
