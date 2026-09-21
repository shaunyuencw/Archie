"""Reviewed predicates selected by project applicability, independently of retrieval."""
import re,sqlite3
from .library import clauses, selected_ids

def zone_tier(zone):
    """Recognise explicit tier labels, optionally under a known demo boundary."""
    boundaries={'production','prod','testbed','test','aws'}
    tiers={'client','z1','z2'}
    matches=set()
    # IDs must be a complete tier ID, with at most one known boundary prefix.
    id_parts=re.split(r'[-_]',zone.id.strip().lower())
    if len(id_parts)==1 and id_parts[0] in tiers:matches.add(id_parts[0])
    elif len(id_parts)==2 and id_parts[0] in boundaries and id_parts[1] in tiers:matches.add(id_parts[1])
    # Names use delimited labels, not free-text occurrences such as "Client support".
    name_parts=[part.strip().lower() for part in re.split(r'[·:/]|\s+[—–-]\s+',zone.name)]
    if name_parts[0] in tiers:matches.add(name_parts[0])
    elif len(name_parts)>1 and name_parts[0] in boundaries and name_parts[1] in tiers:matches.add(name_parts[1])
    return next(iter(matches)) if len(matches)==1 else None

def lookup(query,limit=3,policy_ids=None):
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE VIRTUAL TABLE policy USING fts5(id UNINDEXED,text,tags)')
        allowed=None if policy_ids is None else set(policy_ids)
        rows=[c for c in clauses() if allowed is None or c['id'] in allowed]
        db.executemany('INSERT INTO policy VALUES(?,?,?)',[(c['id'],c['text'],' '.join(c['tags'])) for c in rows])
        words=re.findall(r'[a-zA-Z0-9]+',query)[:20]
        if not words:return []
        ids=[r[0] for r in db.execute('SELECT id FROM policy WHERE policy MATCH ? ORDER BY rank LIMIT ?',(' OR '.join('"'+w+'"' for w in words),min(limit,5)))]
        return [next(c for c in rows if c['id']==i) for i in ids]

def evaluate(p):
    c={x.id:x for x in p.components}; zones={x.component_id:x.zone_id for x in p.deployments}
    constraints={x.key:x.value for x in p.constraints}; results=[]
    library={clause['id']:clause for clause in clauses()}; selected=selected_ids(p)
    def tier(component_id):
        zone=next((z for z in p.zones if z.id==zones.get(component_id)),None)
        if not zone: return None
        return zone_tier(zone)
    def add(rule,issues,applicable=True):
        if rule not in selected:return
        clause=library[rule]
        severity={'pass':0,'not_applicable':0,'insufficient_information':1,'potential_conflict':2}
        result=max((x[0] for x in issues),key=severity.get) if issues else ('pass' if applicable else 'not_applicable')
        affected=list(dict.fromkeys(ident for _,ids,_ in issues for ident in ids))
        evidence=list(dict.fromkeys(e for ident in affected for e in getattr(c.get(ident) or next((i for i in p.interfaces if i.id==ident),None) or next((i for i in p.constraints if i.id==ident),None),'evidence',[])))
        results.append(dict(clause_id=rule,title=clause['title'],version='1.0',execution='implemented',result=result,affected_ids=affected,evidence=evidence,message='; '.join(msg for _,_,msg in issues) or ('Predicate passed on supplied facts.' if applicable else 'Requirement is not applicable.'),clause=clause['text']))
    add('DEMO-ZON-01',[('insufficient_information',[x.id],'Deployment zone or internal/external scope is unspecified.') for x in p.components if x.scope=='unknown' or (x.scope=='internal' and not zones.get(x.id))],bool(p.components))
    issues=[]
    for i in p.interfaces:
        if tier(i.source)=='client' or c[i.source].asset_id=='workstation':
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
    issues=[]
    for i in p.interfaces:
        tiers={tier(i.source),tier(i.target)}
        if tiers=={'client','z2'}:
            issues.append(('potential_conflict',[i.id,i.source,i.target],'A direct Client–Z2 interface bypasses the Z1 entry point.'))
        elif 'client' in tiers and None in tiers:
            issues.append(('insufficient_information',[i.id],'The peer tier for this Client interface is not declared as Client, Z1 or Z2.'))
    add('ARCH-SEG-01',issues,any(tier(i.source)=='client' or tier(i.target)=='client' for i in p.interfaces))
    databases=[x for x in p.components if x.asset_id in {'database','aws-rds','aws-dynamodb'} and x.scope!='external']
    add('ARCH-DAT-01',[(('insufficient_information' if tier(x.id) is None else 'potential_conflict'),[x.id],
        'Database tier is unspecified; declare its protected placement.' if tier(x.id) is None else 'Database is outside the protected Z2 tier.') for x in databases if tier(x.id)!='z2'],bool(databases))
    issues=[];applicable=False
    for i in p.interfaces:
        source_zone,target_zone=zones.get(i.source),zones.get(i.target)
        if not source_zone or not target_zone:
            applicable=True
            issues.append(('insufficient_information',[i.id],'Session zoning is unknown; cross-zone enforcement cannot be assessed.'))
        elif source_zone!=target_zone:
            applicable=True
            if not i.enforcement:issues.append(('insufficient_information',[i.id],'Cross-zone session has no explicit enforcement reference.'))
    add('ARCH-FLW-01',issues,applicable)
    results.extend(dict(clause_id=c['id'],title=c['title'],version=c['version'],execution='manual_review',result=None,affected_ids=[],evidence=[],message=c['text'],clause=c['text']) for c in library.values() if c['id'] in selected and c['implementation']=='manual_review')
    # Imported projects may reference a local draft that is not on this machine.
    results.extend(dict(clause_id=ident,version=None,execution='error',result='insufficient_information',affected_ids=[],evidence=[],message='Selected policy is missing from the local library. Recreate or deselect it before review.',clause='Unavailable local policy') for ident in selected if ident not in library)
    return {'revision':p.revision,'selected':len(selected),'available':len(library),
            'implemented':sum(f['execution']=='implemented' for f in results),
            'manual_review':sum(f['execution']=='manual_review' for f in results),'findings':results}
