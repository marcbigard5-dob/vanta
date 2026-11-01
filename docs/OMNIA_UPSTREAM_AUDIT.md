# OMNIA Upstream Integration Audit

**Audit date:** 2026-10-31  
**Target repository:** `marcbigard5-dob/vanta`  
**Target branch:** `feature/opensource-intelligence-hub`  
**Scope:** The ten upstream projects explicitly selected for OMNIA.

> This is a repository-level due-diligence snapshot, not a security certification. GitHub metadata, visible project documentation and selected manifests were inspected. Exact dependency trees, transitive licences, runtime behavior, vulnerability status, API quotas and deployment compatibility still require pinned-version testing before production adoption.

## 1. Executive decision

OMNIA should **not** clone or install all ten repositories as one application. Their roles differ substantially. Adopt a modular integration strategy:

| Upstream | Observed repository licence | Category | Decision | OMNIA integration |
|---|---|---|---|---|
| public-apis/public-apis | MIT | API catalogue | **Reference/import only** | Metadata importer; selected APIs get individual adapters |
| punkpeye/awesome-mcp-servers | MIT | MCP server catalogue | **Reference/import only** | Curated MCP discovery registry; no automatic install |
| nexu-io/open-design | Apache-2.0 | Design agent workspace + skills/plugins | **Selective adapter / skill reuse** | Consume portable skills, design systems and plugin manifests; evaluate daemon/CLI API |
| Shubhamsaboo/awesome-llm-apps | Apache-2.0 | Example and skill collection | **Reference / selective examples** | Extract patterns and individually reviewed skills; do not depend on entire repo |
| sindresorhus/awesome | CC0-1.0 | General discovery list | **Reference/import only** | Search index for project discovery; preserve source attribution/provenance |
| D4Vinci/Scrapling | BSD-3-Clause | Python web extraction framework | **Optional research adapter** | Separate worker or MCP adapter, isolated and policy-limited |
| ripienaar/free-for-dev | No repository licence declared in GitHub metadata | Free-tier catalogue | **Reference only; no content redistribution until clarified** | Read/search source links; verify service terms directly |
| ollama/ollama | MIT | Local model runtime | **Direct provider adapter** | HTTP API integration; runtime installed separately |
| langflow-ai/langflow | MIT | Visual flow authoring/runtime | **Optional external workflow adapter** | Invoke versioned flows through a narrow API boundary |
| OpenHands/OpenHands (formerly All-Hands-AI/OpenHands) | MIT | Agent Canvas / coding-agent control plane | **Isolated coding adapter** | Integrate with Agent Server / software-agent-sdk API; do not embed the whole UI as OMNIA core |

## 2. Important repository identity and snapshot findings

The following are observations from GitHub repository metadata and project files on the audit date. Popularity figures are intentionally omitted because they do not establish quality or safety.

| Project | Default branch | Language / stack signal | Repository activity signal | Notes |
|---|---|---|---|---|
| Public APIs | master | Python / Markdown catalogue | Pushed 2026-10-30 | README now prominently promotes APILayer; catalogue entries remain third-party services |
| Awesome MCP Servers | main | Catalogue / Markdown | Pushed 2026-10-23 | Very large list; README too large for the connector's content fetch, so inspect individual entries during selection |
| Open Design | main | TypeScript / pnpm workspace | Pushed 2026-10-31 | Very large repository; current README describes daemon, CLI, desktop/web workspace and plugin system |
| Awesome LLM Apps | main | Python examples and agent skills | Pushed 2026-10-22 | README describes 100+ examples/skills; each example has its own runtime and service dependencies |
| Awesome | main | Markdown index | Pushed 2026-09-02 | Broad catalogue, not a runtime |
| Scrapling | main | Python package | Pushed 2026-10-29 | Current pyproject says version 0.5, Python >=3.10, beta classifier |
| Free-for-dev | master | HTML / Markdown list | Pushed 2026-10-30 | GitHub API reports no repository licence |
| Ollama | main | Go runtime | Pushed 2026-10-30 | Documents REST API and separately installed runtime |
| Langflow | main | Python application/workspace | Pushed 2026-10-31 | Current pyproject says 1.13.0 and Python >=3.10,<3.15 |
| OpenHands | main | TypeScript Agent Canvas | Current GitHub project page is active | Organization/repository moved from All-Hands-AI to OpenHands; architecture spans multiple repositories |

Activity timestamps are not a substitute for release pinning. OMNIA must pin a reviewed tag or commit for every executable dependency and record the audit date.

