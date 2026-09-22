import hashlib,json,re,threading
from pathlib import Path
from ..domain.models import Operation,Claim,Source,Passage,uid
from ..domain.naming import name_operation,can_suggest_name,explicit_name_request
from ..domain.commands import command,apply,DomainError,temporary_id_map
from ..domain.catalogue import component_asset
from ..ingest.parser import parse
from ..policies.engine import lookup
from ..policies.library import selected_ids
from ..providers.adapters import OpenAIAdapter,OllamaAdapter,MockAdapter
from ..providers.budget import BudgetedProvider
from ..providers.config import Settings
from ..providers.contracts import operation_value,claim_value
from .service import question_ops
from .references import normalize_references
from .zoning import ZONING_QUERY,supporting_sources,new_zone_layout
from ..providers.instructions import ZONING_GUIDANCE

ROOT=Path(__file__).resolve().parents[4]
CANCELLATIONS={}
_PORT_VALUE=re.compile(r'^\s*(?:(?:tcp|udp|sctp|dccp)\s*(?:[/:\-]\s*)?)?(?:port\s*)?(\d{1,5})(?:\s*/\s*(?:tcp|udp|sctp|dccp))?\s*$',re.I)
_UNKNOWN_VALUES={'','-','n/a','na','none','not decided','not specified','null','unknown','unspecified'}
_UNKNOWN_ENUM_FIELDS={'systems':('scope',),'components':('scope','form_factor'),'deployments':('redundancy_mode',),'interfaces':('data_direction',)}

def normalize_interface_port(value,ident,uncertainties):
    """Keep the canonical port scalar while accepting a few common model spellings."""
    if value is None:
        return None
    if isinstance(value,int) and not isinstance(value,bool):
        port=value
    elif isinstance(value,str):
        text=value.strip()
        if text.lower() in _UNKNOWN_VALUES:return None
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

def normalize_interface_enforcement(value,ident,component_ids,uncertainties):
    """Unknown enforcement is an empty list, never a made-up component reference."""
    items=value if isinstance(value,list) else [value]
    references=[]; unknown=False
    for item in items:
        # Resolve exact IDs first, including a component literally named "unknown".
        if isinstance(item,str) and item in component_ids:
            if item not in references:references.append(item)
        elif item is None or (isinstance(item,str) and item.strip().lower() in _UNKNOWN_VALUES):
            unknown=True
        else:
            raise DomainError('provider_output',f'Connection {ident}: the AI supplied an enforcement reference that does not match a component. Enforcement must list component IDs, or be empty when unspecified. Your current design was not changed.')
    if unknown:
        uncertainties.append(f'{ident}: enforcement is not fully specified. Confirm which firewall or other component controls this connection; no extra enforcement component was assumed.')
    return references

def context(p,query):
    zoning=bool(ZONING_QUERY.search(query))
    matched=[c for c in p.components if c.name.lower() in query.lower() or c.id.lower() in query.lower()]
    selected=p.components if zoning else matched[:8] or p.components[:6]
    ids={c.id for c in selected}
    deployments=[d for d in p.deployments if d.component_id in ids]
    zone_ids={d.zone_id for d in deployments}
    return {'revision':p.revision,'project_name':p.name,'suggest_project_name':can_suggest_name(p),
            'systems':[s.model_dump() for s in p.systems if s.id in {c.system_id for c in selected}],
            'components':[c.model_dump(include={'id','name','role','system_id','scope','status','asset_id'}) if zoning else c.model_dump(exclude={'evidence'}) for c in selected],
            'deployments':[d.model_dump() for d in deployments],
            'zones':[z.model_dump() for z in p.zones if zoning or z.id in zone_ids],
            'interfaces':[i.model_dump(include={'id','source','target','purpose'}) if zoning else i.model_dump(exclude={'evidence'}) for i in p.interfaces if i.source in ids and i.target in ids][:100 if zoning else 8],
            'constraints':{c.key:c.value for c in p.constraints},'decisions':{d.id:d.answer for d in p.decisions},
            'omitted_components':len(p.components)-len(selected),
            **({'zoning_guidance':ZONING_GUIDANCE,'source_excerpts':[{'source_id':s.id,'locator':passage.locator,'text':passage.text}
                                   for s in supporting_sources(p,query) for passage in s.passages]} if zoning else {})}

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

def source_excerpt(source,claim):
    """Restore whitespace from the cited passage; never repair words or locators."""
    passages=[p for p in source.passages if p.locator==claim.locator]
    if claim.excerpt.strip():
        for passage in passages:
            if claim.excerpt in passage.text:
                return claim.excerpt
        # PDFs wrap lines and use non-breaking spaces. Match only a contiguous
        # quote in the stated passage, then store the exact original characters
        # so the canonical model's strict evidence validation still applies.
        pattern=r'\s+'.join(re.escape(word) for word in claim.excerpt.split())
        for passage in passages:
            match=re.search(pattern,passage.text)
            if match:
                return match.group(0)
    reason=('that section was not in the supplied source' if not passages else
            'the quoted words could not be found together in that section')
    raise DomainError('provider_output',
        f'The AI citation for “{claim.target_id[:160]}” at “{claim.locator[:160]}” could not be verified: {reason}. '
        'Retry the import or prompt so the AI can supply an exact source quote. Your current design was not changed.')

