import pytest
from pathlib import Path
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.app.domain.commands import DomainError, apply, command
from apps.api.app.domain.models import Project, Zone, Interface
from apps.api.app.policies.engine import evaluate, zone_tier, lookup
from apps.api.app.policies.library import clauses, router
from apps.api.app.storage.store import Store


def project_with_tiers():
    return Project(name='Three-tier test', policy_ids=['ARCH-SEG-01', 'ARCH-DAT-01', 'ARCH-FLW-01'],
        zones=[{'id':'zone-desktops','name':'Client · Physical endpoints'}, {'id':'zone-web','name':'Z1 · Application'}, {'id':'zone-data','name':'Z2 · Protected data'}],
        components=[{'id':'pc','name':'User PC','role':'operator','asset_id':'workstation'}, {'id':'app','name':'Web app','role':'application'}, {'id':'db','name':'Database','role':'data','asset_id':'database'}, {'id':'fw','name':'Firewall','role':'enforcement','asset_id':'firewall'}],
        deployments=[{'id':'deploy-pc','component_id':'pc','zone_id':'zone-desktops'}, {'id':'deploy-app','component_id':'app','zone_id':'zone-web'}, {'id':'deploy-db','component_id':'db','zone_id':'zone-data'}],
        interfaces=[{'id':'web','source':'pc','target':'app','enforcement':['fw']}, {'id':'data','source':'app','target':'db','enforcement':['fw']}])


