import {test,expect} from '@playwright/test';

test('A fresh 20-component draft without zones opens compactly and survives reopen',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue-jobs|policy-review-jobs)(?:\?|$)/.test(r.url()))calls.push(r.url())});
 const created=await page.request.post('/api/projects',{data:{name:'Synthetic functional layout without zones'}});
 expect(created.ok()).toBeTruthy();const empty=await created.json();
 const operations=[
  ...Array.from({length:20},(_,i)=>({op:'add',entity:'components',id:`tmp:service-${i}`,value:{name:`Functional service ${i}`,role:'application',asset_id:'application'}})),
  ...Array.from({length:22},(_,i)=>({op:'add',entity:'interfaces',id:`tmp:flow-${i}`,value:{source:`tmp:service-${i%20}`,target:`tmp:service-${(i<20?i+1:i+4)%20}`,purpose:'status events'}})),
 ];
 const preview=await page.request.post(`/api/projects/${empty.id}/preview`,{data:{project_id:empty.id,base_revision:empty.revision,base_views:{logical:0,sv1:0,sv2:0},operations}});
 expect(preview.ok()).toBeTruthy();const proposal=await preview.json();
 const accepted=await page.request.post(`/api/changes/${proposal.id}/accept`,{data:{}});
 expect(accepted.ok()).toBeTruthy();const project=await accepted.json();
 expect(project.zones).toEqual([]);expect(project.components).toHaveLength(20);expect(project.interfaces).toHaveLength(22);
 await page.goto('/');await page.getByLabel('Open project',{exact:true}).selectOption(project.id);
 const check=async(kind:string)=>{
  await expect(page.locator('.react-flow__node')).toHaveCount(20);
  const placements=Object.values(project.views[kind].placements) as {x:number,y:number}[];
  expect(new Set(placements.map(n=>n.x)).size).toBeGreaterThan(1);
  expect(new Set(placements.map(n=>n.y)).size).toBeGreaterThan(1);
  const viewport=await page.getByRole('region',{name:'Architecture canvas'}).boundingBox();
  await expect(async()=>{
   const boxes=await page.locator('.react-flow__node').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width}}));
   for(const box of boxes){expect(box.width).toBeGreaterThan(90);expect(box.x).toBeGreaterThanOrEqual(viewport!.x);expect(box.y).toBeGreaterThanOrEqual(viewport!.y);expect(box.right).toBeLessThanOrEqual(viewport!.x+viewport!.width);expect(box.bottom).toBeLessThanOrEqual(viewport!.y+viewport!.height)}
  }).toPass();
 };
 await check('logical');
 await page.screenshot({path:'../../reports/no-zone-layout-browser.png'});
 await page.getByRole('button',{name:'Connection details',exact:true}).click();await check('sv2');
 await page.reload();await page.getByLabel('Open project',{exact:true}).selectOption(project.id);await check('logical');
 const reopened=await(await page.request.get(`/api/projects/${project.id}`)).json();
 expect(reopened.views).toEqual(project.views);expect(reopened.revision).toBe(1);expect(calls).toEqual([]);
});

test('Arrange fits zones to contents, preserves pins and supports one-step undo without AI',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue-jobs|policy-review-jobs)(?:\?|$)/.test(r.url()))calls.push(r.url())});
 const placements=Object.fromEntries(Array.from({length:6},(_,i)=>[`zone-${i}`,{x:40+i%2*580,y:60+Math.floor(i/2)*400,width:530,height:350,locked:i===0}]));
 for(let i=0;i<6;i++)placements[`part-${i}`]={x:30,y:65,width:185,height:90,locked:false};
 const response=await page.request.post('/api/projects/import',{data:{name:'Synthetic compact layout check',
  zones:Array.from({length:6},(_,i)=>({id:`zone-${i}`,name:`Security zone ${i}`})),
  components:Array.from({length:6},(_,i)=>({id:`part-${i}`,name:`Application service ${i}`,role:'application',asset_id:'application'})),
  deployments:Array.from({length:6},(_,i)=>({id:`deployment-${i}`,component_id:`part-${i}`,zone_id:`zone-${i}`})),
  interfaces:Array.from({length:5},(_,i)=>({id:`flow-${i}`,source:`part-${i}`,target:`part-${i+1}`,purpose:'status events'})),
  views:Object.fromEntries(['logical','sv1','sv2'].map(type=>[type,{type,placements:type==='sv1'?{}:placements}]))}});
 expect(response.ok()).toBeTruthy();const project=await response.json();
 await page.goto('/');await page.getByLabel('Open project',{exact:true}).selectOption(project.id);
 await expect(page.locator('.react-flow__node')).toHaveCount(12);
 const snapshot=async()=>await(await page.request.get(`/api/projects/${project.id}`)).json();
 await page.getByRole('button',{name:'Arrange view',exact:true}).click();
 await expect.poll(async()=>(await snapshot()).views.logical.revision).toBe(1);
 const compact=await snapshot();
 expect(compact.views.logical.placements['zone-0']).toEqual(project.views.logical.placements['zone-0']);
 expect(compact.views.logical.placements['zone-1'].height).toBe(178);
 expect(compact.views.logical.placements['zone-1'].width).toBeLessThan(530);
 expect(compact.revision).toBe(project.revision);expect(compact.interfaces).toEqual(project.interfaces);
 await expect(page.locator('.canvas-hint')).toContainText('Layout compacted');
 const viewport=await page.getByRole('region',{name:'Architecture canvas'}).boundingBox();expect(viewport).not.toBeNull();
 await expect(async()=>{
  const boxes=await page.locator('.react-flow__node').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}}));
  for(const box of boxes){expect(box.x).toBeGreaterThanOrEqual(viewport!.x);expect(box.y).toBeGreaterThanOrEqual(viewport!.y);expect(box.right).toBeLessThanOrEqual(viewport!.x+viewport!.width);expect(box.bottom).toBeLessThanOrEqual(viewport!.y+viewport!.height)}
 }).toPass();
 await page.screenshot({path:'../../reports/compact-layout-browser.png'});
 await page.getByRole('button',{name:'Arrange view',exact:true}).click();
 await expect(page.locator('.canvas-hint')).toContainText('already compact');
 expect((await snapshot()).views.logical.revision).toBe(1);
 await page.getByRole('button',{name:'Undo',exact:true}).click();
 await expect.poll(async()=>(await snapshot()).views.logical.placements).toEqual(project.views.logical.placements);
 expect(calls).toEqual([]);
});
