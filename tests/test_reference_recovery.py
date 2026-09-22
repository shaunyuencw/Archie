"""Typed ID recovery must preserve meaning and leave the canonical validator strict."""
import json

import pytest

from apps.api.app.domain.commands import DomainError, apply, command
from apps.api.app.domain.models import Component, Interface, Passage, Project, Source, System
from apps.api.app.orchestration.live import proposal_from_envelope
from apps.api.app.orchestration.references import reference_catalog
from apps.api.app.providers.contracts import Envelope


def source():
    return Source(id='spec', name='Synthetic system flow', kind='document', sha256='spec', canonical_id='spec',
                  passages=[Passage(locator='page/1', text='SYS-VAS Video Analytics System sends events to the console through the firewall.')])


def envelope(operations):
    return Envelope(operations=[{'op':op.get('op','add'),'entity':op['entity'],'id':op['id'],
                                 'value_json':json.dumps(op['value'])} for op in operations],
                    claims=[{'source_id':'S1','locator':'page/1','excerpt':source().passages[0].text,
                             'target_id':op['id'],'field':'record','value_json':'null'} for op in operations],
                    tool=None,message='Review the source-grounded change.')


@pytest.mark.parametrize('alias',['SYS-VAS','sys-vas','Video Analytics System'])
def test_unique_system_alias_resolves_to_same_canonical_record(alias):
    project=Project(systems=[System(id='tmp:SYS-VAS',name='Video Analytics System')])
    proposal=proposal_from_envelope(project,source(),envelope([
        {'entity':'components','id':'tmp:analytics','value':{'name':'Analytics','role':'application','system_id':alias}},
    ]),source_alias='S1')
    accepted=apply(project,proposal)
    assert accepted.components[0].system_id=='tmp:SYS-VAS'
    assert len(accepted.systems)==1 and not project.components


def test_forward_component_aliases_resolve_without_editing_literal_text():
    response=envelope([
        {'entity':'interfaces','id':'IF-01','value':{'source':'VAS','target':'Console','initiator':'vas','enforcement':['FW'],'purpose':'SYS-VAS events'}},
        {'entity':'components','id':'tmp:VAS','value':{'name':'Analytics','role':'application'}},
        {'entity':'components','id':'console','value':{'name':'Console','role':'workstation'}},
        {'entity':'components','id':'tmp:FW','value':{'name':'Firewall','role':'firewall'}},
    ])
    response.claims[1].target_id='VAS'
    original=response.model_dump_json()
    accepted=apply(Project(id='project'),proposal_from_envelope(Project(id='project'),source(),response,source_alias='S1'))
    components={c.name:c.id for c in accepted.components}
    link=accepted.interfaces[0]
    assert (link.source,link.target,link.initiator)==(components['Analytics'],components['Console'],components['Analytics'])
    assert link.enforcement==[components['Firewall']] and link.purpose=='SYS-VAS events'
    assert response.model_dump_json()==original


@pytest.mark.parametrize('system_id',['SYS-VAS','tmp:SYS-VAS'])
def test_system_id_cannot_silently_become_an_internal_component(system_id):
    project=Project(systems=[System(id=system_id,name='Video Analytics System')],components=[
        Component(id='analytics',name='Processor',role='application',system_id=system_id),
        Component(id='console',name='Console',role='workstation'),
    ])
    with pytest.raises(DomainError) as failure:
        proposal_from_envelope(project,source(),envelope([
            {'entity':'interfaces','id':'IF-01','value':{'source':'SYS-VAS','target':'console'}},
        ]),source_alias='S1')
    assert failure.value.code=='provider_output'
    assert 'IF-01' in failure.value.message and 'SYS-VAS' in failure.value.message
    assert 'identifies a system' in failure.value.message and 'boundary component' in failure.value.message
    assert not project.interfaces


@pytest.mark.parametrize('records',[
    [System(id='vas',name='Analytics A'),System(id='tmp:vas',name='Analytics B')],
    [System(id='first',name='VAS'),System(id='second',name='VAS')],
])
def test_ambiguous_aliases_reject_instead_of_selecting_first(records):
    project=Project(systems=records)
    with pytest.raises(DomainError,match='no unambiguous matching system'):
        proposal_from_envelope(project,source(),envelope([
            {'entity':'components','id':'analytics','value':{'name':'Analytics','role':'application','system_id':'VAS'}},
        ]),source_alias='S1')


def test_missing_nullable_membership_is_not_silently_dropped():
    with pytest.raises(DomainError,match='MISSING'):
        proposal_from_envelope(Project(),source(),envelope([
            {'entity':'components','id':'analytics','value':{'name':'Analytics','role':'application','system_id':'MISSING'}},
        ]),source_alias='S1')


def test_evidenced_removal_still_works_and_rejects_the_removed_target_claim():
    project=Project(components=[Component(id='old',name='Old console',role='workstation')])
    accepted=apply(project,proposal_from_envelope(project,source(),envelope([
        {'op':'remove','entity':'components','id':'old','value':{}},
    ]),source_alias='S1'))
    assert not accepted.components and accepted.claims[0].review=='rejected'


def test_manual_system_endpoint_still_rejects():
    project=Project(systems=[System(id='SYS-VAS',name='Video Analytics System')],
                    components=[Component(id='console',name='Console',role='workstation')])
    with pytest.raises(DomainError,match='Unresolved reference: SYS-VAS'):
        apply(project,command(project,[{'op':'add','entity':'interfaces','id':'IF-01',
                                        'value':{'source':'SYS-VAS','target':'console'}}]))


def test_reference_catalog_keeps_types_and_accumulated_record_updates():
    project=Project(systems=[System(id='SYS-VAS',name='Video Analytics System')])
    first=envelope([{'entity':'components','id':'analytics','value':{'name':'Analytics','role':'application','system_id':'SYS-VAS'}}])
    second=envelope([{'op':'update','entity':'components','id':'analytics','value':{'name':'Central analytics'}}])
    result=reference_catalog(project,[first,second])
    assert result['systems']==[{'id':'SYS-VAS','name':'Video Analytics System'}]
    assert result['components']==[{'id':'analytics','name':'Central analytics','role':'application','system_id':'SYS-VAS'}]
    assert not project.components


def test_later_initiator_update_uses_the_resolved_endpoint_ids():
    project=Project(components=[Component(id='tmp:vas',name='Analytics',role='application'),
                                Component(id='console',name='Console',role='workstation')])
    candidate=envelope([
        {'entity':'interfaces','id':'IF-01','value':{'source':'VAS','target':'console'}},
        {'op':'update','entity':'interfaces','id':'IF-01','value':{'initiator':'VAS'}},
    ])
    accepted=apply(project,proposal_from_envelope(project,source(),candidate,source_alias='S1'))
    assert accepted.interfaces[0].source==accepted.interfaces[0].initiator=='tmp:vas'


def test_invalid_candidate_name_cannot_crash_alias_resolution():
    candidate=envelope([
        {'entity':'systems','id':'SYS-VAS','value':{'name':None}},
        {'entity':'components','id':'processor','value':{'name':'Processor','role':'application','system_id':'Video Analytics System'}},
    ])
    with pytest.raises(DomainError,match='no unambiguous matching system'):
        proposal_from_envelope(Project(),source(),candidate,source_alias='S1')
