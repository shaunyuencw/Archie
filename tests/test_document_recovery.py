"""Bounded document recovery uses prior typed records and never accepts a broken graph."""
import json
import threading

import pytest

from apps.api.app.domain.commands import DomainError, command
from apps.api.app.domain.models import Passage, Project, Source
from apps.api.app.domain.views import view_graph
from apps.api.app.orchestration.documents import document_preflight, ingest_live
from apps.api.app.providers.budget import usage_summary
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope, ProviderResult, Usage
from apps.api.app.storage.store import Store


SYSTEM_TEXT='SYS-VAS Video Analytics System. SYS-C2 Command and Control System.'
FLOW_TEXT='SYS-VAS sends analytics alerts to SYS-C2.'


def document():
    return Source(id='spec',name='Synthetic multi-page system specification',kind='document',sha256='spec',canonical_id='spec',
                  passages=[Passage(locator='page/1',text=SYSTEM_TEXT+'\n'+('Synthetic overview. '*170)),
                            Passage(locator='page/2',text=FLOW_TEXT+'\n'+('Synthetic interfaces. '*155))])


def response(operations,locator='page/1',quote=SYSTEM_TEXT):
    return Envelope(operations=[{'op':op.get('op','add'),'entity':op['entity'],'id':op['id'],
                                 'value_json':json.dumps(op['value'])} for op in operations],
                    claims=[{'source_id':'S1','locator':locator,'excerpt':quote,'target_id':op['id'],
                             'field':'record','value_json':'null'} for op in operations],tool=None,message='Review the draft.')


def systems():
    return response([{'entity':'systems','id':ident,'value':{'name':name}} for ident,name in [
        ('SYS-VAS','Video Analytics System'),('SYS-C2','Command and Control System')]])


def flow(repaired=False):
    operations=[]
    if repaired:
        operations=[{'entity':'components','id':f'tmp:boundary-{ident}',
                     'value':{'name':name+' boundary','role':'system boundary','system_id':ident}}
                    for ident,name in [('SYS-VAS','Video Analytics System'),('SYS-C2','Command and Control System')]]
    operations.append({'entity':'interfaces','id':'IF-01','value':{
        'source':'tmp:boundary-SYS-VAS' if repaired else 'SYS-VAS',
        'target':'tmp:boundary-SYS-C2' if repaired else 'SYS-C2',
        'purpose':'analytics alerts','data_direction':'source_to_target'}})
    return response(operations,'page/2',FLOW_TEXT)


class ScriptedAdapter:
    name='openai'
    model='gpt-5.4-mini'

    def __init__(self,outputs,callback=None):
        self.outputs=list(outputs);self.prompts=[];self.callback=callback

    def generate_structured(self,prompt,*args):
        self.prompts.append(json.loads(prompt))
        if self.callback:self.callback(len(self.prompts))
        output=self.outputs.pop(0)
        if isinstance(output,Exception):raise output
        return ProviderResult(content=output,finish_status='completed',model=self.model,usage=Usage(input_tokens=50,output_tokens=50))


def setup(tmp_path,monkeypatch):
    store=Store(tmp_path/'recovery.sqlite');project=store.create(Project())
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:document())
    return store,project


def settings(**kwargs):
    return Settings(allow_cloud=True,max_input=32000,max_calls=kwargs.pop('max_calls',3),**kwargs)


