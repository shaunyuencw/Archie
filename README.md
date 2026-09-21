# Archie — Architecture Workbench

A local architecture PoC with a React Flow editor, FastAPI backend, SQLite persistence, source evidence, reviewed assistant changes, fictional policy checks and three views of one model.

**Stable development checkpoint, 21 September 2026.** See [PROGRESS.md](PROGRESS.md) for implementation status and remaining work. This is not a claim that all M7 acceptance checks are complete.

![Archie workbench](reports/archie-workbench.png)

## Start

Prerequisites: Python 3.12 and Node.js 20.19+ (24.19 tested). Install dependencies once; normal mock use needs no API key or internet connection.

Windows PowerShell, from the repository root:

```powershell
./scripts/setup.ps1
./scripts/dev.ps1
```

macOS terminal (provided, not tested on this host):

```sh
bash scripts/setup.sh
bash scripts/dev.sh
```

Open <http://127.0.0.1:5173/>. Choose **Load demo A**, inspect the three views, select equipment, and edit properties. The robot assistant proposes changes for review before acceptance. Ctrl+C stops the development launcher.

Read [setup and provider configuration](docs/SETUP.md), [demo walkthrough](docs/DEMO.md), [native Visio handover](docs/VISIO.md), and [checkpoint acceptance matrix](docs/ACCEPTANCE.md).

## Verification

```powershell
.venv/Scripts/python.exe scripts/test.py
.venv/Scripts/python.exe scripts/doctor.py
.venv/Scripts/python.exe scripts/evaluate.py
.venv/Scripts/python.exe scripts/export_samples.py
```

On macOS, use `.venv/bin/python`. The test runner is offline and disables cloud calls. Browser tests use installed Microsoft Edge on Windows; on macOS install Playwright Chromium once as described in setup.

Synthetic input sources and rendered DOCX/PDFs are under `fixtures/projects`. Policies, templates, catalogue, references and development/frozen evaluation fixtures are also under `fixtures`. Rebuild with `scripts/seed.py`; this never uses a model.

## Providers and limits

Distributed defaults are **mock** and **cloud disabled**. `.env` and local databases are excluded from Git. Mock interpretation supports authored fixture statements and a small set of edit prompts. OpenAI uses the Responses API; Ollama uses its native local endpoint. Every live runtime call passes through the budget wrapper; there is no automatic escalation or fallback to cloud.

Real OpenAI extraction/tool/edit smoke passed with `gpt-5.6-terra`. Local `qwen3:4b` connected but failed the latest proposal validation checks; it is not a successful local generation demonstration. See `reports/smoke-*.json` for actual evidence.

SVG is an image export. The interactive Windows Visio helper creates native shapes/connectors when Visio is installed, but native editability is **unverified** on this host. Synthetic policies are fictional and do not represent organisational approval.

Architecture: `apps/web` → `apps/api/app` → canonical Pydantic model, bounded orchestrator, SQLite/local files. No hosted database, autonomous agent framework, or paid export SDK. Catalogue artwork is licensed in `fixtures/assets/LICENCE.txt`; branding provenance is in `apps/web/public/brand/README.md`.
