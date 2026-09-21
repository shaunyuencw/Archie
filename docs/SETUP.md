# Setup and operation

The tested host is Windows 11, Python 3.12.4, Node 24.19.0 and Microsoft Edge. Dependencies are pinned in `requirements.lock`, `apps/web/package-lock.json` and the alternative pnpm lockfile. macOS commands are supplied but have not been executed on an M2 Max.

1. Clone the repository and open a terminal at its root.
2. Run `./scripts/setup.ps1` on Windows or `bash scripts/setup.sh` on macOS. Setup preserves an existing `.env`. It downloads software dependencies, not language-model weights.
3. Run `./scripts/dev.ps1` or `bash scripts/dev.sh`. Keep that terminal open. Frontend: <http://127.0.0.1:5173/>; backend health: <http://127.0.0.1:8000/api/health>.
4. Use mock mode first. Select Load demo A or B. Data is saved under `data/workbench.sqlite`; back up that file with the server stopped. The PoC has no accounts or multi-user access control; keep it bound to loopback.

If Windows blocks an unsigned PowerShell script, use two terminals without changing system execution policy:

```powershell
# Terminal 1, repository root after dependency installation
.venv/Scripts/python.exe -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
# Terminal 2, apps/web
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
```

## Configuration

Copy `.env.example` to `.env` if needed. Put the OpenAI key only in `OPENAI_API_KEY`. `OPENAI_ESCALATION_MODEL` is a model-name placeholder, not a key field; automatic escalation is disabled. Never commit `.env`. Restart the backend after changing configuration.

For explicitly authorised cloud use, set `APP_ALLOW_CLOUD=true`, supply the key and select OpenAI in the app. Default model is `gpt-5.4-mini`; the tested alternative is `gpt-5.6-terra`. Price configuration and date are in `config/pricing.json`. Unknown billing models are blocked until pricing is configured. Runtime limits do not cap the coding agent's own usage or the whole OpenAI account.

Defaults: $0.10/action, $0.20/document action, $1/day, $5/project; four calls/action with smaller task limits. The local user's authorised configuration raises the first three to $0.15/$0.30/$1.50, but it is excluded from the repository. Reservations include in-flight requests and survive restart. Ambiguous failures retain their reservation. Settings shows effective limits; mouse edits, layout, deterministic narrative and exports do not call a model.

Ollama: install Ollama separately, provide an already installed `qwen3:4b`, keep `OLLAMA_BASE_URL=http://127.0.0.1:11434`, and select Ollama. No weights are downloaded by startup or tests. The local profile uses 4K context and serial execution. The current small model fails some reference/tool checks, and rejected output does not change accepted architecture. It never falls back to OpenAI.

## Commands

Use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS before these scripts:

| Script | Purpose |
| --- | --- |
| `scripts/seed.py` | Regenerate synthetic fixture categories deterministically. |
| `scripts/contracts.py` then `node scripts/contracts.mjs` | Derive web contracts after canonical schema changes. |
| `scripts/doctor.py` | Read-only environment report, no secrets or model downloads. |
| `scripts/test.py` | Full offline gate; exits on the first failing step. |
| `scripts/evaluate.py` | Compare fixture extraction against authored component/interface facts. |
| `scripts/export_samples.py` | Regenerate snapshot exports. |
| `scripts/smoke.py --provider ollama` | Explicit local smoke using installed model. |
| `scripts/smoke.py --provider openai --live --max-calls 10 --budget-usd 0.50` | Explicit paid smoke, subject to application limits; current script performs three checks, within that ceiling. |

Browser tests run separate services on ports 18000 and 15173 and use an isolated database. They leave the demo services on 8000/5173 alone. Windows uses installed Edge. On macOS, from `apps/web`, run `npx playwright install chromium` once before testing. Setup/browser installation needs internet; mock operation and tests thereafter do not require a model connection.

## Current limits

Synthetic inputs only for live providers; text PDF and DOCX only, no OCR. Uploads are limited to 10 MB, expanded DOCX to 50 MB. Batches report remaining sections; cloud document processing has a separate reviewable preflight. The mock interpreter recognises authored fixture records and a small prompt grammar, not arbitrary prose. Capacity is capped at 50 components/100 interfaces. No organisation-specific compliance approval, native Visio verification, real-world accuracy or human time-saving result is claimed.
