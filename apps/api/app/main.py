import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from .domain.models import Project, ChangeSet, uid
from .domain.commands import DomainError
from .domain.views import view_graph,narrative
from .storage.store import Store
from .orchestration.service import ingest,answer

ROOT=Path(__file__).resolve().parents[3]
store=Store()

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
    p=store.get(pid); return {'revision':p.revision,'text':narrative(p)}

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
async def upload_source(pid:str,file:UploadFile=File(...)):
    data=await file.read(10*1024*1024+1)
    return ingest(store,pid,data,file.filename or 'upload')

@app.post('/api/projects/{pid}/sources/{sid}/continue')
def continue_source(pid:str,sid:str,c:ChangeSet):
    from .domain.commands import apply
    apply(store.get(pid),c)
    return ingest(store,pid,b'','',source_id=sid)

@app.post('/api/projects/{pid}/runs')
def run(pid:str,req:RunRequest):
    from .domain.commands import apply
    apply(store.get(pid),req)
    if req.provider!='mock': raise DomainError('unavailable_provider','Provider adapter is not configured',503)
    if not req.prompt.strip(): raise DomainError('invalid_input','Prompt is empty')
    result=ingest(store,pid,req.prompt.encode(),'Prompt','prompt')
    if result.get('message'): raise DomainError('insufficient_context',result['message'])
    return result

@app.post('/api/projects/{pid}/answers',response_model=Project)
def answers(pid:str,req:AnswerRequest): return answer(store,pid,req)
