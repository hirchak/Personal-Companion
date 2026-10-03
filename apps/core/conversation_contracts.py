"""Strict local conversations. User text is private data, never executable authority."""
from datetime import datetime
from typing import Annotated,Literal
from uuid import UUID
from pydantic import Field,StringConstraints,field_validator
from scripts.m7_admission import Strict,key_closed

UID=Annotated[UUID,Field(strict=False)]
Hash=Annotated[str,StringConstraints(pattern=r'^[0-9a-f]{64}$')]

class VoiceSource(Strict):
    kind: Literal['VOICE_TRANSCRIPT']
    transcript_id: UID
    revision: Annotated[int,Field(ge=1)]
    audio_hash: Hash
    text_hash: Hash

class GoalBinding(Strict):
    id: UID
    revision: Annotated[int,Field(ge=1)]

class NewConversation(Strict):
    operation_id: UID
    goal_id: UID | None = None
    goal_revision: Annotated[int, Field(ge=1)] | None = None

class SendMessage(Strict):
    operation_id: UID
    base_revision: Annotated[int,Field(ge=1)]
    text: Annotated[str,StringConstraints(min_length=1,max_length=12000)]
    source_reference: VoiceSource|None=None
    @field_validator('text')
    @classmethod
    def bounded_text(cls,v):
        v.encode('utf-8')
        if not v.strip() or '\x00' in v or len(v.encode('utf-8'))>48000:raise ValueError('Bounded nonblank Unicode required')
        return v

class ConversationAction(Strict):
    operation_id: UID
    base_revision: Annotated[int,Field(ge=1)]
    action: Literal['archive','unarchive','delete']

class CandidateResponse(Strict):
    role: Literal['ASSISTANT']
    text: Annotated[str,StringConstraints(min_length=1,max_length=12000)]
    provenance: Literal['MOCK_SYNTHETIC']
    synthetic: Literal[True]
    _text=field_validator('text')(SendMessage.bounded_text.__func__)

class Conversation(Strict):
    schema_version: Literal[1]
    id: UID
    title: Annotated[str,StringConstraints(min_length=1,max_length=160)]
    state: Literal['ACTIVE','ARCHIVED']
    revision: Annotated[int,Field(ge=1)]
    created_utc: str
    updated_utc: str
    provenance: Literal['ORIGINAL_SYNTHETIC','USER_LOCAL']
    synthetic: bool
    privacy_class: Literal['PRIVATE_PERSONAL']
    mode: Literal['FREE','DEEP'] = 'FREE'
    goal_binding: GoalBinding | None = None
    @field_validator('created_utc','updated_utc')
    @classmethod
    def utc(cls,v):
        d=datetime.fromisoformat(v.replace('Z','+00:00'))
        if d.utcoffset() is None or d.utcoffset().total_seconds()!=0:raise ValueError('UTC required')
        return v

class Message(Strict):
    schema_version: Literal[1]
    id: UID
    conversation_id: UID
    role: Literal['USER','ASSISTANT']
    raw_text: Annotated[str,StringConstraints(min_length=1,max_length=12000)]
    created_utc: str
    revision: Annotated[int,Field(ge=1)]
    provenance: Literal['USER_AUTHORED','MOCK_SYNTHETIC']
    source_reference: VoiceSource|None
    source_message_id: UID|None
    synthetic: bool
    privacy_class: Literal['PRIVATE_PERSONAL']
    _text=field_validator('raw_text')(SendMessage.bounded_text.__func__)
    _date=field_validator('created_utc')(Conversation.utc.__func__)


def schemas():
    return {c.__name__:key_closed(c.model_json_schema()) for c in (Conversation,Message,NewConversation,SendMessage,ConversationAction)}
