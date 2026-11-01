"""Persistent task store for the OMNIA API."""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStore:
    def __init__(self, path: str | Path | None = None):
        self.path = str(path or os.getenv("OMNIA_DB", "omnia.sqlite3"))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True) if self.path != ":memory:" else None
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, prompt TEXT NOT NULL, status TEXT NOT NULL,
                plan_json TEXT NOT NULL DEFAULT '[]', provider TEXT NOT NULL DEFAULT '',
                approval_required INTEGER NOT NULL DEFAULT 0, approval_granted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, error TEXT NOT NULL DEFAULT ''
            )""")

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def create(self, prompt: str) -> dict:
        task_id, now = str(uuid.uuid4()), utc_now()
        with self.connect() as db:
            db.execute("INSERT INTO tasks(id,prompt,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                       (task_id, prompt, "draft", now, now))
        return self.get(task_id)

    def get(self, task_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return self._decode(row) if row else None

    def list(self, limit: int = 50) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._decode(row) for row in rows]

    def update_plan(self, task_id: str, plan: list[dict], provider: str, approval_required: bool) -> dict:
        status = "awaiting_approval" if approval_required else "planned"
        with self.connect() as db:
            db.execute("""UPDATE tasks SET plan_json=?,provider=?,status=?,approval_required=?,
                approval_granted=0,error='',updated_at=? WHERE id=?""",
                (json.dumps(plan), provider, status, int(approval_required), utc_now(), task_id))
        return self.get(task_id)

    def set_status(self, task_id: str, status: str, error: str = "") -> dict | None:
        with self.connect() as db:
            db.execute("UPDATE tasks SET status=?,error=?,updated_at=? WHERE id=?",
                       (status, error, utc_now(), task_id))
        return self.get(task_id)

    def approve(self, task_id: str) -> dict | None:
        with self.connect() as db:
            db.execute("""UPDATE tasks SET approval_granted=1,status='approved',updated_at=?
                WHERE id=? AND status='awaiting_approval' AND approval_required=1""", (utc_now(), task_id))
        return self.get(task_id)

    @staticmethod
    def _decode(row) -> dict:
        item = dict(row)
        item["plan"] = json.loads(item.pop("plan_json"))
        item["approval_required"] = bool(item["approval_required"])
        item["approval_granted"] = bool(item["approval_granted"])
        return item
