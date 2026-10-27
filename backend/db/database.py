"""
db/database.py
SQLite database using aiosqlite for async access.
Stores mission events for persistent history.
"""
from __future__ import annotations
import aiosqlite
import time
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "robomind.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mission_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT,
                timestamp REAL NOT NULL
            )
        """)
        await db.commit()


async def save_mission_event(mission_id: str, event_type: str, data: dict = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO mission_events (mission_id, event_type, data, timestamp) VALUES (?, ?, ?, ?)",
            (mission_id, event_type, json.dumps(data or {}), time.time()),
        )
        await db.commit()


async def get_mission_history(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM mission_events ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "mission_id": row["mission_id"],
                "event_type": row["event_type"],
                "data": json.loads(row["data"] or "{}"),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
