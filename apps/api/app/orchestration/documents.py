"""Visible, bounded document action. Parsing stays local; selected passages go only to the chosen provider."""
import json
from ..providers.config import Settings
from ..providers.adapters import OpenAIAdapter,OllamaAdapter
from ..providers.budget import BudgetedProvider
from ..providers.contracts import Envelope
from ..domain.commands import DomainError
from ..domain.models import Passage,uid
from ..ingest.parser import parse
from .live import context,proposal_from_envelope

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
    selected=groups[:min(6,settings.max_calls)]
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
    combined=Envelope(operations=[],claims=[],tool=None,message='Document extraction proposal');known=set();used=[]
    for group in groups:
        _check_cancel(cancel)
        prompt=json.dumps({'task':'Extract source facts into proposed architecture records. Reuse IDs already listed; do not repeat an existing add operation.','source':{'id':'S1','passages':[{'locator':x.locator,'text':x.text} for x in group]},'context':context(p,''),'previous_proposed_ids':sorted(known)},separators=(',',':'))
        output=budget.call(prompt,pid,action,task='document',live_run=live_run,deadline=deadline,cancel=cancel)
        if output.content.tool:raise DomainError('insufficient_context','Document extraction requested more context; narrow the document selection.')
        if combined.project_name is None:combined.project_name=output.content.project_name
        for op in output.content.operations:
            if op.op=='add' and op.id in known:raise DomainError('provider_output','Repeated proposed ID; no document changes were committed.')
            known.add(op.id);combined.operations.append(op)
        combined.claims.extend(output.content.claims);used.extend(x.locator for x in group)
    source.processed=previous_processed+used;source.unprocessed=[x.locator for x in passages if x.locator not in used]
    c=proposal_from_envelope(p,source,combined,source_alias='S1')
    _check_cancel(cancel)
    return {'proposal':store.preview(c,job_id=job_id),'mode':'schema_action_envelope','preflight':{'requests':len(groups),'unprocessed_groups':len(remainder),'input_limit':s.max_input},'coverage':{'processed':used,'unprocessed':source.unprocessed}}
