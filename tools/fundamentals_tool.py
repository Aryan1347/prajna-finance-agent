import os
import json
import httpx
import asyncio
import redis.asyncio as aioredis
from typing import Any

from tools.base_tool import BaseTool
from observability import observe


AV_BASE = "https://www.alphavantage.co/query"
CACHE_TTL = 3600  # 1 hour


class FundamentalsTool(BaseTool):
    name = "get_fundamentals"
    description = "Fetch company overview — P/E, EPS, market cap, sector, 52w high/low."

    def __init__(self):
        self._api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    @observe
    async def run(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        cache_key = f"fundamentals:{symbol}"

        r = await self._get_redis()
        cached = await r.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["cache"] = "hit"
            return data

        result = await self._fetch(symbol)
        await r.setex(cache_key, CACHE_TTL, json.dumps(result))
        result["cache"] = "miss"
        return result

    async def _fetch(self, symbol: str) -> dict:
        av_symbol = symbol if "." in symbol else f"{symbol}.BSE"
        params = {
            "function": "OVERVIEW",
            "symbol": av_symbol,
            "apikey": self._api_key,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(AV_BASE, params=params)
            r.raise_for_status()
            data = r.json()

        if not data or "Symbol" not in data:
            raise ValueError(f"No overview data for {av_symbol}")

        return {
            "status": "ok",
            "source": "alpha_vantage",
            "symbol": symbol,
            "name": data.get("Name"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "eps": data.get("EPS"),
            "week_52_high": data.get("52WeekHigh"),
            "week_52_low": data.get("52WeekLow"),
            "dividend_yield": data.get("DividendYield"),
        }