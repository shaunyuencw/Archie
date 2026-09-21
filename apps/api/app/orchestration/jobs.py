"""Persistent, bounded background work for proposal-producing actions."""
import threading
from concurrent.futures import ThreadPoolExecutor

from ..domain.commands import DomainError, apply
from ..orchestration.documents import ingest_live
from ..orchestration.live import assisted_run
from ..orchestration.policy_review import review_project
from ..orchestration.service import ingest


# The provider layer serialises local models separately.  This small executor
# keeps browser requests responsive without introducing an agent framework.
EXECUTOR=ThreadPoolExecutor(max_workers=2,thread_name_prefix='archie-job')
_CANCELLATIONS={}
_CANCELLATIONS_LOCK=threading.Lock()


def _error(error):
    if isinstance(error,DomainError):
        return {'code':error.code,'message':error.message}
    return {'code':'provider_output','message':'Background processing failed before a proposal could be prepared. Your accepted architecture was preserved.'}


def _validate_snapshot(project,base_revision,base_views):
    expected={key:view.revision for key,view in project.views.items()}
    if project.revision!=base_revision or expected!=base_views:
        raise DomainError('stale_revision','The project changed before this background action started. Create a fresh proposal.',409)


def _cancelled(store,job_id,cancel):
    return cancel.is_set() or store.job_cancellation_requested(job_id)


def _worker(store,job_id,action,cancel):
    try:
        if not store.start_job(job_id):
            return
        if _cancelled(store,job_id,cancel):
            store.finish_job_cancelled(job_id)
            return
        result=action(cancel)
        if _cancelled(store,job_id,cancel):
            store.finish_job_cancelled(job_id,result)
            return
        store.complete_job(job_id,result)
        # If cancellation won the transaction race, complete_job has changed the
        # job to cancelled and rejected any just-created pending proposal.
        if _cancelled(store,job_id,cancel):
            store.finish_job_cancelled(job_id,result)
    except Exception as error:
        # Terminal writes are conditional, so an old process cannot overwrite a
        # startup-recovered interruption or revive a project that has been purged.
        if _cancelled(store,job_id,cancel):
            store.finish_job_cancelled(job_id)
        else:
            store.fail_job(job_id,_error(error))
    finally:
        with _CANCELLATIONS_LOCK:
            _CANCELLATIONS.pop(job_id,None)


def _submit(store,job,action):
    # Register before scheduling, so a request that reaches the API immediately
    # after its response can still cancel a queued worker without a provider call.
    cancel=threading.Event()
    with _CANCELLATIONS_LOCK:
        _CANCELLATIONS[job['id']]=cancel
    try:
        EXECUTOR.submit(_worker,store,job['id'],action,cancel)
    except RuntimeError as error:
        with _CANCELLATIONS_LOCK:
            _CANCELLATIONS.pop(job['id'],None)
        store.fail_job(job['id'],{'code':'job_unavailable','message':'ARCHIE could not start this background action. Retry it explicitly.'})
        raise DomainError('job_unavailable','ARCHIE could not start this background action. Retry it explicitly.',503) from error
    return job


def cancel_job(store,job_id):
    """Request cancellation without claiming an already-sent provider call stopped."""
    job=store.request_job_cancel(job_id)
    with _CANCELLATIONS_LOCK:
        cancel=_CANCELLATIONS.get(job_id)
    if cancel:
        cancel.set()
    return job


def schedule_prompt(store,pid,request):
    if request.project_id!=pid:
        raise DomainError('invalid_input','Project mismatch')
    metadata={'provider':request.provider,'base_revision':request.base_revision,'base_views':request.base_views,'prompt':request.prompt}
    job=store.create_job(pid,'prompt',metadata)

    def action(cancel):
        project=store.get(pid)
        apply(project,request)  # validates the captured semantic and view snapshot before any provider call
        if request.provider!='mock':
            return assisted_run(store,pid,request,cancel=cancel,job_id=job['id'])
        result=ingest(store,pid,request.prompt.encode(),'Prompt','prompt',cancel=cancel,job_id=job['id'])
        if result.get('message'):
            raise DomainError('insufficient_context',result['message'])
        return result

    return _submit(store,job,action)


def schedule_source(store,pid,data,name,provider,base_revision,base_views):
    metadata={'provider':provider,'base_revision':base_revision,'base_views':base_views,
              'file':{'name':name,'bytes':len(data)}}
    job=store.create_job(pid,'source',metadata)

    def action(cancel):
        project=store.get(pid)
        _validate_snapshot(project,base_revision,base_views)
        if provider!='mock':
            return ingest_live(store,pid,data,name,provider,cancel=cancel,job_id=job['id'])
        return ingest(store,pid,data,name,cancel=cancel,job_id=job['id'])

    return _submit(store,job,action)


def schedule_continue(store,pid,sid,request):
    if request.project_id!=pid:
        raise DomainError('invalid_input','Project mismatch')
    metadata={'provider':request.provider,'base_revision':request.base_revision,'base_views':request.base_views,'source_id':sid}
    job=store.create_job(pid,'continue',metadata)

    def action(cancel):
        project=store.get(pid)
        apply(project,request)  # validation only; the action remains a preview until acceptance
        if request.provider!='mock':
            return ingest_live(store,pid,b'','',request.provider,source_id=sid,cancel=cancel,job_id=job['id'])
        return ingest(store,pid,b'','',source_id=sid,cancel=cancel,job_id=job['id'])

    return _submit(store,job,action)


def schedule_policy_review(store,pid,request):
    metadata={'provider':request.provider,'base_revision':request.base_revision,'request_id':request.request_id}
    job=store.create_job(pid,'policy_review',metadata)

    def action(cancel):
        project=store.get(pid)
        if project.revision!=request.base_revision:
            raise DomainError('stale_revision','The project changed before this background review started. Reopen Findings and try again.',409)
        return {'review':review_project(store,pid,request,cancel=cancel,job_id=job['id'])}

    return _submit(store,job,action)


def recover_interrupted_jobs(store):
    """Mark work from a previous server process failed; never replay it."""
    return store.recover_jobs()


def shutdown_jobs():
    EXECUTOR.shutdown(wait=False,cancel_futures=True)
