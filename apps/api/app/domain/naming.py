import re
from .models import Operation

DEFAULT_NAMES={'untitled architecture','new architecture','new project'}

def explicit_name_request(source):
    return bool(source and source.kind=='prompt' and re.search(r'\b(?:rename|name|title|call)\b.{0,40}\b(?:project|architecture)\b',' '.join(p.text for p in source.passages),re.I))

def can_suggest_name(project,source=None):
    if not project.components and project.name.strip().lower() in DEFAULT_NAMES:return True
    return explicit_name_request(source)

def name_operation(project,source,suggestion):
    if not suggestion or not can_suggest_name(project,source):return None
    name=' '.join(suggestion.split()).strip('"')
    if not name or name==project.name:return None
    return Operation(op='project_name',value={'name':name})
