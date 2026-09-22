"""Exercise the actual OpenAI boundary with mocked transport, never paid calls."""
import json
from types import SimpleNamespace as NS

import pytest

from apps.api.app.domain.commands import DomainError, command
from apps.api.app.domain.models import Component, Project, Source, Passage
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.orchestration.live import assisted_run
from apps.api.app.providers.adapters import OpenAIAdapter
from apps.api.app.providers.budget import BudgetedProvider, usage_summary
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope, estimate
from apps.api.app.providers.structured import parse_structured, structured_schema, structured_envelope
from apps.api.app.storage.store import Store


def wire(operations=(),claims=()):
    return {'operations':list(operations),'claims':list(claims),'tool':None,'message':'Review the draft','project_name':None}


def op(entity,ident,fields,operation='add'):
    return {'op':operation,'entity':entity,'id':ident,'proposal_reason':None,
            'value':{'fields':[{'key':key,'value':value} for key,value in fields.items()]}}


def client_for(body,calls):
    def create(**kwargs):
        calls.append(kwargs)
        return NS(status='completed',output_text=json.dumps(body),model='gpt-5.6-terra',
                  usage=NS(input_tokens=100,output_tokens=80,input_tokens_details=NS(),output_tokens_details=NS()))
    return NS(responses=NS(create=create))


def test_schema_closes_every_object_and_has_no_embedded_json_fields():
    schema=structured_schema()
    def check(node):
        if isinstance(node,dict):
            if node.get('type')=='object':
                assert node['additionalProperties'] is False
                assert set(node['required'])==set(node['properties'])
                assert 'value_json' not in node['properties']
            assert 'default' not in node
            if '$ref' in node:
                assert node['$ref'].startswith('#/$defs/')
                assert node['$ref'].split('/')[-1] in schema['$defs']
            for value in node.values():check(value)
        elif isinstance(node,list):
            for value in node:check(value)
    check(schema)


@pytest.mark.parametrize('value',[None,False,True,0,3.25,'Operator "A"\nDAS’s path \\rack',
    {'rules':[{'ports':[443,None],'enabled':False},[],{}],'literal':'{"bad JSON":,}'},['one',2,None,False]])
def test_nested_values_round_trip_without_changing_types_or_content(value):
    envelope=Envelope(operations=[dict(op='add',entity='constraints',id='rule',
        value_json=json.dumps({'key':'source requirement','value':value}))],
        claims=[dict(source_id='S1',locator='page/1',excerpt='Requirement',target_id='rule',field='value',value_json=json.dumps(value))],
        tool=None,message='Review')
    decoded=parse_structured(json.dumps(structured_envelope(envelope)))
    assert json.loads(decoded.operations[0].value_json)==json.loads(envelope.operations[0].value_json)
    claim=json.loads(decoded.claims[0].value_json)
    assert claim==value and type(claim) is type(value)


def test_document_with_quotes_zones_and_connections_accepts_without_repair(tmp_path,monkeypatch):
    quote='Operator "A" connects to the application in the Protected zone on port 443. Require segmentation.'
    spec=Source(id='spec',name='Synthetic SSMS regression',kind='document',sha256='synthetic',canonical_id='synthetic',
                passages=[Passage(locator='page/1',text=quote)])
    operations=[op('components','tmp:client',{'name':'Operator "A"','role':'client'}),
                op('components','tmp:app',{'name':'Application','role':'application'}),
                op('zones','tmp:z',{'name':'Protected zone'}),
                op('deployments','tmp:d',{'component_id':'tmp:app','zone_id':'tmp:z'}),
                op('interfaces','tmp:link',{'source':'tmp:client','target':'tmp:app','port':443,'enforcement':[]})]
    claims=[dict(source_id='S1',locator='page/1',excerpt=quote,target_id=o['id'],field='record',value=None) for o in operations]
    calls=[];settings=Settings(allow_cloud=True,max_input=50000,max_output=6000,max_calls=1)
    adapter=OpenAIAdapter(settings,client_for(wire(operations,claims),calls))
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:spec)
    store=Store(tmp_path/'document.sqlite');project=store.create(Project())
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',settings,adapter)
    assert len(calls)==1 and result['repairs']==0 and store.get(project.id)==project
    assert calls[0]['text']['format']['schema']==structured_schema()
    assert 'value_json is a JSON object string' not in calls[0]['input'][0]['content']
    accepted=store.commit(result['proposal'])
    assert accepted.components[0].name=='Operator "A"'
    assert len(accepted.zones)==len(accepted.deployments)==len(accepted.interfaces)==1
    assert accepted.deployments[0].zone_id==accepted.zones[0].id
    assert accepted.interfaces[0].port==443 and accepted.interfaces[0].enforcement==[]
    assert all(c.excerpt==quote for c in accepted.claims)


