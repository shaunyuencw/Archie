import {test,expect} from '@playwright/test';
test('T07 manual edit, route, undo, reopen and three views without provider calls',async({page})=>{
 const calls:string[]=[];page.on('request',r=>{if(r.url().includes('/runs'))calls.push(r.url())});
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 const node=page.locator('.react-flow__node[data-id="vms"]');await expect(node).toBeVisible();await node.click();
 await page.getByLabel('Object name',{exact:true}).fill('Video management renamed');await page.getByLabel('Object name',{exact:true}).press('Tab');
 await expect(node).toContainText('Video management renamed');
 await page.getByLabel('Placement x',{exact:true}).fill('55');await page.getByLabel('Placement x',{exact:true}).press('Tab');
 await expect(page.getByLabel('Placement x',{exact:true})).toHaveValue('55');
 await page.getByRole('button',{name:'SV-1-style',exact:true}).click();await expect(page.locator('.react-flow__node[data-id="vms-system"]')).toContainText('Video management renamed');
 await page.getByRole('button',{name:'SV-2-style',exact:true}).click();await expect(page.locator('.edge-label').first()).toContainText('initiator');
 await page.getByRole('button',{name:'Interfaces',exact:true}).click();await page.getByRole('cell',{name:'video',exact:true}).first().click();
 await page.getByLabel('Line style',{exact:true}).selectOption('straight');await expect(page.getByLabel('Line style',{exact:true})).toHaveValue('straight');
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();await expect(node).toContainText('Video management renamed');
 await page.getByRole('button',{name:'Undo',exact:true}).click();
 await page.getByTitle('Add workstation',{exact:true}).click();await expect(page.getByText('9 components · 4 interfaces · saved locally',{exact:true})).toBeVisible();
 expect(calls).toHaveLength(0);await page.screenshot({path:'../../reports/workbench-m2.png',fullPage:true});
});
