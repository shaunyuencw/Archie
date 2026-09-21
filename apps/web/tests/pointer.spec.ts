import {test,expect} from '@playwright/test';
test('T07 pointer move, resize, connect, reconnect, delete and reopen make zero model calls',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(r.url().includes('/runs')||r.url().includes('/sources'))calls.push(r.url())});
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 const node=(id:string)=>page.locator(`.react-flow__node[data-id="${id}"]`);
 await expect(node('vms')).toBeVisible();const pid=await page.getByLabel('Open project').inputValue();
 const snapshot=async()=>await (await page.request.get('/api/projects/'+pid)).json();
 const initial=await snapshot();
 await node('vms').click();let b=(await node('vms').boundingBox())!;
 await page.mouse.move(b.x+b.width/2,b.y+b.height-10);await page.mouse.down();await page.mouse.move(b.x+b.width/2+15,b.y+b.height+2,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).not.toBe(initial.views.logical.placements.vms.x);
 await expect(page.getByText('Presentation 1',{exact:true})).toBeVisible();
 const corner=node('vms').locator('.react-flow__resize-control.bottom.right');b=(await corner.boundingBox())!;
 await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+14,b.y+10,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.width).toBeGreaterThan(initial.views.logical.placements.vms.width);
 const drag=async(from:any,to:any)=>{const a=(await from.boundingBox())!,z=(await to.boundingBox())!;await page.mouse.move(a.x+a.width/2,a.y+a.height/2);await page.mouse.down();await page.mouse.move(z.x+z.width/2,z.y+z.height/2,{steps:16});await page.mouse.up()};
 await drag(node('vms').locator('[data-handleid="right"]'),node('c2').locator('[data-handleid="left"]'));
 await expect.poll(async()=>(await snapshot()).interfaces.length).toBe(5);
 let saved=await snapshot();const edge=saved.interfaces.find((e:any)=>!initial.interfaces.some((i:any)=>i.id===e.id));
 const connector=page.locator(`.react-flow__edge[data-id="${edge.id}"]`);
 await connector.locator('.react-flow__edge-interaction').click({force:true});
 await drag(connector.locator('.react-flow__edgeupdater-target'),node('analytics').locator('[data-handleid="left"]'));
 await expect.poll(async()=>(await snapshot()).interfaces.find((e:any)=>e.id===edge.id).target).toBe('analytics');
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 saved=await snapshot();expect(saved.interfaces.find((e:any)=>e.id===edge.id).target).toBe('analytics');
 await node('vms').click();page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Delete selected object',exact:true}).click();
 await expect(node('vms')).toHaveCount(0);await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(node('vms')).toBeVisible();
 expect(calls).toHaveLength(0);
});

test('project and reusable pattern JSON can be imported from the workbench',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();const pid=await page.getByLabel('Open project').inputValue();
 const pattern=await (await page.request.get(`/api/projects/${pid}/exports/pattern`)).body();
 await page.getByLabel('Import project',{exact:true}).setInputFiles({name:'pattern.json',mimeType:'application/json',buffer:pattern});
 await expect(page.getByRole('heading',{name:'Synthetic reusable architecture pattern',exact:true})).toBeVisible();
 expect(await page.getByLabel('Open project').inputValue()).not.toBe(pid);
 await page.getByTitle('Add network-zone',{exact:true}).click();await expect(page.locator('.zone-node').filter({hasText:'New zone'})).toBeVisible();
});
