import os
"""
Thin SQLite persistence layer.

Schema
------
watches
    id          INTEGER PK
    chat_id     INTEGER        — Telegram chat that owns this watch
    url         TEXT           — URL of the library item page
    libraries   TEXT           — JSON list of library names the user selected
    created_at  TEXT           — ISO-8601 timestamp

Everything is synchronous / called from async context with run_in_executor
where latency matters, but for a low-traffic bot plain sync is fine.
"""

import json
import sqlite3
from typing import Optional
from config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Call once at startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watches (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id     INTEGER NOT NULL,
                url         TEXT    NOT NULL,
                libraries   TEXT    NOT NULL,  -- JSON list
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def add_watch(chat_id: int, url: str, libraries: list[str]) -> int:
    """Insert a new watch and return its id."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO watches (chat_id, url, libraries) VALUES (?, ?, ?)",
            (chat_id, url, json.dumps(libraries)),
        )
        conn.commit()
        return cur.lastrowid


def delete_watch(watch_id: int, chat_id: int) -> bool:
    """Delete a watch owned by chat_id. Returns True if a row was deleted."""
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM watches WHERE id = ? AND chat_id = ?",
            (watch_id, chat_id),
        )
        conn.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def get_watches_for_chat(chat_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM watches WHERE chat_id = ?", (chat_id,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_all_watches() -> list[dict]:
    """Used by the scheduler to iterate over every active watch."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM watches").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_watch(watch_id: int) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM watches WHERE id = ?", (watch_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["libraries"] = json.loads(d["libraries"])
    return d
