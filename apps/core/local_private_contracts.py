"""Distinct production private requests; synthetic acknowledgement cannot authorize private transmission."""
from typing import Annotated,Literal
from pydantic import Field,StringConstraints,field_validator
from scripts.m7_admission import Strict
from .conversation_contracts import UID,Hash,VoiceSource,SendMessage
from .conversation_runtime_contracts import ProviderPayload,ProviderContextPart,ConversationRequest
from .deep_session_contracts import ContextBinding,ContextSelection

class PrivateInferenceStart(Strict):
 operation_id:UID
 base_revision:Annotated[int,Field(ge=1)]
 text:Annotated[str,StringConstraints(min_length=1,max_length=12000)]
 purpose:Literal['REFLECT','GOAL_PROPOSAL','CLOSURE']='REFLECT'
 owner_approved_external_text:Literal[True]
 source_reference:VoiceSource|None=None
 context_binding:ContextBinding|None=None
 @field_validator('owner_approved_external_text',mode='before')
 @classmethod
 def exact_bool(cls,v):
  if v is not True:raise ValueError('Explicit owner acknowledgement required')
  return v
 _text=field_validator('text')(SendMessage.bounded_text.__func__)

class JournalReference(Strict):
 id:UID
 revision:Annotated[int,Field(ge=1)]

class PrivateContextPreview(Strict):
 operation_id:UID
 base_revision:Annotated[int,Field(ge=1)]
 text:Annotated[str,StringConstraints(min_length=1,max_length=12000)]
 purpose:Literal['REFLECT','GOAL_PROPOSAL','CLOSURE']='REFLECT'
 selection:ContextSelection=Field(default_factory=ContextSelection)
 journal_entries:Annotated[list[JournalReference],Field(max_length=10)]=Field(default_factory=list)
 _text=field_validator('text')(SendMessage.bounded_text.__func__)

class PrivateProviderContextPart(ProviderContextPart):
 kind:Literal['GOAL_REVISION','CURRENT_TURN','FTS_RAW','FILTER_RAW','JOURNAL_SELECTED']

class PrivateProviderPayload(ProviderPayload):
 synthetic:Literal[False]
 context:list[PrivateProviderContextPart]

class PrivateConversationRequest(ConversationRequest):
 schema_version:Literal[2]
 synthetic:Literal[False]
 consent_scope:Literal['M8D_THIS_OWNER_EXACT_APPROVED_PRIVATE_CONTEXT']
 payload:PrivateProviderPayload
