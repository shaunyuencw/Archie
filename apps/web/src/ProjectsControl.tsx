import {useEffect,useState} from 'react';
import {Trash2,RotateCcw,Pencil} from 'lucide-react';
import {api,type Project} from './api';
import './ProjectsControl.css';

type ProjectSummary={id:string;name:string;revision?:number};
type TrashedProject=ProjectSummary&{deleted_at:string};
type Props={
 project:Project|null;
 projects:ProjectSummary[];
 disabled?:boolean;
 workingIds?:string[];
 onOpen:(id:string)=>unknown;
 onRename:(name:string)=>Promise<unknown>;
 onTrashed:(id:string)=>Promise<unknown>|void;
 onRestored:(project:Project)=>Promise<unknown>|void;
};

export default function ProjectsControl({project,projects,disabled=false,workingIds=[],onOpen,onRename,onTrashed,onRestored}:Props){
 const [trash,setTrash]=useState<TrashedProject[]>([]),[working,setWorking]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [renaming,setRenaming]=useState(false),[name,setName]=useState('');
 useEffect(()=>{setRenaming(false);setName(project?.name||'');setNotice('');setError('')},[project?.id]);
 const rename=async()=>{
  if(!project||working)return;
  const nextName=name.trim();
  if(!nextName){setError('Enter a project name.');return;}
  setWorking(true);setError('');setNotice('');
  try{if(nextName!==project.name)await onRename(nextName);setRenaming(false);setNotice(`Renamed project to “${nextName}”.`)}
  catch(e){setError((e as Error).message)}finally{setWorking(false)}
 };
 const loadTrash=async()=>{setTrash(await api<TrashedProject[]>('/projects/trash'))};
 useEffect(()=>{let active=true;api<TrashedProject[]>('/projects/trash').then(items=>{if(active)setTrash(items)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[]);
 // A new accepted project may be ready before the refreshed project list arrives.
 const options=projects.map(item=>item.id===project?.id?{...item,name:project.name}:item);
 if(project&&!options.some(item=>item.id===project.id))options.push(project);
 const remove=async()=>{
  if(!project||working)return;
  const {id,name}=project;setWorking(true);setError('');setNotice('');
  try{await api(`/projects/${id}/trash`,{});await onTrashed(id);await loadTrash();setNotice(`Moved “${name}” to Trash.`)}
  catch(e){setError((e as Error).message)}finally{setWorking(false)}
 };
 const restore=async(item:TrashedProject)=>{
  setWorking(true);setError('');setNotice('');
  try{const restored=await api<Project>(`/projects/${item.id}/restore`,{});await onRestored(restored);await loadTrash();setNotice(`Restored “${item.name}”.`)}
  catch(e){setError((e as Error).message)}finally{setWorking(false)}
 };
 const empty=async()=>{
  if(working)return;
  setWorking(true);setError('');setNotice('');
  try{
   const current=await api<TrashedProject[]>('/projects/trash');setTrash(current);
   if(!current.length)return;
   const names=current.slice(0,5).map(item=>'• '+item.name).join('\n')+(current.length>5?`\n…and ${current.length-5} more.`:'');
   if(!window.confirm(`Permanently remove ${current.length} project${current.length===1?'':'s'} from Trash, including their sources and edit history?\n\n${names}\n\nThis cannot be undone.`))return;
   const result=await api<{deleted_count:number}>('/projects/trash/empty',{confirmed:true,project_ids:current.map(item=>item.id)});
   await loadTrash();setNotice(`Permanently removed ${result.deleted_count} project${result.deleted_count===1?'':'s'} from Trash.`);
  }catch(e){setError((e as Error).message)}finally{setWorking(false)}
 };
 return <div className="projects-control">
  <div className="project-select-row"><select aria-label="Open project" value={project?.id||''} disabled={disabled||working} onChange={event=>{if(event.target.value)onOpen(event.target.value)}}><option value="">Open a saved project…</option>{options.map(item=><option key={item.id} value={item.id}>{item.name}{workingIds.includes(item.id)?' · Working…':''}</option>)}</select><button aria-label="Rename project" title="Rename project" disabled={!project||disabled||working} onClick={()=>{setName(project!.name);setError('');setNotice('');setRenaming(true)}}><Pencil size={15}/></button><button aria-label="Delete project" title="Move selected project to Trash" disabled={!project||disabled||working} onClick={remove}><Trash2 size={15}/></button></div>
  {renaming&&project&&<form className="project-rename" onSubmit={event=>{event.preventDefault();void rename()}}><label htmlFor="project-name">Project name</label><input id="project-name" autoFocus maxLength={160} value={name} disabled={disabled||working} onChange={event=>setName(event.target.value)} onKeyDown={event=>{if(event.key==='Escape'&&!working){event.preventDefault();setRenaming(false);setError('')}}}/><div className="button-row"><button type="submit" disabled={disabled||working||!name.trim()}>{working?'Saving…':'Save name'}</button><button type="button" disabled={working} onClick={()=>{setRenaming(false);setError('')}}>Cancel</button></div></form>}
  {project&&workingIds.includes(project.id)&&<p className="project-working" role="status"><span className="job-spinner" aria-hidden="true"/>Archie is working. You can open another project.</p>}
  {error&&<p role="alert" className="error">{error}</p>}{notice&&<p role="status" className="project-notice">{notice}</p>}
  <details className="project-trash" onToggle={event=>{if(event.currentTarget.open)loadTrash().catch(e=>setError(e.message))}}><summary>Trash ({trash.length})</summary><p>Restore a project to keep its sources and edit history, or empty Trash to permanently remove that project content. Spending records are retained for budget limits.</p><button className="empty-trash" disabled={!trash.length||disabled||working} onClick={empty}>Empty Trash</button>
   {!trash.length?<p className="muted">Trash is empty.</p>:<ul>{trash.map(item=><li key={item.id} data-project-id={item.id}><span><strong>{item.name}</strong><small>Moved {new Date(item.deleted_at).toLocaleString()}</small></span><button aria-label={'Restore '+item.name} title="Restore project" disabled={disabled||working} onClick={()=>restore(item)}><RotateCcw size={13}/>Restore</button></li>)}</ul>}
  </details>
 </div>;
}
