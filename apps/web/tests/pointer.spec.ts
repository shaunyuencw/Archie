import {test,expect,type Locator} from '@playwright/test';
test('T07 pointer move, resize, connect, reconnect, delete and reopen make zero model calls',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue|continue-jobs|policy-review-jobs)(?:\?|$)/.test(r.url()))calls.push(r.url())});
 await page.goto('/');await page.getByText('Legacy examples',{exact:true}).click();await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 const node=(id:string)=>page.locator(`.react-flow__node[data-id="${id}"]`);
 await expect(node('vms')).toBeVisible();await expect(page.getByLabel('Open project')).not.toHaveValue('');const pid=await page.getByLabel('Open project').inputValue();
 const snapshot=async()=>await (await page.request.get('/api/projects/'+pid)).json();
 const initial=await snapshot();
 await node('vms').click();let b=(await node('vms').boundingBox())!;
 await page.mouse.move(b.x+b.width/2,b.y+b.height-10);await page.mouse.down();await page.mouse.move(b.x+b.width/2+15,b.y+b.height+2,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).not.toBe(initial.views.logical.placements.vms.x);
 await expect(page.getByText('Presentation 1',{exact:true})).toBeVisible();
 const corner=node('vms').locator('.react-flow__resize-control.bottom.right');b=(await corner.boundingBox())!;
 await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+14,b.y+10,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.width).toBeGreaterThan(initial.views.logical.placements.vms.width);
 const resized=(await snapshot()).views.logical.placements.vms;
 const parent=initial.views.logical.placements[initial.deployments.find((d:any)=>d.component_id==='vms').zone_id];
 await expect(node('vms')).toHaveCSS('width',`${resized.width}px`);
 await expect(node('vms')).toHaveCSS('height',`${resized.height}px`);
 await expect(node('vms')).toHaveCSS('transform',`matrix(1, 0, 0, 1, ${resized.x+parent.x}, ${resized.y+parent.y})`);
 const drag=async(from:Locator,to:Locator)=>{
  // A persisted resize can precede React Flow's fresh handle measurements. Hover
  // waits for a stable, actionable source; hit-test the stroke before pressing.
  await from.hover();
  await expect.poll(()=>from.evaluate(element=>{const b=element.getBoundingClientRect();return document.elementFromPoint(b.x+b.width/2,b.y+b.height/2)===element})).toBe(true);
  const a=(await from.boundingBox())!;await page.mouse.move(a.x+a.width/2,a.y+a.height/2);await page.mouse.down();
  const z=(await to.boundingBox())!;
  await page.mouse.move(z.x+z.width/2,z.y+z.height/2,{steps:16});
  // End on the current target handle if the viewport/measurement settled while moving.
  await to.hover();await page.mouse.up();
 };
 await drag(node('vms').locator('[data-handleid="right"]'),node('c2').locator('[data-handleid="left"]'));
 await expect.poll(async()=>(await snapshot()).interfaces.length).toBe(5);
 let saved=await snapshot();const edge=saved.interfaces.find((e:any)=>!initial.interfaces.some((i:any)=>i.id===e.id));
 const connector=page.locator(`.react-flow__edge[data-id="${edge.id}"]`);
 // The route's bounding-box center may be inside an unrelated component.
 // Select an exposed stroke point; labels themselves can now be dragged.
 await expect(async()=>{
  const point=await connector.locator('.react-flow__edge-interaction').evaluate((element,id)=>{
   const path=element as SVGPathElement,matrix=path.getScreenCTM()!;
   for(const fraction of [.35,.65,.2,.8,.1,.9,.5]){
    const p=path.getPointAtLength(path.getTotalLength()*fraction).matrixTransform(matrix);
    if(document.elementFromPoint(p.x,p.y)?.closest('.react-flow__edge')?.getAttribute('data-id')===id)return {x:p.x,y:p.y};
   }
   throw new Error('Connector has no exposed selectable stroke');
  },edge.id);
  await page.mouse.click(point.x,point.y);
  await expect(connector).toHaveClass(/selected/);
 }).toPass({timeout:5000});
 await drag(connector.locator('.react-flow__edgeupdater-target'),node('analytics').locator('[data-handleid="left"]'));
 await expect.poll(async()=>(await snapshot()).interfaces.find((e:any)=>e.id===edge.id).target).toBe('analytics');
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 await expect(page.getByRole('button',{name:'Undo',exact:true})).toBeEnabled();
 saved=await snapshot();expect(saved.interfaces.find((e:any)=>e.id===edge.id).target).toBe('analytics');
 await node('vms').click();page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Delete selected object',exact:true}).click();
 await expect(node('vms')).toHaveCount(0);await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(node('vms')).toBeVisible();
 expect(calls).toHaveLength(0);
});

test('project and reusable pattern JSON can be imported from the workbench',async({page})=>{
 await page.goto('/');await page.getByText('Legacy examples',{exact:true}).click();await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();await expect(page.getByLabel('Open project')).not.toHaveValue('');const pid=await page.getByLabel('Open project').inputValue();
 const pattern=await (await page.request.get(`/api/projects/${pid}/exports/pattern`)).body();
 await page.getByLabel('Import project',{exact:true}).setInputFiles({name:'pattern.json',mimeType:'application/json',buffer:pattern});
 await expect(page.getByRole('heading',{name:'Synthetic reusable architecture pattern',exact:true})).toBeVisible();
 expect(await page.getByLabel('Open project').inputValue()).not.toBe(pid);
 await page.getByTitle('Add network-zone',{exact:true}).click();await expect(page.locator('.zone-node').filter({hasText:'New zone'})).toBeVisible();
});
