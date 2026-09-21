import {test,expect} from 'vitest';
import {change} from './api';
test('manual command carries all revisions without a provider request',()=>{
 const c=change({id:'p',revision:7,views:{logical:{revision:2},sv1:{revision:1},sv2:{revision:0}}} as any,[{op:'placement',id:'a',value:{x:45}}]);
 expect(c.base_views).toEqual({logical:2,sv1:1,sv2:0});expect(c.base_revision).toBe(7);expect(c.origin).toBe('manual');
});
