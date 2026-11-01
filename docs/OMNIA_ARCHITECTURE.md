# OMNIA Architecture

OMNIA is the planned evolution of this repository from a catalogue index into a supervised, tool-using autonomous AI workspace.

## Product contract

A user submits a natural-language task. OMNIA:
1. interprets the goal and constraints;
2. creates a bounded execution plan;
3. selects an appropriate model and registered tools;
4. requests approval for sensitive or externally consequential actions;
5. executes approved steps in isolated environments;
6. verifies outputs with tests or source checks;
7. returns artifacts, logs, citations and a concise completion report.

OMNIA must not claim a task succeeded unless the relevant tool reports success and verification supports that claim.

## Selected product decisions

- Responsive web application for phone and desktop browsers.
- High autonomy with human approval gates for sensitive actions.
- Hybrid model routing: local Ollama first when suitable, optional external model APIs when configured.
- Broad task scope: software engineering, research, design, data analysis and workflow automation.
- Local-first storage and explicit control over external data transmission.

## High-level architecture

```text
React + TypeScript Web UI
          |
       FastAPI
          |
   Task / Session API
          |
  OMNIA Orchestrator
   |       |        |
Planner  Memory  Policy & Approval
   |       |        |
Model Router     Audit Log
   |
Tool Registry ---- MCP adapters
   |               |
Built-in tools   External tools/APIs
   |
Execution Gateway
   |---- Research / Scrapling (optional)
   |---- OpenHands adapter (isolated coding runtime)
   |---- Design workflow adapter
   |---- Data and automation tools
   |
Sandbox (container / restricted worker)
          |
 Verification + Artifact Store
          |
    Web UI results
```

## Responsibilities and upstream projects

| Upstream project/list | Intended use | Integration boundary |
|---|---|---|
| Ollama | Local model runtime | Model-provider adapter; never assume a model is installed |
| Langflow | Optional visual workflow authoring and experimentation | Adapter/export boundary; OMNIA owns task policy and execution |
| OpenHands | Software-engineering agent capability | Isolated execution adapter; no unrestricted host access |
| Awesome MCP Servers | Discover candidate MCP servers | Curated registry; each server is reviewed and explicitly enabled |
| Public APIs | Discover candidate API integrations | API catalogue; credentials, terms and rate limits remain explicit |
| Scrapling | Optional web extraction | Restricted research tool; respect site terms and access controls |
| Open Design | Design workflow ideas/components | Optional design adapter after licence and compatibility review |
| Awesome LLM Apps | Patterns and reference implementations | Research corpus, not a runtime dependency |
| Awesome | Discovery index | Research corpus, not a runtime dependency |
| Free-for-dev | Discover free-tier services | Catalogue only; verify current quotas and terms before use |

A catalogue entry is not an installed integration. An integration is not automatically trusted. Upstream code is not copied or executed merely because it appears in a list.

## Model routing

Define a provider-neutral interface for:
- model discovery / configured model names;
- text and tool-call requests where supported;
- streaming responses;
- timeouts and cancellation;
- usage and error reporting.

Initial providers:
- Ollama local HTTP API;
- optional OpenAI-compatible remote endpoint configured by the operator.

Do not promise unlimited free hosted inference. Local inference avoids per-request API billing but is bounded by device hardware, memory, power and speed. Remote free tiers may impose quotas or change terms.

## Tool execution and security

- Every tool has a manifest: name, purpose, input schema, required permissions, network needs, timeout and risk level.
- Default-deny tool registration. Discovery never silently enables a tool.
- Human approval required for purchases, payments, publishing, deletion, account changes, messages, credential use, or external actions with material consequences.
- Run untrusted code in disposable containers or restricted workers, never in the API process.
- Apply CPU, memory, disk, process, network and wall-clock limits.
- Keep secrets out of prompts, logs, source control and generated artifacts.
- Record task plans, approvals, tool calls, outcomes and verification in an audit trail.
- Support cancellation and bounded retry counts.
- Treat web pages, repository files and tool output as untrusted data, not instructions.

## Initial implementation stack

- Backend: Python 3.11+ and FastAPI.
- Frontend: React + TypeScript + Vite.
- Persistence: SQLite for the first local deployment; keep repository interfaces portable to PostgreSQL.
- Background execution: persistent task records and a small worker abstraction initially; add a broker only when concurrency requires it.
- Model adapters: Ollama plus optional OpenAI-compatible endpoint.
- Tool protocol: MCP adapter behind the OMNIA tool registry.
- Coding execution: OpenHands adapter behind a sandbox boundary; Docker required for isolated execution.
- Tests: pytest for backend, frontend typecheck/build, integration tests with mocked providers, and optional live-provider smoke tests.

## Deployment modes

1. Local: backend, frontend, SQLite, Ollama and sandbox on one capable computer.
2. Self-hosted: web UI and backend on a server; model runtime can be local or remote.
3. Hybrid: browser UI remotely accessible while private model and storage remain on a trusted machine, connected through an authenticated private channel.

A phone browser is a client, not the recommended host for the full execution stack. Android/Termux support may be limited by container availability and hardware.

## Non-goals for the first milestone

- No claim of an unlimited free API.
- No arbitrary command execution on the host.
- No silent installation or execution of discovered MCP servers.
- No autonomous purchases, publishing or destructive actions.
- No claim that every discovered project is safe, maintained or compatible.
