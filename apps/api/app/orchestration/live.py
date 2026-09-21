import json,re,threading
from pathlib import Path
from ..domain.models import Operation,Claim,uid
from ..domain.naming import name_operation,can_suggest_name,explicit_name_request
from ..domain.commands import command,apply,DomainError
from ..ingest.parser import parse
from ..policies.engine import lookup
from ..policies.library import selected_ids
from ..providers.adapters import OpenAIAdapter,OllamaAdapter,MockAdapter
from ..providers.budget import BudgetedProvider
from ..providers.config import Settings
from .service import question_ops

ROOT=Path(__file__).resolve().parents[4]
CANCELLATIONS={}
_PORT_VALUE=re.compile(r'^\s*(?:(?:tcp|udp|sctp|dccp)\s*(?:[/:\-]\s*)?)?(?:port\s*)?(\d{1,5})(?:\s*/\s*(?:tcp|udp|sctp|dccp))?\s*$',re.I)
_UNKNOWN_PORT_VALUES={'','-','n/a','na','none','not decided','not specified','null','unknown','unspecified'}

def normalize_interface_port(value,ident,uncertainties):
    """Keep the canonical port scalar while accepting a few common model spellings."""
    if value is None:
        return None
    if isinstance(value,int) and not isinstance(value,bool):
        port=value
    elif isinstance(value,str):
        text=value.strip()
        if text.lower() in _UNKNOWN_PORT_VALUES:return None
        match=_PORT_VALUE.fullmatch(text)
        if match:
            port=int(match.group(1))
        else:
            port=None
    else:
        port=None
    if isinstance(port,int) and 0<=port<=65535:return port
    # A range or several ports cannot be represented by one canonical interface port.
    # Keep it unknown rather than selecting a value that was never specified.
    uncertainties.append(f'{ident}: port was left unknown because the supplied value was not one valid numeric port. Split the connection or provide one port.')
    return None

def context(p,query):
    matched=[c for c in p.components if c.name.lower() in query.lower() or c.id.lower() in query.lower()]
    selected=matched[:8] or p.components[:6]
    ids={c.id for c in selected}
    deployments=[d for d in p.deployments if d.component_id in ids]
    zone_ids={d.zone_id for d in deployments}
    return {'revision':p.revision,'project_name':p.name,'suggest_project_name':can_suggest_name(p),'components':[c.model_dump(exclude={'evidence'}) for c in selected],
            'deployments':[d.model_dump() for d in deployments],
            'zones':[z.model_dump() for z in p.zones if z.id in zone_ids],
            'interfaces':[i.model_dump(exclude={'evidence'}) for i in p.interfaces if i.source in ids and i.target in ids][:8],
            'constraints':{c.key:c.value for c in p.constraints},'decisions':{d.id:d.answer for d in p.decisions},
            'omitted_components':len(p.components)-len(selected)}

def dispatch(tool,p):
    if tool.name=='get_architecture_context':return context(p,tool.query)
    if tool.name=='lookup_policies':return lookup(tool.query,policy_ids=selected_ids(p))
    if tool.name=='find_assets':
        from ..domain.catalogue import catalogue
        rows=catalogue()
        return [r for r in rows if tool.query.lower() in r['id']][:5]
    if tool.name=='load_view_spec':
        import yaml
        views=yaml.safe_load((ROOT/'fixtures/templates/views.yaml').read_text(encoding='utf-8'))['views']
        if tool.query not in views:raise DomainError('invalid_input','Unknown curated view')
        return views[tool.query]
    raise DomainError('invalid_input','Tool is not allowed')

