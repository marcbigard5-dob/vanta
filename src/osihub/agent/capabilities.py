"""Default-deny registry for external and internal OMNIA capabilities.

Registration is metadata-only. This module never loads or executes a tool.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

_ID = re.compile(r"^[a-z][a-z0-9_.-]{1,79}$")
_RISKS = {"low", "medium", "high", "critical"}
_ALLOWED_PERMISSIONS = {"network", "filesystem_read", "filesystem_write", "secrets", "browser", "process"}


class CapabilityError(ValueError):
    pass


class CapabilityRegistry:
    def __init__(self, path: str | Path | None = None):
        self.path = str(path or os.getenv("OMNIA_DB", "omnia.sqlite3"))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True) if self.path != ":memory:" else None
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    input_schema TEXT NOT NULL,
                    output_schema TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    reviewed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _validate(manifest: dict[str, Any]) -> dict[str, Any]:
        required = {"id", "name", "description", "source_url", "source_version",
                    "input_schema", "output_schema", "risk", "permissions"}
        missing = required - manifest.keys()
        if missing:
            raise CapabilityError("Missing manifest fields: " + ", ".join(sorted(missing)))
        item = dict(manifest)
        if not isinstance(item["id"], str) or not _ID.fullmatch(item["id"]):
            raise CapabilityError("id must be a lowercase stable identifier")
        for field in ("name", "description", "source_url", "source_version"):
            if not isinstance(item[field], str) or not item[field].strip() or len(item[field]) > 2000:
                raise CapabilityError(f"{field} must be a non-empty string of at most 2000 characters")
        if item["risk"] not in _RISKS:
            raise CapabilityError("risk must be low, medium, high, or critical")
        if not isinstance(item["permissions"], list) or any(
            p not in _ALLOWED_PERMISSIONS for p in item["permissions"]
        ):
            raise CapabilityError("permissions contains an unsupported permission")
        for field in ("input_schema", "output_schema"):
            if not isinstance(item[field], dict):
                raise CapabilityError(f"{field} must be a JSON object")
            if len(json.dumps(item[field])) > 20000:
                raise CapabilityError(f"{field} is too large")
        return item

    def register(self, manifest: dict[str, Any]) -> dict:
        item = self._validate(manifest)
        from .store import utc_now
        with self.connect() as db:
            db.execute("""
                INSERT INTO capabilities(
                    capability_id,name,description,source_url,source_version,input_schema,
                    output_schema,risk,permissions,enabled,reviewed,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,0,0,?)
                ON CONFLICT(capability_id) DO UPDATE SET
                    name=excluded.name, description=excluded.description,
                    source_url=excluded.source_url, source_version=excluded.source_version,
                    input_schema=excluded.input_schema, output_schema=excluded.output_schema,
                    risk=excluded.risk, permissions=excluded.permissions,
                    enabled=0, reviewed=0
            """, (item["id"], item["name"], item["description"], item["source_url"],
                  item["source_version"], json.dumps(item["input_schema"]),
                  json.dumps(item["output_schema"]), item["risk"],
                  json.dumps(sorted(set(item["permissions"]))), utc_now()))
        return self.get(item["id"])

    def get(self, capability_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM capabilities WHERE capability_id=?",
                             (capability_id,)).fetchone()
        return self._decode(row) if row else None

    def list(self, limit: int = 100) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM capabilities ORDER BY capability_id LIMIT ?",
                              (limit,)).fetchall()
        return [self._decode(row) for row in rows]

    def set_enabled(self, capability_id: str, enabled: bool, reviewed: bool = False) -> dict | None:
        if enabled and reviewed is not True:
            raise CapabilityError("Explicit review confirmation is required to enable a capability")
        with self.connect() as db:
            db.execute("UPDATE capabilities SET enabled=?, reviewed=? WHERE capability_id=?",
                       (int(enabled), int(bool(enabled and reviewed)), capability_id))
        return self.get(capability_id)

    @staticmethod
    def _decode(row) -> dict:
        item = dict(row)
        item["input_schema"] = json.loads(item["input_schema"])
        item["output_schema"] = json.loads(item["output_schema"])
        item["permissions"] = json.loads(item["permissions"])
        item["enabled"] = bool(item["enabled"])
        item["reviewed"] = bool(item["reviewed"])
        return item