## 3. Detailed integration assessment

### 3.1 Public APIs — catalogue, not a connector runtime

**Observed:** GitHub metadata declares MIT. The current README promotes APILayer products and describes the repository as a community-curated list of public APIs.

**Use in OMNIA:**
- Import API names, categories, descriptions and source URLs into a discovery index.
- Store authentication method, base URL, documentation URL and last-checked timestamp only after validation.
- Generate adapter scaffolds, not executable integrations, from catalogue metadata.
- Select one API at a time for a reviewed adapter with schema, rate limits and tests.

**Risks / caveats:**
- MIT applies to the repository's licensed content, not to the services listed in it.
- Each API has separate terms, privacy policy, quotas, commercial restrictions and geographic availability.
- "Public" does not mean unauthenticated, free, unrestricted or reliable.
- README's current promotional content means catalogue freshness and neutrality should be checked before importing entries.

**Decision:** Build an importer and searchable catalogue. Do not add all listed APIs to the live tool registry.

### 3.2 Awesome MCP Servers — discovery catalogue, not a trust authority

**Observed:** GitHub metadata declares MIT. The repository is a large collection of MCP servers. GitHub's security page reported no SECURITY.md policy and no published repository advisories at the time of the inspected page; absence of advisories is not evidence of safety.

**Use in OMNIA:**
- Import candidate server name, repository, transport, description and claimed capabilities.
- Link each candidate to its own source repository and licence.
- Create a review queue with status: discovered, under-review, approved, enabled, disabled, rejected.
- Require a manifest, pinned version, tool schemas, network destinations, secret requirements and risk classification before enablement.
- Run approved servers under a separate identity/process/container with resource and network controls.

**Risks / caveats:**
- The catalogue licence does not relicense individual servers.
- Each server has its own licence, maintainer, dependency chain and security posture.
- MCP tool descriptions and outputs can contain prompt injection or malicious instructions.
- A server may read files, access credentials, or transmit data depending on its implementation and granted permissions.

**Decision:** Use as a discovery feed only. No automatic installation, startup or trust promotion. Evaluate each MCP server independently.

### 3.3 Open Design — reusable design capabilities, not an assumed drop-in library

**Observed:** GitHub metadata and README declare Apache-2.0. The current project describes a collaborative AI design workspace with a local daemon, CLI, desktop/web surfaces, skills, design systems and a plugin marketplace. Its README documents an `open-design.json` manifest, `SKILL.md` payloads, a plugin registry and `/api/plugins` endpoint. The README also documents CLI operations such as plugin list/search/info/install/apply/validate.

**Use in OMNIA:**
- Prefer portable `SKILL.md` workflows and design-system packages as the first integration surface.
- Build an OMNIA adapter that can inspect and validate plugin manifests before use.
- Consider calling the Open Design daemon/CLI as a separate process/service for design-specific tasks.
- Map design outputs into OMNIA artifacts: design brief, system tokens, components, prototype, exported assets and provenance.
- Preserve each plugin's capability declaration and source revision.

**Risks / caveats:**
- Repository size and breadth make whole-repository embedding an expensive and fragile choice.
- The project has its own agent execution and plugin lifecycle. Running it alongside OMNIA requires clear ownership of approvals, memory, task state and audit.
- Plugin metadata is not proof that the referenced code is safe.
- Design-system packages may contain third-party brand assets or upstream-derived content; check package provenance and use rights individually.

**Decision:** Selective integration. Start with the portable skills/design-system/plugin format and an adapter. Do not make Open Design the owner of OMNIA's orchestrator or install its entire stack as a core dependency.

### 3.4 Awesome LLM Apps — pattern library and selected skills

**Observed:** Repository metadata declares Apache-2.0. Current README describes more than 100 AI agents, agent skills and RAG applications, with example-specific setup instructions and integrations.

**Use in OMNIA:**
- Study architecture patterns for RAG, agents, voice, multi-agent workflows and tool use.
- Evaluate specific skills or examples as isolated candidates.
- Port useful patterns into OMNIA-native modules where this reduces coupling.
- For each adopted example, record its exact path, commit, dependencies, model providers and licence.

**Risks / caveats:**
- The repository-level licence is not enough to assume every bundled model, dataset, image, prompt asset or linked dependency has the same rights.
- Examples may expect API keys, paid model access, cloud accounts or particular Python versions.
- Demonstration code is not automatically production-ready.
- Skills that execute shell commands need the same sandbox and approval policy as any other tool.

