"""Finite plain-data packages and explicit session commands. No workflow expressions."""
from __future__ import annotations
import json
import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field, StringConstraints, model_validator, field_validator
from scripts.m7_admission import Strict, key_closed

UID = Annotated[UUID, Field(strict=False)]
Text = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
Id = Annotated[str, StringConstraints(pattern=r'^[a-z][a-z0-9_-]{0,63}$')]
ModuleId = Annotated[str, StringConstraints(pattern=r'^(?:synthetic:)?[a-z][a-z0-9_]{0,63}$')]
Hash = Annotated[str, StringConstraints(pattern=r'^[0-9a-f]{64}$')]


def plain(value: str):
    value.encode('utf-8')
    if not value.strip():
        raise ValueError('Nonblank text required')
    if re.search(r'<[^>]*>|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', value):
        raise ValueError('Plain Unicode text required')
    return value


class Choice(Strict):
    id: Id
    label: Text
    _plain = field_validator('label')(plain)


class Step(Strict):
    id: Id
    kind: Literal['information', 'acknowledgement', 'short_text', 'long_text', 'single_choice', 'completion']
    text: Text
    optional: bool
    next_step: Id | None
    choices: Annotated[list[Choice], Field(max_length=8)] = []
    _plain = field_validator('text')(plain)

    @model_validator(mode='after')
    def consistent(self):
        if (self.kind == 'single_choice') != bool(self.choices):
            raise ValueError('Choices required only for single choice')
        if len({c.id for c in self.choices}) != len(self.choices):
            raise ValueError('Duplicate choices')
        if self.kind == 'completion' and self.optional:
            raise ValueError('Completion cannot be optional')
        return self


class Package(Strict):
    schema_version: Literal[1]
    module_id: ModuleId
    module_version: Annotated[str, StringConstraints(pattern=r'^\d+\.\d+\.\d+$')]
    content_hash: Hash
    title: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    description: Text
    entry_step: Id
    steps: Annotated[list[Step], Field(min_length=2, max_length=16)]
    provenance: Literal['ORIGINAL_SYNTHETIC', 'REVIEWED_PRODUCTION']
    admission_reference: Text
    _plain = field_validator('title', 'description', 'admission_reference')(plain)

    @model_validator(mode='after')
    def finite_linear(self):
        if len({s.id for s in self.steps}) != len(self.steps) or self.entry_step != self.steps[0].id:
            raise ValueError('Duplicate or missing entry step')
        for i, step in enumerate(self.steps):
            expected = self.steps[i + 1].id if i + 1 < len(self.steps) else None
            if step.next_step != expected or (step.kind == 'completion') != (i == len(self.steps) - 1):
                raise ValueError('Only finite linear sequence with terminal completion supported')
        if self.module_id.startswith('synthetic:') != (self.provenance == 'ORIGINAL_SYNTHETIC'):
            raise ValueError('Namespace/provenance mismatch')
        return self


class RuntimeReceipt(Strict):
    schema_version: Literal[1]
    kind: Literal['SYNTHETIC_ENGINEERING_ONLY', 'PRODUCTION']
    module_id: ModuleId
    module_version: Text
    content_hash: Hash
    admission_identity: Hash
    technical_identity: Hash
    technical_evidence: Text
    review_scope: Text
    owner_activation_decision: Text
    activation_epoch: Annotated[int, Field(ge=0)]
    created_at: Text
    expires_at: Text | None
    re_review_status: Literal['CURRENT', 'STALE']
    approval_identity: Hash | None
    rights_hash: Hash | None
    source_claim_identity: Hash | None

    @model_validator(mode='after')
    def kind_boundary(self):
        synthetic = self.module_id.startswith('synthetic:')
        if synthetic != (self.kind == 'SYNTHETIC_ENGINEERING_ONLY'):
            raise ValueError('Receipt namespace mismatch')
        if self.kind == 'PRODUCTION' and (any(v is None for v in (self.approval_identity, self.rights_hash, self.source_claim_identity))
                or self.owner_activation_decision != 'OWNER_AUTHORIZED_FOR_DEFINED_SCOPE'):
            raise ValueError('Exact production gates required')
        return self

    @field_validator('created_at', 'expires_at')
    @classmethod
    def utc(cls, value):
        if value is not None:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
                raise ValueError('UTC required')
        return value


class Start(Strict):
    operation_id: UID
    module_id: ModuleId
    module_version: Text
    content_hash: Hash


class Action(Strict):
    operation_id: UID
    base_revision: Annotated[int, Field(ge=1)]
    action: Literal['save', 'next', 'pause', 'resume', 'skip', 'stop', 'complete', 'delete']
    step_id: Id | None = None
    response: Annotated[str, StringConstraints(max_length=12000)] | bool | None = None

    @field_validator('response')
    @classmethod
    def unicode(cls, value):
        if isinstance(value, str):
            value.encode('utf-8')
            if len(value.encode('utf-8')) > 48000 or '\x00' in value:
                raise ValueError('Response bound exceeded')
        return value

    @model_validator(mode='after')
    def bounded_command(self):
        if self.action != 'save' and self.response is not None:
            raise ValueError('Only explicit save may contain response')
        if self.action in {'save', 'next', 'skip', 'complete'} and self.step_id is None:
            raise ValueError('Exact step required')
        return self


class UserResponse(Strict):
    value: str | bool
    revision: Annotated[int, Field(ge=1)]
    updated_utc: Text


class Session(Strict):
    schema_version: Literal[1]
    id: UID
    module_id: ModuleId
    module_version: Text
    package_hash: Hash
    package_schema_version: Literal[1]
    title: Text
    provenance: Literal['ORIGINAL_SYNTHETIC', 'REVIEWED_PRODUCTION']
    admission_binding: Hash
    activation_epoch: Annotated[int, Field(ge=0)]
    started_utc: Text
    updated_utc: Text
    current_step: Id
    state: Literal['ACTIVE', 'PAUSED', 'COMPLETED', 'STOPPED', 'BLOCKED_BY_ADMISSION']
    revision: Annotated[int, Field(ge=1)]
    responses: dict[Id, UserResponse]
    skipped_steps: list[Id]
    completed_utc: Text | None
    stopped_utc: Text | None
    blocked_reason: Text | None

    @field_validator('started_utc', 'updated_utc', 'completed_utc', 'stopped_utc')
    @classmethod
    def utc(cls, value):
        if value is not None:
            d = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if d.utcoffset() is None or d.utcoffset().total_seconds() != 0:
                raise ValueError('UTC required')
        return value

    @model_validator(mode='after')
    def coherent(self):
        if (self.state == 'COMPLETED') != (self.completed_utc is not None):
            raise ValueError('Completion time/state mismatch')
        if (self.state == 'STOPPED') != (self.stopped_utc is not None):
            raise ValueError('Stop time/state mismatch')
        if self.module_id.startswith('synthetic:') != (self.provenance == 'ORIGINAL_SYNTHETIC'):
            raise ValueError('Session provenance mismatch')
        return self


def schema():
    return {c.__name__: key_closed(c.model_json_schema()) for c in
            (Package, RuntimeReceipt, Start, Action, Session)}
