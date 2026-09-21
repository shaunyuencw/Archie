"""Deterministic projections over canonical semantic IDs."""
from .models import Project, Placement, Route

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
            node(c.id,c.name,c.asset_id,[c.id],parent,c.role,Placement(x=30+(i%2)*235 if parent else 1200,y=65+(i//2 if parent else i)*130,width=185,height=90))
        for e in p.interfaces:
            label=e.purpose or 'purpose ?'
            if kind=='sv2': label+=f' | {e.protocol or "protocol ?"}:{e.port if e.port is not None else "?"} | initiator: {e.initiator or "?"}'
            mappings[e.id]=[e.id]; edges.append(dict(id=e.id,source=e.source,target=e.target,label=label,object_ids=[e.id],route=view.routes.get(e.id),data_direction=e.data_direction))
    # Unrouted connections face the other component using absolute, zone-aware positions.
    # This is derived presentation only; a user's persisted handle choice takes precedence.
    by_id={n['id']:n for n in nodes}
    def center(n):
        x,y=n['x']+n['width']/2,n['y']+n['height']/2
        parent=by_id.get(n.get('parentId'))
        if parent: x+=parent['x']; y+=parent['y']
        return x,y
    for edge in edges:
        if edge['route'] is not None or edge['source'] not in by_id or edge['target'] not in by_id: continue
        ax,ay=center(by_id[edge['source']]); bx,by=center(by_id[edge['target']])
        dx,dy=bx-ax,by-ay
        source,target=(('right','left') if dx>=0 else ('left','right')) if abs(dx)>=abs(dy) else (('bottom','top') if dy>=0 else ('top','bottom'))
        edge['route']=Route(source_handle=source,target_handle=target)
    components={c.id:c for c in p.components}; deployments={d.component_id:d for d in p.deployments}
    for n in nodes:
        component=components.get(n['id'])
        if component is None and len(n['object_ids'])==1: component=components.get(n['object_ids'][0])
        if component:
            deployment=deployments.get(component.id)
            n.update(quantity=deployment.quantity if deployment else None,
                     redundancy_mode=deployment.redundancy_mode if deployment else 'unknown',
                     form_factor=component.form_factor,
                     hosted_controls=[{'id':c.id,'name':c.name,'asset_id':c.asset_id} for c in p.components
                                      if c.asset_id=='virtual-firewall' and deployments.get(c.id)
                                      and deployments[c.id].host_component_id==component.id])
    return {'type':kind,'semantic_revision':p.revision,'presentation_revision':view.revision,'nodes':nodes,'edges':edges,'mappings':mappings}

def initialise_views(p:Project):
    for kind,view in p.views.items():
        graph=view_graph(p,kind); view.mappings=graph['mappings']
        for n in graph['nodes']:
            if n['id'] not in view.placements: view.placements[n['id']]=Placement(**{k:n[k] for k in Placement.model_fields if k!='label'})
    return p

def narrative(p:Project):
    names={c.id:c.name for c in p.components}; zone_names={z.id:z.name for z in p.zones}
    deployments={d.component_id:d for d in p.deployments}
    lines=[f'# {p.name}', '', 'SYNTHETIC — DEMONSTRATION ONLY' if p.synthetic else 'User-supplied project',
           f'Accepted semantic revision: {p.revision}', '', '## Design at a glance',
           f'This design contains {len(p.components)} components and {len(p.interfaces)} connections. The sections below describe the accepted model; unspecified facts stay undecided.']
    if p.notes:lines+=['', '## Design notes', p.notes]
    lines+=['', '## What runs where']
    for c in p.components:
        d=deployments.get(c.id);zone=zone_names.get(d.zone_id,'an unspecified deployment zone') if d else 'an unspecified deployment zone'
        count=f'{d.quantity} declared instance'+('s' if d.quantity!=1 else '') if d and d.quantity is not None else 'instance count undecided'
        text=f'- {c.name} [{c.id}] is a {c.role.replace("_"," ")} in {zone}. Status: {c.status}; {count}.'
        if d and d.redundancy_mode!='unknown':text+=f' Redundancy: {d.redundancy_mode.replace("_"," ")}.'
        if c.form_factor!='unknown':text+=f' Form: {c.form_factor}.'
        if d and d.host_component_id:text+=f' Runs on {names[d.host_component_id]}.'
        lines.append(text)
    lines+=['', '## Connections']
    for i in p.interfaces:
        purpose=i.purpose or 'purpose undecided'
        protocol=i.protocol or 'protocol undecided'
        port=f'port {i.port}' if i.port is not None else 'port undecided'
        starter=f'{names[i.initiator]} starts the session' if i.initiator else 'the session initiator is undecided'
        control=', '.join(names.get(ident,ident) for ident in i.enforcement) or 'not recorded'
        lines.append(f'- {names[i.source]} → {names[i.target]} [{i.id}]: {purpose}, using {protocol} ({port}); {starter}. Data flow: {i.data_direction.replace("_"," ")}. Enforcement: {control}.')
    lines+=['', '## Requirements and open decisions']
    for c in p.constraints:lines.append(f'- {c.key.replace("_"," ")}: {c.value if c.value is not None else "undecided"}.')
    for d in p.decisions:lines.append(f'- {d.question} {d.answer or "Not decided."}')
    if not p.constraints and not p.decisions:lines.append('No requirements or clarification questions are recorded yet. This is not confirmation that the design is complete.')
    lines+=['', '## Sources and review trail']
    sources={s.id:s for s in p.sources}
    for c in p.claims:
        source=sources[c.source_id]
        lines.append(f'- [{c.id}] {c.review} — {source.name}, version {c.source_version}, {c.locator}: {c.excerpt}')
    if not p.claims:lines.append('No source-linked claims are recorded. The current design may contain manual or proposed edits.')
    lines+=['', 'Policy checks and synthetic examples do not constitute organisational approval.']
    return '\n'.join(lines)
