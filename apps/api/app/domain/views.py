"""Deterministic projections over canonical semantic IDs."""
from itertools import product
from .models import Project, Placement, Point, Route

_CLEARANCE=22.0
_SIDES=('left','right','top','bottom')
_VECTORS={'left':(-1,0),'right':(1,0),'top':(0,-1),'bottom':(0,1)}

def _center(node,by_id):
    x,y=node['x']+node['width']/2,node['y']+node['height']/2
    parent=by_id.get(node.get('parentId'))
    if parent:x+=parent['x'];y+=parent['y']
    return x,y

def _absolute_bounds(nodes):
    by_id={n['id']:n for n in nodes};bounds={}
    for ident,node in by_id.items():
        if node['role']=='zone':continue
        x,y=node['x'],node['y'];parent=by_id.get(node.get('parentId'))
        if parent:x+=parent['x'];y+=parent['y']
        bounds[ident]=(x,y,x+node['width'],y+node['height'])
    return bounds

def _anchor(box,side):
    x0,y0,x1,y1=box;side_y=y0+min(27,(y1-y0)/2)
    return {'left':(x0,side_y),'right':(x1,side_y),'top':((x0+x1)/2,y0),'bottom':((x0+x1)/2,y1)}[side]

def _outward(point,side):
    dx,dy=_VECTORS[side];return point[0]+dx*_CLEARANCE,point[1]+dy*_CLEARANCE

def _expanded(box):
    return box[0]-_CLEARANCE,box[1]-_CLEARANCE,box[2]+_CLEARANCE,box[3]+_CLEARANCE

def _inside(point,box):
    return box[0]<point[0]<box[2] and box[1]<point[1]<box[3]

def _segment_clear(first,last,obstacles):
    """Strict intersections leave a route free to follow an obstacle clearance edge."""
    if first[0]!=last[0] and first[1]!=last[1]:return False
    if first==last:return True
    for box in obstacles:
        if first[1]==last[1]:
            lo,hi=sorted((first[0],last[0]))
            if box[1]<first[1]<box[3] and lo<box[2] and hi>box[0]:return False
        else:
            lo,hi=sorted((first[1],last[1]))
            if box[0]<first[0]<box[2] and lo<box[3] and hi>box[1]:return False
    return True

def _simplify(points):
    result=[]
    for point in points:
        point=(round(point[0],3),round(point[1],3))
        if result and result[-1]==point:continue
        if len(result)>1:
            a,b=result[-2],result[-1]
            if (a[0]==b[0]==point[0] or a[1]==b[1]==point[1]):
                result.pop()
        result.append(point)
    return result

def _path_cost(points):
    return sum(abs(b[0]-a[0])+abs(b[1]-a[1]) for a,b in zip(points,points[1:]))+24*(len(points)-2)

def _core_path(start,end,obstacles):
    """Choose a short clear rectilinear lane; bounded for 50 components / 100 edges."""
    if any(_inside(start,box) for box in obstacles) or any(_inside(end,box) for box in obstacles):return None
    candidates=[[start,(end[0],start[1]),end],[start,(start[0],end[1]),end]]
    left=min(box[0] for box in obstacles)-_CLEARANCE;right=max(box[2] for box in obstacles)+_CLEARANCE
    top=min(box[1] for box in obstacles)-_CLEARANCE;bottom=max(box[3] for box in obstacles)+_CLEARANCE
    midpoint=((start[0]+end[0])/2,(start[1]+end[1])/2)
    xs=sorted({left,right,start[0],end[0],*(value for box in obstacles for value in (box[0],box[2]))},key=lambda value:(abs(value-midpoint[0]),value))
    ys=sorted({top,bottom,start[1],end[1],*(value for box in obstacles for value in (box[1],box[3]))},key=lambda value:(abs(value-midpoint[1]),value))
    # A single outside lane handles ordinary blocked elbows without growing a graph.
    for y in ys[:32]:candidates.append([start,(start[0],y),(end[0],y),end])
    for x in xs[:32]:candidates.append([start,(x,start[1]),(x,end[1]),end])
    # Two-lane detours cover boxes that block a source or target clearance leg.
    outer_x=tuple(dict.fromkeys((left,right,*xs[:8])))
    outer_y=tuple(dict.fromkeys((top,bottom,*ys[:8])))
    for x,y in product(outer_x,outer_y):
        candidates.append([start,(start[0],y),(x,y),(x,end[1]),end])
        candidates.append([start,(x,start[1]),(x,y),(end[0],y),end])
    clear=[]
    for candidate in candidates:
        path=_simplify(candidate)
        if all(_segment_clear(a,b,obstacles) for a,b in zip(path,path[1:])):clear.append(path)
    return min(clear,key=_path_cost) if clear else None

def _automatic_points(source,target,boxes,source_side,target_side):
    source_anchor,target_anchor=_anchor(boxes[source],source_side),_anchor(boxes[target],target_side)
    start,end=_outward(source_anchor,source_side),_outward(target_anchor,target_side)
    obstacles=[_expanded(box) for box in boxes.values()]
    # The handle's short outward segment may cross another component in a dense layout.
    source_obstacles=[_expanded(box) for ident,box in boxes.items() if ident!=source]
    target_obstacles=[_expanded(box) for ident,box in boxes.items() if ident!=target]
    if not _segment_clear(source_anchor,start,source_obstacles) or not _segment_clear(end,target_anchor,target_obstacles):return None
    core=_core_path(start,end,obstacles)
    if core is None:return None
    vertices=_simplify([source_anchor,*core,target_anchor])
    return [Point(x=x,y=y) for x,y in vertices[1:-1]]

