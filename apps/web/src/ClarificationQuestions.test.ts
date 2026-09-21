// @vitest-environment jsdom
import {createElement} from 'react';
import {afterEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import ClarificationQuestions,{clarificationOptions} from './ClarificationQuestions';
import type {Project} from './api';
const decision=(patch:Partial<Project['decisions'][number]>={}):Project['decisions'][number]=>({id:'q1',question:'Who starts the connection?',field:'initiator',target_id:'link',options:['client-id','server-id'],answer:null,state:'unknown',evidence:[],...patch});
afterEach(cleanup);

test('all choices stay visible and canonical component IDs submit only on Save answer',async()=>{
 const onAnswer=vi.fn().mockResolvedValue(undefined);
 render(createElement(ClarificationQuestions,{decisions:[decision()],onAnswer,optionLabels:{'client-id':'Operator tablet','server-id':'Application service'}}));
 expect(screen.queryByRole('combobox')).toBeNull();
 expect(screen.getAllByRole('radio')).toHaveLength(4);
 expect(screen.getByRole('radio',{name:'Operator tablet'})).toBeTruthy();
 fireEvent.click(screen.getByRole('radio',{name:'Application service'}));
 expect(onAnswer).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Save answer'}));
 await waitFor(()=>expect(onAnswer).toHaveBeenCalledWith('q1','server-id'));
});

test('Other accepts an inline answer and Not decided preserves its existing canonical value',async()=>{
 const onAnswer=vi.fn().mockResolvedValue(undefined);
 render(createElement(ClarificationQuestions,{decisions:[decision({options:['push','Other','Not decided','other','not_decided']})],onAnswer}));
 expect(clarificationOptions(['push','push','Other','other','Not decided','not_decided'])).toEqual(['push','Other','Not decided']);
 expect(screen.getAllByRole('radio')).toHaveLength(3);
 fireEvent.click(screen.getByRole('radio',{name:/^Other/}));
 expect((screen.getByRole('button',{name:'Save answer'}) as HTMLButtonElement).disabled).toBe(true);
 fireEvent.change(screen.getByRole('textbox'),{target:{value:'  Ask the operations owner  '}});
 fireEvent.click(screen.getByRole('button',{name:'Save answer'}));
 await waitFor(()=>expect(onAnswer).toHaveBeenCalledWith('q1','Ask the operations owner'));
 await waitFor(()=>expect((screen.getByRole('radio',{name:/^Not decided yet/}) as HTMLInputElement).disabled).toBe(false));
 fireEvent.click(screen.getByRole('radio',{name:/^Not decided yet/}));
 fireEvent.click(screen.getByRole('button',{name:'Save answer'}));
 await waitFor(()=>expect(onAnswer).toHaveBeenCalledWith('q1','Not decided'));
});

test('shows at most three unresolved questions and disables saves while busy',()=>{
 render(createElement(ClarificationQuestions,{decisions:[decision({id:'answered',state:'answered'}),...Array.from({length:4},(_,i)=>decision({id:'q'+i}))],onAnswer:vi.fn(),busy:true}));
 expect(screen.getAllByRole('group')).toHaveLength(3);
 for(const button of screen.getAllByRole('button',{name:'Save answer'}))expect((button as HTMLButtonElement).disabled).toBe(true);
});
