"""Read-only decision history over saved proposals, including dismissed jobs."""
import json


def proposal_history(store, project_id, before=None, limit=30):
    project=store.get(project_id)
    with store.connect() as db:
        rows=db.execute("SELECT rowid AS sequence,body,state FROM changes WHERE project_id=? AND state IN ('accepted','rejected') AND (? IS NULL OR rowid<?) ORDER BY rowid DESC LIMIT ?",(project_id,before,before,limit+1)).fetchall()
        jobs={};discarded=set()
        for job in db.execute('SELECT kind,request,result,created_at FROM jobs WHERE project_id=?',(project_id,)):
            request=json.loads(job['request'])
            if request.get('discarded_proposal_id'):discarded.add(request['discarded_proposal_id'])
            result=json.loads(job['result']) if job['result'] else {};proposal=result.get('proposal') or {}
            if proposal.get('id'):jobs[proposal['id']]={**dict(job),'request':request}
    names={item.id:item.name for group in [project.components,project.zones,project.systems] for item in group}
    sources={source.id:source for source in project.sources}
    claim_sources={claim.id:claim.source_id for claim in project.claims}
    items=[]
    for row in rows[:limit]:
        proposal=json.loads(row['body']);job=jobs.get(proposal['id'],{});request=job.get('request',{})
        if proposal['id'] in discarded:continue
        title_names={**names,**{op['id']:op['value']['name'] for op in proposal['operations'] if op.get('id') and op.get('value',{}).get('name')}}
        def name(value):return title_names.get(value,value or 'Unspecified')
        summaries=[];source_prompt=None;source_name=request.get('file',{}).get('name');referenced_sources=set()
        if request.get('source_id'):referenced_sources.add(request['source_id'])
        for op in proposal['operations']:
            value=op.get('value',{});entity=op.get('entity');action=op['op'];ident=op.get('id')
            if entity=='sources':
                source_name=value.get('name')
                if value.get('kind')=='prompt':source_prompt='\n'.join(p.get('text','') for p in value.get('passages',[]))
                continue
            if entity=='claims':
                source_id=value.get('source_id') or claim_sources.get(ident)
                if source_id:referenced_sources.add(source_id)
                continue
            label=name(ident)
            if action=='project_name':text=f'Name project “{value.get("name","")}”'
            elif action=='policy_selection':text=f'Select {len(value.get("policy_ids",[]))} project policies'
            elif action=='notes':text='Update design notes'
            elif action in ['placement','route']:text=f'Adjust diagram presentation for {label}'
            elif entity=='interfaces' and action=='add':text=f'Connect {name(value.get("source"))} → {name(value.get("target"))}'
            elif entity=='deployments':text=f'Update deployment of {name(value.get("component_id"))}'
            elif entity=='decisions':text=value.get('question') or 'Update a design decision'
            elif entity=='constraints':text=f'Record requirement: {value.get("key",label)}'
            elif action=='remove':text=f'Remove {label}'
            elif action=='add':text=f'Add {label}'
            elif value.get('name'):text=f'Set name to “{value["name"]}”'
            else:text=f'Update {label}'
            summaries.append(text)
        if len(referenced_sources)==1:
            source=sources.get(next(iter(referenced_sources)))
            if source:
                source_name=source_name or source.name
                if source.kind=='prompt':source_prompt=source_prompt or '\n'.join(p.text for p in source.passages)
        items.append({'id':proposal['id'],'state':row['state'],'base_revision':proposal['base_revision'],
                      'prompt':request.get('prompt') or source_prompt,'source_name':source_name,
                      'provider':request.get('provider'),'kind':job.get('kind'),'created_at':job.get('created_at'),
                      'summary':summaries,'findings':proposal.get('findings',[])})
    return {'items':items,'next_cursor':rows[limit-1]['sequence'] if len(rows)>limit else None}
