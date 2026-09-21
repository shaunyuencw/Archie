"""Replay common model output shapes through the real proposal/acceptance boundary."""
import json

import pytest

from apps.api.app.domain.commands import DomainError, apply, command
from apps.api.app.domain.models import Component, Interface, Passage, Project, Source
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.orchestration.live import proposal_from_envelope
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope, ProviderResult, Usage
from apps.api.app.storage.store import Store


def source():
    return Source(id='spec', name='Synthetic spec', kind='document', sha256='spec', canonical_id='spec', passages=[
        Passage(locator='paragraph/1', text='Client connects to the application using TCP 443. The application connects to the database using TCP 5432. Enforcement is unknown.')
    ])


def envelope(operations):
    return Envelope(operations=[{**op, 'value_json':json.dumps(op['value_json'])} for op in operations], claims=[
        {'source_id':'S1', 'locator':'paragraph/1', 'excerpt':source().passages[0].text, 'target_id':op['id'], 'field':'record', 'value_json':'null'}
        for op in operations
    ], tool=None, message='Review the draft')


@pytest.mark.parametrize('provider', ['openai', 'ollama'])
def test_document_with_three_unknown_enforcement_fields_can_be_reviewed_and_accepted(tmp_path, monkeypatch, provider):
    store=Store(tmp_path/'db'); project=store.create(Project())
    operations=[
        {'op':'add','entity':'components','id':ident,'value_json':{'name':name,'role':'server','scope':None,'form_factor':None}}
        for ident,name in [('client','Client'),('app','Application'),('db','Database')]
    ]+[
        {'op':'add','entity':'interfaces','id':ident,'value_json':{'source':start,'target':end,'port':port,'enforcement':'unknown','data_direction':None}}
        for ident,start,end,port in [('client-app','client','app','TCP 443'),('app-db','app','db','TCP 5432'),('db-app','db','app',None)]
    ]

    class Adapter:
        name=provider
        model='gpt-5.4-mini' if provider=='openai' else 'mocked-local'
        calls=0
        def generate_structured(self,*args):
            self.calls+=1
            return ProviderResult(model=self.model, finish_status='completed', usage=Usage(), content=envelope(operations))

    adapter=Adapter()
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse', lambda *args:source())
    result=ingest_live(store,project.id,b'fixture','spec.docx',provider,Settings(allow_cloud=True,max_calls=1),adapter)
    assert adapter.calls==1  # Local normalization needs no paid repair request.
    assert store.get(project.id)==project
    assert len(result['proposal'].findings)==3
    accepted=store.commit(result['proposal'])
    assert [i.port for i in accepted.interfaces]==[443,5432,None]
    assert all(i.enforcement==[] and i.data_direction=='unknown' for i in accepted.interfaces)
    assert all(c.scope=='unknown' and c.form_factor=='unknown' for c in accepted.components)
    assert accepted.sources[0].processed==['paragraph/1']
    assert all(c.source_id=='spec' for c in accepted.claims)


@pytest.mark.parametrize('value', [None,'unknown',' Not specified ',['unknown'],[None]])
def test_unknown_enforcement_remains_unspecified(value):
    project=Project(components=[Component(id='a',name='A',role='server'),Component(id='b',name='B',role='server')])
    proposal=proposal_from_envelope(project,source(),envelope([
        {'op':'add','entity':'interfaces','id':'link','value_json':{'source':'a','target':'b','enforcement':value}}
    ]),source_alias='S1')
    assert apply(project,proposal).interfaces[0].enforcement==[]
    assert 'not fully specified' in proposal.findings[0]


@pytest.mark.parametrize('value', ['tmp:firewall',['tmp:firewall','unknown']])
def test_enforcement_keeps_exact_forward_component_reference(value):
    project=Project(components=[Component(id='a',name='A',role='server'),Component(id='b',name='B',role='server')])
    proposal=proposal_from_envelope(project,source(),envelope([
        {'op':'add','entity':'interfaces','id':'link','value_json':{'source':'a','target':'b','enforcement':value}},
        {'op':'add','entity':'components','id':'tmp:firewall','value_json':{'name':'Firewall','role':'firewall'}},
    ]),source_alias='S1')
    accepted=apply(project,proposal)
    assert accepted.interfaces[0].enforcement==[accepted.components[-1].id]


@pytest.mark.parametrize('value', ['unlisted-firewall','fw, a',{'id':'fw'},[123],['fw','missing']])
def test_invalid_enforcement_is_not_silently_removed(value):
    project=Project(components=[Component(id='a',name='A',role='server'),Component(id='fw',name='Firewall',role='firewall')])
    with pytest.raises(DomainError,match='does not match a component'):
        proposal_from_envelope(project,source(),envelope([
            {'op':'add','entity':'interfaces','id':'link','value_json':{'source':'a','target':'fw','enforcement':value}}
        ]),source_alias='S1')
    assert not project.interfaces


def test_omitted_enforcement_update_preserves_saved_firewall():
    project=Project(components=[Component(id='a',name='A',role='server'),Component(id='fw',name='Firewall',role='firewall')],
                    interfaces=[Interface(id='link',source='a',target='fw',enforcement=['fw'])])
    proposal=proposal_from_envelope(project,source(),envelope([
        {'op':'update','entity':'interfaces','id':'link','value_json':{'port':'TCP 443'}}
    ]),source_alias='S1')
    assert apply(project,proposal).interfaces[0].enforcement==['fw']


def test_manual_enforcement_validation_stays_strict_and_readable():
    project=Project(components=[Component(id='a',name='A',role='server'),Component(id='b',name='B',role='server')])
    with pytest.raises(DomainError) as failure:
        apply(project,command(project,[{'op':'add','entity':'interfaces','id':'link','value':{'source':'a','target':'b','enforcement':'unknown'}}]))
    assert 'enforcement must be a list of component IDs' in failure.value.message
    assert 'pydantic' not in failure.value.message and 'list_type' not in failure.value.message
    assert not project.interfaces


def test_other_invalid_fields_explain_the_problem_without_schema_trace():
    project=Project()
    with pytest.raises(DomainError) as failure:
        apply(project,command(project,[{'op':'add','entity':'components','id':'node','value':{'name':'Node','role':'server','status':'unknown'}}]))
    assert 'Component / 1 / status' in failure.value.message
    assert 'pydantic' not in failure.value.message and 'input_value' not in failure.value.message
    assert not project.components
