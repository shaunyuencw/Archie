import {test,expect} from '@playwright/test';
const mod=process.platform==='darwin'?'Meta':'Control';

test('canvas shortcuts, groups, clipboard, delete and history preserve references without AI',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(/\/(runs|sources)(\/|$)/.test(new URL(r.url()).pathname))calls.push(r.url())});
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 const node=(id:string)=>page.locator(`.react-flow__node[data-id="${id}"]`);
 await expect(node('vms')).toBeVisible();const pid=await page.getByLabel('Open project').inputValue();
 const snapshot=async()=>await (await page.request.get('/api/projects/'+pid)).json();
 const initial=await snapshot(),canvas=page.getByRole('region',{name:'Architecture canvas'});
 await node('vms').click();await page.keyboard.press('ArrowRight');
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).toBe(initial.views.logical.placements.vms.x+1);
 await page.keyboard.press(`${mod}+z`);await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).toBe(initial.views.logical.placements.vms.x);
 await page.keyboard.press(`${mod}+Shift+z`);await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).toBe(initial.views.logical.placements.vms.x+1);
 await page.getByLabel('Object name',{exact:true}).fill('Typing leaves canvas intact');await page.getByLabel('Object name',{exact:true}).press(`${mod}+a`);await page.getByLabel('Object name',{exact:true}).press('Backspace');
 expect((await snapshot()).components.length).toBe(8);await page.getByLabel('Object name',{exact:true}).fill(initial.components.find((c:any)=>c.id==='vms').name);await page.getByLabel('Object name',{exact:true}).press('Tab');
 await node('vms').click();await page.keyboard.press(`${mod}+d`);await expect.poll(async()=>(await snapshot()).components.length).toBe(9);
 let saved=await snapshot();const copy=saved.components.find((c:any)=>!initial.components.some((x:any)=>x.id===c.id));expect(copy.status).toBe('proposed');expect(copy.evidence).toEqual([]);
 await canvas.focus();await page.keyboard.press(`${mod}+c`);await page.keyboard.press(`${mod}+v`);await expect.poll(async()=>(await snapshot()).components.length).toBe(10);
 page.once('dialog',d=>d.accept());await page.keyboard.press('Backspace');await expect.poll(async()=>(await snapshot()).components.length).toBe(9);
 await page.keyboard.press(`${mod}+z`);await expect.poll(async()=>(await snapshot()).components.length).toBe(10);
 await page.keyboard.press('Escape');await expect(page.locator('.react-flow__node.selected')).toHaveCount(0);
 await node('vms').click({position:{x:10,y:10}});await node('analytics').click({modifiers:[mod]});await expect(page.locator('.react-flow__node.selected')).toHaveCount(2);
 const before=await snapshot();await page.keyboard.press('Shift+ArrowDown');await expect.poll(async()=>(await snapshot()).views.logical.placements.analytics.y).toBe(before.views.logical.placements.analytics.y+10);
 expect((await snapshot()).views.logical.placements.vms.y).toBe(before.views.logical.placements.vms.y+10);
 await page.keyboard.press(`${mod}+a`);await expect(page.locator('.react-flow__node.selected')).toHaveCount((await snapshot()).components.length+initial.zones.length);
 await page.keyboard.press('Escape');expect(calls).toHaveLength(0);
});

test('panels collapse, resize and persist on laptop; component library filters',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();
 await page.getByLabel('Search component library').fill('workstation');await expect(page.locator('.palette button')).toHaveCount(1);
 const canvas=page.getByRole('region',{name:'Architecture canvas'}),initial=(await canvas.boundingBox())!.width;
 await page.getByLabel('Collapse Archie panel',{exact:true}).click();await expect(page.locator('.assistant')).toBeHidden();
 await page.getByLabel('Collapse Inspector panel',{exact:true}).click();await expect(page.locator('.inspector-panel')).toBeHidden();expect((await canvas.boundingBox())!.width).toBeGreaterThan(initial+450);
 await page.reload();await expect(page.locator('.assistant')).toBeHidden();await expect(page.locator('.inspector-panel')).toBeHidden();
 await page.getByLabel('Toggle Archie panel',{exact:true}).click();await page.getByLabel('Toggle Inspector panel',{exact:true}).click();
 const resizer=page.getByRole('separator',{name:'Resize left panel'});await resizer.focus();await page.keyboard.press('ArrowRight');await expect.poll(async()=>(await page.locator('.assistant').boundingBox())!.width).toBe(282);
 await page.getByLabel('Focus canvas',{exact:true}).click();await expect(page.locator('.assistant')).toBeHidden();await page.getByLabel('Focus canvas',{exact:true}).click();await expect(page.locator('.assistant')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../reports/archie-mac-laptop.png',fullPage:true});
});

test('late view responses cannot replace the selected view',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();
 await page.route('**/views/logical',async route=>{const response=await route.fetch();await new Promise(resolve=>setTimeout(resolve,400));await route.fulfill({response})});
 await page.getByRole('button',{name:'SV-2-style',exact:true}).click();await expect(page.locator('.edge-label').first()).toContainText('initiator');
 await page.getByRole('button',{name:'Logical',exact:true}).click();await page.getByRole('button',{name:'SV-1-style',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="vms-system"]')).toBeVisible();await page.waitForTimeout(600);await expect(page.locator('.react-flow__node[data-id="vms-system"]')).toBeVisible();
});

test('group pointer movement and Option snapping preserve architectural deployment zones',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(/\/(runs|sources)(\/|$)/.test(new URL(r.url()).pathname))calls.push(r.url())});
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 const node=(id:string)=>page.locator(`.react-flow__node[data-id="${id}"]`);await expect(node('vms')).toBeVisible();
 const pid=await page.getByLabel('Open project').inputValue(),snapshot=async()=>await(await page.request.get('/api/projects/'+pid)).json();
 await node('vms').click({position:{x:10,y:10}});await node('analytics').click({modifiers:[mod]});await expect(page.locator('.react-flow__node.selected')).toHaveCount(2);
 const before=await snapshot();let box=(await node('vms').boundingBox())!;
 await page.mouse.move(box.x+box.width/2,box.y+box.height-10);await page.mouse.down();await page.mouse.move(box.x+box.width/2+26,box.y+box.height+14,{steps:10});await page.mouse.up();
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).not.toBe(before.views.logical.placements.vms.x);
 await expect.poll(async()=>(await snapshot()).views.logical.placements.analytics.x).not.toBe(before.views.logical.placements.analytics.x);
 const grouped=await snapshot();expect(grouped.deployments).toEqual(before.deployments);
 await page.getByRole('region',{name:'Architecture canvas'}).focus();await page.keyboard.press('Escape');await node('vms').click();
 box=(await node('vms').boundingBox())!;await page.keyboard.down('Alt');await page.mouse.move(box.x+box.width/2,box.y+box.height-10);await page.mouse.down();await page.mouse.move(box.x+box.width/2+7,box.y+box.height-7,{steps:5});await page.mouse.up();await page.keyboard.up('Alt');
 await expect.poll(async()=>(await snapshot()).views.logical.placements.vms.x).not.toBe(grouped.views.logical.placements.vms.x);
 const free=await snapshot();expect(Math.abs(free.views.logical.placements.vms.x%16)).toBeGreaterThan(.01);expect(free.deployments).toEqual(before.deployments);expect(calls).toHaveLength(0);
});
