"""Local ASR boundary; actual engine unavailable. Trusted synthetic process is not an OS sandbox."""
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from .storage import SafeError, digest, safe_path

class DisabledLocalASR:
    def metadata(self):
        return {'engine':'disabled-local','version':'1','model':None,'model_hash':None,'languages':[],
                'available':False,'status':'LOCAL_ASR_BACKEND_NOT_RUN','supported_input':['audio/wav']}
    def transcribe(self, data, language, cancel, deadline):
        raise SafeError('LOCAL_ASR_BACKEND_NOT_RUN')

class FakeLocalASR:
    executions = 0
    def metadata(self):
        return {'engine':'deterministic-fake-local','version':'1','model':'SYNTHETIC-no-model',
                'model_hash':None,'languages':['uk'],'available':True,'status':'FAKE_ONLY','supported_input':['audio/wav']}
    def transcribe(self, data, language, cancel, deadline):
        self.executions += 1
        if cancel.is_set(): raise SafeError('CANCELLED')
        if time.monotonic() >= deadline: raise SafeError('ASR_TIMEOUT')
        return {'text':'SYNTHETIC · Кандидат локального тесту. Перевірте та виправте текст.', 'language':'uk'}

class ProcessLocalASR(FakeLocalASR):
    """Full bounded process runner for an explicitly supplied hash-pinned trusted fixture.

    Not exposed by API/config. No whisper flags guessed. A future real engine requires inspected
    argv/output contract and separate OS filesystem/egress isolation validation before activation.
    """
    def __init__(self, root, fixture_hash, scenario='valid'):
        self.root = safe_path(root)
        self.fixture = self.root/'asr_fixture.py'
        if scenario not in {'valid','environment','nonzero','malformed','oversized','stderr','timeout','tool','path','child'}:
            raise SafeError('ASR_FIXTURE_DENIED')
        self.hash,self.scenario,self.last_spec = fixture_hash,scenario,None
        self.validate()
    def validate(self):
        safe_path(self.root)
        if not self.fixture.is_file() or digest(self.fixture.read_bytes())!=self.hash:
            raise SafeError('ASR_FIXTURE_DENIED')
    def metadata(self):
        return dict(super().metadata(),engine='trusted-fake-process',fixture_hash=self.hash)
    def transcribe(self, data, language, cancel, deadline):
        self.validate()
        if language != 'uk' or cancel.is_set(): raise SafeError('CANCELLED')
        # Fixed opaque input, within a fresh dedicated controlled directory; never user filenames.
        import tempfile, shutil
        work = self.root/('run-'+os.urandom(12).hex());work.mkdir(mode=0o700)
        source = work/'input.wav'
        fd=os.open(source,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as out: out.write(data);out.flush();os.fsync(out.fileno())
        spec={'args':[sys.executable,'-I','-S',str(self.fixture),'--synthetic-asr',str(source),self.scenario],
              'cwd':str(work),'env':{'PYTHONIOENCODING':'utf-8'},'shell':False}
        self.last_spec=spec
        process=None;sel=selectors.DefaultSelector()
        try:
            process=subprocess.Popen(**spec,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            outputs={'stdout':bytearray(),'stderr':bytearray()}
            for name in outputs:
                stream=getattr(process,name);os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
            while True:
                if cancel.is_set(): raise SafeError('CANCELLED')
                if time.monotonic()>=deadline: raise SafeError('ASR_TIMEOUT')
                for key,_ in sel.select(.02):
                    block=os.read(key.fd,4096)
                    if not block: sel.unregister(key.fileobj)
                    else:
                        outputs[key.data].extend(block)
                        if len(outputs[key.data])>12000: raise SafeError('ASR_OUTPUT_LIMIT')
                if process.poll() is not None and not sel.get_map(): break
            if process.returncode: raise SafeError('ASR_PROCESS_FAILED')
            try:
                value=json.loads(outputs['stdout'].decode('utf-8'))
                if set(value)!={'text','language'} or value['language']!='uk' or not isinstance(value['text'],str) or len(value['text'])>8000:
                    raise ValueError()
                return value
            except (ValueError,UnicodeError,TypeError): raise SafeError('ASR_OUTPUT_INVALID') from None
        finally:
            sel.close()
            if process:
                try: os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait(timeout=1)
                process.stdout.close();process.stderr.close()
            shutil.rmtree(work)
