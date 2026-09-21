# Acceptance checkpoint — 21 September 2026

This matrix records the stable checkpoint requested before the user left. It does not declare full M7 completion. Detailed test logs are in `reports/`; fixture version is 1.0. The final Git checkpoint contains the code and evidence together.

## Product requirements

| ID | Status | Evidence / qualification |
| --- | --- | --- |
| F01 | Passed for offline fixtures; live document integration unverified | DOCX/PDF and prompt tests in `tests/test_ingest.py`; mocked live document transport in `tests/test_live_documents.py`. Exact evidence is validated before commit. |
| F02 | Passed | Unknown fields, bounded questions and saved answers: ingestion and browser tests. |
| F03 | Passed | `tests/test_policies.py`: eight checks execute independently of retrieval; 12 manual clauses remain visible. |
| F04 | Passed | `tests/test_consistency.py`, manual browser journey: one model, three projections. |
| F05 | Passed | Actual pointer move/resize/connect/reconnect/delete, inspector, undo and reopening pass with zero provider requests. `reports/browser-tests.json`. |
| F06 | Passed | Prompt browser journey; stale semantic/view revisions rejected; layout and authored notes preserved. |
| F07 | Passed | Narrative/table share semantic revision; authored notes retained. `tests/test_consistency.py`. |
| F08 | Passed | Persistence tests, pattern sanitisation and browser import journey. |
| F09 | Partial / native unverified | Cross-platform exports tested in `tests/test_exports.py`; native helper supplied and syntax checked. Final SVG appearance and rendered DOCX/PDF visual QA remain. Native Visio is not installed. |
| F10 | Passed offline / mixed live results | Atomic budget and adapter tests pass. Terra smoke passes; Qwen generation/tool/edit smoke fails validation. |

## Milestones

| ID | Status |
| --- | --- |
| M0 | Passed: environment, runnable skeleton, early Visio feasibility. |
| M1 | Passed: canonical model, fixtures, deterministic generation and reference validation. |
| M2 | Passed, including expanded pointer regression. |
| M3 | Passed offline: ingestion, evidence, review, unknowns and contradictions. |
| M4 | Passed offline: policy checks, adapters and spending controls. Live provider results remain separate. |
| M5 | Passed consistency tests and prompted editing journey; integrated in this checkpoint. |
| M6 | Implemented; cross-export tests pass. Final visual review and native Visio remain unverified. |
| M7 | In progress: setup/demo/status/evidence supplied. Final visual/capacity-browser checks and source archive remain. |

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
| T11 | Passed offline fault tests | Malformed/truncated/refused output and false source references leave accepted state unchanged. |
| T12 | Passed | Budget reservations, parallel calls, restart and provider isolation tests. |
| T13 | Passed | Injection fixture cannot change tools/configuration or execute document instructions. |
| T14 | Passed backend / browser capacity unverified | `reports/capacity.json`: 50 components, 100 interfaces, actual SQLite create/edit/reopen timing. No browser capacity timing claimed. |
| T15 | Passed | Explicit partial coverage and unsupported text handling; live batching tested with mocked transport. |
| T16 | Passed exports/pattern / native unverified | JSON round trip, stable cross-export IDs, formula-safe CSV and sanitised pattern tests. `docs/VISIO.md`. |

## Live and environmental evidence

- **OpenAI:** `reports/smoke-openai.json` records three passing extraction/native-tool/targeted-edit checks, zero repairs, approximately $0.006948 for that run. Earlier attempts are preserved; this is not the account's total bill.
- **Ollama:** `reports/smoke-ollama.json` records failed proposal/tool checks with `qwen3:4b`. The provider connected; rejected candidates were not accepted. No paid fallback occurred.
- **Hardware:** `reports/environment.json`; previous live report records Ollama 3.2 GB / 100% GPU / 4K context. No peak sampling or Mac measurement.
- **Extraction:** `reports/extraction-metrics.json` measures authored component/interface record coverage on six specification format variants. It is not field-level or real-world accuracy, and omitted document sections are explicit.
- **Native Visio:** unverified. No generated VSDX, no claim that SVG is editable Visio.
- **Warnings:** production bundle is large because ELK is bundled; backend tests emit a dependency deprecation warning. Final rendered document QA is pending; no human time-savings study was performed.
