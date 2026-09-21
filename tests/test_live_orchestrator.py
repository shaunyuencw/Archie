import json
from pathlib import Path
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage
from apps.api.app.providers.config import Settings
from apps.api.app.orchestration.live import assisted_run
from apps.api.app.domain.commands import command
from apps.api.app.domain.models import Project
from apps.api.app.storage.store import Store
from apps.api.app.main import RunRequest

class FakeOllama:
    name='ollama';model='mocked-local'
    def generate_structured(self,prompt,*args):
        text=json.loads(prompt)['source']['text']
        return ProviderResult(model=self.model,finish_status='completed',usage=Usage(input_tokens=100,output_tokens=100),content=Envelope.model_validate({'operations':[{'op':'add','entity':'components','id':'tmp:new','value_json':'{"name":"New node","role":"workstation","asset_id":"workstation"}'}],'claims':[{'source_id':'S1','locator':'prompt/1','excerpt':text,'target_id':'tmp:new','field':'record','value_json':'"New node"'}],'tool':None,'message':'Review'}))

def test_live_orchestration_only_previews_until_accepted(tmp_path):
    s=Store(tmp_path/'db');p=s.create(Project());c=command(p,[{'op':'notes','value':{}}]);req=RunRequest(**c.model_dump(),prompt='Add New node workstation.',provider='ollama')
    result=assisted_run(s,p.id,req,Settings(),FakeOllama())
    assert not s.get(p.id).components
    accepted=s.commit(s.change(result['proposal']['id']))
    assert accepted.components[0].name=='New node' and accepted.claims[0].source_id==accepted.sources[0].id
