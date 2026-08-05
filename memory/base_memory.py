from abc import ABC, abstractmethod

class BaseMemory(ABC):

    @abstractmethod
    def save(self, session_id: str, key: str, value: str) -> None: ...

    @abstractmethod
    def load(self, session_id: str, key: str) -> str | None: ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[dict]: ...