def test_cross_page_system_flow_gets_one_targeted_repair_and_review(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    adapter=ScriptedAdapter([systems(),flow(),flow(repaired=True)])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert len(adapter.prompts)==3 and result['repairs']==1
    assert len(adapter.prompts[0]['source']['passages'])==1
    assert {r['id'] for r in adapter.prompts[1]['known_records']['systems']}=={'SYS-VAS','SYS-C2'}
    repair=adapter.prompts[2]
    assert 'repair' in repair and 'SYS-VAS' in repair['validation_error'] and 'identifies a system' in repair['validation_error']
    assert repair['previous_response']==flow().model_dump()
    assert {p['locator'] for p in repair['source']['passages']}=={'page/1','page/2'}
    assert store.get(project.id)==project
    accepted=store.commit(result['proposal'])
    assert len(accepted.systems)==2 and len(accepted.components)==2 and len(accepted.interfaces)==1
    assert all(c.role=='system boundary' and c.form_factor=='unknown' for c in accepted.components)
    assert not accepted.deployments
    assert accepted.interfaces[0].initiator is None and accepted.interfaces[0].protocol is None
    assert accepted.sources[0].processed==['page/1','page/2'] and not accepted.sources[0].unprocessed
    for kind in accepted.views:
        graph=view_graph(accepted,kind)
        ids={n['id'] for n in graph['nodes']}
        assert len(graph['edges'])==1 and all(e['source'] in ids and e['target'] in ids for e in graph['edges'])
    records=usage_summary(store,project.id)['records']
    assert len(records)==3 and len({r['action_id'] for r in records})==1


def test_valid_batches_need_no_repair_request(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    adapter=ScriptedAdapter([systems(),flow(repaired=True)])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert len(adapter.prompts)==2 and result['repairs']==0
    assert result['preflight']['requests']==2 and store.get(project.id)==project


def test_numbered_connections_are_extracted_when_the_first_response_omits_them(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    text='IF-01: Client sends requests to Application.'
    spec=document();spec.passages=[Passage(locator='page/1',text=text)]
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:spec)
    parts=response([{'entity':'components','id':ident,'value':{'name':name,'role':'application'}} for ident,name in [('c','Client'),('a','Application')]],'page/1',text)
    links=response([{'entity':'interfaces','id':'IF-01','value':{'source':'c','target':'a','purpose':'requests'}}],'page/1',text)
    adapter=ScriptedAdapter([parts,links])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert len(adapter.prompts)==2 and result['repairs']==0
    assert 'EVERY numbered IF connection' in adapter.prompts[1]['task']
    assert len(store.commit(result['proposal']).interfaces)==1


def test_missing_numbered_connections_cannot_be_silently_accepted(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    spec=document();spec.passages=[Passage(locator='page/1',text='IF-01: Client sends requests to Application. '+SYSTEM_TEXT)]
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:spec)
    adapter=ScriptedAdapter([systems()])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(max_calls=1),adapter)
    assert any('source lists 1 connections' in f for f in result['proposal'].findings)
    assert result['coverage']['unprocessed']==['page/1']
    assert store.get(project.id)==project and len(adapter.prompts)==1


def test_later_deployment_details_refine_core_boundary_and_preserve_declared_flow(tmp_path,monkeypatch):
    """Exercise the prompted refinement contract without asserting live-model quality."""
    store,project=setup(tmp_path,monkeypatch)
    detail='C2 has operator workstations and application services in the Operations zone.'
    spec=document()
    spec.passages[1].text=detail+'\n'+('Synthetic deployment note. '*120)
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:spec)
    first=response([
        {'entity':'systems','id':'SYS-C2','value':{'name':'Command and Control'}},
        {'entity':'systems','id':'SYS-VAS','value':{'name':'Video Analytics'}},
        {'entity':'components','id':'c2','value':{'name':'C2 boundary','role':'system boundary','system_id':'SYS-C2','asset_id':'system-boundary'}},
        {'entity':'components','id':'vas','value':{'name':'VAS boundary','role':'system boundary','system_id':'SYS-VAS','asset_id':'system-boundary'}},
        {'entity':'interfaces','id':'alerts','value':{'source':'vas','target':'c2','purpose':'analytics alerts','data_direction':'source_to_target'}},
    ])
    spec.passages[0].text=SYSTEM_TEXT+' '+FLOW_TEXT+'\n'+('Synthetic overview. '*170)
    first.claims[-1].excerpt=FLOW_TEXT
    second=response([
        {'op':'update','entity':'components','id':'c2','value':{'name':'C2 application services','role':'application services','asset_id':'application','status':'proposed'}},
        {'entity':'components','id':'operators','value':{'name':'Operator workstations','role':'operator client','asset_id':'workstation','system_id':'SYS-C2','status':'proposed'}},
        {'entity':'zones','id':'operations','value':{'name':'Operations zone'}},
        {'entity':'deployments','id':'app-deployment','value':{'component_id':'c2','zone_id':'operations'}},
        {'entity':'deployments','id':'operator-deployment','value':{'component_id':'operators','zone_id':'operations'}},
    ],'page/2',detail)
    adapter=ScriptedAdapter([first,second])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert result['repairs']==0 and len(adapter.prompts)==2
    assert any(r['id']=='c2' and r['role']=='system boundary' for r in adapter.prompts[1]['known_records']['components'])
    accepted=store.commit(result['proposal'])
    assert {c.name for c in accepted.components if c.system_id=='SYS-C2'}=={'C2 application services','Operator workstations'}
    assert all(c.status=='proposed' and c.form_factor=='unknown' for c in accepted.components)
    assert len(accepted.interfaces)==1 and accepted.interfaces[0].target=='c2'
    assert accepted.interfaces[0].data_direction=='source_to_target'
    assert accepted.interfaces[0].protocol is None and accepted.interfaces[0].initiator is None
    assert all(d.quantity is None and d.host_component_id is None for d in accepted.deployments)
    assert len(view_graph(accepted,'logical')['nodes'])==4  # Three parts and one zone.
    assert len(view_graph(accepted,'sv1')['nodes'])==2
    assert len(accepted.claims)==10 and all(c.excerpt for c in accepted.claims)


