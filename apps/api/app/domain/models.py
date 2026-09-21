"""Canonical schema. Frontend contracts are generated from this module."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal, Any
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()

class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class System(Record):
    id: str
    name: str = Field(min_length=1, max_length=160)
    scope: Literal['internal','external'] = 'internal'

class Zone(Record):
    id: str
    name: str = Field(min_length=1, max_length=160)

class Component(Record):
    id: str
    name: str = Field(min_length=1, max_length=160)
    role: str = Field(max_length=160)
    system_id: str | None = None
    status: Literal['existing','new','proposed'] = 'proposed'
    asset_id: str = 'server'
    scope: Literal['internal','external'] = 'internal'
    audit_destination: str | None = None
    storage_destination: str | None = None
    local_only: bool | None = None
    internet_hosted: bool | None = None
    evidence: list[str] = Field(default_factory=list)

class Deployment(Record):
    id: str
    component_id: str
    zone_id: str | None = None
    host: str | None = None
    site: str | None = None
    quantity: int | None = Field(default=None, ge=0)

class Interface(Record):
    id: str
    source: str
    target: str
    purpose: str | None = Field(default=None,max_length=160)
    data_direction: Literal['source_to_target','target_to_source','bidirectional','unknown'] = 'unknown'
    initiator: str | None = None
    protocol: str | None = Field(default=None,max_length=80)
    port: int | None = Field(default=None,ge=0,le=65535)
    enforcement: list[str] = Field(default_factory=list)
    delivery: str | None = None
    evidence: list[str] = Field(default_factory=list)

class Passage(Record):
    locator: str
    heading: str = ''
    text: str
    page: int | None = None

class Source(Record):
    id: str
    name: str
    version: str = '1.0'
    kind: Literal['document','prompt','template','assistant_proposal']
    sha256: str
    canonical_id: str
    variants: list[str] = Field(default_factory=list)
    passages: list[Passage] = Field(default_factory=list)
    processed: list[str] = Field(default_factory=list)
    unprocessed: list[str] = Field(default_factory=list)
    unsupported_pages: list[int] = Field(default_factory=list)

class Claim(Record):
    id: str
    source_id: str
    source_version: str
    locator: str
    excerpt: str
    target_id: str
    field: str
    value: Any = None
    source_kind: Literal['document','prompt','template','assistant_proposal']
    review: Literal['unreviewed','confirmed','rejected','unknown','conflicting'] = 'unreviewed'

class Constraint(Record):
    id: str
    scope: str = 'project'
    key: str
    value: Any = None
    evidence: list[str] = Field(default_factory=list)

class Decision(Record):
    id: str
    question: str
    target_id: str | None = None
    field: str
    options: list[str]
    answer: str | None = None
    state: Literal['unknown','answered'] = 'unknown'
    evidence: list[str] = Field(default_factory=list)

class Placement(Record):
    x: float = 0
    y: float = 0
    width: float = Field(default=170,ge=50,le=4000)
    height: float = Field(default=85,ge=30,le=4000)
    visible: bool = True
    locked: bool = False
    label: str | None = None

class Route(Record):
    style: Literal['straight','orthogonal'] = 'orthogonal'
    points: list[dict[str,float]] = Field(default_factory=list,max_length=30)
    source_handle: str = 'right'
    target_handle: str = 'left'
    locked: bool = False

class View(Record):
    type: Literal['logical','sv1','sv2']
    revision: int = 0
    placements: dict[str,Placement] = Field(default_factory=dict)
    routes: dict[str,Route] = Field(default_factory=dict)
    mappings: dict[str,list[str]] = Field(default_factory=dict)

class Project(Record):
    id: str = Field(default_factory=uid)
    name: str = 'Untitled architecture'
    schema_version: Literal['1.0'] = '1.0'
    revision: int = 0
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    synthetic: bool = True
    policy_version: str = '1.0'
    template_version: str = '1.0'
    systems: list[System] = Field(default_factory=list)
    zones: list[Zone] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list,max_length=50)
    deployments: list[Deployment] = Field(default_factory=list)
    interfaces: list[Interface] = Field(default_factory=list,max_length=100)
    sources: list[Source] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    views: dict[str,View] = Field(default_factory=lambda:{k:View(type=k) for k in ['logical','sv1','sv2']})
    notes: str = ''

    @model_validator(mode='after')
    def references(self):
        groups=['systems','zones','components','deployments','interfaces','sources','claims','constraints','decisions']
        ids=[x.id for group in groups for x in getattr(self,group)]
        if len(ids)!=len(set(ids)): raise ValueError('IDs must be globally unique')
        if any(not x or len(x)>180 for x in ids): raise ValueError('Invalid ID')
        c={x.id for x in self.components}; s={x.id for x in self.systems}; z={x.id for x in self.zones}
        evidence={x.id for x in self.claims}; sources={x.id:x for x in self.sources}
        def ref(value, allowed):
            if value is not None and value not in allowed: raise ValueError(f'Unresolved reference: {value}')
        for x in self.components:
            ref(x.system_id,s); ref(x.audit_destination,c); ref(x.storage_destination,c)
            for e in x.evidence: ref(e,evidence)
        seen=set()
        for x in self.deployments:
            ref(x.component_id,c); ref(x.zone_id,z)
            if x.component_id in seen: raise ValueError('One deployment record per component in PoC')
            seen.add(x.component_id)
        for x in self.interfaces:
            ref(x.source,c); ref(x.target,c); ref(x.initiator,{x.source,x.target})
            for e in x.enforcement: ref(e,c)
            for e in x.evidence: ref(e,evidence)
        for x in self.constraints+self.decisions:
            for e in x.evidence: ref(e,evidence)
        for x in self.decisions: ref(x.target_id,set(ids))
        for x in self.claims:
            ref(x.source_id,sources)
            src=sources[x.source_id]
            if x.source_kind != src.kind or x.source_version != src.version: raise ValueError('Source kind/version mismatch')
            passages=[p for p in src.passages if p.locator==x.locator]
            if not passages or not x.excerpt or not any(x.excerpt in p.text for p in passages): raise ValueError('Unresolvable evidence excerpt/locator')
            # Rejected candidates may refer to objects that were deliberately not accepted.
            if x.review=='confirmed': ref(x.target_id,set(ids))
        if set(self.views)!={'logical','sv1','sv2'}: raise ValueError('All three views required')
        return self

class Operation(Record):
    op: Literal['add','update','remove','placement','route','notes']
    entity: Literal['systems','zones','components','deployments','interfaces','sources','claims','constraints','decisions'] | None = None
    id: str = ''
    value: dict[str,Any] = Field(default_factory=dict)
    view: Literal['logical','sv1','sv2'] = 'logical'
    confirmed: bool = False

class ChangeSet(Record):
    id: str = Field(default_factory=uid)
    project_id: str
    request_id: str = Field(default_factory=uid)
    base_revision: int
    base_views: dict[str,int]
    operations: list[Operation] = Field(min_length=1,max_length=500)
    affected_ids: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    state: Literal['pending','accepted','rejected'] = 'pending'
    origin: Literal['manual','assistant','ingest'] = 'manual'
