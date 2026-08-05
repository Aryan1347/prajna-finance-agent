import os
import redis

from memory.base_memory import BaseMemory

class RedisCache(BaseMemory):
    """Short-term session memory. TTL = 1hr."""

    TTL = 3600

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )

    def _key(self, session_id: str, key: str) -> str:
        return f"session:{session_id}:{key}"

    def save(self, session_id: str, key: str, value: str) -> None:
        self.client.setex(self._key(session_id, key), self.TTL, value)

    def load(self, session_id: str, key: str) -> str | None:
        return self.client.get(self._key(session_id, key))

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        # Redis doesn't do vector search here — that's Qdrant's job
        return []