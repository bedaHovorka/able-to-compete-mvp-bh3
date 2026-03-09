from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from app.config import settings
from app.utils.logger import logger


class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, model: str = None):
        self.model = model or settings.LLM_MODEL
        self.api_key = None  # Configure based on provider
        self.conversation_history: List[Dict[str, str]] = []

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    async def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Call LLM API (simplified for MVP - supports OpenAI-compatible APIs)
        In production, integrate with actual LLM provider
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": prompt})

        # Simulated response for MVP
        logger.info(f"AI Agent called with prompt: {prompt[:100]}...")
        return self.simulate_response(prompt)

    @abstractmethod
    def simulate_response(self, prompt: str) -> str:
        """Simulate LLM response for MVP demo"""
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result"""
        pass
