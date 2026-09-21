import {test,expect} from '@playwright/test';
test('T02 T04 upload review, sources and saved answer',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'New',exact:true}).click();
 await expect(page.getByLabel('Upload document')).toBeEnabled();
 await page.getByLabel('Upload document').setInputFiles('../../fixtures/projects/B/spec.docx');
 await expect(page.getByRole('button',{name:'Accept changes',exact:true})).toBeVisible();
 await expect(page.getByText('0 components · 0 interfaces · saved locally',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Accept changes',exact:true}).click();
 await expect(page.getByText('8 components · 4 interfaces · saved locally',{exact:true})).toBeVisible();
 await expect(page.locator('.claim').first()).toContainText('confirmed');
 const question=page.locator('.clarification-question').first();await expect(question).toBeVisible();
 await expect(question.getByRole('radio',{name:/^Other/})).toBeVisible();
 await expect(question.getByRole('radio',{name:/^Not decided yet/})).toBeVisible();
 await page.screenshot({path:'../../reports/archie-clarification-questions.png',fullPage:true});
 await question.getByRole('radio').first().check();
 const saved=page.waitForResponse(response=>response.url().endsWith('/answers')&&response.request().method()==='POST');
 await question.getByRole('button',{name:'Save answer',exact:true}).click();expect((await saved).ok()).toBe(true);
 await page.getByRole('button',{name:'Save / reopen',exact:true}).click();await expect(page.getByRole('alert')).toHaveCount(0);
});
