"""Deterministic projections over canonical semantic IDs."""
from .models import Project, Placement

def view_graph(p:Project,kind:str):
    view=p.views[kind]; nodes=[]; edges=[]; mappings={}; member={}
    def node(ident,label,asset,objects,parent=None,role='',default=None):
        place=view.placements.get(ident,default or Placement()); mappings[ident]=objects
        if place.visible: nodes.append(dict(id=ident,label=place.label or label,asset_id=asset,object_ids=objects,parentId=parent,role=role,**place.model_dump(exclude={'label'})))
    if kind=='sv1':
        groups={}
        for c in p.components: groups.setdefault(c.system_id or c.id,[]).append(c)
        for i,(ident,cs) in enumerate(groups.items()):
            system=next((s for s in p.systems if s.id==ident),None)
            label=(system.name+'\n' if system else '')+' · '.join(c.name for c in cs)
            node(ident,label,'system-boundary',[c.id for c in cs],role='system',default=Placement(x=70+i%3*300,y=90+i//3*230,width=240,height=125))
            for c in cs: member[c.id]=ident
        combined={}
        for e in p.interfaces:
            a,b=member[e.source],member[e.target]
            if a!=b: combined.setdefault((a,b),[]).append(e)
        for (a,b),items in combined.items():
            ident='aggregate:'+a+':'+b; mappings[ident]=[e.id for e in items]
            edges.append(dict(id=ident,source=a,target=b,label=' / '.join(dict.fromkeys(e.purpose or 'purpose ?' for e in items)),object_ids=mappings[ident],route=view.routes.get(ident),data_direction=items[0].data_direction if len({e.data_direction for e in items})==1 else 'unknown'))
    else:
        for i,z in enumerate(p.zones): node(z.id,z.name,'network-zone',[z.id],role='zone',default=Placement(x=40+i%2*580,y=60+i//2*400,width=530,height=350))
        counts={}
        for c in p.components:
            d=next((d for d in p.deployments if d.component_id==c.id),None); parent=d.zone_id if d else None
            i=counts.get(parent,0); counts[parent]=i+1
            node(c.id,c.name,c.asset_id,[c.id],parent,c.role,Placement(x=30+(i%2)*235 if parent else 1200,y=65+(i//2)*130,width=185,height=90))
        for e in p.interfaces:
            label=e.purpose or 'purpose ?'
            if kind=='sv2': label+=f' | {e.protocol or "protocol ?"}:{e.port if e.port is not None else "?"} | initiator: {e.initiator or "?"}'
            mappings[e.id]=[e.id]; edges.append(dict(id=e.id,source=e.source,target=e.target,label=label,object_ids=[e.id],route=view.routes.get(e.id),data_direction=e.data_direction))
    return {'type':kind,'semantic_revision':p.revision,'presentation_revision':view.revision,'nodes':nodes,'edges':edges,'mappings':mappings}

def initialise_views(p:Project):
    for kind,view in p.views.items():
        graph=view_graph(p,kind); view.mappings=graph['mappings']
        for n in graph['nodes']:
            if n['id'] not in view.placements: view.placements[n['id']]=Placement(**{k:n[k] for k in Placement.model_fields if k!='label'})
    return p

def narrative(p:Project):
    names={c.id:c.name for c in p.components}
    lines=[f'# {p.name}', '', 'SYNTHETIC — DEMONSTRATION ONLY' if p.synthetic else 'User-supplied project',f'Accepted semantic revision: {p.revision}', '', '## Scope and responsibilities']
    for c in p.components:
        d=next((d for d in p.deployments if d.component_id==c.id),None)
        lines.append(f'- [{c.id}] {c.name}: {c.role}; {c.status}; zone {d.zone_id if d and d.zone_id else "unspecified"}; quantity {d.quantity if d and d.quantity is not None else "undecided"}. Evidence: {", ".join(c.evidence) or "manual / proposed"}.')
    lines+=['','## Interfaces and session initiation']
    for e in p.interfaces: lines.append(f'- [{e.id}] {names[e.source]} → {names[e.target]}: {e.purpose or "purpose undecided"}; flow {e.data_direction}; initiator {names.get(e.initiator,"undecided")}; protocol {e.protocol or "undecided"}; port {e.port if e.port is not None else "undecided"}; enforcement {", ".join(e.enforcement) or "unspecified"}.')
    lines+=['','## Constraints and open decisions']
    for c in p.constraints: lines.append(f'- {c.key}: {c.value if c.value is not None else "undecided"}')
    for d in p.decisions: lines.append(f'- {d.question}: {d.answer or "Not decided"}')
    lines+=['','## Sources']
    for c in p.claims: lines.append(f'- [{c.id}] {c.review}: {c.source_id} v{c.source_version}, {c.locator}: {c.excerpt}')
    lines+=['','## Authored notes',p.notes or '(none)']
    return '\n'.join(lines)