def test_second_invalid_repair_returns_partial_draft_without_third_attempt(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    adapter=ScriptedAdapter([systems(),flow(),flow()])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(max_calls=8),adapter)
    assert len(adapter.prompts)==3 and store.get(project.id)==project
    assert any('Omitted IF-01' in f for f in result['proposal'].findings)
    accepted=store.commit(result['proposal'])
    assert len(accepted.systems)==2 and not accepted.interfaces


def test_preflight_reserves_repair_and_reports_unprocessed_sections():
    _,groups,remainder=document_preflight(document(),'openai',settings(max_calls=2))
    assert [[p.locator for p in g] for g in groups]==[['page/1']]
    assert [[p.locator for p in g] for g in remainder]==[['page/2']]
    _,single,remainder=document_preflight(document(),'openai',settings(max_calls=1))
    assert len(single)==len(remainder)==1


def test_one_call_profile_never_spends_on_repair(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    invalid=response([{'entity':'components','id':'processor','value':{'name':'Processor','role':'application','system_id':'missing'}}])
    adapter=ScriptedAdapter([invalid])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(max_calls=1),adapter)
    assert any('Omitted processor' in f for f in result['proposal'].findings)
    assert len(adapter.prompts)==1 and store.get(project.id)==project


def test_repair_stays_inside_remaining_spending_budget(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch);config=settings()
    def exhaust_spending(call):
        if call==2:config.document_usd=0.000001
    adapter=ScriptedAdapter([systems(),flow()],exhaust_spending)
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',config,adapter)
    assert any('spending reservation limit' in f for f in result['proposal'].findings)
    assert len(adapter.prompts)==2 and store.get(project.id)==project
    assert usage_summary(store,project.id)['calls']==2


@pytest.mark.parametrize('code',['provider_timeout','cancelled','unavailable_provider'])
def test_transport_failure_never_starts_schema_repair(tmp_path,monkeypatch,code):
    store,project=setup(tmp_path,monkeypatch)
    adapter=ScriptedAdapter([DomainError(code,'Transport stopped')])
    if code=='cancelled':
        with pytest.raises(DomainError) as error:
            ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
        assert error.value.code==code
    else:
        result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
        assert any('Transport stopped' in f for f in result['proposal'].findings)
        assert result['coverage']['processed']==[]
    assert len(adapter.prompts)==1 and store.get(project.id)==project


def test_cancel_before_repair_preserves_project_and_usage(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch);cancel=threading.Event()
    adapter=ScriptedAdapter([systems(),flow()],lambda call:cancel.set() if call==2 else None)
    with pytest.raises(DomainError) as error:
        ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter,cancel=cancel)
    assert error.value.code=='cancelled'
    assert len(adapter.prompts)==2 and store.get(project.id)==project
    assert usage_summary(store,project.id)['calls']==2