def proposal_from_envelope(p,source,envelope,source_alias=None):
    naming=name_operation(p,source,envelope.project_name)
    if not envelope.operations and (naming is None or not explicit_name_request(source)):
        raise DomainError('insufficient_context',envelope.message or 'No architecture changes proposed')
    claims=[]; ops=[naming] if naming else []; uncertainties=[]
    for w in envelope.claims:
        if w.source_id not in {source.id,source_alias}: raise DomainError('provider_output','Evidence was not in the supplied source context')
        claims.append(Claim(id=uid(),source_id=source.id,source_version=source.version,locator=w.locator,excerpt=w.excerpt,target_id=w.target_id,field=w.field,value=json.loads(w.value_json),source_kind=source.kind,review='confirmed'))
    for w in envelope.operations:
        value=json.loads(w.value_json)
        if not isinstance(value,dict):raise DomainError('provider_output','Operation value must be an object')
        if w.entity=='interfaces' and 'port' in value:
            value['port']=normalize_interface_port(value['port'],w.id,uncertainties)
        # Domain defaults help manual creation; model omissions are unknown facts.
        if w.op=='add' and w.entity in ['components','systems']:
            if value.get('scope') is None:value['scope']='unknown'
            if value['scope']!='unknown' and not any(
                c.target_id==w.id and ((c.field=='scope' and c.value==value['scope']) or
                                      (isinstance(c.value,dict) and c.value.get('scope')==value['scope']))
                for c in claims
            ):
                uncertainties.append(f'{w.id}: scope kept unknown because no matching scope claim was supplied.')
                value['scope']='unknown'
        if w.entity=='components':
            if value.get('asset_id','') is None:value['asset_id']='generic-role-a'
            if value.get('scope','') is None:value['scope']='unknown'
        evidence=[c.id for c in claims if c.target_id in [w.id,value.get('component_id')]]
        if not evidence:raise DomainError('provider_output','Proposed semantic change lacks source evidence')
        if w.entity in ['components','interfaces','constraints'] and w.op=='add':value['evidence']=evidence
        ops.append(Operation(op=w.op,entity=w.entity,id=w.id,value=value))
    all_ops=[Operation(op='update' if any(x.id==source.id for x in p.sources) else 'add',entity='sources',id=source.id,value=source.model_dump(exclude={'id'}))]+[Operation(op='add',entity='claims',id=c.id,value=c.model_dump(exclude={'id'})) for c in claims]+ops
    proposed=command(p,all_ops,origin='assistant',findings=uncertainties)
    candidate=apply(p,proposed)
    proposed.operations.extend(question_ops(candidate))
    return proposed

def assisted_run(store,pid,req,settings=None,adapter=None,live_run=None,deadline=None):
    p=store.get(pid);apply(p,req)
    s=settings or Settings.environment()
    if req.provider=='openai' and not s.allow_cloud:raise DomainError('budget_exceeded','OpenAI requires APP_ALLOW_CLOUD=true; a key alone does not authorize calls.')
    if not p.synthetic:raise DomainError('invalid_input','Real-data provider use requires a separate approved data-handling workflow; this PoC uses synthetic inputs.')
    if req.provider not in ['openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    try:a=adapter or (OpenAIAdapter(s) if req.provider=='openai' else OllamaAdapter(s))
    except Exception as e:raise DomainError('unavailable_provider','Provider credentials or configuration unavailable',503) from e
    source=parse(req.prompt.encode(),'Prompt','prompt');source.processed=[x.locator for x in source.passages];source.unprocessed=[]
    prompt=json.dumps({'source':{'id':'S1','locator':'prompt/1','text':req.prompt},'context':context(p,req.prompt)},separators=(',',':'))
    run_id=req.request_id; cancel=threading.Event();CANCELLATIONS[run_id]=cancel
    with store.connect() as db:
        previous=db.execute('SELECT status,result FROM runs WHERE id=?',(run_id,)).fetchone()
        if previous:raise DomainError('stale_revision','This run ID was already used; requests are never automatically replayed.',409)
        db.execute('INSERT INTO runs VALUES(?,?,?,?)',(run_id,pid,'running','{}'))
    budget=BudgetedProvider(store,s,a); repaired=False; result=None
    try:
        for step in range(min(3,s.max_calls)):
            try:
                output=budget.call(prompt,pid,run_id,'edit' if p.components else 'draft',cancel,deadline=deadline,live_run=live_run)
                if output.content.tool:
                    tool_result=dispatch(output.content.tool,p)
                    prompt=json.dumps({'initial':json.loads(prompt),'tool_result':tool_result},separators=(',',':'))
                    continue
                proposed=proposal_from_envelope(p,source,output.content,source_alias='S1')
                result={'run_id':run_id,'proposal':store.preview(proposed).model_dump(),'mode':'schema_action_envelope','model':output.model,'repairs':int(repaired)}
                break
            except (ValueError,DomainError) as error:
                if isinstance(error,DomainError) and error.code in ['budget_exceeded','insufficient_context','cancelled','unavailable_provider']:raise
                if repaired:raise
                repaired=True
                prompt=json.dumps({'initial':json.loads(prompt),'repair':'Previous response was not a valid reference-safe proposal. Return valid schema and exact source citations.'},separators=(',',':'))
        if result is None:raise DomainError('budget_exceeded','Bounded action finished without an acceptable proposal.')
        with store.connect() as db:db.execute("UPDATE runs SET status='completed',result=? WHERE id=?",(json.dumps(result),run_id))
        return result
    except Exception as e:
        with store.connect() as db:db.execute("UPDATE runs SET status='failed',result=? WHERE id=?",(json.dumps({'code':getattr(e,'code','provider_output')}),run_id))
        if isinstance(e,DomainError):raise
        raise DomainError('provider_output','Invalid provider proposal; accepted state preserved.') from e
    finally:CANCELLATIONS.pop(run_id,None)
