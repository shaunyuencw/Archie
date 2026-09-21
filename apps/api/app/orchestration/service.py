from ..domain.models import Operation,Decision,uid
from ..domain.commands import command,apply,DomainError
from ..ingest.parser import parse,batch
from .mock import extract,edit

def question_ops(p):
    existing={d.id for d in p.decisions}; candidates=[]
    if any(c.key=='no_internet' and c.value is True for c in p.constraints) and any(c.internet_hosted for c in p.components):
        candidates.append(Decision(id='question-internet-conflict',question='Resolve the no-internet requirement and external dependency conflict?',field='resolution',options=['Retain offline requirement and redesign','Request an explicit exception'],evidence=[c.id for c in p.claims if c.target_id in {'offline','cloud'}]))
    if any(c.key=='resilience_required' and c.value is True for c in p.constraints) and any(c.key=='availability_strategy' and 'single_instance' in str(c.value) for c in p.constraints):
        candidates.append(Decision(id='question-resilience-conflict',question='Resolve resilience versus single-instance design?',field='resolution',options=['Define recovery or redundancy','Revisit resilience requirement'],evidence=[c.id for c in p.claims if c.target_id in {'resilience','availability'}]))
    for i in p.interfaces:
        if i.purpose=='events' and i.delivery is None: candidates.append(Decision(id='question-delivery-'+i.id,question='How are events delivered?',target_id=i.id,field='delivery',options=['push','pull'],evidence=i.evidence))
        if i.initiator is None: candidates.append(Decision(id='question-initiator-'+i.id,question=f'Who initiates {i.id}?',target_id=i.id,field='initiator',options=[i.source,i.target],evidence=i.evidence))
        if i.purpose is None: candidates.insert(0,Decision(id='question-purpose-'+i.id,question=f'What is the administration route purpose for {i.id}?',target_id=i.id,field='purpose',options=['management','integration','video'],evidence=i.evidence))
    for c in p.constraints:
        if c.key=='availability_strategy' and c.value is None: candidates.append(Decision(id='question-availability',question='What availability strategy is intended?',target_id=c.id,field='value',options=['active_passive','recovery_plan','single_instance'],evidence=c.evidence))
    capacity=max(0,3-sum(d.state=='unknown' for d in p.decisions))
    return [Operation(op='add',entity='decisions',id=d.id,value=d.model_dump(exclude={'id'})) for d in candidates if d.id not in existing][:capacity]

def ingest(store,pid,data,name,kind='document',source_id=None):
    p=store.get(pid)
    if source_id: source=next(s for s in p.sources if s.id==source_id)
    else:
        source=parse(data,name,kind,store)
        duplicate=next((s for s in p.sources if s.canonical_id==source.canonical_id and s.version==source.version),None)
        if duplicate:
            if source.sha256 not in duplicate.variants:
                # Preserve page/table locators for alternate renderings without duplicating facts.
                variants=duplicate.variants+[source.sha256]
                p=store.commit(command(p,[Operation(op='update',entity='sources',id=duplicate.id,value={'variants':variants})],origin='ingest'))
            return {'proposal':None,'duplicate':True,'source_id':duplicate.id,'coverage':{'processed':duplicate.processed,'unprocessed':duplicate.unprocessed}}
    passages=batch(source)
    claims,ops=(edit(data.decode('utf-8'),p,source) if kind=='prompt' and p.components else ([],[]))
    if not ops: claims,ops=extract(source,passages,p)
    processed=source.processed+[s.locator for s in passages]; remaining=[s for s in source.unprocessed if s not in processed]
    source.processed=processed;source.unprocessed=remaining
    source_op=Operation(op='update' if source_id else 'add',entity='sources',id=source.id,value=source.model_dump(exclude={'id'}))
    metadata=[source_op]+[Operation(op='add',entity='claims',id=c.id,value=c.model_dump(exclude={'id'})) for c in claims]
    p=store.commit(command(p,metadata,origin='ingest'))
    if not ops: return {'proposal':None,'message':'No supported candidate facts found. Mock understands the authored fixture statements and a small set of prompts; use a live provider for broader interpretation.','coverage':{'processed':processed,'unprocessed':remaining}}
    review=[Operation(op='update',entity='claims',id=c.id,value={'review':'confirmed' if c.review!='conflicting' else 'conflicting'}) for c in claims]
    proposed=command(p,ops+review,origin='assistant')
    candidate=apply(p,proposed)
    questions=question_ops(candidate)
    proposed.operations.extend(questions)
    proposal=store.preview(proposed)
    return {'proposal':proposal,'coverage':{'processed':processed,'unprocessed':remaining},'questions':len(questions),'mode':'deterministic_mock'}

def answer(store,pid,request):
    p=store.get(pid); apply(p,request) # revision check only; no write
    d=next((d for d in p.decisions if d.id==request.decision_id),None)
    if d is None: raise DomainError('invalid_input','Question no longer exists')
    ops=[Operation(op='update',entity='decisions',id=d.id,value={'answer':request.answer,'state':'answered'})]
    if request.answer!='Not decided' and d.target_id:
        entity='interfaces' if any(i.id==d.target_id for i in p.interfaces) else 'constraints'
        # Free text answers to typed reference fields stay decisions until a valid object is selected.
        if d.field!='initiator' or request.answer in {c.id for c in p.components}: ops.append(Operation(op='update',entity=entity,id=d.target_id,value={d.field:request.answer}))
    c=command(p,ops);candidate=apply(p,c);c.operations.extend(question_ops(candidate))
    return store.commit(c)
