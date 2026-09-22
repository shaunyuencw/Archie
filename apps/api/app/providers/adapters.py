import json,os,time,threading,math
import httpx
from openai import OpenAI
from .contracts import Envelope,ProviderResult,Usage,schema,ToolRequest
from ..domain.commands import DomainError
from .instructions import SYSTEM_PROMPT
from .structured import STRUCTURED_SYSTEM_PROMPT,structured_schema,parse_structured

class OpenAIAdapter:
    name='openai'
    system_prompt=STRUCTURED_SYSTEM_PROMPT
    response_schema=staticmethod(structured_schema)
    def __init__(self,settings,client=None):
        self.model=settings.openai_model
        self.client=client or OpenAI(api_key=os.getenv('OPENAI_API_KEY'),max_retries=0)
    def capabilities(self):return {'structured':True,'native_tools':'implemented, live unverified','mode':'schema_action_envelope'}
    def generate_structured(self,prompt,max_output,deadline,cancel=None):
        if cancel and cancel.is_set(): raise DomainError('cancelled','Cancelled before transmission')
        started=time.monotonic()
        r=self.client.responses.create(model=self.model,input=[{'role':'system','content':self.system_prompt},{'role':'user','content':prompt}],text={'format':{'type':'json_schema','name':'architecture_action','schema':self.response_schema(),'strict':True}},max_output_tokens=max_output,store=False,timeout=max(.1,deadline-time.monotonic()),**({'reasoning':{'effort':'none'}} if self.model.startswith(('gpt-5.4-mini','gpt-5.6-terra')) else {}))
        if r.status!='completed' or not r.output_text: raise DomainError('provider_output','Provider refused or truncated its response')
        u=r.usage; cached=getattr(u.input_tokens_details,'cached_tokens',0) or 0
        writes=getattr(u.input_tokens_details,'cache_write_tokens',0) or getattr(u.input_tokens_details,'cache_creation_tokens',0) or 0
        usage=Usage(input_tokens=max(0,u.input_tokens-cached-writes),cache_read_tokens=cached,cache_write_tokens=writes,output_tokens=u.output_tokens,reasoning_tokens=getattr(u.output_tokens_details,'reasoning_tokens',0) or 0,latency_ms=(time.monotonic()-started)*1000)
        try:content=parse_structured(r.output_text)
        except ValueError as cause:
            error=DomainError('provider_output','OpenAI returned an invalid structured draft. No changes were applied.')
            error.usage=usage;error.model=r.model;error.usage_status='invalid_output';error.finish_reason='invalid_schema';error.terminal=True
            raise error from cause
        return ProviderResult(content=content,finish_status='completed',model=r.model,usage=usage)
    def invoke_tools(self,prompt,max_output,deadline,cancel=None):
        # Explicit capability probe uses a native function; runtime defaults to labelled envelopes.
        started=time.monotonic()
        if cancel and cancel.is_set(): raise DomainError('cancelled','Cancelled before transmission')
        r=self.client.responses.create(model=self.model,input=prompt,tools=[{'type':'function','name':'architecture_context','description':'Request read-only curated context','parameters':ToolRequest.model_json_schema(),'strict':True}],tool_choice='required',max_output_tokens=max_output,store=False,timeout=max(.1,deadline-time.monotonic()))
        calls=[x for x in r.output if x.type=='function_call' and x.name=='architecture_context']
        if r.status!='completed' or len(calls)!=1: raise DomainError('provider_output','Expected one allowlisted tool request')
        tool=ToolRequest.model_validate_json(calls[0].arguments)
        return ProviderResult(content=Envelope(operations=[],claims=[],tool=tool,message='Native tool probe'),finish_status='completed',model=r.model,usage=Usage(input_tokens=r.usage.input_tokens,output_tokens=r.usage.output_tokens,latency_ms=(time.monotonic()-started)*1000))

