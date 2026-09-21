import {test,expect,type Locator,type Page} from '@playwright/test';

const node=(page:Page,id:string)=>page.locator(`.react-flow__node[data-id="${id}"]`);
const currentProject=async(page:Page)=>{
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 return (await page.request.get('/api/projects/'+await page.getByLabel('Open project').inputValue())).json();
};
function modelRequests(page:Page){
 const requests:string[]=[];
 page.on('request',request=>{if(request.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue-jobs|policy-review-jobs)(?:\?|$)/.test(request.url()))requests.push(request.url())});
 return requests;
}

// The middle server deliberately overlaps the connection and its label. Hit testing
// verifies what can actually be seen and clicked, rather than just saved z-index values.
async function overlapProject(page:Page){
 const components=[
  {id:'source',name:'Source workstation',role:'workstation',asset_id:'workstation'},
  {id:'target',name:'Destination service',role:'application',asset_id:'application-server'},
  {id:'obstacle',name:'Overlapping server',role:'server',asset_id:'server'},
 ];
 const project={name:'Synthetic overlapping layers',policy_ids:[],components,
  zones:[{id:'zone',name:'Shared application zone'}],
  deployments:components.map(component=>({id:'deployment-'+component.id,component_id:component.id,zone_id:'zone'})),
  interfaces:[{id:'connection',source:'source',target:'target',purpose:'Transit traffic',data_direction:'source_to_target'}],
  views:{logical:{type:'logical',placements:{
   zone:{x:20,y:30,width:960,height:360,fill_color:'#fef3c7'},
   source:{x:20,y:140,width:180,height:115},
   target:{x:720,y:140,width:180,height:115},
   obstacle:{x:365,y:110,width:200,height:180,fill_color:'#e0f2fe',icon_color:'#7c3aed'},
  },routes:{connection:{style:'straight',source_handle:'right',target_handle:'left'}}},sv1:{type:'sv1'},sv2:{type:'sv2'}},
 };
 await page.goto('/');
 await page.getByLabel('Import project',{exact:true}).setInputFiles({name:'synthetic-layers.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(project))});
 await expect(node(page,'obstacle')).toBeVisible();
}

async function strokePoint(page:Page,fraction:number){
 return page.locator('.react-flow__edge[data-id="connection"] .react-flow__edge-interaction').evaluate((element,value)=>{
  const path=element as SVGPathElement,point=path.getPointAtLength(path.getTotalLength()*value).matrixTransform(path.getScreenCTM()!);
  return {x:point.x,y:point.y};
 },fraction);
}
async function hitAt(page:Page,point:{x:number,y:number}){
 return page.evaluate(({x,y})=>{
  const hit=document.elementFromPoint(x,y);
  if(hit?.closest('.edge-label'))return 'connection';
  return hit?.closest('.react-flow__node,.react-flow__edge')?.getAttribute('data-id')||null;
 },point);
}
async function crossingHits(page:Page){
 const label=(await page.getByRole('button',{name:'Move connection label for Transit traffic',exact:true}).boundingBox())!;
 return [await hitAt(page,await strokePoint(page,.68)),await hitAt(page,{x:label.x+label.width/2,y:label.y+label.height/2})];
}
async function lineLayer(page:Page,name:string){
 const point=await strokePoint(page,.1);
 await page.mouse.click(point.x,point.y,{button:'right'});
 await page.getByRole('menuitem',{name,exact:true}).click();
}
async function serverLayer(page:Page,name:string){
 const box=(await node(page,'obstacle').boundingBox())!;
 await page.mouse.click(box.x+box.width*.8,box.y+box.height*.85,{button:'right'});
 await page.getByRole('menuitem',{name,exact:true}).click();
}

test('lines, labels and component assets share visible layer order with undo and saved reopening',async({page})=>{
 const requests=modelRequests(page);
 await overlapProject(page);
 await expect.poll(()=>crossingHits(page)).toEqual(['obstacle','obstacle']);
 await lineLayer(page,'Bring to front');
 await expect.poll(()=>crossingHits(page)).toEqual(['connection','connection']);
 // Selection must not silently elevate the line over a component brought forward.
 const exposed=await strokePoint(page,.1);await page.mouse.click(exposed.x,exposed.y);
 await serverLayer(page,'Bring to front');
 await expect.poll(()=>crossingHits(page)).toEqual(['obstacle','obstacle']);
 await serverLayer(page,'Send to back');
 await expect.poll(()=>crossingHits(page)).toEqual(['connection','connection']);
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 await expect.poll(()=>crossingHits(page)).toEqual(['connection','connection']);
 await page.getByRole('button',{name:'Undo',exact:true}).click();
 await expect.poll(()=>crossingHits(page)).toEqual(['obstacle','obstacle']);
 await lineLayer(page,'Bring to front');
 await expect.poll(()=>crossingHits(page)).toEqual(['connection','connection']);
 await lineLayer(page,'Send to back');
 await expect.poll(()=>crossingHits(page)).toEqual(['obstacle','obstacle']);
 expect(requests).toHaveLength(0);
});

async function expectReadableDarkSurface(locator:Locator){
 await expect(locator).toBeVisible();
 const sample=await locator.evaluate(element=>{
  const rgb=(value:string)=>value.match(/[\d.]+/g)!.map(Number);
  const luminance=(values:number[])=>values.slice(0,3).map(value=>{const channel=value/255;return channel<=.04045?channel/12.92:((channel+.055)/1.055)**2.4}).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
  let parent:Element|null=element,background=[255,255,255];
  while(parent){const value=rgb(getComputedStyle(parent).backgroundColor);if(value.length===3||value[3]===1){background=value;break}parent=parent.parentElement}
  const back=luminance(background),front=luminance(rgb(getComputedStyle(element).color));
  return {background:back,contrast:(Math.max(front,back)+.05)/(Math.min(front,back)+.05)};
 });
 expect(sample.background).toBeLessThan(.15);
 expect(sample.contrast).toBeGreaterThanOrEqual(4.5);
}

test('dark mode persists across reload with readable editor surfaces and unchanged diagram colors',async({page})=>{
 const requests=modelRequests(page);let jobs:any[]=[];
 await page.route('**/api/jobs',route=>route.fulfill({json:jobs}));
 await page.goto('/');
 await page.getByRole('button',{name:/^Production portal/}).click();
 const web=node(page,'portal-web');await expect(web).toBeVisible();await web.click();
 await page.getByRole('button',{name:'Set Box fill color to Sky'}).click();
 await page.getByRole('button',{name:'Set Asset icon color to Violet'}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].icon_color).toBe('#7c3aed');
 const before=await currentProject(page),owner=before.id;
 const themeToggle=page.getByRole('button',{name:'Dark mode',exact:true});
 await expect(themeToggle).toHaveAttribute('aria-pressed','false');
 await themeToggle.click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await expect(themeToggle).toHaveAttribute('aria-pressed','true');
 await expect(web.locator('.arch-node')).toHaveCSS('background-color','rgb(224, 242, 254)');
 await expect(web.locator('.primary-symbol.icon-tint')).toHaveCSS('background-color','rgb(124, 58, 237)');
 await expectReadableDarkSurface(page.getByRole('heading',{name:'Project workspace',exact:true}));
 await expectReadableDarkSurface(page.locator('.view-bar'));
 await web.click({button:'right'});
 await expectReadableDarkSurface(page.getByRole('menuitem',{name:'Bring to front',exact:true}));
 await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Connections',exact:true}).click();
 await expectReadableDarkSurface(page.getByRole('columnheader',{name:'Connection',exact:true}));
 await page.getByRole('button',{name:'Edit connection employee-web',exact:true}).click();
 await expectReadableDarkSurface(page.getByLabel('Purpose for employee-web',{exact:true}));
 await page.getByRole('button',{name:'Canvas',exact:true}).click();
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 expect(await page.evaluate(()=>localStorage.getItem('archie.theme'))).toBe('dark');
 await page.getByLabel('Open project').selectOption(owner);await expect(web).toBeVisible();await web.click();
 await expect(web.locator('.arch-node')).toHaveCSS('background-color','rgb(224, 242, 254)');
 await expect(web.locator('.primary-symbol.icon-tint')).toHaveCSS('background-color','rgb(124, 58, 237)');
 expect(await currentProject(page)).toEqual(before);
 await page.screenshot({path:'../../reports/archie-dark-mode.png',fullPage:true});

 // A saved local preview exercises the review dialog without requesting any model.
 const response=await page.request.post(`/api/projects/${owner}/preview`,{data:{project_id:owner,base_revision:before.revision,base_views:Object.fromEntries(Object.entries(before.views).map(([key,value]:[string,any])=>[key,value.revision])),operations:[{op:'update',entity:'components',id:'portal-web',value:{name:'Staff portal'}}]}});
 expect(response.ok()).toBe(true);
 jobs=[{id:'dark-review',project_id:owner,project_name:before.name,kind:'prompt',status:'completed',result:{proposal:await response.json()}}];
 const dialog=page.getByRole('dialog',{name:'Here’s what will change',exact:true});
 await expect(dialog).toBeVisible();
 await expectReadableDarkSurface(dialog.getByRole('heading',{name:'Here’s what will change',exact:true}));
 await expectReadableDarkSurface(dialog.locator('.review-items h3').first());
 await dialog.getByRole('button',{name:'Review later',exact:true}).click();
 await themeToggle.click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','light');
 await expect(themeToggle).toHaveAttribute('aria-pressed','false');
 await expect(web.locator('.arch-node')).toHaveCSS('background-color','rgb(224, 242, 254)');
 expect(await currentProject(page)).toEqual(before);
 expect(requests).toHaveLength(0);
});
