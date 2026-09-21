import {test,expect,type Page} from '@playwright/test';

const currentProject=async(page:Page)=>{
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 return (await page.request.get('/api/projects/'+await page.getByLabel('Open project').inputValue())).json();
};
const node=(page:Page,id:string)=>page.locator(`.react-flow__node[data-id="${id}"]`);

async function selectEdge(page:Page,id:string){
 const edge=page.locator(`.react-flow__edge[data-id="${id}"]`);
 let point={x:0,y:0};
 await expect(async()=>{point=await edge.locator('.react-flow__edge-interaction').evaluate((element,edgeId)=>{
  const path=element as SVGPathElement,matrix=path.getScreenCTM()!;
  for(const fraction of [.2,.8,.35,.65,.5]){
   const hit=path.getPointAtLength(path.getTotalLength()*fraction).matrixTransform(matrix);
   if(document.elementFromPoint(hit.x,hit.y)?.closest('.react-flow__edge')?.getAttribute('data-id')===edgeId)return {x:hit.x,y:hit.y};
  }
  throw new Error('No exposed connector segment');
 },id)}).toPass();
 await page.mouse.click(point.x,point.y);
 await expect(page.getByLabel('Interface purpose',{exact:true})).toBeVisible();
}

test('presentation palette, movable connection labels, resize and layer order persist without AI',async({page})=>{
 const modelCalls:string[]=[];
 page.on('request',request=>{if(request.method()==='POST'&&/\/(runs|sources|jobs|source-jobs)(?:\?|$)/.test(request.url()))modelCalls.push(request.url())});
 await page.goto('/');await page.getByRole('button',{name:/^Production portal/}).click();
 const web=node(page,'portal-web');await expect(web).toBeVisible();await web.click();
 await page.getByRole('button',{name:'Set Box fill color to Sky'}).click();
 await page.getByRole('button',{name:'Set Box border color to Blue'}).click();
 await page.getByRole('button',{name:'Set Box text color to Ink'}).click();
 await page.getByRole('button',{name:'Set Asset icon color to Violet'}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].fill_color).toBe('#e0f2fe');
 await expect(web.locator('.icon-tint')).toBeVisible();

 await selectEdge(page,'employee-web');
 await page.getByRole('button',{name:'Set Line color to Violet'}).click();
 await page.getByRole('button',{name:'Set Connection label color to Rose'}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.routes['employee-web'].line_color).toBe('#7c3aed');
 const label=page.getByRole('button',{name:/Move connection label for service requests/});
 await expect(label).toHaveCSS('color','rgb(190, 18, 60)');await label.press('ArrowRight');
 await expect.poll(async()=>(await currentProject(page)).views.logical.routes['employee-web'].label_offset?.x).toBe(16);
 await label.click({button:'right'});await page.getByRole('menuitem',{name:'Reset label position'}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.routes['employee-web'].label_offset).toBeNull();
 await label.hover();
 const labelBox=(await label.boundingBox())!;
 await page.mouse.move(labelBox.x+labelBox.width/2,labelBox.y+labelBox.height/2);await page.mouse.down();await page.mouse.move(labelBox.x+labelBox.width/2+32,labelBox.y+labelBox.height/2+25,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await currentProject(page)).views.logical.routes['employee-web'].label_offset?.y).toBeGreaterThan(0);
 const movedLabel=(await currentProject(page)).views.logical.routes['employee-web'].label_offset;

 // Visible 11px corner handles let both equipment and zones resize from any corner.
 await web.click();const beforeWeb=(await currentProject(page)).views.logical.placements['portal-web'];
 const bottomRight=web.locator('.react-flow__resize-control.handle.bottom.right');await expect(bottomRight).toBeVisible();
 await bottomRight.hover();
 const corner=(await bottomRight.boundingBox())!;
 await page.mouse.move(corner.x+corner.width/2,corner.y+corner.height/2);await page.mouse.down();await page.mouse.move(corner.x+58,corner.y+36,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].width).toBeGreaterThan(beforeWeb.width);
 const zone=node(page,'z1');await zone.getByText('Z1 · application services',{exact:true}).click();const beforeZone=(await currentProject(page)).views.logical.placements.z1;
 const childBefore=(await currentProject(page)).views.logical.placements['portal-app'];
 const topLeft=zone.locator('.react-flow__resize-control.handle.top.left');await expect(topLeft).toBeVisible();
 await topLeft.hover();
 const start=(await topLeft.boundingBox())!;
 await page.mouse.move(start.x+start.width/2,start.y+start.height/2);await page.mouse.down();await page.mouse.move(start.x-32,start.y-24,{steps:8});await page.mouse.up();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements.z1.width).toBeGreaterThan(beforeZone.width);
 const zoneAfter=(await currentProject(page)).views.logical.placements.z1,childAfter=(await currentProject(page)).views.logical.placements['portal-app'];
 expect(zoneAfter.x).toBeLessThan(beforeZone.x);expect(zoneAfter.y).toBeLessThan(beforeZone.y);
 expect(childAfter.x+zoneAfter.x).toBeCloseTo(childBefore.x+beforeZone.x,1);expect(childAfter.y+zoneAfter.y).toBeCloseTo(childBefore.y+beforeZone.y,1);

 await web.click({button:'right'});await page.getByRole('menuitem',{name:'Bring to front'}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].z_index).toBeGreaterThan(0);
 const front=(await currentProject(page)).views.logical.placements['portal-web'].z_index;
 await web.click({button:'right'});await page.getByRole('menuitem',{name:'Send backward',exact:true}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].z_index).toBe(front-1);
 await web.click({button:'right'});await page.getByRole('menuitem',{name:'Bring forward',exact:true}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].z_index).toBe(front);
 await web.click({button:'right'});await page.getByRole('menuitem',{name:'Send to back'}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].z_index).toBe(0);
 await page.getByRole('button',{name:'Save / reopen'}).click();
 const saved=await currentProject(page);
 expect(saved.views.logical.placements['portal-web'].fill_color).toBe('#e0f2fe');
 expect(saved.views.logical.placements['portal-web'].z_index).toBe(0);
 expect(saved.views.logical.routes['employee-web'].label_offset).toEqual(movedLabel);
 await page.getByRole('button',{name:'Undo',exact:true}).click();
 await expect.poll(async()=>(await currentProject(page)).views.logical.placements['portal-web'].z_index).toBeGreaterThan(0);
 await web.click();await page.getByRole('button',{name:'Set Asset icon color to Violet'}).scrollIntoViewIfNeeded();
 await page.screenshot({path:'../../reports/archie-presentation-palette.png',fullPage:true});
 expect(modelCalls).toHaveLength(0);
});
