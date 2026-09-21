"""Reimporting parsed material must not be confused with accepting its architecture."""
import io
import json
import threading
from types import SimpleNamespace

import pytest
from docx import Document
from fastapi.testclient import TestClient

import apps.api.app.main as main
from apps.api.app.domain.commands import DomainError, command
from apps.api.app.domain.models import Claim, Component, Project
from apps.api.app.ingest.parser import parse
from apps.api.app.orchestration import documents, jobs
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.orchestration.service import ingest
from apps.api.app.providers.budget import usage_summary
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope, ProviderResult, Usage
from apps.api.app.storage.store import Store


def document_bytes(text='Synthetic service: staff use a reception workstation to view arrival events.'):
    document = Document()
    document.add_paragraph(text)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


class DocumentAdapter:
    name = 'ollama'
    model = 'mocked-document-reimport'

    def __init__(self):
        self.calls = 0

    def generate_structured(self, prompt, *args):
        self.calls += 1
        passage = json.loads(prompt)['source']['passages'][0]
        ident = f'tmp:station-{self.calls}'
        return ProviderResult(
            model=self.model, finish_status='completed', usage=Usage(input_tokens=100, output_tokens=100),
            content=Envelope.model_validate({
                'operations': [{'op': 'add', 'entity': 'components', 'id': ident,
                                'value_json': json.dumps({'name': 'Reception workstation', 'role': 'workstation'})}],
                'claims': [{'source_id': 'S1', 'locator': passage['locator'], 'excerpt': passage['text'],
                            'target_id': ident, 'field': 'record', 'value_json': '"Reception workstation"'}],
                'tool': None, 'message': 'Review the reception workstation.',
            }),
        )


class HeldExecutor:
    def __init__(self):
        self.calls = []

    def submit(self, fn, *args):
        self.calls.append((fn, args))
        return SimpleNamespace(cancel=lambda: False)

    def run_all(self):
        while self.calls:
            fn, args = self.calls.pop(0)
            fn(*args)


def settings():
    return Settings(ollama_num_ctx=8192, max_calls=1)


@pytest.mark.parametrize('mock_outcome', ['unsupported', 'pending', 'rejected'])
def test_live_reimport_after_mock_parsing_requires_review_and_reuses_source(tmp_path, mock_outcome):
    store = Store(tmp_path / 'reimport.sqlite')
    project = store.create(Project())
    data = document_bytes() if mock_outcome == 'unsupported' else document_bytes(
        'Component reception: name="Reception workstation"; role="workstation"'
    )
    mock_result = ingest(store, project.id, data, 'synthetic-spec.docx')
    if mock_outcome == 'unsupported':
        assert mock_result['proposal'] is None
    else:
        assert mock_result['proposal'].state == 'pending'
        if mock_outcome == 'rejected':
            store.reject(mock_result['proposal'].id)
    before = store.get(project.id)
    assert len(before.sources) == 1 and not before.components
    source_id = before.sources[0].id
    assert not any(claim.review == 'confirmed' for claim in before.claims)
    adapter = DocumentAdapter()

    result = ingest_live(store, project.id, data, 'synthetic-spec.docx', 'ollama', settings(), adapter)

    assert adapter.calls == 1, 'A parsed but unaccepted source must reach the selected live provider.'
    assert not result.get('duplicate') and result['proposal'].state == 'pending'
    assert store.get(project.id) == before
    source_ops = [op for op in result['proposal'].operations if op.entity == 'sources']
    assert len(source_ops) == 1 and source_ops[0].op == 'update' and source_ops[0].id == source_id
    assert usage_summary(store, project.id)['calls'] == 1
    accepted = store.commit(result['proposal'])
    assert len(accepted.sources) == len(accepted.components) == 1
    assert accepted.sources[0].id == source_id
    assert any(claim.review == 'confirmed' and claim.source_id == source_id for claim in accepted.claims)


