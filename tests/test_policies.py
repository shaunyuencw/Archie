from pathlib import Path
from apps.api.app.domain.models import Project
from apps.api.app.domain.commands import apply,command
from apps.api.app.policies.engine import evaluate,lookup

def test_T06_checks_independent_of_retrieval():
    p=Project.model_validate_json(Path('fixtures/references/A/project.json').read_text(encoding='utf-8'))
    p=apply(p,command(p,[{'op':'update','entity':'interfaces','id':'administration','value':{'enforcement':[],'target':'analytics'}}]))
    retrieved=lookup('storage',1);assert len(retrieved)==1
    result=evaluate(p);f={x['clause_id']:x for x in result['findings']}
    assert f['DEMO-ADM-01']['result']=='potential_conflict'
    assert f['DEMO-FW-01']['result']=='insufficient_information'
    assert f['DEMO-ZON-01']['result']=='pass'
    assert result['implemented']==8 and sum(x['execution']=='manual_review' for x in result['findings'])==12
