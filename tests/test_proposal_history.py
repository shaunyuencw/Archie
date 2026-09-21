from apps.api.app.domain.models import Project
from apps.api.app.domain.commands import command
from apps.api.app.orchestration.history import proposal_history
from apps.api.app.storage.store import Store


def test_review_history_keeps_decisions_and_prompts_after_dismiss_and_undo(tmp_path):
    store=Store(tmp_path/'history.sqlite');project=store.create(Project())
    draft=store.preview(command(project,[{'op':'add','entity':'components','id':'api','value':{'name':'API service','role':'application'}}],origin='assistant'))
    job=store.create_job(project.id,'prompt',{'prompt':'Add an API service','provider':'mock'})
    store.start_job(job['id']);store.complete_job(job['id'],{'proposal':draft});store.commit(draft);store.dismiss_job(job['id'])
    accepted=store.get(project.id);store.undo(command(accepted,[{'op':'notes','value':{}}]))
    another=store.preview(command(store.get(project.id),[{'op':'project_name','value':{'name':'A better title'}}],origin='assistant'))
    store.reject(another.id)
    store.preview(command(store.get(project.id),[{'op':'notes','value':{'text':'Still pending'}}],origin='assistant'))
    loaded=proposal_history(Store(tmp_path/'history.sqlite'),project.id)
    assert [item['state'] for item in loaded['items']]==['rejected','accepted']
    assert loaded['items'][1]['prompt']=='Add an API service'
    assert loaded['items'][1]['summary']==['Add API service']
    assert loaded['items'][0]['summary']==['Name project “A better title”']
    assert not store.get(project.id).components
    assert proposal_history(store,store.create(Project()).id)['items']==[]
    page=proposal_history(store,project.id,limit=1)
    assert page['next_cursor'] is not None
    earlier=proposal_history(store,project.id,before=page['next_cursor'],limit=1)
    assert earlier['items'][0]['id']==draft.id and earlier['next_cursor'] is None


def test_cancelled_unpublished_draft_is_not_a_user_rejection(tmp_path):
    store=Store(tmp_path/'cancel.sqlite');project=store.create(Project())
    draft=store.preview(command(project,[{'op':'notes','value':{'text':'A late draft'}}],origin='assistant'))
    job=store.create_job(project.id,'prompt',{'prompt':'A cancelled follow-up'})
    store.start_job(job['id']);store.request_job_cancel(job['id']);store.complete_job(job['id'],{'proposal':draft})
    assert store.change(draft.id).state=='rejected'
    assert proposal_history(store,project.id)['items']==[]
