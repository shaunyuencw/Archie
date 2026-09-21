import json
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from apps.api.app.domain.commands import command, DomainError
from apps.api.app.domain.models import Project
from apps.api.app.storage.store import Store


def test_trash_and_restore_preserve_architecture_evidence_and_undo(tmp_path):
    store=Store(tmp_path/'projects.sqlite')
    original=store.create(Project.model_validate_json(Path('fixtures/demos/portal/project.json').read_text()))
    change=command(original,[{'op':'notes','value':{'text':'Keep the reviewer notes.'}}])
    accepted=store.commit(change)
    other=store.create(Project(name='Unaffected project'))
    before=accepted.model_dump_json()
    trashed=store.trash(accepted.id)
    assert store.trash(accepted.id)==trashed  # Repeated clicks keep the original timestamp.
    assert [p['id'] for p in store.list()]==[other.id]
    assert store.list_trash()==[{'id':accepted.id,'name':accepted.name,'revision':accepted.revision,'deleted_at':trashed['deleted_at']}]
    with pytest.raises(DomainError) as error:store.get(accepted.id)
    assert error.value.code=='project_trashed'
    with pytest.raises(DomainError):store.commit(change)  # Even cached requests cannot reopen Trash.
    with pytest.raises(DomainError):store.preview(command(accepted,[{'op':'notes','value':{'text':'Rejected edit'}}]))
    with store.connect() as db:
        assert db.execute('SELECT snapshot FROM projects WHERE id=?',(accepted.id,)).fetchone()[0]==before
        assert db.execute('SELECT COUNT(*) FROM history WHERE project_id=?',(accepted.id,)).fetchone()[0]==1
    restored=Store(tmp_path/'projects.sqlite').restore(accepted.id)
    assert restored==accepted and restored.sources==original.sources and restored.claims==original.claims
    assert store.list_trash()==[] and len(store.list())==2
    undone=store.undo(command(restored,[{'op':'notes','value':{}}]))
    assert undone.notes==original.notes
    assert store.redo(command(undone,[{'op':'notes','value':{}}])).notes==accepted.notes


def test_existing_project_database_migrates_to_trash_without_changing_snapshot(tmp_path):
    path=tmp_path/'legacy.sqlite';project=Project(name='Existing saved project')
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE projects(id TEXT PRIMARY KEY, snapshot TEXT NOT NULL)')
        db.execute('INSERT INTO projects VALUES(?,?)',(project.id,project.model_dump_json()))
    store=Store(path)
    assert store.get(project.id)==project
    store.trash(project.id);assert store.restore(project.id)==project
    with pytest.raises(DomainError) as error:store.trash('missing')
    assert error.value.status==404
    with pytest.raises(DomainError):store.restore('missing')


def test_project_trash_api_hides_deleted_projects_and_restores_same_record(tmp_path,monkeypatch):
    import apps.api.app.main as main
    monkeypatch.setattr(main,'store',Store(tmp_path/'api.sqlite'))
    client=TestClient(main.app)
    project=client.post('/api/projects',json={'name':'Delete and restore API','reference':'portal'}).json()
    pid=project['id']
    assert client.get('/api/projects/trash').json()==[]
    assert client.post(f'/api/projects/{pid}/trash',json={}).status_code==200
    assert all(row['id']!=pid for row in client.get('/api/projects').json())
    assert client.get('/api/projects/trash').json()[0]['id']==pid
    for path in ['', '/views/logical', '/exports/json']:
        assert client.get(f'/api/projects/{pid}{path}').status_code==404
    edit=command(Project.model_validate(project),[{'op':'notes','value':{'text':'Should not save'}}])
    assert client.post(f'/api/projects/{pid}/commands',json=json.loads(edit.model_dump_json())).status_code==404
    restored=client.post(f'/api/projects/{pid}/restore',json={})
    assert restored.status_code==200 and restored.json()==project
    assert client.get('/api/projects/trash').json()==[]
    assert client.get(f'/api/projects/{pid}').json()==project
    assert client.post('/api/projects/missing/trash',json={}).status_code==404
    assert client.post('/api/projects/missing/restore',json={}).status_code==404