**Decision:** Reference and selectively reuse reviewed skills/examples. Do not add the repository as a runtime dependency or copy examples wholesale.

### 3.5 Awesome — general discovery index

**Observed:** GitHub metadata declares CC0-1.0. The repository is a broad list of other curated lists, not an executable application.

**Use in OMNIA:**
- Search it as a meta-index to find specialist catalogues relevant to a user's task.
- Store pointers to list repositories rather than copying entire downstream lists.
- Record retrieval date and canonical source URL.

**Risks / caveats:**
- CC0 on this index does not override licences of projects linked from it.
- Its broad scope can produce noisy or outdated discovery results.
- A listing is not a quality, maintenance or security endorsement.

**Decision:** Optional discovery index only. Do not put it in the runtime dependency graph.

### 3.6 Scrapling — optional web extraction worker

**Observed:** GitHub metadata declares BSD-3-Clause. Current `pyproject.toml` reports package version 0.5, Python >=3.10, beta development status, and optional extras including fetchers, RAG, AI/MCP and shell. Fetcher extras include browser-related dependencies such as Playwright and Patchright.

**Use in OMNIA:**
- Wrap Scrapling behind a narrow research capability interface.
- Run it in a separate worker/container, not in the FastAPI request process.
- Default to explicitly allowed domains and conservative request rates.
- Return extracted text/structured data plus source URL, timestamp and extraction metadata.
- Keep browser/fetcher extras optional; install only the features actually needed.
- Add request budgets, response-size limits, timeouts and cancellation.

**Risks / caveats:**
- Scraping can trigger legal, contractual, privacy and operational issues; follow site terms, access controls and applicable law.
- Browser automation and stealth-related capabilities increase misuse and security risk; OMNIA must not use them to bypass authentication, paywalls, CAPTCHAs or access restrictions.
- Browser dependencies increase image size and attack surface.
- Beta status means behavior and API stability must be tested against a pinned release.

**Decision:** Optional research adapter after sandbox and domain policy exist. Do not install the full `all` extra in the core API environment.

### 3.7 Free-for-dev — catalogue with an unresolved licence issue

**Observed:** GitHub repository metadata returned `license: null`. README describes a curated list of SaaS/PaaS/IaaS offerings with free developer tiers and says entries are maintained through community contributions and reviews.

**Use in OMNIA:**
- Use the source as a human-readable discovery reference.
- Prefer storing links and short factual metadata over copying/re-publishing the catalogue.
- For every suggested service, verify its official pricing/terms page and record the verification date, limits, region and payment requirements.
- Distinguish always-free quotas, time-limited trials, credits, and conditional free tiers.

**Risks / caveats:**
- No repository licence is declared in GitHub metadata. Do not assume the list content can be copied, bundled or redistributed under an open-source licence.
- A free tier can change or disappear; the list is not a service-level guarantee.
- "Free" can require a payment card, impose usage caps, restrict commercial use or be unavailable in a user's region.

**Decision:** Reference only until the maintainers clarify content reuse rights. Verify all service claims directly before recommendation or use.

### 3.8 Ollama — initial local model runtime

**Observed:** GitHub metadata declares MIT. Current README documents local installation, a REST API, `/api/chat`, model library, Docker image and Python/JavaScript client libraries.

**Use in OMNIA:**
- Keep the existing provider abstraction and implement a tested Ollama adapter.
- Discover configured models from the running Ollama service; do not assume a model is installed.
- Use REST endpoints for model listing, chat, streaming and health checks as supported by the pinned runtime.
- Route through capability metadata and model-specific context/output limits.
- Keep the Ollama runtime outside the Python API dependency set.

**Risks / caveats:**
- The Ollama repository licence does not determine the licence or acceptable-use terms of every model pulled through it.
- Model memory, speed, context size and tool-call reliability vary by model and hardware.
- Local inference is not unlimited in practical capacity; CPU/RAM/GPU, storage, power and concurrency constrain it.
- The Ollama endpoint must not be exposed to an untrusted network without appropriate authentication/network controls.

**Decision:** Direct integration; make it the first local provider. Add a model registry and a live smoke test, while retaining provider-neutral interfaces.

### 3.9 Langflow — optional visual workflow subsystem

**Observed:** GitHub metadata declares MIT. Current `pyproject.toml` reports version 1.13.0 and Python >=3.10,<3.15, with a large set of core and optional integrations/extensions.

