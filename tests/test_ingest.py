from pathlib import Path
from apps.api.app.storage.store import Store
from apps.api.app.domain.models import Project
from apps.api.app.orchestration.service import ingest
from apps.api.app.ingest.parser import parse,batch

def accept(store,result):
    assert result['proposal'] is not None
    return store.commit(result['proposal'])

def test_T01_prompt_baseline(tmp_path):
    store=Store(tmp_path/'db');p=store.create(Project())
    result=ingest(store,p.id,b'Existing VMS in Infrastructure; two workstations in Client; VAP management/integration services in Z1; VAP analytics in Z2. Existing C2 is outside VAP and its internal zoning is unspecified.','Prompt','prompt')
    p=accept(store,result)
    assert len(p.components)==6 and {z.name for z in p.zones}=={'Infrastructure','Client','Z1','Z2'}
    assert next(d for d in p.deployments if d.component_id=='c2').zone_id is None
    assert all(c.evidence for c in p.components)

def test_T02_T03_docx_pdf_and_dedup(tmp_path):
    store=Store(tmp_path/'db');p=store.create(Project())
    source=Path('fixtures/projects/A/spec.docx')
    p=accept(store,ingest(store,p.id,source.read_bytes(),source.name))
    assert len(p.components)==8 and len(p.interfaces)==4
    assert any(c.locator.startswith('table/') and c.target_id=='video' for c in p.claims)
    result=ingest(store,p.id,Path('fixtures/projects/A/spec.pdf').read_bytes(),'spec.pdf')
    assert result['duplicate']; assert len(store.get(p.id).components)==8
    p2=store.create(Project());p2=accept(store,ingest(store,p2.id,Path('fixtures/projects/A/spec.pdf').read_bytes(),'spec.pdf'))
    assert len(p2.components)==8 and len(p2.interfaces)==4
    assert all(c.locator.startswith('page/') for c in p2.claims)

def test_T04_T05_unknowns_conflicts(tmp_path):
    store=Store(tmp_path/'db');p=store.create(Project())
    p=accept(store,ingest(store,p.id,Path('fixtures/projects/B/spec.docx').read_bytes(),'spec.docx'))
    assert all(i.initiator is None for i in p.interfaces)
    assert 0<len(p.decisions)<=3
    p=store.create(Project())
    for kind in ['sow','spec']:
        result=ingest(store,p.id,Path(f'fixtures/projects/C/{kind}.docx').read_bytes(),kind+'.docx')
        if result['proposal']: p=accept(store,result)
    assert any(c.key=='no_internet' and c.value is True for c in p.constraints)
    assert any(c.internet_hosted for c in p.components)
    assert len(p.sources)==2

def test_T15_coverage():
    source=parse(('Section words. '*5000).encode(),'Prompt','prompt')
    selected=batch(source)
    assert sum(len(s.text) for s in selected)<=24000
    assert len(selected)<len(source.unprocessed)
