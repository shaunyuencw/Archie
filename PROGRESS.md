# ARCHIE — progress

Updated: 22 September 2026, Mac continuation. **Presentable local prototype ready for a guided Terra-backed demonstration; estimated readiness 90%.** This is a product-readiness judgement, not a percentage of tests or a production-readiness claim. Full native-export acceptance remains open.

## Current checkpoint

The Mac offline gate passes: **145 backend tests, 33 frontend unit tests, 33 browser journeys, TypeScript and production build**. Evidence: `reports/offline-gate.json`, `reports/m7-tests.xml`, `reports/browser-tests.json`. The application runs at <http://127.0.0.1:5173/>. No model calls occur in the offline gate.

The restored checkpoint initially passed 25 backend tests, one frontend test and the build, but one browser journey failed due to a late view response. This was fixed alongside serialized local commands and captured file/project inputs, preventing rapid edits from using stale local state. External revision conflicts still reject. Baseline evidence is in `reports/mac-baseline`; earlier Windows reports and screenshots are preserved in `reports/windows-checkpoint` and historical live reports.

## Product changes

- Canvas-first light navy/blue workspace, compact header, collapsible/resizable panels, persistent panel preferences, focus mode, searchable compact component library.
- Undo and redo; Cmd/Ctrl copy, paste, duplicate and select-all; Delete/Backspace, Escape and arrow nudging. Typing fields keep their own shortcuts. Selection supports groups and marquee; group pointer moves commit together.
- 16-unit snapping with temporary Option/Alt bypass. Dragging never silently reassigns a deployment zone; Inspector reassignment remains a reviewed change.
- Connections use footprint-edge handles and zone-aware automatic handle selection. Selected connectors expose draggable segment controls; straight/right-angle styles, precise route coordinates and reliable endpoint reconnection remain editable. Unrelated prompts preserve manual routes and positions.
- New external components no longer receive identical default positions. ELK arrangement loads on demand and preserves locked placements. The initial JS bundle is about 469 kB; the separate ELK chunk remains large.
- SVG equipment/zone styling, handles, arrows, bounds and labels aligned with the canvas. Rendered narrative DOCX and all synthetic DOCX/PDF inputs reviewed on this Mac. SVG is a review image, not native Visio.
- Provider omissions/unsubstantiated scope stay unknown, with visible review findings. Saved live demo projects were corrected through versioned commands; original live reports remain unchanged.

## Product feedback follow-up

The default examples are now **Production service portal** (Client → Z1 application services → Z2 protected data) and **Robotics trial · Production + Testbed + AWS** (isolated wireless robot/tablet trial, explicit production API handoff, outbound AWS telemetry). The legacy VAP examples remain available for regression. Component library: 43 symbols grouped into six categories, including ten generic AWS service symbols and robotics/wireless equipment.

- Drag full right-angle connector segments; right-click for Straight line, Right-angle line or Reset route. Straight line clears old bends. SVG preserves the saved segments.
- The global library contains 42 fictional draft policies (11 available automated checks, 31 manual reviews). Each project selects its own set through a versioned, undoable edit. New projects and sanitised patterns start with none; legacy saved projects retain their original 20. Custom local drafts do not auto-apply. Portal selects 17 clauses; robotics selects 25.
- Instance counts draw stacked equipment with count badges. Redundancy arrangement is separately recorded; hosted virtual firewalls display beside their host. Self-hosting, cycles and an explicit redundancy arrangement with fewer than two instances reject.
- View names are Architecture, System overview and Connection details. Overview replaces the raw narrative panel with readable sections; Connections now edits traffic facts inline. Sources explains bundled demos, uploads and prompts, and exposes original passages. These are local evidence records, not automatically fetched company or web sources.
- Project deletion moves items to a local Trash; restoring retains sources and full edit history. Questions show all options as radio cards with explicit Save, an inline Other field and Not decided. Document confirmation explains the file/provider/cost/coverage, and proposed changes use a larger plain-language review dialog with optional technical details.
- New architecture proposals include a suggested project name, applied on acceptance and undoable; custom names are kept unless explicitly renamed. Empty Trash confirms permanent deletion and preserves spending records, active projects and shared sources. Optional AI policy review uses one explicit, budgeted request, validates source references and marks saved advice stale after changes. Mock demonstrates the review format without a model call.
- Portal and robotics layouts occupy 47% and 48% less area; labels appear 36% and 48% larger at the same laptop viewport. Existing saved layouts are preserved. See `reports/demo-pack-qa/compact-layout/review.json`.
- Panel arrows follow their state. Below 900 pixels, side panels start collapsed and open as overlays; the 640×800 browser case verifies usable drawing width and no body overflow.
- Four technical specifications in Markdown/DOCX/PDF and 15 follow-up prompts: `docs/DEMO_SCENARIOS.md`. Separate authored mock DOCX fixtures support repeatable offline import and rename journeys. Ordinary natural-language specs and broader prompts require a live provider and have **not** been live-tested for this new pack.
- Live document and prompt proposals convert one transport-qualified port such as `TCP 443` into canonical port `443`. Ambiguous values stay unknown with a review note; manual port errors now explain the required numeric value without exposing a raw schema trace. Reopen waits for queued saves.
- Follow-up user imports exposed another provider shape mismatch: connection enforcement arrived as `"unknown"` instead of a list. Unknown/null placeholders now produce an unspecified list with a review note; valid component references remain and unresolved references reject. Nullable unknown enums are normalized, and other field validation errors are readable. The local 90-second timeout was traced to a request still generating at about 12 tokens/second; the bounded default local response window now scales to output size. Regression tests use mocked transports; a fresh complete live import after these fixes is unverified. See `reports/provider-input-recovery-20260921.md`.