def test_empty_trash_purges_only_confirmed_trashed_content_and_keeps_cost_ledger(tmp_path):
    from apps.api.app.ingest.parser import parse
    store=Store(tmp_path/'purge.sqlite')
    private=parse(b'Synthetic private source for deleted project.','Prompt','prompt',store)
    shared=parse(b'Synthetic shared source for active and deleted projects.','Prompt','prompt',store)
    deleted=store.create(Project(name='Purge this',sources=[private,shared]))
    active=store.create(Project(name='Keep active',sources=[shared]))
    later=store.create(Project(name='Trashed after the confirmation list was read'))
    proposal=store.preview(command(deleted,[{'op':'notes','value':{'text':'Pending deleted-project proposal'}}]))
    deleted=store.commit(command(deleted,[{'op':'notes','value':{'text':'Deleted project history'}}]))
    store.trash(deleted.id);store.trash(later.id)
    with store.connect() as db:
        db.executemany('INSERT INTO runs VALUES(?,?,?,?)',[
            ('deleted-run',deleted.id,'completed','{"source_excerpt":"project content"}'),
            ('active-run',active.id,'completed','{}')])
        db.executemany('INSERT INTO usage VALUES(?,?,?,?,?,?,?,?,?,?)',[
            ('spent',deleted.id,'a','2026-09-21','openai','test-model','completed',.04,.03,'{"input_tokens":10}'),
            ('reservation',deleted.id,'b','2026-09-21','openai','test-model','reserved',.02,None,'{}')])
        db.executemany('INSERT INTO cache VALUES(?,?)',[
            (f'narrative-v2:{deleted.id}:1','Deleted narrative'),
            (f'policy-review:{deleted.id}:mock:1:hash:model:v1',json.dumps({'project_id':deleted.id,'summary':'Deleted project policy review'})),
            (f'policy-review:{active.id}:mock:0:hash:model:v1',json.dumps({'project_id':active.id,'summary':'Active project policy review'})),
            (f'narrative-v2:{active.id}:0','Active narrative'),('unrelated-cache','Unrelated content')])
        db.execute('CREATE TABLE policy_library(id TEXT PRIMARY KEY,body TEXT NOT NULL)')
        db.execute('INSERT INTO policy_library VALUES(?,?)',('LOCAL-TEST','{"title":"Shared policy"}'))
        ledger=[tuple(row) for row in db.execute('SELECT * FROM usage ORDER BY id')]
    result=store.empty_trash([deleted.id,active.id,deleted.id])
    assert result=={'deleted_ids':[deleted.id],'deleted_count':1}
    assert store.get(active.id)==active and store.list_trash()[0]['id']==later.id
    with pytest.raises(DomainError):store.restore(deleted.id)
    with pytest.raises(DomainError):store.change(proposal.id)
    with store.connect() as db:
        for table in ['history','changes','requests','runs','project_trash']:
            assert db.execute(f'SELECT COUNT(*) FROM {table} WHERE project_id=?',(deleted.id,)).fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM projects WHERE id=?',(deleted.id,)).fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM runs WHERE id=?',('active-run',)).fetchone()[0]==1
        assert [tuple(row) for row in db.execute('SELECT * FROM usage ORDER BY id')]==ledger
        assert db.execute('SELECT SUM(COALESCE(cost,reserved)) FROM usage').fetchone()[0]==pytest.approx(.05)
        cache={row['hash'] for row in db.execute('SELECT hash FROM cache')}
        assert private.sha256 not in cache and f'narrative-v2:{deleted.id}:1' not in cache
        assert f'policy-review:{deleted.id}:mock:1:hash:model:v1' not in cache
        assert f'policy-review:{active.id}:mock:0:hash:model:v1' in cache
        assert {shared.sha256,f'narrative-v2:{active.id}:0','unrelated-cache'}<=cache
        assert db.execute('SELECT body FROM policy_library WHERE id=?',('LOCAL-TEST',)).fetchone()[0]=='{"title":"Shared policy"}'


