import {test,expect} from '@playwright/test';

test('Ollama duplicate upload explains the existing source and opens its evidence',async({page})=>{
 let jobs:any[]=[],owner='',preflights=0,uploads=0;
 const message='This document already belongs to this project. Two sections remain; open Sources to continue reading.';
 await page.route('**/api/jobs',route=>route.fulfill({json:jobs}));
 // Fail closed: all model actions are intercepted, including the background upload path.
 await page.route(/\/api\/projects\/[^/]+\/(runs|sources|jobs|source-jobs|policy-review-jobs|sources\/[^/]+\/continue(?:-jobs)?)$/,route=>route.abort());
 await page.route('**/api/projects/*/source-preflight',async route=>{
  expect(new URL(route.request().url()).pathname).toBe(`/api/projects/${owner}/source-preflight`);
  expect(route.request().postData()).toContain('name="provider"\r\n\r\nollama');
  preflights++;
  await route.fulfill({json:{provider:'ollama',requests:1,unprocessed_batches:0,max_cost_usd:0,unsupported_pages:[]}});
 });
 await page.route('**/api/projects/*/source-jobs',async route=>{
  expect(new URL(route.request().url()).pathname).toBe(`/api/projects/${owner}/source-jobs`);
  expect(route.request().postData()).toContain('name="provider"\r\n\r\nollama');
  uploads++;
  jobs=[{id:'duplicate-document',project_id:owner,project_name:'New architecture',kind:'source',status:'completed',result:{duplicate:true,message}}];
  await route.fulfill({json:jobs[0]});
 });
 await page.goto('/');await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Open project')).not.toHaveValue('');
 owner=await page.getByLabel('Open project').inputValue();
 const initial=await (await page.request.get('/api/projects/'+owner)).json();
 const seeded=await page.request.post(`/api/projects/${owner}/commands`,{data:{project_id:owner,base_revision:initial.revision,base_views:Object.fromEntries(Object.entries(initial.views).map(([key,view]:[string,any])=>[key,view.revision])),operations:[{op:'add',entity:'sources',id:'test-document',value:{name:'techspec.docx',kind:'document',origin:'upload',sha256:'browser-fixture',canonical_id:'browser-document',passages:[{locator:'section/1',text:'Synthetic portal requirements.'},{locator:'section/2',text:'Synthetic protected data requirements.'}],processed:[],unprocessed:['section/1','section/2']}}]}});
 expect(seeded.ok()).toBe(true);
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();
 const before=await (await page.request.get('/api/projects/'+owner)).json();
 await page.getByLabel('Provider',{exact:true}).selectOption('ollama');
 await page.getByLabel('Upload document',{exact:true}).setInputFiles('../../fixtures/demos/portal/techspec.docx');
 const plan=page.locator('.processing-plan');
 await expect(plan).toContainText('your local Ollama model');
 expect(uploads).toBe(0);
 await plan.getByRole('button',{name:'Read and propose a design',exact:true}).click();
 const notification=page.locator('[data-job-id="duplicate-document"]');
 await expect(notification).toContainText(message);
 await notification.getByRole('button',{name:'Open project',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Sources and evidence',exact:true})).toBeVisible();
 await expect(page.locator('.source-card')).toContainText('techspec.docx');
 await expect(page.getByRole('button',{name:'Process next sections · ollama',exact:true})).toBeVisible();
 expect(preflights).toBe(1);expect(uploads).toBe(1);
 expect(await (await page.request.get('/api/projects/'+owner)).json()).toEqual(before);
 await expect(page.getByRole('dialog',{name:'Here’s what will change'})).toHaveCount(0);
});
