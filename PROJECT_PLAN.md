# Architecture Workbench
## Coding-agent project plan and acceptance specification

**Version:** 1.0 | **Prepared for:** Keru | **Date:** 21 September 2026  
**Delivery target:** A locally runnable, single-user proof of concept (PoC).  
**Authority:** This specification defines the build. References establish library capabilities, not organisational policy.

## 0. Commissioning brief — read this first

Build a working application, not another proposal. The user supplies a prompt or a Statement of Work (SoW)/technical specification. An assistant extracts a reviewable architecture, retrieves relevant policy and template material, asks focused questions with selectable answers, and produces an icon-based diagram and matching narrative. The user can continue by dragging components and connectors or by prompting. Both editing methods must update the same project.

**Fixed choices:** React/TypeScript canvas; Python backend; one bounded orchestrator; interchangeable OpenAI, Ollama and mock providers; synthetic reference material; no model training. Target Windows with an RTX 3080 laptop GPU, or an Apple M2 Max. Actual video memory and unified memory are unknown and must be detected, not assumed.

**The coding agent owns:** implementation, synthetic materials, tests, startup scripts, documentation, screenshots, export adapters and a truthful completion report. Do not ask the user to write policies, supply sample documents or design templates before starting. Generate the specified demonstration materials locally.

**The user retains:** architectural decisions, approval of real-data use, permission to spend beyond configured limits, and final acceptance. Synthetic policies must never be described as the user's real cyber policies. PPM is an organisational process placeholder here; no internal PPM requirements have been supplied.

### Non-negotiable outcomes

- A real interactive canvas with icons, zones, editable labels and reconnectable straight/right-angled connectors; not a generated picture.
- One versioned architecture model, with sources and uncertainty, shared by the diagram, interface table and narrative.
- Functional OpenAI and Ollama adapters plus a clearly labelled, free mock demonstration.
- Generated source documents, policy pack, templates, assets, reference examples and test cases.
- Explicit usage limits, no AI calls for ordinary mouse edits, and no hidden paid fallback.
- Visio export treated as a separate tested capability, not inferred from browser editability.

### Scope and completion rules

Complete milestones M0–M7 in order, preserving a runnable application after each. Do not stop after scaffolding or mock mode. Missing credentials, Ollama hardware or Windows Visio may leave the corresponding live verification pending; they must not block other implementation. Never label an unexecuted check as passed. Avoid commercial SDK purchases, cloud deployment, production security claims and speculative rewrites.

**Read efficiently:** use this brief and section 10 as the route map. Read the relevant section when implementing that milestone; do not reload the entire document on every turn. Put the supplied `AGENTS.md` at the repository root. Record short progress in `docs/STATUS.md`.

**Navigation:** 1 Scope and experience · 2 Synthetic inputs · 3 Policies, views and assets · 4 Data model · 5 Orchestrator · 6 Stack and contracts · 7 Providers/hardware · 8 Runtime budgets · 9 Coding-token discipline · 10 Milestones · 11 Tests · 12 Exports/security · 13 Handover · 14 Sources.

<!-- PAGEBREAK -->

## 1. Product scope and user experience

Implement a desktop-browser workbench: left assistant/upload panel, centre canvas, right inspector. Provide tabs for Logical, SV-1-style and SV-2-style views, and secondary panels for Narrative, Interfaces, Findings and Sources. Show the active provider, project revision and cumulative API cost. Use a restrained visual style, readable text and explicit status badges; colour must not be the only status signal.

| ID | Required behaviour | Acceptance evidence |
|---|---|---|
| F01 | Create a project from text, DOCX or text-based PDF; review extracted information before accepting it. | Each accepted fact links to a prompt passage or document locator. |
| F02 | Ask up to three high-impact questions per round, with options, Other and Not decided. | Answers persist; unknowns do not prevent a labelled draft. |
| F03 | Retrieve policy clauses and apply implemented checks separately. | Findings show clause/version, affected objects and evidence. |
| F04 | Generate three distinct views from one model. | Renaming a system updates all views without duplicating the system. |
| F05 | Add assets by drag-and-drop or click-to-add; move, resize, rename and delete; create/reconnect connectors and change line style. | Actions work without an LLM call. Deleting referenced objects requires confirmation. |
| F06 | Apply prompted changes through a previewable change set. | Accept, reject and undo work; unrelated manual positioning survives. |
| F07 | Generate narrative and interface table; preserve separately authored notes. | Outputs reference the same accepted semantic revision. |
| F08 | Save/reopen projects and save a sanitised reusable pattern. | Layout, routes, sources, answers and versions survive reopening. |
| F09 | Export project JSON, SVG, narrative DOCX/Markdown and interface CSV; implement the Visio handover path. | Native Visio verification is separately reported. |
| F10 | Switch provider explicitly and enforce resource budgets. | Local failure never silently transmits content to OpenAI. |

### Demonstration journey

Upload a synthetic VAP specification. Review extracted systems and zones. Answer the event-delivery and management-access questions. Generate a diagram. Move two nodes manually, then prompt “add one configuration workstation; keep the layout.” Inspect a policy finding, accept a proposed correction, switch views, save/reopen and export. The narrative and interface table must reflect the accepted change, not the original prompt.

### Deliberate boundaries

