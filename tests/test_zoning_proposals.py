"""Zoning draft contract: source facts, explicit assumptions and local layout."""
import json

import pytest

from apps.api.app.domain.commands import DomainError, apply, command
from apps.api.app.domain.models import Project, Source, Passage, Route
from apps.api.app.domain.views import initialise_views, narrative, view_graph
from apps.api.app.exports.service import svg
from apps.api.app.orchestration.live import context, proposal_from_envelope, assisted_run
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.orchestration.zoning import supporting_sources
from apps.api.app.main import RunRequest
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope, ProviderResult, Usage, schema
from apps.api.app.storage.store import Store


TEXT = 'Cyber segmentation is required. Control runs in the Protected application zone. Analytics runs in the Analytics compute zone.'


def source():
    return Source(id='spec', name='Synthetic deployment specification', kind='document',
                  sha256='zoning', canonical_id='zoning', processed=['page/5'],
                  passages=[Passage(locator='page/5', text=TEXT)])


def project(count=20):
    return initialise_views(Project(systems=[dict(id='internal', name='Control', scope='internal'),
                                            dict(id='external', name='External facilities', scope='external')],
        components=[dict(id=f'c{i}', name=f'Service {i}', role='application',
                         system_id='internal' if i<count-1 else 'external') for i in range(count)],
        interfaces=[dict(id=f'e{i}', source=f'c{i}', target=f'c{i+1}') for i in range(count-1)]))


def envelope(inferred=False, members=range(3)):
    operations=[dict(op='add', entity='zones', id='tmp:zone',
                     value_json=json.dumps({'name':'Protected application zone'}),
                     proposal_reason='Separate application processing from other trust domains.' if inferred else None)]
    operations += [dict(op='add', entity='deployments', id=f'tmp:d{i}',
                        value_json=json.dumps({'component_id':f'c{i}', 'zone_id':'tmp:zone'}),
                        proposal_reason='Place this service with application processing pending review.' if inferred else None)
                   for i in members]
    return Envelope(operations=operations,
        claims=[dict(source_id='S1', locator='page/5', excerpt=TEXT,
                     target_id=op['id'], field='record', value_json='null') for op in operations],
        tool=None, message='Review the zoning design.')


def assert_inside(p):
    for kind in ('logical','sv2'):
        nodes={n['id']:n for n in view_graph(p,kind,route_edges=False)['nodes']}
        for n in nodes.values():
            if n['parentId']:
                parent=nodes[n['parentId']]
                assert n['x']>=24 and n['y']>=64
                assert n['x']+n['width']<=parent['width']-24
                assert n['y']+n['height']<=parent['height']-24


@pytest.mark.parametrize('inferred', [False, True])
def test_zoning_preview_accept_reopen_and_undo_preserve_facts_and_unrelated_layout(tmp_path,inferred):
    store=Store(tmp_path/'zoning.sqlite');before=store.create(project())
    draft=store.preview(proposal_from_envelope(before,source(),envelope(inferred),source_alias='S1'))
    assert store.get(before.id)==before
    accepted=store.commit(draft)
    assert len(accepted.zones)==1 and len(accepted.deployments)==3
    assert accepted.components==before.components and accepted.interfaces==before.interfaces
    assert all(d.quantity is None and d.host_component_id is None for d in accepted.deployments)
    assert accepted.views['sv1']==before.views['sv1']
    for kind in ('logical','sv2'):
        for i in range(3,20):
            assert accepted.views[kind].placements[f'c{i}']==before.views[kind].placements[f'c{i}']
    assert_inside(accepted)
    assumptions=[c for c in accepted.claims if c.source_kind=='assistant_proposal']
    assert len(assumptions)==(4 if inferred else 0)
    if inferred:
        assert all(c.review=='unreviewed' for c in accepted.claims)
        assert all(c.field=='proposal_basis' and c.value is None for c in accepted.claims if c.source_kind=='document')
        assert len(draft.findings)==4 and all('proposed zoning' in f for f in draft.findings)
        assert '(proposed)' in svg(accepted,'logical')
        assert 'not a source-stated deployment' in narrative(accepted)
    else:
        assert all(c.review=='confirmed' for c in accepted.claims)
        assert '(proposed)' not in svg(accepted,'logical')
    assert store.get(before.id)==accepted
    restored=store.undo(command(accepted,[dict(op='notes',value={})]))
    assert restored.zones==before.zones and restored.deployments==before.deployments
    assert restored.views['logical'].placements==before.views['logical'].placements
    with store.connect() as db:assert db.execute('SELECT count(*) FROM usage').fetchone()[0]==0


