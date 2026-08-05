import os
import sqlite3
from typing import Any, Literal

from tools.base_tool import BaseTool
from observability import observe


def _get_conn():
    db_path = os.getenv("DB_PATH", "db/watchlist.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            added_at TEXT DEFAULT (datetime('now')),
            note TEXT
        )
    """)
    conn.commit()
    return conn


class WatchlistWriteTool(BaseTool):
    name = "write_watchlist"
    description = (
        "Add or remove a symbol from the watchlist. "
        "REQUIRES confirmed=True — never call without explicit user confirmation."
    )

    @observe
    async def run(
        self,
        action: Literal["add", "remove"],
        symbol: str,
        note: str = "",
        confirmed: bool = False,
    ) -> dict[str, Any]:
        if not confirmed:
            return {
                "status": "needs_confirmation",
                "message": (
                    f"About to {action} '{symbol.upper()}' "
                    f"{'to' if action == 'add' else 'from'} watchlist. Confirm? (yes/no)"
                ),
            }

        symbol = symbol.upper().strip()
        conn = _get_conn()

        if action == "add":
            conn.execute(
                "INSERT OR REPLACE INTO watchlist (symbol, note) VALUES (?, ?)",
                (symbol, note),
            )
            msg = f"Added {symbol} to watchlist."
        elif action == "remove":
            conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
            msg = f"Removed {symbol} from watchlist."
        else:
            conn.close()
            return {"status": "error", "error": f"Unknown action: {action}"}

        conn.commit()
        conn.close()
        return {"status": "ok", "message": msg, "symbol": symbol}