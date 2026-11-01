# OMNIA Master Technical Specification

**Status:** Proposed engineering baseline  
**Product:** OMNIA — Unified Autonomous Intelligence Workspace  
**Repository:** `marcbigard5-dob/vanta`  
**Working branch:** `feature/opensource-intelligence-hub`  
**Document version:** 1.0

## 1. Product definition

OMNIA is a provider-neutral, tool-using autonomous AI workspace. A user describes an outcome in natural language. OMNIA decomposes the request, selects models and approved capabilities, coordinates specialist agents, executes bounded actions, verifies the resulting work, and returns usable artifacts with an auditable explanation.

The product is the **integration and orchestration layer**. The ten upstream projects are capability sources, runtimes, frameworks, or discovery catalogues; they are not ten independent applications placed behind one dashboard.

### 1.1 Product contract

For every task, OMNIA must:
1. capture the user's goal, constraints, and expected deliverables;
2. classify the task and identify missing information;
3. produce a structured, bounded plan;
4. select configured models and explicitly enabled tools;
5. obtain approval before actions classified as sensitive or consequential;
6. execute through controlled adapters and isolated workers;
7. verify outputs using tests, schema checks, source evidence, or other task-specific criteria;
8. deliver artifacts, evidence, execution summary, and known limitations.

OMNIA must distinguish **planned**, **attempted**, **executed**, and **verified**. A plan is never evidence of execution. A tool's success response alone is not always proof that the user's goal was achieved.

### 1.2 Product principles

- User intent first; agents and tools are replaceable implementation details.
- Hybrid inference: local models where suitable, optional remote providers when explicitly configured.
- High autonomy for reversible, low-risk work; human approval for consequential actions.
- Local-first persistence where practical and explicit disclosure of external data transfer.
- Least privilege, default-deny tools, isolated execution, and auditable actions.
- Verifiable deliverables instead of simulated progress or success claims.
- Graceful degradation when a model, tool, API, or upstream project is unavailable.

## 2. The ten upstream projects: integration plan

