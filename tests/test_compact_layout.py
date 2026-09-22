from itertools import combinations

import pytest
from fastapi.testclient import TestClient

from apps.api.app.domain.commands import DomainError, apply, command
from apps.api.app.domain.layout import bounds
from apps.api.app.domain.models import ChangeSet, Placement, Project, Route
from apps.api.app.domain.views import arrange_plan, initialise_views, view_graph
from apps.api.app.storage.store import Store


def sparse_project():
    p = Project(zones=[dict(id=f'z{i}', name=f'Security zone {i}') for i in range(6)],
                components=[dict(id=f'c{i}', name=f'Service {i}', role='server') for i in range(12)],
                deployments=[dict(id=f'd{i}', component_id=f'c{i}', zone_id=f'z{i % 6}') for i in range(8)],
                interfaces=[dict(id=f'e{i}', source=f'c{i}', target=f'c{i+1}') for i in range(11)])
    for view in p.views.values():
        if view.type == 'sv1':
            continue
        for i in range(6):
            view.placements[f'z{i}'] = Placement(x=40+i % 2*580, y=60+i//2*400, width=530, height=350)
        for i in range(12):
            view.placements[f'c{i}'] = Placement(x=30+i//6*235 if i < 8 else 1200,
                                                y=65 if i < 8 else 65+(i-8)*130, width=185, height=90)
    return initialise_views(p)


def graph_nodes(p, kind='logical'):
    return view_graph(p, kind, route_edges=False)['nodes']


def overlaps(a, b):
    return (a['x'] < b['x']+b['width'] and a['x']+a['width'] > b['x'] and
            a['y'] < b['y']+b['height'] and a['y']+a['height'] > b['y'])


def check_clear(p, kind='logical'):
    nodes = graph_nodes(p, kind)
    roots = {n['id']: n for n in nodes if not n.get('parentId')}
    assert not any(overlaps(a, b) for a, b in combinations(roots.values(), 2))
    for node in nodes:
        if node.get('parentId') not in roots:
            continue
        parent = roots[node['parentId']]
        assert node['x'] >= 24 and node['y'] >= 64
        assert node['x']+node['width'] <= parent['width']-24
        assert node['y']+node['height'] <= parent['height']-24
    for parent in roots:
        children = [n for n in nodes if n.get('parentId') == parent]
        assert not any(overlaps(a, b) for a, b in combinations(children, 2))


def test_compaction_reduces_empty_space_preserves_facts_and_is_repeatable():
    p = sparse_project()
    p.views['logical'].placements['c1'].fill_color = '#123456'
    original = p.model_dump()
    before = bounds([n for n in graph_nodes(p) if not n.get('parentId')])
    plan = arrange_plan(p, 'logical')
    assert p.model_dump() == original  # Planning is read-only.
    compact = apply(p, plan['change'])
    after = plan['bounds']
    assert after['width']*after['height'] < before['width']*before['height']*.65
    assert compact.revision == p.revision
    assert compact.views['logical'].revision == p.views['logical'].revision+1
    assert compact.views['sv1'] == p.views['sv1'] and compact.views['sv2'] == p.views['sv2']
    for field in ('components', 'zones', 'systems', 'deployments', 'interfaces', 'claims', 'sources'):
        assert getattr(compact, field) == getattr(p, field)
    for component in p.components:
        first, last = p.views['logical'].placements[component.id], compact.views['logical'].placements[component.id]
        assert (last.width, last.height, last.fill_color) == (first.width, first.height, first.fill_color)
    check_clear(compact)
    assert arrange_plan(compact, 'logical')['change'] is None


@pytest.mark.parametrize('pinned', ['z0', 'c0'])
def test_pin_keeps_entire_family_in_place_and_other_nodes_clear(pinned):
    p = sparse_project()
    p.views['logical'].placements[pinned].locked = True
    result = apply(p, arrange_plan(p, 'logical')['change'])
    for ident in ('z0', 'c0', 'c6'):
        assert result.views['logical'].placements[ident] == p.views['logical'].placements[ident]
    check_clear(result)


def test_manual_bends_keep_endpoint_families_and_routes_intact():
    p = sparse_project()
    p.views['logical'].routes['e8'] = Route(points=[dict(x=1500, y=700)], locked=True,
                                          label_offset=dict(x=20, y=30), line_color='#abcdef')
    result = apply(p, arrange_plan(p, 'logical')['change'])
    for ident in ('c8', 'c9'):
        assert result.views['logical'].placements[ident] == p.views['logical'].placements[ident]
    assert result.views['logical'].routes == p.views['logical'].routes
    check_clear(result)


def test_plan_commits_as_one_undoable_transaction_and_rejects_stale_versions(tmp_path):
    store = Store(tmp_path/'layout.sqlite')
    p = store.create(sparse_project())
    plan = arrange_plan(p, 'logical')
    compact = store.commit(plan['change'])
    with pytest.raises(DomainError, match='project changed'):
        apply(compact, plan['change'])
    restored = store.undo(command(compact, [dict(op='notes', value={})]))
    assert restored.views['logical'].placements == p.views['logical'].placements
    assert restored.interfaces == p.interfaces
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM history').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM usage').fetchone()[0] == 0


