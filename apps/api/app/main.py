import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File,Form,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse,Response
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel,Field,ValidationError
from .domain.models import Project, ChangeSet, uid
from .domain.commands import DomainError
from .domain.views import view_graph,narrative,arrange_plan
from .domain.catalogue import catalogue as asset_catalogue
from .storage.store import Store
from .orchestration.service import ingest,answer
from .orchestration.live import assisted_run,CANCELLATIONS
from .providers.config import Settings,pricing
from .providers.budget import usage_summary,local_limits
from .policies.engine import evaluate,lookup
from .policies.library import router as policy_router
from .exports.service import export
from .orchestration.documents import ingest_live,document_preflight
from .orchestration.policy_review import ReviewRequest, review_project, latest_review
from .orchestration.jobs import schedule_prompt, schedule_source, schedule_continue, schedule_policy_review, recover_interrupted_jobs, cancel_job
from .policies.recommendations import recommendations_for, proposal_recommendations, with_policy_suggestions

ROOT=Path(__file__).resolve().parents[3]
store=Store()

STARTUP_SETTINGS = Settings.environment()  # Validate limits before serving; never performs a provider call.
app = FastAPI(title="Architecture Workbench", version="0.1.0")
app.include_router(policy_router)
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.on_event('startup')
def recover_background_jobs():
    # A previous process has no safe in-memory payload to replay.
    recover_interrupted_jobs(store)

@app.get("/api/health")
def health():
    return {"status": "ok", "provider": "mock", "synthetic": True}

@app.exception_handler(DomainError)
async def domain_error(request,error):
    return JSONResponse(status_code=error.status,content={'code':error.code,'message':error.message})

class CreateRequest(BaseModel):
    name:str='Untitled architecture'
    reference:str|None=None

@app.get('/api/projects')
def projects(): return store.list()

@app.get('/api/projects/trash')
def trashed_projects(): return store.list_trash()

class EmptyTrashRequest(BaseModel):
    confirmed:bool=False
    project_ids:list[str]=Field(default_factory=list,max_length=10000)

@app.post('/api/projects/trash/empty')
def empty_project_trash(req:EmptyTrashRequest):
    if not req.confirmed:raise DomainError('confirmation_required','Confirm permanent removal of the selected trashed projects.')
    return store.empty_trash(req.project_ids)

@app.post('/api/projects/{pid}/trash')
def trash_project(pid:str): return store.trash(pid)

@app.post('/api/projects/{pid}/restore',response_model=Project)
def restore_project(pid:str): return store.restore(pid)

@app.post('/api/projects',response_model=Project)
def create(req:CreateRequest):
    if req.reference:
        if req.reference not in ['A','B','portal','robotics']: raise DomainError('invalid_input','Unknown reference')
        folder='references' if req.reference in ['A','B'] else 'demos'
        p=Project.model_validate_json((ROOT/f'fixtures/{folder}/{req.reference}/project.json').read_text(encoding='utf-8')); p.id=uid(); p.name=req.name if req.name!='Untitled architecture' else p.name
    else: p=Project(name=req.name,policy_ids=[])
    if req.reference:
        for source in p.sources: source.origin='bundled_demo'
    return store.create(p)

@app.get('/api/projects/{pid}',response_model=Project)
def project(pid:str): return store.get(pid)

@app.post('/api/projects/import',response_model=Project)
def import_project(p:Project):
    p.id=uid()
    return store.create(p)

@app.post('/api/projects/{pid}/preview',response_model=ChangeSet)
def preview(pid:str,c:ChangeSet):
    if pid!=c.project_id: raise DomainError('invalid_input','Project mismatch')
    return store.preview(c)

@app.post('/api/projects/{pid}/commands',response_model=Project)
def commit(pid:str,c:ChangeSet):
    if pid!=c.project_id: raise DomainError('invalid_input','Project mismatch')
    return store.commit(c)

class AcceptRequest(BaseModel):
    policy_ids:list[str]=Field(default_factory=list,max_length=100)

@app.get('/api/projects/{pid}/policy-suggestions')
def policy_suggestions(pid:str):return {'items':recommendations_for(store.get(pid))}

@app.get('/api/changes/{ident}/policy-suggestions')
def change_policy_suggestions(ident:str):return {'items':proposal_recommendations(store,ident)}

@app.post('/api/changes/{ident}/accept',response_model=Project)
def accept(ident:str,request:AcceptRequest|None=None):
    c=store.change(ident)
    if c.state!='pending': raise DomainError('invalid_input','Proposal is no longer pending')
    c=with_policy_suggestions(store.get(c.project_id),c,request.policy_ids if request else [])
    return store.commit(c)

