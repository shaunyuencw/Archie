import base64,csv,io,json,re
from html import escape
from pathlib import Path
from docx import Document
from docx.shared import Pt
from ..domain.models import Project,uid
from ..domain.views import view_graph,narrative,initialise_views
ROOT=Path(__file__).resolve().parents[4]

def csv_text(p):
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    fields=['id','source','target','purpose','data_direction','initiator','protocol','port','enforcement','delivery','semantic_revision']
    def safe(v):
        text='' if v is None else str(v)
        return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text
    writer.writerow(fields)
    for i in p.interfaces:
        values=i.model_dump();values['enforcement']=';'.join(i.enforcement);values['semantic_revision']=p.revision
        writer.writerow([safe(values.get(f)) for f in fields])
    return stream.getvalue()

def svg(p,kind):
    g=view_graph(p,kind);nodes={n['id']:dict(n) for n in g['nodes']}
    for n in nodes.values():
        if n['parentId'] in nodes:
            parent=nodes[n['parentId']];n['x']+=parent['x'];n['y']+=parent['y']
    x0=min([n['x'] for n in nodes.values()]+[0])-30;y0=min([n['y'] for n in nodes.values()]+[0])-70
    width=max([n['x']+n['width'] for n in nodes.values()]+[800])-x0+40;height=max([n['y']+n['height'] for n in nodes.values()]+[500])-y0+40
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {width} {height}"><title>{escape(p.name)} — {kind} revision {p.revision}</title><metadata>Image export; not native Visio. SYNTHETIC — DEMONSTRATION ONLY</metadata><rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="#f7fafc"/><text x="0" y="-30" font-family="Arial" font-size="15">SYNTHETIC — DEMONSTRATION ONLY · {kind} · revision {p.revision}</text>']
    def draw_node(n,zone=False):
        x,y,w,h=n['x'],n['y'],n['width'],n['height'];ident=escape(n['id'],quote=True)
        parts.append(f'<g id="{ident}" data-object-ids="{escape(json.dumps(n["object_ids"]),quote=True)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{"#edf4f7" if zone else "white"}" stroke="#91aab6" {"stroke-dasharray=\"5 4\"" if zone else ""}/>')
        path=ROOT/'fixtures/assets'/f'{n["asset_id"]}.svg'
        allowed={a['id'] for a in json.loads((ROOT/'fixtures/assets/manifest.json').read_text())}
        if not zone and n['asset_id'] in allowed:
            b64=base64.b64encode(path.read_bytes()).decode();parts.append(f'<image x="{x+12}" y="{y+10}" width="24" height="24" href="data:image/svg+xml;base64,{b64}"/>')
        words=n['label'].split();lines=[];line=''
        for word in words:
            if len(line+' '+word)>max(12,int(w/7)):
                lines.append(line);line=word
            else:line=(line+' '+word).strip()
        lines.append(line)
        for i,line in enumerate(lines):parts.append(f'<text x="{x+12}" y="{y+(22 if zone else 48)+i*15}" font-family="Arial" font-size="12" fill="#233346">{escape(line)}</text>')
        parts.append('</g>')
    for n in nodes.values():
        if n['role']=='zone':draw_node(n,True)
    for e in g['edges']:
        if e['source'] not in nodes or e['target'] not in nodes:continue
        a,b=nodes[e['source']],nodes[e['target']];sx,sy=a['x']+a['width'],a['y']+a['height']/2;tx,ty=b['x'],b['y']+b['height']/2
        route=e['route'];style=route.style if route else 'orthogonal';points=[pt.model_dump() for pt in route.points] if route else []
        if not points and style=='orthogonal':points=[{'x':(sx+tx)/2,'y':sy},{'x':(sx+tx)/2,'y':ty}]
        path=f'M {sx} {sy} '+''.join(f'L {pt["x"]} {pt["y"]} ' for pt in points)+f'L {tx} {ty}'
        parts.append(f'<g id="{escape(e["id"],quote=True)}" data-interface-ids="{escape(json.dumps(e["object_ids"]),quote=True)}"><path d="{path}" fill="none" stroke="#718096" stroke-width="1.5"/><text x="{(sx+tx)/2}" y="{(sy+ty)/2-6}" font-family="Arial" font-size="10" text-anchor="middle">{escape(e["label"])}</text></g>')
    for n in nodes.values():
        if n['role']!='zone':draw_node(n)
    return ''.join(parts)+'</svg>'

