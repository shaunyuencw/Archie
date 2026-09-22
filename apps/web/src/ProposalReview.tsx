import {useEffect,useRef,useState} from 'react';
import {api,type Project,type ChangeSet} from './api';
import PolicyRecommendations,{type PolicySuggestion} from './PolicyRecommendations';
import {proposalSummary} from './proposalSummary';
import {proposalWarnings} from './proposalWarnings';
import './ProposalReview.css';
export default function ProposalReview({project,proposal,open,busy,error,onAccept,onReject,onDismiss}:{project:Project;proposal:ChangeSet;open:boolean;busy:boolean;error?:string;onAccept:(policyIds:string[])=>void;onReject:()=>void;onDismiss:()=>void}){
 const dialog=useRef<HTMLDialogElement>(null),items=proposalSummary(project,proposal),warnings=proposalWarnings(project,proposal);
 const [suggestions,setSuggestions]=useState<PolicySuggestion[]>([]),[selectedPolicies,setSelectedPolicies]=useState<string[]>([]),[suggestionError,setSuggestionError]=useState('');
 useEffect(()=>{let current=true;setSuggestions([]);setSelectedPolicies([]);setSuggestionError('');api<{items:PolicySuggestion[]}>(`/changes/${proposal.id}/policy-suggestions`).then(result=>{if(current)setSuggestions(result.items)}).catch(e=>{if(current)setSuggestionError('Policy suggestions are unavailable: '+e.message)});return()=>{current=false}},[proposal.id]);
 useEffect(()=>{if(open&&!dialog.current?.open)dialog.current?.showModal();else if(!open&&dialog.current?.open)dialog.current.close()},[open]);
 const counts={add:items.filter(i=>i.kind==='add').length,update:items.filter(i=>i.kind==='update').length,remove:items.filter(i=>i.kind==='remove').length};
 return <dialog className="proposal-review" ref={dialog} aria-labelledby="proposal-title" onCancel={e=>{e.preventDefault();onDismiss()}}>
 <div className="review-heading"><div><small>ARCHIE’S PROPOSED DESIGN</small><h2 id="proposal-title">Here’s what will change</h2><p>Review this draft before adding it to <strong>{project.name}</strong>. Your current design stays unchanged until you accept.</p></div><button onClick={onDismiss} disabled={busy}>Review later</button></div>
 <div className="review-totals">{counts.add>0&&<span>{counts.add} additions</span>}{counts.update>0&&<span>{counts.update} updates</span>}{counts.remove>0&&<span className="review-removal">{counts.remove} removals</span>}<span>Based on revision {proposal.base_revision}</span></div>
 <div className="review-body">{error&&<p className="error" role="alert">{error}</p>}{warnings.length>0&&<section className="review-notes"><h3>Things to check</h3>{warnings.map((warning,i)=><div className="review-warning" key={i}><h4>{warning.title}</h4><p>{warning.message}</p>{warning.items.length>0&&<details open={warning.items.length<=6}><summary>{warning.items.length} {warning.items.length===1?'item needs':'items need'} confirmation</summary><ul>{warning.items.map(item=><li key={item}>{item}</li>)}</ul></details>}</div>)}</section>}
 <ol className="review-items">{items.map((item,i)=><li key={i} className={'review-'+item.kind}><h3>{item.title}</h3>{item.details.map((detail,j)=><p key={j}>{detail}</p>)}</li>)}</ol>
 <PolicyRecommendations items={suggestions} selection={selectedPolicies} onSelectionChange={setSelectedPolicies} hideApply busy={busy} contextLabel="Suggested policies for this draft"/>{suggestionError&&<p className="muted">{suggestionError}</p>}
 <p className="review-evidence">Source passages and review states remain available in Sources. Unspecified details stay undecided; accepting a draft does not verify that the system has been built.</p>
 <details className="review-technical"><summary>Technical details · {proposal.operations.length} saved operations</summary><pre>{JSON.stringify({operations:proposal.operations,findings:proposal.findings},null,2)}</pre></details></div>
 <div className="review-actions"><button className="primary" disabled={busy} onClick={()=>onAccept(selectedPolicies)}>Accept changes</button><button disabled={busy} onClick={onReject}>Reject</button><span>{selectedPolicies.length?`Includes ${selectedPolicies.length} selected policies. `:''}Accepted edits can be undone.</span></div>
 </dialog>
}
