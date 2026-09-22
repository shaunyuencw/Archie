// @vitest-environment jsdom
import {createElement} from 'react';
import {afterEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import PolicyRecommendations,{type PolicySuggestion} from './PolicyRecommendations';
const items:PolicySuggestion[]=[{policy_id:'ARCH-BAK-01',title:'Design backups that can be restored',reason:'The draft includes a database.',category:'data-recovery',implementation:'manual_review',affected_ids:['db'],origin:'rules'}];
afterEach(cleanup);

test('suggestions require an explicit selection and apply action',async()=>{
 const add=vi.fn().mockResolvedValue(undefined);
 render(createElement(PolicyRecommendations,{items,onAdd:add}));
 expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
 expect((screen.getByRole('button',{name:'Add selected policies'}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByText(/built-in rules/)).toBeTruthy();
 fireEvent.click(screen.getByRole('checkbox'));
 expect(add).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Add selected policies'}));
 await waitFor(()=>expect(add).toHaveBeenCalledWith(['ARCH-BAK-01']));
});

test('proposal mode only updates the review checklist until the parent accepts',()=>{
 const change=vi.fn(),add=vi.fn();
 render(createElement(PolicyRecommendations,{items,onAdd:add,selection:[],onSelectionChange:change,hideApply:true}));
 expect(screen.queryByRole('button',{name:'Add selected policies'})).toBeNull();
 fireEvent.click(screen.getByRole('checkbox'));
 expect(change).toHaveBeenCalledWith(['ARCH-BAK-01']);
 expect(add).not.toHaveBeenCalled();
 expect(screen.getByText(/added when you accept this draft/)).toBeTruthy();
});

test('select all and clear all change only the checklist, with individual opt-out and busy protection',()=>{
 const second={...items[0],policy_id:'ARCH-TLS-01',title:'Protect connections'};
 const add=vi.fn();
 const {rerender}=render(createElement(PolicyRecommendations,{items:[...items,second],onAdd:add}));
 fireEvent.click(screen.getByRole('button',{name:'Select all'}));
 expect(screen.getAllByRole('checkbox').every(n=>(n as HTMLInputElement).checked)).toBe(true);
 expect(add).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('checkbox',{name:'Suggest ARCH-BAK-01'}));
 expect(screen.getByText('1 of 2 selected')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Clear all'}));
 expect(screen.getAllByRole('checkbox').every(n=>!(n as HTMLInputElement).checked)).toBe(true);
 rerender(createElement(PolicyRecommendations,{items:[...items,second],onAdd:add,busy:true}));
 expect((screen.getByRole('button',{name:'Select all'}) as HTMLButtonElement).disabled).toBe(true);
});

test('select all in draft review reports every suggested policy without accepting or applying',()=>{
 const change=vi.fn(),add=vi.fn();
 const second={...items[0],policy_id:'ARCH-TLS-01',title:'Protect connections'};
 render(createElement(PolicyRecommendations,{items:[...items,second],selection:[],onSelectionChange:change,onAdd:add,hideApply:true}));
 fireEvent.click(screen.getByRole('button',{name:'Select all'}));
 expect(change).toHaveBeenCalledWith(['ARCH-BAK-01','ARCH-TLS-01']);
 expect(add).not.toHaveBeenCalled();
});
