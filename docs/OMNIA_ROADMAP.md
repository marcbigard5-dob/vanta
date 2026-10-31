# OMNIA Delivery Roadmap

## Milestone 0 — Direction and architecture
- [x] Confirm responsive web, supervised autonomy, hybrid models and broad task scope.
- [x] Define trust boundaries and upstream project roles.
- [ ] Review upstream licences and integration compatibility individually.

## Milestone 1 — Working agent foundation
- [ ] FastAPI application with health and version endpoints.
- [ ] Persistent task/session models and SQLite repository.
- [ ] Task lifecycle: queued, planning, awaiting approval, running, verifying, completed, failed, cancelled.
- [ ] Provider interface and Ollama adapter.
- [ ] Optional OpenAI-compatible provider adapter, disabled until configured.
- [ ] Orchestrator with bounded plans, step state, cancellation and retry limits.
- [ ] Web UI: prompt composer, task timeline, approval panel and result view.
- [ ] Automated unit and integration tests; CI for backend and frontend.

## Milestone 2 — Safe tool system
- [ ] Tool manifest and registry.
- [ ] JSON-schema input validation.
- [ ] Risk classification and approval policy.
- [ ] Audit events and structured execution logs.
- [ ] MCP client adapter; tools are explicitly reviewed and enabled.
- [ ] Network and filesystem permission controls.

## Milestone 3 — Research and knowledge
- [ ] Web search / retrieval adapter.
- [ ] Optional Scrapling integration with domain, rate and policy controls.
- [ ] Source citations and evidence tracking.
- [ ] Document ingestion and retrieval (RAG).
- [ ] API and free-tier catalogue importers; validate current terms and quotas.

## Milestone 4 — Software factory
- [ ] Isolated execution worker.
- [ ] OpenHands adapter.
- [ ] Workspace and artifact management.
- [ ] Test, repair and verification loop with a strict attempt budget.
- [ ] Git integration with explicit approval before push, PR or deployment.

## Milestone 5 — Design and workflow studio
- [ ] Design workflow adapter informed by Open Design.
- [ ] Visual workflow authoring / optional Langflow interoperability.
- [ ] Reusable task templates and scheduled jobs.
- [ ] Data analysis and automation tools.

## Milestone 6 — Hardening and deployment
- [ ] Authentication and per-user authorization for hosted deployments.
- [ ] Secret management, rate limits and abuse controls.
- [ ] Container resource limits and security tests.
- [ ] Backup, restore, observability and upgrade documentation.
- [ ] Local, self-hosted and hybrid deployment guides.

## Release gates

A milestone is not complete merely because files exist. It must have:
- tests that execute in CI;
- documented setup and configuration;
- clear known limitations;
- no false claims about provider quotas, model capability or task completion;
- approval and isolation controls appropriate to its capabilities.
