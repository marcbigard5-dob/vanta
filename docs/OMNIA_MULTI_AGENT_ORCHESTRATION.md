# OMNIA Multi-Agent Orchestration

## Execution contract

A task is first created and planned through the existing task API. A plan that contains medium/high-risk steps enters `awaiting_approval`; the coordinator refuses to start it until the task has been approved.

The coordinator converts each approved plan step into one specialist assignment:

- Research Specialist
- Engineering Specialist
- Analysis Specialist
- Design Specialist
- General Specialist

Assignments execute in plan order. This is an intentionally conservative sequential DAG: each step may consume bounded summaries from preceding steps, while future work can add explicit dependency edges and parallel scheduling without changing the persisted run/step/event contract.

## API

1. `POST /api/tasks` with `{"prompt":"..."}`
2. `POST /api/tasks/{task_id}/plan`
3. If status is `awaiting_approval`, approve via `POST /api/tasks/{task_id}/approve`.
4. `POST /api/tasks/{task_id}/run` starts the specialist pipeline.
5. `GET /api/agent-runs/{run_id}` returns ordered steps and an append-only event history.

## Safety and truthfulness

- Maximum 8 steps per run by default.
- Specialist selection is deterministic and auditable.
- Model provider routing is explicit by task class; failures do not silently fall back.
- Prior agent output is labeled untrusted context.
- No shell, arbitrary Python, MCP, browser, filesystem, or external API execution is enabled by this coordinator.
- The coordinator does not treat model text as evidence of an action.
- `verified` remains false for every result until a separate verifier with evidence checks is implemented.
- A failed specialist marks the run failed; completed earlier outputs remain available for diagnosis.

## Current boundary

This is the orchestration core, not yet the complete autonomous execution fabric. Next integrations must be registered as reviewed capabilities, run in isolated workers, enforce manifest permissions, use action-bound approvals for side effects, and emit verifiable evidence.
