import {test,expect} from '@playwright/test';
test('ARCHIE branding and assistant mascot render with editable equipment canvas',async({page})=>{
 await page.goto('/');await expect(page.getByAltText('ARCHIE').first()).toBeVisible();
 await expect(page.getByAltText('Archie, your friendly robot architecture assistant')).toBeVisible();
 await page.getByText('Legacy examples',{exact:true}).click();await page.getByRole('button',{name:'Load demo A',exact:true}).click();await expect(page.locator('.react-flow__node[data-id="vms"]')).toBeVisible();
 await expect.poll(()=>page.locator('.arch-node img').evaluateAll(images=>images.every(image=>(image as HTMLImageElement).complete&&(image as HTMLImageElement).naturalWidth>0))).toBe(true);
 await page.locator('.assistant').evaluate(e=>{e.scrollTop=0});
 await page.screenshot({path:'../../reports/archie-workbench.png',fullPage:true});
});
