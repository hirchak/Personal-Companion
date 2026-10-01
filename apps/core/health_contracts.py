"""M6 allowlisted, bounded data-only bridge payload. Health is not a journal/AI input."""
from datetime import datetime
from typing import Literal, Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
Kind=Literal['sleep','steps','exercise']
class Stage(Strict):
    start:str
    end:str
    stage:int=Field(ge=0,le=2147483647)
    classification:Literal['SDK_KNOWN','SOURCE_UNKNOWN']
    @model_validator(mode='after')
    def times(self):
        if instant(self.end)<=instant(self.start):raise ValueError('TIME_RANGE')
        return self
class SleepFields(Strict):
    stages:list[Stage]=Field(max_length=500)
    stages_state:Literal['VALUE','MISSING']
    @model_validator(mode='after')
    def availability(self):
        if bool(self.stages)!=(self.stages_state=='VALUE'):raise ValueError('MISSING_IS_NOT_ZERO')
        return self
class StepsFields(Strict):
    count:int=Field(ge=0,le=1000000000)
    unit:Literal['count']
class ExerciseFields(Strict):
    exercise_type:int=Field(ge=0,le=2147483647)
    classification:Literal['SOURCE_CODE']
def instant(s):
    if not isinstance(s,str) or len(s)>40:raise ValueError('TIME_INVALID')
    result=datetime.fromisoformat(s.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('TIME_OFFSET_REQUIRED')
    return result
class HealthRecord(Strict):
    type:Kind
    source_id:str=Field(min_length=1,max_length=256)
    origin:str=Field(max_length=256)
    status:Literal['VALUE','SOURCE_DELETED','UNKNOWN']
    modified:str|None=None
    start:str|None=None
    end:str|None=None
    start_offset:int|None=Field(default=None,ge=-64800,le=64800)
    end_offset:int|None=Field(default=None,ge=-64800,le=64800)
    fields:SleepFields|StepsFields|ExerciseFields|None=None
    @model_validator(mode='after')
    def typed(self):
        if self.status!='SOURCE_DELETED':
            if not self.origin or not self.start or not self.end or not self.modified:raise ValueError('RECORD_REQUIRED')
            if instant(self.end)<=instant(self.start):raise ValueError('TIME_RANGE')
            instant(self.modified)
            expected={'sleep':SleepFields,'steps':StepsFields,'exercise':ExerciseFields}[self.type]
            if not isinstance(self.fields,expected):raise ValueError('TYPE_FIELDS')
            if isinstance(self.fields,SleepFields):
                for stage in self.fields.stages:
                    if instant(stage.start)<instant(self.start) or instant(stage.end)>instant(self.end):raise ValueError('STAGE_RANGE')
        elif any(x is not None for x in (self.fields,self.start,self.end,self.modified,self.start_offset,self.end_offset)):
            raise ValueError('TOMBSTONE_PAYLOAD')
        return self
class Scope(Strict):
    type:Kind
    permission:Literal['GRANTED','PERMISSION_DENIED','READ_FAILED','NOT_AVAILABLE','NOT_REQUESTED']
    mode:Literal['INCREMENTAL','INITIAL_OR_RECOVERY']
    records:list[HealthRecord]=Field(max_length=1000)
    @model_validator(mode='after')
    def consistent(self):
        if self.permission!='GRANTED' and self.records:raise ValueError('UNAUTHORIZED_RECORDS')
        seen=set()
        for r in self.records:
            if r.type!=self.type or r.source_id in seen:raise ValueError('DUPLICATE_OR_TYPE')
            seen.add(r.source_id)
        return self
class HealthBatch(Strict):
    schema_version:Literal[1]
    source_system:Literal['HEALTH_CONNECT']
    epoch:str
    sequence:int=Field(ge=1,le=9007199254740991)
    scopes:list[Scope]=Field(min_length=3,max_length=3)
    @field_validator('schema_version',mode='before')
    @classmethod
    def exact_version(cls,v):
        if type(v) is not int:raise ValueError('SCHEMA_VERSION_INTEGER_REQUIRED')
        return v
    @field_validator('epoch')
    @classmethod
    def uuid(cls,v):UUID(v);return v
    @model_validator(mode='after')
    def scopes_unique(self):
        if {s.type for s in self.scopes}!={'sleep','steps','exercise'}:raise ValueError('SCOPE_SET')
        return self
class HealthApply(Strict):
    batch:HealthBatch
    generation:str
    reconnect:bool=False
class HealthAction(Strict):
    generation:str
