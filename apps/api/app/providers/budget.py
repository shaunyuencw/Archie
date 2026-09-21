import json,time,threading
from datetime import datetime,timezone
from .contracts import Usage,cost,estimate,schema
from .config import pricing
from ..domain.models import uid
from ..domain.commands import DomainError
from .instructions import SYSTEM_PROMPT

LOCAL_LOCK=threading.Lock()
LOCAL_MIN_TOKENS_PER_SECOND=8
LOCAL_STARTUP_SECONDS=15
LOCAL_TIMEOUT_CAP_SECONDS=480
LOCAL_CONTEXT_RESERVE_TOKENS=512
LOCAL_MIN_OUTPUT_TOKENS=512

def local_limits(settings,token_bound):
    """Keep local input, output and reserve inside the chosen Ollama context."""
    context=settings.ollama_num_ctx
    if context<=4096:
        max_input=min(settings.max_input,2500)
        max_output=min(settings.max_output,1024)
    else:
        # The former fixed 1,536 output cap left ample unused 8k context for
        # ordinary three-tier proposals. Bound output by this request's actual
        # conservative input estimate instead of silently truncating it.
        max_input=min(settings.max_input,5500,context-LOCAL_CONTEXT_RESERVE_TOKENS-LOCAL_MIN_OUTPUT_TOKENS)
        context_output=max(0,context-token_bound-LOCAL_CONTEXT_RESERVE_TOKENS)
        time_output=max(0,(LOCAL_TIMEOUT_CAP_SECONDS-LOCAL_STARTUP_SECONDS)*LOCAL_MIN_TOKENS_PER_SECOND)
        max_output=min(settings.max_output,context_output,time_output)
    return max_input,max_output

