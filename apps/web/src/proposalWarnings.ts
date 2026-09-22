import type {Project,ChangeSet} from './api';

export type ReviewWarning={title:string;message:string;items:string[]};
export function proposalWarnings(project:Project,proposal:ChangeSet):ReviewWarning[]{
 const records=new Map<string,Record<string,unknown>>();
 for(const record of [...project.systems,...project.components,...project.zones,...project.interfaces])records.set(record.id,{...record});
 for(const op of proposal.operations)if(op.id&&['systems','components','zones','interfaces'].includes(op.entity||''))records.set(op.id,{...records.get(op.id),...op.value});
 const name=(id:string)=>typeof records.get(id)?.name==='string'?String(records.get(id)!.name):'Unnamed item';
 const label=(id:string)=>{const record=records.get(id);return record?.source&&record?.target?`${name(String(record.source))} → ${name(String(record.target))}`:name(id)};
 const groups=new Map<string,ReviewWarning>();
 const definitions={
  scope:{title:'Confirm what belongs inside the architecture',message:'The draft could not verify whether these items are inside or outside the system boundary. Check the source, then set Architecture boundary in the Inspector. Until confirmed, this stays “Not specified”.'},
  port:{title:'Confirm connection ports',message:'The proposed port value could not be used as a single number. Confirm the port in Connections, or split a connection if it needs several ports. The port stays “Not specified” for now.'},
  enforcement:{title:'Confirm which security controls protect these connections',message:'The firewall or other control is not fully specified. Check the intended security control for each connection and record it in Connections. No extra control has been assumed.'},
 };
 for(const finding of proposal.findings||[]){
  const match=finding.match(/^(.+?): (scope kept unknown because no matching scope claim was supplied\.|port was left unknown because|enforcement is not fully specified\.)/);
  if(match){
   const kind=match[2].startsWith('scope')?'scope':match[2].startsWith('port')?'port':'enforcement';
   const group=groups.get(kind)||{...definitions[kind],items:[]};
   const item=label(match[1]);if(!group.items.includes(item))group.items.push(item);
   groups.set(kind,group);
  }else{
   // Legacy or future findings still remain visible, with known IDs translated.
   let message=finding;
   for(const id of [...records.keys()].sort((a,b)=>b.length-a.length))message=message.split(id).join(label(id));
   const key='other:'+message;if(!groups.has(key))groups.set(key,{title:'Review this detail',message,items:[]});
  }
 }
 return [...groups.values()];
}
