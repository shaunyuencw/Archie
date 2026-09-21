import hashlib,json
from pathlib import Path
from pypdf import PdfReader
from apps.api.app.domain.models import Project
from apps.api.app.domain.catalogue import catalogue
from apps.api.app.ingest.parser import parse
from apps.api.app.orchestration.service import ingest
from apps.api.app.storage.store import Store
from scripts.generate_demos import main

DEMOS=Path('fixtures/demos')


def test_demo_generator_is_deterministic_and_has_four_readable_sources(tmp_path):
    main(tmp_path)
    before={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
    main(tmp_path)
    after={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
    assert before==after
    manifest=json.loads((tmp_path/'manifest.json').read_text())
    assert len(manifest)==8 and len({row['source_id'] for row in manifest})==4
    for code in ['portal','robotics','inventory','building-access']:
        pdf=PdfReader(tmp_path/code/'techspec.pdf')
        assert 1<=len(pdf.pages)<=3 and 'SYNTHETIC' in pdf.pages[0].extract_text()
        assert (tmp_path/code/'techspec.md').exists() and (tmp_path/code/'techspec.docx').exists()
        followups=json.loads((tmp_path/code/'followups.json').read_text())
        assert len(followups['prompts'])>=3 and 'live provider' in followups['provider_notes']


def test_new_references_are_layered_source_linked_and_use_real_catalogue_assets():
    assets={a['id'] for a in catalogue()}
    for code,count in [('portal',7),('robotics',14)]:
        p=Project.model_validate_json((DEMOS/code/'project.json').read_text())
        assert len(p.components)==count and p.synthetic
        assert all(c.asset_id in assets and c.evidence for c in p.components)
        assert p.sources[0].origin=='bundled_demo'
        source=parse((DEMOS/code/'techspec.docx').read_bytes(),'techspec.docx')
        passages={item.locator:item.text for item in source.passages}
        assert all(c.excerpt in passages[c.locator] for c in p.claims)
        clients={d.component_id for d in p.deployments if d.zone_id and 'client' in d.zone_id}
        assert all(c.form_factor=='physical' and c.asset_id in ['workstation','robot','operator-tablet','wireless-access-point'] for c in p.components if c.id in clients)
        assert all(d.quantity>=2 for d in p.deployments if d.redundancy_mode!='unknown')
        assert all(d.zone_id is not None for d in p.deployments)
        assert p.views['logical'].placements and all(e.id in p.views['logical'].routes for e in p.interfaces)


def test_hybrid_demo_has_only_the_named_production_and_cloud_crossings():
    p=Project.model_validate_json((DEMOS/'robotics/project.json').read_text())
    systems={c.id:c.system_id for c in p.components}
    crossings=[i for i in p.interfaces if systems[i.source]=='testbed-system' and systems[i.target]=='production-system']
    assert [i.id for i in crossings]==['production-handoff']
    assert crossings[0].target=='prod-api' and crossings[0].enforcement==['trial-firewall']
    cloud=[i for i in p.interfaces if systems[i.source]=='testbed-system' and systems[i.target]=='telemetry-system']
    assert [i.id for i in cloud]==['cloud-telemetry'] and cloud[0].target=='aws-api'
    assert not any(systems[i.source]=='telemetry-system' and systems[i.target]=='testbed-system' for i in p.interfaces)
    firewall=next(d for d in p.deployments if d.component_id=='trial-firewall')
    assert firewall.host_component_id=='trial-host'
    assert any(c.value is None for c in p.constraints)


def test_authored_mock_inputs_match_new_reference_facts(tmp_path):
    for code in ['portal','robotics']:
        reference=Project.model_validate_json((DEMOS/code/'project.json').read_text())
        store=Store(tmp_path/(code+'.sqlite'));project=store.create(Project())
        result=ingest(store,project.id,(DEMOS/code/'mock-input.docx').read_bytes(),'mock-input.docx')
        assert result['proposal'] is not None
        accepted=store.commit(result['proposal'])
        assert {c.id for c in accepted.components}=={c.id for c in reference.components}
        assert {i.id for i in accepted.interfaces}=={i.id for i in reference.interfaces}
        expected={d.component_id:(d.zone_id,d.quantity,d.redundancy_mode,d.host_component_id) for d in reference.deployments}
        assert {d.component_id:(d.zone_id,d.quantity,d.redundancy_mode,d.host_component_id) for d in accepted.deployments}==expected
        assert {c.id:c.form_factor for c in accepted.components}=={c.id:c.form_factor for c in reference.components}


def test_natural_language_specs_do_not_claim_general_mock_understanding(tmp_path):
    store=Store(tmp_path/'db');project=store.create(Project())
    result=ingest(store,project.id,(DEMOS/'inventory/techspec.docx').read_bytes(),'techspec.docx')
    assert result['proposal'] is None and 'Mock understands' in result['message']
    assert not store.get(project.id).components
