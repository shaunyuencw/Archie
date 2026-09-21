# Decisions

- 2026-09-21: Use the fixed stack and one bounded application orchestrator. No coding subagents, per explicit user request.
- Pin known stable dependency releases and lock transitive dependencies after compatibility build. No recurring upgrade work.
- Native Visio COM helper is interactive and separate from the server. This host has no registered Visio; native verification remains pending.
- Official model page checked once: https://developers.openai.com/api/docs/models/gpt-5.4-mini documents Responses, structured outputs, function calling, snapshot gpt-5.4-mini-2026-03-17 and $0.75/$0.075/$4.50 ordinary-input/cached-input/output per million tokens. Account availability is unverified. Keep configurable plan baseline and disable cloud by default.
- React Flow zone parenting: https://reactflow.dev/learn/layouting/sub-flows. Native Ollama contract: https://docs.ollama.com/api/chat. Visio attachment: https://learn.microsoft.com/en-us/office/vba/api/visio.cell.glueto.