Support one user, one application instance, and up to 50 components/100 interfaces per project as the initial test envelope. Defer simultaneous collaboration, arbitrary Visio import, automated architecture approval, detailed equipment sizing, live security-system integration, scanned-document OCR, architecture reconstruction from screenshots, cloud connectors and enterprise SSO. Do not build a second diagram editor or a multi-agent framework. A saved pattern reuses roles and questions, not previous addresses or unconfirmed decisions.

<!-- PAGEBREAK -->

## 2. Synthetic data — generate all six categories

Generate fixtures from committed, human-readable YAML/Markdown using an idempotent Python script with a fixed seed and fixed fixture date. Commit the material once; do not use runtime API calls to regenerate it during startup or tests. Label every rendered document and reference diagram **SYNTHETIC — DEMONSTRATION ONLY**. The following quantities are scope decisions, not research-derived requirements.

| Category | Required deliverables | Content and validation |
|---|---|---|
| Project documents | Three project packs, each containing one SoW and one technical specification. Render all six sources to DOCX and text-based PDF. | Include paragraphs, headings and tables. Keep each document around 2–4 pages. Render both formats from the same source facts. |
| Policy pack | Twenty uniquely identified clauses, version 1.0; eight executable checks. | Retain applicability, exceptions, source text and implementation status. Twelve clauses remain explicitly manual-review only. |
| View/template definitions | Logical, SV-1-style and SV-2-style definitions; one generic narrative template. | Define allowed content, aggregation, required fields, labels and treatment of unknowns. |
| Icon/component catalogue | Twenty-four locally bundled assets with a manifest and licence notices. | Record asset ID, component type, tags, connection handles and default size. |
| Reference packages | Two model-and-view examples with narratives, interface tables and expected findings. | One complete example; one intentionally incomplete example. These are demonstration references, not approved designs. |
| Evaluation fixtures | Sixteen named scenarios with expected facts, checks or UI behaviours. | Twelve development cases and four frozen variants. Never send expected answers to the runtime LLM. |

### The three project packs

**A — Baseline VAP integration.** Existing VMS in Infrastructure; two workstations in Client; VAP management/integration services in Z1; VAP analytics in Z2. Existing C2 is outside the VAP system boundary, with internal zoning explicitly unspecified. Show it as an external-system reference, not an invented fifth security zone. Specify video, event and management interfaces. Include a synthetic capacity target but leave equipment sizing undecided.

**B — Incomplete integration.** Retain the main systems but omit event delivery, connection initiator, administration route and availability design. Expected behaviour: ask useful questions, preserve unknowns and produce a labelled partial draft without inventing ports, firewalls or server counts.

**C — Conflicting requirements.** One source requires no internet dependency; another includes an external service. Add a declared resilience requirement and an explicitly single-instance design. Expected behaviour: preserve both claims, cite each conflict and request a decision rather than silently choosing a source.

The document manifest must map format variants to the same source/version to prevent double-counting DOCX and PDF copies. Expected answers are developer fixtures, not an independently validated benchmark: the coding agent helped author them. A later human review and fresh real cases are required before claiming organisational effectiveness.

<!-- PAGEBREAK -->

## 3. Policy checks, view definitions and assets

### Eight synthetic checks to implement

Each rule is ordinary reviewed Python with typed inputs, not executable code generated from a retrieved passage. Model answers may explain a result but must not replace the rule's result. These requirements apply only inside the fictional demonstration policy pack.

| Check | Fictional requirement | Required result handling |
|---|---|---|
| DEMO-ZON-01 | Every in-scope networked deployment has a declared zone. | Missing assignment: insufficient information. External-system references are exempt when their scope is explicit. |
| DEMO-ADM-01 | Client management access must use the declared management interface, not a direct processing-service path. | Explicit forbidden management path: potential conflict; unspecified purpose: insufficient information. |
| DEMO-FW-01 | A cross-zone management session identifies its mediation/enforcement control. | Check the interface's control reference. A nearby firewall icon is not evidence. |
| DEMO-NET-01 | A no-internet system has no required internet-hosted dependency. | Explicit dependency contradicting the constraint: potential conflict. |
| DEMO-IF-01 | Network-session definitions identify initiator and protocol. | Missing attributes remain unresolved; data-flow arrows do not prove initiation. |
| DEMO-HA-01 | A resilience requirement has an explicit availability strategy. | No strategy: insufficient information. Explicit single instance/no recovery against the requirement: potential conflict. Two icons do not prove resilience. |
| DEMO-AUD-01 | Management functions identify an audit destination. | Missing destination: insufficient information. Do not fabricate a logging service. |
| DEMO-DAT-01 | Data marked local-only is not assigned an external storage destination. | Explicit external storage: potential conflict. Unknown destination: insufficient information. |

Use results `pass`, `potential_conflict`, `insufficient_information` and `not_applicable`. Also track execution separately: `implemented`, `manual_review` or `error`. A pass means only that the implemented predicate passed on the supplied facts. Evaluate all applicable implemented rules, even when retrieval returns only a few passages. Display coverage and unimplemented clauses; never show an unqualified “cyber compliant” badge.

### Three genuinely different views

**Logical:** application responsibilities and information flows, optionally grouped by zone. **SV-1-style:** systems and their interconnections, aggregating internal components where appropriate. **SV-2-style:** more detailed interface/resource-flow descriptions with protocol, session initiation and relevant connection properties. These are simplified demonstrations informed by DoDAF, not a claim of complete DoDAF or internal PPM conformity. [R12–R13]

