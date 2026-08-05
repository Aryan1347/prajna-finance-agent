import os
import uuid
from memory.base_memory import BaseMemory

COLLECTION = "finance_agent"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2

class QdrantStore(BaseMemory):
    """Long-term vector memory. Fully local."""

    def __init__(self):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        from sentence_transformers import SentenceTransformer

        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
        )
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        # Create collection if missing
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION not in existing:
            self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def save(self, session_id: str, key: str, value: str) -> None:
        from qdrant_client.models import PointStruct
        vec = self.encoder.encode(value).tolist()
        self.client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={"session_id": session_id, "key": key, "value": value},
            )],
        )

    def load(self, session_id: str, key: str) -> str | None:
        # Exact match by payload filter
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        results = self.client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(must=[
                FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                FieldCondition(key="key", match=MatchValue(value=key)),
            ]),
            limit=1,
        )
        hits = results[0]
        return hits[0].payload["value"] if hits else None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        vec = self.encoder.encode(query).tolist()
        hits = self.client.query_points(
            collection_name=COLLECTION,
            query=vec,
            limit=top_k,
        ).points
        return [{"score": h.score, **h.payload} for h in hits]