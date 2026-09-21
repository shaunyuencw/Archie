from pathlib import Path

import pytest

from apps.api.app.domain.commands import DomainError, command
from apps.api.app.domain.models import Project
from apps.api.app.policies.categories import CATEGORIES
from apps.api.app.policies.library import NewPolicy, add_policy, clauses, list_library
from apps.api.app.policies.recommendations import recommendations_for, proposal_recommendations, with_policy_suggestions
from apps.api.app.storage.store import Store


def demo(name):
    project=Project.model_validate_json(Path(f'fixtures/demos/{name}/project.json').read_text())
    project.policy_ids=[]
    return project


def test_library_groups_cover_every_clause_and_classify_local_drafts(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_POLICY_DB',str(tmp_path/'policy.sqlite'))
    valid={category['id'] for category in CATEGORIES}
    data=list_library()
    assert len(data['clauses'])==42
    assert all(clause['category'] in valid for clause in data['clauses'])
    assert {clause['category'] for clause in data['clauses']}==valid-{'local-drafts'}
    custom=add_policy(NewPolicy(title='Trial data owner',text='Record the owner of the wireless trial data.',applicability='Wireless trial',tags=['wireless']))
    assert next(clause for clause in clauses() if clause['id']==custom['id'])['category']=='devices-testbed'


def test_recommendations_are_relevant_read_only_and_exclude_selected_clauses():
    project=demo('portal');before=project.model_dump_json()
    items=recommendations_for(project);ids={item['policy_id'] for item in items}
    assert {'ARCH-BOUND-01','ARCH-SEG-01','ARCH-DAT-01','ARCH-BAK-01','ARCH-AVL-01'}<=ids
    assert not ids&{'ARCH-ROB-01','ARCH-WLS-01','ARCH-CLD-01','ARCH-HYB-01'}
    assert all(item['origin']=='rules' and item['reason'] and item['title'] for item in items)
    assert project.model_dump_json()==before
    project.policy_ids=list(ids)
    assert recommendations_for(project)==[]
    assert recommendations_for(Project(policy_ids=[]))==[]


def test_robotics_and_hybrid_suggestions_follow_actual_assets_and_connections():
    project=demo('robotics')
    ids={item['policy_id'] for item in recommendations_for(project)}
    assert {'ARCH-TST-01','ARCH-HND-01','ARCH-WLS-01','ARCH-ROB-01','ARCH-TRL-01','ARCH-HYB-01'}<=ids
    cloud_ids={component.id for component in project.components if component.asset_id.startswith('aws-')}
    project.interfaces=[interface for interface in project.interfaces if not ((interface.source in cloud_ids)!=(interface.target in cloud_ids))]
    assert 'ARCH-HYB-01' not in {item['policy_id'] for item in recommendations_for(project)}
    misleading=Project(policy_ids=[],name='AWS robotics hybrid trial',components=[{'id':'s','name':'AWS robot','role':'AWS cloud','asset_id':'server'}])
    assert not {'ARCH-CLD-01','ARCH-HYB-01','ARCH-ROB-01'}&{item['policy_id'] for item in recommendations_for(misleading)}


def test_local_drafts_are_suggested_only_for_matching_canonical_signal_tags(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_POLICY_DB',str(tmp_path/'policy.sqlite'))
    matching=add_policy(NewPolicy(title='Local recovery review',text='Record an owner for the backup restoration test.',applicability='Stored data',tags=['backup']))
    unrelated=add_policy(NewPolicy(title='Unrelated review',text='Ask the owner about the unrelated review topic.',applicability='Other systems',tags=['unrelated']))
    items={item['policy_id']:item for item in recommendations_for(demo('portal'))}
    assert matching['id'] in items and unrelated['id'] not in items
    assert 'local draft tag' in items[matching['id']]['reason']


def test_policy_suggestions_are_explicit_and_commit_with_the_architecture(tmp_path):
    store=Store(tmp_path/'projects.sqlite');project=store.create(Project(policy_ids=['DEMO-ZON-01']))
    proposal=store.preview(command(project,[{'op':'add','entity':'components','id':'service','value':{'name':'API service','role':'application','asset_id':'api-service'}}]))
    items=proposal_recommendations(store,proposal.id)
    assert 'ARCH-OWN-01' in {item['policy_id'] for item in items}
    assert not store.get(project.id).components and store.get(project.id).policy_ids==['DEMO-ZON-01']
    assert with_policy_suggestions(project,proposal,[]) is proposal
    for invalid in [['made-up'],['ARCH-ROB-01'],['ARCH-OWN-01','ARCH-OWN-01']]:
        with pytest.raises(DomainError):with_policy_suggestions(project,proposal,invalid)
    combined=with_policy_suggestions(project,proposal,['ARCH-OWN-01'])
    accepted=store.commit(combined)
    assert accepted.revision==project.revision+1
    assert accepted.components[0].id=='service'
    assert accepted.policy_ids==['DEMO-ZON-01','ARCH-OWN-01']
    assert combined.id==proposal.id and combined.request_id==proposal.request_id
    restored=store.undo(command(accepted,[{'op':'notes','value':{}}]))
    assert not restored.components and restored.policy_ids==['DEMO-ZON-01']
    with pytest.raises(DomainError,match='no longer pending'):proposal_recommendations(store,proposal.id)