def proposal_from_envelope(p,source,envelope,source_alias=None,*,evidence_sources=()):
    envelope=normalize_references(p,envelope)
    naming=name_operation(p,source,envelope.project_name)
    if not envelope.operations and (naming is None or not explicit_name_request(source)):
        raise DomainError('insufficient_context',envelope.message or 'No architecture changes proposed')
    claims=[]; ops=[naming] if naming else []; uncertainties=[]
    assumptions={}
    for w in envelope.operations:
        if w.proposal_reason is not None:
            allowed={'name'} if w.entity=='zones' else {'component_id','zone_id'} if w.entity=='deployments' else set()
            value=operation_value(w)
            field='name' if w.entity=='zones' else 'zone_id'
            if w.op not in ('add','update') or not allowed or not isinstance(value,dict) or field not in value or not set(value)<=allowed or not w.proposal_reason.strip():
                raise DomainError('provider_output','proposal_reason is only for proposed zone names or component zone assignments; keep unrelated details as separate evidenced changes.')
            if not any(c.target_id==w.id for c in envelope.claims):
                raise DomainError('provider_output','A proposed zoning choice needs a direct source claim for its supporting requirement.')
            assumptions[w.id]=w
    supplied={s.id:s for s in evidence_sources}
    supplied.update({source.id:source})
    if source_alias:supplied[source_alias]=source
    component_ids=({c.id for c in p.components}|{w.id for w in envelope.operations if w.entity=='components' and w.op=='add'})-{w.id for w in envelope.operations if w.entity=='components' and w.op=='remove'}
    for w in envelope.claims:
        cited=supplied.get(w.source_id)
        if cited is None: raise DomainError('provider_output','Evidence was not in the supplied source context')
        inferred=w.target_id in assumptions
        claims.append(Claim(id=uid(),source_id=cited.id,source_version=cited.version,locator=w.locator,excerpt=source_excerpt(cited,w),target_id=w.target_id,field='proposal_basis' if inferred else w.field,value=None if inferred else claim_value(w),source_kind=cited.kind,review='unreviewed' if inferred else 'confirmed'))
    proposal_source=None
    if assumptions:
        passages=[Passage(locator=f'proposal/{i+1}',text=w.proposal_reason.strip()) for i,w in enumerate(assumptions.values())]
        digest=hashlib.sha256('\n'.join(p.text for p in passages).encode()).hexdigest()
        proposal_source=Source(id=uid(),name='Archie zoning design assumptions',kind='assistant_proposal',sha256=digest,canonical_id=uid(),passages=passages,processed=[p.locator for p in passages])
        for w,passage in zip(assumptions.values(),passages):
            claims.append(Claim(id=uid(),source_id=proposal_source.id,source_version=proposal_source.version,locator=passage.locator,excerpt=passage.text,target_id=w.id,field='proposed_zoning',value=operation_value(w),source_kind='assistant_proposal',review='unreviewed'))
            uncertainties.append(f'{w.id}: proposed zoning — {passage.text}')
    for w in envelope.operations:
        value=operation_value(w)
        if w.entity=='interfaces' and 'port' in value:
            value['port']=normalize_interface_port(value['port'],w.id,uncertainties)
        if w.entity=='interfaces' and 'enforcement' in value:
            value['enforcement']=normalize_interface_enforcement(value['enforcement'],w.id,component_ids,uncertainties)
        # Nullable unknowns from the model must use the canonical enum's unknown value.
        for field in _UNKNOWN_ENUM_FIELDS.get(w.entity,()):
            if field in value and value[field] is None:value[field]='unknown'
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
            if w.op=='add' or 'asset_id' in value:
                existing=next((c.model_dump() for c in p.components if c.id==w.id),{})
                value['asset_id']=component_asset({**existing,**value})
            if value.get('scope','') is None:value['scope']='unknown'
        evidence=[c.id for c in claims if c.target_id in [w.id,value.get('component_id')]]
        if not evidence:raise DomainError('provider_output','Proposed semantic change lacks source evidence')
        if w.entity in ['components','interfaces','constraints'] and w.op=='add':value['evidence']=evidence
        ops.append(Operation(op=w.op,entity=w.entity,id=w.id,value=value))
    all_ops=[Operation(op='update' if any(x.id==source.id for x in p.sources) else 'add',entity='sources',id=source.id,value=source.model_dump(exclude={'id'}))]+[Operation(op='add',entity='claims',id=c.id,value=c.model_dump(exclude={'id'})) for c in claims]+ops
    if proposal_source:all_ops.insert(1,Operation(op='add',entity='sources',id=proposal_source.id,value=proposal_source.model_dump(exclude={'id'})))
    proposed=command(p,all_ops,origin='assistant',findings=uncertainties)
    candidate=apply(p,proposed)
    original_ids={value:key for key,value in temporary_id_map(proposed).items()}
    proposed.operations.extend(op.model_copy(update={'id':original_ids.get(op.id,op.id)}) for op in new_zone_layout(p,candidate))
    proposed.operations.extend(question_ops(candidate))
    return proposed

