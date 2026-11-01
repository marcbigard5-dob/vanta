# OMNIA Execution Engine

## Request lifecycle

1. A capability is registered as metadata only and starts disabled/unreviewed.
2. A reviewer explicitly enables it after reviewing its source, version, schemas, permissions and risk.
3. Trusted application code registers a handler for that capability ID. The public API cannot upload Python code or register arbitrary handlers.
4. An execution request is checked against the capability input schema.
5. Medium/high/critical capabilities require an approved ledger record whose digest matches the exact capability ID, target, arguments, permissions and source version.
6. The runtime invokes the registered handler and enforces JSON-object output and output-size limits.
7. The engine validates output against the capability output schema and persists an execution record.

## API

- `POST /api/executions` — invoke an enabled capability with JSON arguments; include `approval_id` for medium/high/critical risk.
- `GET /api/executions/{execution_id}` — inspect the persisted execution record.
- Existing `POST /api/approvals` and `POST /api/approvals/{id}/decision` manage exact-action approvals.

Example request body:

```json
{
  "capability_id": "internal.example",
  "target": "local",
  "arguments": {"query": "example"},
  "approval_id": null
}
```

## Current supported boundary

The engine supports a fail-closed JSON Schema subset: types, required properties, properties, additionalProperties=false, enum, string lengths, and array item/count limits. It does not claim full JSON Schema Draft conformance.

Handlers are registered only by trusted in-process application code. The engine does not dynamically load plugins, execute shell commands, use eval, start subprocesses, or expose unrestricted network access. No third-party MCP, Scrapling, OpenHands, or browser adapter is registered yet; those integrations must each be implemented and tested behind isolated workers and capability manifests.

Execution status means the handler returned and its output passed schema validation. It does not mean the result is factually correct; `verified` remains false pending an independent evidence-based verifier.
