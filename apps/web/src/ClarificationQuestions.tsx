import {useId,useState} from 'react';
import type {Project} from './api';
import './ClarificationQuestions.css';

type Decision=Project['decisions'][number];
type Props={decisions:Decision[];onAnswer:(decisionId:string,answer:string)=>Promise<unknown>;busy?:boolean;optionLabels?:Record<string,string>};
const readable:Record<string,string>={push:'Push events automatically',pull:'Poll for new events',management:'Administration and management',integration:'System integration',video:'Video transfer',active_passive:'Active and standby instances',active_active:'Multiple active instances',recovery_plan:'A documented recovery plan',single_instance:'A single instance'};
const special=(value:string)=>value.trim().toLowerCase().replace(/[_-]/g,' ');
export function clarificationOptions(options:string[]){return [...new Set(options.filter(value=>value.trim()&&!['other','not decided'].includes(special(value)))),'Other','Not decided']}
export function clarificationLabel(value:string,labels:Record<string,string>={}){if(value==='Other')return 'Other';if(value==='Not decided')return 'Not decided yet';return labels[value]||readable[value]||value.replaceAll('_',' ').replaceAll('-',' ').replace(/^./,first=>first.toUpperCase())}

function Question({decision,onAnswer,busy,optionLabels}:Omit<Props,'decisions'>&{decision:Decision}){
 const group=useId();
 const [choice,setChoice]=useState(''),[other,setOther]=useState(''),[saving,setSaving]=useState(false),[error,setError]=useState('');
 const answer=choice==='Other'?other.trim():choice;
 const disabled=busy||saving;
 const save=async(event:React.FormEvent)=>{event.preventDefault();if(!answer||disabled)return;setSaving(true);setError('');try{await onAnswer(decision.id,answer)}catch(error){setError((error as Error).message)}finally{setSaving(false)}};
 return <form className="question clarification-question" onSubmit={save}><fieldset disabled={disabled}><legend>{decision.question}</legend><div className="clarification-options">{clarificationOptions(decision.options).map(value=><label className={'clarification-option'+(choice===value?' chosen':'')} key={value}><input type="radio" name={group} value={value} checked={choice===value} onChange={()=>setChoice(value)}/><span>{clarificationLabel(value,optionLabels)}{value==='Not decided'&&<small>Keep this detail unresolved.</small>}{value==='Other'&&<small>Write a different answer.</small>}</span></label>)}</div>{choice==='Other'&&<label className="clarification-other">Your answer<textarea aria-label={'Your answer to '+decision.question} rows={3} value={other} onChange={event=>setOther(event.target.value)} placeholder="Describe what should happen…"/></label>}<button className="primary clarification-save" disabled={!answer||disabled}>{saving?'Saving answer…':'Save answer'}</button></fieldset>{error&&<p role="alert" className="clarification-error">{error}</p>}</form>
}

export default function ClarificationQuestions({decisions,...props}:Props){return <>{decisions.filter(decision=>decision.state==='unknown').slice(0,3).map(decision=><Question key={decision.id} decision={decision} {...props}/>)}</>}
