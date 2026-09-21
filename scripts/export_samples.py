"""Generate demo exports from an immutable reference snapshot."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.api.app.domain.models import Project
from apps.api.app.exports.service import export
from apps.api.app.policies.engine import evaluate
import json
for pack in 'AB':
    folder=Path('fixtures/references')/pack
    p=Project.model_validate_json((folder/'project.json').read_text(encoding='utf-8'))
    for kind in p.views:
        body,_=export(p,'svg',kind);(folder/f'{kind}.svg').write_bytes(body)
    for format in ['docx','md','csv']:
        body,_=export(p,format);(folder/f'narrative.{format}' if format!='csv' else folder/'interfaces.csv').write_bytes(body)
    (folder/'findings.json').write_text(json.dumps(evaluate(p),indent=2),encoding='utf-8')
out=Path('reports/exports');out.mkdir(parents=True,exist_ok=True)
p=Project.model_validate_json(Path('fixtures/references/A/project.json').read_text(encoding='utf-8'))
for format in ['json','svg','docx','md','csv','pattern']:
    body,_=export(p,format);(out/f'architecture.{format if format!="pattern" else "pattern.json"}').write_bytes(body)