def assisted_run(store,pid,req,settings=None,adapter=None,live_run=None,deadline=None,cancel=None,job_id=None):
    p=store.get(pid);apply(p,req)
    s=settings or Settings.environment()
    if req.provider=='openai' and not s.allow_cloud:raise DomainError('budget_exceeded','OpenAI requires APP_ALLOW_CLOUD=true; a key alone does not authorize calls.')
    if not p.synthetic:raise DomainError('invalid_input','Real-data provider use requires a separate approved data-handling workflow; this PoC uses synthetic inputs.')
    if req.provider not in ['openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    try:a=adapter or (OpenAIAdapter(s) if req.provider=='openai' else OllamaAdapter(s))
    except Exception as e:raise DomainError('unavailable_provider','Provider credentials or configuration unavailable',503) from e
    source=parse(req.prompt.encode(),'Prompt','prompt');source.processed=[x.locator for x in source.passages];source.unprocessed=[]
    evidence_sources=supporting_sources(p,req.prompt)
    prompt=json.dumps({'source':{'id':'S1','locator':'prompt/1','text':req.prompt},'context':context(p,req.prompt)},separators=(',',':'))
    run_id=req.request_id;active_cancel=cancel or threading.Event();CANCELLATIONS[run_id]=active_cancel
    with store.connect() as db:
        previous=db.execute('SELECT status,result FROM runs WHERE id=?',(run_id,)).fetchone()
        if previous:raise DomainError('stale_revision','This run ID was already used; requests are never automatically replayed.',409)
        if active_cancel.is_set():raise DomainError('cancelled','Cancelled before transmission')
        db.execute('INSERT INTO runs VALUES(?,?,?,?)',(run_id,pid,'running','{}'))
    budget=BudgetedProvider(store,s,a); repaired=False; result=None
    try:
        for step in range(min(3,s.max_calls)):
            output=None
            try:
                output=budget.call(prompt,pid,run_id,'edit' if p.components else 'draft',active_cancel,deadline=deadline,live_run=live_run)
                if output.content.tool:
                    tool_result=dispatch(output.content.tool,p)
                    if output.content.tool.name=='get_architecture_context':
                        evidence_sources.extend(supporting_sources(p,output.content.tool.query))
                    prompt=json.dumps({'initial':json.loads(prompt),'tool_result':tool_result},separators=(',',':'))
                    continue
                proposed=proposal_from_envelope(p,source,output.content,source_alias='S1',evidence_sources=evidence_sources)
                if active_cancel.is_set():raise DomainError('cancelled','Response received after cancellation; no proposal was saved.')
                result={'run_id':run_id,'proposal':store.preview(proposed,job_id=job_id).model_dump(),'mode':'schema_action_envelope','model':output.model,'repairs':int(repaired)}
                break
            except (ValueError,DomainError) as error:
                if isinstance(error,DomainError) and (error.code in ['budget_exceeded','insufficient_context','cancelled','unavailable_provider','provider_timeout','stale_revision','project_trashed','not_found'] or getattr(error,'terminal',False)):raise
                if repaired:raise
                repaired=True
                prompt=json.dumps({'initial':json.loads(prompt),'repair':'Correct the validation error. Return a complete replacement proposal with exact source citations.',
                                   'validation_error':getattr(error,'message',str(error)),
                                   'previous_response':output.content.model_dump() if output else None},separators=(',',':'))
        if result is None:raise DomainError('budget_exceeded','Bounded action finished without an acceptable proposal.')
        with store.connect() as db:db.execute("UPDATE runs SET status='completed',result=? WHERE id=?",(json.dumps(result),run_id))
        return result
    except Exception as e:
        with store.connect() as db:db.execute("UPDATE runs SET status='failed',result=? WHERE id=?",(json.dumps({'code':getattr(e,'code','provider_output')}),run_id))
        if isinstance(e,DomainError):raise
        raise DomainError('provider_output','Invalid provider proposal; accepted state preserved.') from e
    finally:
        if CANCELLATIONS.get(run_id) is active_cancel:CANCELLATIONS.pop(run_id,None)
