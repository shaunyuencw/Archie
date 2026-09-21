"""Explicit, bounded real-provider journeys. Never run from the offline gate.

The harness uses the same proposal/review, clarification, command and projection
services as the application. Its automatic accept/answers are synthetic test actions.
Each invocation saves a new report; historical provider evidence is retained.
"""
import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apps.api.app.domain.commands import command
from apps.api.app.domain.models import ChangeSet, Operation, Project, uid
from apps.api.app.domain.views import narrative, view_graph
from apps.api.app.exports.service import export
from apps.api.app.orchestration.documents import ingest_live
from apps.api.app.orchestration.live import assisted_run
from apps.api.app.orchestration.live import proposal_from_envelope
from apps.api.app.orchestration.service import answer
from apps.api.app.policies.engine import evaluate, lookup
from apps.api.app.providers.adapters import OllamaAdapter
from apps.api.app.providers.budget import BudgetedProvider, usage_summary
from apps.api.app.providers.config import Settings
from apps.api.app.storage.store import Store
from apps.api.app.ingest.parser import parse


class RunRequest(ChangeSet):
    prompt: str
    provider: str


class AnswerRequest(ChangeSet):
    decision_id: str
    answer: str


PROMPT = (
    'SYNTHETIC demonstration. Create a draft with two applications: Event manager '
    '(role event management) and External console (role external command system, '
    'external scope). Event manager sends events to External console. Event '
    'delivery method, session initiator, protocol, port, deployment zones and '
    'equipment quantities are not decided. Preserve these unknowns.'
)


def request(p, prompt, provider, limit):
    base = command(p, [Operation(op='notes', value={'text': p.notes})], request_id=limit['id']+'-'+uid())
    return RunRequest(**base.model_dump(), prompt=prompt, provider=provider)


def accept_result(store, p, result):
    assert store.get(p.id) == p, 'Provider changed accepted state before review'
    proposal = result['proposal']
    if isinstance(proposal, dict):
        proposal = store.change(proposal['id'])
    return store.commit(proposal)


def clarify(store, p):
    before = usage_summary(store, p.id)['calls']
    d = next(d for d in p.decisions if d.state == 'unknown' and d.options)
    chosen = 'push' if 'push' in d.options else d.options[0]
    base = command(p, [Operation(op='notes', value={'text': p.notes})])
    p = answer(store, p.id, AnswerRequest(**base.model_dump(), decision_id=d.id, answer=chosen))
    assert next(x for x in p.decisions if x.id == d.id).answer == chosen
    assert usage_summary(store, p.id)['calls'] == before
    return p, {'question': d.question, 'options': d.options, 'answer': chosen, 'model_calls': 0}


def derived_checks(p):
    graphs = {kind: view_graph(p, kind) for kind in p.views}
    text = narrative(p)
    csv, _ = export(p, 'csv')
    assert all(g['semantic_revision'] == p.revision for g in graphs.values())
    assert all(c.name in text for c in p.components)
    assert all(i.id in csv.decode() for i in p.interfaces)
    return {'revision': p.revision, 'components': len(p.components), 'interfaces': len(p.interfaces),
            'source_claims': len(p.claims), 'three_views': True, 'narrative_and_interfaces': True}