def test_concurrent_edit_is_not_repaired_or_overwritten(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    def manual_edit(call):
        if call==2:store.commit(command(project,[{'op':'notes','value':{'text':'Keep my manual note'}}]))
    adapter=ScriptedAdapter([systems(),flow(repaired=True)],manual_edit)
    with pytest.raises(DomainError) as error:
        ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert error.value.code=='stale_revision' and len(adapter.prompts)==2
    assert store.get(project.id).notes=='Keep my manual note' and not store.get(project.id).components


def test_unseen_page_citation_is_not_verified_even_if_parse_cache_contains_text(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    adapter=ScriptedAdapter([response([{'entity':'systems','id':'SYS-VAS','value':{'name':'Video Analytics System'}}],
                                     'page/2',FLOW_TEXT)])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(max_calls=1),adapter)
    assert store.get(project.id)==project
    accepted=store.commit(result['proposal'])
    assert not any(c.review=='confirmed' for c in accepted.claims)
    assert any('citation could not be verified' in f for f in result['proposal'].findings)


def test_identical_repeated_declaration_is_deduplicated_locally(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    repeated=systems();repeated.claims=[c.model_copy(update={'locator':'page/2','excerpt':FLOW_TEXT}) for c in repeated.claims]
    adapter=ScriptedAdapter([systems(),repeated])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert result['repairs']==0 and len(adapter.prompts)==2
    accepted=store.commit(result['proposal'])
    assert len(accepted.systems)==2 and len(accepted.claims)==4


def test_malformed_record_json_is_omitted_without_a_paid_repair(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    invalid=systems();invalid.operations[0].value_json='{"name":'
    adapter=ScriptedAdapter([invalid,flow(repaired=True),systems()])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert result['repairs']==0 and len(adapter.prompts)==2
    assert adapter.prompts[1]['known_records']['unreadable_operations']==[{'entity':'systems','id':'SYS-VAS'}]
    assert any('Omitted SYS-VAS' in f for f in result['proposal'].findings)
    accepted=store.commit(result['proposal'])
    assert [s.id for s in accepted.systems]==['SYS-C2']
    assert len(accepted.components)==1 and not accepted.interfaces


def test_malformed_claim_keeps_its_record_unverified_without_a_paid_repair(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    invalid=systems();invalid.claims[0].value_json='{"name":"Video Analytics",}'
    adapter=ScriptedAdapter([invalid,flow(repaired=True),systems()])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert result['repairs']==0 and len(adapter.prompts)==2
    accepted=store.commit(result['proposal'])
    assert len(accepted.interfaces)==1
    assert not any(c.target_id=='SYS-VAS' and c.review=='confirmed' for c in accepted.claims)


def test_omitted_json_record_is_named_without_exposing_parser_trace(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    invalid=systems();invalid.operations[0].value_json='{"name":"Video Analytics",}'
    adapter=ScriptedAdapter([invalid,flow(repaired=True),invalid])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert any('Omitted SYS-VAS' in f for f in result['proposal'].findings)
    assert all('Expecting property name' not in f for f in result['proposal'].findings)
    assert len(adapter.prompts)==2 and store.get(project.id)==project


def test_conflicting_repeated_add_keeps_first_definition_with_warning(tmp_path,monkeypatch):
    store,project=setup(tmp_path,monkeypatch)
    duplicate=flow(repaired=True)
    conflicting=response([{'entity':'systems','id':'SYS-VAS','value':{'name':'Wrong system'}}],'page/2',FLOW_TEXT)
    duplicate.operations.extend(conflicting.operations);duplicate.claims.extend(conflicting.claims)
    adapter=ScriptedAdapter([systems(),duplicate,flow(repaired=True)])
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings(),adapter)
    assert result['repairs']==0 and len(adapter.prompts)==2
    assert any('conflicting duplicate SYS-VAS' in f for f in result['proposal'].findings)
    assert store.commit(result['proposal']).systems[0].name=='Video Analytics System'
