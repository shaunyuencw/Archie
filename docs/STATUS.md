# Engineering checkpoint — 21 September 2026

The user requested a stable stopping point and a push to `shaunyuencw/Archie` before leaving. M0–M4 have individual checkpoints. M5 consistency and M6 exports are implemented; M7 handover remains in progress. See root `PROGRESS.md` and `docs/ACCEPTANCE.md` for the honest completion matrix.

Implemented: canonical model and validated commands, SQLite revisions/undo, deterministic synthetic packs, React Flow editing and three projections, local document ingestion and exact evidence, fact review/questions, eight rule checks plus 12 manual clauses, bounded providers and budget ledger, prompt changes, cached narrative, JSON/SVG/DOCX/Markdown/CSV exports, sanitised pattern import/export, native Visio helper, Archie logo/robot.

Verification: 25 backend tests passed in the latest recorded run. Final full offline runner results are in `reports/offline-gate.json`; detailed browser results in `reports/browser-tests.json`. Production build passes with a bundle-size warning. TypeScript and frontend unit test pass. Latest Visio helper passes PowerShell syntax parsing; native execution is unavailable.

Live evidence: Terra extraction/native-tool/targeted-edit smoke passes at about $0.006948 for that three-call run. Previous attempts are preserved separately. Qwen3:4b connects but latest extraction/tool/edit candidates fail validation; rejected output does not mutate accepted state. No hidden cloud fallback or automatic model downloads. User-authorised local cloud settings are ignored by Git; distributed defaults remain mock/cloud-off.

Environment: Windows 11, Python 3.12.4, Node 24.19.0, RTX 3080 Ti Laptop GPU (16,384 MiB), 68,334,067,712 bytes RAM. Visio COM is absent. Mac/M2 Max untested. No peak VRAM measurement or human time-savings experiment.

Remaining after this checkpoint:

1. Final SVG appearance alignment with the updated equipment canvas; rendered PDF/DOCX visual QA (LibreOffice unavailable for DOCX).
2. Browser capacity measurements at 50 components/100 interfaces; backend capacity test already passes.
3. Optional real live-document integration check, only within explicitly authorised budgets; mocked transport tests pass.
4. Native Visio manual checklist on a licensed Windows desktop. Logical/SV-2 handover is implemented; SV-1 aggregation and exact manual bends are not in the helper.
5. Final M7 source archive and acceptance review. Do not claim all milestones or all live providers complete.

Next task: resume these remaining M7 checks without repeating paid smoke tests or rebuilding working modules for style.