def docx_bytes(p):
    doc=Document();doc.styles['Normal'].font.name='Calibri';doc.styles['Normal'].font.size=Pt(10)
    for line in narrative(p).splitlines():
        if line.startswith('# '):doc.add_heading(line[2:],0)
        elif line.startswith('## '):doc.add_heading(line[3:],1)
        elif line.startswith('- '):doc.add_paragraph(line[2:],style='List Bullet')
        elif line:doc.add_paragraph(line)
    stream=io.BytesIO();doc.save(stream);return stream.getvalue()

def pattern(p):
    """Whitelist reusable semantics. No addresses, arbitrary labels, evidence or answers."""
    out=Project(name='Synthetic reusable architecture pattern')
    allowed={a['id'] for a in json.loads((ROOT/'fixtures/assets/manifest.json').read_text())}
    mapping={x.id:f'{group}-{i+1}' for group in ['systems','zones','components','deployments','interfaces','decisions'] for i,x in enumerate(getattr(p,group))}
    d=out.model_dump();roles={'video management','operator','configuration','management integration','analytics','audit','firewall','workstation','external command system'}
    d['systems']=[{'id':mapping[x.id],'name':f'System {i+1}','scope':x.scope} for i,x in enumerate(p.systems)]
    d['zones']=[{'id':mapping[x.id],'name':f'Zone {i+1}'} for i,x in enumerate(p.zones)]
    d['components']=[{'id':mapping[x.id],'name':x.asset_id if x.asset_id in allowed else 'generic role','role':x.role if x.role in roles else 'generic role','asset_id':x.asset_id if x.asset_id in allowed else 'generic-role-a','scope':x.scope,'system_id':mapping.get(x.system_id),'status':'proposed'} for x in p.components]
    d['deployments']=[{'id':mapping[x.id],'component_id':mapping[x.component_id],'zone_id':mapping.get(x.zone_id)} for x in p.deployments]
    d['interfaces']=[{'id':mapping[x.id],'source':mapping[x.source],'target':mapping[x.target],'purpose':x.purpose if x.purpose in ['video','events','management','integration'] else None,'data_direction':'unknown'} for x in p.interfaces]
    d['decisions']=[{'id':f'question-{i+1}','question':f'Confirm {x.field if x.field in ["initiator","delivery","purpose","value"] else "architecture decision"} for the new project','field':x.field if x.field in ['initiator','delivery','purpose','value'] else 'resolution','target_id':mapping.get(x.target_id),'options':['Not decided'],'answer':None,'state':'unknown'} for i,x in enumerate(p.decisions)]
    # Only the pattern's own fictional constraints; project-specific constraints never escape.
    d['constraints']=[{'id':'pattern-synthetic','key':'synthetic_pattern','value':True}]
    for kind,v in p.views.items():
        for ident,pos in v.placements.items():
            if ident in mapping:d['views'][kind]['placements'][mapping[ident]]=pos.model_copy(update={'label':None}).model_dump()
        for ident,route in v.routes.items():
            if ident in mapping:d['views'][kind]['routes'][mapping[ident]]=route.model_dump()
    return initialise_views(Project.model_validate(d))

def export(p,format,view='logical'):
    if view not in p.views:raise ValueError('Unknown view')
    if format=='json':return p.model_dump_json(indent=2).encode(),'application/json'
    if format=='svg':return svg(p,view).encode(),'image/svg+xml'
    if format=='md':return narrative(p).encode(),'text/markdown'
    if format=='csv':return csv_text(p).encode('utf-8-sig'),'text/csv'
    if format=='docx':return docx_bytes(p),'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if format=='pattern':return pattern(p).model_dump_json(indent=2).encode(),'application/json'
    raise ValueError('Unsupported export format')
