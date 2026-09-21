import {expect,test} from 'vitest';
import {graphLayers,moveLayer,orderedLayers,type LayerItem,type LayerUpdate} from './layerOrder';

const node=(id:string,z_index:number,role='server',parentId:string|null=null,order=0):LayerItem=>
 ({id,kind:'node',z_index,role,parentId,order});
const route=(id:string,z_index:number,order=0):LayerItem=>({id,kind:'route',z_index,order});
const ids=(items:LayerItem[])=>orderedLayers(items).map(item=>item.id);
const apply=(items:LayerItem[],updates:LayerUpdate[])=>items.map(item=>
 ({...item,...updates.find(update=>update.id===item.id&&update.kind===item.kind)}));

test('legacy graph defaults put zones behind connections and assets in stable order',()=>{
 const layers=graphLayers([
  {id:'second',role:'application',z_index:0},
  {id:'zone',role:'zone'},
  {id:'first',role:'server',parentId:'zone'},
 ],[{id:'connection',route:{line_color:'#2563eb'}}]);
 expect(ids(layers)).toEqual(['zone','connection','second','first']);
 expect(layers.find(item=>item.id==='connection')?.z_index).toBe(-1);
});

test('connections can move above equipment and behind containers',()=>{
 const original=[node('zone',0,'zone'),node('asset',0),route('connection',-1)];
 const front=moveLayer(original,'connection','front');
 expect(front).toContainEqual({id:'connection',kind:'route',z_index:2});
 expect(ids(apply(original,front))).toEqual(['zone','asset','connection']);
 expect(ids(apply(original,moveLayer(original,'connection','back'))))
  .toEqual(['connection','zone','asset']);
});

test('forward and backward move components exactly one position in the shared stack',()=>{
 const original=[node('a',0),route('incoming',1),node('b',2),route('outgoing',3),node('c',4)];
 expect(ids(apply(original,moveLayer(original,'b','forward'))))
  .toEqual(['a','incoming','outgoing','b','c']);
 expect(ids(apply(original,moveLayer(original,'b','backward'))))
  .toEqual(['a','b','incoming','outgoing','c']);
 expect(ids(apply(original,moveLayer(original,'incoming','forward'))))
  .toEqual(['a','b','incoming','outgoing','c']);
 expect(ids(apply(original,moveLayer(original,'outgoing','backward'))))
  .toEqual(['a','incoming','outgoing','b','c']);
});

test('a zone carries its own assets as a block past unrelated equipment and lines',()=>{
 const original=[node('zone',1000,'zone'),route('inside-line',1),
  node('child-a',2,'application','zone'),node('unrelated',3),
  node('child-b',4,'database','zone'),route('outside-line',5)];
 const front=apply(original,moveLayer(original,'zone','front'));
 expect(ids(front)).toEqual(['inside-line','unrelated','outside-line','zone','child-a','child-b']);
 expect(front.find(item=>item.id==='zone')?.z_index).toBe(1003);
 const back=apply(front,moveLayer(front,'zone','back'));
 expect(ids(back)).toEqual(['zone','child-a','child-b','inside-line','unrelated','outside-line']);
});

test('sending a child backward stops above its own zone',()=>{
 const original=[route('under-zone',0),node('zone',1001,'zone'),node('unrelated',2),
  route('over-zone',3),node('child',4,'server','zone')];
 const back=apply(original,moveLayer(original,'child','back'));
 expect(ids(back)).toEqual(['under-zone','zone','child','unrelated','over-zone']);
 expect(moveLayer(back,'child','backward')).toEqual([]);
 expect(moveLayer(back,'child','back')).toEqual([]);
});

test('explicit child layers cannot place contents underneath a raised zone',()=>{
 const original=[node('zone',1005,'zone'),node('child',-10000,'server','zone'),
  node('outside',3),route('connection',7)];
 expect(ids(original)).toEqual(['outside','zone','child','connection']);
});

test('missing objects and moves already at the boundary produce no updates',()=>{
 const original=[route('back',-1),node('front',0)];
 expect(moveLayer(original,'missing','front')).toEqual([]);
 expect(moveLayer([],'missing','back')).toEqual([]);
 for(const action of ['back','backward'] as const)expect(moveLayer(original,'back',action)).toEqual([]);
 for(const action of ['front','forward'] as const)expect(moveLayer(original,'front',action)).toEqual([]);
});

test('sorting and every layer action preserve the original input',()=>{
 const original=[node('zone',0,'zone'),node('child',0,'server','zone'),route('connection',-1)];
 const saved=structuredClone(original);
 for(const item of original)Object.freeze(item);
 Object.freeze(original);
 orderedLayers(original);
 for(const action of ['front','forward','backward','back'] as const){
  moveLayer(original,'zone',action);
  moveLayer(original,'child',action);
  moveLayer(original,'connection',action);
 }
 expect(original).toEqual(saved);
});
