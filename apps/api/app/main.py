import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse,Response
from pydantic import BaseModel
from .domain.models import Project, ChangeSet, uid
from .domain.commands import DomainError
from .domain.views import view_graph,narrative
from .storage.store import Store
from .orchestration.service import ingest,answer
from .orchestration.live import assisted_run,CANCELLATIONS
from .providers.config import Settings,pricing
from .providers.budget import usage_summary
from .policies.engine import evaluate,lookup
from .exports.service import export
from .orchestration.documents import ingest_live,document_preflight

ROOT=Path(__file__).resolve().parents[3]
store=Store()

STARTUP_SETTINGS = Settings.environment()  # Validate limits before serving; never performs a provider call.
app = FastAPI(title="Architecture Workbench", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

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

@app.post('/api/projects',response_model=Project)
def create(req:CreateRequest):
    if req.reference:
        if req.reference not in ['A','B']: raise DomainError('invalid_input','Unknown reference')
        p=Project.model_validate_json((ROOT/f'fixtures/references/{req.reference}/project.json').read_text(encoding='utf-8')); p.id=uid(); p.name=req.name
    else: p=Project(name=req.name)
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

@app.post('/api/changes/{ident}/accept',response_model=Project)
def accept(ident:str):
    c=store.change(ident)
    if c.state!='pending': raise DomainError('invalid_input','Proposal is no longer pending')
    return store.commit(c)

@app.post('/api/changes/{ident}/reject')
def reject(ident:str): store.reject(ident); return {'state':'rejected'}

@app.post('/api/projects/{pid}/undo',response_model=Project)
def undo(pid:str,c:ChangeSet):
    if pid!=c.project_id: raise DomainError('invalid_input','Project mismatch')
    return store.undo(c)

@app.get('/api/projects/{pid}/views/{kind}')
def view(pid:str,kind:str):
    p=store.get(pid)
    if kind not in p.views: raise DomainError('invalid_input','Unknown view')
    return view_graph(p,kind)

@app.get('/api/projects/{pid}/narrative')
def get_narrative(pid:str):
    p=store.get(pid);key=f'narrative:{pid}:{p.revision}'
    with store.connect() as db:
        row=db.execute('SELECT body FROM cache WHERE hash=?',(key,)).fetchone()
        text=row[0] if row else narrative(p)
        if not row:db.execute('INSERT INTO cache VALUES(?,?)',(key,text))
    return {'revision':p.revision,'text':text}

@app.get('/api/catalogue')
def catalogue(): return json.loads((ROOT/'fixtures/assets/manifest.json').read_text(encoding='utf-8'))

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
    if provider!='mock':return ingest_live(store,pid,data,file.filename or 'upload',provider)
    return ingest(store,pid,data,file.filename or 'upload')

@app.post('/api/projects/{pid}/source-preflight')
async def source_preflight(pid:str,file:UploadFile=File(...),provider:str=Form('mock')):
    from .ingest.parser import parse
    store.get(pid);source=parse(await file.read(10*1024*1024+1),file.filename or 'upload',store=store)
    if provider not in ['mock','openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    source.processed=[]
    settings=Settings.environment();_,groups,remainder=document_preflight(source,provider,settings)
    return {'provider':provider,'requests':len(groups),'unprocessed_batches':len(remainder),'max_cost_usd':settings.document_usd if provider=='openai' else 0,'unsupported_pages':source.unsupported_pages}

class ContinueRequest(ChangeSet):
    provider:str='mock'

@app.post('/api/projects/{pid}/sources/{sid}/continue')
def continue_source(pid:str,sid:str,c:ContinueRequest):
    from .domain.commands import apply
    apply(store.get(pid),c)
    if c.provider!='mock':return ingest_live(store,pid,b'','',c.provider,source_id=sid)
    return ingest(store,pid,b'','',source_id=sid)

@app.post('/api/projects/{pid}/runs')
def run(pid:str,req:RunRequest):
    from .domain.commands import apply
    apply(store.get(pid),req)
    if not req.prompt.strip(): raise DomainError('invalid_input','Prompt is empty')
    if req.provider!='mock': return assisted_run(store,pid,req)
    result=ingest(store,pid,req.prompt.encode(),'Prompt','prompt')
    if result.get('message'): raise DomainError('insufficient_context',result['message'])
    return result

@app.post('/api/projects/{pid}/answers',response_model=Project)
def answers(pid:str,req:AnswerRequest): return answer(store,pid,req)

@app.get('/api/projects/{pid}/findings')
def findings(pid:str):return evaluate(store.get(pid))

@app.get('/api/policies')
def policies(q:str=''):return lookup(q)

@app.get('/api/settings')
def settings():return {**Settings.environment().model_dump(),'price_date':pricing()['date'],'billing_prices':pricing()['models'],'local_profile':{'input':2500,'output':1024,'context':4096},'mode':'schema_action_envelope for live providers; native tools require capability verification','telemetry':False}

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
