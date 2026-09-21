import {useEffect,useRef,useState,type PointerEvent} from 'react';
import {Handle,Position,NodeResizer,BaseEdge,EdgeLabelRenderer,useReactFlow,type NodeProps,type EdgeProps} from '@xyflow/react';
import type {Point,Route} from '../../../packages/contracts/types';
import {routedPath} from './canvasGeometry';
import './Canvas.css';
const positions={left:Position.Left,right:Position.Right,top:Position.Top,bottom:Position.Bottom};
// Connect at the outside of the component footprint, never through its text.
const handles={left:{left:0,top:27},right:{right:0,top:27},top:{left:'50%',top:0},bottom:{left:'50%',bottom:0}};
export function ArchitectureNode({data,selected}:NodeProps){return <div className={'arch-node '+(data.role==='zone'?'zone-node':'')}>
 <NodeResizer isVisible={selected} minWidth={100} minHeight={80} onResizeEnd={(_,p)=>(data.resize as Function)(p)}/>
 {data.role!=='zone'&&<><img src={'/api/assets/'+data.asset_id+'.svg'} alt=""/>{Object.entries(positions).map(([id,position])=><Handle key={id} id={id} type="source" position={position} style={handles[id as keyof typeof handles]} title={`${id} connection point`}/>)}</>}
 <strong title={String(data.label)}>{String(data.label)}</strong><small>{data.role==='zone'?'SECURITY ZONE':String(data.role)}</small></div>}

type Drag={index:number,points:Point[],start:Point,moved:boolean};
export function ArchitectureEdge(props:EdgeProps){
 const route=props.data?.route as Route|undefined,stored=route?.points||[];
 const updateRoute=props.data?.updateRoute as ((points:Point[])=>Promise<unknown>)|undefined;
 const [draft,setDraft]=useState<Point[]|null>(null),drag=useRef<Drag|null>(null);
 const flow=useReactFlow();
 const points=draft??stored,{path,label}=routedPath(props,route?.style,points);
 useEffect(()=>{setDraft(null);drag.current=null},[route]);
 useEffect(()=>{
  const cancel=()=>{drag.current=null;setDraft(null)};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')cancel()};
  window.addEventListener('keydown',escape);window.addEventListener('blur',cancel);
  return ()=>{window.removeEventListener('keydown',escape);window.removeEventListener('blur',cancel)};
 },[]);
 const save=(next:Point[])=>{setDraft(next);Promise.resolve(updateRoute?.(next)).finally(()=>setDraft(null))};
 const start=(event:PointerEvent<HTMLButtonElement>,index:number)=>{
  if(event.button!==0)return;
  event.stopPropagation();event.currentTarget.setPointerCapture(event.pointerId);
  drag.current={index,points:points.length?points.map(p=>({...p})):[label],start:{x:event.clientX,y:event.clientY},moved:false};
 };
 const move=(event:PointerEvent<HTMLButtonElement>)=>{
  const current=drag.current;if(!current)return;event.stopPropagation();
  if(Math.hypot(event.clientX-current.start.x,event.clientY-current.start.y)<2&&!current.moved)return;
  current.moved=true;
  current.points[current.index]=flow.screenToFlowPosition({x:event.clientX,y:event.clientY},event.altKey?{snapToGrid:false}:undefined);
  setDraft([...current.points]);
 };
 const finish=(event:PointerEvent<HTMLButtonElement>)=>{
  event.stopPropagation();const current=drag.current;drag.current=null;
  if(current?.moved)save(current.points);
  event.currentTarget.releasePointerCapture(event.pointerId);
 };
 const controls=points.length?points:[label];
 return <><BaseEdge id={props.id} path={path} markerStart={props.markerStart} markerEnd={props.markerEnd} interactionWidth={22} style={props.selected?{stroke:'#0f766e',strokeWidth:2.5}:{stroke:String(props.data?.color||'#718096'),strokeWidth:1.8}}/>
  <EdgeLabelRenderer><span className={'edge-label nodrag nopan'+(props.selected?' edge-label-selected':'')} style={{transform:`translate(-50%,-50%) translate(${label.x}px,${label.y-(props.selected?18:0)}px)`}}>{props.label}</span>
   {props.selected&&updateRoute&&controls.map((point,index)=><button key={index} className={'route-waypoint nodrag nopan'+(!points.length?' route-waypoint-new':'')} aria-label={points.length?`Route waypoint ${index+1}`:'Drag to add route waypoint'} title="Drag to route · Option/Alt bypasses grid · double-click removes waypoint" style={{transform:`translate(-50%,-50%) translate(${point.x}px,${point.y}px)`}} onPointerDown={e=>start(e,index)} onPointerMove={move} onPointerUp={finish} onPointerCancel={()=>{drag.current=null;setDraft(null)}} onDoubleClick={e=>{e.stopPropagation();if(points.length)save(points.filter((_,i)=>i!==index))}} onKeyDown={e=>{
    if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();e.stopPropagation();if(points.length)save(points.filter((_,i)=>i!==index))}
   }}/>)}</EdgeLabelRenderer></>;
}