View configuration must declare aggregation rules and source-object mappings. A combined SV-1 edge retains the IDs of its underlying interfaces. Do not simply relabel the same canvas three times.

### Asset catalogue

Include server, GPU server, application, analytics engine, database, storage, firewall, switch, router, gateway, proxy, load balancer, workstation, camera, identity service, audit service, event broker, API service, external system, network zone, system boundary, site and two generic role variants. Use a consistent locally bundled icon library such as Lucide with required notices. [R14] Icons decorate semantic nodes; neither icon shape nor screen position proves network behaviour.

<!-- PAGEBREAK -->

## 4. Canonical model and editing semantics

The backend owns accepted state. The language model proposes typed changes; it does not produce the authoritative database or diagram coordinates. Separate meaning, evidence and presentation. Export/import a versioned project envelope, never just the canvas library's incidental internal state.

| Record | Minimum fields |
|---|---|
| Project | ID, schema version, semantic revision, timestamps, source manifest, policy/template versions, synthetic-data flag. |
| System / Component | Stable ID, name, role/type, system membership, existing/new/proposed status, asset ID, scope. |
| Deployment | ID, component ID, zone ID or null, host/site reference when known, quantity when explicitly provided. |
| Interface | ID, source/destination IDs, purpose, data direction, connection initiator, protocol/port or null, enforcement references, source evidence. |
| Evidence / Claim | Source ID/version, locator, excerpt; target field; claimed value; source kind; review state. Preserve conflicting claims. |
| Constraint / Decision | Requirement ID, scope, value, evidence; decision state and accepted user response. |
| View | Type, semantic-object mappings, presentation revision, positions, sizes, visibility, labels, handles, edge routes and layout locks. |
| ChangeSet | ID, base revisions, typed operations, affected IDs, evidence links, validation findings and acceptance state. |

Keep source kind (`document`, `prompt`, `template`, `assistant_proposal`) separate from review state (`unreviewed`, `confirmed`, `rejected`, `unknown`, `conflicting`). A document can contain an unreviewed claim; a template is not proof of a project fact. Avoid invented confidence percentages.

### State invariants

All references resolve; IDs are unique; null is different from zero; quantities/protocols are not filled from guesswork. Grouping has no cycles. Use zones as the primary canvas parent and system tags/overlays for system membership, because those boundaries can overlap. Do not make the model duplicate a component merely to draw it in two views. Backend-generated IDs resolve any temporary IDs in a proposal.

A cosmetic drag or line-style change increments presentation revision only. Reconnecting an edge, changing deployment zone or changing a component role is semantic and triggers validation. Dropping a node across a zone boundary previews reassignment; it must not silently change security placement. Existing routed interfaces retain their meaning when a line is bent.

### Safe changes and undo

Use allowlisted operations such as add/update/remove component, add/update/remove interface, assign deployment zone and update view placement. Validate the entire candidate transaction before committing; reject invalid references and stale base revisions with a conflict response. Persist before announcing success. Coalesce drag events into one undoable change. Keep at least 50 undo steps for the PoC.

A prompted edit touches only relevant objects. Preserve unrelated coordinates and manual routes; full re-layout is explicit. Generated narrative is cached by semantic revision; layout-only changes do not regenerate it. Keep user-authored notes separate, and mark stale generated text until it is refreshed or deterministically regenerated.

<!-- PAGEBREAK -->

## 5. Orchestrator and source handling

Implement one application-controlled state machine: **ingest → extract candidate facts → retrieve context → clarify or draft → validate proposal → user accept → render/export**. The OpenAI/Ollama model supplies interpretation and tool selection within this workflow. It does not own permissions, persistence or budget decisions.

| Tool / service | Behaviour and boundary |
|---|---|
| `extract_requirements` | Input bounded source chunks; output candidate claims with source IDs and locators. Cannot accept them itself. |
| `get_architecture_context` | Return a compact selected subgraph, relevant decisions and unresolved fields, not the entire project/history. |
| `lookup_policies` | Search local clause text and applicability tags; return bounded passages with IDs/versions. |
| `load_view_spec` / `find_assets` | Read curated definitions/catalogue entries. No arbitrary URLs or filesystem paths. |
| `request_clarification` | Produce typed question cards linked to fields, evidence and options. Persist answers. |
| `propose_changes` | Return a typed ChangeSet against supplied base revisions. Cannot commit it. |
| Host-only services | Validate, commit, save, run all implemented checks, lay out views, create exports and account for usage. |

Expose only the small subset needed for the current task. Start with plain Python orchestration rather than an agent framework. Support native tool calls where the selected model passes capability tests; otherwise use schema-constrained action envelopes dispatched by the same allowlisted host. Label this fallback mode. OpenAI and Ollama both document tools and structured outputs, but local-model quality remains an evaluation question. [R01–R02, R05–R06]

### Bounded execution

Apply the call limits in section 8 across every model request, repair and retry. Parallel agent spawning is forbidden. At most one schema-repair attempt is allowed and consumes the same budget. On tool errors, unsupported schema, refusal, truncation, timeout or budget exhaustion, preserve the accepted project and expose a useful error or clarification. Partial JSON must not mutate state.

### Parsing and retrieval

