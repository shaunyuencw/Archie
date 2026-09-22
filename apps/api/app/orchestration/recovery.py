"""Keep usable provider proposals without weakening the canonical model."""
import json

from ..domain.commands import DomainError
from ..providers.contracts import Envelope,WireOperation,operation_value

STOP_CODES={'cancelled','stale_revision','project_trashed','not_found','job_interrupted'}


def recover_proposal(project,source,envelope,*,source_alias='S1',evidence_sources=(),warnings=()):
    from .live import proposal_from_envelope
    working=envelope.model_copy(deep=True)
    notes=list(warnings)
    operations=[];added={}
    for op in working.operations:
        try:value=operation_value(op)
        except DomainError:
            notes.append(f'Omitted {op.id}: its record data could not be read.');continue
        if op.op=='add' and op.id in added:
            if added[op.id]!=(op.entity,value):
                notes.append(f'Omitted conflicting duplicate {op.id}; retained its first definition.')
            continue
        if op.op=='add':added[op.id]=(op.entity,value)
        operations.append(op)
    working.operations=operations;working.tool=None
    # Every unsuccessful pass removes a record/claim. No paid repair loop and
    # no unbounded retry: accepted projects still pass the canonical validator.
    while True:
        if not project.components and not any(op.entity=='components' and op.op=='add' for op in working.operations):
            working.operations.append(WireOperation(op='add',entity='components',id='tmp:unverified-outline',
                value_json=json.dumps({'name':'Unverified system outline','role':'system boundary','asset_id':'system-boundary','scope':'unknown','status':'proposed'}),
                proposal_reason='Placeholder only: no usable component description was returned. Replace this outline after reviewing the source.'))
            notes.append('No usable components were returned. This draft contains an explicitly unverified system outline, not an extracted architecture.')
        try:
            change=proposal_from_envelope(project,source,working,source_alias=source_alias,evidence_sources=evidence_sources,allow_unverified=True)
            change.findings=list(dict.fromkeys(notes+change.findings))
            if notes:change.findings.insert(0,'Partial draft: usable design records were retained. Review the unverified details and omitted items below.')
            return change
        except (DomainError,ValueError) as error:
            if isinstance(error,DomainError) and error.code in STOP_CODES:raise
            ids=getattr(error,'operation_ids',set())
            # A dangling claim must not cause an unrelated valid node to go.
            claim_only=ids-{op.id for op in working.operations}
            if claim_only and any(c.target_id in claim_only for c in working.claims):
                working.claims=[c for c in working.claims if c.target_id not in claim_only]
                notes.append('Omitted a citation whose target could not be resolved.');continue
            bad=[op for op in working.operations if op.id in ids]
            if not bad and working.operations:bad=[working.operations[-1]]
            if not bad:raise
            if any(op.id=='tmp:unverified-outline' for op in bad):raise
            removed={op.id for op in bad}
            detail=getattr(error,'message',str(error)).replace(' Your current design was not changed.','')
            notes.append(f'Omitted {", ".join(sorted(removed))}: {detail}')
            working.operations=[op for op in working.operations if op.id not in removed]
            working.claims=[c for c in working.claims if c.target_id not in removed]


def recover_document(project,source,batches,warnings=()):
    from .live import source_excerpt
    combined=Envelope(operations=[],claims=[],tool=None,message='Review the partial draft')
    notes=list(warnings)
    for batch in batches:
        envelope=batch['envelope']
        combined.operations.extend(envelope.operations)
        if combined.project_name is None:combined.project_name=envelope.project_name
        supplied=source.model_copy(update={'passages':batch['evidence_passages']})
        for claim in envelope.claims:
            try:
                if claim.source_id not in ('S1',source.id):raise ValueError('Source was not supplied')
                source_excerpt(supplied,claim)
                combined.claims.append(claim)
            except (DomainError,ValueError):
                notes.append(f'{claim.target_id}: citation could not be verified in its supplied section; retained only as an unverified proposal.')
    return recover_proposal(project,source,combined,warnings=notes)
