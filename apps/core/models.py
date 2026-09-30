"""M1 input contracts: original Unicode and explicit unknowns."""
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

Kind = Literal['inbox', 'daily', 'sleep', 'creative']
Rating = StrictInt | None
FIELDS = {'inbox': set(), 'daily': {'mood_rating', 'energy_rating'},
          'sleep': {'sleep_start_utc', 'wake_at_utc', 'sleep_quality'}, 'creative': {'creative_kind'}}
TYPED = set.union(*FIELDS.values())

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class EntryInput(StrictModel):
    type: Kind = 'inbox'
    raw_text: str = Field(min_length=1, max_length=100000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    timezone: str = 'Europe/Warsaw'
    occurred_at_utc: datetime | None = None
    local_date: date | None = None
    time_precision: Literal['instant', 'date', 'unknown'] = 'unknown'
    mood_rating: Rating = Field(default=None, ge=0, le=10)
    energy_rating: Rating = Field(default=None, ge=0, le=10)
    sleep_start_utc: datetime | None = None
    wake_at_utc: datetime | None = None
    sleep_quality: Rating = Field(default=None, ge=0, le=10)
    creative_kind: Literal['idea', 'scene', 'character', 'reference', 'other'] | None = None

    @field_validator('raw_text')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('blank')
        return value

    @field_validator('tags')
    @classmethod
    def valid_tags(cls, value):
        if len(set(value)) != len(value) or any(not x.strip() or len(x) > 64 for x in value):
            raise ValueError('tags')
        return value

    @field_validator('timezone')
    @classmethod
    def zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('zone') from None
        return value

    @field_validator('occurred_at_utc', 'sleep_start_utc', 'wake_at_utc', mode='before')
    @classmethod
    def no_epoch_coercion(cls, value):
        if value is not None and not isinstance(value, (str, datetime)):
            raise ValueError('offset-aware timestamp required')
        return value

    @field_validator('occurred_at_utc', 'sleep_start_utc', 'wake_at_utc')
    @classmethod
    def aware(cls, value):
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError('offset required')
            value = value.astimezone(timezone.utc)
        return value

    @model_validator(mode='after')
    def semantics(self):
        if (self.model_fields_set & TYPED) - FIELDS[self.type]:
            raise ValueError('foreign typed field')
        t, d = self.occurred_at_utc, self.local_date
        if self.type == 'sleep':
            if self.sleep_start_utc and self.wake_at_utc and self.wake_at_utc < self.sleep_start_utc:
                raise ValueError('negative interval')
            if self.wake_at_utc:
                if t != self.wake_at_utc:
                    raise ValueError('event must equal wake')
        if self.time_precision == 'instant':
            if t is None or d != t.astimezone(ZoneInfo(self.timezone)).date():
                raise ValueError('instant date')
        elif self.time_precision == 'date':
            if t is not None or d is None:
                raise ValueError('date precision')
        elif t is not None or d is not None:
            raise ValueError('unknown precision')
        return self

    def payload(self):
        return self.model_dump(mode='json', exclude=TYPED - FIELDS[self.type])

class Create(StrictModel):
    operation_id: UUID
    entry_id: UUID
    base_revision: Literal[0]
    payload: EntryInput

class Patch(StrictModel):
    operation_id: UUID
    base_revision: int = Field(ge=1, strict=True)
    changes: dict
    confirm_type_change: bool = False

class Delete(StrictModel):
    operation_id: UUID
    base_revision: int = Field(ge=1, strict=True)

class Selector(StrictModel):
    ids: list[UUID] | None = Field(default=None, max_length=1000)
    types: list[Kind] | None = None
    date_from: date | None = None
    date_to: date | None = None
    include_history: bool = False
    @model_validator(mode='after')
    def explicit(self):
        if not self.ids and not self.types and not self.date_from and not self.date_to:
            raise ValueError('explicit selector required')
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError('date range')
        return self

class Export(StrictModel):
    plan_id: UUID
    format: Literal['json', 'markdown']

class Unlock(StrictModel):
    code: str = Field(min_length=1, max_length=64)


class EntryOutput(EntryInput):
    """Server-managed fields shared with the generated TypeScript read contract."""
    id: UUID
    owner_id: UUID
    revision: StrictInt = Field(ge=1)
    created_at_utc: datetime
    updated_at_utc: datetime
    schema_version: Literal[1]
    privacy_class: Literal['PRIVATE_PERSONAL']
    provenance_type: Literal['USER_REPORTED']
    reported_interval_seconds: float | None = Field(default=None, ge=0)


class EntryRevisionOutput(EntryOutput):
    # Unknown only for already existing pre-correction development history.
    recorded_at_utc: datetime | None = None

    @field_validator('recorded_at_utc')
    @classmethod
    def recorded_aware(cls, value):
        return cls.aware(value)


class EntryPage(StrictModel):
    items: list[EntryOutput]
    next_cursor: str | None


class RevisionPage(StrictModel):
    items: list[EntryRevisionOutput]
    next_after: int | None


class Receipt(StrictModel):
    entry_id: UUID
    operation_id: UUID
    revision: StrictInt = Field(ge=1)
    result_code: Literal['MAC_SAVED', 'DELETED']
