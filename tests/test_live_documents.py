import json
import pytest
from apps.api.app.domain.models import Project,Source,Passage
from apps.api.app.orchestration.documents import ingest_live,document_preflight
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage
from apps.api.app.storage.store import Store

class DocumentAdapter:
    name='ollama';model='mocked-document'
    def __init__(self,bad=False):self.calls=0;self.bad=bad
    def generate_structured(self,prompt,*args):
        self.calls+=1;p=json.loads(prompt)['source']['passages'][0];ident='tmp:node-'+str(self.calls)
        return ProviderResult(model=self.model,finish_status='completed',usage=Usage(input_tokens=100,output_tokens=100),content=Envelope.model_validate({'operations':[{'op':'add','entity':'components','id':ident,'value_json':json.dumps({'name':'Station '+str(self.calls),'role':'workstation'})}],'claims':[{'source_id':'S1','locator':p['locator'],'excerpt':'fabricated excerpt' if self.bad else p['text'][:30],'target_id':ident,'field':'record','value_json':'"Station"'}],'tool':None,'message':'Review'}))

def source():
    return Source(id='source',name='Synthetic document',kind='document',sha256='test',canonical_id='test',passages=[Passage(locator=f'page/{i}',text=('Synthetic station '+str(i)+' ')*35) for i in range(1,4)])

def test_bounded_document_preview_and_explicit_continuation(tmp_path,monkeypatch):
    store=Store(tmp_path/'db');p=store.create(Project());settings=Settings(max_calls=1);adapter=DocumentAdapter()
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:source())
    result=ingest_live(store,p.id,b'fixture','fixture.pdf','ollama',settings,adapter)
    assert adapter.calls==1 and not store.get(p.id).sources
    accepted=store.commit(result['proposal'])
    assert len(accepted.sources[0].processed)==1 and len(accepted.sources[0].unprocessed)==2
    second=ingest_live(store,p.id,b'','','ollama',settings,adapter,source_id='source')
    assert len(store.get(p.id).components)==1
    accepted=store.commit(second['proposal'])
    assert len(accepted.components)==2 and len(accepted.sources)==1
    assert len(accepted.sources[0].processed)==2 and len(accepted.sources[0].unprocessed)==1
    assert all(c.source_id=='source' for c in accepted.claims)

def test_document_failure_preserves_accepted_state_and_preflight_is_local(tmp_path,monkeypatch):
    store=Store(tmp_path/'db');p=store.create(Project());settings=Settings(max_calls=1);adapter=DocumentAdapter(bad=True)
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:source())
    _,groups,remainder=document_preflight(source(),'ollama',settings)
    assert len(groups)==1 and len(remainder)==2 and adapter.calls==0
    with pytest.raises(Exception):ingest_live(store,p.id,b'fixture','fixture.pdf','ollama',settings,adapter)
    assert store.get(p.id)==p