def _preferred_sides(first,last):
    dx,dy=last[0]-first[0],last[1]-first[1]
    preferred=(('right','left') if dx>=0 else ('left','right')) if abs(dx)>=abs(dy) else (('bottom','top') if dy>=0 else ('top','bottom'))
    source=(preferred[0],*(side for side in _SIDES if side!=preferred[0]))
    target=(preferred[1],*(side for side in _SIDES if side!=preferred[1]))
    return source,target

def _safe_route(source,target,route,boxes,centers):
    """Derive an orthogonal route without mutating the canonical presentation model."""
    stored=route
    if stored and (stored.locked or stored.style=='straight' or (stored.points and not stored.automatic)):
        return stored
    if stored:
        source_sides,target_sides=(stored.source_handle,),(stored.target_handle,)
        base=stored
    else:
        source_sides,target_sides=_preferred_sides(centers[source],centers[target]);base=Route(automatic=True)
    for source_side,target_side in product(source_sides,target_sides):
        points=_automatic_points(source,target,boxes,source_side,target_side)
        if points is not None:
            return base.model_copy(update={'source_handle':source_side,'target_handle':target_side,'points':points,'automatic':True})
    # Retain the selected handles and a visible connector if no clearance path exists.
    return base.model_copy(update={'automatic':True,'points':[]})

def view_graph(p:Project,kind:str,*,route_edges=True):
    view=p.views[kind]; nodes=[]; edges=[]; mappings={}; member={}
    proposed_zones={c.target_id for c in p.claims if c.source_kind=='assistant_proposal' and c.field=='proposed_zoning' and c.review!='rejected'}
    def node(ident,label,asset,objects,parent=None,role='',default=None):
        place=view.placements.get(ident,default or Placement()); mappings[ident]=objects
        text=place.label or label
        if role=='zone' and ident in proposed_zones:text+=' (proposed)'
        if place.visible: nodes.append(dict(id=ident,label=text,asset_id=asset,object_ids=objects,parentId=parent,role=role,**place.model_dump(exclude={'label'})))
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
    # Automatic routes use absolute child positions and component clearance boxes. They are
    # presentation only; a locked route remains literal through layout changes and exports.
    by_id={n['id']:n for n in nodes};boxes=_absolute_bounds(nodes)
    centers={ident:_center(node,by_id) for ident,node in by_id.items() if ident in boxes}
    for edge in edges if route_edges else []:
        if edge['source'] in boxes and edge['target'] in boxes:
            edge['route']=_safe_route(edge['source'],edge['target'],edge['route'],boxes,centers)
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
        graph=view_graph(p,kind,route_edges=False); view.mappings=graph['mappings']
        # Fresh detailed views need compact placement even when deployment zones
        # are unspecified. The system overview already has its own grid defaults.
        # Reopening or adding to an existing view preserves saved geometry.
        if not view.placements and kind != 'sv1':
            from .layout import compact_geometry
            geometry=compact_geometry(graph['nodes'],graph['edges'])
            for n in graph['nodes']:n.update(geometry[n['id']])
        for n in graph['nodes']:
            if n['id'] not in view.placements: view.placements[n['id']]=Placement(**{k:n[k] for k in Placement.model_fields if k!='label'})
    return p

def arrange_plan(p:Project,kind:str,aspect_ratio=1.5):
    from .commands import command
    from .layout import compact_geometry,GEOMETRY,bounds
    graph=view_graph(p,kind,route_edges=False)
    geometry=compact_geometry(graph['nodes'],graph['edges'],aspect_ratio)
    operations=[];absolute=[]
    for node in graph['nodes']:
        value=geometry[node['id']]
        patch={key:value[key] for key in GEOMETRY if value[key]!=node[key]}
        if patch:operations.append(dict(op='placement',id=node['id'],view=kind,value=patch))
        parent=geometry.get(node.get('parentId'),{'x':0,'y':0})
        absolute.append(dict(value,x=value['x']+parent['x'],y=value['y']+parent['y']))
    for route in p.views[kind].routes.values():
        if route.locked or (route.points and not route.automatic):
            absolute.extend(dict(x=point.x,y=point.y,width=0,height=0) for point in route.points)
    return {'change':command(p,operations) if operations else None,'bounds':bounds(absolute)}

def narrative(p:Project):
    names={c.id:c.name for c in p.components}; zone_names={z.id:z.name for z in p.zones}
    deployments={d.component_id:d for d in p.deployments}
    proposed_zoning={c.target_id for c in p.claims if c.source_kind=='assistant_proposal' and c.field=='proposed_zoning' and c.review!='rejected'}
    lines=[f'# {p.name}', '', 'SYNTHETIC — DEMONSTRATION ONLY' if p.synthetic else 'User-supplied project',
           f'Accepted semantic revision: {p.revision}', '', '## Design at a glance',
           f'This design contains {len(p.components)} components and {len(p.interfaces)} connections. The sections below describe the accepted model; unspecified facts stay undecided.']
    if p.notes:lines+=['', '## Design notes', p.notes]
    lines+=['', '## What runs where']
    for c in p.components:
        d=deployments.get(c.id);zone=zone_names.get(d.zone_id,'an unspecified deployment zone') if d else 'an unspecified deployment zone'
        count=f'{d.quantity} declared instance'+('s' if d.quantity!=1 else '') if d and d.quantity is not None else 'instance count undecided'
        text=f'- {c.name} [{c.id}] is a {c.role.replace("_"," ")} in {zone}. Status: {c.status}; {count}.'
        if d and (d.id in proposed_zoning or d.zone_id in proposed_zoning):text+=' Zoning is an Archie design proposal, not a source-stated deployment or proof of implemented segmentation.'
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
