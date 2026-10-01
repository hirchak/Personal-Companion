"""Controlled synthetic process harness, NOT a usable Codex adapter or OS sandbox.

Only a caller-supplied, hash-pinned test fixture is executed. Not exposed by HTTP/config.
The real adapter remains disabled because same-user OS filesystem/egress isolation is unproven.
"""
import hashlib
import os
import selectors
import subprocess
import sys
import time
from pathlib import Path
from .providers import DeterministicMock
from .storage import SafeError, encode, safe_path

class FakeProcessProvider(DeterministicMock):
    def __init__(self, root, script_hash, scenario='valid'):
        super().__init__()
        self.root = safe_path(root)
        self.fixture = self.root / 'fixture.py'
        if scenario not in {'valid','malformed','nonzero','oversized','timeout','tool','path','environment'}:
            raise SafeError('FAKE_SCENARIO_DENIED')
        if not self.fixture.is_file() or self.fixture.is_symlink() or hashlib.sha256(self.fixture.read_bytes()).hexdigest()!=script_hash:
            raise SafeError('FAKE_FIXTURE_DENIED')
        self.hash, self.scenario = script_hash, scenario
        self.last_spec = None

    def execute(self, package, cancel, deadline):
        if self.fixture.is_symlink() or hashlib.sha256(self.fixture.read_bytes()).hexdigest()!=self.hash:
            raise SafeError('FAKE_FIXTURE_DENIED')
        if set(package) != {'protocol','output_schema','task','provider','entry_refs','memory_refs','entries','memories','constraints','consent_ref','approval_scope','expires_at'}:
            raise SafeError('PROCESS_REQUEST_DENIED')
        raw=encode(package).encode()
        if len(raw)>24000: raise SafeError('CONTEXT_BUDGET_NARROW_SELECTION')
        if cancel.is_set(): raise SafeError('CANCELLED')
        # No shell expansion, inherited credentials, HOME, provider auth, git, PATH search or login.
        spec={'args':[sys.executable,'-I','-S',str(self.fixture),'--synthetic-provider',self.scenario],
              'cwd':str(self.root), 'env':{'PYTHONIOENCODING':'utf-8'}, 'shell':False}
        self.last_spec=spec
        self.executions += 1
        p=subprocess.Popen(**spec,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
        selector=selectors.DefaultSelector()
        try:
            p.stdin.write(raw); p.stdin.close()
            os.set_blocking(p.stdout.fileno(),False)
            selector.register(p.stdout,selectors.EVENT_READ)
            output=bytearray()
            while True:
                if cancel.is_set(): raise SafeError('CANCELLED')
                if time.monotonic()>=deadline: raise SafeError('JOB_TIMEOUT')
                for key,_ in selector.select(timeout=min(.02,max(0,deadline-time.monotonic()))):
                    chunk=os.read(key.fd,4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output.extend(chunk)
                        if len(output)>8000: raise SafeError('OUTPUT_LIMIT')
                if p.poll() is not None and not selector.get_map(): break
            if p.returncode: raise SafeError('PROCESS_NONZERO')
            try: return output.decode('utf-8')
            except UnicodeError: raise SafeError('OUTPUT_INVALID') from None
        finally:
            selector.close()
            # Fixture and any child group are bounded even on cancel/oversized output.
            import signal
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            p.wait(timeout=1)
            p.stdout.close()
            if not p.stdin.closed: p.stdin.close()
