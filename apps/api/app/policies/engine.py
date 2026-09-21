"""Eight reviewed predicates. Retrieval never controls check coverage."""
import json,re,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def clauses(): return json.loads((ROOT/'fixtures/policies/clauses.json').read_text(encoding='utf-8'))['clauses']

def lookup(query,limit=3):
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE VIRTUAL TABLE policy USING fts5(id UNINDEXED,text,tags)')
        rows=clauses(); db.executemany('INSERT INTO policy VALUES(?,?,?)',[(c['id'],c['text'],' '.join(c['tags'])) for c in rows])
        words=re.findall(r'[a-zA-Z0-9]+',query)[:20]
        if not words:return []
        ids=[r[0] for r in db.execute('SELECT id FROM policy WHERE policy MATCH ? ORDER BY rank LIMIT ?',(' OR '.join('"'+w+'"' for w in words),min(limit,5)))]
        return [next(c for c in rows if c['id']==i) for i in ids]

def evaluate(p):
    c={x.id:x for x in p.components}; zones={x.component_id:x.zone_id for x in p.deployments}
    constraints={x.key:x.value for x in p.constraints}; results=[]
    def add(rule,issues,applicable=True):
        clause=next(x for x in clauses() if x['id']==rule)
        severity={'pass':0,'not_applicable':0,'insufficient_information':1,'potential_conflict':2}
        result=max((x[0] for x in issues),key=severity.get) if issues else ('pass' if applicable else 'not_applicable')
        affected=list(dict.fromkeys(ident for _,ids,_ in issues for ident in ids))
        evidence=list(dict.fromkeys(e for ident in affected for e in getattr(c.get(ident) or next((i for i in p.interfaces if i.id==ident),None) or next((i for i in p.constraints if i.id==ident),None),'evidence',[])))
        results.append(dict(clause_id=rule,version='1.0',execution='implemented',result=result,affected_ids=affected,evidence=evidence,message='; '.join(msg for _,_,msg in issues) or ('Predicate passed on supplied facts.' if applicable else 'Requirement is not applicable.'),clause=clause['text']))
    add('DEMO-ZON-01',[('insufficient_information',[x.id],'Deployment zone is unspecified.') for x in p.components if x.scope=='internal' and not zones.get(x.id)],bool(p.components))
    issues=[]
    for i in p.interfaces:
        if zones.get(i.source)=='client' or c[i.source].asset_id=='workstation':
            if not i.purpose: issues.append(('insufficient_information',[i.id],'Client interface purpose is unspecified.'))
            elif i.purpose=='management' and 'management' not in c[i.target].role: issues.append(('potential_conflict',[i.id,i.target],'Client management targets a processing function rather than the declared management interface.'))
    add('DEMO-ADM-01',issues,bool(p.interfaces))
    issues=[]
    for i in p.interfaces:
        if i.purpose=='management':
            if not zones.get(i.source) or not zones.get(i.target): issues.append(('insufficient_information',[i.id],'Session zoning is unknown.'))
            elif zones[i.source]!=zones[i.target] and not i.enforcement: issues.append(('insufficient_information',[i.id],'Cross-zone management has no explicit enforcement reference.'))
    add('DEMO-FW-01',issues,any(i.purpose=='management' for i in p.interfaces))
    internet=[x.id for x in p.components if x.internet_hosted is True and any(i.target==x.id for i in p.interfaces)]
    add('DEMO-NET-01',[('potential_conflict',internet+[x.id for x in p.constraints if x.key=='no_internet'],'Required internet dependency contradicts the no-internet constraint.')] if constraints.get('no_internet') is True and internet else [],constraints.get('no_internet') is True)
    add('DEMO-IF-01',[('insufficient_information',[i.id],'Session initiator or protocol is unspecified.') for i in p.interfaces if i.initiator is None or not i.protocol],bool(p.interfaces))
    strategy=constraints.get('availability_strategy'); required=constraints.get('resilience_required') is True
    add('DEMO-HA-01',([('insufficient_information',[x.id for x in p.constraints if x.key=='resilience_required'],'No availability strategy supplied.')] if not strategy else [('potential_conflict',[x.id for x in p.constraints if x.key in ['resilience_required','availability_strategy']],'Single-instance design conflicts with resilience requirement.')] if 'single_instance' in str(strategy) else []) if required else [],required)
    management=[x for x in p.components if 'management' in x.role]
    add('DEMO-AUD-01',[('insufficient_information',[x.id],'Management function has no audit destination.') for x in management if not x.audit_destination],bool(management))
    issues=[]
    for x in p.components:
        if x.local_only:
            if not x.storage_destination: issues.append(('insufficient_information',[x.id],'Local-only data has no known storage destination.'))
            elif c[x.storage_destination].scope=='external': issues.append(('potential_conflict',[x.id,x.storage_destination],'Local-only data is assigned external storage.'))
    add('DEMO-DAT-01',issues,any(x.local_only for x in p.components))
    results.extend(dict(clause_id=c['id'],version=c['version'],execution='manual_review',result=None,affected_ids=[],evidence=[],message=c['text'],clause=c['text']) for c in clauses() if c['implementation']=='manual_review')
    return {'revision':p.revision,'implemented':8,'manual_review':12,'findings':results}