Use local DOCX parsing and text-based PDF extraction first. Retain document ID/version, heading path, paragraph or table-cell locator, PDF page when available, and exact excerpt. DOCX page numbers are not reliable without a rendering/layout step; cite section/paragraph/table instead. PDF text extraction has known layout limitations and does not replace OCR. [R17]

Hash documents and cache extraction. Split by section/table boundaries into bounded chunks; record processed and unprocessed ranges. Never silently truncate a long document and claim full coverage. When a document exceeds limits, show partial coverage and offer selection of additional sections. Mark unsupported scanned pages clearly; OCR is out of scope.

Start policy retrieval with tags and SQLite full-text search. No vector database or paid embedding calls are needed for twenty clauses. Missing retrieval results mean no supporting clause was found, not that the architecture is approved. Verify every emitted source ID/locator against the supplied context; quote text must match the source. Uploaded text is untrusted data, not permission to change tools, budget settings or policies.

<!-- PAGEBREAK -->

## 6. Technology choices and repository contracts

These are fixed defaults to reduce decision loops. At M0, verify compatibility once, select supported stable versions and commit Python and npm lockfiles. Do not continuously chase newer package versions. Avoid paid features and premium examples.

| Layer | Selected approach |
|---|---|
| Frontend | React, TypeScript and Vite; `@xyflow/react` for the canvas; minimal CSS/components; Lucide assets. Custom nodes, handles and grouped views are documented building blocks. [R08–R10, R14] |
| Layout | `elkjs` with layered layout for initial arrangements; custom edge rendering for saved paths. ELK supports orthogonal routing, but the application must preserve manual edits and handle rerouting. [R11] |
| Backend | FastAPI, Pydantic and Python 3.11 or a verified compatible newer version. Generate frontend API types from the backend schema; do not maintain two incompatible models. |
| Storage | SQLite plus local project/source files. Store versioned JSON snapshots, changes, evidence and usage records. No Redis, Kubernetes or hosted database. |
| LLM adapters | Official OpenAI Python SDK with Responses API; native Ollama HTTP API via `httpx`; deterministic mock adapter. |
| Documents | `python-docx` for DOCX; `pypdf` for clean PDF text; `reportlab` for synthetic PDFs; Jinja2/`python-docx` for narrative exports. Docling is an optional later parser, not a core dependency. [R17] |
| Tests | pytest; Vitest/React Testing Library; Playwright for browser journeys. Mock transport is the default. |
| Startup | Native backend/frontend launch scripts for Windows and macOS. Docker is optional and must not be required for local GPU inference. |

### Repository layout

```text
AGENTS.md                     # short persistent working rules
PROJECT_PLAN.md               # this specification
apps/web/                     # canvas, chat, inspector, view state
apps/api/app/
  domain/                     # schemas, commands, validation
  orchestration/              # bounded state machine + tools
  providers/                  # mock, OpenAI, Ollama, budget wrapper
  ingest/  policies/  exports/ # deterministic services
  storage/                    # snapshots, changes, usage ledger
packages/contracts/           # generated schema/types
fixtures/{projects,policies,templates,assets,references,evals}/
scripts/                      # seed, doctor, run, test, export helpers
config/                       # model profiles, dated pricing
prompts/                      # small versioned prompts
reports/                      # generated test evidence; no secrets
docs/{STATUS,DECISIONS,SETUP,DEMO,ACCEPTANCE}.md
```

### API boundaries

Provide endpoints for projects/snapshots, source uploads and extraction coverage, clarification answers, assisted runs, change previews/commit, views, findings, exports and usage. Use a request ID, project ID and base revisions on mutations. A run endpoint may return a job ID with status polling; do not introduce a distributed queue. One worker is sufficient, with restart recovery marking interrupted runs rather than replaying paid calls.

Use predictable error codes: invalid input, stale revision, unsupported document, incomplete extraction, unavailable provider, insufficient context and budget exceeded. Test them in the UI. Reopening a project must not automatically call a model.

<!-- PAGEBREAK -->

## 7. Model providers and laptop profiles

**Do not confuse the coding agent with the application's model.** ChatGPT Work may build the repository; the deployed application uses its own configured API credentials or local Ollama server. The runtime model does not need to be the expensive model used for complex implementation.

### Provider contract

Implement `generate_structured`, `invoke_tools`, capability reporting and normalized usage. Pass cancellation/deadline information. Return structured result, finish status, actual model ID, token counts and latency. Validate with Pydantic on every provider. Separate transport/model settings: do not assume changing an OpenAI base URL makes Ollama equivalent.

**OpenAI:** initial configurable economy candidate `gpt-5.4-mini`; its official page documents Responses, function calling and structured outputs. It is a dated baseline, not a claim to be the newest or universally best model. [R03] Verify availability once; pin a tested snapshot where practical. Use low/none reasoning only when supported; do not send unsupported temperature or reasoning parameters. Leave the escalation model blank by default. Never auto-upgrade to a larger model.

**Ollama:** begin with `qwen3:4b` as a capability-test candidate, not a performance guarantee. Its published tag is a roughly 2.5 GB Q4_K_M model, but file size is not total runtime memory. [R07] Disable thinking when supported and suitable for the task; test JSON extraction, a tool request and a targeted graph edit. A larger locally installed model may be selected explicitly after measurement. Do not automatically download several models.