def test_pinned_component_and_manual_route_keep_world_coordinates_during_zoning():
    before=project()
    before.views['logical'].placements['c0'].locked=True
    before.views['logical'].routes['e0']=Route(points=[{'x':500,'y':400}],locked=True)
    draft=proposal_from_envelope(before,source(),envelope(),source_alias='S1')
    accepted=apply(before,draft)
    nodes={n['id']:n for n in view_graph(accepted,'logical',route_edges=False)['nodes']}
    for ident in ('c0','c1'):
        node=nodes[ident];parent=nodes[node['parentId']];old=before.views['logical'].placements[ident]
        assert (node['x']+parent['x'],node['y']+parent['y'])==(old.x,old.y)
    assert accepted.views['logical'].routes==before.views['logical'].routes
    assert_inside(accepted)


def test_existing_deployment_id_and_host_details_are_retained():
    before=project()
    before=apply(before,command(before,[dict(op='add',entity='deployments',id='existing',
        value={'component_id':'c0','quantity':2,'host_component_id':'c3','redundancy_mode':'active_passive'})]))
    draft=envelope(True,members=[0]);draft.operations[1].op='update';draft.operations[1].id='existing'
    draft.claims[1].target_id='existing'
    accepted=apply(before,proposal_from_envelope(before,source(),draft,source_alias='S1'))
    assert len(accepted.deployments)==1
    d=accepted.deployments[0]
    assert d.id=='existing' and d.quantity==2 and d.host_component_id=='c3' and d.redundancy_mode=='active_passive'


@pytest.mark.parametrize('invalid', ['missing_quote','bad_quote'])
def test_proposal_metadata_cannot_bypass_evidence_or_expand_inference_scope(invalid):
    draft=envelope(True)
    if invalid=='missing_quote':draft.claims=draft.claims[1:]
    elif invalid=='bad_quote':draft.claims[0].excerpt='Made-up segmentation requirement.'
    with pytest.raises(DomainError):proposal_from_envelope(project(),source(),draft,source_alias='S1')


def test_reason_on_component_and_full_deployment_remains_unreviewed():
    draft=envelope(True,members=[0])
    draft.operations[1].value_json=json.dumps({'component_id':'c0','zone_id':'tmp:zone','quantity':1,'redundancy_mode':'unknown','host':None})
    from apps.api.app.providers.contracts import WireOperation,WireClaim
    draft.operations.append(WireOperation(op='update',entity='components',id='c0',value_json=json.dumps({'role':'application'}),proposal_reason='Interpret this functional role from the stated control responsibility.'))
    draft.claims.append(WireClaim(source_id='S1',locator='page/5',excerpt=TEXT,target_id='c0',field='record',value_json='null'))
    before=project();accepted=apply(before,proposal_from_envelope(before,source(),draft,source_alias='S1'))
    assert accepted.deployments[0].quantity==1
    assumptions=[c for c in accepted.claims if c.source_kind=='assistant_proposal']
    assert len(assumptions)==3 and all(c.review=='unreviewed' for c in assumptions)
    assert any(c.field=='proposed_design' and c.target_id=='c0' for c in assumptions)


