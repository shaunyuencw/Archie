# Conflicting requirements statement of work

SYNTHETIC — DEMONSTRATION ONLY

Preserve the disagreement between the SoW and specification. The SoW requires no internet dependency and resilience. The specification requires an internet hosted service and a single instance without recovery. Neither source has precedence.

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

Interface video: source="vms"; target="analytics"; purpose="video"; data_direction="source_to_target"; initiator="analytics"; protocol="RTSP"; port=null

Interface events: source="management"; target="c2"; purpose="events"; data_direction="source_to_target"; initiator="management"; protocol="HTTPS"; delivery="push"

Interface administration: source="configuration"; target="management"; purpose="management"; data_direction="bidirectional"; initiator="configuration"; protocol="HTTPS"; enforcement=["enforcement"]

Interface integration: source="management"; target="analytics"; purpose="integration"; data_direction="bidirectional"; initiator="management"; protocol="HTTPS"

Constraint capacity: key="capacity_streams"; value=100

Constraint sizing: key="equipment_sizing"; value="undecided"

Constraint offline: key="no_internet"; value=true

Constraint resilience: key="resilience_required"; value=true