def test_fresh_zones_fit_contents_without_rearranging_saved_views():
    p = sparse_project()
    p.views['logical'].placements.clear()
    p = initialise_views(p)
    assert p.views['logical'].placements['z5'].height == 178
    assert p.views['logical'].placements['z5'].width < 530
    check_clear(p)
    before = p.views['logical'].model_dump()
    p = apply(p, command(p, [dict(op='notes', value={'text': 'Retain this layout.'})]))
    assert p.views['logical'].model_dump() == before


@pytest.mark.parametrize('grouped', [True, False])
def test_capacity_and_custom_component_sizes(grouped):
    p = Project(zones=[dict(id='z', name='A large deployment')],
                components=[dict(id=f'c{i}', name=f'Service {i}', role='server') for i in range(50)],
                deployments=[dict(id=f'd{i}', component_id=f'c{i}', zone_id='z') for i in range(50)] if grouped else [])
    p = initialise_views(p)
    p.views['logical'].placements['c0'].width = 320
    p.views['logical'].placements['c0'].height = 140
    plan = arrange_plan(p, 'logical')
    result = apply(p, plan['change']) if plan['change'] else p
    check_clear(result)
    assert result.views['logical'].placements['c0'].width == 320
    assert arrange_plan(result, 'logical')['change'] is None


def test_empty_and_hidden_nodes_do_not_create_edits():
    assert arrange_plan(Project(), 'logical') == {'change': None, 'bounds': None}
    p = sparse_project()
    p.views['logical'].placements['c8'].visible = False
    result = apply(p, arrange_plan(p, 'logical')['change'])
    assert result.views['logical'].placements['c8'] == p.views['logical'].placements['c8']


def test_read_only_endpoint_validates_view_and_aspect_then_uses_standard_commands(tmp_path, monkeypatch):
    from apps.api.app import main
    store = Store(tmp_path/'api-layout.sqlite')
    monkeypatch.setattr(main, 'store', store)
    p = store.create(sparse_project())
    client = TestClient(main.app)
    url = f'/api/projects/{p.id}/views/logical/arrange'
    response = client.get(url)
    assert response.status_code == 200
    assert store.get(p.id) == p
    proposal = ChangeSet.model_validate(response.json()['change'])
    result = client.post(f'/api/projects/{p.id}/commands', json=proposal.model_dump())
    assert result.status_code == 200
    check_clear(Project.model_validate(result.json()))
    assert client.get(url+'?aspect_ratio=0').status_code == 422
    assert client.get(f'/api/projects/{p.id}/views/missing/arrange').status_code == 422


def test_system_overview_can_compact_without_changing_aggregate_mappings():
    p = sparse_project()
    before = view_graph(p, 'sv1', route_edges=False)['mappings']
    result = apply(p, arrange_plan(p, 'sv1')['change'])
    check_clear(result, 'sv1')
    assert view_graph(result, 'sv1', route_edges=False)['mappings'] == before
