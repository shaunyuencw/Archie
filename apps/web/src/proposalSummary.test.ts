import {it,expect} from 'vitest';
import type {Project,ChangeSet} from './api';
import {proposalSummary} from './proposalSummary';
import fixture from '../../../fixtures/demos/portal/project.json';
const project=fixture as unknown as Project;
const proposal=(operations:ChangeSet['operations'])=>({operations} as ChangeSet);
it('resolves proposed and accepted references into readable names without inventing transport or quantities',()=>{
 const zone=project.zones[0],host=project.components[0];
 const rows=proposalSummary(project,proposal([
  {op:'add',entity:'components',id:'tmp:new',value:{name:'Reporting service',role:'reporting',form_factor:'virtual'}},
  {op:'add',entity:'deployments',id:'tmp:d',value:{component_id:'tmp:new',zone_id:zone.id,quantity:null,host_component_id:host.id}},
  {op:'add',entity:'interfaces',id:'tmp:i',value:{source:'tmp:new',target:host.id,initiator:null,protocol:null}},
  {op:'add',entity:'claims',id:'claim-internal',value:{}},
 ]));
 expect(rows).toHaveLength(2);
 const text=JSON.stringify(rows);
 expect(text).toContain('Add Reporting service');expect(text).toContain(zone.name);expect(text).toContain('Hosted on '+host.name);
 expect(text).toContain('Instance count is not specified');expect(text).toContain('Protocol not specified');expect(text).toContain('Who starts the session is not decided');
 expect(text).not.toContain('tmp:');expect(text).not.toContain('claim-internal');expect(text).not.toContain('HTTPS');
});
it('shows before and after connection facts and explains component removal consequences',()=>{
 const edge=project.interfaces[0],component=project.components[0];
 const rows=proposalSummary(project,proposal([
  {op:'update',entity:'interfaces',id:edge.id,value:{protocol:'TLS',port:8443}},
  {op:'update',entity:'components',id:component.id,value:{name:'Updated workstation'}},
  {op:'remove',entity:'components',id:component.id,confirmed:true},
 ]));
 expect(rows[0].details.join(' ')).toContain(`${edge.protocol} → TLS`);
 expect(rows[1].title).toBe(`Rename ${component.name} to Updated workstation`);
 expect(rows[2].details.join(' ')).toContain('Connections that reference this component will also be removed');
});
