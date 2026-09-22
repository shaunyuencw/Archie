import json
from types import SimpleNamespace as NS

import httpx
import pytest

from apps.api.app.domain.commands import DomainError, command
from apps.api.app.domain.models import Project
from apps.api.app.orchestration.policy_review import ReviewRequest, ReviewBody, latest_review, review_project, verified_body
from apps.api.app.providers.adapters import OpenAIAdapter
from apps.api.app.providers.budget import usage_summary
from apps.api.app.providers.config import Settings
from apps.api.app.storage.store import Store


def setup(tmp_path):
    store=Store(tmp_path/'reviews.sqlite')
    project=store.create(Project(name='Review example',policy_ids=['ARCH-SEG-01','ARCH-BAK-01'],
        zones=[{'id':'client','name':'Client'},{'id':'z2','name':'Z2'}],
        components=[{'id':'pc','name':'Operator','role':'user','asset_id':'workstation'},{'id':'db','name':'Records','role':'database','asset_id':'database'}],
        deployments=[{'id':'p','component_id':'pc','zone_id':'client'},{'id':'d','component_id':'db','zone_id':'z2'}],
        interfaces=[{'id':'bypass','source':'pc','target':'db'}]))
    return store,project


def transport(body, calls, fail=False, mutate=False, title=False):
    def create(**kwargs):
        calls.append(kwargs)
        if fail:raise httpx.ReadTimeout('Ambiguous transport failure')
        envelope={'operations':[],'claims':[],'tool':None,'message':json.dumps(body),'project_name':None}
        if mutate:envelope['operations']=[{'op':'remove','entity':'components','id':'db','value':{'fields':[]},'proposal_reason':None}]
        if title:envelope['project_name']='Unexpected rename'
        return NS(status='completed',output_text=json.dumps(envelope),model='gpt-5.4-mini',usage=NS(input_tokens=200,input_tokens_details=NS(cached_tokens=0),output_tokens=150,output_tokens_details=NS(reasoning_tokens=0)))
    return NS(responses=NS(create=create))


BODY={'summary':'Review the direct path and document recovery.','assessments':[{'policy_id':'ARCH-SEG-01','status':'potential_concern','message':'The direct Client to Z2 path needs review.','affected_ids':['bypass'],'citations':[]},{'policy_id':'ARCH-BAK-01','status':'insufficient_information','message':'No recovery target or restore evidence was supplied.','affected_ids':['db'],'citations':[]}]}


def test_mock_advisory_is_explicit_cached_and_stale_without_model_usage(tmp_path):
    store,project=setup(tmp_path);before=store.get(project.id).model_dump_json()
    assert latest_review(store,project.id)['review'] is None
    result=review_project(store,project.id,ReviewRequest(base_revision=0))
    assert result['mode']=='deterministic_demo' and result['cost_usd']==0
    assert result['assessments'][0]['status']=='potential_concern'
    assert store.get(project.id).model_dump_json()==before
    assert usage_summary(store,project.id)['calls']==0
    assert latest_review(store,project.id)['review']['cached'] is True
    assert latest_review(store,project.id)['review']['id']==result['id']
    assert review_project(store,project.id,ReviewRequest(base_revision=0))['cached']
    changed=store.commit(command(project,[{'op':'notes','value':{'text':'New accepted note'}}]))
    assert latest_review(store,project.id)['review']['stale']
    with pytest.raises(DomainError,match='project changed'):
        review_project(store,project.id,ReviewRequest(base_revision=project.revision))
    assert changed.revision==1


def test_mocked_openai_review_uses_budget_and_selected_policies_only(tmp_path):
    store,project=setup(tmp_path);calls=[];settings=Settings(allow_cloud=True,max_input=32000)
    adapter=OpenAIAdapter(settings,transport(BODY,calls))
    before=project.model_dump_json()
    result=review_project(store,project.id,ReviewRequest(base_revision=0,provider='openai'),settings,adapter)
    supplied=json.loads(calls[0]['input'][1]['content'])
    assert {clause['id'] for clause in supplied['selected_policies']}==set(project.policy_ids)
    assert len(calls)==1 and calls[0]['store'] is False
    assert result['mode']=='ai_advisory' and result['cost_usd']>0
    assert usage_summary(store,project.id)['calls']==1
    assert store.get(project.id).model_dump_json()==before
    cached=review_project(store,project.id,ReviewRequest(base_revision=0,provider='openai'),settings,adapter)
    assert cached['cached'] and len(calls)==1