@pytest.mark.parametrize('review', ['confirmed', 'conflicting'])
def test_accepted_document_repeat_reports_existing_source_without_provider_call(tmp_path, review):
    store = Store(tmp_path / 'accepted.sqlite')
    project = store.create(Project())
    adapter = DocumentAdapter()
    data = document_bytes()
    result = ingest_live(store, project.id, data, 'synthetic-spec.docx', 'ollama', settings(), adapter)
    accepted = store.commit(result['proposal'])
    if review == 'conflicting':
        accepted = store.commit(command(accepted, [{'op': 'update', 'entity': 'claims',
                                                   'id': accepted.claims[0].id, 'value': {'review': review}}]))
    before_usage = usage_summary(store, project.id)

    repeated = ingest_live(store, project.id, data, 'synthetic-spec.docx', 'ollama', settings(), adapter)

    assert repeated['duplicate'] and repeated['proposal'] is None
    assert repeated['source_id'] == accepted.sources[0].id
    assert repeated['coverage'] == {'processed': accepted.sources[0].processed,
                                    'unprocessed': accepted.sources[0].unprocessed}
    assert repeated['message'] and 'project' in repeated['message'].lower()
    assert adapter.calls == 1 and usage_summary(store, project.id) == before_usage
    assert store.get(project.id) == accepted


@pytest.mark.parametrize('existing_target', [False, True], ids=['missing-target', 'existing-target-without-evidence'])
def test_unaccepted_conflicting_claim_does_not_block_reimport(tmp_path, existing_target):
    store = Store(tmp_path / 'missing-target.sqlite')
    data = document_bytes()
    source = parse(data, 'synthetic-spec.docx', store=store)
    passage = source.passages[0]
    claim = Claim(id='unaccepted-conflict', source_id=source.id, source_version=source.version,
                  source_kind=source.kind, locator=passage.locator, excerpt=passage.text,
                  target_id='absent-component', field='record', review='conflicting')
    components = [Component(id=claim.target_id, name='Previously created station', role='workstation')] if existing_target else []
    project = store.create(Project(sources=[source], claims=[claim], components=components))
    adapter = DocumentAdapter()

    result = ingest_live(store, project.id, data, 'synthetic-spec.docx', 'ollama', settings(), adapter)

    assert adapter.calls == 1 and result['proposal'].state == 'pending'
    assert store.get(project.id) == project
    assert next(op for op in result['proposal'].operations if op.entity == 'sources').id == source.id


def test_rejected_long_mock_source_keeps_evidence_and_continues_only_remaining_ranges(tmp_path):
    store = Store(tmp_path / 'long-source.sqlite')
    project = store.create(Project())
    text = 'Component reception: name="Reception workstation"; role="workstation". '
    text += 'Synthetic reception data is displayed for a staff operator. ' * 25
    data = document_bytes(text)
    result = ingest(store, project.id, data, 'long-synthetic-spec.docx')
    store.reject(result['proposal'].id)
    before = store.get(project.id)
    original_claim = before.claims[0]
    source_id = before.sources[0].id
    expected_ranges = [f'paragraph/1/chars/{start}-{min(start + 700, len(text))}'
                       for start in range(0, len(text), 700)]
    adapter = DocumentAdapter()

    result = ingest_live(store, project.id, data, 'long-synthetic-spec.docx', 'ollama', settings(), adapter)
    for index, locator in enumerate(expected_ranges):
        assert result['coverage']['processed'] == [locator]
        assert store.get(project.id) == before
        accepted = store.commit(result['proposal'])
        source = accepted.sources[0]
        assert source.processed == expected_ranges[:index + 1]
        assert source.unprocessed == expected_ranges[index + 1:]
        assert len(source.passages) == len({passage.locator for passage in source.passages})
        assert original_claim in accepted.claims
        assert any(passage.locator == original_claim.locator and original_claim.excerpt in passage.text
                   for passage in source.passages)
        before = accepted
        if source.unprocessed:
            result = ingest_live(store, project.id, b'', '', 'ollama', settings(), adapter, source_id=source_id)
    assert adapter.calls == len(expected_ranges)
    assert len(accepted.sources) == 1 and not source.unprocessed


