"""One read-only catalogue for the palette, provider lookup and exports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
GROUPS={
 'Compute':{'server','gpu-server','application','analytics-engine','database','storage','event-broker','api-service'},
 'Networking':{'switch','router','gateway','proxy','load-balancer'},
 'Security':{'firewall','identity-service','audit-service'},
 'Devices & robotics':{'workstation','camera'},
 'Boundaries & other':{'external-system','network-zone','system-boundary','site','generic-role-a','generic-role-b'},
}
def catalogue():
 rows=json.loads((ROOT/'fixtures/assets/manifest.json').read_text())
 extra=ROOT/'fixtures/assets/extra-manifest.json'
 if extra.exists():rows+=json.loads(extra.read_text())
 return [{**r,'label':r.get('label',r['id'].replace('-',' ').capitalize()),'category':r.get('category',next((name for name,ids in GROUPS.items() if r['id'] in ids),'Boundaries & other'))} for r in rows]
