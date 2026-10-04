"""Explicit agreed goals and scoped longitudinal retrieval; no clinical skill activation."""
from typing import Annotated,Literal
from pydantic import Field,StringConstraints,field_validator
from .conversation_contracts import UID,Hash,Conversation,SendMessage
from scripts.m7_admission import Strict,key_closed
from .logical_day import OWNER_REFERENCE_TIMEZONE,validate_timezone

class GoalRef(Strict):
    id:UID
    revision:Annotated[int,Field(ge=1)]

class GoalCreate(Strict):
    operation_id:UID
    text:Annotated[str,StringConstraints(min_length=1,max_length=2000)]
    user_agreed:Literal[True]
    _text=field_validator('text')(SendMessage.bounded_text.__func__)

class GoalChange(Strict):
    operation_id:UID
    base_revision:Annotated[int,Field(ge=1)]
    text:Annotated[str,StringConstraints(min_length=1,max_length=2000)]|None=None
    state:Literal['ACTIVE','PAUSED','COMPLETED']|None=None
    user_agreed:Literal[True]
    @field_validator('text')
    @classmethod
    def optional_text(cls,v):return SendMessage.bounded_text.__func__(cls,v) if v is not None else None

class ReflectionGoal(Strict):
    id:UID
    text:Annotated[str,StringConstraints(min_length=1,max_length=2000)]
    state:Literal['ACTIVE','PAUSED','COMPLETED']
    revision:Annotated[int,Field(ge=1)]
    user_agreed:Literal[True]
    created_at:str
    updated_at:str
    completed_at:str|None
    synthetic:bool
    privacy_class:Literal['PRIVATE_PERSONAL']
    _dates=field_validator('created_at','updated_at')(Conversation.utc.__func__)
    @field_validator('completed_at')
    @classmethod
    def completion(cls,v):return Conversation.utc.__func__(cls,v) if v is not None else None

class MessageEdit(Strict):
    operation_id:UID
    base_conversation_revision:Annotated[int,Field(ge=1)]
    base_message_revision:Annotated[int,Field(ge=1)]
    text:Annotated[str,StringConstraints(min_length=1,max_length=12000)]
    _text=field_validator('text')(SendMessage.bounded_text.__func__)

class ContextRequest(Strict):
    operation_id:UID
    goal:GoalRef
    conversation_id:UID
    window_start:str|None=None
    window_end:str|None=None
    selection_type:Literal['LEGACY','GOAL_START','LAST_7_DAYS','LAST_30_DAYS','CUSTOM']='LEGACY'
    query:Annotated[str,StringConstraints(max_length=200)]=''
    token_budget:Annotated[int,Field(ge=128,le=12000)]=2000
    byte_budget:Annotated[int,Field(ge=512,le=48000)]=8000
    max_sources:Annotated[int,Field(ge=1,le=50)]=16
    prepare_synthetic_digests:bool=False
    timezone:Annotated[str,StringConstraints(min_length=1,max_length=100)]=OWNER_REFERENCE_TIMEZONE
    _timezone=field_validator('timezone')(validate_timezone)
    confirmed_memories:Annotated[list[GoalRef],Field(max_length=8)]=[]
    memory_scope:Literal['USER_CONFIRMED_EXPLICIT']|None=None
    @field_validator('window_start','window_end')
    @classmethod
    def date(cls,v):
        if v is None:return None
        from datetime import datetime
        Conversation.utc.__func__(cls,v)
        return datetime.fromisoformat(v.replace('Z','+00:00')).isoformat()

class Expansion(Strict):
    receipt_id:UID
    sources:Annotated[list[GoalRef],Field(min_length=1,max_length=8)]
    token_budget:Annotated[int,Field(ge=128,le=12000)]=1000
    byte_budget:Annotated[int,Field(ge=512,le=48000)]=4000

SKILLS={name:{'status':'CONTRACT_ONLY_NOT_ACTIVE','clinical':name in {'cbt_reflection','worry_rumination','sleep_review','nightmare_review','grounding'},'active':False} for name in ('core_reflection','deep_session','goal_setting','cbt_reflection','worry_rumination','sleep_review','nightmare_review','grounding','session_closure')}

def schemas():return {c.__name__:key_closed(c.model_json_schema()) for c in (GoalRef,GoalCreate,GoalChange,ReflectionGoal,MessageEdit,ContextRequest,Expansion,DerivedDigest,RetrievalReceipt)}

class DerivedDigest(Strict):
    id:UID
    kind:Literal['DAILY','GOAL']
    scope_key:str
    version:Annotated[int,Field(ge=1)]
    status:Literal['CURRENT','STALE']
    provenance:Literal['MODEL_DERIVED']
    synthetic:Literal[True]
    generator_version:Literal['SYNTHETIC_EXCERPT_V1']
    generator_kind:Literal['DETERMINISTIC_FIXTURE_NOT_LLM']
    goal:GoalRef|None
    timezone:str|None=None
    logical_local_date:str|None=None
    day_identity_version:Literal['LEGACY_UTC_V0','IANA_LOCAL_V1']='LEGACY_UTC_V0'
    sources:Annotated[list[GoalRef],Field(max_length=12)]
    window_start:str
    window_end:str
    text:str|None
    created_at:str
    _dates=field_validator('window_start','window_end','created_at')(Conversation.utc.__func__)

class DigestVersion(Strict):
    id:UID
    version:Annotated[int,Field(ge=1)]
    kind:Literal['DAILY','GOAL']

class ContextPartMeta(Strict):
    kind:Literal['GOAL_REVISION','CURRENT_TURN','GOAL_DIGEST','DAILY_DIGEST','FTS_RAW','FILTER_RAW','CONFIRMED_MEMORY']
    sources:list[GoalRef]
    digest_version:int|None
    artifact_id:UID|None
    memory_ref:GoalRef|None

class RetrievalReceipt(Strict):
    id:UID
    goal:GoalRef|None
    conversation_id:UID
    timezone:str=OWNER_REFERENCE_TIMEZONE
    window_start:str
    window_end:str
    sources:Annotated[list[GoalRef],Field(max_length=50)]
    digest_versions:list[DigestVersion]
    retrieval_method:Literal['GOAL_CURRENT_DIGEST_FTS5_FILTER_V1','FREE_RECENT_V1']
    token_budget:Annotated[int,Field(ge=128,le=12000)]
    byte_budget:Annotated[int,Field(ge=512,le=48000)]
    used_tokens_upper_bound:Annotated[int,Field(ge=0)]
    used_bytes_estimate:Annotated[int,Field(ge=0)]
    budget_scope:Literal['SERIALIZED_CONTEXT_PARTS_UTF8_JSON']
    token_estimator:Literal['UTF8_BYTE_UPPER_BOUND_V1_NOT_MODEL_TOKENIZER']
    confirmed_memory_refs:list[GoalRef]
    created_at:str
    raw_text_logged:Literal[False]
    parts_meta:list[ContextPartMeta]
    _dates=field_validator('window_start','window_end','created_at')(Conversation.utc.__func__)
