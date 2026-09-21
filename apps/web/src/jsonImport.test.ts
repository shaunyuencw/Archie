import {expect,test} from 'vitest';
import {parseImport} from './jsonImport';
import access from '../../../fixtures/demos/building-access/followups.json';
test('bundled follow-up pack loads as selectable prompts rather than a Project',()=>{
 const result=parseImport(JSON.stringify(access));
 expect(result.kind).toBe('prompts');
 if(result.kind==='prompts'){expect(result.pack.scenario).toBe('Building access event system');expect(result.pack.prompts).toHaveLength(3);expect(result.pack.prompts[1].prompt).toContain('push delivery');}
});
test('project imports remain distinct and malformed packs have readable errors',()=>{
 expect(parseImport('{"components":[],"interfaces":[]}').kind).toBe('project');
 for(const input of ['not json','[]','{"scenario":"x","prompts":[{}]}','{"random":true}'])expect(()=>parseImport(input)).toThrow();
});
