"""Provider citations retain exact source text after harmless whitespace repair."""
import json
from pathlib import Path

import pytest

from apps.api.app.domain.commands import DomainError, apply, command
from apps.api.app.domain.models import Passage, Project, Source
from apps.api.app.ingest.parser import parse
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.orchestration.live import proposal_from_envelope
from apps.api.app.providers.budget import usage_summary
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope, ProviderResult, Usage
from apps.api.app.storage.store import Store


def source(text, locator='page/1'):
    return Source(id='spec', name='Synthetic specification', kind='document',
                  sha256='spec', canonical_id='spec',
                  passages=[Passage(locator=locator, text=text)])


def envelope(excerpt, locator='page/1', source_id='S1'):
    return Envelope(operations=[{
        'op': 'add', 'entity': 'components', 'id': 'tmp:database',
        'value_json': json.dumps({'name': 'Inventory database', 'role': 'database'}),
    }], claims=[{
        'source_id': source_id, 'locator': locator, 'excerpt': excerpt,
        'target_id': 'tmp:database', 'field': 'record', 'value_json': 'null',
    }], tool=None, message='Review the database.')


@pytest.mark.parametrize('text,quote,expected', [
    ('Use the Inventory\ndatabase.', 'Inventory database', 'Inventory\ndatabase'),
    ('Use the Inventory  \r\n\t database.', ' Inventory database ', 'Inventory  \r\n\t database'),
    ('Use the Inventory\u00a0database.', 'Inventory database', 'Inventory\u00a0database'),
    ('Use the Inventory database.', 'Inventory\n database', 'Inventory database'),
    ('Use the Inventory\ndatabase.', 'Inventory\ndatabase', 'Inventory\ndatabase'),
    ('Inventory (database) uses TCP 5432.', 'Inventory (database)', 'Inventory (database)'),
])
def test_provider_citations_keep_original_source_characters(text, quote, expected):
    project = Project()
    proposal = proposal_from_envelope(project, source(text), envelope(quote), source_alias='S1')
    accepted = apply(project, proposal)
    assert accepted.claims[0].excerpt == expected
    assert accepted.claims[0].excerpt in accepted.sources[0].passages[0].text
    assert accepted.claims[0].locator == 'page/1'
    assert accepted.claims[0].target_id == accepted.components[0].id
    assert not project.components and not project.sources


@pytest.mark.parametrize('quote,locator', [
    ('Inventory database', 'page/2'),
    ('Inventory ledger', 'page/1'),
    ('Inventory Database', 'page/1'),
    ('Inventorydatabase', 'page/1'),
    ('Inventory ... database', 'page/1'),
    ('Inventory database uses TCP 443.', 'page/1'),
    ('   \n', 'page/1'),
    ('', 'page/1'),
])
def test_invalid_provider_citations_explain_the_section_and_preserve_design(quote, locator):
    project = Project()
    with pytest.raises(DomainError) as failure:
        proposal_from_envelope(project, source('Inventory\ndatabase uses TCP 5432.'),
                               envelope(quote, locator), source_alias='S1')
    assert failure.value.code == 'provider_output'
    assert locator in failure.value.message
    assert 'citation' in failure.value.message.lower()
    assert 'Your current design was not changed.' in failure.value.message
    assert not project.components and not project.sources


def test_words_cannot_be_joined_across_source_passages():
    document = source('Inventory')
    document.passages.append(Passage(locator='page/2', text='database'))
    with pytest.raises(DomainError):
        proposal_from_envelope(Project(), document, envelope('Inventory database'), source_alias='S1')


def test_wrong_source_id_remains_rejected():
    with pytest.raises(DomainError, match='supplied source context'):
        proposal_from_envelope(Project(), source('Inventory database'),
                               envelope('Inventory database', source_id='S2'), source_alias='S1')


def test_manual_claims_still_require_exact_source_text():
    project = Project()
    document = source('Inventory\ndatabase')
    with pytest.raises(DomainError, match='Unresolvable evidence'):
        apply(project, command(project, [
            {'op': 'add', 'entity': 'sources', 'id': document.id,
             'value': document.model_dump(exclude={'id'})},
            {'op': 'add', 'entity': 'claims', 'id': 'claim', 'value': {
                'source_id': document.id, 'source_version': '1.0', 'source_kind': 'document',
                'locator': 'page/1', 'excerpt': 'Inventory database', 'target_id': 'candidate', 'field': 'record',
            }},
        ]))


def test_inventory_pdf_import_restores_wrapped_quote_before_review(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'fixtures/demos/inventory/techspec.pdf'
    data = path.read_bytes()
    document = parse(data, path.name)
    quote = 'The application initiates PostgreSQL on TCP 5432 to Inventory database.'
    assert quote not in document.passages[0].text  # The PDF contains a line break.
    assert quote in ' '.join(document.passages[0].text.split())

    class Adapter:
        name = 'openai'
        model = 'gpt-5.4-mini'
        calls = 0

        def generate_structured(self, *args):
            self.calls += 1
            return ProviderResult(model=self.model, finish_status='completed', usage=Usage(),
                                  content=envelope(quote))

    store = Store(tmp_path / 'pdf.sqlite')
    project = store.create(Project())
    adapter = Adapter()
    result = ingest_live(store, project.id, data, path.name, 'openai',
                         Settings(allow_cloud=True, max_calls=1), adapter)
    assert adapter.calls == 1 and store.get(project.id) == project
    assert result['proposal'].state == 'pending'
    accepted = store.commit(result['proposal'])
    assert len(accepted.components) == 1
    assert accepted.claims[0].excerpt == quote.replace('The application', 'The\napplication')
    assert accepted.claims[0].excerpt in accepted.sources[0].passages[0].text
    assert usage_summary(store, project.id)['calls'] == 1
    assert store.get(project.id) == accepted
