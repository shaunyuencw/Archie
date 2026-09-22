from pathlib import Path
import pytest
from apps.api.app.domain.commands import apply,command,DomainError
from apps.api.app.domain.models import Project,Component,Source,Passage
from apps.api.app.domain.naming import name_operation,can_suggest_name
from apps.api.app.ingest.parser import parse
from apps.api.app.orchestration.live import proposal_from_envelope
from apps.api.app.orchestration.service import ingest
from apps.api.app.providers.contracts import Envelope,schema
from apps.api.app.storage.store import Store


def test_provider_suggested_name_is_reviewed_and_undoable(tmp_path):
    store=Store(tmp_path/'naming.db');p=store.create(Project())
    source=parse(b'Create a warehouse inventory service.','Prompt','prompt')
    response=Envelope(operations=[{'op':'add','entity':'components','id':'inventory','value_json':'{"name":"Inventory service","role":"inventory application"}'}],claims=[{'source_id':source.id,'locator':'prompt/1','excerpt':'Create a warehouse inventory service.','target_id':'inventory','field':'record','value_json':'"Inventory service"'}],tool=None,message='Suggested title',project_name='Warehouse inventory service')
    proposal=store.preview(proposal_from_envelope(p,source,response))
    assert store.get(p.id).name=='Untitled architecture'
    accepted=store.commit(proposal);assert accepted.name=='Warehouse inventory service'
    assert accepted.components[0].name=='Inventory service'
    assert store.undo(command(accepted,[{'op':'notes','value':{}}])).name=='Untitled architecture'
    assert 'project_name' in schema()['required'] and 'default' not in schema()['properties']['project_name']
    with pytest.raises(DomainError):proposal_from_envelope(p,source,response.model_copy(update={'operations':[],'claims':[]}))


def test_custom_project_name_requires_explicit_prompt_and_imported_documents_cannot_rename_it():
    p=Project(name='My chosen project')
    response=Envelope(operations=[],claims=[],tool=None,message='No architecture edits',project_name='Another name')
    for source in [parse(b'Create a service.','Prompt','prompt'),parse(b'Rename this project to Another name.','Prompt','prompt').model_copy(update={'kind':'document'})]:
        with pytest.raises(DomainError):proposal_from_envelope(p,source,response)
    source=parse(b'Rename this project to Another name.','Prompt','prompt')
    result=apply(p,proposal_from_envelope(p,source,response))
    assert result.name=='Another name'
    for name in ['', ' '*4, 'x'*161]:
        with pytest.raises(DomainError):apply(p,command(p,[{'op':'project_name','value':{'name':name}}]))


def test_mock_document_names_initial_draft_and_mock_prompt_can_rename_it(tmp_path):
    store=Store(tmp_path/'mock-naming.db');p=store.create(Project(name='New architecture'))
    path=Path('fixtures/demos/portal/mock-input.docx')
    draft=ingest(store,p.id,path.read_bytes(),path.name)
    assert store.get(p.id).name=='New architecture'
    p=store.commit(draft['proposal']);assert p.name=='Portal web service architecture'
    draft=ingest(store,p.id,b'Rename this project to Employee services','Prompt','prompt')
    p=store.commit(draft['proposal']);assert p.name=='Employee services'


def test_default_name_can_be_filled_after_a_partial_architecture_exists():
    project=Project(name='New architecture',components=[Component(id='a',name='Client',role='client')])
    assert can_suggest_name(project)
    source=Source(id='s',name='techspec.pdf',kind='document',sha256='s',canonical_id='s',
        passages=[Passage(locator='page/1',text='Production service portal technical specification\nSYNTHETIC — DEMONSTRATION ONLY')])
    op=name_operation(project,source,None)
    assert op.value['name']=='Production service portal'
    project.name='My chosen name'
    assert name_operation(project,source,None) is None


def test_ssms_document_title_beats_repeated_pdf_header():
    source=Source(id='s',name='ssms.pdf',kind='document',sha256='s',canonical_id='s',
        passages=[Passage(locator='page/1',text='SSMS - Simplified Technical System Description\nPage 1\nSentinel Security Management System\n(SSMS)\nSystem\nSentinel Security Management System (SSMS)')])
    assert name_operation(Project(),source,None).value['name']=='Sentinel Security Management System (SSMS)'
