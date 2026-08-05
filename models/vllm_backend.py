import json
import os
from models.base_model import BaseModel

class VLLMBackend(BaseModel):
    def __init__(self):
        self.model_name = os.getenv("VLLM_MODEL", "microsoft/Phi-3-mini-4k-instruct")
        self.base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self.base_url,
                api_key="EMPTY"  # vLLM doesn't need a real key
            )
        return self._client

    def is_available(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{self.base_url}/models", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, schema: dict | None = None) -> str:
        client = self._get_client()
        kwargs = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.1,
        }
        if schema:
            kwargs["extra_body"] = {
                "guided_json": schema,
                "guided_decoding_backend": "outlines"
            }
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content