def default_deadline(adapter_name,max_output):
    """Use a bounded local window sized for the response the app requested.

    Local models run serially and can be substantially slower than the API.
    Explicit caller deadlines are handled by ``call`` unchanged.
    """
    seconds=90
    if adapter_name=='ollama':
        seconds=min(LOCAL_TIMEOUT_CAP_SECONDS,max(seconds,LOCAL_STARTUP_SECONDS+(max_output+LOCAL_MIN_TOKENS_PER_SECOND-1)//LOCAL_MIN_TOKENS_PER_SECOND))
    return time.monotonic()+seconds

class BudgetedProvider:
    """Only runtime entry to adapters. Persist reservations before transmission."""
    def __init__(self,store,settings,adapter):self.store=store;self.settings=settings;self.adapter=adapter
    def call(self,prompt,project_id,action_id,task='edit',cancel=None,deadline=None,native=False,live_run=None):
        s=self.settings;a=self.adapter;day=datetime.now(timezone.utc).date().isoformat()
        if a.name=='openai' and not s.allow_cloud: raise DomainError('budget_exceeded','Cloud is disabled. Enable APP_ALLOW_CLOUD explicitly.')
        rates=pricing()['models'].get(a.model) if a.name=='openai' else None
        if a.name=='openai' and rates is None: raise DomainError('budget_exceeded','Unknown billing model price; configure it before a paid request.')
        local=a.name=='ollama'
        byte_bound=estimate(SYSTEM_PROMPT+prompt+json.dumps(schema(),separators=(',',':')))+128
        # Local tokenizer is model-specific. Estimate 2 UTF-8 bytes/token and reserve context for response framing.
        token_bound=(byte_bound+1)//2 if local else byte_bound
        max_input,max_output=local_limits(s,token_bound) if local else (s.max_input,s.max_output)
        if token_bound>max_input: raise DomainError('insufficient_context',f'Request estimate {token_bound} tokens exceeds {max_input}; select fewer sources/objects. Nothing was sent.')
        if local and max_output<LOCAL_MIN_OUTPUT_TOKENS:
            raise DomainError('insufficient_context','This local request leaves too little context for a complete proposal. Select fewer sources or objects; nothing was sent.')
        reserve=(token_bound*max(rates['input'],rates['cache_read'],rates['cache_write'])+max_output*rates['output'])/1_000_000 if rates else 0
        ident=uid(); call_limit=min(s.max_calls,3 if task=='edit' else 8 if task=='document' else 4)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            def total(where,args): return db.execute('SELECT COALESCE(SUM(COALESCE(cost,reserved)),0) FROM usage WHERE '+where,args).fetchone()[0]
            count=db.execute('SELECT count(*) FROM usage WHERE action_id=?',(action_id,)).fetchone()[0]
            limits=[(total('action_id=?',(action_id,)),s.document_usd if task=='document' else s.action_usd),(total('day=?',(day,)),s.day_usd),(total('project_id=?',(project_id,)),s.project_usd)]
            if count>=call_limit or any(value+reserve>limit+1e-12 for value,limit in limits):raise DomainError('budget_exceeded','Call or spending reservation limit reached.')
            if live_run:
                row=db.execute('SELECT count(*),COALESCE(SUM(COALESCE(cost,reserved)),0) FROM usage WHERE action_id LIKE ?',(live_run['id']+'%',)).fetchone()
                if row[0]>=min(10,live_run['max_calls']) or row[1]+reserve>min(.5,live_run['budget_usd']):raise DomainError('budget_exceeded','Live smoke run ceiling reached.')
            db.execute('INSERT INTO usage VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,project_id,action_id,day,a.name,a.model,'reserved',reserve,None,'{}'))
        def cancelled_before_send():
            with self.store.connect() as db:
                db.execute("UPDATE usage SET status='cancelled_before_send',cost=0 WHERE id=? AND status='reserved'",(ident,))
            raise DomainError('cancelled','Cancelled before transmission')
        try:
            if cancel and cancel.is_set():
                cancelled_before_send()
            fn=a.invoke_tools if native else a.generate_structured
            # An explicit deadline is an upper bound owned by the caller.  Start a
            # default local window only after the serial local-model lock is held.
            if local:
                while not LOCAL_LOCK.acquire(timeout=.05):
                    if cancel and cancel.is_set():
                        cancelled_before_send()
                try:
                    if cancel and cancel.is_set():
                        cancelled_before_send()
                    request_deadline=deadline if deadline is not None else default_deadline(a.name,max_output)
                    result=fn(prompt,max_output,request_deadline,cancel)
                finally:
                    LOCAL_LOCK.release()
            else:
                if cancel and cancel.is_set():
                    cancelled_before_send()
                request_deadline=deadline if deadline is not None else default_deadline(a.name,max_output)
                result=fn(prompt,max_output,request_deadline,cancel)
            actual=cost(result.usage,rates) if rates else 0
            with self.store.connect() as db: db.execute("UPDATE usage SET status='completed',cost=?,model=?,details=? WHERE id=?",(actual,result.model,result.usage.model_dump_json(),ident))
            if cancel and cancel.is_set():raise DomainError('cancelled','Response received after cancellation; usage retained.')
            return result
        except Exception as e:
            if cancel and cancel.is_set():
                # A provider may already have received work. Retain its reservation
                # unless an exact completed usage record was already written above.
                with self.store.connect() as db:
                    db.execute("UPDATE usage SET status='cancelled_in_flight',details=? WHERE id=? AND status='reserved'",(json.dumps({'error_code':'cancelled'}),ident))
                raise DomainError('cancelled','Cancellation was requested while provider work was in progress. Any transmitted usage remains recorded.') from e
            known_usage=getattr(e,'usage',None)
            if known_usage is not None:
                actual=cost(known_usage,rates) if rates else 0
                details=json.dumps({**known_usage.model_dump(mode='json'),'error_code':getattr(e,'code','provider_output'),'finish_reason':'length'},separators=(',',':'))
                with self.store.connect() as db:
                    db.execute("UPDATE usage SET status='truncated',cost=?,model=?,details=? WHERE id=? AND status='reserved'",(actual,getattr(e,'model',a.model),details,ident))
            status=getattr(e,'status_code',None)
            if status is None and getattr(e,'response',None) is not None:status=e.response.status_code
            if status in [400,401,403,404,422,429]:
                with self.store.connect() as db:db.execute("UPDATE usage SET status='rejected_before_generation',cost=0 WHERE id=? AND status='reserved'",(ident,))
            # Unknown transport outcomes retain their conservative cost reservation across restarts.
            details=json.dumps({'error_code':e.code}) if isinstance(e,DomainError) and e.code=='provider_timeout' else '{}'
            with self.store.connect() as db:db.execute("UPDATE usage SET status='unresolved',details=? WHERE id=? AND status='reserved'",(details,ident))
            if isinstance(e,DomainError):raise
            raise DomainError('unavailable_provider','Provider failed or returned invalid output; accepted architecture was preserved.',503) from e

def usage_summary(store,pid):
    with store.connect() as db:
        rows=[dict(r) for r in db.execute('SELECT * FROM usage WHERE project_id=? ORDER BY rowid',(pid,))]
    return {'total':sum(r['cost'] if r['cost'] is not None else r['reserved'] for r in rows),'calls':len(rows),'records':[{**r,'details':json.loads(r['details'])} for r in rows]}
