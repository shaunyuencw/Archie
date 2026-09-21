# Synthetic demo scenarios

These examples demonstrate a traceable architecture draft from a small specification. They are fictional designs, not approved organisational policies or production implementation instructions. Existing VAP packs A/B/C remain unchanged for regression testing.

## Start with the two prepared diagrams

| Demo | What the diagram shows | Deliberately unresolved |
| --- | --- | --- |
| **Production service portal** (`portal`) | Physical employee and service-desk workstations in Client; web/application services and their compute hosts in Z1; a protected database in Z2. Application hosts and application instances are active-active; database servers are active-passive. The virtual firewall has an explicit host reference. | End-to-end availability, web/firewall redundancy, backups, retention, sizing and infrastructure administration. |
| **Hybrid robotics trial** (`robotics`) | Separate Production and Testbed Client/Z1/Z2 boundaries. Robot, tablet and wireless AP remain in Testbed Client. Testbed services have an explicit physical host and virtual firewall. A narrow status handoff reaches the Production API; a separate telemetry path reaches AWS API Gateway, Lambda and S3. | AWS region/residency, connection approval, retention, identity lifecycle, trial exit date and recovery evidence. |

Load one of the prepared demo projects to inspect an already authored synthetic reference. This action does not call a model. Its confirmed source claims mean “confirmed in this fictional source”; they do not mean that a real organisation approved the design. Each Sources entry retains exact DOCX paragraph locators.

The portal has **7 canonical components, 4 interfaces and 3 zones**. The robotics trial has **14 canonical components, 11 interfaces and 8 zones**. Quantity represents declared instances of a canonical component; it is not evidence that independent failure domains exist. In particular, two virtual firewalls on one physical host would still share that host's failure risk.

AWS tier labels describe logical trust and responsibility boundaries. They do **not** assert that regional API Gateway, Lambda or S3 services sit inside a private VPC subnet. The wireless association and the robot's MQTT application session are separate interfaces. No direct Testbed-to-Production database path, unrestricted lateral access or cloud-to-robot command path is present.

Use focus mode and zoom for the larger hybrid diagram. Its explicit presentation routes preserve the intended boundaries; an arrow or nearby firewall symbol does not prove a deployed security control.

## Test a plain-language document workflow

Create a new empty project, explicitly choose a live provider, and upload one of these small specifications. Review the processing plan and proposed changes, then inspect evidence and clarification questions before accepting. Do not upload a specification into an unrelated prepared project when the intention is to create a new architecture.

| Scenario | Human-readable specification | Upload files | Useful uncertainty to inspect |
| --- | --- | --- | --- |
| Service portal | [Technical specification](../fixtures/demos/portal/techspec.md) | [DOCX](../fixtures/demos/portal/techspec.docx) / [PDF](../fixtures/demos/portal/techspec.pdf) | Partial redundancy does not establish an end-to-end availability strategy. |
| Hybrid robotics | [Technical specification](../fixtures/demos/robotics/techspec.md) | [DOCX](../fixtures/demos/robotics/techspec.docx) / [PDF](../fixtures/demos/robotics/techspec.pdf) | Narrow handoff, wireless trial isolation and cloud approval remain distinct concerns. |
| Warehouse inventory | [Technical specification](../fixtures/demos/inventory/techspec.md) | [DOCX](../fixtures/demos/inventory/techspec.docx) / [PDF](../fixtures/demos/inventory/techspec.pdf) | Finance integration endpoint, protocol and initiator are not specified. |
| Building access events | [Technical specification](../fixtures/demos/building-access/techspec.md) | [DOCX](../fixtures/demos/building-access/techspec.docx) / [PDF](../fixtures/demos/building-access/techspec.pdf) | Door-event push/polling, protocol and session initiation are intentionally undecided. Remote unlock is outside scope. |

The two featured specifications are two pages each; the inventory and building-access specifications are one page each. DOCX and PDF variants share the same source/version through `fixtures/demos/manifest.json`, so importing both should not duplicate source facts.

These four natural-language document workflows have **not been validated by real model calls as part of generating this pack**. Generation and the regression checks are deterministic and make zero provider calls. A live provider may still fail or produce an incomplete proposal; failures and unresolved facts must remain visible.

