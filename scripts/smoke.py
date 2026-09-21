"""Explicit provider verification. Never run from offline tests or startup."""
import argparse,json,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.api.app.providers.config import Settings
from apps.api.app.providers.adapters import OpenAIAdapter,OllamaAdapter
from apps.api.app.providers.budget import BudgetedProvider,usage_summary
from apps.api.app.storage.store import Store
from apps.api.app.domain.models import Project,uid
from apps.api.app.ingest.parser import parse
from apps.api.app.orchestration.live import proposal_from_envelope

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--provider',choices=['openai','ollama'],required=True);parser.add_argument('--live',action='store_true');parser.add_argument('--max-calls',type=int,default=3);parser.add_argument('--budget-usd',type=float,default=.5)
    args=parser.parse_args();settings=Settings.environment()
    if args.provider=='openai' and not args.live:parser.error('Paid smoke requires --live explicit opt-in')
    if args.max_calls<1 or args.max_calls>10 or not 0<args.budget_usd<=.5:parser.error('Live smoke is limited to ten calls / $0.50')
    store=Store();p=store.create(Project(name=f'{args.provider} live verification'));run_id='smoke-'+uid();limit={'id':run_id,'max_calls':args.max_calls,'budget_usd':args.budget_usd}
    adapter=OpenAIAdapter(settings) if args.provider=='openai' else OllamaAdapter(settings);budget=BudgetedProvider(store,settings,adapter)
    report={'provider':args.provider,'model':adapter.model,'run_id':run_id,'checks':[],'repair_count':0,'fixture_version':'1.0','hardware_measurement':'nvidia-smi and ollama ps; no peak sampling'}
    for index,task in enumerate(['extract','native_tool','targeted_edit'][:args.max_calls]):
        candidate=None
        text='Add one workstation named Review station with role workstation. Its zone is unspecified.' if task=='extract' else 'Rename Review station to Reviewed station.'
        src=parse(text.encode(),'Prompt','prompt');prompt=json.dumps({'source':{'id':'S1','locator':'prompt/1','text':text},'components':[{'id':c.id,'name':c.name,'role':c.role} for c in p.components]},separators=(',',':'))
        if task=='native_tool':prompt='Request the read-only lookup_policies tool with query management.'
        started=time.monotonic()
        try:
            result=budget.call(prompt,p.id,run_id+f'-{index}','draft',native=task=='native_tool',live_run=limit,deadline=time.monotonic()+90)
            candidate=result.content.model_dump()
            check={'task':task,'schema_valid':True,'model':result.model,'usage':result.usage.model_dump()}
            if task=='native_tool':check['passed']=result.content.tool is not None
            else:
                change=proposal_from_envelope(p,src,result.content,source_alias='S1');store.preview(change);p=store.commit(change)
                check['passed']=any(c.name==('Review station' if task=='extract' else 'Reviewed station') for c in p.components)
                check['accepted_changes']=len(change.operations)
            check['latency_ms']=(time.monotonic()-started)*1000
        except Exception as error:
            # Error details deliberately exclude request headers, environment and SDK exception strings.
            check={'task':task,'passed':False,'error_code':getattr(error,'code',type(error).__name__),'latency_ms':(time.monotonic()-started)*1000}
            if hasattr(error,'message'):check['validation_message']=error.message
            cause=error.__cause__
            if cause is not None:check['cause_type']=type(cause).__name__;check['http_status']=getattr(cause,'status_code',None)
        check['candidate']=candidate
        report['checks'].append(check)
        if check.get('http_status') in [401,403]:break
    report['usage']=usage_summary(store,p.id)
    report['all_passed']=all(x['passed'] for x in report['checks'])
    report['ollama_ps']=subprocess.run(['ollama','ps'],capture_output=True,text=True).stdout if args.provider=='ollama' else None
    Path('reports').mkdir(exist_ok=True);Path(f'reports/smoke-{args.provider}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return 0 if report['all_passed'] else 1
if __name__=='__main__':sys.exit(main())
