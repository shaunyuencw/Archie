import {test,expect} from '@playwright/test';
test('T08 preview reject accept and undo preserve manual placement',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Load demo A',exact:true}).click();
 await page.locator('.react-flow__node[data-id="vms"]').click();
 await page.getByLabel('Placement x',{exact:true}).fill('77');await page.getByLabel('Placement x',{exact:true}).press('Tab');
 await page.getByLabel('Architecture prompt').fill('add one configuration workstation; keep the layout.');await page.getByRole('button',{name:'Preview proposed changes',exact:true}).click();
 await expect(page.getByRole('button',{name:'Accept changes',exact:true})).toBeVisible();await page.getByRole('button',{name:'Accept changes',exact:true}).click();
 await expect(page.getByText('9 components · 4 interfaces · saved locally',{exact:true})).toBeVisible();await expect(page.getByLabel('Placement x',{exact:true})).toHaveValue('77');
 await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(page.getByText('8 components · 4 interfaces · saved locally',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Findings',exact:true}).click();await expect(page.locator('.finding')).toHaveCount(20);
});
