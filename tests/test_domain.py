import pytest
from pydantic import ValidationError
from apps.api.app.domain.models import Placement,Project,Route
from apps.api.app.domain.commands import apply,command,DomainError
from apps.api.app.storage.store import Store

def test_transaction_and_revisions(tmp_path):
    store=Store(tmp_path/'db.sqlite'); p=store.create(Project())
    c=command(p,[{'op':'add','entity':'components','id':'a','value':{'name':'A','role':'server'}}])
    p=store.commit(c); assert p.revision==1
    assert store.commit(c)==p
    drag=command(p,[{'op':'placement','id':'a','value':{'x':99}}]); moved=store.commit(drag)
    assert moved.revision==1 and moved.views['logical'].revision==1
    with pytest.raises(DomainError): store.commit(command(p,[{'op':'notes','value':{'text':'stale'}}]))
    with pytest.raises(DomainError): store.commit(command(moved,[{'op':'add','entity':'interfaces','id':'bad','value':{'source':'a','target':'missing'}}]))
    assert store.get(p.id)==moved
    undone=store.undo(command(moved,[{'op':'notes','value':{}}])); assert undone.views['logical'].placements['a'].x!=99

def test_temp_id_resolution_and_unknown():
    p=Project()
    p=apply(p,command(p,[{'op':'add','entity':'components','id':'tmp:a','value':{'name':'A','role':'application'}},{'op':'add','entity':'deployments','id':'tmp:d','value':{'component_id':'tmp:a'}}]))
    assert p.deployments[0].component_id==p.components[0].id
    assert p.deployments[0].quantity is None

def test_interface_port_validation_is_human_readable_and_keeps_project_unchanged():
    p=Project()
    p=apply(p,command(p,[
        {'op':'add','entity':'components','id':'web','value':{'name':'Web service','role':'application'}},
        {'op':'add','entity':'components','id':'database','value':{'name':'Database','role':'database'}},
    ]))
    with pytest.raises(DomainError) as failure:
        apply(p,command(p,[
            {'op':'add','entity':'interfaces','id':'web-to-db','value':{'source':'web','target':'database','protocol':'HTTPS','port':'TCP 443'}},
            {'op':'add','entity':'interfaces','id':'db-to-web','value':{'source':'database','target':'web','protocol':'PostgreSQL','port':'TCP 5432'}},
        ]))
    assert failure.value.code=='invalid_input'
    assert failure.value.message=='2 connection ports could not be read: “TCP 443”, “TCP 5432”. Enter only a number from 0 to 65535 in Port, for example 443; put the protocol, such as HTTPS or PostgreSQL, in Protocol. Your current design was not changed.'
    assert not p.interfaces


def test_presentation_colors_are_hex_only_and_do_not_change_semantic_revision():
    placement=Placement(fill_color=' #0F766E ',text_color='#abc',border_color='#11223344',icon_color='#d43')
    route=Route(line_color='#2563EB',text_color='#654321')
    assert placement.fill_color=='#0f766e' and placement.text_color=='#abc'
    assert route.line_color=='#2563eb'
    with pytest.raises(ValidationError): Placement(fill_color='rgb(1, 2, 3)')
    with pytest.raises(ValidationError): Route(text_color='url(javascript:alert(1))')
    p=Project(components=[{'id':'a','name':'A','role':'server'}]);before=p.revision
    p=apply(p,command(p,[{'op':'placement','id':'a','value':{'fill_color':'#123456','icon_color':'#0f766e','z_index':4}}]))
    assert p.revision==before and p.views['logical'].revision==1
    assert p.views['logical'].placements['a'].fill_color=='#123456'
    assert p.views['logical'].placements['a'].z_index==4

def test_host_and_redundancy_validation_and_transaction_undo(tmp_path):
    store=Store(tmp_path/'deployment.sqlite');p=store.create(Project())
    p=store.commit(command(p,[
        {'op':'add','entity':'components','id':'tmp:host','value':{'name':'Host','role':'server'}},
        {'op':'add','entity':'components','id':'tmp:fw','value':{'name':'Firewall','role':'firewall','asset_id':'virtual-firewall','form_factor':'virtual'}},
        {'op':'add','entity':'deployments','id':'tmp:d','value':{'component_id':'tmp:fw','host_component_id':'tmp:host','quantity':2,'redundancy_mode':'active_passive'}},
    ]))
    host,fw=p.components;deployment=p.deployments[0]
    assert deployment.host_component_id==host.id and deployment.component_id==fw.id
    with pytest.raises(DomainError,match='at least two'):
        store.commit(command(p,[{'op':'update','entity':'deployments','id':deployment.id,'value':{'quantity':1}}]))
    with pytest.raises(DomainError,match='host itself'):
        store.commit(command(p,[{'op':'update','entity':'deployments','id':deployment.id,'value':{'host_component_id':fw.id}}]))
    with pytest.raises(DomainError,match='cycle'):
        store.commit(command(p,[{'op':'add','entity':'deployments','id':'dh','value':{'component_id':host.id,'host_component_id':fw.id}}]))
    assert store.get(p.id)==p
    p=store.commit(command(p,[{'op':'remove','entity':'components','id':host.id,'confirmed':True}]))
    assert p.deployments[0].host_component_id is None
    p=store.undo(command(p,[{'op':'notes','value':{}}]))
    assert p.deployments[0].host_component_id==host.id and p.deployments[0].redundancy_mode=='active_passive'

def test_redo_restores_layout_and_rejects_stale_or_abandoned_branch(tmp_path):
    store=Store(tmp_path/'history.sqlite'); p=store.create(Project())
    p=store.commit(command(p,[{'op':'add','entity':'components','id':'a','value':{'name':'A','role':'server'}}]))
    p=store.commit(command(p,[{'op':'placement','id':'a','value':{'x':123,'locked':True}}]))
    old=p
    p=store.undo(command(p,[{'op':'notes','value':{}}]))
    p=store.undo(command(p,[{'op':'notes','value':{}}]))
    assert not p.components
    with pytest.raises(DomainError): store.redo(command(old,[{'op':'notes','value':{}}]))
    p=store.redo(command(p,[{'op':'notes','value':{}}]))
    assert len(p.components)==1
    p=store.redo(command(p,[{'op':'notes','value':{}}]))
    assert p.views['logical'].placements['a'].x==123 and p.revision>old.revision
    p=store.undo(command(p,[{'op':'notes','value':{}}]))
    p=store.commit(command(p,[{'op':'update','entity':'components','id':'a','value':{'name':'Branched'}}]))
    with pytest.raises(DomainError,match='Nothing to redo'): store.redo(command(p,[{'op':'notes','value':{}}]))
    p=store.undo(command(p,[{'op':'notes','value':{}}]))
    assert p.components[0].name=='A'
