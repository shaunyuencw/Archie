import {test,expect} from '@playwright/test';

test('whole connector segments, direct line menu, reconnect and prompt preservation',async({page})=>{
 const modelCalls:string[]=[];
 page.on('request',request=>{if(request.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue|continue-jobs|policy-review-jobs)(?:\?|$)/.test(request.url()))modelCalls.push(request.url())});
 await page.goto('/');await page.getByText('Legacy examples',{exact:true}).click();await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');const pid=await page.getByLabel('Open project').inputValue();
 const snapshot=async()=>await(await page.request.get('/api/projects/'+pid)).json();
 const initial=await snapshot(),edge=initial.interfaces[0];
 const connector=page.locator(`.react-flow__edge[data-id="${edge.id}"]`);
 const selectConnector=async()=>{
  // A path's bounding-box center can be on another overlapping connector.
  // Click an exposed point on this actual rendered path, just as the user does.
  let location={x:0,y:0};
  await expect(async()=>{location=await connector.locator('.react-flow__edge-interaction').evaluate((element,id)=>{
   const path=element as SVGPathElement,matrix=path.getScreenCTM()!;
   const hits=[];
   for(const fraction of [.35,.65,.2,.8,.1,.9,.5]){
    const point=path.getPointAtLength(path.getTotalLength()*fraction).matrixTransform(matrix);
    if(document.elementFromPoint(point.x,point.y)?.closest('.react-flow__edge')?.getAttribute('data-id')===id)return {x:point.x,y:point.y};
    hits.push([point.x,point.y,document.elementFromPoint(point.x,point.y)?.outerHTML.slice(0,180)]);
   }
   throw new Error('Connector has no exposed clickable segment: '+JSON.stringify(hits));
  },edge.id)}).toPass({timeout:5000});
  const bounds=(await connector.boundingBox())!;
  // Locator actions wait for the SVG group to settle after a view refresh.
  await connector.click({position:{x:location.x-bounds.x,y:location.y-bounds.y}});
  await expect(page.getByLabel('Interface purpose',{exact:true})).toHaveValue(edge.purpose||'');
 };
 await selectConnector();
 const segment=connector.locator('.route-segment').nth(1);
 // Axis-aligned SVG paths have a zero-width/height geometric box; hit-test their stroke.
 await expect(segment).toBeAttached();
 let dragPoint={x:0,y:0,horizontal:false};
 await expect(async()=>{dragPoint=await segment.evaluate(element=>{
  const path=element as SVGPathElement,matrix=path.getScreenCTM()!;
  // The label is intentionally draggable and may cover a segment midpoint. Pick a
  // visible point on this exact segment instead of force-clicking through its label.
  for(const fraction of [.2,.8,.35,.65,.1,.9,.5]){
   const point=path.getPointAtLength(path.getTotalLength()*fraction).matrixTransform(matrix);
   if(document.elementFromPoint(point.x,point.y)?.closest('.route-segment')===path)return {x:point.x,y:point.y,horizontal:path.classList.contains('horizontal')};
  }
  throw new Error('Selected route segment has no exposed draggable point');
 })}).toPass({timeout:5000});
 expect(await page.evaluate(point=>document.elementFromPoint(point.x,point.y)?.classList.contains('route-segment'),dragPoint)).toBe(true);
 await page.mouse.move(dragPoint.x,dragPoint.y);await page.mouse.down();
 await page.mouse.move(dragPoint.x+(dragPoint.horizontal?0:-75),dragPoint.y+(dragPoint.horizontal?-70:0),{steps:10});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.routes[edge.id]?.points.length).toBeGreaterThanOrEqual(2);
 const routed=await snapshot(),route=routed.views.logical.routes[edge.id];
 expect(route.locked).toBe(true);
 const axis=dragPoint.horizontal?'y':'x';
 expect(route.points[0][axis]%16).toBe(0);
 expect(route.points[0][axis]).toBe(route.points[1][axis]);
 // Saving the command and fetching its rendered view finish on separate frames.
 await expect(async()=>{
  const rendered=await connector.locator('.react-flow__edge-path').getAttribute('d');
  const vertices=[...rendered!.matchAll(/[ML]\s*(-?[\d.]+)[, ]+(-?[\d.]+)/g)].map(m=>({x:Number(m[1]),y:Number(m[2])}));
  for(let i=1;i<vertices.length;i++)expect(vertices[i].x===vertices[i-1].x||vertices[i].y===vertices[i-1].y).toBe(true);
  expect(vertices.slice(1,-1)).toEqual(route.points);
 }).toPass({timeout:5000});
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

 // A straight-line command clears all bends, including after a saved manual route.
 await selectConnector();
 const contextPoint=await connector.locator('.react-flow__edge-path').evaluate(element=>{
  const path=element as SVGPathElement,point=path.getPointAtLength(path.getTotalLength()*.4).matrixTransform(path.getScreenCTM()!);
  return {x:point.x,y:point.y};
 });
 await page.mouse.click(contextPoint.x,contextPoint.y,{button:'right'});
 await page.getByRole('menuitem',{name:'Straight line',exact:true}).click();
 await expect.poll(async()=>(await snapshot()).views.logical.routes[edge.id].style).toBe('straight');
 expect((await snapshot()).views.logical.routes[edge.id].points).toEqual([]);
 await expect.poll(async()=>(await connector.locator('.react-flow__edge-path').getAttribute('d'))!.match(/L/g)).toHaveLength(1);
 await page.getByLabel('Line style',{exact:true}).selectOption('orthogonal');
 await expect.poll(async()=>(await snapshot()).views.logical.routes[edge.id].style).toBe('orthogonal');
 await expect(connector.locator('.route-segment')).not.toHaveCount(0);
 expect(modelCalls).toHaveLength(1);

 // Reconnecting is explicit and clears only this connector's now-stale waypoints.
 await selectConnector();
 const updater=page.getByRole('button',{name:'Reconnect target of '+(edge.purpose||'purpose ?'),exact:true});
 const target=page.locator(`.react-flow__node[data-id="${edge.target==='analytics'?'c2':'analytics'}"] [data-handleid="left"]`);
 const from=(await updater.boundingBox())!,to=(await target.boundingBox())!;
 expect(await page.evaluate(b=>document.elementFromPoint(b.x+b.width/2,b.y+b.height/2)?.getAttribute('data-edge-id'),from)).toBe(edge.id);
 await page.mouse.move(from.x+from.width/2,from.y+from.height/2);await page.mouse.down();
 await page.mouse.move(to.x+to.width/2,to.y+to.height/2,{steps:15});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).interfaces.find((i:any)=>i.id===edge.id).target).toBe(edge.target==='analytics'?'c2':'analytics');
 expect((await snapshot()).views.logical.routes[edge.id].points).toEqual([]);
 // The independent overlay handles reconnect either end without changing layer order.
 const sourceUpdater=page.getByRole('button',{name:'Reconnect source of '+(edge.purpose||'purpose ?'),exact:true});
 await sourceUpdater.hover();
 const sourceFrom=(await sourceUpdater.boundingBox())!;
 const sourceTo=page.locator('.react-flow__node[data-id="operator"] [data-handleid="right"]');
 const sourceBox=(await sourceTo.boundingBox())!;
 await page.mouse.move(sourceFrom.x+sourceFrom.width/2,sourceFrom.y+sourceFrom.height/2);await page.mouse.down();
 await page.mouse.move(sourceBox.x+sourceBox.width/2,sourceBox.y+sourceBox.height/2,{steps:12});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).interfaces.find((i:any)=>i.id===edge.id).source).toBe('operator');
 expect((await snapshot()).views.logical.routes[edge.id].source_handle).toBe('right');
 expect(modelCalls).toHaveLength(1);
});
