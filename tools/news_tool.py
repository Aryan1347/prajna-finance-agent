import os
import json
import httpx
import redis.asyncio as aioredis
from typing import Any

from tools.base_tool import BaseTool
from observability import observe


AV_BASE = "https://www.alphavantage.co/query"
CACHE_TTL = 900  # 15 minutes


class NewsTool(BaseTool):
    name = "get_news"
    description = "Fetch latest news + sentiment for a symbol. Returns top 5 articles."

    def __init__(self):
        self._api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    @observe
    async def run(self, symbol: str, limit: int = 5) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        cache_key = f"news:{symbol}"

        r = await self._get_redis()
        cached = await r.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["cache"] = "hit"
            return data

        result = await self._fetch(symbol, limit)
        await r.setex(cache_key, CACHE_TTL, json.dumps(result))
        result["cache"] = "miss"
        return result

    async def _fetch(self, symbol: str, limit: int) -> dict:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "limit": limit,
            "apikey": self._api_key,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(AV_BASE, params=params)
            r.raise_for_status()
            data = r.json()

        feed = data.get("feed", [])
        articles = []
        for item in feed[:limit]:
            ticker_sentiments = {
                t["ticker"]: t["ticker_sentiment_label"]
                for t in item.get("ticker_sentiment", [])
            }
            articles.append({
                "title": item.get("title"),
                "source": item.get("source"),
                "url": item.get("url"),
                "published": item.get("time_published"),
                "overall_sentiment": item.get("overall_sentiment_label"),
                "ticker_sentiment": ticker_sentiments.get(symbol),
            })

        return {
            "status": "ok",
            "source": "alpha_vantage",
            "symbol": symbol,
            "articles": articles,
        }