| Profile | Starting limits — proposed, not measured guarantees |
|---|---|
| RTX 3080 laptop, memory unknown | Detect VRAM; try one 4B quantized model; `num_ctx=4096`; maximum input 2,500 tokens, output 1,024, safety reserve 512. One request at a time. |
| M2 Max, unified memory unknown | Run Ollama natively; start with the same 4K profile. Apple GPU acceleration uses Metal. [R04] |
| Larger local profile after testing | `num_ctx=8192`; maximum input 5,500, output 1,536, reserve 768. Try an 8B-class model only when memory and quality tests justify it. |

Prompt limits include instructions, tool schemas, evidence and conversation. Schema plus selected context must fit; shrink the subgraph/chunks or report insufficient context, never silently discard constraints. Context size affects memory use; inspect actual GPU/CPU offload with `ollama ps`. [R04–R06]

A `doctor` script reports OS/architecture, available RAM/VRAM when obtainable, Ollama version/models, provider configuration without secrets, and tested capabilities. Record cold/warm latency, input/output tokens, schema success, peak memory where measurable and `ollama ps` output. Do not invent speed targets. No cloud fallback when local inference fails; preserve manual and mock functionality.

<!-- PAGEBREAK -->

## 8. Runtime token and spending controls

Treat these as implementation requirements, not a request to spend. Ship in `mock` mode with cloud disabled. A user explicitly enables OpenAI and supplies a key server-side. Budget limits are adjustable settings, never hard-coded provider-wide spending promises.

| Control | Initial default |
|---|---|
| Manual editing, layout, rule checks, save/export | Zero model calls. Baseline narrative is deterministically templated; optional prose refinement is explicit. |
| Simple prompted edit | Aim for one request; maximum three model requests including repair/retry. |
| Initial prompt-based draft | Aim for two requests; maximum four including clarification/tool follow-up/repair. |
| Document ingestion batch | Maximum six extraction requests plus two draft requests, with a preflight plan. Additional sections require a new visible action. |
| Cloud request size | Maximum 12,000 input and 3,000 output tokens; local profiles use section 7 limits. |
| Application spend guard | US$0.10 per interactive action; US$0.20 per document batch; US$1/day; US$5/project. Block the next call when reservation would exceed any limit. |
| Retry policy | At most one repair/retry for a task, inside its existing call and cost ceilings. No automatic model escalation. |
| Live development tests | Opt-in only; ten calls or US$0.50 per run, whichever is reached first; also subject to normal application limits. |

A clarification click may save an answer for free; “Continue” starts a new visible assisted action. Limit the default document batch to the source chunks it can actually process and report coverage. Do not silently drop a six-chunk remainder.

### Enforce before calling

All provider access must pass through one `BudgetedProvider`. Atomically reserve a conservative estimated input cost plus the maximum output cost before a request. Account for in-flight reservations, not just completed usage. Persist the ledger across restarts. Reconcile against provider usage after completion; retain a conservative reservation for ambiguous timeouts until reconciled. A request already transmitted can still incur charges when cancelled. These limits constrain this application, not unrelated API-key use.

Record model, action/project IDs, input tokens, cached reads, cache writes when applicable, output tokens, reported reasoning-token subset, latency and estimated/actual cost. Do not double-count reasoning if it is already included in output tokens. Ollama exposes prompt/generation counts; record its API fee as zero, not its electricity or hardware cost. [R05]

Use a dated price configuration. For distinct input categories, cost equals `(ordinary input × input rate + cache-read input × read rate + cache-write input × write rate + output × output rate) / 1,000,000`. Normalize categories using the selected provider's semantics. Model families can have different cache-write charges; do not assume caching is free or guaranteed. [R15]

For scale only: the dated mini-model rates are US$0.75/M input and US$4.50/M output. A request actually using 5,000 uncached input and 2,000 total output tokens is US$0.01275 before other charges. This is arithmetic, not a promised per-draft cost. [R03] If model pricing is unknown, require configuration before enabling paid calls.

<!-- PAGEBREAK -->

## 9. Keep coding-agent usage economical

These rules govern development behaviour; application caps cannot technically limit the external coding agent's ChatGPT usage. Follow them as working discipline and report actual coding usage only when the host provides it.

### Read and change less

Use `AGENTS.md`, `docs/STATUS.md`, the current milestone and relevant files. Search filenames/symbols before opening large files. Do not repeatedly ingest lockfiles, generated schemas, fixture binaries, build folders or the complete chat history. Keep generated output out of search where possible. Patch the smallest relevant area; do not rewrite working modules to restyle them.

Create the canonical domain types once and derive API/frontend contracts. Build one provider abstraction, one change-application path and one policy engine. Do not create “architect,” “critic,” “reviewer” and “coder” subagents that repeat the same context. Use normal tests rather than asking another model to review every output.

### Spend calls where they add information

Generate fixture prose and configuration as development artifacts once. A deterministic script should render variants, not ask an API to author them again. Mock unit, integration and browser tests. Use one small opt-in live smoke run after the relevant gates pass; do not call a paid model for every failing UI test.

At runtime, send the current task, a compact state summary, at most the last two useful conversational exchanges, selected evidence and the affected subgraph. Cache parsing, retrieval and derived outputs by content hash/revision. Never reuse a cached ChangeSet on a different base revision. Reuse accepted facts rather than repeatedly extracting unchanged documents.

Stable prompts and schemas can support provider caching, but application-level avoidance of unnecessary calls is the first saving. Do not pad prompts solely to reach a cache threshold. Log real cache behaviour and cost. [R15]

