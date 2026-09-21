from pathlib import Path
from apps.api.app.domain.models import Project
from apps.api.app.orchestration.live import context


def test_bounded_edit_context_preserves_deployment_ids_counts_and_host_references():
    project=Project.model_validate_json(Path('fixtures/demos/portal/project.json').read_text())
    result=context(project,'Make Zone firewall a pair, still hosted on Application hosts')
    ids={c['id'] for c in result['components']}
    expected=[c for c in project.components if c.name in {'Zone firewall','Application hosts'}]
    assert ids=={c.id for c in expected}
    assert all('asset_id' in c and 'form_factor' in c and 'evidence' not in c for c in result['components'])
    assert result['deployments']==[d.model_dump() for d in project.deployments if d.component_id in ids]
    assert all(d['zone_id'] in {z['id'] for z in result['zones']} for d in result['deployments'])
    assert any(d['host_component_id'] in ids for d in result['deployments'])
    assert any(d['quantity']==2 and d['redundancy_mode']=='active_active' for d in result['deployments'])
    assert result['omitted_components']==len(project.components)-2
