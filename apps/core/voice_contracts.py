"""Strict metadata and commands: no paths, tools, destinations or credentials in payloads."""
from datetime import datetime, date
from typing import Literal
from uuid import UUID
from pydantic import Field, StrictInt, field_validator
from .models import StrictModel, EntryInput
from .audio_format import MAX_AUDIO, CHUNK_SIZE

class AudioBegin(StrictModel):
    audio_id: UUID
    operation_id: UUID
    content_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    byte_size: StrictInt = Field(ge=44,le=MAX_AUDIO)
    mime: Literal['audio/wav']
    created_at_utc: datetime
    timezone: str = 'Europe/Warsaw'
    local_date: date | None = None
    linked_entry_id: UUID | None = None
    @field_validator('created_at_utc')
    @classmethod
    def utc(cls,v):
        if v.tzinfo is None or v.utcoffset().total_seconds()!=0: raise ValueError('UTC required')
        return v
    @field_validator('timezone')
    @classmethod
    def zone(cls,v): return EntryInput.zone(v)

class AudioChunk(StrictModel):
    index: StrictInt = Field(ge=0,lt=32)
    content_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    data: str = Field(min_length=4,max_length=4*((CHUNK_SIZE+2)//3))

class VoiceEmpty(StrictModel):
    pass
class ASRRequest(StrictModel):
    mode: Literal['DISABLED','FAKE'] = 'DISABLED'
    language: Literal['uk'] = 'uk'
class TranscriptEdit(StrictModel):
    revision: StrictInt = Field(ge=1)
    text: str = Field(max_length=100000)
class TranscriptConfirm(StrictModel):
    revision: StrictInt = Field(ge=1)
    operation_id: UUID
    entry_id: UUID
    base_revision: StrictInt = Field(ge=0)
    retention: Literal['KEEP','DELETE_AFTER_CONFIRM']
class AudioDelete(StrictModel):
    confirm: Literal[True]
