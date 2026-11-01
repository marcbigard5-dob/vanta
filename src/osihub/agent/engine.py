"""Policy-enforced execution engine for reviewed, explicitly registered handlers.

This engine is an execution boundary, not a plugin loader. Handlers must be
registered by trusted application code. No shell, eval, dynamic imports, or
arbitrary network execution is exposed by this module.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .capabilities import CapabilityRegistry
from .policy import ApprovalLedger, action_digest
from .runtime import AgentRuntime, RuntimeErrorBase


class ExecutionError(RuntimeError):
    pass


def _matches_type(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }
    return checks.get(expected, lambda _v: False)(value)


def validate_schema(value: Any, schema: dict, path: str = "$") -> None:
    """Validate a deliberately small, fail-closed JSON Schema subset."""
    if not isinstance(schema, dict):
        raise ExecutionError("Capability schema must be an object")
    expected = schema.get("type")
    if expected and not _matches_type(value, expected):
        raise ExecutionError(f"{path} must be {expected}")
    if "enum" in schema and value not in schema["enum"]:
        raise ExecutionError(f"{path} is not an allowed value")
    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list) or any(not isinstance(k, str) for k in required):
            raise ExecutionError("Invalid schema required list")
        missing = set(required) - value.keys()
        if missing:
            raise ExecutionError(f"{path} missing required fields: {', '.join(sorted(missing))}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ExecutionError("Invalid schema properties")
        if schema.get("additionalProperties") is False:
            extra = value.keys() - properties.keys()
            if extra:
                raise ExecutionError(f"{path} contains unsupported fields: {', '.join(sorted(extra))}")
        for key, child in properties.items():
            if key in value:
                validate_schema(value[key], child, f"{path}.{key}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ExecutionError(f"{path} has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ExecutionError(f"{path} has too many items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_schema(item, item_schema, f"{path}[{index}]")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ExecutionError(f"{path} is too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ExecutionError(f"{path} is too long")


class ExecutionEngine:
    def __init__(self, registry: CapabilityRegistry, approvals: ApprovalLedger,
                 runtime: AgentRuntime, db_path: str):
        self.registry, self.approvals, self.runtime = registry, approvals, runtime
        self.db_path = str(db_path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS execution_records (
                execution_id TEXT PRIMARY KEY, capability_id TEXT NOT NULL,
                action_digest TEXT NOT NULL, status TEXT NOT NULL,
                result_json TEXT NOT NULL DEFAULT '{}', error TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, finished_at TEXT NOT NULL DEFAULT ''
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS approval_consumptions (
                approval_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL UNIQUE,
                consumed_at TEXT NOT NULL
            )""")

    def _connect(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def execute(self, capability_id: str, arguments: dict[str, Any], *,
                target: str = "local", approval_id: str | None = None) -> dict:
        manifest = self.registry.get(capability_id)
        if manifest is None:
            raise ExecutionError("Unknown capability")
        if not manifest["enabled"] or not manifest["reviewed"]:
            raise ExecutionError("Capability is disabled or not reviewed")
        if not isinstance(arguments, dict):
            raise ExecutionError("arguments must be a JSON object")
        validate_schema(arguments, manifest["input_schema"])
        digest = action_digest(capability_id, target, arguments,
                               manifest["permissions"], manifest["source_version"])
        approval_status = None
        if manifest["risk"] in {"medium", "high", "critical"}:
            if not approval_id:
                raise ExecutionError("An approval for this exact action is required")
            approval = self.approvals.get(approval_id)
            if not approval or approval["status"] != "approved":
                raise ExecutionError("Approval is missing, pending, or rejected")
            if approval["digest"] != digest:
                raise ExecutionError("Approval does not match the exact action parameters")
            action = approval["action"]
            if (action["capability_id"] != capability_id or action["target"] != target
                or action["capability_version"] != manifest["source_version"]
                or sorted(action["permissions"]) != sorted(manifest["permissions"])
                or action["risk"] != manifest["risk"]):
                raise ExecutionError("Approval scope or capability version has changed")
            approval_status = "approved"
        execution_id, now = str(uuid.uuid4()), datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            if approval_id:
                try:
                    db.execute("""INSERT INTO approval_consumptions
                        (approval_id,execution_id,consumed_at) VALUES(?,?,?)""",
                        (approval_id, execution_id, now))
                except sqlite3.IntegrityError as exc:
                    raise ExecutionError("Approval has already been consumed") from exc
            db.execute("""INSERT INTO execution_records
                (execution_id,capability_id,action_digest,status,created_at)
                VALUES(?,?,?,?,?)""", (execution_id, capability_id, digest, "running", now))
        try:
            outcome = self.runtime.execute(capability_id, arguments, approval_status=approval_status)
            validate_schema(outcome["result"], manifest["output_schema"])
            encoded = json.dumps(outcome["result"], ensure_ascii=False)
            finished = datetime.now(timezone.utc).isoformat()
            with self._connect() as db:
                db.execute("""UPDATE execution_records SET status='completed',result_json=?,finished_at=?
                              WHERE execution_id=?""", (encoded, finished, execution_id))
            return {"execution_id": execution_id, "capability_id": capability_id,
                    "status": "completed", "result": outcome["result"], "verified": False,
                    "verification_note": "Execution completion is not independent verification"}
        except Exception as exc:
            finished = datetime.now(timezone.utc).isoformat()
            with self._connect() as db:
                db.execute("""UPDATE execution_records SET status='failed',error=?,finished_at=?
                              WHERE execution_id=?""", (str(exc)[:1000], finished, execution_id))
            if isinstance(exc, (ExecutionError, RuntimeErrorBase)):
                raise ExecutionError(str(exc)) from exc
            raise ExecutionError("Capability handler failed") from exc

    def get_execution(self, execution_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM execution_records WHERE execution_id=?",
                             (execution_id,)).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json"))
        return item
