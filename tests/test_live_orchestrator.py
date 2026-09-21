import json
import pytest
from pathlib import Path
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage
from apps.api.app.providers.config import Settings
from apps.api.app.orchestration.live import assisted_run
from apps.api.app.domain.commands import command
from apps.api.app.domain.commands import DomainError
from apps.api.app.domain.models import Project
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
