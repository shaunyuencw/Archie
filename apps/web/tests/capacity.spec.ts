import {test,expect} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import {performance} from 'node:perf_hooks';

test('T14 browser loads, edits and reopens 50 components and 100 interfaces',async({page,browser})=>{
 const modelCalls:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue|continue-jobs|policy-review-jobs)(?:\?|$)/.test(r.url()))modelCalls.push(r.url())});
 const placements=Object.fromEntries(Array.from({length:50},(_,i)=>[`capacity-${i}`,{x:50+i%10*210,y:50+Math.floor(i/10)*150,width:185,height:110}]));
 const payload={name:'Synthetic capacity check — 50 components / 100 interfaces',synthetic:true,
  components:Array.from({length:50},(_,i)=>({id:`capacity-${i}`,name:`Component ${i}`,role:'application',asset_id:i%3===0?'server':'application'})),
  interfaces:Array.from({length:100},(_,i)=>({id:`capacity-interface-${i}`,source:`capacity-${i%50}`,target:`capacity-${(i+1+Math.floor(i/50)*9)%50}`,purpose:i<50?'integration':'events'})),
  views:Object.fromEntries(['logical','sv1','sv2'].map(type=>[type,{type,placements}]))};
 const imported=await page.request.post('/api/projects/import',{data:payload});expect(imported.ok()).toBeTruthy();const project=await imported.json();
 await page.goto('/');
 await expect(page.getByLabel('Open project').locator(`option[value="${project.id}"]`)).toHaveCount(1);
 const loadStart=performance.now();await page.getByLabel('Open project').selectOption(project.id);
 await expect(page.locator('.react-flow__node')).toHaveCount(50);await expect(page.locator('.react-flow__edge')).toHaveCount(100);
 const loadMs=performance.now()-loadStart;
 const snapshot=async()=>await(await page.request.get(`/api/projects/${project.id}`)).json();
 const node=page.locator('.react-flow__node[data-id="capacity-24"]');await node.click();
 const editMs:number[]=[];
 for(const x of [915,930,945]){
  const start=performance.now();await page.getByLabel('Placement x',{exact:true}).fill(String(x));await page.getByLabel('Placement x',{exact:true}).press('Tab');
  await expect.poll(async()=>(await snapshot()).views.logical.placements['capacity-24'].x).toBe(x);
  await expect(node).toHaveCSS('transform',`matrix(1, 0, 0, 1, ${x}, 350)`);editMs.push(performance.now()-start);
 }
 const framePromise=page.evaluate(()=>new Promise<number[]>(resolve=>{const gaps:number[]=[];let last=performance.now();function frame(now:number){gaps.push(now-last);last=now;if(gaps.length===60)resolve(gaps);else requestAnimationFrame(frame)}requestAnimationFrame(frame)}));
 const box=(await node.boundingBox())!;await page.mouse.move(box.x+box.width/2,box.y+box.height-8);await page.mouse.down();await page.mouse.move(box.x+box.width/2+24,box.y+box.height+4,{steps:24});await page.mouse.up();
 const gaps=await framePromise;
 await expect.poll(async()=>(await snapshot()).views.logical.placements['capacity-24'].x).not.toBe(945);
 const moved=await snapshot();
 const reopenStart=performance.now();await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 await expect(page.locator('.react-flow__node')).toHaveCount(50);await expect(page.locator('.react-flow__edge')).toHaveCount(100);
 const reopened=await snapshot();const reopenMs=performance.now()-reopenStart;
 expect(reopened.components).toHaveLength(50);expect(reopened.interfaces).toHaveLength(100);
 expect(reopened.views.logical.placements['capacity-24']).toEqual(moved.views.logical.placements['capacity-24']);
 const ids=new Set(reopened.components.map((c:any)=>c.id));expect(reopened.interfaces.every((i:any)=>ids.has(i.source)&&ids.has(i.target))).toBe(true);expect(modelCalls).toHaveLength(0);
 const ordered=[...gaps].sort((a,b)=>a-b);const round=(n:number)=>Math.round(n*100)/100;
 const report={platform:process.platform,browser:browser.browserType().name(),browser_version:browser.version(),viewport:page.viewportSize(),components:50,interfaces:100,load_to_render_ms:round(loadMs),placement_edit_saved_and_rendered_ms:editMs.map(round),reopen_ms:round(reopenMs),drag_frame_intervals_ms:{samples:gaps.length,median:round(ordered[30]),p95:round(ordered[Math.ceil(ordered.length*.95)-1]),maximum:round(ordered.at(-1)!)},model_calls:modelCalls.length,references_preserved:true,measurement:'Single local browser run. Wall-clock UI timings include Playwright action and polling overhead; 60 requestAnimationFrame intervals sampled across a pointer drag. This is not an INP or hardware benchmark.'};
 await mkdir('../../reports',{recursive:true});await writeFile(`../../reports/browser-capacity-${process.platform}.json`,JSON.stringify(report,null,2));
 await page.screenshot({path:`../../reports/browser-capacity-${process.platform}.png`,fullPage:true});
});
