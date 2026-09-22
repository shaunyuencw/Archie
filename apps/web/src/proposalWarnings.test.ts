import {it,expect} from 'vitest';
import type {Project,ChangeSet} from './api';
import {proposalWarnings} from './proposalWarnings';
import fixture from '../../../fixtures/demos/portal/project.json';
const project=fixture as unknown as Project;

it('groups repeated technical warnings into one actionable checklist using draft names',()=>{
 const proposal:ChangeSet={project_id:project.id,base_revision:project.revision,base_views:{},operations:[
  {op:'add',entity:'systems',id:'tmp:sys-c2',value:{name:'Command and Control'}},
  {op:'add',entity:'components',id:'tmp:operator',value:{name:'Operator Client'}},
 ],findings:['tmp:sys-c2: scope kept unknown because no matching scope claim was supplied.',
             'tmp:operator: scope kept unknown because no matching scope claim was supplied.']};
 const warnings=proposalWarnings(project,proposal);
 expect(warnings).toHaveLength(1);
 expect(warnings[0].items).toEqual(['Command and Control','Operator Client']);
 expect(warnings[0].message).toContain('Architecture boundary in the Inspector');
 expect(warnings[0].message).toContain('Not specified');
 expect(JSON.stringify(warnings)).not.toMatch(/tmp:|scope claim/);
});

it('names connection endpoints and retains unknown findings for review',()=>{
 const first=project.components[0],last=project.components[1];
 const proposal:ChangeSet={project_id:project.id,base_revision:project.revision,base_views:{},operations:[{op:'add',entity:'interfaces',id:'tmp:link',value:{source:first.id,target:last.id}}],findings:[
  'tmp:link: port was left unknown because the supplied value was not one valid numeric port. Split the connection or provide one port.',
  'tmp:link: enforcement is not fully specified. Confirm which firewall or other component controls this connection; no extra enforcement component was assumed.',
  'An unusual warning must remain visible.',
 ]};
 const warnings=proposalWarnings(project,proposal);
 expect(warnings).toHaveLength(3);
 expect(warnings[0].items).toEqual([`${first.name} → ${last.name}`]);
 expect(warnings[1].items).toEqual(warnings[0].items);
 expect(warnings[2].message).toBe('An unusual warning must remain visible.');
 expect(JSON.stringify(warnings)).not.toContain('tmp:');
});

it('groups inferred zoning separately and names deployment choices',()=>{
 const proposal:ChangeSet={project_id:project.id,base_revision:project.revision,base_views:{},operations:[
  {op:'add',entity:'zones',id:'tmp:zone',value:{name:'Application zone'}},
  {op:'add',entity:'deployments',id:'tmp:deploy',value:{component_id:project.components[0].id,zone_id:'tmp:zone'}},
 ],findings:['tmp:zone: proposed zoning — Isolate application processing.',
             'tmp:deploy: proposed zoning — Assign the service by its responsibility.']};
 const warnings=proposalWarnings(project,proposal);
 expect(warnings).toHaveLength(1);expect(warnings[0].title).toBe('Review proposed zoning');
 expect(warnings[0].message).toContain('does not configure network security');
 expect(warnings[0].items).toEqual(['Application zone: Isolate application processing.',
  `${project.components[0].name} → Application zone: Assign the service by its responsibility.`]);
 expect(JSON.stringify(warnings)).not.toContain('tmp:');
});
