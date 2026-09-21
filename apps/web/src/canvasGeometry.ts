import {getSmoothStepPath,getStraightPath,Position,type EdgeProps} from '@xyflow/react';
import type {Point,Route} from '../../../packages/contracts/types';

type Endpoints=Pick<EdgeProps,'sourceX'|'sourceY'|'targetX'|'targetY'|'sourcePosition'|'targetPosition'>;
function facing(from:Point,to:Point):Position{
 return Math.abs(to.x-from.x)>=Math.abs(to.y-from.y)
  ?to.x>=from.x?Position.Right:Position.Left
  :to.y>=from.y?Position.Bottom:Position.Top;
}

/** React Flow supplies the step routing. Stored points remain literal, draggable waypoints. */
export function routedPath(endpoints:Endpoints,style:Route['style']='orthogonal',points:Point[]=[]){
 const anchors=[{x:endpoints.sourceX,y:endpoints.sourceY},...points,{x:endpoints.targetX,y:endpoints.targetY}];
 let path='',label={x:0,y:0},longest=-1;
 for(let i=0;i<anchors.length-1;i++){
  const source=anchors[i],target=anchors[i+1];
  const input={sourceX:source.x,sourceY:source.y,targetX:target.x,targetY:target.y,
   sourcePosition:i===0?endpoints.sourcePosition:facing(source,target),
   targetPosition:i===anchors.length-2?endpoints.targetPosition:facing(target,source)};
  const [segment,x,y]=style==='straight'?getStraightPath(input):getSmoothStepPath({...input,borderRadius:0,offset:points.length?0:24});
  path+=i===0?segment:segment.replace(/^M/,'L');
  const length=Math.abs(target.x-source.x)+Math.abs(target.y-source.y);
  if(length>longest){longest=length;label={x,y};}
 }
 return {path,label};
}
