# Editor controls

The canvas is the main workspace. Collapse either side panel with its header button, or use the two panel controls beside the content tabs. **Focus canvas** hides both panels and restores their previous state. Drag the panel divider, or focus it and use left/right arrows, to resize. Panel state and width stay in this browser's local storage.

Click a component or connector to inspect it. Shift/Cmd/Ctrl-click adds to selection; drag empty canvas space for marquee selection. Drag a selected component to move the group. Hold Space to pan, or use the middle/right mouse button. The grid snaps to 16 diagram units; Option/Alt temporarily bypasses it. Arrow keys nudge by one unit, Shift+arrow by ten.

The bottom-right **diagram overview** shows the whole layout and outlines your current viewport. Click it to centre the canvas on that spot, drag to pan, or scroll over it to zoom. Navigation changes only your view; it does not move components or create architecture edits. It works in light and dark mode.

With the canvas focused:

| Action | macOS | Windows |
| --- | --- | --- |
| Undo | Cmd Z | Ctrl Z |
| Redo | Cmd Shift Z | Ctrl Shift Z or Ctrl Y |
| Copy / paste | Cmd C / Cmd V | Ctrl C / Ctrl V |
| Duplicate | Cmd D | Ctrl D |
| Select all | Cmd A | Ctrl A |
| Delete | Backspace or Delete | Backspace or Delete |
| Clear selection / cancel segment drag | Escape | Escape |

Typing fields retain their native shortcuts. Delete asks before removing selected objects and connected interfaces. A group edit is one undo step. New edits after undo discard the abandoned redo branch. Stale externally changed revisions still reject.

Copy/paste is an internal, same-project clipboard, available in Architecture and Connection details. Selecting a zone copies its contained components; connectors between copied components retain remapped references. Copies are proposed, have no asserted original source evidence, and have unknown quantities. System overview aggregates are edited through their individual components in another view.

Dragging a component across a zone changes its **layout only**. Use **Deployment zone** in the Inspector to propose an architectural reassignment, then review and accept it. Arrangement preserves locked manual placements and uses ELK for unlocked top-level objects. It is not a full obstacle-avoiding router.

Select a right-angle connector to reveal handles along its segments. Drag a segment sideways: both of its corners move together. Arrow keys move a focused segment handle; Option/Alt bypasses snapping. Right-click the line for **Straight line**, **Right-angle line** or **Reset route**. Straight line clears its previous bends and can run at any angle. The Inspector also exposes line style and exact route coordinates. Reconnecting clears only that connector's manual route. Unrelated prompt edits preserve manual routes and node positions.

Drag a connection's text label to move it independently of its line. A focused label also accepts arrow keys; Option/Alt uses a smaller nudge. Right-click for **Reset label position**. Label positions are saved per view, can be undone, and carry through to SVG export. Automatic right-angle routes try clearance lanes around component footprints; a saved manual route stays where you put it. **Reset route** returns it to automatic routing.

Select a component, system box or zone to change **Box fill color**, **Box border color** and **Box text color** in the Inspector. Components and system boxes also offer **Asset icon color**. Select a connection for **Line color** and **Connection label color**. Choose one of ten color swatches, or **Default** to restore that field. These are per-object, per-view presentation choices: they save, undo and export without changing component facts or the shared asset library.

Select a box to expose its resize corners and edges. Resizing from the top or left saves its changed position as well as its dimensions; zone contents keep their positions when the boundary moves. Right-click any component, asset, system box, zone, connection or connection label for **Bring to front**, **Bring forward**, **Send backward** or **Send to back**. Components and lines share one stack; a connection’s label follows its line. Layer order is saved per view, can be undone, and carries through to SVG. A zone moves with its contents; a contained component stays above its own zone. Selecting an object does not change its saved layer. Connection endpoint handles float above the drawing so you can still reconnect a selected line that is behind another object.

In the Inspector, **Instance count** controls the stacked symbol and count badge. **Redundancy arrangement** separately records active/standby, active/active or undecided; a stack alone does not prove high availability. Choose **Virtual appliance / machine** and **Hosted on** for a virtual firewall to show its badge next to the host. References are validated; self-hosting and host cycles reject.

The component library groups Compute, Networking, Security, Devices & robotics, AWS, and Boundaries & other. Search combines with the category filter. The 10 AWS assets use generic Lucide-based symbols with service names, not official AWS architecture icons.

The main views are **Architecture**, **System overview** and **Connection details** (the saved IDs remain `logical`, `sv1`, `sv2`). **Connections** is an editable design table: endpoints, purpose, transport/port, session initiator, direction and enforcement references. Saving uses the same validated, undoable commands as the canvas. **Overview** summarises the accepted design in readable sections. **Sources** explains each document or prompt's origin and exposes original passages and review states. Bundled demo sources are synthetic local files; ARCHIE does not fetch organisation policies or web sources automatically.

Known presentation limits: no alignment-guide overlay; dense or overlapping equipment can leave no clear automatic route. Connector-to-connector and label overlaps still need manual adjustment. Drag a segment or label, or choose a straight line for a presentation. SVG respects stored handles, label offsets and colors, but is not pixel-identical to React Flow and is not editable native Visio.

