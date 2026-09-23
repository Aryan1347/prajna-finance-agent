# Prajna Finance Agent

An AI-powered stock market assistant for NSE/BSE, built with a local-first architecture — no paid LLM APIs, no cloud dependency.

Uses a **ReAct (Reasoning + Acting) agent loop** backed by a quantized local LLM, with session memory via Redis and long-term vector memory via Qdrant.

---

## Features

- **ReAct Agent Loop** — LLM reasons over tool outputs iteratively before responding
- **5 Financial Tools** — live price, fundamentals, news, watchlist read/write
- **Local LLM Inference** — llama.cpp with GGUF models (GPU via CUDA, CPU fallback)
- **Session Memory** — Redis cache with TTL-based expiry (1hr)
- **Long-term Memory** — Qdrant vector store with `all-MiniLM-L6-v2` embeddings
- **Observability** — per-tool latency tracking via decorator (`observability.py`)
- **Confirmation Gate** — watchlist writes require explicit confirmation before execution

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Agent | Custom ReAct loop (`agent.py`) |
| LLM | llama.cpp (`llamacpp_backend.py`), vLLM stub (`vllm_backend.py`) |
| Session Memory | Redis (Docker, TTL 1hr) |
| Long-term Memory | Qdrant (local, `all-MiniLM-L6-v2`) |
| Tools | Alpha Vantage (primary), yfinance (fallback) |
| Watchlist DB | SQLite |
| UI | — *(in progress)* |

---

## Project Structure

```
prajna-finance-agent/
├── agent.py               # ReAct loop — reason, act, observe
├── main.py                # FastAPI app — /health, /chat, /price, /watchlist
├── registry.py            # Tool registry
├── observability.py       # Latency decorator for all tools
├── memory/
│   ├── base_memory.py     # Abstract memory interface
│   ├── redis_cache.py     # Session memory (TTL 1hr)
│   └── qdrant_store.py    # Long-term vector memory
├── models/
│   ├── base_model.py      # Abstract LLM interface
│   ├── llamacpp_backend.py
│   └── vllm_backend.py
├── tools/
│   ├── base_tool.py
│   ├── price_tool.py
│   ├── fundamentals_tool.py
│   ├── news_tool.py
│   ├── watchlist_read.py
│   └── watchlist_write.py
└── ui/                    # (in progress)
```

---

## Setup

### Prerequisites

- Python 3.10+
- Docker (for Redis)
- CUDA-compatible GPU *(optional — CPU fallback works)*
- GGUF model file (e.g. Phi-3 Mini Q4)

### Install

```bash
git clone https://github.com/YOUR_USERNAME/prajna-finance-agent.git
cd prajna-finance-agent
pip install -r requirements.txt
```

### Environment

Create a `.env` file:

```env
ALPHA_VANTAGE_API_KEY=your_key_here
```

### Start Redis

```bash
docker run -d -p 6379:6379 -p 8001:8001 redis/redis-stack
```

### Run

```bash
uvicorn main:app --reload
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Lists all registered tools |
| `/price/{symbol}` | GET | Live NSE/BSE price |
| `/watchlist` | GET | Read current watchlist |
| `/chat` | POST | Agent chat (ReAct loop) |

### Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current price of RELIANCE?", "session_id": "user-123"}'
```

---

## Status

| Component | Status |
|---|---|
| FastAPI + tools | ✅ Done |
| ReAct agent loop | ✅ Done |
| Redis session memory | ✅ Done |
| Qdrant long-term memory | 🔄 In progress |
| Local LLM (llama.cpp) | ✅ Done |
| End-to-end testing | 🔄 In progress |
| UI | 🔄 In progress |

---

## Author

**Aryan Vithal Gawade**  
B.E. AI & Data Science — DMCE, Navi Mumbai  
[LinkedIn](https://linkedin.com/in/YOUR_PROFILE) · [GitHub](https://github.com/YOUR_USERNAME)