### Bounded engineering decisions

Use the selected stack. Research only a specific unresolved capability and record the decision once in `docs/DECISIONS.md`. After two unsuccessful materially different approaches to a non-core integration, document the blocker, isolate the adapter and continue with remaining scope. Do not silently remove that feature or call it complete.

Keep milestone updates short: implemented, tests run, failures and next step. Keep `STATUS.md` under roughly 800 words and each routine update under roughly 150 words. Do not reproduce source code in chat when it is already saved in the repository. These are working targets, not limits that justify omitting essential warnings.

### Stop conditions

Pause paid calls at the budget ceiling. Do not buy libraries, alter account plans, upload the repository, weaken machine security or use real internal documents without permission. Missing keys/hardware are verification blockers, not reasons to abandon the mock/editor work. Do not ask for decisions already fixed here; choose conservative defaults for minor details and record them.

<!-- PAGEBREAK -->

## 10. Milestone plan and exit gates

Build by capability, not calendar promises. Effort shares are planning allocations, not time estimates. Implement all core milestones; stretch scope is not allowed to displace a failing core gate.

| Milestone | Allocation | Work and mandatory exit gate |
|---|---:|---|
| M0 — Feasibility and skeleton | 8% | Pin dependencies; create contracts, mock app and startup/doctor scripts. Demonstrate a small zone/icon/edge graph. Build a minimal Visio-export experiment early; record whether native testing is available. |
| M1 — Model and synthetic pack | 12% | Implement records, revisions, commands and deterministic generators. Produce all section 2 materials. Gate: valid fixtures, idempotent generation, reference resolution and no live calls. |
| M2 — Editable workbench | 18% | Implement canvas palette, inspector, straight/orthogonal edges, zone reassignment, save/reopen, undo and all three view mappings. Gate: manual-edit Playwright journey passes without a provider. |
| M3 — Ingestion and mock assistant | 15% | Parse DOCX/PDF, preserve sources/coverage, present fact review and clarification cards, apply mock proposals. Gate: each source fact is traceable; incomplete/conflicting cases remain explicit. |
| M4 — Policies and model adapters | 12% | Add retrieval, eight rule checks, OpenAI/Ollama implementations and budget wrapper. Gate: contract/error/budget tests pass; live smoke runs only when explicitly enabled. |
| M5 — Prompt editing and consistency | 12% | Implement targeted changes, stale-proposal handling, layout preservation, rejection/undo and synchronized derived outputs. Gate: sequential mouse-plus-prompt edits pass all invariants. |
| M6 — Exports and reusable patterns | 13% | Export JSON/SVG/DOCX/Markdown/CSV; finish interactive Windows Visio helper; sanitise reusable patterns. Gate: reopen/export consistency passes; Visio status is separately demonstrated or pending. |
| M7 — Verification and handover | 10% | Run acceptance suite, document actual environments/provider behaviour, capture UI evidence, package app and walkthrough. Gate: completion matrix distinguishes passed, failed and unverified. |

### Dependency and continuation rules

M0 informs export feasibility before major investment. M1 contracts are the base for every subsequent feature. A small editor prototype may occur during M0, but a competing persistent data model must not survive it. M4 adds live intelligence only after the mock workflow works. M6 may continue with an unverified Windows adapter when the build host lacks Visio, but native-export acceptance stays pending.

After each gate, save a working checkpoint and update `STATUS.md`. Run focused tests after edits and the complete offline suite at milestone boundaries. Do not reset the repository or rewrite earlier milestones to evade failing tests.

### Prototype levels

**Level 0:** M0–M1 establish feasibility and contracts. **Level 1:** M2–M3 deliver the editable synthetic demonstration. **Level 2:** M4–M7 deliver the requested substantive PoC. A real-data organisational pilot is not included; it requires approved policies/templates, data-handling decisions and human evaluation.

Default priorities are factual traceability and edit consistency first, acceptable layout second, visual polish third. A beautiful screenshot does not compensate for hidden invented interfaces or lost edits.

<!-- PAGEBREAK -->

## 11. Acceptance suite and evidence

Implement the sixteen fixture scenarios below. The first twelve are development cases; the final four are frozen variant cases unavailable through runtime retrieval. Do not describe this split as independently authored or statistically representative. Expected facts and rule outcomes are versioned test data.

| Test | Required observation |
|---|---|
| T01 Prompt baseline | Extract VMS/VAP/C2 and the specified zones; no invented equipment sizing. |
| T02 DOCX/table extraction | Correctly map a requirement from a table and resolve its document locator. |
| T03 PDF/version handling | Preserve page evidence; equivalent DOCX/PDF copies do not duplicate components or claims. |
| T04 Unknowns and questions | Missing delivery/initiator fields remain null; up to three useful questions; saved answers are not repeatedly requested. |
| T05 Source contradiction | Conflicting dependency/availability claims remain visible with both sources. |
| T06 Policy and coverage | All applicable implemented rules run, including a relevant clause outside retrieval top results; manual-only clauses stay visible. |
| T07 Mouse operations | Add/move/rename/reconnect/change edge style/undo/save/reopen with zero LLM calls. |
| T08 Mouse then prompt | Add a node by prompt after manual positioning; unaffected positions/routes remain unchanged. |
| T09 Version conflict | A stale proposal cannot overwrite a newer manual semantic or presentation edit. |
| T10 Views and narrative | Rename/change an interface once; all three views, table and narrative reflect the accepted semantic revision. |
| T11 Provider failures | Reject malformed/truncated output and nonexistent source references; timeout/refusal leaves accepted state unchanged. |
| T12 Budget/provider isolation | Enforce action/day/project reservations, retries and restarts; no hidden local-to-cloud fallback; mock opens no provider connection. |
| T13 Injection variant | Document text requesting secret disclosure or disabling policies cannot change tool permissions, configuration or network destinations. |
| T14 Capacity variant | Load 50 components/100 interfaces, edit and reopen without losing references; record measured responsiveness. |
| T15 Oversized-document variant | Show processed/unprocessed sections; no silent truncation or false full-document coverage. |
| T16 Export/template variant | JSON round trip and cross-export IDs agree; reusable pattern removes project evidence/addresses; Visio checklist is reported separately. |

