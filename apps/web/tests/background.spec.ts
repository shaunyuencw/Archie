import {test,expect} from '@playwright/test';

test('follow-up JSON opens a prompt pack without importing a project or starting AI',async({page})=>{
 let imports=0,runs=0;
 page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith('/projects/import'))imports++;if(request.method()==='POST'&&/\/(runs|jobs|source-jobs)$/.test(request.url()))runs++;});
 await page.goto('/');await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 const id=await page.getByLabel('Open project').inputValue();
 await page.getByLabel('Import project',{exact:true}).setInputFiles('../../fixtures/demos/building-access/followups.json');
 const pack=page.getByRole('region',{name:'Follow-up prompt pack'});
 await expect(pack).toContainText('Building access event system');
 await expect(pack.getByRole('button',{name:/Use prompt/})).toHaveCount(3);
 await pack.getByRole('button',{name:'Use prompt 2',exact:true}).click();
 await expect(page.getByLabel('Architecture prompt')).toHaveValue(/Use push delivery from Door controllers/);
 await expect(page.getByLabel('Open project')).toHaveValue(id);
 expect(imports).toBe(0);expect(runs).toBe(0);
 await expect(page.getByRole('alert')).toHaveCount(0);
});

test('background draft permits project switching, survives reload and opens its owning project',async({page})=>{
 let jobs:any[]=[],submitted:any=null,owner='';
 await page.route('**/api/jobs',route=>route.fulfill({json:jobs}));
 await page.route('**/api/jobs/browser-background/dismiss',async route=>{jobs=[];await route.fulfill({json:{status:'dismissed'}})});
 await page.route('**/api/projects/*/jobs',async route=>{
  submitted=route.request().postDataJSON();
  jobs=[{id:'browser-background',project_id:owner,project_name:'Production service portal',kind:'prompt',status:'running',result:{}}];
  await route.fulfill({json:jobs[0]});
 });
 await page.goto('/');await page.getByRole('button',{name:/^Production portal/}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 owner=await page.getByLabel('Open project').inputValue();
 const before=await (await page.request.get('/api/projects/'+owner)).json();
 await page.getByLabel('Architecture prompt').fill('Rename Portal web service to Staff portal');
 await page.getByRole('button',{name:'Preview proposed changes',exact:true}).click();
 await expect(page.locator('.project-working')).toContainText('You can open another project');
 await expect(page.getByLabel('Open project')).toBeEnabled();
 await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue(owner);
 const other=await page.getByLabel('Open project').inputValue();expect(other).not.toBe(owner);
 const otherBefore=await (await page.request.get('/api/projects/'+other)).json();
 // A real local Mock proposal supplies the delayed job result. No model is invoked.
 const {kind,...request}=submitted;
 const response=await page.request.post(`/api/projects/${owner}/runs`,{data:request});expect(response.ok()).toBe(true);
 jobs=[{...jobs[0],status:'completed',result:await response.json()}];
 await expect(page.getByRole('button',{name:'Review draft',exact:true})).toBeVisible();
 await expect(page.getByLabel('Open project')).toHaveValue(other);
 await expect(page.getByRole('dialog',{name:'Here’s what will change'})).toHaveCount(0);
 await page.screenshot({path:'../../reports/archie-background-projects.png',fullPage:true});
 await page.reload();
 await page.getByRole('button',{name:'Review draft',exact:true}).click();
 await expect(page.getByLabel('Open project')).toHaveValue(owner);
 const review=page.getByRole('dialog',{name:'Here’s what will change'});
 await expect(review).toBeVisible();await expect(review).toContainText('Rename Portal web service to Staff portal');
 await review.getByRole('button',{name:'Accept changes',exact:true}).click();
 await expect(review).toHaveCount(0);
 const accepted=await (await page.request.get('/api/projects/'+owner)).json();
 expect(accepted.components.find((item:any)=>item.id==='portal-web').name).toBe('Staff portal');
 expect(accepted.components.length).toBe(before.components.length);
 expect(await (await page.request.get('/api/projects/'+other)).json()).toEqual(otherBefore);
 await expect(page.getByRole('button',{name:'Review draft',exact:true})).toHaveCount(0);
});

test('background failure is readable and belongs to its original project',async({page})=>{
 let jobs:any[]=[];
 await page.route('**/api/jobs',route=>route.fulfill({json:jobs}));
 await page.goto('/');await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 const owner=await page.getByLabel('Open project').inputValue();
 jobs=[{id:'failed-job',project_id:owner,project_name:'Failed draft',kind:'prompt',status:'failed',result:{},error:{code:'provider_timeout',message:'Ollama did not finish in time. Your accepted architecture was preserved.'}}];
 await expect(page.getByRole('region',{name:'Background activity'})).toContainText('Ollama did not finish in time');
 const snapshot=await (await page.request.get('/api/projects/'+owner)).json();expect(snapshot.components).toHaveLength(0);
});

test('draft policy suggestions are optional and accepted in the same undoable change',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 const id=await page.getByLabel('Open project').inputValue();
 await page.getByLabel('Upload document',{exact:true}).setInputFiles('../../fixtures/demos/portal/mock-input.docx');
 const review=page.getByRole('dialog',{name:'Here’s what will change'});
 await expect(review).toBeVisible();
 const choice=review.getByLabel('Suggest ARCH-TLS-01',{exact:true});
 await expect(choice).not.toBeChecked();await choice.check();
 expect((await (await page.request.get('/api/projects/'+id)).json()).policy_ids).toEqual([]);
 await review.getByRole('button',{name:'Accept changes',exact:true}).click();
 await expect(review).toHaveCount(0);
 const accepted=await (await page.request.get('/api/projects/'+id)).json();
 expect(accepted.components).toHaveLength(7);expect(accepted.policy_ids).toEqual(['ARCH-TLS-01']);
 await page.getByRole('button',{name:'Undo',exact:true}).click();
 await expect.poll(async()=>{const p=await (await page.request.get('/api/projects/'+id)).json();return [p.components.length,p.policy_ids]}).toEqual([0,[]]);
});

