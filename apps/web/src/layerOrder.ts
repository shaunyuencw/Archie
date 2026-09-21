export type LayerAction='front'|'forward'|'backward'|'back';
export type LayerItem={id:string;kind:'node'|'route';z_index:number;role?:string;parentId?:string|null;order:number};
export type LayerUpdate=Pick<LayerItem,'id'|'kind'|'z_index'>;

export function orderedLayers(items:LayerItem[]){
 const byId=new Map(items.map(item=>[item.id,item]));
 const level=(item:LayerItem):number=>{
  const own=item.z_index-(item.role==='zone'?1000:0),parent=item.parentId&&byId.get(item.parentId);
  return parent?Math.max(own,level(parent)+1):own;
 };
 const category=(item:LayerItem)=>item.role==='zone'?0:item.kind==='route'?1:2;
 return [...items].sort((a,b)=>level(a)-level(b)||category(a)-category(b)||a.order-b.order);
}

export function moveLayer(items:LayerItem[],id:string,action:LayerAction):LayerUpdate[]{
 const ordered=orderedLayers(items),target=ordered.find(item=>item.id===id);
 if(!target)return [];
 // A container carries its contents through the stack; children never disappear
 // underneath their own opaque zone. Other objects share one common order.
 const moved=new Set([id]);
 if(target.role==='zone')for(const item of ordered)if(item.parentId&&moved.has(item.parentId))moved.add(item.id);
 const block=ordered.filter(item=>moved.has(item.id)),rest=ordered.filter(item=>!moved.has(item.id));
 const first=ordered.findIndex(item=>moved.has(item.id)),last=ordered.map(item=>moved.has(item.id)).lastIndexOf(true);
 let index=action==='front'?rest.length:action==='back'?0:action==='forward'
  ?rest.findIndex(item=>item.id===ordered[last+1]?.id)+1
  :rest.findIndex(item=>item.id===ordered[first-1]?.id);
 if(action==='forward'&&last===ordered.length-1||action==='backward'&&first===0)return [];
 if(target.parentId)index=Math.max(index,rest.findIndex(item=>item.id===target.parentId)+1);
 rest.splice(Math.max(0,index),0,...block);
 if(rest.every((item,i)=>item.id===ordered[i].id))return [];
 return rest.flatMap((item,index)=>{
  const z_index=index+(item.role==='zone'?1000:0);
  return z_index===item.z_index?[]:[{id:item.id,kind:item.kind,z_index}];
 });
}

export function graphLayers(nodes:any[],edges:any[]):LayerItem[]{
 return [...nodes.map((node,order)=>({id:node.id,kind:'node' as const,z_index:node.z_index??0,role:node.role,parentId:node.parentId,order})),
  ...edges.map((edge,order)=>({id:edge.id,kind:'route' as const,z_index:edge.route?.z_index??-1,order}))];
}
