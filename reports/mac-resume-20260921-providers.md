# Mac provider journey evidence — 21 September 2026

Seven requests total: four OpenAI, three Ollama. Estimated OpenAI API cost was **US$0.0743975**, computed from returned token usage and configured pricing, not an account bill. The shared ledger enforced an eight-request / US$0.50 ceiling; every request used `BudgetedProvider`. No downloads, escalation or cloud fallback occurred. See `mac-resume-20260921-usage.json`.

## OpenAI `gpt-5.6-terra`

Both requested journeys passed at the application service layer, using the same validation, proposal acceptance, clarification, commands and projections as the web app. This is real provider integration evidence; browser interaction tests are separate. The harness accepts synthetic proposals and chooses example clarification answers automatically, solely for verification.

- **Flow A:** two applications and one event interface from ordinary prose; delivery, initiation, protocol and port remained unknown. A push/pull clarification was answered for free. A manual position and locked connector route survived a targeted rename; all three views, narrative and interface CSV agreed. Three requests included one bounded schema repair. Duration: 19.415 seconds for the journey.
- **Flow B:** the existing incomplete synthetic SoW DOCX produced eight components, four interfaces and 32 resolvable source claims. Every parsed locator was processed. An administration-purpose clarification was answered for free. Deterministic retrieval found relevant firewall/audit/interface clauses; all eight implemented rules and 12 manual clauses were reported. Unspecified port, session initiation, event delivery and equipment sizing remained unknown. One request, 27.046 seconds.

Full reports, original accepted snapshots and findings: `mac-resume-20260921-openai/`.

Post-run source review identified unsupported `internal` scope on one component/system. Provider additions now keep omitted or unsubstantiated scope unknown and include a review finding. A deterministic replay of the saved Terra output proves this fix while preserving explicitly cited external scope; no paid rerun was used. See `scope-normalization-replay.json`. Original live snapshots remain unchanged as historical evidence. Source citations still require human review; structural validation alone cannot prove every interpretation is correct.

Official model/pricing guidance was checked against [Terra documentation](https://developers.openai.com/api/docs/models/gpt-5.6-terra) and [API pricing](https://developers.openai.com/api/docs/pricing). Configured prices are $2 input, $0.20 cached input, $2.50 cache writes and $12 output per million tokens.

## Ollama `qwen3:14b`

This already-installed candidate is 14.8B, Q4_K_M. The Mac has 32 GiB unified memory. Ollama reported **10 GB loaded, 100% GPU, 8,192 context**. That is a loaded-model observation, not a peak memory measurement. Historical `qwen3:4b` and Windows reports remain separate.

- A richer two-node journey failed safely after two local attempts. The first response was incomplete/invalid and its bounded follow-up failed before a valid proposal. No accepted architecture changed. `mac-resume-20260921-ollama/report.json` retains this failure.
- A final deliberately small one-component extraction/structured proposal **passed** in one request: 250 reported input tokens, 464 output tokens, 43.931 seconds on an already-loaded model. `mac-resume-20260921-ollama/small-extraction.json` retains the source-grounded candidate, accepted model and usage.

The local API fee was zero; hardware/electricity cost was not measured. The full local architecture journey is **not verified for a demo**. Use Terra for the core demonstration.

## Reproduction

Paid runs require both `--live` and the explicit `.env` cloud/live flags. Each run writes a fresh timestamped evidence directory and uses the persistent application budget ledger. Do not repeat these merely for wording or layout changes.

```sh
.venv/bin/python scripts/live_journeys.py --provider openai --live
.venv/bin/python scripts/live_journeys.py --provider ollama --model qwen3:14b --context 8192 --local-small --live
```

The richer local test is available by omitting `--local-small`; its failure above remains a limitation. Distributed defaults remain mock/cloud-disabled. The authorised ignored `.env` uses Terra, 32,000 input / 6,000 output ceilings, six calls/action and the requested development budgets; these are ceilings, not targets. The installed local candidate is selected there at 8,192 context.
