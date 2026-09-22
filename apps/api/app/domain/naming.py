import re
from .models import Operation

DEFAULT_NAMES={'untitled architecture','new architecture','new project'}

def explicit_name_request(source):
    return bool(source and source.kind=='prompt' and re.search(r'\b(?:rename|name|title|call)\b.{0,40}\b(?:project|architecture)\b',' '.join(p.text for p in source.passages),re.I))

def can_suggest_name(project,source=None):
    if project.name.strip().lower() in DEFAULT_NAMES:return True
    return explicit_name_request(source)

def document_title(source):
    """Use an explicit document title when the provider omits naming metadata."""
    if not source or source.kind!='document':return None
    lines=[line.strip().strip('# ').strip() for passage in source.passages[:3] for line in passage.text.splitlines() if line.strip()][:24]
    for index,line in enumerate(lines[:-1]):
        if line.casefold() in {'system','system name','project name'}:
            title=lines[index+1]
            if 3<=len(title)<=160:return title
    for line in lines[:8]:
        if re.search(r'^(?:page\s+\d+|version\b|synthetic\b|\(?[A-Z]{2,8}\)?$)',line,re.I):continue
        if 'technical system description' in line.lower():continue
        title=re.sub(r'\s+(?:technical\s+(?:specification|description)|system specification)\b.*$','',line,flags=re.I).strip(' -–—:')
        if 3<=len(title)<=120 and len(title.split())>=2 and not title.endswith('.'):
            return title
    return None

def name_operation(project,source,suggestion):
    if not can_suggest_name(project,source):return None
    suggestion=suggestion or document_title(source)
    if not suggestion:return None
    name=' '.join(suggestion.split()).strip('"')
    if not name or name==project.name:return None
    return Operation(op='project_name',value={'name':name})
