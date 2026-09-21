"""Authored-fixture extraction metrics. This is not an independent benchmark."""
import json,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.api.app.domain.models import Project
from apps.api.app.storage.store import Store
from apps.api.app.orchestration.service import ingest
from scripts.seed import facts

rows=[]
with tempfile.TemporaryDirectory() as folder:
    s=Store(Path(folder)/'db')
    for pack in 'ABC':
        _,expected=facts(pack);wanted={('component',x['id']) for x in expected['components']}|{('interface',x['id']) for x in expected['interfaces']}
        for format in ['docx','pdf']:
            p=s.create(Project());start=time.perf_counter();questions=0;accepted=0
            path=Path(f'fixtures/projects/{pack}/spec.{format}')
            result=ingest(s,p.id,path.read_bytes(),path.name)
            if result['proposal']:
                p=s.commit(result['proposal']);accepted=len(result['proposal'].operations);questions=len(p.decisions)
            actual={('component',x.id) for x in p.components}|{('interface',x.id) for x in p.interfaces}
            tp=len(actual&wanted);fp=len(actual-wanted);fn=len(wanted-actual)
            rows.append({'fixture':pack,'format':format,'true_positive':tp,'false_positive':fp,'false_negative':fn,'precision':tp/(tp+fp) if tp+fp else 0,'recall':tp/(tp+fn),'missed':sorted(wanted-actual),'questions':questions,'accepted_operations':accepted,'repairs':0,'provider':'mock','api_calls':0,'api_cost_usd':0,'latency_ms':round((time.perf_counter()-start)*1000,2),'unprocessed_sections':len(p.sources[0].unprocessed)})
Path('reports/extraction-metrics.json').write_text(json.dumps({'caveat':'Agent-authored expectations and mock fixture parser; no claim of real-world accuracy or independent evaluation. Metrics count explicitly enumerated component/interface records, not every field.','results':rows},indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
