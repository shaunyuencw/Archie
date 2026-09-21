import json
import httpx
import pytest
from pathlib import Path
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage
from apps.api.app.providers.config import Settings
from apps.api.app.providers.adapters import OllamaAdapter
from apps.api.app.providers.budget import usage_summary
from apps.api.app.orchestration.live import assisted_run,proposal_from_envelope
from apps.api.app.domain.commands import apply,command
from apps.api.app.domain.commands import DomainError
from apps.api.app.domain.models import Component,Passage,Project,Source
from apps.api.app.storage.store import Store
from apps.api.app.main import RunRequest

class FakeOllama:
    name='ollama';model='mocked-local'
    def generate_structured(self,prompt,*args):
        text=json.loads(prompt)['source']['text']
        return ProviderResult(model=self.model,finish_status='completed',usage=Usage(input_tokens=100,output_tokens=100),content=Envelope.model_validate({'operations':[{'op':'add','entity':'components','id':'tmp:new','value_json':'{"name":"New node","role":"workstation","asset_id":"workstation"}'}],'claims':[{'source_id':'S1','locator':'prompt/1','excerpt':text,'target_id':'tmp:new','field':'record','value_json':'"New node"'}],'tool':None,'message':'Review'}))

class UnsupportedScopeAdapter(FakeOllama):
    def generate_structured(self,prompt,*args):
        result=super().generate_structured(prompt,*args)
        value=json.loads(result.content.operations[0].value_json);value['scope']='internal'
        result.content.operations[0].value_json=json.dumps(value)
        return result

def test_live_orchestration_only_previews_until_accepted(tmp_path):
    s=Store(tmp_path/'db');p=s.create(Project());c=command(p,[{'op':'notes','value':{}}]);req=RunRequest(**c.model_dump(),prompt='Add New node workstation.',provider='ollama')
    result=assisted_run(s,p.id,req,Settings(),FakeOllama())
    assert not s.get(p.id).components
    accepted=s.commit(s.change(result['proposal']['id']))
    assert accepted.components[0].name=='New node' and accepted.claims[0].source_id==accepted.sources[0].id
    assert accepted.components[0].scope=='unknown'

def test_provider_scope_without_matching_claim_stays_unknown(tmp_path):
    store=Store(tmp_path/'db');p=store.create(Project());c=command(p,[{'op':'notes','value':{}}])
    req=RunRequest(**c.model_dump(),prompt='Add New node workstation.',provider='ollama')
    result=assisted_run(store,p.id,req,Settings(),UnsupportedScopeAdapter())
    assert result['proposal']['findings']
    accepted=store.commit(store.change(result['proposal']['id']))
    assert accepted.components[0].scope=='unknown'

def test_live_journey_ceiling_spans_separate_actions_and_projects(tmp_path):
    store=Store(tmp_path/'db');settings=Settings();adapter=FakeOllama()
    limit={'id':'bounded-journey','max_calls':1,'budget_usd':.5}
    for index in range(2):
        p=store.create(Project());c=command(p,[{'op':'notes','value':{}}],request_id=f'bounded-journey-{index}')
        req=RunRequest(**c.model_dump(),prompt='Add New node workstation.',provider='ollama')
        if index==0:assisted_run(store,p.id,req,settings,adapter,live_run=limit)
        else:
            with pytest.raises(DomainError,match='Live smoke run ceiling'):
                assisted_run(store,p.id,req,settings,adapter,live_run=limit)
        assert not store.get(p.id).components

