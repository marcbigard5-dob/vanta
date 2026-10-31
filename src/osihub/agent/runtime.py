"""Bounded agent runtime. Only explicitly registered Python handlers can run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .capabilities import CapabilityRegistry


class RuntimeErrorBase(RuntimeError):
    pass


@dataclass(frozen=True)
class HandlerSpec:
    capability_id: str
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    max_output_chars: int = 12000


class AgentRuntime:
    """A safe execution seam; it does not spawn processes, load plugins, or run shell commands."""
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self._handlers: dict[str, HandlerSpec] = {}

    def register_handler(self, capability_id: str,
                         handler: Callable[[dict[str, Any]], dict[str, Any]],
                         *, max_output_chars: int = 12000) -> None:
        if capability_id in self._handlers:
            raise RuntimeErrorBase("A handler is already registered for this capability")
        if not callable(handler) or not 100 <= max_output_chars <= 50000:
            raise RuntimeErrorBase("Invalid handler or output bound")
        self._handlers[capability_id] = HandlerSpec(capability_id, handler, max_output_chars)

    def execute(self, capability_id: str, arguments: dict[str, Any], *,
                approval_status: str | None = None) -> dict[str, Any]:
        manifest = self.registry.get(capability_id)
        if manifest is None:
            raise RuntimeErrorBase("Unknown capability")
        if not manifest["enabled"] or not manifest["reviewed"]:
            raise RuntimeErrorBase("Capability is disabled or not reviewed")
        if manifest["risk"] in {"medium", "high", "critical"} and approval_status != "approved":
            raise RuntimeErrorBase("A matching approved action is required")
        spec = self._handlers.get(capability_id)
        if spec is None:
            raise RuntimeErrorBase("No trusted in-process handler is registered")
        result = spec.handler(arguments)
        if not isinstance(result, dict):
            raise RuntimeErrorBase("Handler must return a JSON object")
        import json
        try:
            encoded = json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise RuntimeErrorBase("Handler returned non-JSON data") from exc
        if len(encoded) > spec.max_output_chars:
            raise RuntimeErrorBase("Handler output exceeded configured limit")
        return {"capability_id": capability_id, "status": "completed",
                "result": result, "verified": False,
                "verification_note": "Handler completion is not independent verification"}
