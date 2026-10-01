"""Narrow data-only provider interface. Codex is a disabled candidate, never a child process."""
from dataclasses import dataclass, asdict
from typing import Protocol
from threading import Event
from .storage import SafeError, encode
from .ai_contracts import Task

@dataclass(frozen=True)
class ProviderMetadata:
    id: str
    model: str | None
    version: str
    auth_mode: str
    destination: str
    availability: str
    quota: str
    retention_note: str
    tasks: tuple = ('capture_classify', 'organize_selected', 'memory_propose')
    scopes: tuple = ('selected_journal', 'confirmed_preferences')
    capabilities: tuple = ('structured_output', 'cancel')
    tools: tuple = ()
    external: bool = False

class Provider(Protocol):
    metadata: ProviderMetadata
    def execute(self, package: dict, cancel: Event, deadline: float) -> str: ...
    def cancel(self, job_id: str) -> None: ...

class DeterministicMock:
    metadata = ProviderMetadata('mock', 'deterministic-neutral-v1', '1', 'NONE', 'LOCAL_PROCESS_NO_EGRESS',
        'AVAILABLE', 'NOT_APPLICABLE', 'Synthetic local mock; no provider retention or external disclosure.')
    def __init__(self): self.executions = 0
    def execute(self, package, cancel, deadline):
        if cancel.is_set(): raise SafeError('CANCELLED')
        self.executions += 1
        task = package['task']
        result = {'task': task, 'sources': package['entry_refs']}
        if task == 'capture_classify':
            kind = package['entries'][0]['type']
            result.update(type=kind, tags=['ідея' if kind == 'creative' else 'нотатка'], reason='selected_entry')
        elif task == 'organize_selected':
            result.update(groups=sorted({e['type'] for e in package['entries']}), reason='explicit_selection')
        elif task == 'memory_propose':
            result.update(preference='concise', reason='review_preference')
        else: raise SafeError('TASK_DENIED')
        return encode(result)
    def cancel(self, job_id): pass

class DisabledCodex:
    metadata = ProviderMetadata('codex-disabled', None, 'candidate-1', 'UNINSPECTED_NO_AUTH_ACCESS',
        'UNVERIFIED_EXTERNAL_CODEX', 'PROVIDER_DISABLED', 'UNKNOWN',
        'Destination/retention/auth/OS isolation require a separately authorized live gate.', external=True)
    def execute(self, package, cancel, deadline):
        raise SafeError('PROVIDER_DISABLED', 403)  # no configurable permission bypass, no executable
    def cancel(self, job_id): pass

def metadata(provider):
    import json
    return json.loads(encode(asdict(provider.metadata)))
