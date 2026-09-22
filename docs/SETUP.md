# Setup and operation

Verified Mac: macOS 26.6.2, M2 Max, 32 GiB unified memory, Python 3.12.0, Node 22.23.1, pnpm 11.19.0 and Playwright Chromium 153.0.8010.12. Historical Windows 11 / Python 3.12.4 / Node 24.19.0 / Edge evidence remains in `reports/windows-checkpoint` and prior live reports. Dependencies are pinned in `requirements.lock` and `apps/web/pnpm-lock.yaml`.

The Mac launcher preserves a supported active Node, or chooses an already installed Node 22/24/Homebrew runtime when the shell default is unsupported. This Mac's shell default was Node 21.5.0 / Python 3.10.9; setup selected installed Python 3.12 and Node 22 without changing shell configuration. Install pnpm 11 (or provide Corepack) before first setup.

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

Live document reads reserve room for one automatic correction within the existing action call and spending limits. Valid section responses are retained; only the invalid section is replaced. A one-call profile cannot repair automatically. Preflight reports any sections left for a later read. If a relationship still cannot be verified, the action stops with a record/field explanation and the accepted design remains unchanged.

Defaults: $0.10/action, $0.20/document action, $1/day, $5/project; four calls/action with smaller task limits. The authorised ignored `.env` on this Mac uses `OPENAI_MODEL=gpt-5.6-terra`, 32,000 input / 6,000 output tokens, six calls/action, and $0.50/action, $1/document, $5/day, $12/project ceilings. `APP_LIVE_TESTS=true` and cloud opt-in are enabled for the authorised workflow; startup still selects mock. These are hard ceilings, not targets. Reservations include in-flight requests and survive restart. Ambiguous failures retain their reservation. Settings shows effective limits; mouse edits, layout, deterministic narrative and exports do not call a model.

Ollama is installed and running here (0.34.2). The selected already-installed `qwen3:14b` is Q4_K_M, 14.8B, with 8,192 context; observed loaded memory was 10 GB / 100% GPU, not a peak measurement. Its small extraction passed, but the richer two-component journey failed. Historical qwen3:4b remains separately recorded. No models are downloaded by setup/tests, and there is no cloud fallback. Local requests run serially. The 4K profile retains its 1,024-token output cap. For 8K, output is bounded by the user limit, remaining context after the conservative input estimate and a 512-token reserve, and a 3,720-token time allowance. This replaces the fixed 1,536-token cap. Default local response windows scale with output size, up to 480 seconds; explicit action deadlines remain authoritative and may be shorter. Timeout and output-limit failures are not automatically replayed. Returned usage counters from a length-limited response are recorded as truncated without storing the incomplete output. Full-document local reliability remains unverified after this adjustment.

Drafting and policy review run as background actions, so you can browse another project. **Cancel** prevents queued processing or signals running work to discard its result. A running non-streaming provider request may need to return or time out before cancellation becomes terminal; the activity row says **Stopping…** during that interval. ARCHIE does not terminate the shared Ollama service.

## Commands

Use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS before these scripts:

| Script | Purpose |
| --- | --- |
| `scripts/seed.py` | Regenerate synthetic fixture categories deterministically. |
| `scripts/contracts.py` then `node scripts/contracts.mjs` | Derive web contracts after canonical schema changes. |
| `scripts/doctor.py` | Read-only environment report, no secrets or model downloads. |
| `scripts/test.py` (Mac: `bash scripts/test.sh`) | Full offline gate; exits on the first failing step. |
| `scripts/evaluate.py` | Compare fixture extraction against authored component/interface facts. |
| `scripts/export_samples.py` | Regenerate snapshot exports. |
| `scripts/smoke.py --provider ollama` | Explicit local smoke using installed model. |
| `scripts/smoke.py --provider openai --live --max-calls 10 --budget-usd 0.50` | Explicit paid smoke, subject to application limits; current script performs three checks, within that ceiling. |

Browser tests run separate services on ports 18000 and 15173 and use an isolated database. They leave the demo services on 8000/5173 alone. Windows uses installed Edge. On macOS, from `apps/web`, run `pnpm exec playwright install chromium` once before testing. Setup/browser installation needs internet; mock operation and tests thereafter do not require a model connection.

## Current limits

Synthetic inputs only for live providers; text PDF and DOCX only, no OCR. Uploads are limited to 10 MB, expanded DOCX to 50 MB. Batches report remaining sections; cloud document processing has a separate reviewable preflight. The mock interpreter recognises authored fixture records and a small prompt grammar, not arbitrary prose. Capacity is capped at 50 components/100 interfaces. No organisation-specific compliance approval, native Visio verification, real-world accuracy or human time-saving result is claimed.

## Verified Mac launch

```sh
cd /Users/shauny/Developer/Archie
bash scripts/setup.sh   # first time, or when dependencies change
bash scripts/dev.sh
```

For the offline gate use `bash scripts/test.sh`. The launcher keeps ports 8000 and 5173 on loopback. Stop an existing launcher with Ctrl+C before starting another. After `.env` changes, restart the backend.