def test_sparse_edit_preserves_omitted_fields_and_applies_explicit_null(tmp_path):
    store=Store(tmp_path/'edit.sqlite')
    project=store.create(Project(components=[Component(id='app',name='Old',role='application',local_only=True,internet_hosted=False)]))
    prompt='Rename the application to Operator "A" and clear whether it is local only.'
    body=wire([op('components','app',{'name':'Operator "A"','local_only':None},'update')],
              [dict(source_id='S1',locator='prompt/1',excerpt=prompt,target_id='app',field='record',value=None)])
    calls=[];settings=Settings(allow_cloud=True,max_input=50000)
    from apps.api.app.main import RunRequest
    request=RunRequest(**command(project,[{'op':'notes','value':{}}]).model_dump(),prompt=prompt,provider='openai')
    result=assisted_run(store,project.id,request,settings,OpenAIAdapter(settings,client_for(body,calls)))
    assert len(calls)==1 and result['repairs']==0
    accepted=store.commit(store.change(result['proposal']['id']))
    assert accepted.components[0].name=='Operator "A"'
    assert accepted.components[0].local_only is None
    assert accepted.components[0].internet_hosted is False and accepted.components[0].role=='application'


@pytest.mark.parametrize('bad_value',['{"name":"Broken",}',{'fields':[{'key':'name','value':'A'},{'key':'name','value':'B'}]}])
def test_malformed_or_duplicate_payload_fails_readably_and_keeps_usage(tmp_path,bad_value):
    operation=op('components','app',{'name':'A','role':'application'});operation['value']=bad_value
    body=wire([operation]);calls=[];settings=Settings(allow_cloud=True)
    store=Store(tmp_path/'invalid.sqlite');project=store.create(Project())
    with pytest.raises(DomainError,match='invalid structured draft'):
        BudgetedProvider(store,settings,OpenAIAdapter(settings,client_for(body,calls))).call('draft',project.id,'invalid')
    assert len(calls)==1 and store.get(project.id)==project
    record=usage_summary(store,project.id)['records'][0]
    assert record['status']=='invalid_output' and record['cost']>0
    assert record['details']['output_tokens']==80 and record['details']['finish_reason']=='invalid_schema'


def test_input_guard_accounts_for_actual_openai_schema_and_prompt(tmp_path):
    calls=[];settings=Settings(allow_cloud=True,max_input=50000,max_output=6000,document_usd=1)
    adapter=OpenAIAdapter(settings,client_for(wire(),calls))
    overhead=estimate(adapter.system_prompt+json.dumps(adapter.response_schema(),separators=(',',':')))+128
    store=Store(tmp_path/'budget.sqlite');budget=BudgetedProvider(store,settings,adapter)
    budget.call('x'*(50000-overhead),'p','fits',task='document')
    with pytest.raises(DomainError,match='50001 tokens exceeds 50000'):
        budget.call('x'*(50001-overhead),'p','too-large',task='document')
    assert len(calls)==1 and usage_summary(store,'p')['calls']==1