One bounded real OpenAI call verified the new advisory policy review; it cost an estimated US$0.01538 and preserved the accepted architecture (`reports/mac-policy-review-20260921.json`). All layout and wording work used no provider calls. The earlier prompt/document evidence below remains separate. Visual QA: 22 document pages and six current SVGs (`reports/demo-pack-qa/review.json`). New screenshots: `reports/archie-robotics-testbed.png` and `reports/archie-narrow-browser.png`. Dense Connection details labels can still partly cover short arrowheads; Architecture and System overview are clearer for the guided demo.

## Editor and background workflow checkpoint

- Ten swatches plus Default replace the color picker. Per-view box fill/border, text, connection and individual asset-icon colors persist through reopen, undo and SVG export.
- Drag connection labels independently, reset their positions from the context menu, resize boxes with visible handles and use right-click layer commands. Resizing a zone preserves its contents' absolute positions. Automatic routes try bounded clearance lanes around component footprints; saved manual routes remain authoritative.
- Policies are grouped by category. Draft reviews offer relevant unselected policies with reasons and explicit opt-in; these suggestions use local rules, while AI policy advice remains a separate explicit action.
- Importing a demo `followups.json` opens its prompt list. Choosing a prompt fills the editor without submitting it or changing provider.
- Prompts, document extraction and policy advice run as persisted background jobs. Project spinners, completion notifications, switching projects, reload recovery and cancellation are covered. Running cancellation waits for the current provider request to end and discards its result; it does not terminate the shared Ollama daemon.
- History keeps accepted/rejected proposals and their prompts after reload or notification dismissal. Resolving a proposal clears its submitted text, preserving any different next prompt already typed.
- The latest Ollama failure hit the fixed 1,536-output-token cap. The 8K profile now allocates remaining estimated context, up to 3,720 output tokens within a bounded 480-second window, with shorter output instructions. Truncated responses preserve token accounting and do not trigger automatic replay. **A fresh live full generation after this adjustment remains unverified.**

This checkpoint used no additional live model calls, downloads or paid checks. Details and visual evidence: `reports/editor-background-followup-20260921.md`, `reports/presentation-qa/review.json`.

## Shared layers and dark mode

Assets, components, system boxes, zones, connectors and connection labels now expose the four layer commands. Lines and equipment share a stack, with their saved order preserved on selection, undo, reopen and SVG export. Zone movement carries its contents; children remain above their own zone. Selected endpoint handles float above the drawing independently, preserving reconnection while a line stays behind other objects.

A remembered Light/Dark toggle now covers the canvas and the surrounding application. Default icons, labels, forms, tables and dialogs adapt; explicit object palette colors and exported presentation remain unchanged. Browser checks hit-test overlapping lines/labels/components and verify theme persistence, palette preservation and contrast on key surfaces. Screenshot: `reports/archie-dark-mode.png`; export QA: `reports/layers-theme-qa/`. No new model calls.

Mini-map follow-up (22 September): matched its SVG and panel dimensions to remove clipping, enabled drag panning and wheel zoom, added click-to-centre and a theme-aware viewport outline. Navigation preserves architecture/layout state and makes no model calls.

