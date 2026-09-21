import {test,expect,type Page} from '@playwright/test';

const viewport=async(page:Page)=>page.locator('.react-flow__viewport').evaluate(element=>{
 const matrix=new DOMMatrix(getComputedStyle(element).transform);
 return {x:matrix.e,y:matrix.f,zoom:matrix.a};
});

test('diagram overview is unclipped and navigates by click, drag and scroll without editing the project',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:/^Production portal/}).click();
 await expect(page.locator('.react-flow__node[data-id="portal-web"]')).toBeVisible();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 const projectId=await page.getByLabel('Open project').inputValue();
 const snapshot=async()=>(await page.request.get('/api/projects/'+projectId)).json();
 const before=await snapshot(),mutations:string[]=[];
 page.on('request',request=>{
  if(/\/api\//.test(request.url())&&['POST','PUT','PATCH','DELETE'].includes(request.method()))mutations.push(request.method()+' '+request.url());
 });
 const overview=page.getByRole('img',{name:'Diagram overview: click to centre, drag to pan, scroll to zoom',exact:true});
 const panel=page.getByTestId('rf__minimap');
 await expect(overview).toBeVisible();await overview.hover();

 // Every miniature box must fit inside the visible overview, not merely inside
 // a larger SVG that is cropped by a small CSS panel.
 await expect(async()=>{
  const map=(await overview.boundingBox())!,frame=(await panel.boundingBox())!;
  expect(map.width).toBeCloseTo(frame.width,0);expect(map.height).toBeCloseTo(frame.height,0);
  expect(map.x).toBeCloseTo(frame.x,0);expect(map.y).toBeCloseTo(frame.y,0);
  const boxes=await overview.locator('.react-flow__minimap-node').evaluateAll(elements=>elements.map(element=>{
   const rect=element.getBoundingClientRect();return {x:rect.x,y:rect.y,right:rect.right,bottom:rect.bottom};
  }));
  expect(boxes.length).toBe(await page.locator('.react-flow__node').count());
  expect(boxes.length).toBeGreaterThan(3);
  for(const box of boxes){
   expect(box.x).toBeGreaterThanOrEqual(map.x-.5);expect(box.y).toBeGreaterThanOrEqual(map.y-.5);
   expect(box.right).toBeLessThanOrEqual(map.x+map.width+.5);expect(box.bottom).toBeLessThanOrEqual(map.y+map.height+.5);
  }
 }).toPass();

 const initial=await viewport(page),map=(await overview.boundingBox())!;
 const click={x:map.x+map.width*.75,y:map.y+map.height*.3};
 const destination=await overview.evaluate((element,point)=>{
  const svg=element as SVGSVGElement,p=new DOMPoint(point.x,point.y).matrixTransform(svg.getScreenCTM()!.inverse());
  return {x:p.x,y:p.y};
 },click);
 const canvas=(await page.locator('.react-flow').boundingBox())!;
 await page.mouse.click(click.x,click.y);
 await expect.poll(async()=>{const current=await viewport(page);return Math.hypot(current.x-initial.x,current.y-initial.y)}).toBeGreaterThan(20);
 // A click centres the chosen place, preserving zoom. Wait for the animated
 // navigation to finish so the next drag cannot pass because of this movement.
 await expect.poll(async()=>(await viewport(page)).x).toBeCloseTo(canvas.width/2-destination.x*initial.zoom,0);
 await expect.poll(async()=>(await viewport(page)).y).toBeCloseTo(canvas.height/2-destination.y*initial.zoom,0);
 await expect.poll(async()=>(await viewport(page)).zoom).toBeCloseTo(initial.zoom,5);
 const clicked=await viewport(page);
 await page.mouse.move(map.x+map.width/2,map.y+map.height/2);await page.mouse.down();
 await page.mouse.move(map.x+map.width/2+22,map.y+map.height/2-14,{steps:10});await page.mouse.up();
 await expect.poll(async()=>{const current=await viewport(page);return Math.hypot(current.x-clicked.x,current.y-clicked.y)}).toBeGreaterThan(20);
 expect((await viewport(page)).zoom).toBeCloseTo(clicked.zoom,5);

 const panned=await viewport(page);
 await overview.hover();await page.mouse.wheel(0,-450);
 await expect.poll(async()=>(await viewport(page)).zoom).toBeGreaterThan(panned.zoom*1.2);
 await page.screenshot({path:'../../reports/archie-minimap.png',fullPage:true});

 await page.getByRole('button',{name:'Dark mode',exact:true}).click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 // The current viewport outline must remain distinguishable against the dark overview.
 const outline=await overview.locator('.react-flow__minimap-mask').evaluate(element=>{
  const rgb=(value:string)=>value.match(/[\d.]+/g)!.map(Number);
  const luminance=(values:number[])=>values.slice(0,3).map(value=>{const c=value/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4}).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
  const style=getComputedStyle(element),background=getComputedStyle(element.closest('.react-flow__minimap')!).backgroundColor;
  const front=luminance(rgb(style.stroke)),back=luminance(rgb(background));
  return {stroke:style.stroke,width:Number.parseFloat(style.strokeWidth),contrast:(Math.max(front,back)+.05)/(Math.min(front,back)+.05)};
 });
 expect(outline.stroke).not.toBe('none');expect(outline.width).toBeGreaterThan(0);expect(outline.contrast).toBeGreaterThanOrEqual(3);
 expect(await snapshot()).toEqual(before);
 expect(mutations).toEqual([]);
});