## Offline mock workflow

Mock understands a narrow authored-record format and a small set of edit prompts. It does not generally understand the plain-language specifications above.

For a repeatable free extraction journey, start an empty project in Mock mode and upload one of these explicitly labelled parser fixtures:

- [Service portal authored mock input](../fixtures/demos/portal/mock-input.docx)
- [Robotics trial authored mock input](../fixtures/demos/robotics/mock-input.docx)

They encode the same component, deployment and interface facts as the prepared references. Accepting the proposal does not import the prepared diagram's presentation coordinates; use Arrange view or manual placement. This is evidence of the authored fixture parser, not evidence of general document understanding.

## Follow-up prompts

Move a node manually before trying a follow-up. Preview the proposal and inspect its affected IDs, then accept or reject. Verify that unrelated coordinates, routes, source references and interface IDs survive. Undo should restore the prior accepted state.

**Service portal**

1. `Rename Portal web service to Employee self-service portal` — supported by Mock or a live provider; expect a rename only.
2. `Add one workstation` — supported by Mock or a live provider. Mock leaves the zone unspecified; review it and explicitly assign Client.
3. `Add a reporting service to Z1 and connect it to Request database over PostgreSQL TCP 5432 through Zone firewall. Keep all existing positions and routes.` — live provider; expect a targeted service/deployment/interface proposal.
4. `Make Portal web service a pair of active-active instances, and make Zone firewall a pair of active-passive instances. Keep them hosted on Application hosts. Do not change Request database.` — live provider; review explicit quantity/redundancy/hosting changes. Recovery targets remain separate decisions.

**Hybrid robotics**

1. `Rename Trial integration gateway to Trial telemetry gateway` — Mock or live; preserve both handoff interface IDs and routes.
2. `Add a second Trial robot in Testbed Client with its own MQTT over TLS TCP 8883 session to Robot controller through Trial virtual firewall. Keep production and AWS unchanged.` — live; ensure the robot remains in Testbed.
3. `Set telemetry retention to 7 days for this trial. Do not change which payloads may leave the testbed.` — live; expect a constraint/decision update, not a new data path.
4. `Make Trial virtual firewall a pair of active-passive instances, hosted on Trial compute host. Keep all placements and routes.` — live; a shared physical host remains a common failure point.
5. `Remove the proposed production status handoff for the trial, leaving the AWS telemetry path unchanged.` — live; review removal of `production-handoff` before accepting.

**Warehouse inventory**

1. `Rename Inventory web application to Warehouse stock application`
2. `Add a stock-movement API for the finance integration in Z1, but leave its external endpoint, protocol and initiator unresolved. Ask me the most important integration question.`
3. `Make Inventory database a pair of active-passive instances and keep its zone Z2.`

**Building access events**

1. `Rename Access event service to Building event viewer`
2. `Use push delivery from Door controllers to Access event service over HTTPS TCP 443, initiated by each controller. Keep remote unlock out of scope.`
3. `Add a separate audit service in Z2 and connect Access event service to it. Leave the audit transport undecided.`

Use a live provider for the inventory/building-access document journeys. Once a component with the exact named label exists, Mock's narrow rename command can rename it, but the broader follow-ups require live interpretation. Machine-readable prompt lists and expected effects are in each scenario's `followups.json`.

## Regenerate and verify

The single editable source is [source.yaml](../fixtures/demos/source.yaml). Generated references, source manifests, document variants and mock inputs contain no API key or runtime model result.

```sh
.venv/bin/python scripts/generate_demos.py
.venv/bin/python -m pytest tests/test_demo_scenarios.py -q
```

For an isolated regeneration check:

```sh
.venv/bin/python scripts/generate_demos.py --output-dir tmp/demo-regeneration
```

The generator fixes document metadata and ZIP timestamps and validates canonical model references. It does not change the original fixture generator or the original VAP packs. Source documents and SVG diagrams were rendered for local visual review; see `reports/demo-pack-qa/` for evidence. Native editable Visio remains a separate, unverified capability on this Mac.
