"""One read-only catalogue for the palette, provider lookup and exports."""
import json
import re
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

def component_asset(value):
 """Choose a functional symbol for AI omissions/generic defaults, not hardware facts.

 Specific catalogue choices survive. This runs at the proposal boundary only;
 ordinary manual icon edits and existing saved projects are never rewritten.
 """
 allowed={row['id'] for row in catalogue()}
 supplied=value.get('asset_id')
 asset=re.sub(r'[ _]+','-',supplied.strip().lower()) if isinstance(supplied,str) else ''
 if asset in allowed-{'server','generic-role-a','generic-role-b'}:return asset
 if asset=='server' and value.get('form_factor')=='physical':return asset
 name=str(value.get('name','')).lower();role=str(value.get('role','')).lower()
 text=name+' '+role
 def has(pattern):return re.search(pattern,text) is not None
 if 'boundary' in role or role=='external system':
  return 'external-system' if value.get('scope')=='external' or role=='external system' else 'system-boundary'
 if has(r'\b(video archive|recording storage|archive|storage)\b'):return 'storage'
 if has(r'\b(database|data store|datastore|metadata store|event store)\b'):return 'database'
 if has(r'\b(workstation|operator client|desktop client|operator console)\b') or role in {'client','operator'}:return 'workstation'
 if has(r'\b(gateway)\b'):return 'gateway'
 if has(r'\b(api|integration adapter)\b'):return 'api-service'
 if has(r'\b(analytics processing|analytics engine|video analytics)\b'):return 'analytics-engine'
 if has(r'\b(firewall)\b'):return 'firewall'
 if has(r'\b(event broker|message broker)\b'):return 'event-broker'
 # A camera control *service* is software, not another camera sensor.
 if has(r'\b(server|host)\b'):return 'server'
 if has(r'\b(service|application|publisher)\b'):return 'application'
 if has(r'\b(camera|cameras)\b'):return 'camera'
 if has(r'\b(sensor|sensors|reader|readers|controller|controllers)\b'):return 'sensor'
 return asset if asset in allowed else 'generic-role-a'
