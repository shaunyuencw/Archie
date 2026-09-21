import os,json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[4]
load_dotenv(ROOT/'.env')

class Settings(BaseModel):
    provider:str='mock'
    allow_cloud:bool=False
    openai_model:str='gpt-5.4-mini'
    ollama_model:str='qwen3:4b'
    ollama_base_url:str='http://127.0.0.1:11434'
    ollama_num_ctx:int=Field(default=4096,ge=4096,le=8192)
    max_input:int=Field(default=12000,gt=0,le=12000)
    max_output:int=Field(default=3000,gt=0,le=3000)
    max_calls:int=Field(default=4,gt=0,le=8)
    action_usd:float=Field(default=.10,gt=0)
    document_usd:float=Field(default=.20,gt=0)
    day_usd:float=Field(default=1,gt=0)
    project_usd:float=Field(default=5,gt=0)
    live_tests:bool=False
    @classmethod
    def environment(cls):
        mapping={'provider':'APP_PROVIDER','allow_cloud':'APP_ALLOW_CLOUD','openai_model':'OPENAI_MODEL','ollama_model':'OLLAMA_MODEL','ollama_base_url':'OLLAMA_BASE_URL','ollama_num_ctx':'OLLAMA_NUM_CTX','max_input':'APP_MAX_INPUT_TOKENS','max_output':'APP_MAX_OUTPUT_TOKENS','max_calls':'APP_MAX_CALLS_PER_ACTION','action_usd':'APP_BUDGET_ACTION_USD','document_usd':'APP_BUDGET_DOCUMENT_USD','day_usd':'APP_BUDGET_DAY_USD','project_usd':'APP_BUDGET_PROJECT_USD','live_tests':'APP_LIVE_TESTS'}
        settings=cls(**{k:os.environ[v] for k,v in mapping.items() if v in os.environ})
        if settings.provider not in ['mock','openai','ollama']: raise ValueError('Unknown provider')
        url=urlparse(settings.ollama_base_url)
        if url.scheme!='http' or url.hostname not in ['localhost','127.0.0.1','::1'] or url.username or url.password: raise ValueError('Ollama must use a loopback HTTP endpoint')
        return settings

def pricing():return json.loads((ROOT/'config/pricing.json').read_text())
