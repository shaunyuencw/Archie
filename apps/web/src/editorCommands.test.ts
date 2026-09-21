import {describe,it,expect} from 'vitest';
import {deleteOperations,pasteOperations} from './editorCommands';
import type {Project} from './api';
import fixture from '../../../fixtures/references/A/project.json';
const project=fixture as unknown as Project;
describe('selection transactions',()=>{
 it('duplicates a zone and its contained components with internal references remapped and evidence cleared',()=>{
  const zone=project.deployments.find(d=>d.component_id==='management')!.zone_id!;
  const result=pasteOperations({project,ids:[zone],view:'logical'},project,'logical');
  const adds=result.operations.filter(o=>o.op==='add');
  const zoneCopy=adds.find(o=>o.entity==='zones')!;
  const members=project.deployments.filter(d=>d.zone_id===zone);
  expect(adds.filter(o=>o.entity==='components')).toHaveLength(members.length);
  expect(adds.filter(o=>o.entity==='deployments').every(o=>o.value!.zone_id===zoneCopy.id)).toBe(true);
  expect(adds.filter(o=>o.entity==='components').every(o=>o.value!.status==='proposed'&&(o.value!.evidence as unknown[]).length===0)).toBe(true);
  expect(adds.filter(o=>o.entity==='deployments').every(o=>o.value!.quantity===null)).toBe(true);
 });
 it('avoids duplicate remove operations for interfaces cascaded by component deletion',()=>{
  const edge=project.interfaces.find(e=>e.source==='vms'||e.target==='vms')!;
  const ops=deleteOperations(project,['vms',edge.id]);
  expect(ops).toHaveLength(1);expect(ops[0].id).toBe('vms');expect(ops[0].confirmed).toBe(true);
 });
 it('rejects cross-project references and aggregate view duplication',()=>{
  expect(()=>pasteOperations({project,ids:['vms'],view:'logical'},{...project,id:'different'},'logical')).toThrow('current project');
  expect(()=>pasteOperations({project,ids:['vms'],view:'sv1'},project,'logical')).toThrow('Logical');
 });
});
