# Editor controls

The canvas is the main workspace. Collapse either side panel with its header button, or use the two panel controls beside the content tabs. **Focus canvas** hides both panels and restores their previous state. Drag the panel divider, or focus it and use left/right arrows, to resize. Panel state and width stay in this browser's local storage.

Click a component or connector to inspect it. Shift/Cmd/Ctrl-click adds to selection; drag empty canvas space for marquee selection. Drag a selected component to move the group. Hold Space to pan, or use the middle/right mouse button. The grid snaps to 16 diagram units; Option/Alt temporarily bypasses it. Arrow keys nudge by one unit, Shift+arrow by ten.

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

In the Inspector, **Instance count** controls the stacked symbol and count badge. **Redundancy arrangement** separately records active/standby, active/active or undecided; a stack alone does not prove high availability. Choose **Virtual appliance / machine** and **Hosted on** for a virtual firewall to show its badge next to the host. References are validated; self-hosting and host cycles reject.

The component library groups Compute, Networking, Security, Devices & robotics, AWS, and Boundaries & other. Search combines with the category filter. The 10 AWS assets use generic Lucide-based symbols with service names, not official AWS architecture icons.

The main views are **Architecture**, **System overview** and **Connection details** (the saved IDs remain `logical`, `sv1`, `sv2`). **Connections** is an editable design table: endpoints, purpose, transport/port, session initiator, direction and enforcement references. Saving uses the same validated, undoable commands as the canvas. **Overview** summarises the accepted design in readable sections. **Sources** explains each document or prompt's origin and exposes original passages and review states. Bundled demo sources are synthetic local files; ARCHIE does not fetch organisation policies or web sources automatically.

Known presentation limits: no alignment-guide overlay; complex automatic routes can cross unrelated equipment, especially in System overview. Drag a segment or choose a straight line for a presentation. SVG respects stored handles and anchors, but is not pixel-identical to React Flow and is not editable native Visio.

At widths below 900 pixels the app starts with panels collapsed. Opening a panel overlays the canvas, preserving useful drawing space in a narrow in-app browser. Panel toggle arrows follow the current open/closed state.

## Projects, questions and proposal review

Choose a saved project in the sidebar and use its trash button to remove it from the active list. **Trash** lists deleted projects with a Restore action. Restoration preserves the full accepted model, sources, claims and undo/redo history. **Empty Trash** shows the project names and asks for confirmation before permanently deleting their models, history and unshared cached content. Spending records remain so deletion cannot reset budget limits. Active projects, shared sources and global policies are retained. Projects with an action still running must finish before they can be purged.

When Archie generates an architecture for a new, untitled project, it also proposes a short project name. The name appears in the review dialog and applies when you accept; undo restores the previous name. A custom project name is preserved unless your prompt explicitly asks to rename the project.

Clarification questions show every option as a radio card. **Other** opens a text field; **Not decided yet** leaves the detail unresolved. Choose an answer and click **Save answer**. Answer labels can use component names while the saved references remain canonical.

Document preflight explains which file and provider will be used, any partial or unreadable coverage, and the maximum cloud cost. The resulting proposal opens in a wider review dialog with readable additions, updates, removals, named endpoints, zone placement and known deployment counts. Unknown facts remain explicit. Raw operations are available only under **Technical details**. **Review later** keeps the proposal pending; **Accept changes** applies the validated versioned transaction and **Reject** leaves the design unchanged.

The prepared portal and robotics diagrams now occupy about half their previous area, making labels larger when fitting the whole architecture on screen. Open a fresh worked example to see the compact layout; saved project placements are preserved. **Arrange** also uses tighter spacing and retains locked placements.
