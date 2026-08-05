import os
import httpx
from typing import Any

from tools.base_tool import BaseTool
from observability import observe


AV_BASE = "https://www.alphavantage.co/query"


class PriceTool(BaseTool):
    name = "get_price"
    description = "Fetch real-time quote for an NSE/BSE symbol. Returns price, change%, volume."

    def __init__(self):
        self._api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    @observe
    async def run(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        try:
            return await self._alpha_vantage(symbol)
        except Exception as primary_err:
            try:
                return await self._yfinance_fallback(symbol)
            except Exception as fallback_err:
                return {
                    "status": "error",
                    "symbol": symbol,
                    "error": f"primary={primary_err} | fallback={fallback_err}",
                }

    async def _alpha_vantage(self, symbol: str) -> dict:
        av_symbol = symbol if "." in symbol else f"{symbol}.BSE"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": av_symbol,
            "apikey": self._api_key,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(AV_BASE, params=params)
            r.raise_for_status()
            data = r.json()

        quote = data.get("Global Quote", {})
        if not quote or not quote.get("05. price"):
            raise ValueError(f"Empty quote from Alpha Vantage for {av_symbol}")

        return {
            "status": "ok",
            "source": "alpha_vantage",
            "symbol": symbol,
            "price": float(quote["05. price"]),
            "change_pct": float(quote["10. change percent"].strip("%")),
            "volume": int(quote["06. volume"]),
            "prev_close": float(quote["08. previous close"]),
        }

    async def _yfinance_fallback(self, symbol: str) -> dict:
        import yfinance as yf

        yf_symbol = symbol if "." in symbol else f"{symbol}.NS"
        ticker = yf.Ticker(yf_symbol)
        info = ticker.fast_info
        price = info.last_price
        prev = info.previous_close
        if not price:
            raise ValueError(f"yfinance returned no price for {yf_symbol}")

        return {
            "status": "ok",
            "source": "yfinance_fallback",
            "symbol": symbol,
            "price": float(price),
            "change_pct": round((price - prev) / prev * 100, 2) if prev else None,
            "volume": int(info.three_month_average_volume or 0),
            "prev_close": float(prev) if prev else None,
        }