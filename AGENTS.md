# Architecture Workbench — coding-agent rules

## Mission
Implement PROJECT_PLAN.md end to end through M0–M7. Deliver a runnable PoC, not another plan or only a mock. Generate every synthetic input category. This file is a working summary; the project plan remains the acceptance specification.

## Fixed architecture
React/TypeScript + React Flow; FastAPI/Pydantic; SQLite/local files; one bounded orchestrator; mock, OpenAI and native Ollama adapters. One canonical architecture model, separate evidence and per-view presentation. Both mouse and prompt edits use validated versioned commands. No multi-agent framework, paid SDK or hosted database.

## Working sequence
Read commissioning brief and milestone table first. Inspect the existing repository and preserve user changes. Implement one milestone at a time, run focused tests, then run the offline suite at each gate. Check Visio feasibility early. Save checkpoints and maintain docs/STATUS.md with completed work, evidence, blockers and next task. Continue implementation when credentials/hardware are unavailable; mark corresponding live checks unverified.

## Token discipline
Read only relevant source sections/files after initial orientation. Search symbols before opening large files. Avoid reading binaries, lockfiles and generated folders repeatedly. Patch working code; do not rewrite for style alone. Keep one contract and derive types. Generate fixtures once using deterministic scripts. Do not call another model to review every change. Keep status concise; do not print saved code in chat. No autonomous subagents by default. Do not change tests to hide a failure.

## Cost discipline
Default to mock and APP_ALLOW_CLOUD=false. Tests use mocked transport. Paid smoke tests require explicit opt-in; a key's presence alone is not authorisation. All live calls use BudgetedProvider. Default guards: US$0.10/action, US$0.20/document batch, US$1/day and US$5/project. Paid test run: ten calls or US$0.50, plus application limits. Count retries and reserve in-flight costs. No automatic model escalation or Ollama-to-cloud fallback. Mouse edits, layout, validation and normal exports make zero model calls. These app controls do not cap this coding agent's own usage.

## Integrity and security
Keep synthetic labels and source locators. Unknown is not confirmed. Policies are fictional, not organisational approval. No arbitrary code execution from documents/model output. Never expose keys, upload real internal material, buy services, publish the repository or weaken host security without permission. Do not assume RTX 3080 VRAM or M2 Max memory. Use one small local model first; do not auto-download a model collection.

## Done means evidence
Report F01–F10, M0–M7 and T01–T16 status with evidence. Separate mock success, real OpenAI, real Ollama, hardware measurements and native Visio verification. A generated image is not an editable Visio export. Supply startup scripts, fixtures, tests, screenshots, export helper and setup/demo instructions. Never fabricate passed tests, cost, speed or time savings.
