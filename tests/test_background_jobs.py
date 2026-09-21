import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import apps.api.app.main as main
from apps.api.app.domain.commands import DomainError, command
from apps.api.app.domain.models import Project
from apps.api.app.orchestration import jobs
from apps.api.app.policies.recommendations import with_policy_suggestions
from apps.api.app.storage.store import Store


class HeldExecutor:
    def __init__(self):self.calls=[]
    def submit(self,fn,*args):
        self.calls.append((fn,args))
        return SimpleNamespace(cancel=lambda:False)
    def run_all(self):
        while self.calls:
            fn,args=self.calls.pop(0);fn(*args)


def views(project):return {key:view.revision for key,view in project.views.items()}


def prompt_request(project,text='Existing VMS in Infrastructure; two workstations in Client; VAP management/integration services in Z1; VAP analytics in Z2.'):
    change=command(project,[{'op':'notes','value':{'text':project.notes}}])
    return main.RunRequest(**change.model_dump(),prompt=text,provider='mock')


def test_prompt_job_is_durable_and_rejects_a_stale_snapshot_before_work(tmp_path,monkeypatch):
    store=Store(tmp_path/'jobs.sqlite');project=store.create(Project());held=HeldExecutor();monkeypatch.setattr(jobs,'EXECUTOR',held)
    request=prompt_request(project);job=jobs.schedule_prompt(store,project.id,request)
    assert job['status']=='queued' and store.get_job(job['id'])['project_name']==project.name
    with pytest.raises(DomainError,match='background action'):
        jobs.schedule_prompt(store,project.id,prompt_request(project))
    changed=store.commit(command(project,[{'op':'notes','value':{'text':'A newer edit'}}]))
    held.run_all()
    failed=store.get_job(job['id'])
    assert failed['status']=='failed' and failed['error']['code']=='stale_revision'
    assert store.get(project.id)==changed and not store.get(project.id).sources


def test_completed_job_hydrates_the_live_accepted_proposal_body(tmp_path):
    store=Store(tmp_path/'jobs.sqlite');project=store.create(Project(policy_ids=[]))
    proposal=store.preview(command(project,[{'op':'add','entity':'components','id':'service','value':{'name':'API','role':'application','asset_id':'api-service'}}]))
    job=store.create_job(project.id,'prompt',{'provider':'mock','base_revision':0,'base_views':views(project)})
    assert store.start_job(job['id']);store.complete_job(job['id'],{'proposal':proposal})
    combined=with_policy_suggestions(project,proposal,['ARCH-OWN-01'])
    accepted=store.commit(combined)
    hydrated=store.get_job(job['id'])['result']['proposal']
    assert hydrated['state']=='accepted'
    assert any(item['op']=='policy_selection' and item['value']['policy_ids']==['ARCH-OWN-01'] for item in hydrated['operations'])
    assert accepted.policy_ids==['ARCH-OWN-01']


def test_jobs_are_bounded_recovered_without_replay_and_block_trash_purge(tmp_path):
    store=Store(tmp_path/'jobs.sqlite');projects=[store.create(Project(name=f'Project {index}')) for index in range(9)]
    for project in projects[:8]:store.create_job(project.id,'prompt',{'provider':'mock','base_revision':0,'base_views':views(project)})
    with pytest.raises(DomainError) as busy:store.create_job(projects[8].id,'prompt',{'provider':'mock','base_revision':0,'base_views':views(projects[8])})
    assert busy.value.code=='job_busy'
    store.trash(projects[0].id)
    with pytest.raises(DomainError) as blocked:store.empty_trash([projects[0].id])
    assert blocked.value.code=='project_busy'
    assert jobs.recover_interrupted_jobs(store)==8
    recovered=store.get_job(store.list_jobs()[0]['id'])
    assert recovered['status']=='failed' and recovered['error']['code']=='job_interrupted'
    assert store.empty_trash([projects[0].id])['deleted_count']==1


def test_actual_background_thread_keeps_other_projects_readable_while_a_source_waits(tmp_path,monkeypatch):
    store=Store(tmp_path/'jobs.sqlite');owner=store.create(Project(name='Working'));other=store.create(Project(name='Other'))
    started=threading.Event();release=threading.Event();executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='test-job')
    def blocked_ingest(*args,**kwargs):
        started.set();assert release.wait(2)
        return {'proposal':None,'message':'Document processed without a proposal.'}
    monkeypatch.setattr(jobs,'EXECUTOR',executor);monkeypatch.setattr(jobs,'ingest',blocked_ingest)
    before=store.get(owner.id).model_dump_json()
    try:
        job=jobs.schedule_source(store,owner.id,b'Synthetic source','spec.txt','mock',owner.revision,views(owner))
        assert started.wait(1) and store.get_job(job['id'])['status']=='running'
        assert store.get(other.id)==other and {item['id'] for item in store.list()}=={owner.id,other.id}
        release.set();executor.shutdown(wait=True)
        assert store.get_job(job['id'])['status']=='completed' and store.get(owner.id).model_dump_json()==before
    finally:
        release.set();executor.shutdown(wait=True,cancel_futures=True)


