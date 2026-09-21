import type {Project,Operation} from './api';

export type Clipboard = {project:Project; ids:string[]; view:string};
export const isEditable = (target:EventTarget|null) => target instanceof Element && !!target.closest('input,textarea,select,[contenteditable="true"],[role="textbox"]');

export function deleteOperations(project:Project,ids:string[]):Operation[]{
 const selected=new Set(ids);
 const components=new Set(project.components.filter(c=>selected.has(c.id)).map(c=>c.id));
 return [
  ...project.interfaces.filter(e=>selected.has(e.id)&&![e.source,e.target,...e.enforcement].some(id=>components.has(id))).map(e=>({op:'remove',entity:'interfaces',id:e.id,confirmed:true} as Operation)),
  ...project.components.filter(c=>components.has(c.id)).map(c=>({op:'remove',entity:'components',id:c.id,confirmed:true} as Operation)),
  ...project.zones.filter(z=>selected.has(z.id)).map(z=>({op:'remove',entity:'zones',id:z.id,confirmed:true} as Operation)),
 ];
}

export function pasteOperations(clipboard:Clipboard,current:Project,view:string,offset=32):{operations:Operation[];ids:string[]}{
 const p=clipboard.project;
 if(p.id!==current.id)throw new Error('Copy and paste stays within the current project to preserve references.');
 if(view==='sv1'||clipboard.view==='sv1')throw new Error('Use Logical or SV-2 to duplicate individual components.');
 const selected=new Set(clipboard.ids);
 const zones=p.zones.filter(z=>selected.has(z.id));
 const zoneIds=new Set(zones.map(z=>z.id));
 const components=p.components.filter(c=>selected.has(c.id)||p.deployments.some(d=>d.component_id===c.id&&zoneIds.has(d.zone_id||'')));
 const componentIds=new Set(components.map(c=>c.id));
 const interfaces=p.interfaces.filter(e=>selected.has(e.id)||(componentIds.has(e.source)&&componentIds.has(e.target)));
 const records=[...zones,...components,...interfaces];
 const ids=new Map(records.map(c=>[c.id,'tmp:'+crypto.randomUUID()]));
 const remap=(id:string|null)=>id===null?null:ids.get(id)||id;
 const operations:Operation[]=[];
 for(const zone of zones)operations.push({op:'add',entity:'zones',id:ids.get(zone.id)!,value:{name:zone.name+' copy'}});
 for(const c of components){
  const {id,...value}=c;
  operations.push({op:'add',entity:'components',id:ids.get(id)!,value:{...value,name:c.name+' copy',status:'proposed',evidence:[],audit_destination:remap(c.audit_destination),storage_destination:remap(c.storage_destination)}});
  const d=p.deployments.find(d=>d.component_id===c.id);
  operations.push({op:'add',entity:'deployments',id:'tmp:'+crypto.randomUUID(),value:{component_id:ids.get(id),zone_id:remap(d?.zone_id||null),quantity:null}});
 }
 for(const e of interfaces){const {id,...value}=e;operations.push({op:'add',entity:'interfaces',id:ids.get(id)!,value:{...value,source:remap(e.source),target:remap(e.target),initiator:remap(e.initiator),enforcement:e.enforcement.map(remap),evidence:[]}});}
 for(const object of [...zones,...components]){
  const place=p.views[clipboard.view].placements[object.id];if(!place)continue;
  const parent=p.deployments.find(d=>d.component_id===object.id)?.zone_id;
  const delta=parent&&zoneIds.has(parent)?0:offset;
  operations.push({op:'placement',view:view as Operation['view'],id:ids.get(object.id)!,value:{...place,x:place.x+delta,y:place.y+delta,locked:true}});
 }
 for(const e of interfaces){const route=p.views[clipboard.view].routes[e.id];if(route)operations.push({op:'route',view:view as Operation['view'],id:ids.get(e.id)!,value:{...route,points:route.points.map(point=>({x:point.x+offset,y:point.y+offset}))}});}
 return {operations,ids:[...ids.values()]};
}
