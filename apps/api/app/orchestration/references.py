"""Resolve only unambiguous provider aliases and explain invalid typed references."""
import json

from ..domain.commands import DomainError
from ..providers.contracts import operation_value


ENTITIES=('systems','zones','components','deployments','interfaces','constraints')
REFERENCE_FIELDS={
    'components':{'system_id':'systems','audit_destination':'components','storage_destination':'components'},
    'deployments':{'component_id':'components','zone_id':'zones','host_component_id':'components'},
    'interfaces':{'source':'components','target':'components','initiator':'components','enforcement':'components'},
}


class ProposalReferenceError(DomainError):
    def __init__(self,entity,ident,field,value,expected,actual=None):
        self.operation_ids={ident}
        label={'interfaces':'Connection','deployments':'Deployment','components':'Component','claims':'Source claim'}.get(entity,'Record')
        reason=f'“{str(value)[:160]}” identifies a {actual[:-1]}' if actual else f'“{str(value)[:160]}” has no unambiguous matching {expected[:-1]}'
        detail=' For a system-level connection, explicitly propose a logical boundary component with source evidence; do not choose an internal service arbitrarily.' if actual=='systems' and expected=='components' else ''
        if field=='enforcement':detail+=' The enforcement reference does not match a component.'
        super().__init__('provider_output',f'{label} “{ident[:160]}”, {field}: {reason}; this field needs a {expected[:-1]} reference.{detail} Your current design was not changed.')
        Exception.__init__(self,self.message)


def proposed_records(project,envelopes,unreadable=None):
    records={entity:{record.id:record.model_dump(exclude={'evidence'}) for record in getattr(project,entity)} for entity in ENTITIES}
    for envelope in envelopes:
        for op in envelope.operations:
            try:
                value=operation_value(op)
            except DomainError:
                if unreadable is not None:
                    unreadable.append({'entity':op.entity,'id':op.id})
                    continue
                raise
            group=records[op.entity]
            if op.op=='remove':group.pop(op.id,None)
            else:group[op.id]={**group.get(op.id,{}),**value,'id':op.id}
    return records


def reference_catalog(project,envelopes=(),*,include_zoning=False):
    """Compact typed symbols for every record; budget checks bound transmission."""
    unreadable=[]
    records=proposed_records(project,envelopes,unreadable)
    fields=('name','role','system_id','component_id','zone_id','source','target','key')
    if include_zoning:fields+=('scope','value')
    catalog={entity:[{'id':ident,**{key:record[key] for key in fields if key in record}}
                     for ident,record in group.items()] for entity,group in records.items() if group}
    if unreadable:catalog['unreadable_operations']=unreadable
    return catalog


def normalize_references(project,envelope):
    """Return a copy. Never substitute a system for a component or invent records."""
    result=envelope.model_copy(deep=True)
    records=proposed_records(project,[result])
    all_ids={ident:entity for entity,group in records.items() for ident in group}
    # Source/decision IDs may also be legal evidence targets.
    for entity in ('sources','claims','decisions'):
        all_ids.update({record.id:entity for record in getattr(project,entity)})
    claim_ids={**all_ids,**{record.id:entity for entity in ENTITIES for record in getattr(project,entity)}}

    def key(value):return value.removeprefix('tmp:').casefold()

    def resolve(value,expected,entity,ident,field,allow_none=True):
        if value is None and allow_none:return None
        if not isinstance(value,str):return value  # The canonical field validator supplies its type error.
        allowed=claim_ids if expected=='records' else records[expected]
        if value in allowed:return value
        # An exact ID of the wrong type must never fall through to name matching.
        if value in all_ids:raise ProposalReferenceError(entity,ident,field,value,expected,all_ids[value])
        symbols=claim_ids if expected=='records' else all_ids
        aliases={candidate for candidate in symbols if key(candidate)==key(value)}
        if len(aliases)==1:
            candidate=next(iter(aliases))
            if candidate in allowed:return candidate
            raise ProposalReferenceError(entity,ident,field,value,expected,symbols[candidate])
        if aliases:raise ProposalReferenceError(entity,ident,field,value,expected)
        candidates=({candidate for candidate,record in records[expected].items()
                     if isinstance(record.get('name'),str) and record['name'].casefold()==value.casefold()} if expected!='records' else set())
        if len(candidates)==1:return next(iter(candidates))
        raise ProposalReferenceError(entity,ident,field,value,expected)

    for op in result.operations:
        if op.op=='remove':continue
        value=operation_value(op)
        for field,expected in REFERENCE_FIELDS.get(op.entity,{}).items():
            if field not in value:continue
            if field=='enforcement':
                # Existing enforcement normalization handles unknown values and malformed lists.
                items=value[field] if isinstance(value[field],list) else [value[field]]
                unknown={'','-','n/a','na','none','not decided','not specified','null','unknown','unspecified'}
                value[field]=[item if item is None or (isinstance(item,str) and item not in records['components'] and item.strip().lower() in unknown)
                              else resolve(item,expected,op.entity,op.id,field) for item in items]
            else:
                value[field]=resolve(value[field],expected,op.entity,op.id,field)
        if op.entity=='interfaces' and value.get('initiator') is not None:
            full={**records['interfaces'].get(op.id,{}),**value}
            endpoints=tuple(resolve(full.get(field),'components',op.entity,op.id,field) for field in ('source','target'))
            if value['initiator'] not in endpoints:
                raise ProposalReferenceError(op.entity,op.id,'initiator',value['initiator'],'connection endpoints')
        op.value_json=json.dumps(value,separators=(',',':'))
    for claim in result.claims:
        claim.target_id=resolve(claim.target_id,'records','claims',claim.target_id,'target_id',allow_none=False)
    return result