At widths below 900 pixels the app starts with panels collapsed. Opening a panel overlays the canvas, preserving useful drawing space in a narrow in-app browser. Panel toggle arrows follow the current open/closed state.

## Projects, questions and proposal review

Choose a saved project in the sidebar and use its trash button to remove it from the active list. **Trash** lists deleted projects with a Restore action. Restoration preserves the full accepted model, sources, claims and undo/redo history. **Empty Trash** shows the project names and asks for confirmation before permanently deleting their models, history and unshared cached content. Spending records remain so deletion cannot reset budget limits. Active projects, shared sources and global policies are retained. Projects with an action still running must finish before they can be purged.

When Archie generates an architecture for a new, untitled project, it also proposes a short project name. The name appears in the review dialog and applies when you accept; undo restores the previous name. A custom project name is preserved unless your prompt explicitly asks to rename the project.

Clarification questions show every option as a radio card. **Other** opens a text field; **Not decided yet** leaves the detail unresolved. Choose an answer and click **Save answer**. Answer labels can use component names while the saved references remain canonical.

Document preflight explains which file and provider will be used, any partial or unreadable coverage, and the maximum cloud cost. The resulting proposal opens in a wider review dialog with readable additions, updates, removals, named endpoints, zone placement and known deployment counts. Unknown facts remain explicit. Raw operations are available only under **Technical details**. **Review later** keeps the proposal pending; **Accept changes** applies the validated versioned transaction and **Reject** leaves the design unchanged.

The dialog also shows **Suggested policies for this draft** when the proposed architecture has relevant policies that are not already selected. Each suggestion explains its connection to the recorded components, zones or interfaces. These suggestions come from built-in relevance rules; they are not an AI compliance verdict. Nothing is selected automatically. Tick the policies that apply, then **Accept changes** to save the architecture and those policy selections together. Undo restores both. Rejecting the draft adds neither the architecture changes nor the suggested policies.

**History** lists each project's accepted and rejected proposals with its prompt or document name, revision and readable change summary. Dismissing an activity notice does not erase this history. Undo keeps the original acceptance decision in the history while reverting the design. Accepting or rejecting a follow-up clears its submitted prompt from the editor; a different next prompt you have already typed is preserved.

## Prompt packs and background work

Use **Open project / pattern / prompt pack JSON** to open a scenario's `followups.json`. The prompt pack appears beside the prompt editor with its expected effects and provider guidance. **Use prompt 1**, **Use prompt 2**, and the other numbered buttons only fill the editor. They do not run the prompt, change the provider, or import a new architecture. Check the current project, prompt and provider, then click **Preview proposed changes** when ready.

Prompt generation, document interpretation and optional policy review run as background actions. A working indicator identifies the project being processed, and you can open another project while it runs. An in-app notice names the project when its draft or review is ready. Choose **Review draft** to inspect a pending proposal, or **Open project** to return to the relevant workspace. Completion never accepts architecture changes automatically.

Use **Cancel** on the activity row to stop an action. A queued action cancels before processing. A running action shows **Stopping…** until its worker exits; its late result is discarded and your accepted design stays unchanged. Requests already received by a provider may continue processing or incur costs. Cancellation retains usage accounting and never stops the shared Ollama service. A project cannot start another action while its previous one is still stopping.

Job status and completed results are saved locally, so reloading the browser does not discard them. The backend must remain running for work to continue. If ARCHIE's server restarts before an action finishes, it marks that action interrupted and shows the failure message. It does not automatically replay the request; review the state before starting a new action yourself.

You can reuse the same specification in a new project, including after deleting the old project. The shared cache only avoids reparsing the file. If Mock saved a document without an accepted design, select Ollama or OpenAI and upload it again to request a live proposal. If that document already has accepted facts in the current project, ARCHIE skips a duplicate model call; choose **Open project** on its notice to view **Sources**, then **Process next sections** if text remains.

## Global policies and project selection

**Policies** opens the shared local library. Browse **Network & access**, **Cloud & hybrid connections**, **Data, secrets & backups**, **Resilience & monitoring**, **Devices & testbeds**, or **Ownership & operations**. Category counts reflect the current search and the number selected. Locally authored drafts join a category when their tags match; unmatched drafts appear under **Other local drafts**.

Search and category changes preserve your pending checkbox selections. **Selected only** narrows the list, while **All categories** removes the category filter. Click **Apply to project** to save the selection for this project, or **Discard selection changes** to return to its saved choices. Saving a new local policy draft adds it to the shared library but does not apply it to any project. The optional AI policy review is separate from these relevance suggestions and from the automated fact checks.

The prepared portal and robotics diagrams now occupy about half their previous area, making labels larger when fitting the whole architecture on screen. Open a fresh worked example to see the compact layout; saved project placements are preserved. **Arrange** also uses tighter spacing and retains locked placements.

## Light and dark mode

Use the **Light / Dark** button in the top bar to switch themes. ARCHIE remembers this device preference after reload and synchronises it across open tabs. The canvas, component library, inspector, menus, tables and proposal dialogs adapt together. Explicit colors from your ten-color palette remain unchanged; default text and icons adapt to keep custom box fills readable. Theme changes make no model calls and do not alter the saved architecture or exported document colors.
