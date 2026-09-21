# ARCHIE — progress

Updated: 21 September 2026, Mac continuation. **Presentable local prototype ready for a guided Terra-backed demonstration; estimated readiness 90%.** This is a product-readiness judgement, not a percentage of tests or a production-readiness claim. Full native-export acceptance remains open.

## Current checkpoint

The Mac offline gate passes: **35 backend tests, 7 frontend unit tests, 12 browser journeys, TypeScript and production build**. Evidence: `reports/offline-gate.json`, `reports/m7-tests.xml`, `reports/browser-tests.json`. The application runs at <http://127.0.0.1:5173/>. No model calls occur in the offline gate.

The restored checkpoint initially passed 25 backend tests, one frontend test and the build, but one browser journey failed due to a late view response. This was fixed alongside serialized local commands and captured file/project inputs, preventing rapid edits from using stale local state. External revision conflicts still reject. Baseline evidence is in `reports/mac-baseline`; earlier Windows reports and screenshots are preserved in `reports/windows-checkpoint` and historical live reports.

## Product changes

- Canvas-first light navy/blue workspace, compact header, collapsible/resizable panels, persistent panel preferences, focus mode, searchable compact component library.
- Undo and redo; Cmd/Ctrl copy, paste, duplicate and select-all; Delete/Backspace, Escape and arrow nudging. Typing fields keep their own shortcuts. Selection supports groups and marquee; group pointer moves commit together.
- 16-unit snapping with temporary Option/Alt bypass. Dragging never silently reassigns a deployment zone; Inspector reassignment remains a reviewed change.
- Connections use footprint-edge handles and zone-aware automatic handle selection. Selected connectors expose draggable waypoints; straight/right-angle styles, precise route coordinates and reliable endpoint reconnection remain editable. Unrelated prompts preserve manual routes and positions.
- New external components no longer receive identical default positions. ELK arrangement loads on demand and preserves locked placements. The initial JS bundle is about 403 kB (130 kB gzip); the separate ELK chunk remains large.
- SVG equipment/zone styling, handles, arrows, bounds and labels aligned with the canvas. Rendered narrative DOCX and all synthetic DOCX/PDF inputs reviewed on this Mac. SVG is a review image, not native Visio.
- Provider omissions/unsubstantiated scope stay unknown, with visible review findings. Saved live demo projects were corrected through versioned commands; original live reports remain unchanged.

## Real provider evidence

| Area | Actual result |
| --- | --- |
| OpenAI `gpt-5.6-terra` | **Flow A and Flow B passed** using actual application orchestration; browser editing tested separately. Four requests including one bounded repair, approximately **US$0.0743975** from returned token counts/configured prices. `reports/mac-resume-20260921-providers.md`. |
| Flow A | Plain-language extraction → push/pull clarification → accepted editable model → manual placement/route → targeted rename. Three views, narrative and CSV agree; unrelated layout is unchanged. |
| Flow B | Synthetic B SoW DOCX → 8 components / 4 interfaces / 32 exact source claims → clarification → relevant policy retrieval and 8 deterministic checks / 12 manual clauses. Unknown sizing, initiation, ports and delivery remain explicit. |
| Ollama `qwen3:14b` | Already installed 14.8B Q4_K_M. A small one-component extraction/proposal passed in one request (43.931 s warm). A richer two-component journey failed safely after two attempts. **Do not demo the full local workflow as reliable.** |
| Mac local memory | Ollama observed 10 GB loaded, 100% GPU, 8,192 context. This is not a peak memory measurement. No model downloads or cloud fallback. |
| Historical Windows OpenAI | Previous three-call Terra smoke passed at about $0.006948; `reports/smoke-openai.json` retained. |
| Historical Windows Ollama | Qwen3:4b generation/tool/edit smoke failed validation; earlier 3.2 GB / 100% GPU / 4K observation retained. |

Seven provider requests total in this continuation: four cloud and three local, under a shared eight-request / $0.50 test ceiling. No paid re-run was used for UI iteration or the scope fix; saved output was replayed offline. Source citations remain subject to human interpretation review.