### Pass criteria

All deterministic core tests must pass with mock mode and no API key. In live tests, accept only schema-valid, reference-valid transactions. Require exact source-reference resolution and zero unsupported additions committed without review. Record candidate extraction precision/recall against the authored fixture facts, repair count, questions asked, accepted changes, token/cost usage and latency; do not hide a poor local-model result behind the mock adapter.

The assistant should achieve at least 90% coverage of explicitly enumerated component/interface facts on the development extraction fixtures as an initial project target, with omissions visibly reviewable. Failed fields and counts must be reported. This target is not evidence of real-world accuracy.

Compare time to a reviewer-acceptable draft against a manual baseline only when an actual person performs both tasks. A 50% effort reduction is a future hypothesis, not an auto-generated result. Keep screenshots and test logs tied to the commit, OS, model/provider and fixture version.

<!-- PAGEBREAK -->

## 12. Exports, Visio and security boundaries

### Required cross-platform exports

**Project JSON:** full versioned semantics, sources/locators, accepted decisions, view layouts/routes and user notes; no API keys or hidden provider credentials. Test exact round trip within the supported schema version.

**SVG:** a faithful review image of the selected view with locally embedded assets. Label it as an image export, not a native Visio document. **DOCX/Markdown:** editable narrative, scope, component roles, interfaces, assumptions/open items, source references and model revision. **CSV:** stable interface IDs and separate information-flow/session-initiation columns.

Exports operate on one immutable accepted snapshot. Warn when a proposal is pending or generated text is stale. Prevent spreadsheet-formula execution from untrusted labels in CSV exports. A template export strips source excerpts, project-specific identifiers/addresses and unconfirmed answers; it preserves roles, layout conventions, questions and synthetic pattern constraints.

### Native Visio path — free tooling, environment-dependent verification

Implement an interactive Windows helper, such as `scripts/export_visio.ps1`, that reads the project export and uses an installed, licensed desktop Visio instance to create a `.vsdx`. Keep it outside the web-server request path. Use native nodes/text/connectors, meaningful object IDs and containers where supported; imported icons may decorate nodes, but do not flatten the entire page. Microsoft documents connector gluing and container creation. [R18–R19]

The helper must create its own document, avoid modifying existing user diagrams, support explicit input/output paths and refuse overwrite without confirmation. Resolve coordinates, units and inverted vertical axes deliberately. Do not alter system-wide execution policies or fetch third-party scripts.

**Visio acceptance:** open the exported file without repair; select/rename a node; move it and confirm connector attachment; change a connector route; move a zone/container; save/reopen and inspect the result. Record which features were tested. If no Windows/Visio environment is available, deliver the helper and a manual verification checklist, with native export labelled **implemented but unverified**, not complete. Do not purchase a commercial exporter or reverse-engineer the entire format to conceal the limitation.

Visio is one-way handover in this PoC; later Visio edits do not synchronise back. Microsoft does not recommend or support unattended server-side Office automation, so the interactive helper must not become a headless service. [R20]

### Security and data controls

Default to loopback binding, explicit local-origin CORS and synthetic material. Keep keys in server environment variables; redact logs. Validate upload types and size, sandbox paths, reject macro-enabled inputs, sanitize SVG/HTML and disallow external asset fetches. Treat project JSON as untrusted and validate imports. Do not expose Ollama on public interfaces by default.

OpenAI API data controls and retention must be checked before real material is enabled; not being used for training does not mean zero retention. `store=false`, where supported, is not a blanket zero-retention guarantee. [R16] No remote tracing or telemetry by default. Local mode must not call OpenAI, hosted embeddings, external fonts or cloud document parsers. Setup downloads are distinct from runtime network isolation.

<!-- PAGEBREAK -->

## 13. Packaging, configuration and final handover

Provide a working repository, not only code snippets. Include `.env.example`, lockfiles, generated fixture sources/rendered samples, licence notices, tests, screenshots, walkthrough and an acceptance matrix. Never include a real key, secret-bearing log, `node_modules`, model weights or machine-specific virtual environment in the handover archive.

### Minimum configuration contract

```text
APP_PROVIDER=mock
APP_ALLOW_CLOUD=false
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
OPENAI_ESCALATION_MODEL=
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_NUM_CTX=4096
APP_MAX_INPUT_TOKENS=12000
APP_MAX_OUTPUT_TOKENS=3000
APP_MAX_CALLS_PER_ACTION=4
APP_BUDGET_ACTION_USD=0.10
APP_BUDGET_DOCUMENT_USD=0.20
APP_BUDGET_DAY_USD=1.00
APP_BUDGET_PROJECT_USD=5.00
APP_LIVE_TESTS=false
APP_TELEMETRY=false
```

