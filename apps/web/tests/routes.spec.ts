import {test,expect} from '@playwright/test';

test('manual connector waypoints, line style, reconnect and prompt preservation',async({page})=>{
 const modelCalls:string[]=[];
 page.on('request',request=>{if(/\/runs(?:\?|$)|\/sources(?:\?|$)/.test(request.url()))modelCalls.push(request.url())});
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();
 const pid=await page.getByLabel('Open project').inputValue();
 const snapshot=async()=>await(await page.request.get('/api/projects/'+pid)).json();
 const initial=await snapshot(),edge=initial.interfaces[0];
 const connector=page.locator(`.react-flow__edge[data-id="${edge.id}"]`);
 const selectConnector=async()=>{
  // A path's bounding-box center can be on another overlapping connector.
  // Click an exposed point on this actual rendered path, just as the user does.
  const location=await connector.locator('.react-flow__edge-interaction').evaluate((element,id)=>{
   const path=element as SVGPathElement,matrix=path.getScreenCTM()!;
   for(const fraction of [.35,.65,.2,.8,.1,.9,.5]){
    const point=path.getPointAtLength(path.getTotalLength()*fraction).matrixTransform(matrix);
    if(document.elementFromPoint(point.x,point.y)?.closest('.react-flow__edge')?.getAttribute('data-id')===id)return {x:point.x,y:point.y};
   }
   throw new Error('Connector has no exposed clickable segment');
  },edge.id);
  await page.mouse.click(location.x,location.y);
  await expect(page.getByLabel('Interface purpose',{exact:true})).toHaveValue(edge.purpose||'');
 };
 await selectConnector();
 const handle=page.getByRole('button',{name:'Drag to add route waypoint',exact:true});
 await expect(handle).toBeVisible();
 const box=(await handle.boundingBox())!;
 await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();
 await page.mouse.move(box.x+75,box.y-70,{steps:10});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.routes[edge.id]?.points.length).toBe(1);
 const routed=await snapshot(),route=routed.views.logical.routes[edge.id];
 expect(route.locked).toBe(true);
 expect(route.points[0].x%16).toBe(0);expect(route.points[0].y%16).toBe(0);
 await page.getByLabel('Line style',{exact:true}).selectOption('straight');
 await expect.poll(async()=>(await snapshot()).views.logical.routes[edge.id].style).toBe('straight');
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 expect((await snapshot()).views.logical.routes[edge.id].points).toEqual(route.points);
 expect(modelCalls).toHaveLength(0);

 await page.getByLabel('Architecture prompt').fill('add one configuration workstation; keep the layout.');
 await page.getByRole('button',{name:'Preview proposed changes',exact:true}).click();
 await page.getByRole('button',{name:'Accept changes',exact:true}).click();
 await expect.poll(async()=>(await snapshot()).components.length).toBe(initial.components.length+1);
 const edited=await snapshot();
 expect(edited.views.logical.routes[edge.id].points).toEqual(route.points);
 expect(edited.views.logical.placements.vms).toEqual(initial.views.logical.placements.vms);
 expect(modelCalls).toHaveLength(1);

 // Reconnecting is explicit and clears only this connector's now-stale waypoints.
 await selectConnector();
 const updater=connector.locator('.react-flow__edgeupdater-target');
 const target=page.locator(`.react-flow__node[data-id="${edge.target==='analytics'?'c2':'analytics'}"] [data-handleid="left"]`);
 const from=(await updater.boundingBox())!,to=(await target.boundingBox())!;
 expect(await page.evaluate(b=>document.elementFromPoint(b.x+b.width/2,b.y+b.height/2)?.closest('.react-flow__edge')?.getAttribute('data-id'),from)).toBe(edge.id);
 await page.mouse.move(from.x+from.width/2,from.y+from.height/2);await page.mouse.down();
 await page.mouse.move(to.x+to.width/2,to.y+to.height/2,{steps:15});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).interfaces.find((i:any)=>i.id===edge.id).target).toBe(edge.target==='analytics'?'c2':'analytics');
 expect((await snapshot()).views.logical.routes[edge.id].points).toEqual([]);
 expect(modelCalls).toHaveLength(1);
});
