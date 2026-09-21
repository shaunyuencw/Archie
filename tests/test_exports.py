import csv,io,json
from pathlib import Path
from xml.etree import ElementTree as ET
from docx import Document
from apps.api.app.domain.models import Project
from apps.api.app.exports.service import export,pattern

def test_T16_exports_and_sanitised_pattern():
    p=Project.model_validate_json(Path('fixtures/references/A/project.json').read_text(encoding='utf-8'))
    p.notes='Private reviewer 192.0.2.4';p.components[0].name='Private server 192.0.2.4';p.interfaces[0].purpose='=HYPERLINK("danger")'
    raw,_=export(p,'json');assert Project.model_validate_json(raw)==p
    doc,_=export(p,'docx');assert 'Private server' in '\n'.join(x.text for x in Document(io.BytesIO(doc)).paragraphs)
    raw,_=export(p,'csv');rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));assert rows[0]['purpose'].startswith("'=")
    assert {r['id'] for r in rows}=={i.id for i in p.interfaces}
    for view in ['logical','sv1','sv2']:
        raw,_=export(p,'svg',view);svg=ET.fromstring(raw);assert 'not native Visio' in raw.decode()
        ids={i for element in svg.iter() for i in json.loads(element.attrib.get('data-interface-ids','[]'))}
        expected={i.id for i in p.interfaces if view!='sv1' or next(c for c in p.components if c.id==i.source).system_id!=next(c for c in p.components if c.id==i.target).system_id}
        assert ids==expected
    sanitised=pattern(p);text=sanitised.model_dump_json()
    assert '192.0.2.4' not in text and 'Private' not in text and 'HYPERLINK' not in text
    assert not sanitised.sources and not sanitised.claims and not sanitised.notes
    assert sanitised.policy_ids==[]
    assert all(d.answer is None for d in sanitised.decisions)

def test_svg_escapes_markup():
    p=Project(components=[{'id':'safe','name':'<script>alert(1)</script>','role':'server','asset_id':'../../secret'}])
    raw,_=export(p,'svg');assert b'<script>' not in raw and b'&lt;script&gt;' in raw

def test_stacked_cloud_and_hosted_appliance_symbols_follow_canonical_deployment():
    from apps.api.app.domain.catalogue import catalogue
    p=Project(components=[{'id':'host','name':'Cloud host','role':'server','asset_id':'aws-ec2'},
                          {'id':'fw','name':'Virtual firewall','role':'firewall','asset_id':'virtual-firewall','form_factor':'virtual'}],
              deployments=[{'id':'dh','component_id':'host','quantity':2},
                           {'id':'df','component_id':'fw','host_component_id':'host','quantity':2,'redundancy_mode':'active_passive'}])
    root=ET.fromstring(export(p,'svg')[0]);ns={'s':'http://www.w3.org/2000/svg'}
    assert len(root.findall(".//s:image[@class='stack-copy']",ns))==2
    assert root.find("s:g[@id='host']/s:g[@class='hosted-control']/s:title",ns).text=='Virtual firewall hosted here'
    assert 'arrangement not decided' in ''.join(root.itertext()) and 'active / standby' in ''.join(root.itertext())
    assert {c.asset_id for c in pattern(p).components}=={'aws-ec2','virtual-firewall'}
    assets=catalogue();assert len({a['id'] for a in assets})==len(assets)==43

def test_svg_matches_equipment_ports_routes_and_flow_direction():
    p=Project(components=[{'id':'a','name':'Application','role':'application','asset_id':'application'},
                          {'id':'b','name':'Storage','role':'storage','asset_id':'storage'}],
              zones=[{'id':'z','name':'Declared zone'}],
              interfaces=[{'id':'i','source':'a','target':'b','data_direction':'bidirectional'}])
    from apps.api.app.domain.models import Placement,Route
    p.views['logical'].placements={'a':Placement(x=10,y=20,width=180,height=100),
                                   'b':Placement(x=400,y=300,width=180,height=100)}
    p.views['logical'].routes['i']=Route(source_handle='bottom',target_handle='top',points=[{'x':230,'y':210}])
    root=ET.fromstring(export(p,'svg')[0]);ns={'s':'http://www.w3.org/2000/svg'}
    equipment=root.find("s:g[@id='a']",ns);assert equipment.find('s:rect',ns) is None
    assert equipment.find('s:image',ns).attrib['width']=='43'
    assert root.find("s:g[@id='z']/s:rect",ns).attrib['stroke-dasharray']=='7 5'
    path=root.find("s:g[@id='i']/s:path",ns).attrib
    assert path['d'].startswith('M 100.0 120.0 ') and path['d'].endswith('490.0 300.0')
    assert '230.0 210.0' in path['d']
    assert path['marker-start']==path['marker-end']=='url(#flow-arrow)'
    coordinates=[tuple(map(float,point.split())) for point in path['d'][2:].split(' L ')]
    assert all(a[0]==b[0] or a[1]==b[1] for a,b in zip(coordinates,coordinates[1:]))
    p.views['logical'].routes['i'].style='straight'
    straight=ET.fromstring(export(p,'svg')[0]).find("s:g[@id='i']/s:path",ns)
    assert straight.attrib['d']=='M 100.0 120.0 L 230.0 210.0 L 490.0 300.0'

