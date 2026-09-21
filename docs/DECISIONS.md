# Decisions

- 2026-09-21: Use the fixed stack and one bounded application orchestrator. No coding subagents, per explicit user request.
- Pin known stable dependency releases and lock transitive dependencies after compatibility build. No recurring upgrade work.
- Native Visio COM helper is interactive and separate from the server. This host has no registered Visio; native verification remains pending.
- Official model page checked once: https://developers.openai.com/api/docs/models/gpt-5.4-mini documents Responses, structured outputs, function calling, snapshot gpt-5.4-mini-2026-03-17 and $0.75/$0.075/$4.50 ordinary-input/cached-input/output per million tokens. Account availability is unverified. Keep configurable plan baseline and disable cloud by default.
- React Flow zone parenting: https://reactflow.dev/learn/layouting/sub-flows. Native Ollama contract: https://docs.ollama.com/api/chat. Visio attachment: https://learn.microsoft.com/en-us/office/vba/api/visio.cell.glueto.
- User update: explicitly authorized GPT-5.6 Terra and a modest budget increase, and installed qwen3:4b. Verified https://developers.openai.com/api/docs/models/gpt-5.6-terra: $2/M ordinary input, $0.20/M cached input, $2.50/M cache writes, $12/M output for our short-context limits. Local .env now opts into cloud while startup provider stays mock; action $0.15, document $0.30, day $1.50, project $5.00. Live development smoke still capped at ten calls / $0.50 per run. Public .env.example retains original conservative defaults.