def flow_a(store, provider, settings, limit, report_dir):
    p = store.create(Project(name=f'ARCHIE {provider} live prompt journey'))
    started = time.monotonic()
    result = assisted_run(store, p.id, request(p, PROMPT, provider, limit), settings,
                          live_run=limit, deadline=time.monotonic()+180)
    repairs = result['repairs']
    p = accept_result(store, p, result)
    assert len(p.components) == 2 and len(p.interfaces) == 1
    assert p.interfaces[0].initiator is None and p.interfaces[0].delivery is None
    assert p.interfaces[0].protocol is None and p.interfaces[0].port is None
    assert 1 <= len(p.decisions) <= 3
    p, clarification = clarify(store, p)
    manager = next(c for c in p.components if c.name == 'Event manager')
    calls_before = usage_summary(store, p.id)['calls']
    p = store.commit(command(p, [Operation(op='placement', id=manager.id, value={'x': 123, 'y': 287}),
                                Operation(op='route', id=p.interfaces[0].id,
                                          value={'style': 'orthogonal', 'points': [{'x': 350, 'y': 322}], 'locked': True})]))
    before = p.views['logical'].model_dump()
    assert usage_summary(store, p.id)['calls'] == calls_before
    result = assisted_run(store, p.id, request(p, 'Rename External console to Review console. Keep every other fact unchanged.', provider, limit),
                          settings, live_run=limit, deadline=time.monotonic()+180)
    repairs += result['repairs']
    p = accept_result(store, p, result)
    assert any(c.name == 'Review console' for c in p.components)
    assert p.views['logical'].model_dump() == before, 'Prompt edit changed manual presentation'
    checks = derived_checks(p)
    assert 'Review console' in narrative(p)
    (report_dir/'flow-a-project.json').write_text(p.model_dump_json(indent=2))
    return {'passed': True, 'project_id': p.id, 'clarification': clarification,
            'bounded_schema_repairs': repairs,
            'manual_position_and_route_preserved': True, 'preview_before_accept': True,
            'seconds': round(time.monotonic()-started, 3), **checks}


def flow_b(store, provider, settings, limit, report_dir):
    p = store.create(Project(name=f'ARCHIE {provider} live document journey'))
    source = ROOT/'fixtures/projects/B/sow.docx'
    started = time.monotonic()
    result = ingest_live(store, p.id, source.read_bytes(), source.name, provider, settings,
                         live_run=limit, deadline=time.monotonic()+180)
    p = accept_result(store, p, result)
    assert len(p.components) == 8 and len(p.interfaces) == 4
    assert p.sources and p.claims and not p.sources[0].unprocessed
    assert all(c.source_id == p.sources[0].id for c in p.claims)
    assert all(i.initiator is None and i.port is None for i in p.interfaces)
    assert next(i for i in p.interfaces if i.id == 'events').delivery is None
    assert all(d.quantity is None for d in p.deployments if d.component_id not in ['operator', 'configuration'])
    assert 1 <= len(p.decisions) <= 3
    p, clarification = clarify(store, p)
    policies = lookup('management cross zone session initiator audit')
    findings = evaluate(p)
    assert policies and findings['implemented'] == 8 and findings['manual_review'] == 12
    checks = derived_checks(p)
    (report_dir/'flow-b-project.json').write_text(p.model_dump_json(indent=2))
    (report_dir/'flow-b-findings.json').write_text(json.dumps(findings, indent=2))
    return {'passed': True, 'project_id': p.id, 'fixture': str(source.relative_to(ROOT)),
            'coverage': result['coverage'], 'clarification': clarification,
            'retrieved_policy_ids': [r['id'] for r in policies], 'implemented_checks': 8,
            'manual_clauses': 12, 'preview_before_accept': True,
            'seconds': round(time.monotonic()-started, 3), **checks}


