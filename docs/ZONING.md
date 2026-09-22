# Zoning proposals

Archie’s shared provider instructions now request zones and component assignments alongside component and connection extraction. Deployment tables and cyber requirements trigger additional zoning guidance. This applies to OpenAI and Ollama; Mock retains its authored examples.

Stated zone names and assignments use document citations. When segmentation is required but an allocation is unspecified, the provider can propose a zone or assignment using `proposal_reason` on the operation. The backend retains the cited requirement separately from an `assistant_proposal` source containing the rationale. Proposed claims remain unreviewed after acceptance. The draft review, zone labels, Sources, Overview and narrative identify those assumptions.

Rationales may also accompany functional parts and complete deployment records. These remain explicitly unreviewed design proposals; additional deployment fields are retained, not silently treated as confirmed source facts. A blank rationale is absent metadata. Exact source quotes are required to verify a source claim. Missing or invalid citations now produce an unverified design assumption and review warning, rather than discarding an otherwise usable architecture. Structurally invalid records and their invalid dependencies are omitted with explanations; the remaining draft still passes normal architecture validation.

For an existing project, use this prompt:

> Use the uploaded specification’s deployment table and cybersecurity requirements to create the stated cyber zones. Propose any missing assignments and place every in-scope component in its zone. Keep external systems outside internal zones, preserve existing components and connections, and explain assumptions.

Explicit zoning prompts receive the whole bounded component inventory, deployment IDs and up to 6,000 characters of relevant saved source passages. Existing deployment records are updated rather than duplicated. A model citation must refer to a passage actually supplied in that action; access to other saved documents is not implicit.

Accept changes creates the canonical zones and assignments and packs new zone families in Architecture and Connection details. Unrelated saved families remain in place; pins and manual-route endpoints retain world coordinates. One Undo restores the previous design. This edits the architecture model; it does not configure switches, VLANs or firewalls. Unknown enforcement, transport and equipment details stay unknown.

The rules live in `apps/api/app/providers/instructions.py`: `SYSTEM_PROMPT` contains the short shared contract and `ZONING_GUIDANCE` contains the detailed drafting behavior. Detailed guidance is supplied only for relevant work to preserve the small local-model context budget. Existing spending, cancellation, review and provider-selection controls still apply.

Initial zoning validation used scripted provider responses, acceptance/reopen/undo tests, browser review and a replay of the earlier SSMS v1.5 checkpoint. The replay produces four named internal zones, assigns 14 internal components, preserves 20 components/22 connections, leaves six external components outside internal zones, and labels five VSS allocations as proposed. That replay does not modify the live project or establish live-model accuracy. Evidence is in `reports/zoning-proposals-tests.xml`, `reports/zoning-proposals-browser.json` and `reports/ssms-v15-zoning-replay.json`.

Subsequent live validation is recorded separately: a real OpenAI portal import accepted seven components, three zones and four interfaces, retaining a connection with an unverifiable citation as an unreviewed assumption. It used one request, no repair, 39.8 seconds and an estimated $0.047861. See `reports/partial-draft-live-validation.json`; this establishes that case, not universal provider accuracy.
