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
    for p in source.passages:
        if p.locator in source.processed:continue
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

def ingest_live(store,pid,data,name,provider,settings=None,adapter=None,source_id=None,live_run=None,deadline=None):
    s=settings or Settings.environment()
    if provider not in ['openai','ollama']:raise DomainError('unavailable_provider','Unknown provider')
    if provider=='openai' and not s.allow_cloud:raise DomainError('budget_exceeded','Cloud is disabled')
    p=store.get(pid)
    if not p.synthetic:raise DomainError('invalid_input','Live document interpretation currently requires synthetic material')
    source=next((x.model_copy(deep=True) for x in p.sources if x.id==source_id),None) if source_id else parse(data,name,'document',store)
    if source is None:raise DomainError('invalid_input','Source no longer exists')
    if not source_id and any(x.canonical_id==source.canonical_id and x.version==source.version for x in p.sources):return {'proposal':None,'duplicate':True}
    # Parser coverage describes local parsing, not live interpretation; new uploads start unprocessed.
    if not source_id:source.processed=[]
    previous_processed=list(source.processed)
    previous_passages=[x for x in source.passages if x.locator in previous_processed]
    passages,groups,remainder=document_preflight(source,provider,s)
    source.passages=previous_passages+passages;source.unprocessed=[x.locator for x in passages]
    if not groups:raise DomainError('unsupported_document','No text extracted. Scanned pages need OCR, which is out of scope.')
    a=adapter or (OpenAIAdapter(s) if provider=='openai' else OllamaAdapter(s));budget=BudgetedProvider(store,s,a);action=(live_run['id']+'-' if live_run else '')+uid()
    combined=Envelope(operations=[],claims=[],tool=None,message='Document extraction proposal');known=set();used=[]
    for group in groups:
        prompt=json.dumps({'task':'Extract source facts into proposed architecture records. Reuse IDs already listed; do not repeat an existing add operation.','source':{'id':'S1','passages':[{'locator':x.locator,'text':x.text} for x in group]},'context':context(p,''),'previous_proposed_ids':sorted(known)},separators=(',',':'))
        output=budget.call(prompt,pid,action,task='document',live_run=live_run,deadline=deadline)
        if output.content.tool:raise DomainError('insufficient_context','Document extraction requested more context; narrow the document selection.')
        for op in output.content.operations:
            if op.op=='add' and op.id in known:raise DomainError('provider_output','Repeated proposed ID; no document changes were committed.')
            known.add(op.id);combined.operations.append(op)
        combined.claims.extend(output.content.claims);used.extend(x.locator for x in group)
    source.processed=previous_processed+used;source.unprocessed=[x.locator for x in passages if x.locator not in used]
    c=proposal_from_envelope(p,source,combined,source_alias='S1')
    return {'proposal':store.preview(c),'mode':'schema_action_envelope','preflight':{'requests':len(groups),'unprocessed_groups':len(remainder),'input_limit':s.max_input},'coverage':{'processed':used,'unprocessed':source.unprocessed}}
