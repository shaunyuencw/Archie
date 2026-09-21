# Acceptance checkpoint — 21 September 2026

This matrix records the Mac continuation. The full offline gate passes (109 backend, 19 frontend unit, 21 browser journeys, TypeScript and production build). New product scenarios and library are covered by `apps/web/tests/product.spec.ts`. Mac handover is ready; full native Visio acceptance remains conditional. Fixture version is 1.0; historical Windows results are retained separately.

## Product requirements

| ID | Status | Evidence / qualification |
| --- | --- | --- |
| F01 | Passed for offline fixtures and real Terra journeys | Prompt and B SoW DOCX service flows passed with exact source locators; transport-qualified single ports normalize to the canonical integer while ambiguous values remain unknown. `reports/mac-resume-20260921-openai/report.json`, `tests/test_ingest.py`, `tests/test_live_documents.py`, `tests/test_live_orchestrator.py`. |
| F02 | Passed | Unknown fields, visible radio-card options and saved answers: ingestion and browser tests. |
| F03 | Passed | `tests/test_policies.py` preserves the original eight checks/12 manual clauses; `tests/test_policy_library.py` verifies 42 global clauses, 11 available checks, project applicability, local drafts and three-tier/hybrid separation. Optional advisory review is tested independently in `tests/test_policy_review.py`; one real three-policy Terra review passed. |
| F04 | Passed | `tests/test_consistency.py`, manual browser journey: one model, three projections. |
| F05 | Passed | Pointer move/resize/connect/reconnect/segment dragging and straight-line menu, groups, snapping, keyboard copy/paste/duplicate/delete/undo/redo, panels and reopening pass with zero manual provider requests. `reports/browser-tests.json`. |
| F06 | Passed | Prompt browser journey; stale semantic/view revisions rejected; layout and authored notes preserved. |
| F07 | Passed | Readable Overview and editable Connections share semantic revision; authored notes retained. `tests/test_consistency.py`. |
| F08 | Passed | Persistence tests, pattern sanitisation, project Trash/restore/confirmed purge, budget-ledger preservation and browser import journey. |
| F09 | Partial / native unverified | Cross-platform exports tested in `tests/test_exports.py`; native helper supplied and syntax checked. Three SVG views, narrative DOCX and all source DOCX/PDF pages visually checked on Mac (`reports/mac-export-qa/review.json`). Native Visio remains unverified. |
| F10 | Passed offline / mixed live results | Atomic budget and adapter tests pass. Terra A/B journeys pass; Qwen14B small extraction passes but richer journey fails safely. Historical Qwen4B results retained. |

## Milestones

| ID | Status |
| --- | --- |
| M0 | Passed: environment, runnable skeleton, early Visio feasibility. |
| M1 | Passed: canonical model, fixtures, deterministic generation and reference validation. |
| M2 | Passed, including expanded pointer regression. |
| M3 | Passed offline and real Terra prompt/DOCX service integration. |
| M4 | Passed offline: policy checks, adapters and spending controls. Live provider results remain separate. |
| M5 | Passed consistency tests and prompted editing journey; integrated in this checkpoint. |
| M6 | Cross-platform exports and rendered visual QA pass; native editable Visio remains unverified. |
| M7 | Mac verification, documentation and source handover complete; full acceptance conditional on native Windows/Visio check. |

## Acceptance tests

