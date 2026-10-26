"""SQLite persistence: a canonical event ledger plus rebuildable mission snapshots."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from nile_gate.models import EventRecord, MissionRecord

DEFAULT_DB = Path(os.getenv("NILE_GATE_DB_PATH", "data/nile_gate.db"))


class Store:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path), timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    document TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id TEXT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_events_mission ON events(mission_id, id)")

    def save_mission(self, mission: MissionRecord, *, event_type: str, actor: str, payload: dict[str, Any] | None = None) -> MissionRecord:
        document = mission.model_dump_json()
        with self._connect() as db:
            db.execute(
                """INSERT INTO missions(id, document, created_at, updated_at) VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET document=excluded.document, updated_at=excluded.updated_at""",
                (mission.id, document, mission.created_at.isoformat(), mission.updated_at.isoformat()),
            )
            db.execute(
                "INSERT INTO events(mission_id, event_type, actor, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (mission.id, event_type, actor, json.dumps(payload or {}, sort_keys=True), mission.updated_at.isoformat()),
            )
        return mission

    def get_mission(self, mission_id: str) -> MissionRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT document FROM missions WHERE id=?", (mission_id,)).fetchone()
        return MissionRecord.model_validate_json(row["document"]) if row else None

    def list_missions(self, limit: int = 50) -> list[MissionRecord]:
        with self._connect() as db:
            rows = db.execute("SELECT document FROM missions ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [MissionRecord.model_validate_json(row["document"]) for row in rows]

    def list_events(self, mission_id: str | None = None, limit: int = 100) -> list[EventRecord]:
        with self._connect() as db:
            if mission_id:
                rows = db.execute("SELECT * FROM events WHERE mission_id=? ORDER BY id DESC LIMIT ?", (mission_id, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [
            EventRecord(
                id=row["id"], mission_id=row["mission_id"], event_type=row["event_type"],
                actor=row["actor"], payload=json.loads(row["payload"]), created_at=row["created_at"]
            )
            for row in rows
        ]

    def record_event(self, event_type: str, actor: str, payload: dict[str, Any], mission_id: str | None = None) -> None:
        from datetime import datetime, timezone
        with self._connect() as db:
            db.execute(
                "INSERT INTO events(mission_id, event_type, actor, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (mission_id, event_type, actor, json.dumps(payload, sort_keys=True), datetime.now(timezone.utc).isoformat()),
            )