| Upstream | Category | OMNIA role | Integration approach | Not assumed |
|---|---|---|---|---|
| [Public APIs](https://github.com/public-apis/public-apis) | API discovery catalogue | Find candidate service APIs | Import metadata into a searchable catalogue; create reviewed adapters for selected APIs | Catalogue entries are not executable connectors |
| [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) | MCP discovery catalogue | Discover candidate tool servers | Curated index, security review, manifest generation, explicit enablement | A listed server is not trusted or installed |
| [Open Design](https://github.com/nexu-io/open-design) | Design project/reference | Design capability and workflow source | Inspect actual interfaces, dependencies and licence; implement an adapter or reuse eligible components | No assumed universal design API |
| [Awesome LLM Apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | Reference collection | Patterns and implementation research | Extract architecture patterns and evaluate selected projects individually | Not a runtime dependency |
| [Awesome](https://github.com/sindresorhus/awesome) | Discovery index | Find relevant libraries and resources | Search/import selected metadata with provenance | Not an executable subsystem |
| [Scrapling](https://github.com/D4Vinci/Scrapling) | Web extraction library | Structured extraction for research workflows | Optional Python adapter behind domain, rate, robots/terms and network policies | Not a general permission bypass or unrestricted crawler |
| [Free-for-dev](https://github.com/ripienaar/free-for-dev) | Free-tier catalogue | Discover candidate services and constraints | Catalogue importer with source date and manual verification of current terms | No guarantee that a tier is free, permanent, or sufficient |
| [Ollama](https://github.com/ollama/ollama) | Local model runtime | Local inference provider | Provider adapter to configured Ollama endpoint; model capability checks and timeouts | No model is assumed installed or capable of every task |
| [Langflow](https://github.com/langflow-ai/langflow) | Visual workflow framework | Optional workflow authoring/interoperability | Import/export or invoke selected flows through a narrow adapter | Langflow does not own OMNIA policy, task state, or approvals |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | Software engineering agent/runtime | Coding and repository-work capability | Isolated execution adapter with workspace and resource boundaries | Never grant unrestricted host, credential, or production access |

### 2.1 Integration selection gates

Before adopting any upstream component, record:
- canonical repository URL and exact commit/release;
- licence and obligations for code, assets, models, and dependencies;
- maintenance signals, security advisories, open issues, and release cadence;
- supported Python/Node/runtime versions and operating systems;
- network destinations, telemetry, credential handling, and data retention;
- resource requirements and operational complexity;
- adapter contract, tests, rollback path, and owner.

Do not vendor, install, execute, or expose a discovered component merely because it appears in a catalogue. Maintain a software bill of materials and provenance for adopted dependencies.

## 3. System architecture

### 3.1 Logical architecture

```text
Responsive Web Client (React / TypeScript)
              |
       Authenticated API
              |
     Task & Session Service
              |
       OMNIA Orchestrator
       /       |        \
  Planner   Agent Team   Policy Engine
     |       |    |          |
 Model Router |  Memory   Approval Service
     |        |
 Ollama / Remote LLMs
              |
       Capability Registry
       /        |          \
 Built-in    MCP Adapter   API Adapters
 Tools       Servers       & Libraries
       \        |          /
        Execution Gateway
          /           \
 Research Workers   Coding Workers
 Scrapling           OpenHands
          \           /
       Isolated Sandbox
              |
    Verification Engine
              |
 Artifact Store + Audit Log
              |
       Result Workspace
```

The diagram is logical, not a claim that every component already exists. The first release is a modular monolith with explicit interfaces. Services should be split only when isolation, scaling, or operational requirements justify it.

### 3.2 Core modules and responsibilities

| Module | Responsibility |
|---|---|
| Web Client | Prompt entry, task history, plan review, approval, progress, artifact access |
| API Layer | Validation, authentication boundary, request limits, stable versioned endpoints |
| Task Service | Task/session lifecycle, persistence, cancellation and ownership |
| Orchestrator | Plan coordination, agent delegation, dependency handling, retries and deadlines |
| Planner | Convert user intent into structured steps, acceptance criteria and required capabilities |
| Agent Manager | Assign specialist roles, enforce budgets, merge outputs and resolve conflicts |
| Model Router | Choose configured provider/model based on capability, privacy, latency, availability and cost policy |
| Memory Service | Task context, project memory, approved user preferences and retrieval with provenance |
| Capability Registry | Store tool manifests, versions, permissions, schemas, risk and enablement state |
| Policy Engine | Evaluate permissions, data egress, risk and approval requirements |
| Approval Service | Bind approval to an exact action/plan version and record the decision |
| Execution Gateway | Dispatch approved work to the correct adapter or isolated worker |
| Verification Engine | Run acceptance checks and classify evidence and unresolved failures |
| Artifact Store | Store generated files and metadata with ownership and retention policy |
| Audit Service | Append structured events for plans, approvals, calls, outputs and verification |

## 4. Agent collaboration model

### 4.1 Initial specialist roles

- **Manager Agent:** owns the task plan, delegation, dependencies, budget and final synthesis.
- **Research Agent:** gathers sources, extracts information and records evidence.
- **Developer Agent:** edits code in a controlled workspace and proposes changes.
- **Designer Agent:** produces design specifications, assets or interface implementations.
- **Data Agent:** validates, transforms and analyzes user-provided datasets.
- **Automation Agent:** coordinates approved service integrations and repeatable workflows.
- **Security Agent:** reviews proposed actions, permissions, dependencies and outputs.
- **QA Agent:** derives and runs acceptance checks and reports failures.

Roles are logical profiles, not necessarily separate processes or separate models. Start with one orchestrator and role-specific instructions/capability scopes. Add parallel execution only for independent steps.

### 4.2 Agent task envelope

Every delegated step must use a typed envelope containing:
- task_id, step_id, parent_step_id;
- assigned_role and objective;
- input references, not copied secrets;
- expected output schema and acceptance criteria;
- allowed capability IDs and permission scope;
- deadline, token/cost budget and retry budget;
- risk classification and approval reference;
- status and structured error information.

Agent outputs are untrusted until validated. Agents cannot grant themselves new permissions, approve their own high-risk actions, or silently add tools to their capability scope.

### 4.3 Collaboration rules

- The Manager owns the canonical task state.
- Agents communicate through structured messages and artifact references.
- Parallelize only steps without unresolved dependencies or conflicting writes.
- Use one designated writer per workspace path at a time, or explicit patch/merge coordination.
- Bound recursion, delegation depth, concurrent agents, retries, tokens and wall-clock duration.
- Require the Manager to reconcile conflicting findings and preserve dissenting evidence when unresolved.

## 5. Model provider abstraction

### 5.1 Provider contract

Implement a provider-neutral interface for:
- provider/model identification and configured capabilities;
- message completion and streaming where supported;
- structured output / JSON mode where supported;
- tool-call proposal where supported (never direct unmediated execution);
- timeout, cancellation, retryability and normalized errors;
- usage metadata where available;
- health checks without leaking prompts or secrets.

### 5.2 Routing policy

The Model Router should consider, in order:
1. required capability and output format;
2. data classification and whether external transmission is allowed;
3. user/operator provider preferences;
4. provider availability and context limits;
5. latency and resource constraints;
6. configured cost ceilings.

Ollama is the initial local provider. Remote providers are optional adapters and remain disabled until configured. OpenAI-compatible APIs may be supported through a generic endpoint configuration, but compatibility must be tested per provider. Never advertise unlimited free inference.

### 5.3 Reliability

- Explicit connect/read/total timeouts.
- Bounded retry with jitter only for retryable failures.
- No automatic retry for non-idempotent external actions.
- Provider health state and circuit breaking.
- Validate model output against schemas; reject malformed or unsafe plans.
- Redact secrets and sensitive fields from logs.

## 6. Unified capability and MCP system

### 6.1 Capability manifest

Each tool/capability must declare at least:

```yaml
id: research.fetch_page
version: 1.0.0
description: Retrieve a permitted public page
kind: mcp | api | builtin | worker
input_schema: {}
output_schema: {}
permissions:
  filesystem: []
  network:
    - approved-domain.example
secrets: []
risk: low
requires_approval: false
timeout_seconds: 20
resource_limits:
  memory_mb: 256
  cpu_seconds: 10
enabled: false
source:
  repository: https://example.invalid/project
  revision: pinned-revision
```

This is an illustrative schema. Production manifests must be validated, versioned, and stored centrally.

### 6.2 Registry lifecycle

1. Discover candidate.
2. Record provenance and licence.
3. Review source, dependencies, permissions and network behavior.
4. Create or validate manifest.
5. Run static and dynamic checks in isolation.
6. Operator explicitly enables the integration.
7. Pin version and configuration.
8. Monitor errors and changes; disable or roll back if trust changes.

MCP servers are treated as external processes with explicit transport, identity, timeout, permission and network policy. Tool descriptions and results are data, not policy instructions.

### 6.3 API catalogue lifecycle

Public APIs and free-tier entries are discovery metadata. Before making an adapter:
- verify endpoint and authentication requirements;
- inspect current terms, rate limits, quotas and regional restrictions;
- classify data transmitted to the service;
- implement rate limiting, pagination, retries and error mapping;
- store attribution, source URL and last verification date.

## 7. Task lifecycle and execution semantics

### 7.1 Canonical task states

```text
queued -> planning -> awaiting_approval -> ready
       -> running -> verifying -> completed
                         |           |
                         +-> failed  +-> completed_with_warnings

Any non-terminal state may -> cancelling -> cancelled
planning/running/verifying may -> failed
```

A low-risk plan may move directly from planning to ready. Approval is required only when policy says so. State transitions must be validated server-side and persisted transactionally.

### 7.2 Step states

`pending`, `ready`, `awaiting_approval`, `running`, `succeeded`, `failed`, `skipped`, `cancelled`, `verification_failed`.

### 7.3 Execution guarantees

- At-least-once dispatch may occur after worker failure; tools must declare idempotency behavior.
- Use idempotency keys for external operations when supported.
- Persist intent before dispatch and outcome after completion.
- A timeout does not prove that a remote action did not happen; reconcile before retrying.
- Cancellation is cooperative and must propagate to workers; report when an external action cannot be recalled.
- No hidden background execution after the user cancels a task.

## 8. Risk, permissions and human approval

### 8.1 Risk levels

| Level | Examples | Default behavior |
|---|---|---|
| Low | Local analysis, read-only parsing, draft generation | May run within granted task scope |
| Medium | Accessing external websites, modifying files in a task workspace, installing reviewed dependencies | Restricted execution; approval based on policy and context |
| High | Sending messages, publishing, pushing code, changing accounts, using credentials, modifying production systems | Explicit user approval before action |
| Critical | Payments, purchases, irreversible deletion, security-sensitive changes | Explicit, action-specific confirmation; consider disallowing by default |

Risk is based on actual tool effect, data sensitivity, reversibility, scope and destination—not merely the agent's label.

### 8.2 Approval binding

An approval must bind to:
- exact task and step;
- exact action and normalized parameters;
- target account, destination or resource;
- data to be transmitted;
- tool and version;
- expiry time and policy version.

If any material parameter changes, approval is invalidated and must be requested again. Agents cannot approve actions. Approval is not a blanket permission for future actions.

### 8.3 Secrets and privacy

- Store secrets in an OS/host secret manager or encrypted deployment secret store.
- Never place secrets in prompts, source files, artifacts or ordinary logs.
- Redact authorization headers, tokens, cookies and personal data.
- Require explicit opt-in for external model transmission of private task content.
- Provide data retention and deletion controls for hosted deployments.
- Do not use user content for training unless a separate, explicit product policy and consent permit it.

## 9. Execution isolation

Untrusted code and third-party tools must never execute inside the FastAPI process or on the host with unrestricted privileges.

### 9.1 Worker boundary

Use disposable containers or restricted workers with:
- non-root user and read-only base filesystem;
- dedicated per-task workspace;
- CPU, memory, disk, process and wall-clock limits;
- default-deny network egress with allowlisted destinations;
- no host Docker socket or privileged mode;
- no host home directory or ambient credentials;
- bounded artifact import/export;
- process-tree cleanup on cancellation and timeout.

OpenHands is integrated behind this boundary. The exact supported deployment mode and isolation controls must be validated against its current version before activation.

### 9.2 Mobile constraints

The responsive web client must work on Android browsers. The full orchestration, model and sandbox stack is not assumed to run reliably on a phone. Termux may support limited development or local experiments, but Docker/container availability, memory, CPU, battery and Android background restrictions make a capable computer or server the recommended execution host.

## 10. Research, evidence and memory

### 10.1 Research pipeline

- Search/retrieval adapters return source URL, title, retrieval timestamp and extracted content.
- Scrapling is optional and must obey applicable site terms, access controls, rate limits and configured domain policy.
- Store evidence references separately from model-generated summaries.
- Distinguish direct observations, source claims, inferences and unknowns.
- Cite evidence in final reports when external sources materially support claims.
- Detect conflicting sources and report uncertainty rather than silently choosing one.

### 10.2 Memory layers

- **Task memory:** current task context and step outputs.
- **Project memory:** user-approved project decisions, architecture and artifact references.
- **User preferences:** only information explicitly allowed by product memory controls.
- **Knowledge index:** imported documents and public references with provenance.

Memory retrieval must respect tenant/user boundaries, access control and source provenance. Retrieved text is untrusted context, never a higher-priority instruction.

## 11. Design, workflow and data capabilities

### 11.1 Design

Open Design is evaluated as a source for design workflows and components. OMNIA should expose design tasks through a stable capability interface, such as producing a design brief, component specification, asset bundle or frontend implementation. Confirm the upstream project's actual interface and licence before choosing a concrete adapter.

### 11.2 Workflow authoring

Langflow may provide visual flow authoring and interoperability. OMNIA remains the owner of task identity, policy, approvals, execution audit and artifact delivery. Imported flows must be inspected, versioned, permission-scoped and tested before use.

### 11.3 Data analysis

Provide built-in, schema-validated operations for common tabular formats. Run untrusted notebooks/scripts in the sandbox. Outputs should include transformed files, assumptions, validation checks and reproducible summaries.

## 12. API design

All endpoints are versioned under `/api/v1` once the current prototype transitions to a stable contract.

Proposed endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/v1/health/ready` | Dependency readiness |
| POST | `/api/v1/tasks` | Create a task |
| GET | `/api/v1/tasks` | List caller's tasks |
| GET | `/api/v1/tasks/{id}` | Task, plan and current state |
| POST | `/api/v1/tasks/{id}/plan` | Generate/re-generate a plan |
| POST | `/api/v1/tasks/{id}/approvals/{approval_id}` | Approve or reject an exact action |
| POST | `/api/v1/tasks/{id}/cancel` | Request cancellation |
| GET | `/api/v1/tasks/{id}/events` | Authorized task event stream |
| GET | `/api/v1/tasks/{id}/artifacts` | List artifacts |
| GET | `/api/v1/artifacts/{id}` | Authorized artifact metadata/download |
| GET | `/api/v1/capabilities` | List enabled capabilities visible to caller |

The current prototype endpoints may remain temporarily for compatibility, then be migrated with documented deprecation. Never expose arbitrary tool invocation as a public endpoint.

### 12.1 API requirements

- Pydantic request/response schemas and strict validation.
- Stable error envelope with machine-readable code and safe message.
- Pagination and bounded request sizes.
- Authentication and per-user authorization before any hosted multi-user deployment.
- No secret values in responses.
- OpenAPI contract tests and compatibility checks.

## 13. Data model

Initial logical entities:

- `User` / `Workspace`: identity and ownership boundary (required before multi-user hosting).
- `Task`: prompt, normalized goal, owner, status, timestamps, policy snapshot.
- `TaskStep`: ordered/dependent work unit, assigned agent, status, input/output references.
- `PlanVersion`: structured plan, model/provider metadata, acceptance criteria and revision.
- `Approval`: exact action binding, requester, decision, approver, expiry and policy version.
- `Capability`: manifest, source provenance, version, enablement and health.
- `Execution`: worker identity, start/end, resource usage, outcome and idempotency key.
- `AuditEvent`: append-only event record with actor, action, target and timestamp.
- `Artifact`: file/object metadata, checksum, media type, size, owner and retention.
- `Evidence`: source reference, retrieval time, excerpt/claim mapping and confidence metadata.
- `MemoryItem`: scoped content/reference, provenance, permissions and expiry.

SQLite is suitable for the initial single-user local milestone. Define repository interfaces and migrations so PostgreSQL can be adopted for concurrent hosted deployments. Do not store large artifacts as unbounded database blobs.

## 14. Frontend workspace

The web application should provide:
- **Task Composer:** natural-language prompt, attachments, constraints and privacy/provider choice.
- **Task Board:** status, recent tasks, filters and search.
- **Plan View:** ordered steps, dependencies, assigned agent, expected output and risk.
- **Approval Center:** exact action, destination, data scope and approve/reject controls.
- **Execution Monitor:** live event timeline, step states, resource use where available, cancellation.
- **Artifact Workspace:** downloadable outputs, previews, checksums and versions.
- **Capability Manager:** reviewed integrations, permissions, versions and enablement.
- **Model Settings:** local Ollama connection, configured models and optional remote providers.
- **Audit & Settings:** execution history, privacy, retention and system health.

The interface must be responsive and accessible. It must not display fake progress, fabricated tool activity or success states unsupported by backend events.

## 15. Verification and quality strategy

Every task type must define acceptance criteria before execution. Verification can include:
- unit/integration test results;
- build/type-check/lint results;
- schema and file integrity checks;
- repository diff review;
- source and citation checks;
- API response validation;
- human review for subjective or consequential outputs.

The final task result must use one of:
- **Completed and verified**
- **Completed with warnings**
- **Partially completed**
- **Failed**
- **Cancelled**

A result must include what was actually done, verification evidence, artifacts, remaining issues and whether any external action occurred.

## 16. Testing and CI gates

### 16.1 Test layers

1. Unit tests for planner validation, state transitions, risk rules, provider adapters and manifest validation.
2. API tests for authorization, schemas, task lifecycle, approvals, cancellation and error handling.
3. Contract tests for MCP/API adapters using mocks and pinned schemas.
4. Integration tests with fake model providers and fake workers.
5. Sandbox tests for filesystem, network, resource and process restrictions.
6. End-to-end tests for prompt → plan → approval → execution → verification → artifact.
7. Optional live Ollama smoke test, separate from required CI so CI does not depend on a local model.

### 16.2 Release gates

A milestone is complete only when:
- its automated tests pass in CI;
- setup and configuration are documented;
- failure and cancellation behavior are tested;
- security controls match the new capability;
- known limitations are explicit;
- evidence supports every completion claim.

## 17. Observability and operations

Use structured logs with task_id, step_id, agent_id, provider_id and capability_id, while redacting secrets and sensitive content. Track:
- task success/failure/cancellation rates;
- planning and execution latency;
- provider/tool error rates;
- retry counts and budget consumption;
- approval wait time;
- sandbox resource use;
- verification pass/fail rates.

Provide health/readiness checks, backup/restore procedures, database migrations, log retention and dependency update policy. Avoid logging full prompts or artifacts by default.

## 18. Deployment profiles

### Local single-user
Frontend, FastAPI, SQLite, Ollama and isolated workers on a capable host. This is the preferred initial development profile.

### Self-hosted
Authenticated frontend/API, PostgreSQL, managed secrets, isolated worker pool, backups and monitoring. Required before exposing the service to multiple users or the public internet.

### Hybrid
Browser client and orchestration service communicate with private model/worker infrastructure through an authenticated private channel. External data flow must be visible and configurable.

## 19. Threat model

Primary threats:
- prompt injection in web pages, repositories, documents and tool output;
- malicious or compromised MCP servers and dependencies;
- credential theft or accidental secret disclosure;
- sandbox escape and resource exhaustion;
- unauthorized task/artifact access;
- approval replay or approval of modified actions;
- SSRF and unsafe network egress;
- malicious generated code or dependency installation;
- poisoned memory or cross-workspace retrieval;
- false completion claims and fabricated evidence.

Required mitigations include default-deny network and tools, strict schemas, least privilege, pinned dependencies, sandbox isolation, approval binding, authorization checks, redaction, quotas, audit trails and adversarial tests.

## 20. Delivery sequence and acceptance criteria

### Phase A — Specification and integration due diligence
- [x] Product direction and high-level architecture documented.
- [x] Ten upstream projects assigned explicit roles and boundaries.
- [ ] Review exact upstream licences, APIs, releases and runtime compatibility.
- [ ] Approve versioned capability and agent contracts.

**Exit:** integration decisions are evidence-based and no upstream is treated as a blind dependency.

### Phase B — Reliable agent core
- [ ] Formal task/step state machine and migrations.
- [ ] Provider interface and Ollama adapter tests.
- [ ] Model routing policy and budgets.
- [ ] Planner output schema and acceptance criteria.
- [ ] Task event/audit model and cancellation.

**Exit:** a task can be planned, persisted, resumed and cancelled reliably using a fake provider and an Ollama smoke test.

### Phase C — Agent collaboration and policy
- [ ] Manager and specialist role contracts.
- [ ] Structured delegation and bounded parallelism.
- [ ] Capability manifest and registry.
- [ ] Risk policy and action-bound approval.
- [ ] Audit and permission tests.

**Exit:** agents can collaborate on a mocked multi-step task without exceeding permissions or budgets.

### Phase D — Real tool integrations
- [ ] MCP client with reviewed, explicitly enabled test server.
- [ ] Public API adapter framework and one reviewed integration.
- [ ] Research adapter and optional Scrapling integration.
- [ ] Provenance, citations and rate controls.

**Exit:** at least one real integration executes under policy and produces verifiable evidence.

### Phase E — Isolated software execution
- [ ] Disposable sandbox worker.
- [ ] OpenHands adapter review and integration.
- [ ] Workspace/artifact handling.
- [ ] Build/test/repair loop with strict attempt budget.
- [ ] Git operations require approval where externally consequential.

**Exit:** a sample code task is executed and tested in isolation, with artifacts and logs.

### Phase F — Design, workflow and data studio
- [ ] Open Design compatibility and licence review; adapter if justified.
- [ ] Langflow interoperability prototype.
- [ ] Data analysis and automation capabilities.
- [ ] Reusable task templates.

**Exit:** at least one design workflow and one data/workflow task complete end-to-end.

### Phase G — Productization
- [ ] Responsive workspace and task monitoring.
- [ ] Authentication, authorization and secret management.
- [ ] Security, load, backup/restore and deployment tests.
- [ ] Operational documentation and release process.

**Exit:** release candidate passes end-to-end CI and security gates with documented limitations.

## 21. Explicit non-goals and honesty rules

- OMNIA is not yet a finished autonomous platform.
- The existing API foundation currently plans and stores tasks; it does not yet perform arbitrary tool execution.
- No unlimited free hosted model/API is promised.
- A repository link or catalogue entry is not proof of integration.
- A generated plan is not proof of work.
- A successful command is not automatically proof that the user's intended outcome is correct.
- Do not merge the working branch into `main` without explicit user authorization.
- Do not enable a third-party integration before licence, security, compatibility and policy review.

## 22. Immediate engineering work after this specification

1. Reconcile the current code with this specification and identify the gap between implemented behavior and target contracts.
2. Add task/step state machine, schema validation, migrations and audit events.
3. Add robust provider interface and deterministic mocked integration tests.
4. Add capability manifest/registry and policy evaluation before connecting real MCP servers.
5. Add frontend only against stable task/event/approval contracts.
6. Introduce isolated workers before enabling OpenHands or arbitrary code execution.

This document is the engineering baseline. Implementation status must be tracked separately in the roadmap and verified through commits, tests and runtime evidence.
