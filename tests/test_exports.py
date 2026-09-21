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
    assert all(d.answer is None for d in sanitised.decisions)

def test_svg_escapes_markup():
    p=Project(components=[{'id':'safe','name':'<script>alert(1)</script>','role':'server','asset_id':'../../secret'}])
    raw,_=export(p,'svg');assert b'<script>' not in raw and b'&lt;script&gt;' in raw