**Use in OMNIA:**
- Keep OMNIA as the canonical owner of tasks, approvals, memory, policies and audit.
- Use Langflow for visual authoring/prototyping of selected flows.
- Version and validate exported flows before they are registered in OMNIA.
- Invoke flows through a narrow adapter/API with typed inputs/outputs and timeouts.
- Treat each flow as a capability requiring permission review.

**Risks / caveats:**
- Embedding the entire Langflow runtime into the current small FastAPI service would create dependency and upgrade coupling.
- Flows may contain arbitrary components, credentials or network calls.
- A flow's visual graph does not by itself prove its security or determinism.
- Extension bundles and provider integrations add their own dependencies and secrets.

**Decision:** Optional separate service or workflow adapter, not OMNIA's core orchestrator. Prototype only after the task/tool contracts are stable.

### 3.10 OpenHands — isolated software execution capability

**Observed:** The old `All-Hands-AI/OpenHands` URL now redirects because the organization moved to `OpenHands/OpenHands`. The current repository page declares MIT and describes Agent Canvas. Its README states that Agent Canvas uses an Agent Server REST API and that the wider system spans multiple repositories:
- `OpenHands/OpenHands`: Agent Canvas frontend and local-stack orchestration.
- `OpenHands/software-agent-sdk`: Python SDK, Agent Server, agents, tools, workspaces, events and server API.
- `OpenHands/typescript-client`: browser-compatible API client.
- `OpenHands/automation`: scheduling, webhooks and dispatching.

The README explicitly warns that running without a sandbox grants the agent full filesystem access. Docker sandbox mode and multiple Docker sandbox mode are documented. Current quickstart references Node.js 24+ and `uv`.

**Use in OMNIA:**
- Integrate the Agent Server/SDK boundary as a coding execution backend, not as the OMNIA master orchestrator.
- Use a dedicated worker host and per-task workspace/container.
- Map OMNIA task IDs and approval scope to OpenHands conversation/workspace identifiers.
- Stream structured events back into OMNIA's execution timeline.
- Export diffs, test reports and generated artifacts for OMNIA verification.
- Pin compatible versions of Agent Server/SDK/client and document the API contract.

**Risks / caveats:**
- The rename means existing references and container image names may be stale; update to canonical OpenHands locations after validating each release.
- The no-sandbox mode is not acceptable for untrusted autonomous execution.
- Docker socket access is highly privileged; do not mount it into a worker that runs untrusted code unless the isolation architecture explicitly requires and protects a controlled outer daemon.
- Agent Canvas is a separate frontend product; embedding its whole UI would duplicate OMNIA's workspace and confuse task ownership.
- OpenHands itself is not a replacement for OMNIA's policy/approval/audit layer.

**Decision:** High-value coding backend, but integrate only after sandbox infrastructure and policy gates are operational. Prefer the SDK/Agent Server API over embedding Agent Canvas.

## 4. Cross-project compatibility and dependency strategy

### 4.1 Avoid one giant dependency environment

Do not install Scrapling browser extras, Langflow, Open Design, OpenHands and all MCP servers into one Python environment. This would create avoidable version conflicts, a large attack surface and difficult upgrades.

Use separate runtime boundaries:

| Runtime | Components | Why separate |
|---|---|---|
| OMNIA Core | FastAPI, Pydantic, task store, policy, provider interfaces | Small, stable control plane |
| Model Runtime | Ollama | Native model service and hardware-specific lifecycle |
| Research Worker | Scrapling and selected parsers/browser dependencies | Browser/network isolation and optional dependencies |
| Workflow Service | Langflow (optional) | Large independent application and plugin ecosystem |
| Design Service | Open Design daemon/CLI (optional) | TypeScript/Node/pnpm and its own agent/plugin runtime |
| Coding Worker | OpenHands Agent Server/SDK and sandbox | Untrusted code execution boundary |
| MCP Tool Workers | One process/container per reviewed server or trust group | Separate permissions, credentials and network policy |

### 4.2 Version and licence records

For every executable integration, store:
- canonical repository and package name;
- pinned tag and immutable commit SHA;
- package versions and lockfile;
- licence identifier and licence file reference;
- transitive dependency/SBOM record;
- container image digest where relevant;
- configuration schema and required secrets;
- security review date and reviewer;
- compatibility test result;
- rollback version.

For catalogue entries, store the upstream source and the individual service's terms; do not confuse repository licence with API/service terms.

### 4.3 Runtime/API boundaries

