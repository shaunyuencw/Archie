import {getSmoothStepPath,getStraightPath,Position,type EdgeProps} from '@xyflow/react';
import type {Point,Route} from '../../../packages/contracts/types';

type Endpoints=Pick<EdgeProps,'sourceX'|'sourceY'|'targetX'|'targetY'|'sourcePosition'|'targetPosition'>;
const same=(a:Point,b:Point)=>a.x===b.x&&a.y===b.y;
const aligned=(a:Point,b:Point)=>a.x===b.x||a.y===b.y;

/** Remove duplicate/collinear vertices without collapsing a deliberate reversal. */
export function simplifyRoute(points:Point[]):Point[]{
 const result:Point[]=[];
 for(const point of points){
  if(result.length&&same(result.at(-1)!,point))continue;
  while(result.length>1){
   const a=result.at(-2)!,b=result.at(-1)!;
   if(!((a.x===b.x&&b.x===point.x)||(a.y===b.y&&b.y===point.y))||(b.x-a.x)*(point.x-b.x)+(b.y-a.y)*(point.y-b.y)<0)break;
   result.pop();
  }
  result.push({...point});
 }
 return result;
}

/** Move both ends of one segment together; connection anchors stay attached. */
export function moveRouteSegment(vertices:Point[],index:number,coordinate:Point):Point[]{
 if(index<0||index>=vertices.length-1||!aligned(vertices[index],vertices[index+1]))return vertices.map(p=>({...p}));
 const next=vertices.map(p=>({...p})),axis=vertices[index].y===vertices[index+1].y?'y':'x';
 next[index][axis]=coordinate[axis];next[index+1][axis]=coordinate[axis];
 if(index===0)next.unshift({...vertices[0]});
 if(index===vertices.length-2)next.push({...vertices.at(-1)!});
 return simplifyRoute(next);
}

/** Keep a dragged label relative to the route's current automatic label anchor. */
export function moveLabelOffset(offset:Point,start:Point,current:Point):Point{
 return {x:offset.x+current.x-start.x,y:offset.y+current.y-start.y};
}

function facing(from:Point,to:Point):Position{
 return Math.abs(to.x-from.x)>=Math.abs(to.y-from.y)
  ?to.x>=from.x?Position.Right:Position.Left
  :to.y>=from.y?Position.Bottom:Position.Top;
}

/** React Flow supplies automatic elbows. Aligned stored vertices are literal segments. */
export function routedPath(endpoints:Endpoints,style:Route['style']='orthogonal',points:Point[]=[]){
 // DOM measurements after zoom can drift by ~0.0001px. Do not turn that into elbows.
 const pixel=(value:number)=>Math.round(value*1000)/1000;
 const anchors=[{x:pixel(endpoints.sourceX),y:pixel(endpoints.sourceY)},...points,{x:pixel(endpoints.targetX),y:pixel(endpoints.targetY)}];
 const vertices:Point[]=[];
 for(let i=0;i<anchors.length-1;i++){
  const source=anchors[i],target=anchors[i+1];
  const input={sourceX:source.x,sourceY:source.y,targetX:target.x,targetY:target.y,
   sourcePosition:i===0?endpoints.sourcePosition:facing(source,target),
   targetPosition:i===anchors.length-2?endpoints.targetPosition:facing(target,source)};
  const [segment]=style==='straight'||(points.length&&aligned(source,target))?getStraightPath(input):getSmoothStepPath({...input,borderRadius:0,offset:points.length?0:24});
  // borderRadius:0 means Q commands only repeat their adjacent L vertex.
  vertices.push(...[...segment.matchAll(/[ML]\s*(-?[\d.e+]+)[, ]+(-?[\d.e+]+)/g)].map(match=>({x:Number(match[1]),y:Number(match[2])})));
 }
 const route=simplifyRoute(vertices);
 let label=route[0]??anchors[0],longest=-1;
 for(let i=1;i<route.length;i++){
  const a=route[i-1],b=route[i],length=Math.hypot(b.x-a.x,b.y-a.y);
  if(length>longest){longest=length;label={x:(a.x+b.x)/2,y:(a.y+b.y)/2};}
 }
 return {path:route.map((p,i)=>`${i?'L':'M'}${p.x} ${p.y}`).join(''),label,vertices:route};
}
