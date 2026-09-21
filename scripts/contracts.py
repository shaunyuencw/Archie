import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.api.app.domain.models import Project, ChangeSet
from pydantic import create_model
Contract=create_model('Contract',project=(Project,...),change=(ChangeSet,...))
Path('packages/contracts').mkdir(parents=True,exist_ok=True)
Path('packages/contracts/schema.json').write_text(json.dumps(Contract.model_json_schema(),indent=2),encoding='utf-8')