class OllamaAdapter:
    name='ollama'
    def __init__(self,settings,client=None):
        self.model=settings.ollama_model; self.settings=settings
        self.client=client or httpx.Client(base_url=settings.ollama_base_url,trust_env=False)
    def capabilities(self):return {'structured':True,'native_tools':'implemented, model unverified','mode':'schema_action_envelope'}
    def _request(self,prompt,max_output,deadline,cancel,tools=False):
        if cancel and cancel.is_set(): raise DomainError('cancelled','Cancelled before transmission')
        started=time.monotonic()
        payload={'model':self.model,'messages':[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':prompt}],'stream':False,'think':False,'options':{'num_ctx':self.settings.ollama_num_ctx,'num_predict':max_output,'temperature':0}}
        if tools:payload['tools']=[{'type':'function','function':{'name':'architecture_context','description':'Request read-only context','parameters':ToolRequest.model_json_schema()}}]
        else:payload['format']=schema()
        remaining=deadline-time.monotonic()
        if remaining<=0: raise DomainError('provider_timeout','Ollama response deadline passed before transmission. Your accepted architecture was preserved.',504)
        try:
            r=self.client.post('/api/chat',json=payload,timeout=remaining); r.raise_for_status(); body=r.json()
        except httpx.TimeoutException as e:
            seconds=max(1,math.ceil(remaining))
            raise DomainError('provider_timeout',f'Ollama did not finish within the local response window ({seconds} seconds). Your accepted architecture was preserved. Retry with a smaller section or a faster local model.',504) from e
        except httpx.HTTPStatusError as e:
            status=e.response.status_code
            error=DomainError('unavailable_provider',f'Ollama returned HTTP {status}. Check that Ollama and the selected local model are available, then retry. Your accepted architecture was preserved.',503)
            error.status_code=status
            raise error from e
        except (TypeError,ValueError) as e:
            raise DomainError('provider_output','Ollama returned a response that was not valid JSON. Your accepted architecture was preserved.') from e
        if not isinstance(body,dict): raise DomainError('provider_output','Ollama returned a response that did not match the required architecture format. Your accepted architecture was preserved.')
        if body.get('done_reason')=='length':
            error=DomainError('provider_output','Ollama reached its local response limit before completing a valid proposal. Your accepted architecture was preserved. Retry with a smaller section or a model that can return a shorter response.')
            # The partial JSON is never persisted, but Ollama's counters make
            # this known truncation observable instead of an unresolved call.
            error.usage=Usage(input_tokens=body.get('prompt_eval_count',0) or 0,output_tokens=body.get('eval_count',0) or 0,latency_ms=(time.monotonic()-started)*1000)
            error.model=body.get('model',self.model)
            error.terminal=True
            raise error
        if not body.get('done'): raise DomainError('provider_output','Ollama returned an incomplete response. Your accepted architecture was preserved.')
        try:
            if tools:
                calls=body.get('message',{}).get('tool_calls',[])
                if len(calls)!=1 or calls[0]['function']['name']!='architecture_context': raise DomainError('provider_output','Ollama returned an unexpected context request. Your accepted architecture was preserved.')
                content=Envelope(operations=[],claims=[],tool=ToolRequest.model_validate(calls[0]['function']['arguments']),message='Native tool probe')
            else:content=Envelope.model_validate_json(body['message']['content'])
        except (KeyError,TypeError,ValueError) as e:
            raise DomainError('provider_output','Ollama returned a response that did not match the required architecture format. Your accepted architecture was preserved.') from e
        return ProviderResult(content=content,finish_status='completed',model=body.get('model',self.model),usage=Usage(input_tokens=body.get('prompt_eval_count',0),output_tokens=body.get('eval_count',0),latency_ms=(time.monotonic()-started)*1000))
    def generate_structured(self,prompt,max_output,deadline,cancel=None):return self._request(prompt,max_output,deadline,cancel)
    def invoke_tools(self,prompt,max_output,deadline,cancel=None):return self._request(prompt,max_output,deadline,cancel,True)

class MockAdapter:
    name='mock';model='deterministic-1'
    def capabilities(self):return {'structured':True,'native_tools':False,'mode':'deterministic_mock'}
    def generate_structured(self,prompt,max_output,deadline,cancel=None):return ProviderResult(content=Envelope(operations=[],claims=[],tool=None,message='Use local deterministic fixture parser'),finish_status='completed',model=self.model,usage=Usage())
    def invoke_tools(self,*args,**kwargs):return self.generate_structured(*args,**kwargs)
