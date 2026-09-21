import {useCallback,useEffect,useRef,useState} from 'react';
import {api,type ChangeSet} from './api';
import './BackgroundJobs.css';
export type BackgroundJob={id:string;project_id:string;project_name:string;kind:string;status:'queued'|'running'|'cancelling'|'cancelled'|'completed'|'failed';request?:{prompt?:string};result?:{proposal?:ChangeSet|null;message?:string;duplicate?:boolean;review?:unknown};error?:{code:string;message:string}|null};
export const jobRunning=(job:BackgroundJob)=>job.status==='queued'||job.status==='running'||job.status==='cancelling';
export function useBackgroundJobs(onComplete:(job:BackgroundJob)=>void){
 const [jobs,setJobs]=useState<BackgroundJob[]>([]),[statusError,setStatusError]=useState('');
 const latest=useRef(onComplete),seen=useRef(new Set<string>());latest.current=onComplete;
 const refresh=useCallback(async()=>{const next=await api<BackgroundJob[]>('/jobs');setJobs(next);setStatusError('');return next},[]);
 useEffect(()=>{let mounted=true,timer:ReturnType<typeof setTimeout>;
  const poll=async()=>{try{const next=await api<BackgroundJob[]>('/jobs');if(mounted){setJobs(next);setStatusError('');}}catch{if(mounted)setStatusError('Background status is temporarily unavailable. Your work may still be running.');}finally{if(mounted)timer=setTimeout(poll,1500)}};
  void poll();return()=>{mounted=false;clearTimeout(timer)};
 },[]);
 useEffect(()=>{for(const job of jobs)if(!jobRunning(job)&&!seen.current.has(job.id)){seen.current.add(job.id);latest.current(job)}},[jobs]);
 const add=useCallback((job:BackgroundJob)=>setJobs(current=>[job,...current.filter(item=>item.id!==job.id)]),[]);
 const cancel=useCallback(async(id:string)=>{const job=await api<BackgroundJob>(`/jobs/${id}/cancel`,{});setJobs(current=>current.map(item=>item.id===id?job:item))},[]);
 const dismiss=useCallback(async(id:string)=>{await api(`/jobs/${id}/dismiss`,{});setJobs(current=>current.filter(item=>item.id!==id))},[]);
 return {jobs,add,refresh,dismiss,cancel,statusError};
}
export function JobNotifications({jobs,error,onOpen,onDismiss,onCancel,onRetry}:{jobs:BackgroundJob[];error:string;onOpen:(job:BackgroundJob)=>void;onDismiss:(id:string)=>void;onCancel:(id:string)=>void;onRetry:()=>void}){
 if(!jobs.length&&!error)return null;
 return <section className="job-notifications" aria-label="Background activity" aria-live="polite">{error&&<div role="status">{error}<button onClick={onRetry}>Check status</button></div>}{jobs.map(job=>{
  const running=jobRunning(job),ready=job.status==='completed'&&job.result?.proposal?.state==='pending';
  return <article key={job.id} className={'job-notice '+job.status} data-job-id={job.id}><span aria-hidden="true" className={running?'job-spinner':'job-result-icon'}>{running?'':job.status==='failed'?'!':job.status==='cancelled'?'—':'✓'}</span><div><strong>{job.project_name}</strong><span>{running?(job.status==='cancelling'?'Stopping this action… Waiting for the current provider request to end; its result will be discarded.':job.status==='queued'?'Queued':'Archie is working…'):job.status==='cancelled'?'Cancelled. Your accepted design is unchanged.':job.status==='failed'?(job.error?.message||'The action could not finish.'):ready?'Your draft is ready to review.':job.kind==='policy_review'?'Your policy review is ready.':job.result?.message||(job.result?.duplicate?'This document already belongs to this project. Open Sources to review it.':'Work finished.')}</span></div><button onClick={()=>onOpen(job)}>{ready?'Review draft':'Open project'}</button>{running?<button aria-label={'Cancel activity for '+job.project_name} disabled={job.status==='cancelling'} onClick={()=>onCancel(job.id)}>{job.status==='cancelling'?'Stopping…':'Cancel'}</button>:<button aria-label={'Dismiss activity for '+job.project_name} onClick={()=>onDismiss(job.id)}>×</button>}</article>;
 })}</section>;
}
