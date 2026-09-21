# Architecture Workbench / Archie — progress

Updated: 21 September 2026. This is a working progress report, not a claim that every acceptance gate has passed.

**Current position: stable checkpoint ready for GitHub; M0–M5 core gates pass, M6 exports are implemented, and M7 handover remains in progress.** Work is stopping here at the user's request before departure. The app is running locally at <http://127.0.0.1:5173/>. Final offline gate: **25 backend tests, 6 browser journeys, 1 frontend unit test, TypeScript and production build all passed** (`reports/offline-gate.json`).

## What you can see now

- Archie logo and robot assistant from the proposal infographic.
- Editable architecture canvas, equipment icons, labelled dashed zones, and connections styled toward the supplied VLAN diagram example.
- Reference projects, three views (Logical, SV-1, SV-2), properties, palette, save/reopen and undo.
- Document upload, source evidence, proposed changes to review, clarification questions, policy findings, narrative and interface table.
- Explicit mock/OpenAI/Ollama selection, budget display, and export controls.

The mock assistant is a deterministic fixture and narrow-prompt interpreter. It is useful for the offline demonstration; it is not evidence of general document understanding.

## Milestones

| Milestone | Current state | Evidence / remaining gate |
| --- | --- | --- |
| M0 — Environment and skeleton | Complete | Windows/Python/Node/GPU inspected; app runs; early Visio feasibility experiment. `reports/m0-tests.xml`. |
| M1 — Model and synthetic pack | Complete | Canonical model, commands, SQLite history, deterministic fixtures. `reports/m1-tests.xml`; `fixtures/`. |
| M2 — Editable workbench | Passed | Actual pointer move/resize/connect/reconnect/delete, undo, save/reopen and three views pass with zero model requests. `reports/browser-tests.json`. |
| M3 — Ingestion and mock assistant | Passed offline | DOCX/PDF locators, deduplication, explicit partial coverage, review and questions. Live document batches and explicit continuation pass mocked-transport tests; real-provider document integration remains unverified. |
| M4 — Policies and adapters | Implemented; offline gate passed | Eight deterministic rules, 12 manual clauses, retrieval, provider adapters and persisted spending reservations. `reports/m4-tests.xml`. Live results below. |
| M5 — Prompt edits and consistency | Passed | Version conflict rejection, layout preservation, targeted edits, rejection/undo, derived outputs. `reports/m7-tests.xml`; `reports/browser-tests.json`. |
| M6 — Exports and patterns | Implemented; handover checks in progress | JSON/SVG/DOCX/Markdown/CSV, sanitised patterns and Windows Visio helper. `reports/m6-tests.xml`; `reports/exports/`; `docs/VISIO.md`. Native Visio remains unverified. |
| M7 — Verification and handover | In progress | Full offline gate passes. Setup scripts, README, demo and acceptance matrix supplied. Remaining: rendered document/SVG visual review, browser capacity measurement, native Visio checks and final archive. |

## Synthetic material generated

All six categories are present: three project packs (SoW and specification in DOCX and PDF), 20 fictional policy clauses, three view definitions plus narrative template, 24 licensed catalogue assets, two canonical reference models with derived outputs, and 12 development plus four frozen evaluation fixtures. Sources are explicitly synthetic. Deterministic regeneration is tested.

## Provider and environment evidence

| Area | Actual result |
| --- | --- |
| Mock / offline | Backend and browser checks pass in the recorded runs. Ordinary mouse edits, validation, layout and exports require no model call. |
| OpenAI `gpt-5.6-terra` | Latest paid smoke: extraction, native tool request and targeted edit all passed. Three calls, approximately **US$0.006948** using returned token counts and configured pricing; this is that run only, not the account bill. Earlier generation attempts are preserved separately. `reports/smoke-openai.json`. |
| Ollama `qwen3:4b` | Adapter connects and executes locally, but the latest generation/tool/edit smoke **failed validation**. Invalid proposals were rejected. It is not a passed local architecture-generation demonstration. `reports/smoke-ollama.json`. |
| Hardware | RTX 3080 Ti Laptop GPU, 16,384 MiB VRAM; 68,334,067,712 bytes system RAM. Ollama reported 3.2 GB, 100% GPU, 4,096 context. These are observed values, not peak-memory measurements. M2 Max has not been tested. |
| Native Visio | COM registration unavailable on this host. Helper provided; native shapes, glue/editing and VSDX save/reopen remain unverified. SVG is a separate export, not a substitute for editable Visio. |
| Document visual QA | PDF and DOCX generation exists. Final rendered-page inspection remains; DOCX rendering is constrained by unavailable LibreOffice. |

Cloud use remains explicit. The user's local settings allow the authorised Terra smoke tests with modest application limits; distributed defaults remain mock with cloud disabled. An API key alone never enables a paid test. No automatic escalation or local-to-cloud fallback is implemented.

## Remaining work before final handover

1. Align SVG appearance with the latest equipment canvas, then finish rendered PDF/DOCX visual QA where the host supports rendering.
2. Measure browser responsiveness at 50 components/100 interfaces; backend capacity evidence already exists.
3. Optionally verify a real-provider document batch within an explicitly authorised budget; mocked live batching tests already pass.
4. Run the native Visio checklist on a licensed host, finish the final M7 archive, and retain the explicit Ollama/Mac/DOCX limitations.

No measured human time savings or blanket compliance claims have been made. `docs/STATUS.md` is the concise engineering checkpoint log; this file is the readable current overview.