| ID | Status | Evidence |
| --- | --- | --- |
| T01 | Passed | `tests/test_ingest.py`: prompt baseline without invented sizing. |
| T02 | Passed | DOCX/table locators; upload and review browser journey. |
| T03 | Passed | PDF page evidence and equivalent-format deduplication. |
| T04 | Passed | Null unknowns, bounded questions and persistent answers. |
| T05 | Passed | Contradictory sources preserved. |
| T06 | Passed | All implemented predicates run, independent of retrieval. |
| T07 | Passed | `apps/web/tests/manual.spec.ts`, `pointer.spec.ts`; actual move/resize/connect/reconnect/delete and zero provider requests asserted. |
| T08 | Passed | Targeted prompt after manual positioning, accept/reject/undo. |
| T09 | Passed | Stale semantic and presentation proposals rejected. |
| T10 | Passed | Three views, narrative and interface table consistency. |
| T11 | Passed offline fault tests | Malformed/truncated/refused output and false source references leave accepted state unchanged. Reported unknown enforcement fields normalize with review notes; invalid references still reject (`tests/test_provider_normalization.py`). |
| T12 | Passed | Budget reservations, parallel calls, restart and provider isolation tests. Local default deadlines scale to response size; explicit deadlines are retained and timeouts do not replay. |
| T13 | Passed | Injection fixture cannot change tools/configuration or execute document instructions. |
| T14 | Passed backend and Mac browser | `reports/capacity.json`, `reports/browser-capacity-darwin.json`: 50 components / 100 interfaces, render/edit/drag/reopen, intact references and no model calls. Single-run browser timings include automation overhead. |
| T15 | Passed | Explicit partial coverage and unsupported text handling; live batching tested with mocked transport. |
| T16 | Passed exports/pattern / native unverified | JSON round trip, stable cross-export IDs, formula-safe CSV and sanitised pattern tests. `docs/VISIO.md`. |

## Live and environmental evidence

- **OpenAI:** Terra Flow A/B passed at the application service layer, four requests including one repair, approximately $0.0743975. Browser interaction tests are separate. `reports/mac-resume-20260921-providers.md`. Saved-output scope guard replay and versioned corrections are documented; original live snapshots are preserved.
- **New AI policy review:** one real Terra request assessed three selected portal policies for an estimated $0.01538, with valid source references and no architecture changes (`reports/mac-policy-review-20260921.json`). Combined continuation usage is eight requests (five cloud, three local), approximately $0.0897775. Automatic project naming is verified offline with mocked transport and browser acceptance/undo; no separate real naming call was made.
- **Ollama:** installed qwen3:14b, 14.8B Q4_K_M, 8192 context. Small extraction passed; richer generation failed safely. Loaded-model observation: 10 GB / 100% GPU, not peak memory. No fallback.
- **User-import follow-up:** enforcement type mismatches and the local 90-second response timeout were reproduced or traced and corrected offline. No fresh full live import was run after the fixes; the earlier successful journeys are not a claim of general import reliability. `reports/provider-input-recovery-20260921.md`.
- **Mac:** macOS 26.6.2, M2 Max, 32 GiB, Python 3.12.0, Node 22.23.1, pnpm 11.19.0, Chromium 153.0.8010.12. `reports/environment-mac.json`.
- **Windows history:** `reports/windows-checkpoint`, `reports/smoke-openai.json` (three checks/$0.006948), `reports/smoke-ollama.json` (qwen3:4b failure). RTX 3080 Ti Laptop/16,384 MiB and 68,334,067,712 bytes RAM are historical Windows observations.
- **Extraction:** `reports/extraction-metrics.json` records authored component/interface coverage across six specification format variants. It is not field-level or real-world accuracy; remaining sections stay explicit.
- **Visual QA:** `reports/mac-export-qa/review.json`: three SVG views, three narrative DOCX pages, six source DOCX and six source PDF files (12 pages each category). SVG retains some automatic route crossings and is not pixel-identical to React Flow.
- **Native Visio:** unverified. No generated VSDX or shape/glue/edit/save/reopen claim; a licensed Windows host is required.
- **Limitations:** no automatic obstacle-free routing or alignment-guide overlay; full local-model workflow unreliable. Mac keyboard paths were executed; fresh Windows shortcut/platform verification remains pending. On-demand ELK chunk remains large; Starlette test client emits a deprecation warning. No human time-savings study.

New demo visual QA: `reports/demo-pack-qa/review.json` records 22 inspected document pages and six SVGs. `tests/test_demo_scenarios.py` verifies authored mock roundtrips, deterministic regeneration and exact source locators. The new plain-language specifications and broad prompts have not been tested with real provider calls.

Product review screenshots: `reports/archie-specification-review.png`, `reports/archie-policy-review.png`, `reports/archie-clarification-questions.png`, `reports/archie-narrow-browser.png`. Compact demo before/after geometry and screenshots: `reports/demo-pack-qa/compact-layout/review.json`.
