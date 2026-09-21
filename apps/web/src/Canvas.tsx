import {useEffect,useRef,useState,type PointerEvent,type MouseEvent} from 'react';
import {Handle,Position,NodeResizer,BaseEdge,EdgeLabelRenderer,useReactFlow,type NodeProps,type EdgeProps} from '@xyflow/react';
import type {Point,Route} from '../../../packages/contracts/types';
import {moveRouteSegment,routedPath} from './canvasGeometry';
import './Canvas.css';
const positions={left:Position.Left,right:Position.Right,top:Position.Top,bottom:Position.Bottom};
// Connect at the outside of the component footprint, never through its text.
const handles={left:{left:0,top:27},right:{right:0,top:27},top:{left:'50%',top:0},bottom:{left:'50%',bottom:0}};
export function ArchitectureNode({data,selected}:NodeProps){return <div className={'arch-node '+(data.role==='zone'?'zone-node':'')}>
 <NodeResizer isVisible={selected} minWidth={100} minHeight={80} onResizeEnd={(_,p)=>(data.resize as Function)(p)}/>
 {data.role!=='zone'&&<><div className="equipment-symbol" title={Number(data.quantity)>1?`${data.quantity} declared instances; redundancy ${String(data.redundancy_mode||'unknown').replaceAll('_',' ')}`:undefined}>{Number(data.quantity)>1&&<img className="stack-copy second" src={'/api/assets/'+data.asset_id+'.svg'} alt=""/>}{Number(data.quantity)>2&&<img className="stack-copy third" src={'/api/assets/'+data.asset_id+'.svg'} alt=""/>}<img className="primary-symbol" src={'/api/assets/'+data.asset_id+'.svg'} alt=""/>{Number(data.quantity)>1&&<span className="instance-count">×{Number(data.quantity)}</span>}{data.form_factor==='virtual'&&<span className="virtual-marker">VM</span>}{String(data.asset_id).startsWith('aws-')&&<span className="cloud-marker">AWS</span>}{(data.hosted_controls as {id:string,name:string,asset_id:string}[]||[]).map(control=><img className="hosted-control" key={control.id} src={'/api/assets/'+control.asset_id+'.svg'} alt={'Hosted '+control.name} title={control.name+' runs on this component'}/>)}</div>{Object.entries(positions).map(([id,position])=><Handle key={id} id={id} type="source" position={position} style={handles[id as keyof typeof handles]} title={`${id} connection point`}/>)}</>}
 <strong title={String(data.label)}>{String(data.label)}</strong><small>{data.role==='zone'?'SECURITY ZONE':String(data.role)}</small></div>}

