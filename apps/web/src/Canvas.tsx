import {Handle,Position,NodeResizer,BaseEdge,EdgeLabelRenderer,getStraightPath,getSmoothStepPath,type NodeProps,type EdgeProps} from '@xyflow/react';
const positions={left:Position.Left,right:Position.Right,top:Position.Top,bottom:Position.Bottom};
export function ArchitectureNode({data,selected}:NodeProps){return <div className={'arch-node '+(data.role==='zone'?'zone-node':'')}>
 <NodeResizer isVisible={selected} minWidth={80} minHeight={45} onResizeEnd={(_,p)=>(data.resize as Function)(p)}/>
 {data.role!=='zone'&&<><img src={'/api/assets/'+data.asset_id+'.svg'} alt=""/>{Object.entries(positions).map(([id,position])=><span key={id}><Handle id={id} type="source" position={position}/><Handle id={id+'-in'} type="target" position={position}/></span>)}</>}
 <strong>{String(data.label)}</strong><small>{data.role==='zone'?'SECURITY ZONE':String(data.role)}</small></div>}
export function ArchitectureEdge(props:EdgeProps){const route=props.data?.route as any;const points=route?.points||[];const [automatic,x,y]=route?.style==='straight'?getStraightPath(props):getSmoothStepPath(props);
 const path=points.length?`M ${props.sourceX} ${props.sourceY} ${points.map((p:any)=>`L ${p.x} ${p.y}`).join(' ')} L ${props.targetX} ${props.targetY}`:automatic;
 return <><BaseEdge path={path} style={props.selected?{stroke:'#0f766e',strokeWidth:3}:{stroke:'#718096',strokeWidth:1.6}}/><EdgeLabelRenderer><span className="edge-label nodrag nopan" style={{transform:`translate(-50%,-50%) translate(${x}px,${y}px)`}}>{props.label}</span></EdgeLabelRenderer></>}
