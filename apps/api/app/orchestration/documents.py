"""Visible, bounded document action. Parsing stays local; selected passages go only to the chosen provider."""
import json,re
from ..providers.config import Settings
from ..providers.adapters import OpenAIAdapter,OllamaAdapter
from ..providers.budget import BudgetedProvider
from ..providers.contracts import Envelope,operation_value,claim_value
from ..domain.commands import DomainError
from ..domain.models import Passage,uid
from ..ingest.parser import parse
from .live import context,proposal_from_envelope,source_excerpt
from .references import reference_catalog
from .zoning import ZONING_REQUIREMENT
from ..providers.instructions import ZONING_GUIDANCE


DOCUMENT_TASK=('Extract parts AND stated flows as interfaces. Reuse typed known_records; connections/deployments need component IDs. '
               'Refine boundaries; preserve flows. Empty if nothing new.')

def connection_passages(passages):
    return [p for p in passages if re.search(r'\bIF-\d+\b',p.text)]

def connection_prompt(project,source,previous,passages):
    return json.dumps({'task':'Extract EVERY numbered IF connection row as an interfaces operation. Preserve each IF ID, source, destination and stated data direction. Use existing component IDs. Add an endpoint component only if explicitly named in the supplied source and absent from known_records. Return no systems, zones or deployments. One exact row quote per connection; claim value=null is sufficient. Keep unknown protocol, port and initiator omitted. Do not omit connections because zoning already exists.',
        'source':{'id':'S1','passages':[{'locator':p.locator,'text':p.text} for p in passages]},
        'known_records':reference_catalog(project,previous,include_zoning=True)},separators=(',',':'))

def document_preflight(source,provider,settings):
    limit=700 if provider=='ollama' else 6000
    # Split oversized PDF pages into explicit ranges; never claim the omitted range was processed.
    passages=[]
    remaining=set(source.unprocessed) if source.processed or source.unprocessed else None
    for p in source.passages:
        if p.locator in source.processed or (remaining is not None and p.locator not in remaining):continue
        if len(p.text)<=limit:passages.append(p)
        else:
            for i in range(0,len(p.text),limit):passages.append(Passage(locator=f'{p.locator}/chars/{i}-{min(i+limit,len(p.text))}',text=p.text[i:i+limit],heading=p.heading,page=p.page))
    groups=[];group=[];size=0
    for p in passages:
        if group and size+len(p.text)>limit:groups.append(group);group=[];size=0
        group.append(p);size+=len(p.text)
    if group:groups.append(group)
    # Leave room for one repair inside the existing action limit. A one-call
    # profile still processes one group, but cannot automatically repair it.
    selected=groups[:min(6,max(1,settings.max_calls-1))]
    return passages,selected,groups[len(selected):]

def _check_cancel(cancel):
    if cancel and cancel.is_set():
        raise DomainError('cancelled','This background action was cancelled before it could save a result.',409)


def _has_accepted_facts(project,source):
    records=project.systems+project.zones+project.components+project.deployments+project.interfaces+project.constraints
    targets={record.id for record in records}
    evidence={ident for record in records for ident in getattr(record,'evidence',[])}
    # Mock saves source text and candidate claims before proposal acceptance.
    # Neither that metadata nor a shared parse-cache entry is an accepted design.
    return any(claim.source_id==source.id and claim.target_id in targets and
               (claim.review=='confirmed' or (claim.review=='conflicting' and claim.id in evidence))
               for claim in project.claims)