def test_unsupported_citations_and_unselected_policy_are_not_presented_as_verified(tmp_path):
    store,project=setup(tmp_path);calls=[];settings=Settings(allow_cloud=True,max_input=32000)
    body={'summary':'Advisory only.','assessments':[{'policy_id':'ARCH-SEG-01','status':'no_issue_identified','message':'A source reference was proposed.','affected_ids':['invented-object'],'citations':[{'source_id':'invented-source','locator':'page/99','excerpt':'invented'}]},{'policy_id':'ARCH-TLS-01','status':'no_issue_identified','message':'Not selected.','affected_ids':[],'citations':[]}]}
    result=review_project(store,project.id,ReviewRequest(base_revision=0,provider='openai'),settings,OpenAIAdapter(settings,transport(body,calls)))
    assert result['warnings']
    assert {item['policy_id'] for item in result['assessments']}==set(project.policy_ids)
    assert result['assessments'][0]['status']=='insufficient_information'
    assert result['assessments'][0]['reference_check']=='flagged'
    assert not result['assessments'][0]['citations'] and not result['assessments'][0]['affected_ids']
    assert result['assessments'][1]['reference_check']=='not_assessed'


@pytest.mark.parametrize('failure',['cloud_disabled','budget','context','transport','mutation','title'])
def test_failed_review_preserves_model_and_never_falls_back(tmp_path,failure):
    store,project=setup(tmp_path);calls=[];before=project.model_dump_json()
    settings=Settings(allow_cloud=failure!='cloud_disabled',max_input=100 if failure=='context' else 32000,action_usd=.00001 if failure=='budget' else .10)
    adapter=OpenAIAdapter(settings,transport(BODY,calls,fail=failure=='transport',mutate=failure=='mutation',title=failure=='title'))
    with pytest.raises(DomainError):review_project(store,project.id,ReviewRequest(base_revision=0,provider='openai'),settings,adapter)
    assert store.get(project.id).model_dump_json()==before
    assert latest_review(store,project.id,'openai')['review'] is None
    assert len(calls)==(1 if failure in ['transport','mutation','title'] else 0)
    if failure=='transport':assert usage_summary(store,project.id)['records'][0]['status']=='unresolved'


def test_empty_selection_never_calls_provider(tmp_path):
    store=Store(tmp_path/'reviews.sqlite');project=store.create(Project(policy_ids=[]))
    with pytest.raises(DomainError,match='Select policies'):
        review_project(store,project.id,ReviewRequest(base_revision=0,provider='openai'))
    assert usage_summary(store,project.id)['calls']==0


def test_valid_citations_are_checked_against_exact_supplied_locator_and_excerpt():
    evidence=[{'source_id':'spec','locator':'section/2','excerpt':'The backup retention is undecided.'}]
    body=ReviewBody.model_validate({'summary':'Review needed.','assessments':[{'policy_id':'ARCH-BAK-01','status':'insufficient_information','message':'Decide the retention period.','affected_ids':['db'],'citations':[evidence[0]]}]})
    checked=verified_body(body,['ARCH-BAK-01'],evidence,{'db'})
    assert checked['assessments'][0]['reference_check']=='verified_references'
    assert checked['assessments'][0]['citations']==evidence
    body.assessments[0].citations[0].locator='section/9'
    checked=verified_body(body,['ARCH-BAK-01'],evidence,{'db'})
    assert checked['assessments'][0]['reference_check']=='flagged'
    assert checked['assessments'][0]['citations']==[]


@pytest.mark.parametrize('first_id,second_id',[('review_%','review_AB'),('review','review:mock:0')])
def test_latest_review_cannot_match_another_project_through_imported_id(first_id,second_id,tmp_path):
    store=Store(tmp_path/'reviews.sqlite')
    first=store.create(Project(id=first_id,policy_ids=['ARCH-BAK-01']))
    second=store.create(Project(id=second_id,policy_ids=['ARCH-BAK-01']))
    review_project(store,first.id,ReviewRequest(base_revision=0))
    review_project(store,second.id,ReviewRequest(base_revision=0))
    loaded=latest_review(store,first.id)['review']
    assert loaded['project_id']==first.id
    assert loaded['assessments'][0]['title']=='Design backups that can be restored'


def test_project_trashed_during_review_does_not_gain_cached_content(tmp_path):
    store,project=setup(tmp_path);calls=[];settings=Settings(allow_cloud=True,max_input=32000)
    client=transport(BODY,calls)
    generate=client.responses.create
    def trash_during_call(**kwargs):
        store.trash(project.id)
        return generate(**kwargs)
    client.responses.create=trash_during_call
    with pytest.raises(DomainError,match='Trash'):
        review_project(store,project.id,ReviewRequest(base_revision=0,provider='openai'),settings,OpenAIAdapter(settings,client))
    with store.connect() as db:
        assert db.execute('SELECT count(*) FROM cache').fetchone()[0]==0
        row=db.execute('SELECT status,result FROM runs WHERE project_id=?',(project.id,)).fetchone()
        assert row['status']=='failed' and json.loads(row['result'])=={'code':'project_trashed'}
    assert usage_summary(store,project.id)['calls']==1 and usage_summary(store,project.id)['total']>0
