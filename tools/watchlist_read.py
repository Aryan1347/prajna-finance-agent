import os
import sqlite3
from typing import Any

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


class WatchlistReadTool(BaseTool):
    name = "read_watchlist"
    description = "Return all symbols currently in the user's watchlist."

    @observe
    async def run(self) -> dict[str, Any]:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT symbol, added_at, note FROM watchlist ORDER BY added_at DESC"
        ).fetchall()
        conn.close()
        return {
            "status": "ok",
            "watchlist": [
                {"symbol": r[0], "added_at": r[1], "note": r[2]} for r in rows
            ],
        }