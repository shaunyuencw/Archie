# B reference — SYNTHETIC — DEMONSTRATION ONLY

SYNTHETIC — DEMONSTRATION ONLY
Accepted semantic revision: 0

## Scope and responsibilities
- [vms] VMS: video management; existing; zone infrastructure; quantity undecided. Evidence: claim-vms.
- [operator] Operator workstation: operator; existing; zone client; quantity 1. Evidence: claim-operator.
- [configuration] Configuration workstation: configuration; existing; zone client; quantity 1. Evidence: claim-configuration.
- [management] VAP management: management integration; new; zone z1; quantity undecided. Evidence: claim-management.
- [analytics] VAP analytics: analytics; new; zone z2; quantity undecided. Evidence: claim-analytics.
- [c2] C2: external command system; existing; zone unspecified; quantity undecided. Evidence: claim-c2.
- [audit] Audit destination: audit; proposed; zone z1; quantity undecided. Evidence: claim-audit.
- [enforcement] Management enforcement: firewall; proposed; zone z1; quantity undecided. Evidence: claim-enforcement.

## Interfaces and session initiation
- [video] VMS → VAP analytics: video; flow source_to_target; initiator undecided; protocol RTSP; port undecided; enforcement unspecified.
- [events] VAP management → C2: events; flow source_to_target; initiator undecided; protocol undecided; port undecided; enforcement unspecified.
- [administration] Configuration workstation → VAP management: purpose undecided; flow bidirectional; initiator undecided; protocol HTTPS; port undecided; enforcement unspecified.
- [integration] VAP management → VAP analytics: integration; flow bidirectional; initiator undecided; protocol HTTPS; port undecided; enforcement unspecified.

## Constraints and open decisions
- capacity_streams: 100
- equipment_sizing: undecided
- no_internet: True
- resilience_required: False
- availability_strategy: undecided

## Sources
- [claim-vms-system] confirmed: reference-source v1.0, row/1: System vms-system: name="VMS"; scope="internal"
- [claim-client-system] confirmed: reference-source v1.0, row/2: System client-system: name="Client"; scope="internal"
- [claim-vap-system] confirmed: reference-source v1.0, row/3: System vap-system: name="VAP"; scope="internal"
- [claim-c2-system] confirmed: reference-source v1.0, row/4: System c2-system: name="C2"; scope="external"
- [claim-infrastructure] confirmed: reference-source v1.0, row/5: Zone infrastructure: name="Infrastructure"
- [claim-client] confirmed: reference-source v1.0, row/6: Zone client: name="Client"
- [claim-z1] confirmed: reference-source v1.0, row/7: Zone z1: name="Z1"
- [claim-z2] confirmed: reference-source v1.0, row/8: Zone z2: name="Z2"
- [claim-vms] confirmed: reference-source v1.0, row/9: Component vms: name="VMS"; role="video management"; system_id="vms-system"; zone_id="infrastructure"; status="existing"; asset_id="application"
- [claim-operator] confirmed: reference-source v1.0, row/10: Component operator: name="Operator workstation"; role="operator"; system_id="client-system"; zone_id="client"; status="existing"; asset_id="workstation"; quantity=1
- [claim-configuration] confirmed: reference-source v1.0, row/11: Component configuration: name="Configuration workstation"; role="configuration"; system_id="client-system"; zone_id="client"; status="existing"; asset_id="workstation"; quantity=1
- [claim-management] confirmed: reference-source v1.0, row/12: Component management: name="VAP management"; role="management integration"; system_id="vap-system"; zone_id="z1"; status="new"; asset_id="api-service"; audit_destination="audit"
- [claim-analytics] confirmed: reference-source v1.0, row/13: Component analytics: name="VAP analytics"; role="analytics"; system_id="vap-system"; zone_id="z2"; status="new"; asset_id="analytics-engine"
- [claim-c2] confirmed: reference-source v1.0, row/14: Component c2: name="C2"; role="external command system"; system_id="c2-system"; zone_id=null; status="existing"; asset_id="external-system"; scope="external"
- [claim-audit] confirmed: reference-source v1.0, row/15: Component audit: name="Audit destination"; role="audit"; system_id="vap-system"; zone_id="z1"; status="proposed"; asset_id="audit-service"
- [claim-enforcement] confirmed: reference-source v1.0, row/16: Component enforcement: name="Management enforcement"; role="firewall"; system_id="vap-system"; zone_id="z1"; status="proposed"; asset_id="firewall"
- [claim-video] confirmed: reference-source v1.0, row/17: Interface video: source="vms"; target="analytics"; purpose="video"; data_direction="source_to_target"; initiator=null; protocol="RTSP"; port=null
- [claim-events] confirmed: reference-source v1.0, row/18: Interface events: source="management"; target="c2"; purpose="events"; data_direction="source_to_target"; initiator=null; protocol=null; delivery=null
- [claim-administration] confirmed: reference-source v1.0, row/19: Interface administration: source="configuration"; target="management"; purpose=null; data_direction="bidirectional"; initiator=null; protocol="HTTPS"; enforcement=[]
- [claim-integration] confirmed: reference-source v1.0, row/20: Interface integration: source="management"; target="analytics"; purpose="integration"; data_direction="bidirectional"; initiator=null; protocol="HTTPS"
- [claim-capacity] confirmed: reference-source v1.0, row/21: Constraint capacity: key="capacity_streams"; value=100
- [claim-sizing] confirmed: reference-source v1.0, row/22: Constraint sizing: key="equipment_sizing"; value="undecided"
- [claim-offline] confirmed: reference-source v1.0, row/23: Constraint offline: key="no_internet"; value=true
- [claim-resilience] confirmed: reference-source v1.0, row/24: Constraint resilience: key="resilience_required"; value=false
- [claim-availability] confirmed: reference-source v1.0, row/25: Constraint availability: key="availability_strategy"; value=null

## Authored notes
(none)