The two token ceilings above are cloud defaults; local profile limits override them. Lower task-specific limits, such as three calls for a simple edit, override the general ceiling. Document batches have their separately declared ceiling. Validate all limits at startup and display effective values in Settings. Provide an explicit price-file date and billing-model ID.

### Required commands or equivalent scripts

`seed` generates/checks synthetic artifacts without paid calls. `doctor` reports prerequisites without revealing secrets. `dev` runs the application. `test` runs the offline suites. `smoke --provider openai --live --max-calls 10 --budget-usd 0.50` is opt-in. `smoke --provider ollama` uses an already installed local model. `package` assembles the source handover and demo artifacts. Provide equivalent Windows PowerShell and macOS instructions; native startup is the primary supported path.

### Completion report

Report each F01–F10 requirement, M0–M7 milestone and T01–T16 test as passed, failed or unverified, with evidence paths. Explicitly separate mock demonstration, real OpenAI integration, real Ollama integration, hardware performance and native Visio verification. A health check alone is not a successful live architecture-generation test.

Include exact setup commands, tested versions, where to enter configuration, how to run the demonstration, known limitations and remaining manual checks. Do not invent measured time savings, provider spend, hardware benchmarks or a security certification. Keep the report concise enough to act on, and place detailed logs in files.

### Coding-agent launch instruction

> Implement this project end to end using PROJECT_PLAN.md as the acceptance specification and AGENTS.md as the working rules. Start with M0, inspect the environment, then implement M1–M7 with mock-first tests and the specified synthetic fixtures. Preserve working code between milestones. Do not ask me to author inputs. Paid model calls are opt-in and budgeted; missing credentials or hardware leave those checks unverified while other work continues. Finish with the runnable repository, setup/demo instructions and an evidence-based completion matrix, not another plan.

<!-- PAGEBREAK -->

## 14. Technical references and verification notes

Official documentation checked on 21 September 2026. These references support implementation choices; all quantities, budgets, milestones, synthetic policies and acceptance targets in this plan are proposed project requirements. Recheck model availability/prices and package compatibility once at M0, then record tested versions. Do not interpret the links as a requirement to browse them repeatedly.

| Ref | Official source | Relevance |
|---|---|---|
| R01 | [OpenAI — Function calling](https://developers.openai.com/api/docs/guides/function-calling) | Application-defined tools and host execution. |
| R02 | [OpenAI — Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | Schema-constrained results; still validate meaning and evidence. |
| R03 | [OpenAI — GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini) | Dated baseline capabilities, model ID and example pricing. |
| R04 | [Ollama — Hardware support](https://docs.ollama.com/gpu) | GPU support, including Apple Metal. |
| R05 | [Ollama — Chat API](https://docs.ollama.com/api/chat) | Native requests, structured format, tools and usage counts. |
| R06 | [Ollama — Context length](https://docs.ollama.com/context-length) | Memory implications and offload inspection. |
| R07 | [Ollama — qwen3:4b](https://ollama.com/library/qwen3:4b) | Candidate tag, quantization and published file size. |
| R08 | [React Flow — Custom nodes](https://reactflow.dev/learn/customization/custom-nodes) | Interactive nodes and connection handles. |
| R09 | [React Flow — Sub flows](https://reactflow.dev/learn/layouting/sub-flows) | Parent/grouped diagram representation. |
| R10 | [React Flow — Edge types](https://reactflow.dev/api-reference/types/edge) | Edge representation and styling. |
| R11 | [Eclipse ELK — Layered layout](https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html) | Routing and layout building blocks. |
| R12 | [DoD CIO — SV-1](https://dodcio.defense.gov/Library/DoD-Architecture-Framework/dodaf20_sv1/) | Systems Interface Description. |
| R13 | [DoD CIO — SV-2](https://dodcio.defense.gov/Library/DoD-Architecture-Framework/dodaf20_sv2/) | Systems Resource Flow Description. |
| R14 | [Lucide — Licence](https://lucide.dev/license) | Asset licence and notices. |
| R15 | [OpenAI — Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) | Read/write usage, exact-prefix reuse and model-dependent billing. |
| R16 | [OpenAI — Data controls](https://developers.openai.com/api/docs/guides/your-data) | API retention and data-handling caveats. |
| R17 | [pypdf — Text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | Clean-PDF extraction and its limitations. |
| R18 | [Microsoft — Visio Cell.GlueTo](https://learn.microsoft.com/en-us/office/vba/api/visio.cell.glueto) | Native connector attachment. |
| R19 | [Microsoft — Visio Page.DropContainer](https://learn.microsoft.com/en-us/office/vba/api/visio.page.dropcontainer) | Native container creation. |
| R20 | [Microsoft — Server-side Office automation](https://support.microsoft.com/en-us/visio/considerations-for-server-side-automation-of-office) | Why the Visio helper is interactive, not a web-server service. |

**Open issues deliberately retained:** actual laptop memory; selected local model's measured quality; exact organisational PPM/SV conventions; approved cyber-policy wording; availability of a licensed Windows Visio test environment. None may be replaced with an invented fact.
