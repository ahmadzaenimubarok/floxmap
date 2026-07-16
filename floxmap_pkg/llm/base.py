"""LLM provider abstraction."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, user: str) -> str:
        """Send a chat message and return the response text."""
        ...
