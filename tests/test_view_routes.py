from apps.api.app.domain.models import Project,Placement,Route
from apps.api.app.domain.views import view_graph
from apps.api.app.domain.commands import apply,command


def sample():
    p=Project(components=[{'id':'a','name':'A','role':'server'},{'id':'b','name':'B','role':'server'}],
              zones=[{'id':'zone','name':'Zone'}],deployments=[{'id':'deployment','component_id':'a','zone_id':'zone'}],
              interfaces=[{'id':'ab','source':'a','target':'b'}])
    p.views['logical'].placements={
        'zone':Placement(x=500,y=0,width=400,height=400),
        'a':Placement(x=10,y=20,width=100,height=80),
        'b':Placement(x=0,y=400,width=100,height=80)}
    return p


def test_automatic_handles_include_parent_position_without_mutating_model():
    p=sample();before=p.model_dump()
    route=view_graph(p,'logical')['edges'][0]['route']
    assert (route.source_handle,route.target_handle)==('left','right')
    assert p.model_dump()==before and not p.views['logical'].routes
    p.views['logical'].placements['b'].x=600
    route=view_graph(p,'logical')['edges'][0]['route']
    assert (route.source_handle,route.target_handle)==('bottom','top')


def test_explicit_handles_and_first_manual_edit_preserve_displayed_route():
    p=sample();p.views['logical'].placements['b'].x=600
    p=apply(p,command(p,[{'op':'route','id':'ab','value':{'points':[{'x':800,'y':200}],'locked':True}}]))
    route=p.views['logical'].routes['ab']
    assert (route.source_handle,route.target_handle)==('bottom','top')
    assert route.locked and route.points[0].x==800
    p.views['logical'].routes['ab']=Route(source_handle='top',target_handle='left')
    derived=view_graph(p,'logical')['edges'][0]['route']
    # Handle choices remain user-owned, while an unlocked empty route is recomputed
    # when another component or the target moves.
    assert (derived.source_handle,derived.target_handle)==('top','left')
    assert derived.automatic and derived.points
    assert not p.views['logical'].routes['ab'].automatic and not p.views['logical'].routes['ab'].points


def _crosses(first,last,box):
    x0,y0,x1,y1=box
    if first[1]==last[1]:
        lo,hi=sorted((first[0],last[0]))
        return y0<first[1]<y1 and lo<x1 and hi>x0
    lo,hi=sorted((first[1],last[1]))
    return x0<first[0]<x1 and lo<y1 and hi>y0


def test_automatic_routes_clear_unrelated_component_footprints_and_regenerate():
    p=Project(components=[{'id':'a','name':'A','role':'server'},
                          {'id':'blocker','name':'B','role':'server'},
                          {'id':'c','name':'C','role':'server'}],
              interfaces=[{'id':'ac','source':'a','target':'c'}])
    p.views['logical'].placements={
        'a':Placement(x=0,y=0,width=100,height=80),
        'blocker':Placement(x=190,y=-50,width=120,height=150),
        'c':Placement(x=400,y=0,width=100,height=80),
    }
    first=view_graph(p,'logical')['edges'][0]['route']
    vertices=[(100,27),*((point.x,point.y) for point in first.points),(400,27)]
    assert first.automatic and first.points
    assert not any(_crosses(a,b,(190,-50,310,100)) for a,b in zip(vertices,vertices[1:]))
    # A label-only edit must not freeze the generated clearance path.
    p=apply(p,command(p,[{'op':'route','id':'ac','value':{'label_offset':{'x':30,'y':-10}}}]))
    saved=p.views['logical'].routes['ac'];before=[point.model_dump() for point in saved.points]
    assert saved.automatic and saved.label_offset.model_dump()=={'x':30.0,'y':-10.0}
    p.views['logical'].placements['blocker'].y=160
    regenerated=view_graph(p,'logical')['edges'][0]['route']
    assert regenerated.automatic and regenerated.label_offset==saved.label_offset
    assert [point.model_dump() for point in regenerated.points]!=before


def test_new_external_components_do_not_share_default_position():
    from apps.api.app.domain.views import initialise_views
    p=Project(components=[{'id':'a','name':'A','role':'server'},{'id':'b','name':'B','role':'server'}])
    p=initialise_views(p)
    assert p.views['logical'].placements['a'].y!=p.views['logical'].placements['b'].y
    original=p.views['logical'].placements.copy()
    p=apply(p,command(p,[{'op':'add','entity':'components','id':'c','value':{'name':'C','role':'server'}}]))
    assert len({p.views['logical'].placements[key].y for key in ['a','b','c']})==3
    assert all(p.views['logical'].placements[key]==placement for key,placement in original.items())
