from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from app.config import settings
from app.utils.logger import logger


class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, model: str = None):
        self.model = model or settings.LLM_MODEL
        self.conversation_history: List[Dict[str, str]] = []

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    async def call_llm(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = settings.MAX_TOKENS) -> str:
        """
        Call LLM API via Anthropic. Falls back to simulate_response when the
        API key is absent or the request fails.
        """
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set — using simulated response")
            return self.simulate_response(prompt)

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            messages = list(self.conversation_history)
            messages.append({"role": "user", "content": prompt})

            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=messages,
            )
            result = response.content[0].text
            self.add_to_history("user", prompt)
            self.add_to_history("assistant", result)
            return result
        except Exception as e:
            logger.error(f"LLM call failed: {e} — falling back to simulated response")
            return self.simulate_response(prompt)

    @abstractmethod
    def simulate_response(self, prompt: str) -> str:
        """Simulate LLM response for MVP demo"""
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result"""
        pass
