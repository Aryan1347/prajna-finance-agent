from abc import ABC, abstractmethod
from typing import Any

class BaseModel(ABC):
    """Hardware-agnostic LLM interface."""

    @abstractmethod
    def generate(self, prompt: str, schema: dict | None = None) -> str:
        """Generate text. If schema passed, return JSON conforming to it."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if backend can serve requests right now."""
        ...