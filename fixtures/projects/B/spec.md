# Incomplete integration technical specification

SYNTHETIC — DEMONSTRATION ONLY

Prepare a partial architecture for review. Event delivery, session initiation, administration route and availability strategy are not decided. Reviewers must choose these explicitly; do not infer ports or server counts.

System vms-system: name="VMS"; scope="internal"

System client-system: name="Client"; scope="internal"

System vap-system: name="VAP"; scope="internal"

System c2-system: name="C2"; scope="external"

Zone infrastructure: name="Infrastructure"

Zone client: name="Client"

Zone z1: name="Z1"

Zone z2: name="Z2"

Component vms: name="VMS"; role="video management"; system_id="vms-system"; zone_id="infrastructure"; status="existing"; asset_id="application"

Component operator: name="Operator workstation"; role="operator"; system_id="client-system"; zone_id="client"; status="existing"; asset_id="workstation"; quantity=1

Component configuration: name="Configuration workstation"; role="configuration"; system_id="client-system"; zone_id="client"; status="existing"; asset_id="workstation"; quantity=1

Component management: name="VAP management"; role="management integration"; system_id="vap-system"; zone_id="z1"; status="new"; asset_id="api-service"; audit_destination="audit"

Component analytics: name="VAP analytics"; role="analytics"; system_id="vap-system"; zone_id="z2"; status="new"; asset_id="analytics-engine"

Component c2: name="C2"; role="external command system"; system_id="c2-system"; zone_id=null; status="existing"; asset_id="external-system"; scope="external"

Component audit: name="Audit destination"; role="audit"; system_id="vap-system"; zone_id="z1"; status="proposed"; asset_id="audit-service"

Component enforcement: name="Management enforcement"; role="firewall"; system_id="vap-system"; zone_id="z1"; status="proposed"; asset_id="firewall"

Interface video: source="vms"; target="analytics"; purpose="video"; data_direction="source_to_target"; initiator=null; protocol="RTSP"; port=null

Interface events: source="management"; target="c2"; purpose="events"; data_direction="source_to_target"; initiator=null; protocol=null; delivery=null

Interface administration: source="configuration"; target="management"; purpose=null; data_direction="bidirectional"; initiator=null; protocol="HTTPS"; enforcement=[]

Interface integration: source="management"; target="analytics"; purpose="integration"; data_direction="bidirectional"; initiator=null; protocol="HTTPS"

Constraint capacity: key="capacity_streams"; value=100

Constraint sizing: key="equipment_sizing"; value="undecided"

Constraint offline: key="no_internet"; value=true

Constraint resilience: key="resilience_required"; value=false

Constraint availability: key="availability_strategy"; value=null
