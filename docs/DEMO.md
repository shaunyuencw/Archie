> For the current product examples, start with **Production portal** and **Robotics testbed** in the sidebar. See [Synthetic demo scenarios](DEMO_SCENARIOS.md) for four technical specifications, offline authored inputs and 15 follow-up prompts. The VAP references below remain available under **Legacy examples** for regression and historical provider evidence.

# Five-minute demo

1. Open <http://127.0.0.1:5173/> with **Mock** selected. Expand **Legacy examples** and choose **Load demo A**. Archie appears beside the assistant controls. The reference is explicitly synthetic.
2. Inspect Architecture, System overview and Connection details. Architecture groups components by zone; System overview aggregates systems and parallel interfaces; Connection details exposes protocol and session initiator separately from flow direction.
3. Collapse the Inspector or choose Focus canvas. Select VMS, move it with snapping (Option/Alt bypasses), duplicate it with Cmd/Ctrl D, then Undo/Redo. Select a connector and drag one of its segment handles. Change its line style, reconnect an endpoint, and save/reopen. Inspect Connections and Overview; they reflect the same semantic revision. Manual layout changes have their own view revisions.
4. Enter `Add one configuration workstation; keep the layout.` Choose Preview proposed changes, inspect Details, and Accept changes. Repeat with a second proposal and Reject it. Use Undo. Existing manually positioned objects should stay put.
5. Create a New project and upload `fixtures/projects/B/spec.docx`. Review extracted changes before accepting. Open Sources to inspect paragraph/table locators and remaining sections. Answer a clarification with Not decided; it persists without becoming a confirmed fact.
6. Inspect Findings. Eight fictional rules run independently of the retrieved clauses, and 12 clauses require manual review. Unknowns and potential conflicts remain visible.
7. Export JSON, SVG, narrative DOCX/Markdown and CSV. Export a sanitised pattern, then use Open project / pattern JSON to reopen it as a new project. Evidence and project-specific addresses are excluded from the pattern.

Demo A is the complete baseline; B has incomplete/conflicting facts. Pack C adds availability and dependency variations for ingestion tests. Do not present deterministic mock extraction as general AI capability.

Live demonstration: create a **New** project and explicitly select **OpenAI**. Use this verified Flow A input:

> SYNTHETIC demonstration. Create a draft with two applications: Event manager (role event management) and External console (role external command system, external scope). Event manager sends events to External console. Event delivery method, session initiator, protocol, port, deployment zones and equipment quantities are not decided. Preserve these unknowns.

Review and accept, answer the event-delivery clarification, manually move a component and adjust a route, then prompt: `Rename External console to Review console. Keep every other fact unchanged.` Review the targeted change, then inspect Overview and Connections. To show Flow B, create another project, select OpenAI, upload `fixtures/projects/B/sow.docx`, review the cost preflight, interpret and accept, then inspect exact Sources, questions and Policy checks. The recorded four-call Mac run cost about $0.0744; another demo is a new paid run within configured ceilings.

The saved local projects **ARCHIE openai live prompt journey** and **ARCHIE openai live document journey** can demonstrate the accepted results without additional model calls. Unsupported scope values were corrected through versioned commands; original live snapshots remain historical evidence. For another machine, import `flow-a-current-project.json` or `flow-b-current-project.json` from `reports/mac-resume-20260921-openai`; these include the reviewed scope corrections.

Do not demo a full Ollama workflow as reliable: Qwen3:14b passed only a small extraction; its richer journey failed safely. Also do not claim automatic obstacle-free routing, organisation-approved compliance, production readiness or measured human time savings.

Native Visio requires a separate licensed Windows desktop and the checklist in `VISIO.md`. Generated SVGs remain review images.