type Drag={index:number,vertices:Point[],points:Point[],start:Point,moved:boolean};
export function ArchitectureEdge(props:EdgeProps){
 const route=props.data?.route as Route|undefined,stored=route?.points||[];
 const updateRoute=props.data?.updateRoute as ((patch:Partial<Route>)=>Promise<unknown>)|undefined;
 const [draft,setDraft]=useState<Point[]|null>(null),[menu,setMenu]=useState<Point|null>(null),drag=useRef<Drag|null>(null);
 const menuRef=useRef<HTMLDivElement>(null),flow=useReactFlow();
 const points=draft??stored,{path,label,vertices}=routedPath(props,route?.style,points);
 useEffect(()=>{setDraft(null);drag.current=null},[route]);
 useEffect(()=>{
  const cancel=()=>{drag.current=null;setDraft(null);setMenu(null)};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')cancel()};
  const dismiss=(event:globalThis.PointerEvent)=>{if(!menuRef.current?.contains(event.target as Node))setMenu(null)};
  window.addEventListener('keydown',escape);window.addEventListener('blur',cancel);window.addEventListener('pointerdown',dismiss);
  return ()=>{window.removeEventListener('keydown',escape);window.removeEventListener('blur',cancel);window.removeEventListener('pointerdown',dismiss)};
 },[]);
 useEffect(()=>{if(menu)menuRef.current?.querySelector<HTMLButtonElement>('button')?.focus()},[menu]);
 const save=(next:Point[])=>{setDraft(next);Promise.resolve(updateRoute?.({points:next,locked:next.length>0})).finally(()=>setDraft(null))};
 const chooseStyle=(style:Route['style'])=>{setMenu(null);setDraft(null);void updateRoute?.({style,points:[],locked:false})};
 const context=(event:MouseEvent)=>{event.preventDefault();event.stopPropagation();setMenu(flow.screenToFlowPosition({x:event.clientX,y:event.clientY},{snapToGrid:false}))};
 const start=(event:PointerEvent<SVGPathElement>,index:number)=>{
  if(event.button!==0)return;
  event.preventDefault();event.stopPropagation();setMenu(null);
  // Capture on the stable group: a zero-length segment may disappear during a drag.
  event.currentTarget.parentElement!.setPointerCapture(event.pointerId);
  drag.current={index,vertices:vertices.map(p=>({...p})),points,start:{x:event.clientX,y:event.clientY},moved:false};
 };
 const move=(event:PointerEvent<SVGGElement>)=>{
  const current=drag.current;if(!current)return;event.stopPropagation();
  if(Math.hypot(event.clientX-current.start.x,event.clientY-current.start.y)<2&&!current.moved)return;
  current.moved=true;
  const coordinate=flow.screenToFlowPosition({x:event.clientX,y:event.clientY},event.altKey?{snapToGrid:false}:undefined);
  current.points=moveRouteSegment(current.vertices,current.index,coordinate).slice(1,-1);
  setDraft(current.points);
 };
 const finish=(event:PointerEvent<SVGGElement>)=>{
  event.stopPropagation();const current=drag.current;drag.current=null;
  if(current?.moved)save(current.points);
  if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);
 };
 return <><g onContextMenu={context}>
  <BaseEdge id={props.id} path={path} markerStart={props.markerStart} markerEnd={props.markerEnd} interactionWidth={22} style={props.selected?{stroke:'#0f766e',strokeWidth:2.5}:{stroke:String(props.data?.color||'#718096'),strokeWidth:1.8}}/>
  <g className="route-segments nodrag nopan" onPointerMove={move} onPointerUp={finish} onPointerCancel={()=>{drag.current=null;setDraft(null)}}>
   {props.selected&&updateRoute&&route?.style!=='straight'&&vertices.slice(0,-1).map((a,index)=>{
    const b=vertices[index+1],horizontal=a.y===b.y;
    return <path key={index} d={`M${a.x} ${a.y}L${b.x} ${b.y}`} className={'route-segment '+(horizontal?'horizontal':'vertical')} tabIndex={0} role="button" aria-label={`Move ${horizontal?'horizontal':'vertical'} line segment ${index+1}`} onPointerDown={event=>start(event,index)} onKeyDown={event=>{
     const direction=horizontal?{ArrowUp:-1,ArrowDown:1}:{ArrowLeft:-1,ArrowRight:1},delta=direction[event.key as keyof typeof direction];
     if(delta){event.preventDefault();event.stopPropagation();const step=delta*(event.altKey?1:16);save(moveRouteSegment(vertices,index,{x:a.x+(horizontal?0:step),y:a.y+(horizontal?step:0)}).slice(1,-1))}
     else if(event.key==='ContextMenu'||(event.shiftKey&&event.key==='F10')){event.preventDefault();event.stopPropagation();setMenu({x:(a.x+b.x)/2,y:(a.y+b.y)/2})}
    }}><title>Drag this line segment {horizontal?'up or down':'left or right'} · right-click for line style · Alt bypasses snap</title></path>;
   })}
  </g>
 </g><EdgeLabelRenderer><span onContextMenu={context} className={'edge-label nodrag nopan'+(props.selected?' edge-label-selected':'')} style={{transform:`translate(-50%,-50%) translate(${label.x}px,${label.y-(props.selected?18:0)}px)`}}>{props.label}</span>
  {menu&&updateRoute&&<div ref={menuRef} role="menu" aria-label="Connector options" className="route-menu nodrag nopan" style={{transform:`translate(${menu.x}px,${menu.y}px)`}} onPointerDown={event=>event.stopPropagation()} onContextMenu={event=>event.preventDefault()} onKeyDown={event=>{
   if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();const buttons=[...event.currentTarget.querySelectorAll<HTMLButtonElement>('button')],index=buttons.indexOf(document.activeElement as HTMLButtonElement);buttons[(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length]?.focus()}
  }}><button role="menuitem" onClick={()=>chooseStyle('straight')}>Straight line</button><button role="menuitem" onClick={()=>chooseStyle('orthogonal')}>Right-angle line</button><button role="menuitem" onClick={()=>{setMenu(null);save([])}}>Reset route</button><small>Drag a right-angle line to move its segment.</small></div>}
 </EdgeLabelRenderer></>;
}