test('cancel keeps a running project busy until the worker stops and never opens a late draft',async({page})=>{
 let jobs:any[]=[],cancels=0;
 await page.route('**/api/jobs',route=>route.fulfill({json:jobs}));
 await page.route('**/api/projects/*/jobs',async route=>{
  const request=route.request().postDataJSON();
  jobs=[{id:'cancel-me',project_id:request.project_id,project_name:'Cancellation example',kind:'prompt',status:'running',result:null}];
  await route.fulfill({json:jobs[0]});
 });
 await page.route('**/api/jobs/cancel-me/cancel',async route=>{cancels++;jobs=[{...jobs[0],status:'cancelling'}];await route.fulfill({json:jobs[0]})});
 await page.goto('/');await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 const owner=await page.getByLabel('Open project').inputValue(),before=await (await page.request.get('/api/projects/'+owner)).json();
 await page.getByLabel('Architecture prompt').fill('Add a workstation');
 const submit=page.getByRole('button',{name:'Preview proposed changes',exact:true});await submit.click();
 const cancel=page.getByRole('button',{name:'Cancel activity for Cancellation example',exact:true});
 await expect(cancel).toBeEnabled();await cancel.click();
 await expect(cancel).toBeDisabled();await expect(page.getByRole('region',{name:'Background activity'})).toContainText('Stopping this action');
 await page.screenshot({path:'../../reports/archie-cancel-action.png',fullPage:true});
 await expect(submit).toBeDisabled();expect(cancels).toBe(1);
 jobs=[{...jobs[0],status:'cancelled'}];
 await expect(page.getByRole('region',{name:'Background activity'})).toContainText('Cancelled. Your accepted design is unchanged.');
 await expect(submit).toBeEnabled();await expect(page.getByRole('dialog',{name:'Here’s what will change'})).toHaveCount(0);
 expect(await (await page.request.get('/api/projects/'+owner)).json()).toEqual(before);
 await page.reload();await expect(page.getByRole('region',{name:'Background activity'})).toContainText('Cancelled.');
});
