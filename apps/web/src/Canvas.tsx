import {useEffect,useRef,useState,type CSSProperties,type PointerEvent,type MouseEvent} from 'react';
import {createPortal} from 'react-dom';
import {Handle,Position,NodeResizer,BaseEdge,EdgeLabelRenderer,useReactFlow,type NodeProps,type EdgeProps} from '@xyflow/react';
import type {Point,Route} from '../../../packages/contracts/types';
import {moveLabelOffset,moveRouteSegment,routedPath} from './canvasGeometry';
import type {LayerAction} from './layerOrder';
import './Canvas.css';
const positions={left:Position.Left,right:Position.Right,top:Position.Top,bottom:Position.Bottom};
// Connect at the outside of the component footprint, never through its text.
const handles={left:{left:0,top:27},right:{right:0,top:27},top:{left:'50%',top:0},bottom:{left:'50%',bottom:0}};
function LayerActions({onChange}:{onChange:(action:LayerAction)=>void}){
 return <>{([['front','Bring to front'],['forward','Bring forward'],['backward','Send backward'],['back','Send to back']] as const).map(([action,label])=><button role="menuitem" key={action} onClick={()=>onChange(action)}>{label}</button>)}</>;
}
function fillTone(value:unknown){
 if(typeof value!=='string')return undefined;
 let hex=value.slice(1);if(hex.length<=4)hex=[...hex].map(c=>c+c).join('');
 if(hex.length===8&&parseInt(hex.slice(6),16)<128)return undefined;
 const rgb=[0,2,4].map(index=>parseInt(hex.slice(index,index+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
 return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722>.4?'light':'dark';
}
export function ArchitectureNode({data,selected}:NodeProps){
 const color=(value:unknown)=>typeof value==='string'?value:undefined;
 const nodeStyle:CSSProperties={backgroundColor:color(data.fill_color),borderColor:color(data.border_color)};
 const textStyle:CSSProperties={color:color(data.text_color)};
 const [menu,setMenu]=useState<Point|null>(null),menuRef=useRef<HTMLDivElement>(null);
 const updatePlacement=data.updatePlacement as ((patch:Record<string,unknown>)=>Promise<unknown>)|undefined;
 const updateLayer=data.changeLayer as ((action:LayerAction)=>Promise<unknown>)|undefined;
 const iconUrl='/api/assets/'+encodeURIComponent(String(data.asset_id))+'.svg';
 const iconColor=color(data.icon_color),tintedIcon=!!iconColor;
 const iconStyle:CSSProperties=tintedIcon?{backgroundColor:iconColor,WebkitMask:`url("${iconUrl}") center / contain no-repeat`,mask:`url("${iconUrl}") center / contain no-repeat`}:{};
 const symbol=(className:string,alt:string)=>(tintedIcon?<span className={className+' icon-tint'} style={iconStyle} role={alt?'img':undefined} aria-label={alt||undefined}/>:<img className={className} src={iconUrl} alt={alt}/>);
 useEffect(()=>{
  if(!menu)return;
  const dismiss=(event:globalThis.PointerEvent)=>{if(!menuRef.current?.contains(event.target as Node))setMenu(null)};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')setMenu(null)};
  window.addEventListener('pointerdown',dismiss);window.addEventListener('keydown',escape);
  return()=>{window.removeEventListener('pointerdown',dismiss);window.removeEventListener('keydown',escape)};
 },[menu]);
 const changeLayer=(action:LayerAction)=>{setMenu(null);void updateLayer?.(action)};
 const context=(event:MouseEvent<HTMLDivElement>)=>{event.preventDefault();event.stopPropagation();setMenu({x:Math.max(8,Math.min(event.clientX,window.innerWidth-166)),y:Math.max(8,Math.min(event.clientY,window.innerHeight-150))})};
 return <><div onContextMenu={context} data-fill-tone={fillTone(data.fill_color)} className={'arch-node '+(data.role==='zone'?'zone-node':'')} style={nodeStyle}>
 <NodeResizer isVisible={selected} minWidth={100} minHeight={80} keepAspectRatio={false} color="#138276" handleStyle={{width:11,height:11,border:'2px solid #fff',borderRadius:3,boxShadow:'0 0 0 1px #138276'}} lineStyle={{borderColor:'#138276'}} onResizeEnd={(_,p)=>(data.resize as Function)(p)}/>
 {data.role!=='zone'&&<><div className="equipment-symbol" title={Number(data.quantity)>1?`${data.quantity} declared instances; redundancy ${String(data.redundancy_mode||'unknown').replaceAll('_',' ')}`:undefined}>{Number(data.quantity)>1&&symbol('stack-copy second','')}{Number(data.quantity)>2&&symbol('stack-copy third','')}{symbol('primary-symbol',String(data.label))}{Number(data.quantity)>1&&<span className="instance-count">×{Number(data.quantity)}</span>}{data.form_factor==='virtual'&&<span className="virtual-marker">VM</span>}{String(data.asset_id).startsWith('aws-')&&<span className="cloud-marker">AWS</span>}{(data.hosted_controls as {id:string,name:string,asset_id:string}[]||[]).map(control=><img className="hosted-control" key={control.id} src={'/api/assets/'+control.asset_id+'.svg'} alt={'Hosted '+control.name} title={control.name+' runs on this component'}/>)}</div>{Object.entries(positions).map(([id,position])=><Handle key={id} id={id} type="source" position={position} style={handles[id as keyof typeof handles]} title={`${id} connection point`}/>)}</>}
 <strong style={textStyle} title={String(data.label)}>{String(data.label)}</strong><small style={textStyle}>{data.role==='zone'?'SECURITY ZONE':String(data.role)}</small></div>{menu&&updatePlacement&&updateLayer&&createPortal(<div ref={menuRef} role="menu" aria-label="Layer order options" className="node-menu nodrag nopan" style={{left:menu.x,top:menu.y}} onPointerDown={event=>event.stopPropagation()} onContextMenu={event=>event.preventDefault()}><LayerActions onChange={changeLayer}/></div>,document.body)}</>}

type Drag={index:number,vertices:Point[],points:Point[],start:Point,moved:boolean};
type LabelDrag={start:Point,offset:Point,next:Point,moved:boolean};
type Reconnection={source:string;target:string;sourceHandle:string;targetHandle:string};
export function ArchitectureEdge(props:EdgeProps){
 const route=props.data?.route as Route|undefined,stored=route?.points||[];
 const updateLayer=props.data?.changeLayer as ((action:LayerAction)=>Promise<unknown>)|undefined;
 const changeLayer=(action:LayerAction)=>{setMenu(null);void updateLayer?.(action)};
 const menuPosition=(point:Point)=>({x:Math.max(8,Math.min(point.x,window.innerWidth-218)),y:Math.max(8,Math.min(point.y,window.innerHeight-330))});
 const updateRoute=props.data?.updateRoute as ((patch:Partial<Route>)=>Promise<unknown>)|undefined;
 const [draft,setDraft]=useState<Point[]|null>(null),[draftLabelOffset,setDraftLabelOffset]=useState<Point|null>(null),[menu,setMenu]=useState<Point|null>(null),drag=useRef<Drag|null>(null),labelDrag=useRef<LabelDrag|null>(null);
 const menuRef=useRef<HTMLDivElement>(null),flow=useReactFlow();
 const reconnect=props.data?.reconnect as ((connection:Reconnection)=>Promise<unknown>)|undefined;
 const [reconnecting,setReconnecting]=useState<{end:'source'|'target';point:Point}|null>(null);
 const reconnectActive=useRef(false);
 const points=draft??stored,{path,label,vertices}=routedPath(props,route?.style,points);
 const labelOffset=draftLabelOffset??route?.label_offset??{x:0,y:0};
 const displayedLabel={x:label.x+labelOffset.x,y:label.y+labelOffset.y};
 useEffect(()=>{setDraft(null);setDraftLabelOffset(null);drag.current=null;labelDrag.current=null},[route]);
 useEffect(()=>{
  const cancel=()=>{drag.current=null;labelDrag.current=null;reconnectActive.current=false;setDraft(null);setDraftLabelOffset(null);setReconnecting(null);setMenu(null)};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')cancel()};
  const dismiss=(event:globalThis.PointerEvent)=>{if(!menuRef.current?.contains(event.target as Node))setMenu(null)};
  window.addEventListener('keydown',escape);window.addEventListener('blur',cancel);window.addEventListener('pointerdown',dismiss);
  return ()=>{window.removeEventListener('keydown',escape);window.removeEventListener('blur',cancel);window.removeEventListener('pointerdown',dismiss)};
 },[]);
 useEffect(()=>{if(menu)menuRef.current?.querySelector<HTMLButtonElement>('button')?.focus()},[menu]);
 const save=(next:Point[])=>{setDraft(next);Promise.resolve(updateRoute?.({points:next,locked:next.length>0,automatic:false})).finally(()=>setDraft(null))};
 const resetRoute=()=>{setMenu(null);setDraft(null);void updateRoute?.({style:'orthogonal',points:[],locked:false,automatic:true})};
 const chooseStyle=(style:Route['style'])=>{setMenu(null);setDraft(null);void updateRoute?.({style,points:[],locked:false,automatic:style==='orthogonal'})};
 const saveLabel=(next:Point)=>{setDraftLabelOffset(next);Promise.resolve(updateRoute?.({label_offset:next})).finally(()=>setDraftLabelOffset(null))};
 const resetLabel=()=>{setMenu(null);setDraftLabelOffset(null);void updateRoute?.({label_offset:null})};
 const context=(event:MouseEvent)=>{event.preventDefault();event.stopPropagation();setMenu(menuPosition({x:event.clientX,y:event.clientY}))};
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
 const startLabel=(event:PointerEvent<HTMLSpanElement>)=>{
  if(event.button!==0)return;
  event.preventDefault();event.stopPropagation();setMenu(null);event.currentTarget.setPointerCapture(event.pointerId);
  const start=flow.screenToFlowPosition({x:event.clientX,y:event.clientY},{snapToGrid:false});
  labelDrag.current={start,offset:{...labelOffset},next:{...labelOffset},moved:false};
 };
 const moveLabel=(event:PointerEvent<HTMLSpanElement>)=>{
  const current=labelDrag.current;if(!current)return;event.stopPropagation();
  const coordinate=flow.screenToFlowPosition({x:event.clientX,y:event.clientY},event.altKey?{snapToGrid:false}:undefined);
  const next=moveLabelOffset(current.offset,current.start,coordinate);
  if(Math.hypot(next.x-current.offset.x,next.y-current.offset.y)<1&&!current.moved)return;
  current.moved=true;current.next=next;setDraftLabelOffset(next);
 };
 const finishLabel=(event:PointerEvent<HTMLSpanElement>)=>{
  event.stopPropagation();const current=labelDrag.current;labelDrag.current=null;
  if(current?.moved)saveLabel(current.next);
  if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);
 };
 const labelKey=(event:React.KeyboardEvent<HTMLSpanElement>)=>{
  const direction={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0]} as Record<string,number[]>;
  if(direction[event.key]){event.preventDefault();event.stopPropagation();const [x,y]=direction[event.key],step=event.altKey?1:16;saveLabel({x:labelOffset.x+x*step,y:labelOffset.y+y*step})}
  else if(event.key==='ContextMenu'||(event.shiftKey&&event.key==='F10')){event.preventDefault();event.stopPropagation();setMenu(menuPosition(flow.flowToScreenPosition(displayedLabel)))}
 };
 const lineColor=route?.line_color||String(props.data?.color||'#718096');
 const reconnectControl=(end:'source'|'target')=>{
  const point=end==='source'?{x:props.sourceX,y:props.sourceY}:{x:props.targetX,y:props.targetY};
  return <button key={end} className="reconnect-handle nodrag nopan" data-edge-id={props.id} aria-label={`Reconnect ${end} of ${String(props.label)}`} title={`Drag to reconnect the ${end}`} style={{left:point.x,top:point.y}} onContextMenu={context} onPointerDown={event=>{
   if(event.button!==0)return;event.preventDefault();event.stopPropagation();event.currentTarget.setPointerCapture(event.pointerId);reconnectActive.current=true;setMenu(null);setReconnecting({end,point});
  }} onPointerMove={event=>{
   if(!event.currentTarget.hasPointerCapture(event.pointerId)||!reconnectActive.current)return;
   setReconnecting({end,point:flow.screenToFlowPosition({x:event.clientX,y:event.clientY},{snapToGrid:false})});
  }} onPointerCancel={()=>{reconnectActive.current=false;setReconnecting(null)}} onPointerUp={event=>{
   if(!event.currentTarget.hasPointerCapture(event.pointerId))return;
   event.stopPropagation();event.currentTarget.releasePointerCapture(event.pointerId);setReconnecting(null);
   if(!reconnectActive.current)return;reconnectActive.current=false;
   const handle=document.elementFromPoint(event.clientX,event.clientY)?.closest<HTMLElement>('.react-flow__handle');
   if(!handle?.dataset.nodeid||!handle.dataset.handleid)return;
   void reconnect?.({source:props.source,target:props.target,sourceHandle:props.sourceHandleId||'right',targetHandle:props.targetHandleId||'left',[end]:handle.dataset.nodeid,[end+'Handle']:handle.dataset.handleid});
  }}/>;
 };
 return <><g onContextMenu={context}>
  <BaseEdge id={props.id} path={path} markerStart={props.markerStart} markerEnd={props.markerEnd} interactionWidth={22} style={{stroke:lineColor,strokeWidth:props.selected?2.5:1.8}}/>
  <g className="route-segments nodrag nopan" onPointerMove={move} onPointerUp={finish} onPointerCancel={()=>{drag.current=null;setDraft(null)}}>
   {props.selected&&updateRoute&&route?.style!=='straight'&&vertices.slice(0,-1).map((a,index)=>{
    const b=vertices[index+1],horizontal=a.y===b.y;
    return <path key={index} d={`M${a.x} ${a.y}L${b.x} ${b.y}`} className={'route-segment '+(horizontal?'horizontal':'vertical')} tabIndex={0} role="button" aria-label={`Move ${horizontal?'horizontal':'vertical'} line segment ${index+1}`} onPointerDown={event=>start(event,index)} onKeyDown={event=>{
     const direction=horizontal?{ArrowUp:-1,ArrowDown:1}:{ArrowLeft:-1,ArrowRight:1},delta=direction[event.key as keyof typeof direction];
     if(delta){event.preventDefault();event.stopPropagation();const step=delta*(event.altKey?1:16);save(moveRouteSegment(vertices,index,{x:a.x+(horizontal?0:step),y:a.y+(horizontal?step:0)}).slice(1,-1))}
     else if(event.key==='ContextMenu'||(event.shiftKey&&event.key==='F10')){event.preventDefault();event.stopPropagation();setMenu(menuPosition(flow.flowToScreenPosition({x:(a.x+b.x)/2,y:(a.y+b.y)/2})))}
    }}><title>Drag this line segment {horizontal?'up or down':'left or right'} · right-click for line style · Alt bypasses snap</title></path>;
   })}
  </g>
 </g><EdgeLabelRenderer><span onContextMenu={context} onPointerDown={startLabel} onPointerMove={moveLabel} onPointerUp={finishLabel} onPointerCancel={()=>{labelDrag.current=null;setDraftLabelOffset(null)}} onKeyDown={labelKey} tabIndex={0} role="button" aria-label={`Move connection label for ${String(props.label)}`} title="Drag this label or use arrow keys. Alt moves one pixel." className={'edge-label edge-label-movable nodrag nopan'+(props.selected?' edge-label-selected':'')} data-edge-id={props.id} style={{zIndex:Number(props.data?.layerZ??0),color:route?.text_color||undefined,transform:`translate(-50%,-50%) translate(${displayedLabel.x}px,${displayedLabel.y}px)`}}>{props.label}</span>
 {props.selected&&reconnect&&(['source','target'] as const).map(reconnectControl)}
 {reconnecting&&<svg className="reconnect-preview"><path d={`M${reconnecting.end==='source'?props.targetX:props.sourceX} ${reconnecting.end==='source'?props.targetY:props.sourceY}L${reconnecting.point.x} ${reconnecting.point.y}`} fill="none" stroke="var(--diagram-arrow,#587d93)" strokeWidth={2} strokeDasharray="5 4"/></svg>}
 </EdgeLabelRenderer>{menu&&updateRoute&&createPortal(<div ref={menuRef} role="menu" aria-label="Connector options" className="route-menu nodrag nopan" style={{left:menu.x,top:menu.y}} onPointerDown={event=>event.stopPropagation()} onContextMenu={event=>event.preventDefault()} onKeyDown={event=>{
   if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();const buttons=[...event.currentTarget.querySelectorAll<HTMLButtonElement>('button')],index=buttons.indexOf(document.activeElement as HTMLButtonElement);buttons[(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length]?.focus()}
  }}><button role="menuitem" onClick={()=>chooseStyle('straight')}>Straight line</button><button role="menuitem" onClick={()=>chooseStyle('orthogonal')}>Right-angle line</button><button role="menuitem" onClick={resetRoute}>Reset route</button><button role="menuitem" onClick={resetLabel}>Reset label position</button><hr/>{updateLayer&&<LayerActions onChange={changeLayer}/>}<small>Drag a label or right-angle line. Arrow keys move the focused item.</small></div>,document.body)}
 </>;
}
