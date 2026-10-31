# OMNIA — Autonomous AI Workspace

OMNIA is the planned evolution of this repository into a supervised, tool-using AI workspace. The goal is simple: describe a task in natural language, let OMNIA plan and execute it using selected models and tools, verify the result, and return useful artifacts.

## Product direction

- Responsive web interface for phones and computers.
- High autonomy with approval gates for sensitive actions.
- Hybrid AI: local models through Ollama and optional external model APIs.
- Broad capabilities: software engineering, research, design, data analysis and automation.
- Local-first data handling, explicit tool permissions and auditable execution.

## How the listed projects fit

- **Ollama:** local model runtime.
- **Langflow:** optional visual workflow authoring and interoperability.
- **OpenHands:** isolated software-engineering execution adapter.
- **Awesome MCP Servers:** discovery catalogue for candidate tool integrations.
- **Public APIs:** discovery catalogue for service integrations.
- **Scrapling:** optional web extraction component.
- **Open Design:** design workflow reference and possible adapter.
- **Awesome LLM Apps** and **Awesome:** research and reference catalogues.
- **Free-for-dev:** discovery catalogue for services with free tiers.

These projects are not all embedded as dependencies. Some are catalogues, some are runtimes, and some are reference implementations. Every executable integration must be reviewed, licensed appropriately, configured and explicitly enabled.

## Important limitations

OMNIA does not promise an unlimited free hosted API. Local inference through Ollama avoids per-call API charges but depends on available hardware, memory and speed. External free tiers may have quotas and changing terms.

Discovered tools are not automatically trusted or executed. Untrusted code must run in an isolated, resource-limited environment. Purchases, publishing, deletion, account changes and other consequential external actions require user approval.

## Current repository status

This repository currently contains the initial Open Source Intelligence Hub catalogue-indexing foundation. It is **not yet** a working autonomous agent platform. The OMNIA architecture and staged roadmap define the intended transition; implementation and verification will happen milestone by milestone.

## Documentation

- [OMNIA architecture](docs/OMNIA_ARCHITECTURE.md)
- [Implementation roadmap](docs/OMNIA_ROADMAP.md)
- [Master technical specification](docs/OMNIA_MASTER_SPEC.md)
- [Upstream integration audit](docs/OMNIA_UPSTREAM_AUDIT.md)

## Existing catalogue prototype

The existing Python prototype can index configured public catalogues into a local SQLite database. See the earlier CLI and source configuration for its current commands. Its catalogue capability is intended to become one subsystem of OMNIA, not the product's final purpose.


## OMNIA API — first working foundation

The first backend milestone adds a task API and an Ollama-backed planning adapter. It creates and persists task records, asks a configured local Ollama model to produce a bounded plan, classifies plan-step risk, and requires approval when a plan contains medium/high-risk steps.

This is **planning only**: arbitrary tool execution, browser control, code execution and the web UI are not enabled yet.

### Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
# Start Ollama separately and pull a model, for example:
ollama pull llama3.2
omnia-api
```

The API listens on `http://127.0.0.1:8000` by default. Set `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OMNIA_DB`, `OMNIA_HOST` or `OMNIA_PORT` to configure it.

### Initial endpoints

- `GET /health`
- `POST /api/tasks` with JSON `{"prompt":"..." }`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/plan`
- `POST /api/tasks/{task_id}/approve`

Interactive API documentation is available at `/docs` when the server is running. A task plan does not mean its steps have been executed.
