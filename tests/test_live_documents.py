import json
import pytest
from apps.api.app.domain.models import Project,Source,Passage
from apps.api.app.orchestration.documents import ingest_live,document_preflight
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage
from apps.api.app.storage.store import Store
from apps.api.app.domain.layout import bounds
from apps.api.app.domain.views import view_graph

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
    result=ingest_live(store,p.id,b'fixture','fixture.pdf','ollama',settings,adapter)
    assert store.get(p.id)==p
    accepted=store.commit(result['proposal'])
    assert len(accepted.components)==1 and all(c.review=='unreviewed' for c in accepted.claims)


def test_openai_document_without_zones_accepts_a_compact_layout(tmp_path,monkeypatch):
    """Scripted provider output reproduces the 20-component SSMS layout shape."""
    from types import SimpleNamespace as NS
    from apps.api.app.providers.adapters import OpenAIAdapter
    from apps.api.app.providers.structured import structured_envelope

    operations=[];claims=[];quotes=[]
    def add(entity,ident,value,quote):
        operations.append(dict(op='add',entity=entity,id=ident,value_json=json.dumps(value)))
        claims.append(dict(source_id='S1',locator='page/1',excerpt=quote,target_id=ident,
                           field='record',value_json='null'))
        quotes.append(quote)
    for i in range(20):
        add('components',f'tmp:c{i}',dict(name=f'Service {i}',role='application'),
            f'Service {i} is an application.')
    for i in range(22):
        a,b=i%20,(i+1 if i<20 else i+4)%20
        add('interfaces',f'tmp:e{i}',dict(source=f'tmp:c{a}',target=f'tmp:c{b}',purpose='events'),
            f'Service {a} sends events to Service {b}.')
    spec=Source(id='spec',name='Synthetic functional specification',kind='document',sha256='no-zones',
                canonical_id='no-zones',passages=[Passage(locator='page/1',text='\n'.join(quotes))])
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:spec)
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return NS(status='completed',model='gpt-5.4-mini',
                  usage=NS(input_tokens=100,output_tokens=100,input_tokens_details=NS(),output_tokens_details=NS()),
                  output_text=json.dumps(structured_envelope(Envelope(operations=operations,claims=claims,tool=None,message='Review'))))
    settings=Settings(allow_cloud=True,max_calls=1)
    adapter=OpenAIAdapter(settings,NS(responses=NS(create=create)))
    store=Store(tmp_path/'no-zones.sqlite');p=store.create(Project())
    result=ingest_live(store,p.id,b'synthetic','spec.pdf','openai',settings,adapter)
    assert len(calls)==1 and store.get(p.id)==p
    accepted=store.commit(result['proposal'])
    assert len(accepted.components)==20 and len(accepted.interfaces)==22
    assert not accepted.zones and not accepted.deployments
    assert len(accepted.claims)==42 and accepted.sources[0].processed==['page/1']
    for kind in ('logical','sv2'):
        nodes=view_graph(accepted,kind,route_edges=False)['nodes'];box=bounds(nodes)
        assert len({node['x'] for node in nodes})>1
        assert .75<=box['width']/box['height']<=2.5
        assert all(node['parentId'] is None for node in nodes)
    assert store.get(p.id)==accepted
