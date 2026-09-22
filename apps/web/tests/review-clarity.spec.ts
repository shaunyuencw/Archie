import {test,expect} from '@playwright/test';

test('readable draft warnings, bulk policy selection and icon choice remain explicit and undoable',async({page})=>{
 const created=await page.request.post('/api/projects',{data:{name:'Synthetic review clarity check'}});
 const project=await created.json();
 const draft={project_id:project.id,base_revision:project.revision,base_views:Object.fromEntries(Object.entries(project.views).map(([k,v]:[string,any])=>[k,v.revision])),origin:'assistant',operations:[
  {op:'add',entity:'components',id:'tmp:client',value:{name:'Operator Client',role:'client',asset_id:'workstation',scope:'unknown'}},
  {op:'add',entity:'components',id:'tmp:camera',value:{name:'Camera Sensors',role:'sensor/device',asset_id:'camera',scope:'unknown'}},
  {op:'add',entity:'interfaces',id:'tmp:video',value:{source:'tmp:camera',target:'tmp:client',purpose:'live video'}},
 ],findings:['tmp:client: scope kept unknown because no matching scope claim was supplied.','tmp:camera: scope kept unknown because no matching scope claim was supplied.']};
 const preview=await page.request.post(`/api/projects/${project.id}/preview`,{data:draft});expect(preview.ok()).toBe(true);const proposal=await preview.json();
 // The provider notification is scripted; preview, policy lookup and acceptance use the real local API.
 await page.route('**/api/jobs',route=>route.fulfill({json:[{id:'scripted-review',project_id:project.id,project_name:project.name,kind:'prompt',status:'completed',request:{},result:{proposal},error:null,created_at:new Date().toISOString(),started_at:null,finished_at:null,dismissed_at:null,cancel_requested_at:null}]}));
 await page.goto('/');await page.getByRole('button',{name:'Review draft',exact:true}).click();
 const review=page.getByRole('dialog',{name:'Here’s what will change'});await expect(review).toBeVisible();
 const notes=review.locator('.review-notes');await expect(notes).toContainText('Confirm what belongs inside the architecture');
 await expect(notes).toContainText('Operator Client');await expect(notes).toContainText('Camera Sensors');await expect(notes).not.toContainText('tmp:');await expect(notes).not.toContainText('scope claim');
 const policies=review.locator('.policy-recommendations');await expect(policies.getByRole('checkbox').first()).toBeVisible();
 const count=await policies.getByRole('checkbox').count();expect(count).toBeGreaterThan(1);
 await policies.getByRole('button',{name:'Select all',exact:true}).click();
 await expect(policies.locator('input:checked')).toHaveCount(count);
 expect((await(await page.request.get(`/api/projects/${project.id}`)).json()).policy_ids).toEqual([]);
 await policies.getByRole('button',{name:'Clear all',exact:true}).click();await expect(policies.locator('input:checked')).toHaveCount(0);
 await policies.getByRole('button',{name:'Select all',exact:true}).click();
 await page.screenshot({path:'../../reports/review-clarity-browser.png'});
 await review.getByRole('button',{name:'Accept changes',exact:true}).click();await expect(review).toHaveCount(0);
 const accepted=await(await page.request.get(`/api/projects/${project.id}`)).json();expect(accepted.policy_ids).toHaveLength(count);
 await page.getByRole('button',{name:'Canvas',exact:true}).click();
 const camera=page.locator('.react-flow__node').filter({has:page.getByRole('img',{name:'Camera Sensors',exact:true})});
 await expect(camera.getByRole('img',{name:'Camera Sensors',exact:true})).toHaveAttribute('src','/api/assets/camera.svg');
 await camera.click();await page.getByLabel('Component icon',{exact:true}).selectOption('sensor');
 await expect(camera.getByRole('img',{name:'Camera Sensors',exact:true})).toHaveAttribute('src','/api/assets/sensor.svg');
 await page.getByLabel('Architecture boundary',{exact:true}).selectOption('internal');
 const snapshot=async()=>await(await page.request.get(`/api/projects/${project.id}`)).json();
 await expect.poll(async()=>(await snapshot()).components.find((c:any)=>c.name==='Camera Sensors').scope).toBe('internal');
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 await expect(camera.getByRole('img',{name:'Camera Sensors',exact:true})).toHaveAttribute('src','/api/assets/sensor.svg');
 expect((await snapshot()).interfaces).toEqual(accepted.interfaces);
});
