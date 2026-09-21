import json,time,threading
from datetime import datetime,timezone
from .contracts import Usage,cost,estimate,schema
from .config import pricing
from ..domain.models import uid
from ..domain.commands import DomainError

LOCAL_LOCK=threading.Lock()

class BudgetedProvider:
    """Only runtime entry to adapters. Persist reservations before transmission."""
    def __init__(self,store,settings,adapter):self.store=store;self.settings=settings;self.adapter=adapter
    def call(self,prompt,project_id,action_id,task='edit',cancel=None,deadline=None,native=False,live_run=None):
        s=self.settings;a=self.adapter;day=datetime.now(timezone.utc).date().isoformat()
        if a.name=='openai' and not s.allow_cloud: raise DomainError('budget_exceeded','Cloud is disabled. Enable APP_ALLOW_CLOUD explicitly.')
        rates=pricing()['models'].get(a.model) if a.name=='openai' else None
        if a.name=='openai' and rates is None: raise DomainError('budget_exceeded','Unknown billing model price; configure it before a paid request.')
        local=a.name=='ollama'; max_input=min(s.max_input,2500 if s.ollama_num_ctx==4096 else 5500) if local else s.max_input
        max_output=min(s.max_output,1024 if s.ollama_num_ctx==4096 else 1536) if local else s.max_output
        token_bound=estimate(prompt+json.dumps(schema(),separators=(',',':')))+100
        if token_bound>max_input: raise DomainError('insufficient_context',f'Request upper bound {token_bound} tokens exceeds {max_input}; select fewer sources/objects. Nothing was sent.')
        reserve=cost(Usage(input_tokens=token_bound,output_tokens=max_output),rates) if rates else 0
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
        try:
            if cancel and cancel.is_set():
                with self.store.connect() as db:db.execute("UPDATE usage SET status='cancelled_before_send',cost=0 WHERE id=?",(ident,))
                raise DomainError('cancelled','Cancelled before transmission')
            fn=a.invoke_tools if native else a.generate_structured
            if local:
                with LOCAL_LOCK: result=fn(prompt,max_output,deadline or time.monotonic()+90,cancel)
            else: result=fn(prompt,max_output,deadline or time.monotonic()+90,cancel)
            actual=cost(result.usage,rates) if rates else 0
            with self.store.connect() as db: db.execute("UPDATE usage SET status='completed',cost=?,model=?,details=? WHERE id=?",(actual,result.model,result.usage.model_dump_json(),ident))
            if cancel and cancel.is_set():raise DomainError('cancelled','Response received after cancellation; usage retained.')
            return result
        except Exception as e:
            # Unknown transport outcomes retain their conservative cost reservation across restarts.
            with self.store.connect() as db:db.execute("UPDATE usage SET status='unresolved' WHERE id=? AND status='reserved'",(ident,))
            if isinstance(e,DomainError):raise
            raise DomainError('unavailable_provider','Provider failed or returned invalid output; accepted architecture was preserved.',503) from e

def usage_summary(store,pid):
    with store.connect() as db:
        rows=[dict(r) for r in db.execute('SELECT * FROM usage WHERE project_id=? ORDER BY rowid',(pid,))]
    return {'total':sum(r['cost'] if r['cost'] is not None else r['reserved'] for r in rows),'calls':len(rows),'records':[{**r,'details':json.loads(r['details'])} for r in rows]}