def test_whitespace_reason_is_treated_as_absent_metadata():
    before=project();draft=envelope();draft.operations[0].proposal_reason='   '
    accepted=apply(before,proposal_from_envelope(before,source(),draft,source_alias='S1'))
    assert len(accepted.zones)==1 and not any(c.source_kind=='assistant_proposal' for c in accepted.claims)


def test_zoning_context_includes_every_component_and_only_supplied_source_excerpts():
    before=project();before.sources=[source()]
    before.sources[0].passages.append(Passage(locator='page/3',text='Building alarm zone status.'))
    result=context(before,'Propose cyber zones for this architecture')
    assert len(result['components'])==20 and result['omitted_components']==0
    assert {s['scope'] for s in result['systems']}=={'internal','external'}
    assert [e['locator'] for e in result['source_excerpts']]==['page/5']
    assert 'Do not record required segmentation only as a constraint' in result['zoning_guidance']
    draft=envelope();draft.claims=[c.model_copy(update={'source_id':'spec'}) for c in draft.claims]
    prompt=source().model_copy(update={'id':'new-prompt','kind':'prompt'})
    with pytest.raises(DomainError,match='supplied source context'):
        proposal_from_envelope(before,prompt,draft,source_alias='S1')
    accepted=apply(before,proposal_from_envelope(before,prompt,draft,source_alias='S1',
        evidence_sources=supporting_sources(before,'Propose zones')))
    assert len(accepted.zones)==1
    assert all(c.source_id=='spec' and c.source_kind=='document' for c in accepted.claims)


def test_wire_schema_requires_nullable_proposal_metadata_for_strict_providers():
    op=schema()['$defs']['WireOperation']
    assert 'proposal_reason' in op['required'] and 'default' not in op['properties']['proposal_reason']
    assert envelope().operations[0].proposal_reason is None


class ScriptedAdapter:
    name='openai';model='gpt-5.4-mini'
    def __init__(self,output):self.output=output;self.prompts=[]
    def generate_structured(self,prompt,*args):
        self.prompts.append(json.loads(prompt))
        return ProviderResult(content=self.output,finish_status='completed',model=self.model,
                              usage=Usage(input_tokens=100,output_tokens=100))


def test_document_zoning_guidance_and_acceptance_use_scripted_provider(tmp_path,monkeypatch):
    store=Store(tmp_path/'doc.sqlite');before=store.create(project())
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:source())
    adapter=ScriptedAdapter(envelope())
    result=ingest_live(store,before.id,b'synthetic','spec.pdf','openai',Settings(allow_cloud=True,max_input=32000),adapter)
    assert len(adapter.prompts)==1 and 'Always create explicitly named' in adapter.prompts[0]['task']
    assert adapter.prompts[0]['known_records']['systems'][-1]['scope']=='external'
    assert store.get(before.id)==before
    accepted=store.commit(result['proposal']);assert_inside(accepted)
    assert len(accepted.zones)==1 and len(accepted.deployments)==3


def test_prompt_zoning_can_cite_retrieved_saved_document(tmp_path):
    store=Store(tmp_path/'prompt.sqlite');before=project();before.sources=[source()];before=store.create(before)
    output=envelope(True);output.claims=[c.model_copy(update={'source_id':'spec'}) for c in output.claims]
    adapter=ScriptedAdapter(output)
    req=RunRequest(**command(before,[dict(op='notes',value={})]).model_dump(),
                   prompt='Propose cyber zones using the specification.',provider='openai')
    result=assisted_run(store,before.id,req,Settings(allow_cloud=True,max_input=32000),adapter)
    assert adapter.prompts[0]['context']['source_excerpts'][0]['source_id']=='spec'
    assert len(adapter.prompts[0]['context']['components'])==20
    assert store.get(before.id)==before
    accepted=store.commit(store.change(result['proposal']['id']))
    assert len(accepted.zones)==1 and len(accepted.deployments)==3
