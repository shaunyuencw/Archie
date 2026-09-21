import json,time
from typing import Literal
from pydantic import Field
from ..domain.models import Record

class WireOperation(Record):
    op:Literal['add','update','remove']
    entity:Literal['systems','zones','components','deployments','interfaces','constraints']
    id:str
    value_json:str

class WireClaim(Record):
    source_id:str
    locator:str
    excerpt:str
    target_id:str
    field:str
    value_json:str

class ToolRequest(Record):
    name:Literal['get_architecture_context','lookup_policies','find_assets','load_view_spec']
    query:str

class Envelope(Record):
    operations:list[WireOperation]
    claims:list[WireClaim]
    tool:ToolRequest|None
    message:str
    project_name:str|None=Field(default=None,max_length=160)

class Usage(Record):
    input_tokens:int=0
    cache_read_tokens:int=0
    cache_write_tokens:int=0
    output_tokens:int=0
    reasoning_tokens:int=0
    latency_ms:float=0

class ProviderResult(Record):
    content:Envelope
    finish_status:Literal['completed']
    model:str
    usage:Usage

def schema():
    result=Envelope.model_json_schema()
    # Live strict schemas require every property, including nullable metadata.
    result['required']=list(result['properties'])
    result['properties']['project_name'].pop('default',None)
    return result
def estimate(text):
    # Conservative byte upper bound. May reject long local requests early; never truncates context.
    return len(text.encode('utf-8'))

def cost(usage,rates):
    return (usage.input_tokens*rates['input']+usage.cache_read_tokens*rates['cache_read']+usage.cache_write_tokens*rates['cache_write']+usage.output_tokens*rates['output'])/1_000_000
