# Policy library and project applicability

The policy library is shared across all local projects. Open **Policies**, choose a starting set or individual clauses, and click **Apply to project**. Selecting policies is a versioned project edit: it supports preview, persistence, undo and redo. It does not modify other projects and makes no model calls.

The library contains 42 bundled, fictional demonstration clauses:

- The original 20 clauses in `fixtures/policies/clauses.json` retain their original text and eight checks.
- The 22 additional drafts in `fixtures/policies/library.json` cover three-tier separation, database placement, enforcement references, encryption, identity, secrets, least privilege, backups, availability, logging, cloud networking, egress, patching, retention and ownership. They also cover on-premises/AWS connections and a wireless robotics testbed alongside production.
- Of the 22 additions, three are deterministic checks; 19 require human review. The robotics checklist does not implement or validate safety controls.

These clauses were authored for this demonstration. They are not imported organisational policies, certifications or quotations from an external security standard. A reported pass means only that a selected predicate passed on the recorded model facts.

**Your local drafts** accepts a title, requirement, applicability, exceptions and search tags. Drafts are saved in the local SQLite database and are always manual-review clauses. Adding a draft to the library does not automatically select it in any project. The usual database is `data/workbench.sqlite`; `APP_POLICY_DB` can isolate policy storage, otherwise `APP_DB` is respected.

Existing saved projects with `policy_ids: null` keep the original 20-clause policy set. An explicit empty list means no policies have been selected. Missing local policy IDs in an imported project are reported as unresolved rather than silently ignored; the library lets you deselect those missing IDs.

The three new automated checks are deliberately narrow:

| Clause | Model fact checked | Limit |
|---|---|---|
| `ARCH-SEG-01` | A Client–Z2 interface is a potential conflict in either direction. | Recognises explicit Client, Z1 or Z2 labels, optionally under Production, Testbed or AWS prefixes. Misleading prose and conflicting ID/name tiers stay unknown. It does not inspect deployed network reachability. |
| `ARCH-DAT-01` | An internal `database`, `aws-rds` or `aws-dynamodb` asset has a Z2 deployment. | Unknown tiers remain unresolved. Other data assets require human review. |
| `ARCH-FLW-01` | A cross-zone interface names an enforcement component. | A referenced component records intent; it does not prove firewall or cloud-rule configuration. |

`tests/test_policy_library.py` covers selected-rule evaluation, empty selections, undo/redo, invalid selections, zone names independent of IDs, reverse-direction bypasses, missing information, custom draft persistence, project isolation and missing imported policy IDs. `tests/test_policies.py` retains the original eight-rule/twelve-manual-review regression.

## Optional AI review

Open **Policy checks** and use **Review with OpenAI** or **Review with Ollama**, according to the provider selected in the header. The button makes one budgeted request covering only the project's selected policies. It does not edit the architecture. The automatic fact checks remain available independently. In Mock mode, **Try review format · free demo** displays deterministic sample advice and calls no model.

The review reports possible concerns, missing information and matters requiring human review. A narrow “no issue identified” observation is not a compliance decision. Source references are checked against supplied IDs, locators and exact excerpts; this does not verify the model's interpretation. Reviews use bounded context (up to 24 components, 32 interfaces, 20 constraints and 16 evidence excerpts), with included/total counts shown. Omitted material stays outside the review's coverage.

Results are saved locally and reused for the same revision, policy contents and provider/model. Accepted edits or policy-library changes mark a previous result as stale. Refreshing is an explicit action; there are no automatic retries or cloud fallback. Live reviews require synthetic projects and the usual provider opt-in and spending limits.

Evidence: `tests/test_policy_review.py`, frontend component tests and the browser journey verify budget enforcement, preservation of the accepted model, caching, stale results and source-reference rejection. A real Terra review of three selected portal policies passed in one request at an estimated US$0.01538, with two source-cited observations and one manual backup review (`reports/mac-policy-review-20260921.json`). This is a focused service integration check, not validation of every clause or model.
