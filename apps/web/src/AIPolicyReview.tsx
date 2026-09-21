import {useEffect,useRef,useState} from 'react';
import {api,type Project} from './api';
import './AIPolicyReview.css';

type Assessment={policy_id:string;title?:string;status:string;message:string;affected_ids:string[];citations:{source_id:string;locator:string;excerpt:string}[];reference_check:string};
type Review={id:string;revision:number;current_revision:number;stale:boolean;provider:string;model:string;created_at:string;mode:string;summary:string;assessments:Assessment[];warnings:string[];coverage:Record<string,[number,number]>;cost_usd:number;cached:boolean};
type Props={project:Project;provider:string;budgetUsd?:number;modelName?:string;onComplete?:()=>void};
const statuses:Record<string,string>={potential_concern:'Potential concern',needs_human_review:'Human review needed',insufficient_information:'Missing information',no_issue_identified:'No issue identified in supplied facts'};

export default function AIPolicyReview({project,provider,budgetUsd,modelName,onComplete}:Props){
 const [review,setReview]=useState<Review|null>(null),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState('');
 const key=project.id+':'+provider,current=useRef(key);current.current=key;
 useEffect(()=>{let active=true;setLoading(true);setReview(null);setError('');api<{review:Review|null}>(`/projects/${project.id}/policy-review?provider=${encodeURIComponent(provider)}`).then(result=>{if(active)setReview(result.review)}).catch(error=>{if(active)setError(error.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[project.id,project.revision,provider]);
 const run=async()=>{setBusy(true);setError('');const startedKey=key;try{const result=await api<Review>(`/projects/${project.id}/policy-review`,{base_revision:project.revision,provider,request_id:crypto.randomUUID()});if(current.current===startedKey)setReview(result)}catch(error){if(current.current===startedKey)setError((error as Error).message)}finally{setBusy(false);onComplete?.()}};
 const selectedCount=project.policy_ids?.length??20;
 const partial=review&&Object.values(review.coverage).some(([included,total])=>included<total);
 const stale=review&&(review.stale||review.revision!==project.revision);
 const names=Object.fromEntries([...project.components,...project.zones,...project.systems].map(item=>[item.id,item.name]));
 return <section className="ai-policy-review"><div className="ai-policy-heading"><div><h2>Optional AI policy review</h2><p>Ask for advice on this project’s {selectedCount} selected policies. This is separate from the automated fact checks and does not change your architecture.</p></div><button className="primary" disabled={busy||loading||!selectedCount} onClick={run}>{busy?'Reviewing…':provider==='mock'?'Try review format · free demo':`Review with ${provider==='openai'?'OpenAI':'Ollama'}`}</button></div>
 <p className="ai-policy-boundary">{provider==='mock'?'Mock shows a deterministic example of the advisory format; no AI model is called.':provider==='openai'?`One request to ${modelName||'the selected OpenAI model'}, containing selected policies, model facts and source excerpts${budgetUsd!==undefined?` (up to $${budgetUsd.toFixed(2)} per action)`:''}.`:`One request to ${modelName||'your local Ollama model'}, with no cloud fallback.`} Saved results are reused for the same project revision and policy set.</p>
 {!selectedCount&&<p>Select policies in the Policy library before requesting a review.</p>}
 {error&&<p role="alert" className="ai-policy-error">{error}</p>}
 {review&&<div className="ai-policy-result"><div className="ai-policy-meta"><span className="badge">{review.mode==='deterministic_demo'?'Mock demonstration':'AI advisory · verify with a person'}</span><span>Revision {review.revision} · {review.model} · ${review.cost_usd.toFixed(4)}{review.cached?' · saved result':''}</span></div>{stale&&<p className="ai-policy-warning">This review is out of date. It covers revision {review.revision}; your project is now revision {project.revision}. Run a review of the current project before using it.</p>}<p className="ai-policy-summary">{review.summary}</p>
 <p className="ai-policy-coverage">Context supplied: {Object.entries(review.coverage).map(([name,[included,total]])=>`${included}/${total} ${name}`).join(' · ')}.{partial?' This is a partial review. Omitted context remains unknown.':''}</p>
 <p className="ai-policy-boundary">Source checks verify cited IDs, locators and excerpts. They do not verify the AI’s interpretation or establish policy approval.</p>
 {review.warnings.length>0&&<ul className="ai-policy-warning">{review.warnings.map((warning,index)=><li key={index}>{warning}</li>)}</ul>}
 <div className="ai-policy-assessments">{review.assessments.map(assessment=><article key={assessment.policy_id} className={'ai-policy-assessment '+assessment.status}><div><strong>{assessment.title||assessment.policy_id}</strong><span>{statuses[assessment.status]||assessment.status}</span></div><small>{assessment.policy_id}</small><p>{assessment.message}</p>{assessment.affected_ids.length>0&&<small>Affected: {assessment.affected_ids.map(id=>names[id]||id).join(', ')}</small>}{assessment.reference_check==='flagged'&&<p className="ai-policy-warning">Unsupported references were removed. Treat this assessment as unresolved.</p>}{assessment.citations.map((citation,index)=><blockquote key={index}><p>{citation.excerpt}</p><cite>{project.sources.find(source=>source.id===citation.source_id)?.name||citation.source_id} · {citation.locator}</cite></blockquote>)}{!assessment.citations.length&&<small className="ai-policy-no-citation">No source passage cited; check the recorded model and source material.</small>}</article>)}</div></div>}
 </section>
}
