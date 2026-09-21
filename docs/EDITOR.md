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
| Clear selection / cancel bend drag | Escape | Escape |

Typing fields retain their native shortcuts. Delete asks before removing selected objects and connected interfaces. A group edit is one undo step. New edits after undo discard the abandoned redo branch. Stale externally changed revisions still reject.

Copy/paste is an internal, same-project clipboard, available in Logical and SV-2. Selecting a zone copies its contained components; connectors between copied components retain remapped references. Copies are proposed, have no asserted original source evidence, and have unknown quantities. SV-1 aggregates are edited through their individual components in another view.

Dragging a component across a zone changes its **layout only**. Use **Deployment zone** in the Inspector to propose an architectural reassignment, then review and accept it. Arrangement preserves locked manual placements and uses ELK for unlocked top-level objects. It is not a full obstacle-avoiding router.

Select a connector to show endpoint reconnect controls and a bend control. Drag the bend to create a waypoint; saved waypoints remain draggable. Double-click a waypoint, or focus it and press Delete, to remove it. The Inspector supports straight and right-angled styles plus exact coordinates for multiple waypoints. Reconnecting clears the route for that connector; unrelated routes stay intact. Prompt edits preserve manual routes and positions.

Known presentation limits: no alignment-guide overlay; complex automatic routes can cross unrelated equipment, especially in SV-1. Use manual waypoints for a presentation. SVG respects stored handles and anchors, but is not pixel-identical to React Flow and is not editable native Visio.
