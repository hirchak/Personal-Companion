"""M3 data-only contracts. Every output key is allowlisted; no tools or free-form profiles."""
from typing import Literal
from uuid import UUID
from pydantic import Field, StrictInt, model_validator, field_validator
from .models import StrictModel, Kind, EntryInput

Task = Literal['capture_classify', 'organize_selected', 'memory_propose']
ProviderId = Literal['mock', 'codex-disabled']
Tag = Literal['нотатка', 'ідея', 'план', 'щоденник']
Preference = Literal['concise', 'source_references']
PREFERENCES = {'concise': 'Показувати короткі відповіді.', 'source_references': 'Показувати посилання на вибрані записи.'}

class Ref(StrictModel):
    id: UUID
    revision: StrictInt = Field(ge=1)

class PreviewRequest(StrictModel):
    task: Task
    provider: ProviderId = 'mock'
    entries: list[Ref] = Field(min_length=1, max_length=20)
    memories: list[Ref] = Field(default_factory=list, max_length=10)
    @model_validator(mode='after')
    def distinct(self):
        for refs in (self.entries, self.memories):
            if len({r.id for r in refs}) != len(refs): raise ValueError('duplicate refs')
        if self.task == 'capture_classify' and len(self.entries) != 1: raise ValueError('one source')
        return self

class Approval(StrictModel):
    context_hash: str = Field(pattern=r'^[a-f0-9]{64}$')

class Enqueue(StrictModel):
    consent_id: UUID
    operation_id: UUID

class RuntimeMode(StrictModel):
    mode: Literal['OFF', 'MOCK']

class Empty(StrictModel):
    pass

class Classification(StrictModel):
    task: Literal['capture_classify']
    sources: list[Ref] = Field(min_length=1, max_length=1)
    type: Kind
    tags: list[Tag] = Field(max_length=4)
    reason: Literal['selected_entry']
    @model_validator(mode='after')
    def unique(self):
        if len(set(self.tags)) != len(self.tags): raise ValueError('duplicate tags')
        return self

class Organized(StrictModel):
    task: Literal['organize_selected']
    sources: list[Ref] = Field(min_length=1, max_length=20)
    groups: list[Kind] = Field(min_length=1, max_length=4)
    reason: Literal['explicit_selection']

class MemoryProposal(StrictModel):
    task: Literal['memory_propose']
    sources: list[Ref] = Field(min_length=1, max_length=20)
    preference: Preference
    reason: Literal['review_preference']

OUTPUTS = {'capture_classify': Classification, 'organize_selected': Organized, 'memory_propose': MemoryProposal}

class MemoryCreate(StrictModel):
    scope: Literal['preferences', 'organization'] = 'preferences'
    content: str = Field(min_length=1, max_length=500)
    expires_at: float | None = Field(default=None, gt=0)
    @field_validator('content')
    @classmethod
    def valid_content(cls,value): return EntryInput.nonblank(value)

class MemoryChange(StrictModel):
    revision: StrictInt = Field(ge=1)
    action: Literal['confirm', 'edit', 'reject', 'delete']
    content: str | None = Field(default=None, min_length=1, max_length=500)
    @field_validator('content')
    @classmethod
    def valid_content(cls,value): return EntryInput.nonblank(value) if value is not None else value
    @model_validator(mode='after')
    def edit_only(self):
        if (self.action == 'edit') != (self.content is not None): raise ValueError('edit content')
        return self

class SuggestionChange(StrictModel):
    action: Literal['accept', 'edit', 'reject', 'ignore', 'undo']
    type: Kind | None = None
    tags: list[Tag] | None = Field(default=None, max_length=4)
    confirm_type_change: bool = False
    @model_validator(mode='after')
    def edit_only(self):
        if self.action == 'edit':
            if self.type is None or self.tags is None: raise ValueError('explicit edited structure')
        elif self.type is not None or self.tags is not None: raise ValueError('edit only')
        return self
