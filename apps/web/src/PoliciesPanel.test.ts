// @vitest-environment jsdom
import {createElement} from 'react';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {api,type Project} from './api';
import PoliciesPanel from './PoliciesPanel';
vi.mock('./api',()=>({api:vi.fn()}));
const project={id:'p',name:'Draft',revision:0,policy_ids:[]} as unknown as Project;
const clause=(id:string,title:string,category:string)=>({id,title,category,text:title+' review requirement.',version:'1.0',pack:'Architecture essentials',implementation:'manual_review',applicability:['Demo systems'],exceptions:'Review with owner.',tags:[category]});
const library={clauses:[clause('cloud','Review AWS boundaries','cloud-hybrid'),clause('backup','Review restore evidence','data-recovery')],categories:[{id:'cloud-hybrid',name:'Cloud & hybrid connections',description:'Cloud boundary review.'},{id:'data-recovery',name:'Data, secrets & backups',description:'Stored data review.'}],legacy_ids:[],presets:[]};
afterEach(cleanup);beforeEach(()=>vi.mocked(api).mockReset());

test('category browsing and global search preserve explicit project selection',async()=>{
 vi.mocked(api).mockResolvedValue(library);const execute=vi.fn().mockResolvedValue(undefined);
 render(createElement(PoliciesPanel,{project,execute}));
 await waitFor(()=>expect(screen.getByLabelText('Apply cloud')).toBeTruthy());
 fireEvent.click(screen.getByLabelText('Apply cloud'));
 fireEvent.click(screen.getByRole('button',{name:/^Data, secrets & backups/}));
 expect(screen.queryByLabelText('Apply cloud')).toBeNull();
 expect(screen.getByLabelText('Apply backup')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:/^All categories/}));
 expect((screen.getByLabelText('Apply cloud') as HTMLInputElement).checked).toBe(true);
 fireEvent.change(screen.getByLabelText('Search policy library'),{target:{value:'restore'}});
 expect(screen.queryByLabelText('Apply cloud')).toBeNull();
 expect(screen.getByLabelText('Apply backup')).toBeTruthy();
 expect(execute).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Apply to project'}));
 await waitFor(()=>expect(execute).toHaveBeenCalledWith([{op:'policy_selection',value:{policy_ids:['cloud']}}]));
});
