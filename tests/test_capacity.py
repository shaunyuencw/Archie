import json,time
from apps.api.app.domain.models import Project
from apps.api.app.domain.commands import command
from apps.api.app.storage.store import Store

def test_T14_capacity_preserves_references(tmp_path):
    p=Project(components=[{'id':f'c{i}','name':f'Component {i}','role':'application'} for i in range(50)],interfaces=[{'id':f'i{i}','source':f'c{i%50}','target':f'c{(i+1)%50}'} for i in range(100)])
    s=Store(tmp_path/'db');start=time.perf_counter();p=s.create(p)
    p=s.commit(command(p,[{'op':'update','entity':'components','id':'c49','value':{'name':'Last component edited'}}]));reopened=s.get(p.id)
    elapsed=(time.perf_counter()-start)*1000
    assert reopened==p and len(p.components)==50 and len(p.interfaces)==100
    assert p.components[-1].name=='Last component edited'
    from pathlib import Path
    Path('reports/capacity.json').write_text(json.dumps({'components':50,'interfaces':100,'create_edit_reopen_ms':round(elapsed,3),'measurement':'Python SQLite transaction plus reload; browser measurement separate'},indent=2))
