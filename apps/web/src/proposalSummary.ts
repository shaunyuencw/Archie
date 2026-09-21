import type {Project,ChangeSet} from './api';
export type ReviewItem={title:string;details:string[];kind:'add'|'update'|'remove'};
export function proposalSummary(project:Project,proposal:ChangeSet):ReviewItem[]{
 const operations=proposal.operations;
 const groups=['components','systems','zones','interfaces','deployments','constraints','decisions'] as const;
 const records=Object.fromEntries(groups.flatMap(group=>project[group].map(item=>[item.id,item])));
 const names:Record<string,string>=Object.fromEntries([...project.components,...project.zones,...project.systems].map(c=>[c.id,c.name]));
 for(const o of operations)if(o.id&&o.value?.name)names[o.id]=String(o.value.name);
 const name=(id:unknown)=>id==null?'Not specified':names[String(id)]||String(id);
 const readable=(value:unknown):string=>value==null||value===''?'Not specified':Array.isArray(value)?value.map(name).join(', ')||'None':typeof value==='boolean'?value?'Yes':'No':typeof value==='object'?Object.entries(value).map(([k,v])=>`${k.replaceAll('_',' ')}: ${readable(v)}`).join('; '):name(value).replaceAll('_',' ');
 const deploymentDetails=(v:Record<string,unknown>)=>[
  ...('zone_id' in v?[`Zone: ${name(v.zone_id)}.`]:[]),
  ...('quantity' in v?[v.quantity==null?'Instance count is not specified.':`${v.quantity} declared instance${v.quantity===1?'':'s'}.`]:[]),
  ...('redundancy_mode' in v?[`Redundancy: ${v.redundancy_mode==='unknown'?'not decided':v.redundancy_mode==='active_passive'?'active / standby':'active / active'}.`]:[]),
  ...(v.host_component_id?[`Hosted on ${name(v.host_component_id)}.`]:[]),
 ];
 const items:ReviewItem[]=[];
 for(const o of operations){
  const id=o.id||'',v=o.value||{},old=records[id] as unknown as Record<string,unknown>|undefined;
  const kind=o.op==='remove'?'remove':o.op==='add'?'add':'update';
  if(o.entity==='claims'||o.entity==='sources')continue;
  if(o.entity==='deployments'&&o.op==='add'&&operations.some(c=>c.entity==='components'&&c.op==='add'&&c.id===v.component_id))continue;
  let title='',details:string[]=[];
  if(o.op==='remove'){
   title=`Remove ${names[id]||readable(old?.purpose)||'this connection'}`;
   details=o.entity==='components'?['Connections that reference this component will also be removed. You can undo the accepted change.']:['You can undo the accepted change.'];
  }else if(o.entity==='components'&&o.op==='add'){
   title=`Add ${name(o.id)}`;
   if(v.role)details.push(`Purpose: ${readable(v.role)}.`);
   const d=operations.find(d=>d.entity==='deployments'&&d.op==='add'&&d.value?.component_id===o.id);
   if(d)details.push(...deploymentDetails(d.value||{}));
   if(v.form_factor&&v.form_factor!=='unknown')details.push(`Type: ${readable(v.form_factor)}.`);
  }else if(o.entity==='interfaces'&&o.op==='add'){
   title=`Connect ${name(v.source)} → ${name(v.target)}`;
   details.push(`${v.purpose?readable(v.purpose):'Purpose not specified'}. ${v.protocol?readable(v.protocol):'Protocol not specified'}${v.port!=null?`, port ${v.port}`:''}.`);
   details.push(v.initiator?`${name(v.initiator)} starts the session.`:'Who starts the session is not decided.');
   if(Array.isArray(v.enforcement)&&v.enforcement.length)details.push(`Enforcement: ${v.enforcement.map(name).join(', ')}.`);
  }else if(o.entity==='deployments'){
   title=`Update deployment of ${name(v.component_id||old?.component_id)}`;details=deploymentDetails(v);
  }else if(o.entity==='decisions'){
   title='Clarify a design decision';details=[String(v.question||old?.question||'Review the pending question'),...(v.answer?[`Answer: ${readable(v.answer)}.`]:[])];
  }else if(o.entity==='constraints'){
   title=`${o.op==='add'?'Record':'Update'} requirement: ${readable(v.key||old?.key)}`;
   details=[readable(v.value)];
  }else if(o.op==='placement'||o.op==='route'){
   title=`${o.op==='placement'?'Adjust the position or size of':'Adjust the line for'} ${name(o.id)}`;
   details=['This changes the diagram presentation only.'];
  }else if(o.op==='notes'){
   title='Update design notes';details=[String(v.text||'Clear the existing notes.')];
  }else if(o.op==='project_name'){
   title=`Name this project “${String(v.name)}”`;details=[`Current name: ${project.name}.`];
  }else if(o.op==='policy_selection'){
   title='Change this project’s policy selection';details=[`${Array.isArray(v.policy_ids)?v.policy_ids.length:0} policies will apply.`];
  }else if(o.op==='add'){
   title=`Add ${o.entity==='zones'?'zone':'system'}: ${name(o.id)}`;
  }else{
   title=v.name&&old?.name?`Rename ${old.name} to ${v.name}`:`Update ${names[id]||name(old?.source)+' → '+name(old?.target)}`;
   const labels:Record<string,string>={source:'From',target:'To',initiator:'Session starts at',data_direction:'Data direction',enforcement:'Enforcement',asset_id:'Symbol',form_factor:'Type',scope:'Scope',storage_destination:'Storage destination',audit_destination:'Audit destination'};
   for(const [key,value] of Object.entries(v))if(!['name','evidence','component_id'].includes(key)&&JSON.stringify(old?.[key])!==JSON.stringify(value))details.push(`${labels[key]||key.replaceAll('_',' ')}: ${readable(old?.[key])} → ${readable(value)}.`);
  }
  items.push({title,details,kind});
 }
 return items;
}