def _document_proposal(project,source,batches):
    combined=Envelope(operations=[],claims=[],tool=None,message='Document extraction proposal')
    additions={}
    for index,batch in enumerate(batches):
        envelope=batch['envelope']
        try:
            if envelope.tool:raise DomainError('provider_output','Document extraction must return a proposal, not a tool request.')
            supplied=source.model_copy(update={'passages':batch['evidence_passages']})
            for claim in envelope.claims:
                if claim.source_id not in ('S1',source.id):raise DomainError('provider_output','Evidence was not in the supplied source context')
                source_excerpt(supplied,claim)
                claim_value(claim)
            if combined.project_name is None:combined.project_name=envelope.project_name
            for op in envelope.operations:
                value=operation_value(op)
                if op.op=='add':
                    signature=(op.entity,value,op.proposal_reason)
                    if op.id in additions:
                        if additions[op.id]==signature:continue  # Identical repeated declarations add no new fact.
                        raise DomainError('provider_output',f'Record “{op.id[:160]}” was added twice with different definitions. Reuse its existing ID in an update, or keep distinct source-supported IDs.')
                    additions[op.id]=signature
                combined.operations.append(op)
            combined.claims.extend(envelope.claims)
        except (DomainError,ValueError) as error:
            error.batch_index=index
            raise
    try:
        return proposal_from_envelope(project,source,combined,source_alias='S1')
    except (DomainError,ValueError) as error:
        ids=getattr(error,'operation_ids',set())
        indexes=[index for index,batch in enumerate(batches) if any(op.id in ids for op in batch['envelope'].operations)]
        error.batch_index=indexes[-1] if indexes else len(batches)-1
        raise


def _repair_prompt(project,source,batches,index,error):
    batch=batches[index]
    selected=list(batch['passages'])
    locators={p.locator for p in selected}
    # Retrieve only already-processed supporting text, for identifiers mentioned
    # in the error. This can supply an earlier system definition to a later flow.
    message=getattr(error,'message',str(error))
    references=[part for part in message.split('“')[1:] if '”' in part]
    references=[part.split('”')[0] for part in references]
    extra=0
    used={p.locator for item in batches for p in item['passages']}
    for passage in source.passages:
        if passage.locator not in used or passage.locator in locators:continue
        if not any(reference and reference in passage.text for reference in references):continue
        if extra+len(passage.text)>6000:continue
        selected.append(passage);locators.add(passage.locator);extra+=len(passage.text)
    others=[item['envelope'] for i,item in enumerate(batches) if i!=index]
    task=DOCUMENT_TASK+(' '+ZONING_GUIDANCE if any(ZONING_REQUIREMENT.search(p.text) for p in selected) else '')
    payload={'task':task,'repair':'Correct this section response using the validation error. Return its complete replacement; other section responses are retained.',
             'validation_error':message,'source':{'id':'S1','passages':[{'locator':p.locator,'text':p.text} for p in selected]},
             'known_records':reference_catalog(project,others,include_zoning=True),'previous_response':batch['envelope'].model_dump()}
    return json.dumps(payload,separators=(',',':')),selected


