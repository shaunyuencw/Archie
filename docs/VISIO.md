# Native Visio handover

Implementation: interactive Windows COM helper. Native node rectangles/text, glued connectors, declared zones with attempted container membership, stable object names, straight/right-angled routing, 96 pixel/inch conversion and inverted Y axis. Logical and SV-2 component views are supported. SV-1 aggregation and exact manual bend reproduction are currently not implemented in this helper; use its SVG review export for that view.

Run in an interactive desktop session with an installed, licensed Visio:

```powershell
./scripts/export_visio.ps1 -InputPath ./reports/exports/architecture.json -OutputPath ./reports/exports/architecture.vsdx -View logical
```

The helper creates its own visible application/document. It never attaches to an existing document, changes execution policy, downloads scripts or runs in the web server. It refuses overwrite unless you type OVERWRITE. Visio edits do not synchronise back.

Native verification on this host: **unverified**. Visio.Application COM registration is absent; no .vsdx has been generated. Static PowerShell syntax check passes. SVG is an image export, not evidence of native editability.

Manual acceptance checklist (all unverified):

- Open .vsdx without repair.
- Select and rename a node; inspect its stable NameU.
- Move the node and verify both connector endpoints remain attached.
- Change a connector route.
- Move a zone and verify container membership moves its nodes.
- Save, close and reopen; inspect names, placement, routes and attachment.
- Record Visio version, exported project revision, screenshot paths and any container warnings.
