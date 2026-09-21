# Five-minute demo

1. Open <http://127.0.0.1:5173/> with **Mock** selected. Choose **Load demo A**. Archie appears beside the assistant controls. The reference is explicitly synthetic.
2. Inspect Logical, SV-1-style and SV-2-style. Logical groups components by zone; SV-1 aggregates systems and parallel interfaces; SV-2 exposes protocol and session initiator separately from flow direction.
3. Select VMS, change its name, move it, and save/reopen. Inspect Interfaces and Narrative; they reflect the same semantic revision. Manual layout changes have their own view revisions.
4. Enter `Add one configuration workstation; keep the layout.` Choose Preview proposed changes, inspect Details, and Accept changes. Repeat with a second proposal and Reject it. Use Undo. Existing manually positioned objects should stay put.
5. Create a New project and upload `fixtures/projects/B/spec.docx`. Review extracted changes before accepting. Open Sources to inspect paragraph/table locators and remaining sections. Answer a clarification with Not decided; it persists without becoming a confirmed fact.
6. Inspect Findings. Eight fictional rules run independently of the retrieved clauses, and 12 clauses require manual review. Unknowns and potential conflicts remain visible.
7. Export JSON, SVG, narrative DOCX/Markdown and CSV. Export a sanitised pattern, then use Open project / pattern JSON to reopen it as a new project. Evidence and project-specific addresses are excluded from the pattern.

Demo A is the complete baseline; B has incomplete/conflicting facts. Pack C adds availability and dependency variations for ingestion tests. Do not present deterministic mock extraction as general AI capability.

Optional live demonstration: explicitly select OpenAI with authorised configuration, then ask `Add one workstation named Review station with role workstation. Its zone is unspecified.` A reviewed proposal is the success criterion. The recorded Terra smoke passed this and a targeted rename. Qwen's latest generation smoke failed validation; use its report to discuss limits rather than presenting a false success.

Native Visio requires a separate licensed Windows desktop and the checklist in `VISIO.md`. Generated SVGs remain review images.