def test_policy_selection_is_versioned_and_undoable(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_POLICY_DB',str(tmp_path/'policies.sqlite'))
    store=Store(tmp_path/'projects.sqlite'); project=store.create(Project())
    selected=store.commit(command(project,[{'op':'policy_selection','value':{'policy_ids':['ARCH-SEG-01','ARCH-BAK-01']}}]))
    assert selected.revision==project.revision+1
    assert {k:v.revision for k,v in selected.views.items()}=={k:v.revision for k,v in project.views.items()}
    assert selected.policy_ids==['ARCH-SEG-01','ARCH-BAK-01']
    findings=evaluate(selected)
    assert findings['implemented']==1 and findings['manual_review']==1
    assert {f['clause_id'] for f in findings['findings']}==set(selected.policy_ids)
    restored=store.undo(command(selected,[{'op':'notes','value':{}}]))
    assert restored.policy_ids is None
    assert evaluate(restored)['implemented']==8
    assert evaluate(restored)['manual_review']==12
    assert store.redo(command(restored,[{'op':'notes','value':{}}])).policy_ids==selected.policy_ids
    empty=apply(selected,command(selected,[{'op':'policy_selection','value':{'policy_ids':[]}}]))
    assert evaluate(empty)['findings']==[]
    for value in [{'policy_ids':['invented']},{'policy_ids':['ARCH-SEG-01','ARCH-SEG-01']},{'policy_ids':'ARCH-SEG-01'},{'policy_ids':None},{'policy_ids':[],'unexpected':True}]:
        with pytest.raises(DomainError):apply(project,command(project,[{'op':'policy_selection','value':value}]))


def test_three_tier_checks_use_declared_names_and_both_path_directions():
    project=project_with_tiers()
    assert all(f['result']=='pass' for f in evaluate(project)['findings'])
    project.interfaces.append(project.interfaces[0].model_copy(update={'id':'bypass','source':'db','target':'pc','enforcement':[]}))
    result={f['clause_id']:f for f in evaluate(project)['findings']}
    assert result['ARCH-SEG-01']['result']=='potential_conflict'
    assert result['ARCH-FLW-01']['result']=='insufficient_information'
    assert 'bypass' in result['ARCH-SEG-01']['affected_ids']
    project.deployments[-1].zone_id='zone-web'
    result={f['clause_id']:f for f in evaluate(project)['findings']}
    assert result['ARCH-DAT-01']['result']=='potential_conflict'
    project.deployments[-1].zone_id=None
    result={f['clause_id']:f for f in evaluate(project)['findings']}
    assert result['ARCH-DAT-01']['result']=='insufficient_information'


def test_global_custom_policy_persists_without_auto_attaching(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_POLICY_DB',str(tmp_path/'policies.sqlite'))
    app=FastAPI();app.include_router(router);client=TestClient(app)
    library=client.get('/api/policies').json()
    assert len(library['clauses'])==42
    assert len(library['legacy_ids'])==20
    response=client.post('/api/policies',json={'title':'Review trial retention','text':'Delete trial telemetry after the agreed trial retention period.','applicability':'Wireless robotics trial data','tags':['trial','retention']})
    assert response.status_code==201
    added=response.json();assert added['implementation']=='manual_review'
    assert client.get('/api/policies?q=trial+retention').status_code==200
    assert added['id'] in {c['id'] for c in clauses()}
    first=Project(policy_ids=[]); second=Project(policy_ids=[])
    first=apply(first,command(first,[{'op':'policy_selection','value':{'policy_ids':[added['id']]}}]))
    assert evaluate(first)['findings'][0]['execution']=='manual_review'
    assert evaluate(second)['findings']==[]
    assert client.post('/api/policies',json={'title':'   ','text':'A valid length policy clause.','applicability':'All systems'}).status_code==422
    assert client.post('/api/policies',json={'title':'Execute me','text':'A valid length policy clause.','applicability':'All systems','implementation':'implemented'}).status_code==422


def test_imported_missing_local_policy_is_unresolved():
    result=evaluate(Project(policy_ids=['LOCAL-MISSING']))
    assert result['findings'][0]['execution']=='error'
    assert result['findings'][0]['result']=='insufficient_information'
    assert result['implemented']==0


def test_imported_policy_selections_reject_duplicates():
    with pytest.raises(ValidationError,match='Policy IDs must be unique'):
        Project.model_validate_json('{"policy_ids":["ARCH-SEG-01","ARCH-SEG-01"]}')
    assert Project(policy_ids=[]).policy_ids==[]
    assert Project().policy_ids is None


def test_policy_retrieval_ranks_only_the_selected_subset(monkeypatch):
    rows=[{'id':f'POL-{index}','text':'backup '*max(1,10-index),'tags':['backup']} for index in range(6)]
    monkeypatch.setattr('apps.api.app.policies.engine.clauses',lambda:rows)
    global_ids={item['id'] for item in lookup('backup')}
    selected=next(row['id'] for row in rows if row['id'] not in global_ids)
    assert lookup('backup',policy_ids=[])==[]
    assert [item['id'] for item in lookup('backup',policy_ids=[selected])]==[selected]
    assert lookup('backup',policy_ids=['missing'])==[]


def test_live_policy_tool_respects_project_applicability():
    from apps.api.app.orchestration.live import dispatch
    tool=SimpleNamespace(name='lookup_policies',query='backup')
    assert dispatch(tool,Project(policy_ids=[]))==[]
    assert [item['id'] for item in dispatch(tool,Project(policy_ids=['ARCH-BAK-01']))]==['ARCH-BAK-01']
    legacy_ids={item['id'] for item in dispatch(tool,Project())}
    assert legacy_ids and all(ident.startswith('DEMO-') for ident in legacy_ids)


@pytest.mark.parametrize('ident,name,expected',[
    ('prod-z2','Production · Z2 · protected data','z2'),
    ('test-client','Testbed · Client · trial devices','client'),
    ('aws-z1','AWS · Z1 · telemetry ingestion','z1'),
    ('opaque-zone-id','Production · Z2 · protected data','z2'),
    ('client-service','Client support team',None),
    ('clientele','Production clients',None),
    ('random-z2','A zone that connects to Z2',None),
    ('z2','Z1 · conflicting label',None),
])
def test_tiers_require_explicit_unambiguous_labels(ident,name,expected):
    assert zone_tier(Zone(id=ident,name=name))==expected


@pytest.mark.parametrize('demo,client,database',[
    ('portal','employee','request-db'),
    ('robotics','trial-robot','prod-db'),
])
def test_demo_policies_detect_protected_database_bypass(demo,client,database):
    project=Project.model_validate_json(Path(f'fixtures/demos/{demo}/project.json').read_text())
    # Exercise the selected policy pack rather than substituting test-only applicability.
    assert {'ARCH-SEG-01','ARCH-DAT-01','ARCH-FLW-01'}<=set(project.policy_ids or [])
    initial={finding['clause_id']:finding for finding in evaluate(project)['findings']}
    assert initial['ARCH-SEG-01']['result']=='pass'
    assert initial['ARCH-DAT-01']['result']=='pass'
    project.interfaces.append(Interface(id='test-protected-bypass',source=database,target=client))
    changed={finding['clause_id']:finding for finding in evaluate(project)['findings']}
    assert changed['ARCH-SEG-01']['result']=='potential_conflict'
    assert 'test-protected-bypass' in changed['ARCH-SEG-01']['affected_ids']
    database_deployment=next(deployment for deployment in project.deployments if deployment.component_id==database)
    database_deployment.zone_id=next(deployment.zone_id for deployment in project.deployments if deployment.component_id==client)
    changed={finding['clause_id']:finding for finding in evaluate(project)['findings']}
    assert changed['ARCH-DAT-01']['result']=='potential_conflict'
