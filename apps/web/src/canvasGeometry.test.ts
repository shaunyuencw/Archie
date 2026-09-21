import {test,expect} from 'vitest';
import {Position} from '@xyflow/react';
import {routedPath} from './canvasGeometry';

const endpoints={sourceX:10,sourceY:20,targetX:300,targetY:200,sourcePosition:Position.Right,targetPosition:Position.Left};
const vertices=(path:string)=>[...path.matchAll(/[ML]\s*(-?[\d.]+)[, ]+(-?[\d.]+)/g)].map(m=>({x:Number(m[1]),y:Number(m[2])}));

test('automatic orthogonal connectors leave outward from endpoint handles',()=>{
 const points=vertices(routedPath(endpoints).path);
 expect(points[0]).toEqual({x:10,y:20});expect(points.at(-1)).toEqual({x:300,y:200});
 expect(points[1].x).toBeGreaterThan(10);expect(points[1].y).toBe(20);
 expect(points.at(-2)!.x).toBeLessThan(300);expect(points.at(-2)!.y).toBe(200);
});

test('manual waypoints remain exact while orthogonal segments stay axis aligned',()=>{
 const manual=[{x:120,y:-80},{x:220,y:260}];
 const points=vertices(routedPath(endpoints,'orthogonal',manual).path);
 for(const point of manual)expect(points).toContainEqual(point);
 for(let i=1;i<points.length;i++)expect(points[i].x===points[i-1].x||points[i].y===points[i-1].y).toBe(true);
 expect(manual).toEqual([{x:120,y:-80},{x:220,y:260}]);
});

test('straight manual routes use waypoints and position labels on the edited route',()=>{
 const {path,label}=routedPath(endpoints,'straight',[{x:100,y:-200}]);
 expect(vertices(path)).toContainEqual({x:100,y:-200});
 expect(label).toEqual({x:200,y:0});
});