def ingest_live(store,pid,data,name,provider,settings=None,adapter=None,source_id=None,live_run=None,deadline=None,cancel=None,job_id=None):
    _check_cancel(cancel)
    s=settings or Settings.environment()
    if provider not in ['openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    if provider=='openai' and not s.allow_cloud:raise DomainError('budget_exceeded','Cloud is disabled')
    p=store.get(pid)
    if not p.synthetic:raise DomainError('invalid_input','Live document interpretation currently requires synthetic material')
    source=next((x.model_copy(deep=True) for x in p.sources if x.id==source_id),None) if source_id else parse(data,name,'document',store)
    if source is None:raise DomainError('invalid_input','Source no longer exists')
    existing=next((x for x in p.sources if x.canonical_id==source.canonical_id and x.version==source.version),None) if not source_id else None
    if existing and _has_accepted_facts(p,existing):
        message='This document already has accepted facts in this project. Open Sources to review them.'
        if existing.unprocessed:message+=' Use Process next sections for the remaining text.'
        return {'proposal':None,'duplicate':True,'source_id':existing.id,'message':message,
                'coverage':{'processed':existing.processed,'unprocessed':existing.unprocessed}}
    if existing:
        # Retry the saved document with the explicitly selected live provider.
        # Keep its ID and original locators so prior candidate evidence still resolves.
        source=existing.model_copy(deep=True)
    # Parser coverage describes local parsing, not live interpretation; new uploads start unprocessed.
    if not source_id:
        source.processed=[];source.unprocessed=[x.locator for x in source.passages]
    previous_processed=list(source.processed)
    previous_passages=[x for x in source.passages if x.locator in previous_processed]
    passages,groups,remainder=document_preflight(source,provider,s)
    # Retain evidence passages, including original paragraphs when a live retry
    # splits them into smaller ranges. Only explicit remaining ranges are revisited.
    retained=source.passages if existing or source_id else previous_passages
    source.passages=list({x.locator:x for x in retained+passages}.values());source.unprocessed=[x.locator for x in passages]
    if not groups:raise DomainError('unsupported_document','No text extracted. Scanned pages need OCR, which is out of scope.')
    a=adapter or (OpenAIAdapter(s) if provider=='openai' else OllamaAdapter(s));budget=BudgetedProvider(store,s,a);action=(live_run['id']+'-' if live_run else '')+uid()
    batches=[];used=[];requests=0
    draft_context={key:value for key,value in context(p,'').items() if key in ('revision','project_name','suggest_project_name','decisions')}
    for group in groups:
        _check_cancel(cancel)
        previous=[batch['envelope'] for batch in batches]
        task=DOCUMENT_TASK+(' '+ZONING_GUIDANCE if any(ZONING_REQUIREMENT.search(x.text) for x in group) else '')
        prompt=json.dumps({'task':task,'source':{'id':'S1','passages':[{'locator':x.locator,'text':x.text} for x in group]},'context':draft_context,
                           'known_records':reference_catalog(p,previous,include_zoning=True),
                           'previous_proposed_ids':sorted({op.id for output in previous for op in output.operations})},separators=(',',':'))
        output=budget.call(prompt,pid,action,task='document',live_run=live_run,deadline=deadline,cancel=cancel)
        requests+=1
        batches.append({'passages':group,'evidence_passages':group,'envelope':output.content})
        used.extend(x.locator for x in group)
    # Numbered interface tables are an explicit coverage contract. A valid
    # component-only JSON response must not silently count them as extracted.
    flows=connection_passages([passage for group in groups for passage in group])
    expected={ident for passage in flows for ident in re.findall(r'\bIF-\d+\b',passage.text)}
    interfaces={i.id for i in p.interfaces}|{op.id for batch in batches for op in batch['envelope'].operations if op.entity=='interfaces' and op.op=='add'}
    if expected and len(interfaces)<len(expected) and requests<s.max_calls:
        _check_cancel(cancel)
        prompt=connection_prompt(p,source,[batch['envelope'] for batch in batches],flows)
        output=budget.call(prompt,pid,action,task='document',live_run=live_run,deadline=deadline,cancel=cancel)
        requests+=1
        batches.append({'passages':flows,'evidence_passages':flows,'envelope':output.content})
        interfaces|={op.id for op in output.content.operations if op.entity=='interfaces' and op.op=='add'}
    if expected and len(interfaces)<len(expected):
        raise DomainError('provider_output',f'The source lists {len(expected)} connections but the draft contains only {len(interfaces)}. The incomplete draft was not accepted.')
    source.processed=previous_processed+used;source.unprocessed=[x.locator for x in passages if x.locator not in used]
    repaired=False
    try:
        c=_document_proposal(p,source,batches)
    except (DomainError,ValueError) as error:
        if isinstance(error,DomainError) and error.code=='insufficient_context':raise
        if requests>=s.max_calls:
            message=getattr(error,'message',str(error))
            raise DomainError('provider_output',message+' No repair request remains within this action’s call limit.') from error
        _check_cancel(cancel)
        index=error.batch_index
        prompt,evidence_passages=_repair_prompt(p,source,batches,index,error)
        output=budget.call(prompt,pid,action,task='document',live_run=live_run,deadline=deadline,cancel=cancel)
        requests+=1;repaired=True
        batches[index]['envelope']=output.content;batches[index]['evidence_passages']=evidence_passages
        try:
            c=_document_proposal(p,source,batches)
        except (DomainError,ValueError) as repair_error:
            message=getattr(repair_error,'message',str(repair_error))
            raise DomainError('provider_output',message+' The single automatic repair did not produce a valid draft; no further requests were made.') from repair_error
    _check_cancel(cancel)
    return {'proposal':store.preview(c,job_id=job_id),'mode':'schema_action_envelope','repairs':int(repaired),
            'preflight':{'requests':requests,'unprocessed_groups':len(remainder),'input_limit':s.max_input},'coverage':{'processed':used,'unprocessed':source.unprocessed}}
