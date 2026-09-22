import json

import pytest

from apps.api.app.domain.catalogue import component_asset
from apps.api.app.domain.commands import apply
from apps.api.app.domain.models import Project, Source, Passage
from apps.api.app.orchestration.live import proposal_from_envelope
from apps.api.app.providers.contracts import Envelope


@pytest.mark.parametrize('name,role,expected',[
    ('Operator Client','client','workstation'),
    ('Camera Sensors','sensor/device','camera'),
    ('Camera Control Service','service','application'),
    ('C2 Application Service','service','application'),
    ('Integration Gateway','integration adapter','gateway'),
    ('VSS Integration API','integration adapter','api-service'),
    ('Video Archive','data store','storage'),
    ('Operational Event Store','data store','database'),
    ('Analytics Metadata Store','data store','database'),
    ('Analytics Processing Service','service','analytics-engine'),
    ('Building Sensors & Controllers','sensor/device','sensor'),
    ('Readers, Door Sensors & Controllers','sensor/device','sensor'),
    ('Access Control Server','service','server'),
    ('BMS boundary','system boundary','system-boundary'),
])
def test_generic_server_default_uses_function_not_one_icon_for_everything(name,role,expected):
    assert component_asset(dict(name=name,role=role,asset_id='server'))==expected


def test_specific_icon_and_declared_physical_server_are_preserved():
    assert component_asset(dict(name='Operator client',role='client',asset_id='operator-tablet'))=='operator-tablet'
    assert component_asset(dict(name='Camera service host',role='server',asset_id='server',form_factor='physical'))=='server'
    assert component_asset(dict(name='Unknown part',role='unspecified',asset_id='nonexistent-icon'))=='generic-role-a'
    assert component_asset(dict(name='API',role='service',asset_id='API_SERVICE'))=='api-service'


def test_ai_icon_normalisation_is_source_linked_without_guessing_physical_facts_or_overwriting_manual_choice():
    source=Source(id='source',name='Synthetic specification',kind='document',sha256='x',canonical_id='x',
                  passages=[Passage(locator='page/1',text='Operators use the Operator Client.')])
    proposal=Envelope(operations=[dict(op='add',entity='components',id='client',value_json=json.dumps(dict(name='Operator Client',role='client')))],
                      claims=[dict(source_id='S1',locator='page/1',excerpt='Operators use the Operator Client.',target_id='client',field='record',value_json='null')],tool=None,message='Review the client.')
    p=Project()
    draft=proposal_from_envelope(p,source,proposal,source_alias='S1')
    assert not p.components
    result=apply(p,draft)
    assert result.components[0].asset_id=='workstation'
    assert result.components[0].form_factor=='unknown' and result.components[0].status=='proposed'
    assert result.components[0].evidence and not result.deployments
    result.components[0].asset_id='operator-tablet'
    proposal.operations[0].op='update'
    proposal.operations[0].value_json=json.dumps(dict(name='Updated Operator Client'))
    updated=apply(result,proposal_from_envelope(result,source,proposal,source_alias='S1'))
    assert updated.components[0].asset_id=='operator-tablet'