All integrations must be behind OMNIA-owned interfaces:
- `ModelProvider`
- `ResearchProvider`
- `DesignProvider`
- `WorkflowProvider`
- `CodingExecutionProvider`
- `MCPToolProvider`
- `CatalogSource`

Adapters must normalize errors, timeouts, cancellation, structured outputs and audit events. Do not let upstream-specific data models leak into the core task domain.

## 5. Recommended adoption order

| Order | Integration | Reason | Entry condition |
|---:|---|---|---|
| 1 | Ollama | Needed to make local planning/inference reliable | Provider tests, model discovery, timeout and health handling |
| 2 | MCP registry using Awesome MCP Servers as source | Unlocks broad tool capability | Manifest validation, server review, process/network isolation |
| 3 | One selected Public API | Demonstrates controlled API integration | Verified terms, quota, schema and credentials policy |
| 4 | Scrapling | Adds research extraction | Research worker sandbox, domain allowlist and rate controls |
| 5 | OpenHands SDK/Agent Server | Adds real software task execution | Disposable sandbox, resource limits, workspace isolation and approval |
| 6 | Open Design skills/plugin adapter | Adds structured design workflows | Plugin validation, provenance and capability-scoped skill execution |
| 7 | Langflow interoperability | Adds optional visual workflow authoring | Stable workflow/task contracts and separate service deployment |
| 8 | Awesome LLM Apps | Select specific patterns/skills as needed | Per-example review, licence and dependency tests |
| 9 | Public APIs / Awesome / Free-for-dev catalogue importers | Expand discovery | Source attribution and per-entry validation; Free-for-dev reuse rights clarified |

This is an order of engineering adoption, not a claim that the remaining projects are unimportant. Catalogue importers can be built in parallel with core work, but they must not auto-enable execution.

## 6. Immediate blockers before live integration

1. **No sandbox yet:** OpenHands, MCP servers, arbitrary shell/code and browser automation must remain disabled until isolated workers are implemented and tested.
2. **No stable capability registry yet:** create manifest schema, review state and enablement policy before adding MCP servers.
3. **No complete approval binding yet:** approval must bind to exact action parameters and target, not just a task-level boolean.
4. **Ollama adapter requires real verification:** test connection, model discovery, malformed outputs, timeouts and unavailable runtime.
5. **OpenHands rename and multi-repository split:** update upstream identity and select the canonical Agent Server/SDK interface.
6. **Free-for-dev licence unresolved:** do not redistribute or bundle the list content without permission or a confirmed licence.
7. **Third-party licences are separate:** catalogue repository licences do not cover every linked server, API, model, plugin or design asset.
8. **No production security claim:** current audit is due diligence, not a penetration test or dependency vulnerability scan.

## 7. Concrete engineering decisions for OMNIA

- Keep the current FastAPI/SQLite task API as a temporary core foundation; evolve its contracts before adding more runtimes.
- Keep Ollama as the first local model provider.
- Create a provider-neutral model router; no model vendor owns orchestration.
- Build a first-party capability manifest and registry before MCP execution.
- Treat Public APIs, Awesome MCP Servers, Awesome and Free-for-dev as discovery sources, not runtime dependencies.
- Integrate Scrapling and OpenHands only through isolated workers.
- Integrate Open Design through portable skills/design-system/plugin contracts first.
- Keep Langflow optional and externally isolated.
- Use Awesome LLM Apps as an engineering pattern library; selectively port reviewed implementations.
- Record all upstream versions, commits, licences and test outcomes in a machine-readable integration inventory.

## 8. Validation status

| Check | Status |
|---|---|
| GitHub repository metadata for all ten original sources | Inspected; OpenHands canonical name updated |
| Repository-level licence metadata | Inspected; Free-for-dev has no declared licence |
| Selected current README / package manifests | Inspected where accessible |
| Open Design plugin interface | README and plugin spec inspected |
| OpenHands Agent Canvas / multi-repository architecture | Current repository page inspected |
| Exact immutable commit pins for all ten | Not yet recorded |
| Full transitive dependency/licence scan | Not run |
| CVE/SCA scan at pinned versions | Not run |
| Runtime integration tests | Not run |
| Sandbox penetration/adversarial tests | Not run |
| Production approval | Not granted / not applicable |

**Conclusion:** OMNIA can reuse meaningful capabilities from all ten sources, but the correct integration is a combination of direct API adapters, isolated runtime adapters, portable skills and discovery catalogues. The first real execution milestone should be Ollama + capability registry + one reviewed MCP tool, followed by a tested sandbox before enabling OpenHands or arbitrary code execution.
