import json
import os
import re
from observability import observe
from registry import get_registry
from models.vllm_backend import VLLMBackend
from models.llamacpp_backend import LlamaCppBackend
from memory.redis_cache import RedisCache
from memory.qdrant_store import QdrantStore
from dotenv import load_dotenv
load_dotenv()

TOOL_CALL_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
        "args": {"type": "object"},
    },
    "required": ["tool", "args"],
}

SYSTEM_PROMPT = """You are a Finance AI Agent for NSE/BSE markets.
You have access to these tools: {tools}

Given a user query, respond with EXACTLY one JSON object:
{{"tool": "<tool_name>", "args": {{"symbol": "<NSE_SYMBOL>"}}}}

If no tool is needed, respond with:
{{"tool": "none", "args": {{"reply": "<your answer>"}}}}
"""

def normalize_query(q: str) -> str:
    m = re.search(r'(?:what|how) about (\w+)|show me (\w+)|and (\w+)', q.lower())
    if m:
        symbol = next(g for g in m.groups() if g).upper()
        return f"What is the price of {symbol}?"
    return q


class FinanceAgent:
    def __init__(self):
        self.registry = get_registry()
        self.session_memory = RedisCache()
        self.long_memory = QdrantStore()
        self.model = self._load_model()

    def _load_model(self):
        gpu = VLLMBackend()
        if gpu.is_available():
            print("[agent] using vLLM (GPU)")
            return gpu
        cpu = LlamaCppBackend()
        if cpu.is_available():
            print("[agent] using llama.cpp (CPU fallback)")
            return cpu
        raise RuntimeError("No LLM backend available.")

    @observe
    async def run(self, session_id: str, user_query: str) -> dict:
        user_query = normalize_query(user_query)

        # 1. Short-term context (Redis)
        history = self.session_memory.load(session_id, "history") or ""

        # 2. Long-term memory — only at session start
        past_ctx = ""
        if not history:
            past = self.long_memory.search(user_query, top_k=2)
            past_ctx = "\n".join(p["value"] for p in past) if past else ""

        # 3. Build prompt
        tool_names = list(self.registry.keys())
        prompt = SYSTEM_PROMPT.format(tools=tool_names)
        if past_ctx:
            prompt += f"\n\nRelevant past context:\n{past_ctx}"
        if history:
            prompt += f"\n\nConversation so far:\n{history}"
        prompt += f"\n\nUser: {user_query}\nOutput ONLY the JSON object, nothing else:"

        # 4. LLM → tool decision
        raw = self.model.generate(prompt, schema=TOOL_CALL_SCHEMA)
        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}', raw)
            decision = json.loads(m.group()) if m else {"tool": "none", "args": {"reply": raw}}

        # 5. Execute tool
        tool_name = decision.get("tool", "none").strip().lstrip("$-: ")
        args = decision.get("args", {})

        if tool_name == "none":
            answer = args.get("reply", "")
            result = {"status": "ok", "reply": answer}
        elif tool_name in self.registry:
            tool = self.registry[tool_name]
            result = await tool.run(**args)
            answer_prompt = f"User asked: {user_query}\nData: {json.dumps(result)}\nOne sentence answer:"
            answer = self.model.generate(answer_prompt, schema=None)
        else:
            result = {"status": "error", "message": f"Unknown tool: {tool_name}"}
            answer = f"Unknown tool: {tool_name}"

        # 6. Persist memory
        turn = f"User: {user_query}\nAnswer: {answer}"
        new_history = (history + "\n" + turn)[-3000:]
        self.session_memory.save(session_id, "history", new_history)
        self.long_memory.save(session_id, "turn", turn)

        return {"tool_used": tool_name, "result": result, "answer": answer}