def test_empty_trash_cache_ownership_handles_imported_id_delimiters(tmp_path):
    store=Store(tmp_path/'imported-ids.sqlite')
    deleted=store.create(Project(id='imported:_%',name='Imported project'))
    active=store.create(Project(id=deleted.id+':keep',name='Keep similar ID'))
    def keys(p):return [f'narrative-v2:{p.id}:0',f'policy-review:{p.id}:ollama:0:fingerprint:qwen:7b:v1']
    with store.connect() as db:
        for project in [deleted,active]:
            for key in keys(project):db.execute('INSERT INTO cache VALUES(?,?)',(key,json.dumps({'project_id':project.id})))
    store.trash(deleted.id);store.empty_trash([deleted.id])
    with store.connect() as db:assert {row['hash'] for row in db.execute('SELECT hash FROM cache')}==set(keys(active))
    assert store.get(active.id)==active


def test_empty_trash_rolls_back_the_entire_purge_if_a_database_write_fails(tmp_path):
    store=Store(tmp_path/'atomic.sqlite');p=store.create(Project())
    p=store.commit(command(p,[{'op':'notes','value':{'text':'Saved history'}}]));store.trash(p.id)
    with store.connect() as db:
        db.execute("CREATE TRIGGER stop_purge BEFORE DELETE ON projects BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END")
    with pytest.raises(sqlite3.IntegrityError):store.empty_trash([p.id])
    assert store.restore(p.id)==p
    assert store.undo(command(p,[{'op':'notes','value':{}}])).notes==''


def test_empty_trash_api_requires_confirmation_and_cannot_remove_active_projects(tmp_path,monkeypatch):
    import apps.api.app.main as main
    monkeypatch.setattr(main,'store',Store(tmp_path/'empty-api.sqlite'));client=TestClient(main.app)
    dead=client.post('/api/projects',json={'name':'Remove only this project'}).json()
    active=client.post('/api/projects',json={'name':'Keep this project'}).json()
    client.post('/api/projects/'+dead['id']+'/trash',json={})
    payload={'project_ids':[dead['id'],active['id']]}
    assert client.post('/api/projects/trash/empty',json=payload).status_code==422
    assert client.get('/api/projects/trash').json()[0]['id']==dead['id']
    result=client.post('/api/projects/trash/empty',json={**payload,'confirmed':True})
    assert result.status_code==200 and result.json()=={'deleted_ids':[dead['id']],'deleted_count':1}
    assert client.get('/api/projects/trash').json()==[]
    assert client.get('/api/projects/'+active['id']).json()==active
    assert client.post('/api/projects/'+dead['id']+'/restore',json={}).status_code==404
    assert client.post('/api/projects/trash/empty',json={**payload,'confirmed':True}).json()['deleted_count']==0


def test_empty_trash_waits_for_running_model_actions_before_removing_any_project(tmp_path,monkeypatch):
    import apps.api.app.main as main
    store=Store(tmp_path/'running.sqlite');monkeypatch.setattr(main,'store',store);client=TestClient(main.app)
    reviewing=store.create(Project(name='Review in progress'));other=store.create(Project(name='Also in Trash'))
    store.trash(reviewing.id);store.trash(other.id)
    with store.connect() as db:db.execute('INSERT INTO runs VALUES(?,?,?,?)',('policy-review:running',reviewing.id,'running','{}'))
    payload={'confirmed':True,'project_ids':[reviewing.id,other.id]}
    response=client.post('/api/projects/trash/empty',json=payload)
    assert response.status_code==409 and response.json()['code']=='project_busy'
    assert {p['id'] for p in store.list_trash()}=={reviewing.id,other.id}
    with store.connect() as db:db.execute("UPDATE runs SET status='completed' WHERE id='policy-review:running'")
    assert client.post('/api/projects/trash/empty',json=payload).json()['deleted_count']==2
    assert store.list_trash()==[]
