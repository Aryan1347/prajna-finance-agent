from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, **kwargs) -> dict[str, Any]:
        pass

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description}