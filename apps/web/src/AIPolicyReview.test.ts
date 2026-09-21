// @vitest-environment jsdom
import {createElement} from 'react';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {api,type Project} from './api';
import AIPolicyReview from './AIPolicyReview';
vi.mock('./api',()=>({api:vi.fn()}));
const project={id:'project1',name:'Portal',revision:3,policy_ids:['ARCH-SEG-01'],components:[],zones:[],systems:[],sources:[]} as unknown as Project;
const result={id:'review1',revision:3,current_revision:3,stale:false,provider:'mock',model:'deterministic-policy-demo',created_at:'2026-09-21',mode:'deterministic_demo',summary:'No AI model was called.',assessments:[],warnings:[],coverage:{components:[0,0]},cost_usd:0,cached:false};
afterEach(cleanup);beforeEach(()=>vi.mocked(api).mockReset());

test('reads saved reviews without invoking AI and requires an explicit review click',async()=>{
 vi.mocked(api).mockImplementation(async(_path,body)=>body?result:{review:null});
 const complete=vi.fn();render(createElement(AIPolicyReview,{project,provider:'mock',onComplete:complete}));
 await waitFor(()=>expect((screen.getByRole('button',{name:'Try review format · free demo'}) as HTMLButtonElement).disabled).toBe(false));
 expect(api).toHaveBeenCalledTimes(1);expect(api).toHaveBeenCalledWith('/projects/project1/policy-review?provider=mock');
 fireEvent.click(screen.getByRole('button',{name:'Try review format · free demo'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/projects/project1/policy-review',expect.objectContaining({base_revision:3,provider:'mock',request_id:expect.any(String)})));
 await waitFor(()=>expect(complete).toHaveBeenCalledTimes(1));
 expect(screen.getByText('No AI model was called.')).toBeTruthy();
});

test('labels saved advice stale after a semantic edit without automatically rerunning it',async()=>{
 vi.mocked(api).mockResolvedValue({review:{...result,revision:2,stale:true}});
 render(createElement(AIPolicyReview,{project,provider:'openai',budgetUsd:.1}));
 await waitFor(()=>expect(screen.getByText(/This review is out of date/)).toBeTruthy());
 expect(api).toHaveBeenCalledTimes(1);
 expect(screen.getByText(/up to \$0.10 per action/)).toBeTruthy();
});
