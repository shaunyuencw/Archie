# Engineering checkpoint — 21 September 2026, Mac continuation

Mac presentation-prototype checkpoint. M0–M5 pass; M6 cross-platform exports and M7 Mac handover verified. Native Visio acceptance remains open. Estimated guided-demo readiness 90%; this is a judgement, not test coverage or production readiness. See `PROGRESS.md` and `docs/ACCEPTANCE.md`.

Implemented this pass: pnpm/Node/Python startup portability, stale-view cancellation and serialized local commands, backend redo/branch invalidation, canvas keyboard and clipboard/group edits, 16-unit snapping with Option bypass, explicit zone reassignment, draggable routes and dependable endpoint hit targets, inferred directional handles, non-overlapping external defaults, collapsible/resizable persisted panels/focus/search, compact visual hierarchy, deferred ELK loading, updated SVG/DOCX rendering, conservative provider scope evidence guard.

Final offline gate: **35 backend, 7 frontend unit, 12 browser journeys, TypeScript, production build — passed** (`reports/offline-gate.json`). Existing tests were retained. Additional evidence includes actual pointer groups, snapping, undo/redo/copy/paste/delete, input shortcut isolation, route/prompt preservation, zero model calls for canvas work and 50/100 capacity. Initial Mac baseline failure and previous Windows results retained separately.

Live: Terra A/B flows passed in four requests including one repair, estimated $0.0743975. Qwen3:14b small extraction passed (one request); richer flow failed safely (two attempts). Shared seven requests stayed below eight/$0.50. No escalation, cloud fallback or downloads. Report: `reports/mac-resume-20260921-providers.md`. Unsupported scope found in live-output review was corrected via offline replay and versioned commands in current saved demos; original evidence preserved.

Environment: macOS 26.6.2, M2 Max, 32 GiB, Python 3.12.0, Node 22.23.1, pnpm 11.19.0, Chromium 153.0.8010.12, Ollama 0.34.2. Qwen14B observed 10 GB loaded / 100% GPU / 8192 context, not peak sampling. Historical Windows RTX evidence remains in `reports/windows-checkpoint` and prior smoke reports.

QA: all source DOCX/PDF pages, three narrative pages and three SVG views inspected (`reports/mac-export-qa/review.json`). Browser capacity records 50 components/100 interfaces with intact references and zero provider requests. Initial application JS reduced to ~403 kB/~130 kB gzip; on-demand ELK chunk still triggers size warning. Starlette test client emits a dependency deprecation warning.

Remaining: P0 none known for verified guided Terra demo; P1 dense automatic-routing intersections, no alignment guides, full Ollama reliability; P2 licensed Windows native Visio and refreshed Windows execution. No native VSDX claim or measured human time savings.

Launch: `bash scripts/dev.sh`; offline gate: `bash scripts/test.sh`; initial dependencies: `bash scripts/setup.sh`. Handover archive excludes `.env`, local databases and dependencies. Next task: native-host Visio verification or scoped routing/local-model work. Do not rerun paid calls for wording/layout.
