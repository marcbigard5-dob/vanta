"""Policy primitives for exact-action approvals; no tool execution is performed here."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .store import utc_now


class ApprovalError(ValueError):
    pass


def action_digest(capability_id: str, target: str, arguments: dict[str, Any],
                  permissions: list[str], capability_version: str) -> str:
    """Stable digest binds approval to exact capability, target, args, scope and version."""
    canonical = json.dumps({
        "capability_id": capability_id,
        "target": target,
        "arguments": arguments,
        "permissions": sorted(set(permissions)),
        "capability_version": capability_version,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ApprovalLedger:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS action_approvals (
                    approval_id TEXT PRIMARY KEY,
                    digest TEXT NOT NULL,
                    capability_id TEXT NOT NULL,
                    action_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT NOT NULL DEFAULT ''
                )
            """)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def request(self, capability_id: str, target: str, arguments: dict[str, Any],
                permissions: list[str], capability_version: str, risk: str) -> dict:
        if risk not in {"medium", "high", "critical"}:
            raise ApprovalError("Only medium, high, or critical actions require this approval ledger")
        digest = action_digest(capability_id, target, arguments, permissions, capability_version)
        approval_id = str(uuid.uuid4())
        action = {"capability_id": capability_id, "target": target, "arguments": arguments,
                  "permissions": sorted(set(permissions)), "capability_version": capability_version,
                  "risk": risk, "digest": digest}
        with self.connect() as db:
            db.execute("""INSERT INTO action_approvals
                (approval_id,digest,capability_id,action_json,status,created_at)
                VALUES(?,?,?,?,?,?)""",
                (approval_id, digest, capability_id, json.dumps(action, sort_keys=True),
                 "pending", utc_now()))
        return self.get(approval_id)

    def decide(self, approval_id: str, approved: bool, expected_digest: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM action_approvals WHERE approval_id=?",
                             (approval_id,)).fetchone()
            if row is None:
                return None
            if row["status"] != "pending":
                raise ApprovalError("Approval has already been decided")
            if row["digest"] != expected_digest:
                raise ApprovalError("Action digest mismatch; approval cannot be applied")
            db.execute("""UPDATE action_approvals SET status=?,decided_at=? WHERE approval_id=?
                AND status='pending' AND digest=?""",
                ("approved" if approved else "rejected", utc_now(), approval_id, expected_digest))
        return self.get(approval_id)

    def get(self, approval_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM action_approvals WHERE approval_id=?",
                             (approval_id,)).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["action"] = json.loads(item.pop("action_json"))
        return item
