# Editor and background workflow follow-up — 21 September 2026

This checkpoint addresses movable connection labels, overlapping routes, policy-library categories, prompt-pack imports, background work, cancellation, per-project review history, box resizing/layers, and a ten-color palette including individual asset icons.

Presentation remains separate from the canonical architecture. Label offsets, safe hex colors, box dimensions and layer order are per-view saved commands. SVG uses the same saved custom label anchor, icon alpha masks and colors; label overlays render above opaque boxes. Automatic orthogonal routing tries bounded clearance lanes around component footprints. Dense overlaps and crossing connectors still need manual adjustment.

Background work is persisted in SQLite, with two workers, a maximum of eight active/queued actions, and one active action per project. A browser reload preserves results. Server restarts mark interrupted actions without replaying them. Accepted architecture changes require explicit proposal acceptance. Policy suggestions use deterministic relevance rules and remain unchecked until chosen; selecting them and accepting a proposal is one undoable command. Optional model policy advice is separate.

Cancellation is immediate for queued jobs. Running jobs remain `cancelling` until the worker exits, discard late results, and retain usage accounting. Transactional guards prevent post-cancellation proposal/source writes. The synchronous provider transport has no safe immediate remote termination; ARCHIE does not stop the shared Ollama daemon. Cancelled unpublished drafts are excluded from the user's accepted/rejected review history.

History persists accepted/rejected proposals and prompts after activity dismissal and browser reload. Undo keeps the original review decision. Resolving a follow-up clears only its submitted prompt, preserving a different prompt already typed for the next edit.

The reported Ollama output-limit failure exposed a fixed 1,536-token local cap. The 8K profile now sizes output against remaining estimated context, the user limit, a 512-token reserve and a bounded 480-second response window (maximum 3,720 output tokens). The 4K profile, explicit deadlines, spending limits and provider separation remain intact. A length-limited response records available token counts as truncated and is not repaired by automatic replay. Shorter wire instructions reduce repeated claims and default fields while retaining source and scope checks.

No new live model call, paid call, model download, hardware benchmark or native Visio verification was performed for this checkpoint. Earlier live evidence remains separate; full local generation after this adjustment is unverified.

Visual evidence: `archie-presentation-palette.png`, `archie-change-history.png`, `archie-background-projects.png`, `archie-cancel-action.png`, and `presentation-qa/colors-and-labels.png`. The standalone SVG is an image export, not an editable Visio document.

Final Mac offline gate: **131 backend tests, 25 frontend unit tests, 29 browser journeys, TypeScript and production build passed**. Evidence: `offline-gate.json`, `m7-tests.xml`, `browser-tests.json`. The gate disables cloud/live calls and uses mocked transports. Initial application JS is 463.91 kB; deferred ELK remains 1,419.88 kB and emits a chunk warning. FastAPI startup hooks and the Starlette test client emit deprecation warnings.

Regression work also fixed connector/menu flicker: graph refreshes retain measured handle geometry when dimensions and node role are unchanged, while resized boxes are remeasured. Pointer tests select exposed rendered strokes and avoid draggable label overlays; they retain real hit-testing and assert generation-request counts against the new background endpoints.

The local API was restarted with no active jobs, then health, job listing and project history were checked successfully. Readiness remains an estimated 90% for a guided prototype demonstration, with full local-model reliability and native Visio still open.
