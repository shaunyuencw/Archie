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
    assert view_graph(p,'logical')['edges'][0]['route']==p.views['logical'].routes['ab']


def test_new_external_components_do_not_share_default_position():
    from apps.api.app.domain.views import initialise_views
    p=Project(components=[{'id':'a','name':'A','role':'server'},{'id':'b','name':'B','role':'server'}])
    p=initialise_views(p)
    assert p.views['logical'].placements['a'].y!=p.views['logical'].placements['b'].y
    original=p.views['logical'].placements.copy()
    p=apply(p,command(p,[{'op':'add','entity':'components','id':'c','value':{'name':'C','role':'server'}}]))
    assert len({p.views['logical'].placements[key].y for key in ['a','b','c']})==3
    assert all(p.views['logical'].placements[key]==placement for key,placement in original.items())