def test_cancelling_a_queued_job_skips_work_and_a_late_proposal_is_rejected(tmp_path,monkeypatch):
    store=Store(tmp_path/'jobs.sqlite');project=store.create(Project());held=HeldExecutor();monkeypatch.setattr(jobs,'EXECUTOR',held)
    queued=jobs.schedule_prompt(store,project.id,prompt_request(project))
    cancelled=jobs.cancel_job(store,queued['id'])
    assert cancelled['status']=='cancelled' and cancelled['cancel_requested_at']
    held.run_all()
    assert store.get_job(queued['id'])['status']=='cancelled' and not store.get(project.id).sources

    proposal=store.preview(command(project,[{'op':'add','entity':'components','id':'late','value':{'name':'Late API','role':'application'}}]))
    running=store.create_job(project.id,'prompt',{'provider':'mock','base_revision':0,'base_views':views(project)})
    assert store.start_job(running['id'])
    assert jobs.cancel_job(store,running['id'])['status']=='cancelling'
    store.complete_job(running['id'],{'proposal':proposal})
    assert store.get_job(running['id'])['status']=='cancelled' and store.get_job(running['id'])['result'] is None
    assert store.get_job(running['id'])['request']['discarded_proposal_id']==proposal.id
    assert store.change(proposal.id).state=='rejected'


def test_running_cancel_signals_the_worker_and_blocks_late_source_writes(tmp_path,monkeypatch):
    store=Store(tmp_path/'jobs.sqlite');project=store.create(Project());started=threading.Event();executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='cancel-job')
    def blocked_ingest(*args,cancel=None,job_id=None,**kwargs):
        started.set();assert cancel is not None and cancel.wait(2)
        with pytest.raises(DomainError,match='cancelled'):
            store.commit(command(store.get(project.id),[{'op':'notes','value':{'text':'must not persist'}}]),job_id=job_id)
        return {'proposal':None,'message':'discarded'}
    monkeypatch.setattr(jobs,'EXECUTOR',executor);monkeypatch.setattr(jobs,'ingest',blocked_ingest)
    before=store.get(project.id).model_dump_json()
    try:
        job=jobs.schedule_source(store,project.id,b'Synthetic source','spec.txt','mock',project.revision,views(project))
        assert started.wait(1) and store.get_job(job['id'])['status']=='running'
        assert jobs.cancel_job(store,job['id'])['status']=='cancelling'
        executor.shutdown(wait=True)
        finished=store.get_job(job['id'])
        assert finished['status']=='cancelled' and finished['result'] is None and store.get(project.id).model_dump_json()==before
    finally:
        executor.shutdown(wait=True,cancel_futures=True)


def test_job_api_contract_source_continue_and_policy_review_use_no_live_model(tmp_path,monkeypatch):
    store=Store(tmp_path/'api.sqlite');held=HeldExecutor();monkeypatch.setattr(main,'store',store);monkeypatch.setattr(jobs,'EXECUTOR',held)
    client=TestClient(main.app)
    created=client.post('/api/projects',json={'name':'Background API'}).json();project=Project.model_validate(created)
    request=prompt_request(project)
    response=client.post(f'/api/projects/{project.id}/jobs',json={'kind':'prompt',**request.model_dump()})
    assert response.status_code==200 and response.json()['status']=='queued'
    job=response.json();assert client.get('/api/jobs').json()[0]['id']==job['id']
    held.run_all()
    detail=client.get('/api/jobs/'+job['id']).json()
    assert detail['status']=='completed' and detail['result']['proposal']['state']=='pending'
    assert client.post('/api/jobs/'+job['id']+'/dismiss',json={}).json()['dismissed_at']
    assert client.get('/api/jobs').json()==[]
    invalid=client.post(f'/api/projects/{project.id}/jobs',json={'kind':'prompt'})
    assert invalid.status_code==422 and 'current project snapshot' in invalid.json()['message']

    cancelled_project=store.create(Project(name='Cancelled API'))
    cancelled_request=prompt_request(cancelled_project)
    queued=client.post(f'/api/projects/{cancelled_project.id}/jobs',json={'kind':'prompt',**cancelled_request.model_dump()}).json()
    cancelled=client.post('/api/jobs/'+queued['id']+'/cancel',json={})
    assert cancelled.status_code==200 and cancelled.json()['status']=='cancelled'
    held.run_all()
    assert client.get('/api/jobs/'+queued['id']).json()['status']=='cancelled'

    source_project=store.create(Project(name='Source job'))
    source_response=client.post(f'/api/projects/{source_project.id}/source-jobs',data={'provider':'mock','base_revision':'0','base_views':json.dumps(views(source_project))},files={'file':('spec.txt',b'No supported source facts.','text/plain')})
    assert source_response.status_code==200 and source_response.json()['kind']=='source'
    continue_request=prompt_request(source_project)
    continue_payload={key:value for key,value in continue_request.model_dump().items() if key!='prompt'}
    assert client.post(f'/api/projects/{source_project.id}/sources/source/continue-jobs',json=continue_payload).status_code==409

    review_project=store.create(Project(name='Review job',policy_ids=['ARCH-BAK-01']))
    review_response=client.post(f'/api/projects/{review_project.id}/policy-review-jobs',json={'base_revision':0,'provider':'mock','request_id':'background-review'})
    assert review_response.status_code==200 and review_response.json()['kind']=='policy_review'
    held.run_all()
    review=client.get('/api/jobs/'+review_response.json()['id']).json()
    assert review['status']=='completed' and review['result']['review']['mode']=='deterministic_demo'
