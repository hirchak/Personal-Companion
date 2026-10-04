"""Neutral reflection records; hypotheses never grant clinical or user authority."""
from typing import Annotated, Literal
from pydantic import Field, StringConstraints, field_validator, model_validator
from scripts.m7_admission import Strict, key_closed
from .conversation_contracts import UID, Hash, SendMessage, Conversation
from .reflection_contracts import GoalRef
from .logical_day import validate_timezone

Text = Annotated[str, StringConstraints(min_length=1, max_length=800)]
class MapItem(Strict):
    id: UID
    kind: Literal['OBSERVATION','FEELING','ACTION','HYPOTHESIS','QUESTION','CHANGE','OPTION','TAKEAWAY','UNRESOLVED']
    text: Text
    provenance: Literal['USER_STATED','USER_CONFIRMED','MODEL_HYPOTHESIS','MODEL_DERIVED_SUMMARY','COMPUTED']
    sources: Annotated[list[GoalRef], Field(min_length=1,max_length=8)]
    state: Literal['CURRENT','REJECTED','IRRELEVANT','STALE'] = 'CURRENT'
    _text = field_validator('text')(SendMessage.bounded_text.__func__)
    @model_validator(mode='after')
    def authority(self):
        if self.kind=='HYPOTHESIS' and self.provenance!='MODEL_HYPOTHESIS':raise ValueError('Hypothesis provenance required')
        return self

class MapCandidateItem(Strict):
    kind: Literal['OBSERVATION','FEELING','ACTION','HYPOTHESIS','QUESTION','CHANGE','OPTION','TAKEAWAY','UNRESOLVED']
    text: Text
    provenance: Literal['USER_STATED','MODEL_HYPOTHESIS','MODEL_DERIVED_SUMMARY']
    source_refs: Annotated[list[Annotated[str,StringConstraints(pattern=r'^s[0-9]{1,2}$')]], Field(min_length=1,max_length=8)]
    _text = field_validator('text')(SendMessage.bounded_text.__func__)
    @model_validator(mode='after')
    def authority(self):
        if (self.kind=='HYPOTHESIS')!=(self.provenance=='MODEL_HYPOTHESIS'):raise ValueError('Hypothesis provenance mismatch')
        if self.provenance=='USER_STATED' and self.kind not in {'OBSERVATION','FEELING','ACTION'}:raise ValueError('Only literal user statements allowed')
        return self

class WorkingMapCandidate(Strict):
    items: Annotated[list[MapCandidateItem], Field(max_length=8)]

class WorkingMap(Strict):
    schema_version: Literal[1] = 1
    goal: GoalRef
    version: Annotated[int,Field(ge=1)]
    conversation_id: UID
    items: Annotated[list[MapItem],Field(max_length=40)]
    created_at: str
    provider_model: str
    provider_route: str
    skills: list[dict]
    request_hash: Hash
    provenance: Literal['SOURCE_BOUND_NEUTRAL_REFLECTION'] = 'SOURCE_BOUND_NEUTRAL_REFLECTION'
    _date = field_validator('created_at')(Conversation.utc.__func__)

class SessionAction(Strict):
    operation_id: UID
    base_revision: Annotated[int,Field(ge=1)]
    action: Literal['focus','phase','pause','resume','close']
    focus: Text|None = None
    phase: Literal['AGREE_FOCUS','EXPLORE','SYNTHESIZE','NEXT_STEP','CLOSING']|None = None

class MapAction(Strict):
    operation_id: UID
    base_version: Annotated[int,Field(ge=1)]
    item_id: UID
    action: Literal['reject','irrelevant','confirm','clarify']
    text: Text|None = None
    user_confirmed: Literal[True]

class ContextSelection(Strict):
    type: Literal['GOAL_START','LAST_7_DAYS','LAST_30_DAYS','CUSTOM'] = 'GOAL_START'
    timezone: Annotated[str,StringConstraints(min_length=1,max_length=100)] = 'Europe/Warsaw'
    window_start: str|None = None
    window_end: str|None = None
    _timezone = field_validator('timezone')(validate_timezone)
    @field_validator('window_start','window_end')
    @classmethod
    def date(cls,v):
        if v is None:return None
        from datetime import datetime
        Conversation.utc.__func__(cls,v)
        return datetime.fromisoformat(v.replace('Z','+00:00')).isoformat()
    @model_validator(mode='after')
    def range(self):
        if self.type=='CUSTOM':
            if not self.window_start or not self.window_end or self.window_start>self.window_end:raise ValueError('Explicit ordered custom range required')
        elif self.window_start or self.window_end:raise ValueError('Preset range cannot override timestamps')
        return self

class DeepContextPreview(Strict):
    operation_id: UID
    base_revision: Annotated[int,Field(ge=1)]
    text: Annotated[str,StringConstraints(min_length=1,max_length=12000)]
    selection: ContextSelection
    _text = field_validator('text')(SendMessage.bounded_text.__func__)

class ContextBinding(Strict):
    receipt_id: UID
    context_hash: Hash
    preview_hash: Hash

class DeepSession(Strict):
    conversation_id: UID
    goal: GoalRef
    revision: Annotated[int,Field(ge=1)] = 1
    focus: Annotated[str,StringConstraints(max_length=800)] = ''
    phase: Literal['OPEN','AGREE_FOCUS','EXPLORE','SYNTHESIZE','NEXT_STEP','CLOSING','PAUSED','CLOSED'] = 'OPEN'
    created_at: str
    updated_at: str
    closed_at: str|None = None
    closure_job_id: UID|None = None
    _date = field_validator('created_at','updated_at')(Conversation.utc.__func__)

def schemas():
    return {c.__name__:key_closed(c.model_json_schema()) for c in (WorkingMap,WorkingMapCandidate,MapAction,SessionAction,ContextSelection,DeepContextPreview,ContextBinding,DeepSession)}