Browser branding (22 September): the existing robot mascot is also the favicon. TypeScript, production build, and browser checks of the favicon link, served PNG and decoded image pass in development and the production build (`reports/favicon-qa-20260922.json`). Its provenance remains in `apps/web/public/brand/README.md`.

Document retry follow-up (22 September): a saved source alone no longer blocks live interpretation. Mock can save source text without producing an accepted design; explicitly uploading it with Ollama or OpenAI now prepares a reviewable proposal and reuses its source ID. Existing candidate evidence and original passage locators remain intact when local-model batches split long sections. Already accepted facts still avoid duplicate model calls within that project, with an explanation and a link through to Sources for remaining sections. Parsing-cache reuse never counts as another project's accepted design. Regression coverage uses mocked adapters; no fresh live Ollama reliability claim is made.

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

Eight agent-run provider validation requests in this continuation: five cloud and three local, within the eight-request / $0.50 test ceiling. Combined estimated OpenAI cost for those checks is **US$0.0897775**, using returned usage and configured rates, not an account bill. The eighth request was the new three-policy portal review, capped at US$0.075 with no retries. Subsequent user-initiated imports are separate from this validation total. No paid re-run was used for UI iteration or the scope fix; saved output was replayed offline. Source citations remain subject to human interpretation review.

The ignored `.env` now uses the requested 32,000 input / 6,000 output, six calls/action and $0.50/$1/$5/$12 action/document/day/project ceilings, with Terra/cloud/live opt-in. These are ceilings, not targets. Startup still selects mock. Distributed defaults remain mock/cloud-disabled. A key alone never authorizes paid calls.

## Environment and visual evidence

Mac: **macOS 26.6.2, Apple M2 Max, 32 GiB memory, Python 3.12.0, Node 22.23.1, pnpm 11.19.0, Chromium 153.0.8010.12, Ollama 0.34.2**. Shell defaults Node 21.5.0/Python 3.10.9 were unsuitable; launch/setup selects installed supported runtimes without changing shell configuration. Setup uses the shipped pnpm lockfile. `reports/environment-mac.json`.

Previous Windows host: Windows 11, Python 3.12.4, Node 24.19.0, RTX 3080 Ti Laptop GPU with 16,384 MiB VRAM, 68,334,067,712 bytes RAM. This evidence has not been reinterpreted as Mac results.

Laptop/workspace screenshots: `reports/archie-mac-1280.png`, `reports/archie-mac-laptop.png`, `reports/archie-mac-focus.png`, `reports/archie-workbench.png` (1280×800, 1440×900 and 1600×1000; no horizontal overflow at 1280). Export visual evidence: `reports/mac-export-qa/review.json` (three SVG views, three narrative DOCX pages, 12 source PDF pages, 12 source DOCX pages).

Capacity: 50 components / 100 interfaces load, edit, drag and reopen with intact references and zero model calls. Latest full-gate sample: render about 399 ms, saved/rendered placement edits 872–945 ms, reopen 271 ms, 60 drag frame samples p95 16.7 ms / max 66.7 ms. Timings include Playwright/poll overhead and parallel-test contention; they are not INP or guaranteed performance. `reports/browser-capacity-darwin.json`.

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

**Demo:** the two new prepared scenarios, global policy applicability and optional advisory review, readable proposal/name review, Trash/restore, editable Connections, the authored mock import/follow-up journey, or the previously verified saved Terra prompt/document projects, clarification and source evidence, targeted changes, canvas selection/duplicate/undo/redo, draggable routes, panels/focus, three views and reviewed exports. See `docs/DEMO.md` and `docs/EDITOR.md`.

- **P0:** no known blocker to the verified guided Terra demonstration.
- **P1:** richer Ollama generation remains unreliable; overlapping dense geometry and connector crossings can still defeat bounded automatic route clearance; no alignment-guide overlay. Segment dragging and straight lines are the practical routing controls. Cross-project clipboard and System overview aggregate duplication are not supported.
- **P2:** native VSDX shapes/glue/edit/save/reopen require a licensed compatible Windows/Visio host. SVG is not equivalent. Windows-specific shortcut variants are implemented but this pass executed on Mac Chromium.

Launch on this Mac:

```sh
cd /Users/shauny/Developer/Archie
bash scripts/setup.sh  # only when dependencies need installing
bash scripts/dev.sh
```

Open <http://127.0.0.1:5173/>. Verification: `bash scripts/test.sh`. Keep the launcher running; Ctrl+C stops it. Next useful task: native Visio verification on the appropriate host, or an explicitly opted-in focused local-model verification without repeating paid calls merely for presentation.
