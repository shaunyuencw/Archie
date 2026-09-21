import json,time,threading
from types import SimpleNamespace as NS
import httpx,pytest
from apps.api.app.providers.adapters import OllamaAdapter,OpenAIAdapter,MockAdapter
from apps.api.app.providers.config import Settings
from apps.api.app.providers.budget import BudgetedProvider,usage_summary
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage,cost
from apps.api.app.domain.commands import DomainError
from apps.api.app.storage.store import Store

EMPTY={'operations':[],'claims':[],'tool':None,'message':'No supported facts'}

def test_openai_contract_transport():
    captured={}
    def create(**kwargs):
        captured.update(kwargs)
        return NS(status='completed',output_text=json.dumps(EMPTY),model='gpt-5.4-mini-2026-03-17',usage=NS(input_tokens=110,input_tokens_details=NS(cached_tokens=10),output_tokens=30,output_tokens_details=NS(reasoning_tokens=8)))
    result=OpenAIAdapter(Settings(),NS(responses=NS(create=create))).generate_structured('task',300,time.monotonic()+10)
    assert result.usage.input_tokens==100 and result.usage.cache_read_tokens==10
    assert captured['store'] is False and captured['reasoning']=={'effort':'none'} and 'temperature' not in captured
    assert captured['text']['format']['strict'] is True

def test_ollama_contract_and_no_fallback():
    captured=[]
    def handler(request):
        captured.append(json.loads(request.content));return httpx.Response(200,json={'done':True,'done_reason':'stop','model':'local','message':{'content':json.dumps(EMPTY)},'prompt_eval_count':50,'eval_count':20})
    a=OllamaAdapter(Settings(),httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(handler)))
    result=a.generate_structured('task',100,time.monotonic()+10)
    assert result.model=='local' and captured[0]['options']['num_ctx']==4096 and captured[0]['think'] is False
    assert len(captured)==1

def test_T11_malformed_truncation_and_refusal():
    for body in [{'done':False,'message':{'content':'{}'}},{'done':True,'message':{'content':'{"operations":'}}]:
        a=OllamaAdapter(Settings(),httpx.Client(base_url='http://localhost',transport=httpx.MockTransport(lambda r:httpx.Response(200,json=body))))
        with pytest.raises((DomainError,ValueError)):a.generate_structured('x',100,time.monotonic()+5)
    a=OpenAIAdapter(Settings(),NS(responses=NS(create=lambda **k:NS(status='incomplete',output_text=''))))
    with pytest.raises(DomainError):a.generate_structured('x',100,time.monotonic()+5)

def test_ollama_timeout_and_incomplete_output_have_actionable_messages(tmp_path):
    def timeout(request):raise httpx.ReadTimeout('slow local model',request=request)
    a=OllamaAdapter(Settings(),httpx.Client(base_url='http://localhost',transport=httpx.MockTransport(timeout)))
    with pytest.raises(DomainError) as error:a.generate_structured('x',100,time.monotonic()+7)
    assert error.value.code=='provider_timeout' and '7 seconds' in error.value.message and 'smaller section' in error.value.message
    a=OllamaAdapter(Settings(),httpx.Client(base_url='http://localhost',transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'done':True,'done_reason':'length','message':{'content':'{}'}}))))
    with pytest.raises(DomainError) as error:a.generate_structured('x',100,time.monotonic()+7)
    assert error.value.code=='provider_output' and 'response limit' in error.value.message
    store=Store(tmp_path/'db')
    with pytest.raises(DomainError,match='local response window'):
        BudgetedProvider(store,Settings(),OllamaAdapter(Settings(),httpx.Client(base_url='http://localhost',transport=httpx.MockTransport(timeout)))).call('x','p','timeout')
    assert usage_summary(store,'p')['records'][0]['details']=={'error_code':'provider_timeout'}

def test_ollama_http_404_is_rejected_before_generation(tmp_path):
    def missing(request):return httpx.Response(404,request=request,json={'error':'model not found'})
    store=Store(tmp_path/'db');adapter=OllamaAdapter(Settings(),httpx.Client(base_url='http://localhost',transport=httpx.MockTransport(missing)))
    with pytest.raises(DomainError,match='HTTP 404'):
        BudgetedProvider(store,Settings(),adapter).call('x','p','missing')
    assert usage_summary(store,'p')['records'][0]['status']=='rejected_before_generation'

class CapturingLocal:
    name='ollama';model='mocked-local'
    def __init__(self):self.deadlines=[];self.max_outputs=[]
    def generate_structured(self,prompt,max_output,deadline,cancel=None):
        self.deadlines.append(deadline);self.max_outputs.append(max_output)
        return ProviderResult(model=self.model,finish_status='completed',usage=Usage(),content=Envelope.model_validate(EMPTY))

def test_local_default_deadline_scales_to_capped_output_and_explicit_deadline_is_preserved(tmp_path):
    adapter=CapturingLocal();store=Store(tmp_path/'db');settings=Settings(ollama_num_ctx=8192,max_output=6000)
    started=time.monotonic();BudgetedProvider(store,settings,adapter).call('x','p','first')
    remaining=adapter.deadlines[-1]-started
    assert adapter.max_outputs[-1]==1536 and 200<=remaining<=210
    explicit=time.monotonic()+7
    BudgetedProvider(store,settings,adapter).call('x','p','second',deadline=explicit)
    assert adapter.deadlines[-1]==explicit

class Fake:
    name='openai';model='gpt-5.4-mini'
    def generate_structured(self,*args):
        raise httpx.ReadTimeout('ambiguous timeout')

def test_T12_reservations_restarts_and_call_limits(tmp_path):
    db=tmp_path/'db';store=Store(db);settings=Settings(allow_cloud=True,action_usd=.02,day_usd=.03,project_usd=.04)
    b=BudgetedProvider(store,settings,Fake())
    with pytest.raises(DomainError):b.call('x','p','a')
    spent=usage_summary(store,'p');assert spent['total']>0 and spent['records'][0]['status']=='unresolved'
    with pytest.raises(DomainError):BudgetedProvider(Store(db),settings,Fake()).call('x','p','a')
    assert usage_summary(Store(db),'p')['calls']==1
    with pytest.raises(DomainError):BudgetedProvider(store,Settings(),Fake()).call('x','p','b')
    assert usage_summary(store,'p')['calls']==1

def test_atomic_concurrent_reservation(tmp_path):
    store=Store(tmp_path/'db');b=BudgetedProvider(store,Settings(allow_cloud=True,action_usd=.02),Fake()); errors=[]
    def call():
        try:b.call('x','p','a')
        except DomainError as e:errors.append(e.code)
    ts=[threading.Thread(target=call) for _ in range(2)]
    for t in ts:t.start()
    for t in ts:t.join()
    assert usage_summary(store,'p')['calls']==1
    assert 'budget_exceeded' in errors

def test_cost_reasoning_subset_not_double_counted():
    assert cost(Usage(input_tokens=5000,output_tokens=2000,reasoning_tokens=500),{'input':.75,'cache_read':.075,'cache_write':.75,'output':4.5})==.01275

def test_requested_development_ceilings_leave_safe_defaults():
    configured=Settings(max_input=32000,max_output=6000,max_calls=6)
    assert configured.max_input==32000 and configured.max_output==6000
    assert Settings().provider=='mock' and not Settings().allow_cloud
    for overrides in [{'max_input':32001},{'max_output':6001}]:
        with pytest.raises(ValueError):Settings(**overrides)