def test_svg_keeps_far_manual_routes_inside_image():
    p=Project(components=[{'id':'a','name':'A','role':'application'},{'id':'b','name':'B','role':'application'}],
              interfaces=[{'id':'i','source':'a','target':'b'}])
    from apps.api.app.domain.models import Route
    p.views['logical'].routes['i']=Route(points=[{'x':-450,'y':1500}])
    root=ET.fromstring(export(p,'svg')[0]);x,y,width,height=map(float,root.attrib['viewBox'].split())
    assert x < -450 < x+width and y < 1500 < y+height

def test_svg_preserves_dragged_segments_without_midpoint_doglegs():
    from apps.api.app.domain.models import Route
    from apps.api.app.exports.service import _edge_points
    source={'x':0,'y':0,'width':100,'height':100}
    target={'x':400,'y':200,'width':100,'height':100}
    route=Route(points=[{'x':240,'y':27},{'x':240,'y':227}])
    assert _edge_points(source,target,route)==[(100,27),(240,27),(240,227),(400,227)]
    route=Route(style='straight',points=[])
    assert _edge_points(source,target,route)==[(100,27),(400,227)]

def test_reference_svg_interface_labels_do_not_cover_each_other():
    p=Project.model_validate_json(Path('fixtures/references/A/project.json').read_text(encoding='utf-8'))
    ns='{http://www.w3.org/2000/svg}'
    for view in p.views:
        root=ET.fromstring(export(p,'svg',view)[0]);boxes=[]
        for group in root.findall(f".//{ns}g[@data-interface-label-for]"):
            rect=group.find(ns+'rect');x,y,w,h=[float(rect.attrib[key]) for key in ['x','y','width','height']]
            boxes.append((x,y,x+w,y+h))
        assert all(not (a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1])
                   for i,a in enumerate(boxes) for b in boxes[i+1:])


def test_svg_preserves_presentation_colors_icon_alpha_and_canvas_label_offset():
    from apps.api.app.domain.models import Placement,Route
    p=Project(components=[{'id':'a','name':'Application','role':'application','asset_id':'server'},
                          {'id':'b','name':'Database','role':'database','asset_id':'database'}],
              zones=[{'id':'z','name':'Protected zone'}],
              interfaces=[{'id':'i','source':'a','target':'b','purpose':'application traffic'}])
    p.views['logical'].placements={
        'z':Placement(x=-20,y=-30,width=600,height=220,fill_color='#fef3c7',text_color='#713f12',border_color='#92400e'),
        'a':Placement(x=0,y=0,width=100,height=90,fill_color='#ecfeff',text_color='#155e75',border_color='#0891b2',icon_color='#0f766e',z_index=3),
        'b':Placement(x=400,y=0,width=100,height=90,z_index=-2),
    }
    p.views['logical'].routes['i']=Route(line_color='#7c3aed',text_color='#be123c',label_offset={'x':30,'y':-12})
    raw,_=export(p,'svg');root=ET.fromstring(raw);ns={'s':'http://www.w3.org/2000/svg'}
    application=root.find("s:g[@id='a']",ns)
    assert application.find('s:rect',ns).attrib['fill']=='#ecfeff'
    assert application.find('s:rect',ns).attrib['stroke']=='#0891b2'
    mask=application.find('s:mask',ns);assert mask is not None and mask.attrib['mask-type']=='alpha'
    tinted=application.find("s:rect[@mask]",ns);assert tinted is not None and tinted.attrib['fill']=='#0f766e'
    assert '#155e75' in [text.attrib['fill'] for text in application.findall('s:text',ns)]
    zone=root.find("s:g[@id='z']/s:rect",ns);assert zone.attrib['fill']=='#fef3c7' and zone.attrib['stroke']=='#92400e'
    edge=root.find("s:g[@id='i']",ns);path=edge.find('s:path',ns)
    assert path.attrib['stroke']=='#7c3aed'
    label_group=root.find("s:g[@data-interface-label-for='i']",ns)
    assert all(text.attrib['fill']=='#be123c' for text in label_group.findall('s:text',ns))
    label_box=label_group.find('s:rect',ns)
    # The Canvas smooth-step base has a longest 124..250 segment at y=27; moved +30,-12.
    assert float(label_box.attrib['x'])+float(label_box.attrib['width'])/2==217
    assert float(label_box.attrib['y'])+float(label_box.attrib['height'])/2==15
    assert raw.index(b'id="a"')<raw.index(b'data-interface-label-for="i"')
    assert raw.index(b'id="b"')<raw.index(b'id="a"')
