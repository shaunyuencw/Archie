"""Global, local-only policy catalogue. Project applicability lives in its snapshot."""
import json
import os
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..domain.commands import DomainError
from .categories import CATEGORIES, category_for

ROOT = Path(__file__).resolve().parents[4]
router = APIRouter(prefix='/api/policies', tags=['Policy library'])


def legacy_clauses():
    return json.loads((ROOT / 'fixtures/policies/clauses.json').read_text(encoding='utf-8'))['clauses']


def database_path():
    return Path(os.getenv('APP_POLICY_DB', os.getenv('APP_DB', 'data/workbench.sqlite')))


def custom_clauses():
    path = database_path()
    if not path.exists():
        return []
    with sqlite3.connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='policy_library'").fetchone():
            return []
        return [json.loads(row[0]) for row in db.execute('SELECT body FROM policy_library ORDER BY id')]


def clauses():
    original = [dict(c, title=c['text'].rstrip('.'), pack='Original demonstration') for c in legacy_clauses()]
    expanded = [dict(c, pack='Architecture essentials') for c in json.loads((ROOT / 'fixtures/policies/library.json').read_text(encoding='utf-8'))['clauses']]
    return [dict(clause,category=category_for(clause)) for clause in original + expanded + custom_clauses()]


def selected_ids(project):
    return [c['id'] for c in legacy_clauses()] if project.policy_ids is None else project.policy_ids


def validate_selection(value):
    if set(value) != {'policy_ids'}:
        raise DomainError('invalid_input', 'Policy selection accepts only policy_ids.')
    ids = value.get('policy_ids')
    if not isinstance(ids, list) or len(ids) > 100 or any(not isinstance(i, str) for i in ids):
        raise DomainError('invalid_input', 'Choose a list of at most 100 policy IDs.')
    if len(ids) != len(set(ids)):
        raise DomainError('invalid_input', 'Policy IDs must be unique.')
    unknown = set(ids) - {c['id'] for c in clauses()}
    if unknown:
        raise DomainError('invalid_input', 'Unknown policy: ' + ', '.join(sorted(unknown)))
    return ids


class NewPolicy(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=3, max_length=140)
    text: str = Field(min_length=15, max_length=2400)
    applicability: str = Field(min_length=3, max_length=500)
    exceptions: str = Field(default='No exception documented; review with the design owner.', max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=12)

    @field_validator('title', 'text', 'applicability')
    @classmethod
    def non_blank(cls, value):
        if not value.strip():
            raise ValueError('Policy fields cannot be blank.')
        return value.strip()

    @field_validator('tags')
    @classmethod
    def bounded_tags(cls, value):
        if any(not tag.strip() or len(tag) > 60 for tag in value):
            raise ValueError('Use non-empty tags up to 60 characters.')
        return list(dict.fromkeys(tag.strip() for tag in value))


@router.get('')
def list_library(q: str = ''):
    all_clauses = clauses()
    terms = q.lower().split()
    visible = [c for c in all_clauses if all(term in ' '.join([c['id'], c['title'], c['text'], *c['tags']]).lower() for term in terms)]
    essentials = [c['id'] for c in all_clauses if c['pack'] == 'Architecture essentials']
    return {'synthetic': True, 'clauses': visible, 'categories':CATEGORIES, 'legacy_ids': [c['id'] for c in legacy_clauses()],
            'presets': [{'id': 'essentials', 'name': 'Architecture essentials', 'policy_ids': essentials},
                        {'id': 'original', 'name': 'Original demo policies', 'policy_ids': [c['id'] for c in legacy_clauses()]}]}


@router.post('', status_code=201)
def add_policy(request: NewPolicy):
    clause = dict(id='LOCAL-' + uuid4().hex[:12].upper(), title=request.title, text=request.text,
                  applicability=[request.applicability], exceptions=request.exceptions, tags=request.tags,
                  implementation='manual_review', version='1.0', pack='Your local drafts')
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS policy_library(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        db.execute('INSERT INTO policy_library VALUES(?,?)', (clause['id'], json.dumps(clause)))
    return clause
