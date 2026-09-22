"""Best-effort drafts retain usable records without claiming unverified facts."""
import json

import pytest

from apps.api.app.domain.commands import apply,DomainError
from apps.api.app.domain.models import Component,Project,Source,Passage
from apps.api.app.orchestration.recovery import recover_proposal
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.providers.config import Settings
from apps.api.app.providers.contracts import Envelope,ProviderResult,Usage
from apps.api.app.storage.store import Store


def source():
    return Source(id='spec',name='Synthetic specification',kind='document',sha256='spec',canonical_id='spec',
                  passages=[Passage(locator='page/1',text='A client communicates with an application.')])


def operation(ident,value,entity='components',kind='add',reason=None):
    return dict(op=kind,entity=entity,id=ident,value_json=json.dumps(value),proposal_reason=reason)


def envelope(operations,claims=()):
    return Envelope(operations=operations,claims=list(claims),tool=None,message='Review')


def claim(target,quote=None,locator='page/1'):
    return dict(source_id='S1',locator=locator,excerpt=quote or source().passages[0].text,
                target_id=target,field='record',value_json='null')


def test_missing_direct_claim_retains_complete_architecture_as_unverified():
    project=Project()
    output=envelope([operation('a',{'name':'Client','role':'client'},reason='Functional interpretation'),
                     operation('b',{'name':'Application','role':'application'}),
                     operation('ab',{'source':'a','target':'b'},'interfaces')])
    draft=recover_proposal(project,source(),output)
    accepted=apply(project,draft)
    assert len(accepted.components)==2 and len(accepted.interfaces)==1
    assert all(c.source_kind=='assistant_proposal' and c.review=='unreviewed' for c in accepted.claims)
    assert any('Unverified' in finding for finding in draft.findings)
    assert all(c.excerpt in next(s for s in accepted.sources if s.id==c.source_id).passages[0].text or
               any(c.excerpt in p.text for p in next(s for s in accepted.sources if s.id==c.source_id).passages)
               for c in accepted.claims)


@pytest.mark.parametrize('bad',[
    operation('bad',{'name':'Bad','role':{'invalid':'type'}}),
    dict(op='add',entity='components',id='bad',value_json='{"name":'),
])
def test_one_bad_record_and_its_dependent_edge_do_not_discard_good_records(bad):
    project=Project();output=envelope([operation('good',{'name':'Client','role':'client'}),bad,
                                      operation('edge',{'source':'good','target':'bad'},'interfaces')],[claim('good')])
    draft=recover_proposal(project,source(),output);accepted=apply(project,draft)
    assert [c.id for c in accepted.components]==['good'] and not accepted.interfaces
    assert any('Omitted bad' in finding for finding in draft.findings)
    assert any('Omitted edge' in finding for finding in draft.findings)
    assert any(c.target_id=='good' and c.review=='confirmed' for c in accepted.claims)


@pytest.mark.parametrize('bad_claim',[claim('a','Fabricated words'),claim('a',locator='page/99'),claim('missing')])
def test_unverifiable_claim_is_never_saved_as_verified_evidence(bad_claim):
    project=Project();output=envelope([operation('a',{'name':'Client','role':'client'})],[bad_claim])
    accepted=apply(project,recover_proposal(project,source(),output))
    assert len(accepted.components)==1
    assert not any(c.review=='confirmed' for c in accepted.claims)
    assert all(c.source_kind=='assistant_proposal' for c in accepted.claims)


def test_invalid_update_keeps_existing_architecture():
    project=Project(components=[Component(id='a',name='Existing',role='client')])
    draft=recover_proposal(project,source(),envelope([operation('a',{'role':[]},kind='update')]))
    accepted=apply(project,draft)
    assert accepted.components==project.components
    assert any('Omitted a' in finding for finding in draft.findings)


def test_no_usable_output_returns_an_explicit_outline_not_verified_extraction():
    project=Project();draft=recover_proposal(project,source(),envelope([]))
    accepted=apply(project,draft)
    assert len(accepted.components)==1 and accepted.components[0].name=='Unverified system outline'
    assert all(c.review=='unreviewed' for c in accepted.claims)
    assert any('not an extracted architecture' in finding for finding in draft.findings)


def test_failed_later_batch_returns_first_batch_and_honest_coverage(tmp_path,monkeypatch):
    spec=source();spec.passages[0].text+=' '+'Synthetic detail. '*220
    spec.passages.append(Passage(locator='page/2',text='Remaining details. '*220))
    monkeypatch.setattr('apps.api.app.orchestration.documents.parse',lambda *args:spec)
    class Adapter:
        name='openai';model='gpt-5.4-mini';calls=0
        def generate_structured(self,*args):
            self.calls+=1
            if self.calls==2:raise DomainError('provider_timeout','Generation timed out')
            return ProviderResult(model=self.model,finish_status='completed',usage=Usage(),
                content=envelope([operation('a',{'name':'Client','role':'client'})],[claim('a')]))
    adapter=Adapter();store=Store(tmp_path/'db');project=store.create(Project())
    result=ingest_live(store,project.id,b'synthetic','spec.pdf','openai',Settings(allow_cloud=True,max_input=50000,max_calls=3),adapter)
    assert adapter.calls==2 and store.get(project.id)==project
    accepted=store.commit(result['proposal'])
    assert [c.id for c in accepted.components]==['a']
    assert accepted.sources[0].processed==['page/1'] and accepted.sources[0].unprocessed==['page/2']
    assert any('timed out' in finding for finding in result['proposal'].findings)