def local_small(store, provider, settings, limit, report_dir):
    """One request, no repair: the intentionally small installed-model check."""
    p = store.create(Project(name='ARCHIE local small extraction smoke'))
    text = 'Add one workstation named Review station with role workstation. Its zone is unspecified.'
    source = parse(text.encode(), 'Prompt', 'prompt')
    prompt = json.dumps({'source': {'id': 'S1', 'locator': 'prompt/1', 'text': text}, 'components': []}, separators=(',', ':'))
    started = time.monotonic()
    local_settings = settings.model_copy(update={'max_output': min(settings.max_output, 1024)})
    result = BudgetedProvider(store, local_settings, OllamaAdapter(local_settings)).call(
        prompt, p.id, limit['id']+'-small-'+uid(), task='draft', live_run=limit, deadline=time.monotonic()+120)
    proposal = store.preview(proposal_from_envelope(p, source, result.content, source_alias='S1'))
    p = accept_result(store, p, {'proposal': proposal})
    assert len(p.components) == 1 and p.components[0].name == 'Review station'
    (report_dir/'small-project.json').write_text(p.model_dump_json(indent=2))
    return {'passed': True, 'project_id': p.id, 'preview_before_accept': True,
            'usage': result.usage.model_dump(), 'seconds': round(time.monotonic()-started, 3),
            'scope': 'One component extraction/validated proposal only; no broader local journey claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['openai', 'ollama'], required=True)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--model')
    parser.add_argument('--context', type=int, choices=[4096, 8192])
    parser.add_argument('--local-small', action='store_true', help='One small local extraction only; no repair')
    parser.add_argument('--run-id', default='journeys-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    parser.add_argument('--max-calls', type=int, default=6)
    parser.add_argument('--budget-usd', type=float, default=.5)
    args = parser.parse_args()
    if not args.live:
        parser.error('Real provider journeys require explicit --live')
    if args.local_small and args.provider != 'ollama':
        parser.error('--local-small is only for Ollama')
    if not 1 <= args.max_calls <= 10 or not 0 < args.budget_usd <= .5:
        parser.error('Live journeys are limited to ten calls / $0.50')
    settings = Settings.environment()
    if args.provider == 'openai' and (not settings.live_tests or not settings.allow_cloud):
        parser.error('OpenAI also requires APP_LIVE_TESTS=true and APP_ALLOW_CLOUD=true')
    updates = {}
    if args.model:
        updates['openai_model' if args.provider == 'openai' else 'ollama_model'] = args.model
    if args.context:
        updates['ollama_num_ctx'] = args.context
    settings = Settings.model_validate({**settings.model_dump(), **updates})
    report_dir = ROOT/'reports'/(f'{args.run_id}-{args.provider}'+('-small' if args.local_small else ''))
    report_dir.mkdir(parents=True, exist_ok=False)
    store = Store()
    limit = {'id': args.run_id, 'max_calls': args.max_calls, 'budget_usd': args.budget_usd}
    report = {'provider': args.provider, 'model': settings.openai_model if args.provider == 'openai' else settings.ollama_model,
              'run_id': args.run_id, 'platform': platform.platform(), 'settings': settings.model_dump(),
              'test_ceiling': limit, 'flows': {},
              'scope': 'Actual application orchestration services; browser editing verified separately. Synthetic automatic acceptance/answers in this test only.'}
    before_ids = {p['id'] for p in store.list()}
    flows = [('small_extraction', local_small)] if args.local_small else [('A', flow_a)] + ([('B', flow_b)] if args.provider == 'openai' else [])
    for name, flow in flows:
        try:
            report['flows'][name] = flow(store, args.provider, settings, limit, report_dir)
        except Exception as error:
            report['flows'][name] = {'passed': False, 'error_code': getattr(error, 'code', type(error).__name__),
                                     'message': getattr(error, 'message', str(error) if isinstance(error, AssertionError) else 'Provider or journey validation failed')}
        project_ids = [p['id'] for p in store.list() if p['id'] not in before_ids]
        report['usage'] = {pid: usage_summary(store, pid) for pid in project_ids}
        report['total_calls'] = sum(u['calls'] for u in report['usage'].values())
        report['total_usd'] = sum(u['total'] for u in report['usage'].values())
        report['all_passed'] = all(f['passed'] for f in report['flows'].values())
        (report_dir/'report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps({'flow': name, **report['flows'][name], 'calls': report['total_calls'], 'usd': report['total_usd']}), flush=True)
    if args.provider == 'ollama':
        report['ollama_ps'] = subprocess.run(['ollama', 'ps'], capture_output=True, text=True).stdout
        report['ollama_show'] = subprocess.run(['ollama', 'show', settings.ollama_model], capture_output=True, text=True).stdout
        report['memory_note'] = 'Ollama loaded-model observation after generation; not peak unified-memory sampling.'
        (report_dir/'report.json').write_text(json.dumps(report, indent=2))
    print(f'Report: {report_dir}/report.json')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