@app.post('/api/changes/{ident}/reject')
def reject(ident:str): store.reject(ident); return {'state':'rejected'}

@app.post('/api/projects/{pid}/undo',response_model=Project)
def undo(pid:str,c:ChangeSet):
    if pid!=c.project_id: raise DomainError('invalid_input','Project mismatch')
    return store.undo(c)

@app.post('/api/projects/{pid}/redo',response_model=Project)
def redo(pid:str,c:ChangeSet):
    if pid!=c.project_id: raise DomainError('invalid_input','Project mismatch')
    return store.redo(c)

@app.get('/api/projects/{pid}/views/{kind}')
def view(pid:str,kind:str):
    p=store.get(pid)
    if kind not in p.views: raise DomainError('invalid_input','Unknown view')
    return view_graph(p,kind)

@app.get('/api/projects/{pid}/views/{kind}/arrange')
def arrange(pid:str,kind:str,aspect_ratio:float=Query(default=1.5,ge=.5,le=3)):
    p=store.get(pid)
    if kind not in p.views: raise DomainError('invalid_input','Unknown view')
    return arrange_plan(p,kind,aspect_ratio)

@app.get('/api/projects/{pid}/narrative')
def get_narrative(pid:str):
    p=store.get(pid);key=f'narrative-v2:{pid}:{p.revision}'
    with store.connect() as db:
        row=db.execute('SELECT body FROM cache WHERE hash=?',(key,)).fetchone()
        text=row[0] if row else narrative(p)
        if not row:db.execute('INSERT INTO cache VALUES(?,?)',(key,text))
    return {'revision':p.revision,'text':text}

@app.get('/api/catalogue')
def catalogue(): return asset_catalogue()

@app.get('/api/assets/{asset}')
def asset_file(asset:str):
    if asset not in {a['icon'] for a in catalogue()}: raise DomainError('invalid_input','Asset not in catalogue')
    return FileResponse(ROOT/'fixtures/assets'/asset,media_type='image/svg+xml')

class RunRequest(ChangeSet):
    prompt:str
    provider:str='mock'

class AnswerRequest(ChangeSet):
    decision_id:str
    answer:str

@app.post('/api/projects/{pid}/sources')
async def upload_source(pid:str,file:UploadFile=File(...),provider:str=Form('mock')):
    data=await file.read(10*1024*1024+1)
    if provider!='mock':return await run_in_threadpool(ingest_live,store,pid,data,file.filename or 'upload',provider)
    return await run_in_threadpool(ingest,store,pid,data,file.filename or 'upload')

