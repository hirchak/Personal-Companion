"""M5 bounded data contracts. No publication or arbitrary attachment capability."""
from typing import Literal
from uuid import UUID
from pydantic import Field, StrictInt, field_validator, model_validator
from .models import StrictModel, EntryInput
from .ai_contracts import Ref

ExportField = Literal['raw_text','title','creative_kind','tags','collections','related_ids','timestamps','provenance']
class CreativeSelection(StrictModel):
    entries: list[Ref] = Field(min_length=1, max_length=100)
    fields: list[ExportField] = Field(min_length=1, max_length=8)
    include_related: Literal[False] = False
    @model_validator(mode='after')
    def unique(self):
        if len({r.id for r in self.entries})!=len(self.entries) or len(set(self.fields))!=len(self.fields):
            raise ValueError('duplicate selection')
        return self

class CreativeDownload(StrictModel):
    plan_id: UUID
    content_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    format: Literal['markdown','json']

class FeedbackInput(StrictModel):
    title: str = Field(min_length=1,max_length=160)
    type: Literal['bug','feature','design','other'] = 'other'
    expected: str = Field(default='',max_length=4000)
    actual: str = Field(default='',max_length=4000)
    steps: str = Field(default='',max_length=4000)
    description: str = Field(default='',max_length=12000)
    visibility: Literal['private','intended_share'] = 'private'
    destination: str = Field(default='Локальний файл',min_length=1,max_length=240)
    # M5 deliberately supports no attachments or source references. Raw sources never auto-copy.
    attachments: list = Field(default_factory=list,max_length=0)
    references: list = Field(default_factory=list,max_length=0)
    @field_validator('title','destination')
    @classmethod
    def nonblank(cls,value): return EntryInput.nonblank(value)
    @field_validator('expected','actual','steps','description')
    @classmethod
    def text_utf8(cls,value): value.encode('utf-8');return value

class FeedbackSave(StrictModel):
    draft_id: UUID
    base_version: StrictInt = Field(ge=0)
    payload: FeedbackInput

class FeedbackExact(StrictModel):
    version: StrictInt = Field(ge=1)
    content_hash: str = Field(pattern=r'^[a-f0-9]{64}$')

class FeedbackExport(FeedbackExact):
    format: Literal['markdown','json'] = 'markdown'

class SpaceState(StrictModel):
    enabled: bool = False
    theme: Literal['paper','sage','clay'] = 'paper'
    owned_ids: list[Literal['vase','books','print']] = Field(default_factory=lambda:['vase','books','print'],min_length=3,max_length=3)
    layout: list[Literal['vase','books','print']] = Field(default_factory=lambda:['books','vase','print'],min_length=3,max_length=3)
    @model_validator(mode='after')
    def complete(self):
        if set(self.owned_ids)!=set(self.layout) or len(set(self.owned_ids))!=3:
            raise ValueError('cosmetic layout')
        return self

class SpaceUpdate(StrictModel):
    base_version: StrictInt = Field(ge=0)
    state: SpaceState
