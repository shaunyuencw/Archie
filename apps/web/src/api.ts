import type {Project, ChangeSet, Operation} from '../../../packages/contracts/types';
export type {Project, ChangeSet, Operation};
export async function api<T=any>(path:string,body?:unknown):Promise<T>{
 const r=await fetch('/api'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const result=await r.json(); if(!r.ok)throw new Error(result.message||JSON.stringify(result.detail)||'Request failed'); return result;
}
export function change(p:Project,operations:Operation[]):ChangeSet{return {id:crypto.randomUUID(),request_id:crypto.randomUUID(),project_id:p.id,base_revision:p.revision,base_views:Object.fromEntries(Object.entries(p.views).map(([k,v])=>[k,v.revision])),operations,affected_ids:[],evidence:[],findings:[],state:'pending',origin:'manual'}}
