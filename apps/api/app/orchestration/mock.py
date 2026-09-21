"""A transparent deterministic parser for authored fixtures and narrow prompt edits.
It never retrieves eval answers. Unknown natural language requests fail explicitly.
"""
import json,re
from ..domain.models import Claim,Operation,uid,Source

TYPES={'System':'systems','Zone':'zones','Component':'components','Interface':'interfaces','Constraint':'constraints'}
MARKER=re.compile(r'\b(System|Zone|Component|Interface|Constraint)\s+([\w-]+):\s*')
FIELD=re.compile(r'(\w+)\s*=\s*(.*?)(?=;\s*\w+\s*=|$)',re.S)

def records(source,passages):
    found=[]
    for passage in passages:
        matches=list(MARKER.finditer(passage.text))
        for i,m in enumerate(matches):
            excerpt=passage.text[m.start():matches[i+1].start() if i+1<len(matches) else len(passage.text)].strip()
            # PDF table extraction may append an ID or review footer after the final value.
            body=excerpt[m.end()-m.start():]; values={}
            for field in FIELD.finditer(body):
                raw=' '.join(field[2].split())
                try: value,_=json.JSONDecoder().raw_decode(raw)
                except ValueError: continue
                values[field[1]]=value
            if values: found.append((TYPES[m[1]],m[2],values,passage,excerpt))
    return found

def natural_records(source,passages):
    result=[]
    for p in passages:
        text=p.text
        specs=[('vms','VMS','video management','application',r'VMS','Infrastructure','vms-system'),('management','VAP management','management integration','api-service',r'VAP management','Z1','vap-system'),('analytics','VAP analytics','analytics','analytics-engine',r'VAP analytics','Z2','vap-system'),('c2','C2','external command system','external-system',r'C2',None,'c2-system')]
        for ident,name,role,asset,pattern,zone,system in specs:
            if not re.search(pattern,text,re.I): continue
            # A default zone is accepted only when named in the same clause.
            clause=next((s for s in re.split(r'[;.\n]',text) if re.search(pattern,s,re.I)),text)
            zone_id=zone.lower() if zone and re.search(r'\b'+zone+r'\b',clause,re.I) else None
            result.append(('systems',system,{'name':system.split('-')[0].upper(),'scope':'external' if ident=='c2' else 'internal'},p,clause.strip()))
            if zone_id: result.append(('zones',zone_id,{'name':zone},p,clause.strip()))
            result.append(('components',ident,{'name':name,'role':role,'asset_id':asset,'system_id':system,'zone_id':zone_id,'scope':'external' if ident=='c2' else 'internal','status':'existing' if re.search('existing',clause,re.I) else 'proposed'},p,clause.strip()))
        if re.search(r'(two|2) workstations',text,re.I):
            clause=next(s for s in re.split(r'[;.\n]',text) if re.search('workstations',s,re.I))
            zone='client' if 'client' in clause.lower() else None
            if zone: result.append(('zones',zone,{'name':'Client'},p,clause.strip()))
            for i in range(1,3): result.append(('components',f'workstation-{i}',{'name':f'Workstation {i}','role':'workstation','asset_id':'workstation','zone_id':zone,'quantity':1},p,clause.strip()))
    return result

def extract(source,passages,project):
    rows=records(source,passages) or (natural_records(source,passages) if source.kind=='prompt' else [])
    operations=[]; claims=[]; staged=set(); existing={x.id for group in TYPES.values() for x in getattr(project,group)}
    for entity,ident,values,passage,excerpt in rows:
        if (entity,ident) in staged: continue
        staged.add((entity,ident))
        claim=Claim(id=uid(),source_id=source.id,source_version=source.version,locator=passage.locator,excerpt=excerpt,target_id=ident,field='record',value=values,source_kind=source.kind)
        previous=[c for c in project.claims if c.target_id==ident and c.field=='record']
        if any(c.value!=values for c in previous): claim.review='conflicting'
        claims.append(claim)
        if ident in existing: continue # Preserve both claims; never silently replace source facts.
        clean=dict(values)
        if entity=='components':
            zone=clean.pop('zone_id',None); quantity=clean.pop('quantity',None)
            operations.append(Operation(op='add',entity='deployments',id='deployment-'+ident,value={'component_id':ident,'zone_id':zone,'quantity':quantity}))
        if entity in ('components','interfaces','constraints'): clean['evidence']=[claim.id]
        operations.append(Operation(op='add',entity=entity,id=ident,value=clean))
    return claims,operations

def edit(prompt,project,source):
    passage=source.passages[0]; operations=[]; claim_id=uid()
    match=re.search(r'add\s+(?:one|a|1)\s+(configuration\s+)?workstation',prompt,re.I)
    if match:
        ident='tmp:'+uid(); name='Configuration workstation' if match[1] else 'Workstation'
        operations=[Operation(op='add',entity='components',id=ident,value={'name':name,'role':'configuration' if match[1] else 'workstation','asset_id':'workstation','evidence':[claim_id]}),Operation(op='add',entity='deployments',id='tmp:'+uid(),value={'component_id':ident,'zone_id':None,'quantity':1})]
    else:
        match=re.search(r'rename\s+(.+?)\s+to\s+(.+?)[.!]?$',prompt,re.I)
        if match:
            c=next((c for c in project.components if c.name.lower()==match[1].strip('"').lower()),None)
            if c: ident=c.id; operations=[Operation(op='update',entity='components',id=ident,value={'name':match[2].strip('"')})]
    if not operations: return [],[]
    claim=Claim(id=claim_id,source_id=source.id,source_version=source.version,locator=passage.locator,excerpt=passage.text,target_id=ident,field='proposed_change',value=prompt,source_kind='prompt')
    return [claim],operations
