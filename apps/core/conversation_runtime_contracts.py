"""Synthetic-only inference requests, inert model candidates and metadata receipts."""
from typing import Annotated,Literal
from pydantic import Field,StringConstraints,field_validator
from scripts.m7_admission import Strict,key_closed
from .conversation_contracts import UID,Hash,SendMessage,VoiceSource
from .deep_session_contracts import WorkingMapCandidate,ContextBinding

class SkillBinding(Strict):
    skill_id:Literal['core_reflection','deep_session','goal_setting','session_closure']
    version:str
    content_hash:Hash

class ClosureCandidate(Strict):
    discussed:Annotated[list[Annotated[str,StringConstraints(min_length=1,max_length=600)]],Field(max_length=4)]
    clearer:Annotated[str,StringConstraints(max_length=1000)]
    unresolved:Annotated[str,StringConstraints(max_length=600)]
    possible_steps:Annotated[list[Annotated[str,StringConstraints(min_length=1,max_length=600)]],Field(max_length=3)]

class ConversationCandidate(Strict):
    assistant_text:Annotated[str,StringConstraints(min_length=1,max_length=4000)]
    source_refs:Annotated[list[Annotated[str,StringConstraints(pattern=r'^s[0-9]{1,2}$')]],Field(max_length=50)]
    goal_suggestion:Annotated[str,StringConstraints(min_length=1,max_length=1000)]|None
    closure:ClosureCandidate|None
    topics:Annotated[list[Literal['work','relationship','sleep','daily_event','decision','self_reflection']],Field(max_length=5)]
    working_map:WorkingMapCandidate|None=None
    _text=field_validator('assistant_text')(SendMessage.bounded_text.__func__)

class InferenceStart(Strict):
    operation_id:UID
    base_revision:Annotated[int,Field(ge=1)]
    text:Annotated[str,StringConstraints(min_length=1,max_length=12000)]
    purpose:Literal['REFLECT','GOAL_PROPOSAL','CLOSURE']='REFLECT'
    synthetic_test_ack:Literal[True]
    source_reference:VoiceSource|None=None
    context_binding:ContextBinding|None=None
    _text=field_validator('text')(SendMessage.bounded_text.__func__)

class InferenceAction(Strict):
    operation_id:UID
    base_revision:Annotated[int,Field(ge=1)]
    action:Literal['cancel','retry']

class JournalPointPreview(Strict):
    message_id:UID
    source_revision:Annotated[int,Field(ge=1)]

class JournalPointConfirm(JournalPointPreview):
    operation_id:UID
    preview_hash:Hash
    user_confirmed:Literal[True]

class ProviderContextPart(Strict):
    kind:Literal['GOAL_REVISION','CURRENT_TURN','GOAL_DIGEST','DAILY_DIGEST','FTS_RAW','FILTER_RAW','CONFIRMED_MEMORY']
    text:str
    source_refs:Annotated[list[str],Field(max_length=50)]

class RuntimeSkill(Strict):
    skill_id:Literal['core_reflection','deep_session','goal_setting','session_closure']
    version:str
    content_hash:Hash
    instructions:str

class ProviderMapItem(Strict):
    kind:str
    text:str
    provenance:str
    state:str
    source_refs:list[str]

class ProviderPriorClosure(Strict):
    closure:ClosureCandidate
    source_refs:list[str]

class ProviderReflectionState(Strict):
    focus:str
    phase:str
    map_version:int
    items:list[ProviderMapItem]
    prior_closures:list[ProviderPriorClosure]

class ProviderPayload(Strict):
    mode:Literal['FREE','DEEP']
    purpose:Literal['REFLECT','GOAL_PROPOSAL','CLOSURE']
    synthetic:Literal[True]
    language:Literal['uk']
    address_form:Literal['FORMAL_VY']='FORMAL_VY'
    skills:list[RuntimeSkill]
    context:list[ProviderContextPart]
    current_message_ref:str
    source_refs_allowed:list[str]
    goal_revision:int|None
    tool_permissions:Annotated[list[str],Field(max_length=0)]
    controller_frame_hash:Hash
    reflection_state:ProviderReflectionState|None=None

class ConversationRequest(Strict):
    schema_version:Literal[1]
    request_id:UID
    mode:Literal['FREE','DEEP']
    purpose:Literal['REFLECT','GOAL_PROPOSAL','CLOSURE']
    selected_skills:list[SkillBinding]
    context_hash:Hash
    retrieval_receipt_id:UID
    provider_route:Literal['CODEX_SUBSCRIPTION','MINIMAX_TOKEN_PLAN','EXISTING_LOCAL','OFFLINE_FIXTURE']
    provider_model:str
    provider_effort:str='low'
    provider_profile:str='M7C_COMPAT_LOW'
    selection_type:str='GOAL_START'
    selection_timezone:str='Europe/Warsaw'
    selected_window_start:str|None=None
    selected_window_end:str|None=None
    selected_receipt_id:UID|None=None
    selected_context_hash:Hash|None=None
    map_snapshot_hash:Hash|None=None
    consent_scope:Literal['M7C_OWNER_AUTHORIZED_ORIGINAL_SYNTHETIC_ONLY','M7D_OWNER_AUTHORIZED_ORIGINAL_SYNTHETIC_ONLY']
    synthetic:Literal[True]
    clinical_active:Literal[0]
    tools:Annotated[list[str],Field(max_length=0)]
    timeout_seconds:Annotated[int,Field(ge=1,le=120)]
    input_byte_budget:Annotated[int,Field(ge=512,le=64000)]
    response_schema:Literal['M7C_CONVERSATION_CANDIDATE_V1']
    payload:ProviderPayload

def schemas():return {c.__name__:key_closed(c.model_json_schema()) for c in (ConversationCandidate,ConversationRequest,InferenceStart,InferenceAction,ClosureCandidate,SkillBinding,JournalPointPreview,JournalPointConfirm)}
