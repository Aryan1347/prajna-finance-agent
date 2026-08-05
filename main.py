from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from registry import ToolRegistry

app = FastAPI(title="Finance AI Agent", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

registry = ToolRegistry()

from agent import FinanceAgent
import uuid

agent = FinanceAgent()


@app.get("/health")
async def health():
    return {"status": "ok", "tools": list(registry.all())}


@app.get("/price/{symbol}")
async def price(symbol: str):
    return await registry.get("get_price").run(symbol=symbol)


@app.get("/fundamentals/{symbol}")
async def fundamentals(symbol: str):
    return await registry.get("get_fundamentals").run(symbol=symbol)


@app.get("/news/{symbol}")
async def news(symbol: str, limit: int = 5):
    return await registry.get("get_news").run(symbol=symbol, limit=limit)


@app.get("/watchlist")
async def get_watchlist():
    return await registry.get("read_watchlist").run()


class WatchlistRequest(BaseModel):
    action: str
    symbol: str
    note: str = ""
    confirmed: bool = False

@app.post("/watchlist")
async def update_watchlist(body: WatchlistRequest):
    return await registry.get("write_watchlist").run(
        action=body.action,
        symbol=body.symbol,
        note=body.note,
        confirmed=body.confirmed,
    )


@app.post("/chat")
async def chat(body: dict):
    session_id = body.get("session_id") or str(uuid.uuid4())
    query = body.get("query", "")
    result = await agent.run(session_id=session_id, user_query=query)  
    return {"session_id": session_id, **result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.post("/chat")
def chat(body: dict):
    session_id = body.get("session_id") or str(uuid.uuid4())
    query = body.get("query", "")
    result = agent.run(session_id=session_id, user_query=query)
    return {"session_id": session_id, **result}