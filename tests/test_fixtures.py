import hashlib,json
from pathlib import Path
from pypdf import PdfReader
from apps.api.app.domain.models import Project
from scripts.seed import main

def test_fixture_completeness_and_idempotency(tmp_path):
    main(tmp_path)
    before={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
    main(tmp_path)
    assert before=={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
    assert len(list(tmp_path.rglob('*.docx')))==6
    for pdf in tmp_path.rglob('*.pdf'):
        reader=PdfReader(pdf); assert 2<=len(reader.pages)<=4
        assert 'SYNTHETIC' in reader.pages[0].extract_text()
    for f in (tmp_path/'references').glob('*/project.json'): Project.model_validate_json(f.read_text(encoding='utf-8'))
    assert len(json.loads((tmp_path/'assets/manifest.json').read_text()))==24
    assert len(json.loads((tmp_path/'policies/clauses.json').read_text(encoding='utf-8'))['clauses'])==20