The ignored `.env` now uses the requested 32,000 input / 6,000 output, six calls/action and $0.50/$1/$5/$12 action/document/day/project ceilings, with Terra/cloud/live opt-in. These are ceilings, not targets. Startup still selects mock. Distributed defaults remain mock/cloud-disabled. A key alone never authorizes paid calls.

## Environment and visual evidence

Mac: **macOS 26.6.2, Apple M2 Max, 32 GiB memory, Python 3.12.0, Node 22.23.1, pnpm 11.19.0, Chromium 153.0.8010.12, Ollama 0.34.2**. Shell defaults Node 21.5.0/Python 3.10.9 were unsuitable; launch/setup selects installed supported runtimes without changing shell configuration. Setup uses the shipped pnpm lockfile. `reports/environment-mac.json`.

Previous Windows host: Windows 11, Python 3.12.4, Node 24.19.0, RTX 3080 Ti Laptop GPU with 16,384 MiB VRAM, 68,334,067,712 bytes RAM. This evidence has not been reinterpreted as Mac results.

Laptop/workspace screenshots: `reports/archie-mac-1280.png`, `reports/archie-mac-laptop.png`, `reports/archie-mac-focus.png`, `reports/archie-workbench.png` (1280×800, 1440×900 and 1600×1000; no horizontal overflow at 1280). Export visual evidence: `reports/mac-export-qa/review.json` (three SVG views, three narrative DOCX pages, 12 source PDF pages, 12 source DOCX pages).

Capacity: 50 components / 100 interfaces load, edit, drag and reopen with intact references and zero model calls. Latest full-gate sample: render about 894 ms, saved/rendered placement edits 217–445 ms, reopen 127 ms, 60 drag frame samples p95 16.8 ms / max 66.7 ms. Timings include Playwright/poll overhead and parallel-test contention; they are not INP or guaranteed performance. `reports/browser-capacity-darwin.json`.

## Milestones

| Milestone | State and evidence |
| --- | --- |
| M0 | Passed, now also verified on Mac; startup/environment evidence retained per host. |
| M1 | Passed; canonical contract and all six synthetic categories retained, deterministic generation tests pass. |
| M2 | Passed; expanded keyboard/panels/groups/snapping/route/reconnect browser journeys. |
| M3 | Passed offline and real Terra prompt/DOCX integration; source/unknown/review behavior retained. |
| M4 | Passed offline, real Terra passed; local provider limitation separately recorded. |
| M5 | Passed; stale changes reject, targeted prompts preserve manual layout and routes, derived outputs agree. |
| M6 | Cross-platform exports implemented and visually checked. Native editable Visio remains **unverified**. |
| M7 | Mac verification and handover completed; full acceptance remains conditional on the outstanding native host check. Source archive: `reports/handover.zip`. |

F01–F10 and T01–T16 are individually recorded in `docs/ACCEPTANCE.md`. No time-savings study, real-world accuracy or organisational compliance approval is claimed.

## Demo and remaining priorities

**Demo:** saved Terra prompt/document projects, clarification and source evidence, targeted changes, canvas selection/duplicate/undo/redo, draggable routes, panels/focus, three views and reviewed exports. See `docs/DEMO.md` and `docs/EDITOR.md`.

- **P0:** no known blocker to the verified guided Terra demonstration.
- **P1:** richer Ollama generation remains unreliable; automatic routes can cross unrelated equipment in dense/SV-1 views; no alignment-guide overlay. Manual waypoints are the practical routing control. Cross-project clipboard and SV-1 aggregate duplication are not supported.
- **P2:** native VSDX shapes/glue/edit/save/reopen require a licensed compatible Windows/Visio host. SVG is not equivalent. Windows-specific shortcut variants are implemented but this pass executed on Mac Chromium.

Launch on this Mac:

```sh
cd /Users/shauny/Developer/Archie
bash scripts/setup.sh  # only when dependencies need installing
bash scripts/dev.sh
```

Open <http://127.0.0.1:5173/>. Verification: `bash scripts/test.sh`. Keep the launcher running; Ctrl+C stops it. Next useful task: native Visio verification on the appropriate host, or a focused routing/local-model improvement pass without repeating paid calls merely for presentation.