def test_document_port_text_is_normalized_without_choosing_ambiguous_ports():
    project=Project(components=[
        Component(id='web',name='Web service',role='application'),
        Component(id='database',name='Database',role='database'),
    ])
    source=Source(id='document-source',name='Spec',kind='document',sha256='source',canonical_id='source',passages=[
        Passage(locator='paragraph/1',text='HTTPS uses TCP 443. PostgreSQL uses TCP 5432.'),
    ])
    def claim(target):
        return {'source_id':'S1','locator':'paragraph/1','excerpt':'HTTPS uses TCP 443. PostgreSQL uses TCP 5432.','target_id':target,'field':'record','value_json':'null'}
    envelope=Envelope(operations=[
        {'op':'add','entity':'interfaces','id':'web-db','value_json':json.dumps({'source':'web','target':'database','protocol':'HTTPS','port':'TCP 443'})},
        {'op':'add','entity':'interfaces','id':'db-web','value_json':json.dumps({'source':'database','target':'web','protocol':'PostgreSQL','port':'TCP 5432'})},
        {'op':'add','entity':'interfaces','id':'ambiguous','value_json':json.dumps({'source':'web','target':'database','protocol':'HTTPS','port':'TCP 443 or 8443'})},
    ],claims=[claim('web-db'),claim('db-web'),claim('ambiguous')],tool=None,message='Review')
    proposal=proposal_from_envelope(project,source,envelope,source_alias='S1')
    accepted=apply(project,proposal)
    assert {item.id:item.port for item in accepted.interfaces}=={'web-db':443,'db-web':5432,'ambiguous':None}
    assert proposal.findings==['ambiguous: port was left unknown because the supplied value was not one valid numeric port. Split the connection or provide one port.']

def test_timed_out_local_run_is_not_replayed(tmp_path):
    class TimedOutAdapter(FakeOllama):
        calls=0
        def generate_structured(self,*args):
            self.calls+=1
            raise DomainError('provider_timeout','Ollama did not finish within the local response window.',504)
    store=Store(tmp_path/'db');project=store.create(Project());adapter=TimedOutAdapter()
    req=RunRequest(**command(project,[{'op':'notes','value':{}}]).model_dump(),prompt='Add a workstation.',provider='ollama')
    with pytest.raises(DomainError) as error:
        assisted_run(store,project.id,req,Settings(),adapter)
    assert error.value.code=='provider_timeout' and adapter.calls==1
    assert store.get(project.id)==project
    with store.connect() as db:
        run=db.execute('SELECT status,result FROM runs WHERE id=?',(req.request_id,)).fetchone()
    assert run['status']=='failed' and json.loads(run['result'])['code']=='provider_timeout'


def test_ollama_response_limit_is_not_repaired_or_replayed(tmp_path):
    calls=[]
    def length(request):
        calls.append(request)
        return httpx.Response(200,json={'done':True,'done_reason':'length','model':'local','message':{'content':'{}'},'prompt_eval_count':615,'eval_count':1536})
    store=Store(tmp_path/'db');project=store.create(Project())
    request=RunRequest(**command(project,[{'op':'notes','value':{}}]).model_dump(),prompt='Add a workstation.',provider='ollama')
    adapter=OllamaAdapter(Settings(),httpx.Client(base_url='http://localhost',transport=httpx.MockTransport(length)))
    with pytest.raises(DomainError,match='response limit'):
        assisted_run(store,project.id,request,Settings(),adapter)
    assert len(calls)==1 and store.get(project.id)==project
    assert usage_summary(store,project.id)['records'][0]['status']=='truncated'
    with store.connect() as db:run=db.execute('SELECT status,result FROM runs WHERE id=?',(request.request_id,)).fetchone()
    assert run['status']=='failed' and json.loads(run['result'])['code']=='provider_output'


def test_background_stale_preview_is_terminal_and_preserves_the_manual_edit(tmp_path):
    store=Store(tmp_path/'db');project=store.create(Project())
    class ConcurrentEditAdapter(FakeOllama):
        def __init__(self):self.calls=0
        def generate_structured(self,*args):
            self.calls+=1
            current=store.get(project.id)
            store.commit(command(current,[{'op':'notes','value':{'text':'Manual edit while ARCHIE was working'}}]))
            return super().generate_structured(*args)
    adapter=ConcurrentEditAdapter()
    request=RunRequest(**command(project,[{'op':'notes','value':{}}]).model_dump(),prompt='Add New node workstation.',provider='ollama')
    with pytest.raises(DomainError) as error:
        assisted_run(store,project.id,request,Settings(),adapter)
    assert error.value.code=='stale_revision' and adapter.calls==1
    assert store.get(project.id).notes=='Manual edit while ARCHIE was working' and not store.get(project.id).components
