import json
from uuid import uuid5,NAMESPACE_URL
from .models import Project, ChangeSet, uid, now

class DomainError(Exception):
    def __init__(self,code,message,status=422): self.code=code; self.message=message; self.status=status

def apply(project:Project,change:ChangeSet)->Project:
    if change.project_id!=project.id: raise DomainError('invalid_input','Project mismatch')
    if change.base_revision!=project.revision or change.base_views!={k:v.revision for k,v in project.views.items()}:
        raise DomainError('stale_revision','The project changed. Review a fresh proposal.',409)
    data=project.model_dump(); semantic=False; touched=set()
    # Allocate temporary IDs once across the whole transaction, including references.
    mapping={o.id:str(uuid5(NAMESPACE_URL,change.id+':'+o.id)) for o in change.operations if o.op=='add' and o.id.startswith('tmp:')}
    def resolve(v):
        if isinstance(v,str): return mapping.get(v,v)
        if isinstance(v,list): return [resolve(x) for x in v]
        if isinstance(v,dict): return {k:resolve(x) for k,x in v.items()}
        return v
    data=resolve(data)
    for operation in change.operations:
        o=operation.model_copy(update={'id':mapping.get(operation.id,operation.id),'value':resolve(operation.value)})
        if o.op in ('placement','route'):
            key='placements' if o.op=='placement' else 'routes'
            allowed={x['id'] for x in data['components']+data['zones']+data['systems']+data['interfaces']}
            if o.id not in allowed and not o.id.startswith('aggregate:'): raise DomainError('invalid_input','Unknown presentation object')
            data['views'][o.view][key][o.id]=dict(data['views'][o.view][key].get(o.id,{}),**o.value)
            touched.add(o.view); continue
        semantic=True
        if o.op=='notes': data['notes']=str(o.value.get('text','')); continue
        if not o.entity: raise DomainError('invalid_input','Entity is required')
        records=data[o.entity]; existing=next((x for x in records if x['id']==o.id),None)
        if o.op=='add':
            if existing: raise DomainError('invalid_input','ID already exists')
            records.append(dict(o.value,id=o.id or uid()))
        elif not existing: raise DomainError('invalid_input','Object no longer exists')
        elif o.op=='update':
            if 'id' in o.value: raise DomainError('invalid_input','IDs cannot be edited')
            existing.update(o.value)
        elif o.op=='remove':
            refs=[x for x in data['interfaces'] if o.id in [x['source'],x['target']]+x.get('enforcement',[])]
            if refs and not o.confirmed: raise DomainError('confirmation_required',f'Deleting this object also removes {len(refs)} referenced interfaces.',409)
            if o.entity=='components':
                data['interfaces']=[x for x in data['interfaces'] if x not in refs]
                data['deployments']=[x for x in data['deployments'] if x['component_id']!=o.id]
                for x in data['components']:
                    for field in ['audit_destination','storage_destination']:
                        if x.get(field)==o.id: x[field]=None
            if o.entity=='zones':
                assigned=[x for x in data['deployments'] if x['zone_id']==o.id]
                if assigned and not o.confirmed: raise DomainError('confirmation_required','This zone has assigned deployments.',409)
                for x in assigned: x['zone_id']=None
            records.remove(existing)
            removed={o.id}|{x['id'] for x in refs}
            for x in data['claims']:
                if x['target_id'] in removed: x['review']='rejected'
            data['decisions']=[x for x in data['decisions'] if x['target_id'] not in removed]
            for view in data['views'].values():
                for key in ['placements','routes','mappings']:
                    for ident in removed: view[key].pop(ident,None)
    data['revision']+=int(semantic)
    for k in touched: data['views'][k]['revision']+=1
    data['updated_at']=now()
    try:
        from .views import initialise_views
        return initialise_views(Project.model_validate(data))
    except ValueError as e: raise DomainError('invalid_input',str(e)) from e

def command(project,operations,**kwargs):
    return ChangeSet(project_id=project.id,base_revision=project.revision,base_views={k:v.revision for k,v in project.views.items()},operations=operations,**kwargs)
