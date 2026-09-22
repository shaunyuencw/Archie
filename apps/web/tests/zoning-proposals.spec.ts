import {test,expect} from '@playwright/test';

test('proposed zoning stays explicit through review, canvas, sources, reopen and undo',async({page})=>{
 const providerCalls:string[]=[];
 page.on('request',r=>{if(r.method()==='POST'&&/\/(runs|sources|jobs|source-jobs|continue-jobs)(?:\?|$)/.test(r.url()))providerCalls.push(r.url())});
 const created=await page.request.post('/api/projects',{data:{name:'Synthetic zoning review'}});
 const project=await created.json();
 const rationale='Separate application processing from device networks pending security review.';
 const requirement='Cyber segmentation is required; detailed zone assignments are not specified.';
 const source=(id:string,kind:string,name:string,text:string)=>({op:'add',entity:'sources',id,value:{name,kind,sha256:id,canonical_id:id,passages:[{locator:'paragraph/1',text}],processed:['paragraph/1']}});
 const claim=(id:string,source_id:string,source_kind:string,target_id:string,field:string,excerpt:string)=>({op:'add',entity:'claims',id,value:{source_id,source_kind,source_version:'1.0',locator:'paragraph/1',excerpt,target_id,field,review:'unreviewed'}});
 const draft={project_id:project.id,base_revision:project.revision,base_views:{logical:0,sv1:0,sv2:0},origin:'assistant',operations:[
  source('tmp:spec','document','Synthetic cyber requirements',requirement),
  source('tmp:design','assistant_proposal','Archie zoning design assumptions',rationale),
  claim('tmp:basis','tmp:spec','document','tmp:zone','proposal_basis',requirement),
  claim('tmp:assumption','tmp:design','assistant_proposal','tmp:zone','proposed_zoning',rationale),
  claim('tmp:assignment','tmp:design','assistant_proposal','tmp:deployment','proposed_zoning',rationale),
  {op:'add',entity:'zones',id:'tmp:zone',value:{name:'Application zone'}},
  {op:'add',entity:'components',id:'tmp:app',value:{name:'Control service',role:'application',asset_id:'application',scope:'unknown'}},
  {op:'add',entity:'deployments',id:'tmp:deployment',value:{component_id:'tmp:app',zone_id:'tmp:zone'}},
 ],findings:[`tmp:zone: proposed zoning — ${rationale}`,`tmp:deployment: proposed zoning — ${rationale}`]};
 const preview=await page.request.post(`/api/projects/${project.id}/preview`,{data:draft});
 expect(preview.ok()).toBeTruthy();const proposal=await preview.json();
 await page.route(`**/api/changes/${proposal.id}/accept`,async route=>{
  const response=await route.fetch();if(response.ok())proposal.state='accepted';await route.fulfill({response});
 });
 let dismissed=false;
 await page.route('**/api/jobs/scripted-zoning/dismiss',async route=>{dismissed=true;await route.fulfill({json:{}})});
 // Only the completion notification is scripted; review and persistence use the API.
 await page.route('**/api/jobs',route=>route.fulfill({json:dismissed?[]:[{id:'scripted-zoning',project_id:project.id,project_name:project.name,kind:'prompt',status:'completed',request:{},result:{proposal},error:null,created_at:new Date().toISOString(),started_at:null,finished_at:null,dismissed_at:null,cancel_requested_at:null}]}));
 await page.goto('/');await page.getByRole('button',{name:'Review draft',exact:true}).click();
 const review=page.getByRole('dialog',{name:'Here’s what will change'});
 await expect(review.getByRole('heading',{name:'Review proposed zoning',exact:true})).toBeVisible();
 await expect(review.locator('.review-notes')).toContainText('Control service → Application zone');
 await expect(review.locator('.review-notes')).toContainText('does not configure network security');
 const snapshot=async()=>await(await page.request.get(`/api/projects/${project.id}`)).json();
 expect((await snapshot()).zones).toHaveLength(0);
 await review.getByRole('button',{name:'Accept changes',exact:true}).click();await expect(review).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Save / reopen',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Canvas',exact:true}).click();
 await expect(page.locator('.react-flow__node')).toHaveCount(2);
 await expect(page.locator('.zone-node')).toContainText('Application zone (proposed)');
 const accepted=await snapshot();expect(accepted.deployments[0].zone_id).toBe(accepted.zones[0].id);
 const placement=accepted.views.logical.placements[accepted.components[0].id];const zone=accepted.views.logical.placements[accepted.zones[0].id];
 expect(placement.x+placement.width).toBeLessThanOrEqual(zone.width-24);
 expect(placement.y+placement.height).toBeLessThanOrEqual(zone.height-24);
 await page.screenshot({path:'../../reports/zoning-proposal-canvas.png'});
 await page.getByRole('button',{name:'Overview',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Proposed zoning',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Sources',exact:true}).click();
 await expect(page.getByText('Archie design proposal',{exact:true})).toBeVisible();
 await expect(page.getByText('Proposed · unreviewed',{exact:true})).toHaveCount(2);
 await expect(page.getByText('Archie’s design assumption, not a fact stated by the specification or proof of implemented security.',{exact:true})).toHaveCount(2);
 await page.screenshot({path:'../../reports/zoning-proposal-sources.png'});
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 expect((await snapshot()).claims).toEqual(accepted.claims);
 await page.getByRole('button',{name:'Undo',exact:true}).click();
 await expect.poll(async()=>(await snapshot()).zones.length).toBe(0);
 expect(providerCalls).toEqual([]);
});
