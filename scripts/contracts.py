import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.api.app.domain.models import Project, ChangeSet
from pydantic import create_model
Contract=create_model('Contract',project=(Project,...),change=(ChangeSet,...))
Path('packages/contracts').mkdir(parents=True,exist_ok=True)
schema=Contract.model_json_schema()
# API responses materialise every Pydantic default; command inputs may omit defaults.
for name,definition in schema['$defs'].items():
    if name not in ('ChangeSet','Operation') and 'properties' in definition:
        definition['required']=list(definition['properties'])
Path('packages/contracts/schema.json').write_text(json.dumps(schema,indent=2),encoding='utf-8')