@pytest.mark.parametrize('outcome', ['failed', 'cancelled'])
def test_failed_or_cancelled_live_retry_preserves_saved_source(tmp_path, outcome):
    store = Store(tmp_path / 'failed-retry.sqlite')
    project = store.create(Project())
    data = document_bytes()
    assert ingest(store, project.id, data, 'synthetic-spec.docx')['proposal'] is None
    before = store.get(project.id)
    cancel = threading.Event()

    class InterruptedAdapter(DocumentAdapter):
        def generate_structured(self, prompt, *args):
            result = super().generate_structured(prompt, *args)
            if outcome == 'failed':
                raise RuntimeError('Synthetic transport failure')
            cancel.set()
            return result

    adapter = InterruptedAdapter()
    with pytest.raises(DomainError) as error:
        ingest_live(store, project.id, data, 'synthetic-spec.docx', 'ollama', settings(), adapter, cancel=cancel)
    assert error.value.code == ('unavailable_provider' if outcome == 'failed' else 'cancelled')
    assert adapter.calls == 1 and usage_summary(store, project.id)['calls'] == 1
    assert store.get(project.id) == before
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM changes').fetchone()[0] == 0


@pytest.mark.parametrize('purge', [False, True], ids=['trashed', 'emptied-trash'])
def test_preflight_and_background_reimport_are_project_local_after_deletion(tmp_path, monkeypatch, purge):
    store = Store(tmp_path / 'background.sqlite')
    adapter = DocumentAdapter()
    held = HeldExecutor()
    monkeypatch.setattr(main, 'store', store)
    monkeypatch.setattr(jobs, 'EXECUTOR', held)
    monkeypatch.setattr(documents, 'OllamaAdapter', lambda selected_settings: adapter)
    monkeypatch.setattr(Settings, 'environment', classmethod(lambda cls: settings()))
    client = TestClient(main.app)
    data = document_bytes()
    files = {'file': ('synthetic-spec.docx', data, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}

    for iteration in range(2):
        project_response = client.post('/api/projects', json={'name': 'New architecture'})
        assert project_response.status_code == 200
        project = Project.model_validate(project_response.json())
        # Mock can save a parsed source without a draft.
        if iteration == 0:
            mock_response = client.post(f'/api/projects/{project.id}/sources', data={'provider': 'mock'}, files=files)
            assert mock_response.status_code == 200 and mock_response.json()['proposal'] is None
            project = store.get(project.id)
        before = project.model_dump_json()
        calls_before = adapter.calls
        preflight = client.post(f'/api/projects/{project.id}/source-preflight', data={'provider': 'ollama'}, files=files)
        assert preflight.status_code == 200 and preflight.json()['requests'] == 1
        assert adapter.calls == calls_before and usage_summary(store, project.id)['calls'] == 0
        assert store.get(project.id).model_dump_json() == before
        # The queued job reads the exact bytes that preflight already cached.
        queued = client.post(f'/api/projects/{project.id}/source-jobs', files=files,
                             data={'provider': 'ollama', 'base_revision': str(project.revision),
                                   'base_views': json.dumps({key: view.revision for key, view in project.views.items()})})
        assert queued.status_code == 200 and queued.json()['status'] == 'queued'
        assert adapter.calls == calls_before and store.get(project.id).model_dump_json() == before
        held.run_all()
        completed = client.get(f"/api/jobs/{queued.json()['id']}")
        assert completed.status_code == 200 and completed.json()['status'] == 'completed'
        result = completed.json()['result']
        assert not result.get('duplicate') and result['proposal']['state'] == 'pending'
        assert adapter.calls == calls_before + 1 and usage_summary(store, project.id)['calls'] == 1
        assert store.get(project.id).model_dump_json() == before
        accepted = client.post(f"/api/changes/{result['proposal']['id']}/accept")
        assert accepted.status_code == 200 and len(accepted.json()['components']) == 1
        assert len(accepted.json()['sources']) == 1
        if iteration == 0:
            assert client.post(f'/api/projects/{project.id}/trash').status_code == 200
            if purge:
                emptied = client.post('/api/projects/trash/empty', json={'confirmed': True, 'project_ids': [project.id]})
                assert emptied.status_code == 200 and emptied.json()['deleted_count'] == 1
            assert client.get('/api/projects').json() == []