@app.post('/api/projects/{pid}/source-preflight')
async def source_preflight(pid:str,file:UploadFile=File(...),provider:str=Form('mock')):
    from .ingest.parser import parse
    data=await file.read(10*1024*1024+1)
    def preflight():
        store.get(pid);source=parse(data,file.filename or 'upload',store=store)
        if provider not in ['mock','openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
        source.processed=[]
        settings=Settings.environment();_,groups,remainder=document_preflight(source,provider,settings)
        return {'provider':provider,'requests':len(groups),'repair_requests':int(provider!='mock' and bool(groups) and settings.max_calls>len(groups)),
                'unprocessed_batches':len(remainder),'max_cost_usd':settings.document_usd if provider=='openai' else 0,'unsupported_pages':source.unsupported_pages}
    return await run_in_threadpool(preflight)

class ContinueRequest(ChangeSet):
    provider:str='mock'

class SourceJobSnapshot(BaseModel):
    base_revision:int=Field(ge=0)
    base_views:dict[str,int]
    provider:str='mock'

@app.post('/api/projects/{pid}/jobs')
def start_prompt_job(pid:str,payload:dict):
    if payload.get('kind')!='prompt':raise DomainError('invalid_input','Background job kind must be prompt')
    try:request=RunRequest.model_validate({key:value for key,value in payload.items() if key!='kind'})
    except ValidationError as error:raise DomainError('invalid_input','Background prompt jobs require a complete current project snapshot and a prompt.') from error
    if request.provider not in ['mock','openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    return schedule_prompt(store,pid,request)

@app.post('/api/projects/{pid}/source-jobs')
async def start_source_job(pid:str,file:UploadFile=File(...),provider:str=Form('mock'),base_revision:str=Form(...),base_views:str=Form(...)):
    data=await file.read(10*1024*1024+1)
    try:snapshot=SourceJobSnapshot(base_revision=int(base_revision),base_views=json.loads(base_views),provider=provider)
    except (TypeError,ValueError) as error:raise DomainError('invalid_input','Background source jobs require a valid base revision and base views JSON.') from error
    if snapshot.provider not in ['mock','openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    return schedule_source(store,pid,data,file.filename or 'upload',snapshot.provider,snapshot.base_revision,snapshot.base_views)

@app.post('/api/projects/{pid}/sources/{sid}/continue')
def continue_source(pid:str,sid:str,c:ContinueRequest):
    from .domain.commands import apply
    apply(store.get(pid),c)
    if c.provider!='mock':return ingest_live(store,pid,b'','',c.provider,source_id=sid)
    return ingest(store,pid,b'','',source_id=sid)

@app.post('/api/projects/{pid}/sources/{sid}/continue-jobs')
def start_continue_job(pid:str,sid:str,request:ContinueRequest):return schedule_continue(store,pid,sid,request)

@app.post('/api/projects/{pid}/runs')
def run(pid:str,req:RunRequest):
    from .domain.commands import apply
    apply(store.get(pid),req)
    if not req.prompt.strip(): raise DomainError('invalid_input','Prompt is empty')
    if req.provider!='mock': return assisted_run(store,pid,req)
    result=ingest(store,pid,req.prompt.encode(),'Prompt','prompt')
    if result.get('message'): raise DomainError('insufficient_context',result['message'])
    return result

@app.get('/api/jobs')
def jobs():return store.list_jobs()

@app.get('/api/jobs/{ident}')
def job(ident:str):return store.get_job(ident)

@app.post('/api/jobs/{ident}/cancel')
def cancel_background_job(ident:str):return cancel_job(store,ident)

@app.post('/api/jobs/{ident}/dismiss')
def dismiss_job(ident:str):return store.dismiss_job(ident)

@app.post('/api/projects/{pid}/answers',response_model=Project)
def answers(pid:str,req:AnswerRequest): return answer(store,pid,req)

@app.get('/api/projects/{pid}/findings')
def findings(pid:str):return evaluate(store.get(pid))

@app.get('/api/projects/{pid}/policy-review')
def get_policy_review(pid:str,provider:str='mock'):return latest_review(store,pid,provider)

@app.post('/api/projects/{pid}/policy-review')
def run_policy_review(pid:str,request:ReviewRequest):return review_project(store,pid,request)

@app.post('/api/projects/{pid}/policy-review-jobs')
def start_policy_review_job(pid:str,request:ReviewRequest):return schedule_policy_review(store,pid,request)

@app.get('/api/settings')
def settings():
    s=Settings.environment()
    local_input,local_output=local_limits(s,0)
    local={'input':local_input,'output_up_to':local_output,'context':s.ollama_num_ctx,'context_reserve':512}
    return {**s.model_dump(),'price_date':pricing()['date'],'billing_prices':pricing()['models'],'local_profile':local,'mode':'schema_action_envelope for live providers; native tools require capability verification','telemetry':False}

@app.get('/api/projects/{pid}/usage')
def usage(pid:str):return usage_summary(store,pid)

@app.get('/api/runs/{ident}')
def get_run(ident:str):
    with store.connect() as db:row=db.execute('SELECT status,result FROM runs WHERE id=?',(ident,)).fetchone()
    if not row:raise DomainError('not_found','Run not found',404)
    return {'status':row['status'],'result':json.loads(row['result'])}

@app.post('/api/runs/{ident}/cancel')
def cancel_run(ident:str):
    if ident in CANCELLATIONS:CANCELLATIONS[ident].set()
    return {'status':'cancellation_requested','note':'Transmitted requests may still incur usage.'}

@app.get('/api/projects/{pid}/exports/{format}')
def export_project(pid:str,format:str,view:str='logical'):
    snapshot=store.get(pid)
    try:body,mime=export(snapshot,format,view)
    except ValueError as e:raise DomainError('invalid_input',str(e)) from e
    ext='json' if format=='pattern' else format
    return Response(body,media_type=mime,headers={'Content-Disposition':f'attachment; filename="architecture-{format}.{ext}"','X-Semantic-Revision':str(snapshot.revision),'X-Content-Type-Options':'nosniff'})

@app.get('/api/projects/{pid}/proposal-history')
def reviewed_proposals(pid:str,before:int|None=None):
    from .orchestration.history import proposal_history
    return proposal_history(store,pid,before)
