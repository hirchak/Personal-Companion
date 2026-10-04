"""Pinned project-local whisper.cpp, bounded M4 interface and deny-network/filesystem sandbox."""
import os,json,time,selectors,subprocess,signal,tempfile,shutil
from pathlib import Path
from .storage import SafeError,digest,REPO

class WhisperLocalASR:
    def __init__(self,root=None,private_scope=False):
        self.private_scope=private_scope
        self.root=Path(root or REPO/'generated/local-asr').resolve();self.binary=self.root/'build-v1.9.4-cpu/bin/whisper-cli';self.model=self.root/'models/ggml-small.bin';self.sandbox=Path('/usr/bin/sandbox-exec');self.executions=0;self.last_spec=None
        if not self.sandbox.is_file() or (not self.root.is_relative_to((REPO/'generated').resolve()) and not (private_scope and root is not None)):raise SafeError('LOCAL_ASR_ISOLATION_UNAVAILABLE')
        if root is not None:
            source=Path(root).absolute()
            if '..' in source.parts or any(p.is_symlink() for p in (source,*source.parents)):raise SafeError('LOCAL_ASR_ASSET_PATH_UNSAFE')
        receipt=json.loads((self.root/'M7C_ASR_MODEL_RECEIPT.json').read_text())
        if receipt.get('model_checksum_verified') is not True or receipt['model_bytes']>2500000000:raise SafeError('LOCAL_ASR_MODEL_INTEGRITY')
        isolation=self.root/'M7C_ASR_ISOLATION_RECEIPT.json'
        if not isolation.is_file() or json.loads(isolation.read_text()).get('status')!='PASS':raise SafeError('LOCAL_ASR_ISOLATION_UNVERIFIED')
        self.model_hash='1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b';self.version='1.9.4-dev';self.binary_hash='54d1e7bf2e36ec29bdf70b87a45e26158396d5004909d16d5ad76e51920b566c'
        proof=json.loads(isolation.read_text())
        if receipt['model_sha256']!=self.model_hash or proof['engine']['binary_hash']!=self.binary_hash or proof.get('profile')!=self.profile(Path('/private/tmp/ORIGINAL_SYNTHETIC_WORKDIR')):raise SafeError('LOCAL_ASR_ISOLATION_UNVERIFIED')
        self.validate()
    def validate(self):
        if self.binary.is_symlink() or self.model.is_symlink() or digest(self.binary.read_bytes())!=self.binary_hash or self.model.stat().st_size!=487601967 or digest(self.model.read_bytes())!=self.model_hash:raise SafeError('LOCAL_ASR_MODEL_INTEGRITY')
    def metadata(self):return {'engine':'whisper.cpp','version':self.version,'model':'small-multilingual','model_hash':self.model_hash,'binary_hash':self.binary_hash,'languages':['uk'],'available':True,'status':'LOCAL_PRIVATE_OWNER_REVIEW_REQUIRED' if self.private_scope else 'LOCAL_SYNTHETIC_ONLY','supported_input':['audio/wav'],'cloud_asr':False,'scope':'M8D_OWNER_LOCAL_AUDIO_ONLY_NO_HUMAN_QUALITY_CERTIFICATION' if self.private_scope else 'M7D_ORIGINAL_SYNTHETIC_AUDIO_ONLY','speech_guard':'PCM_SIGNAL_V1'}
    def profile(self,work):
        q=lambda p:json.dumps(str(p))
        return '\n'.join(['(version 1)','(allow default)','(deny network*)','(deny file-read-data)','(deny file-write*)','(deny process-exec)','(allow file-read-data (literal "/"))','(allow process-fork)','(allow process-exec (literal '+q(self.binary)+'))','(allow sysctl-read)','(allow mach-lookup)','(allow file-read-data (subpath "/System") (subpath "/usr/lib") (subpath "/Library/Apple") (subpath "/private/var/db/dyld") (subpath "/dev") (literal "/etc/localtime") (literal '+q(self.binary)+') (literal '+q(self.model)+') (literal '+q(self.binary.parent)+') (literal '+q(work.parent)+') (subpath '+q(work)+'))','(allow file-write* (subpath '+q(work)+') (literal "/dev/null"))'])
    def transcribe(self,data,language,cancel,deadline):
        if language!='uk':raise SafeError('LOCAL_ASR_LANGUAGE_DENIED')
        if cancel.is_set():raise SafeError('CANCELLED')
        from .speech_presence import speech_presence
        guard=speech_presence(data)
        if guard['state']=='NO_SPEECH':raise SafeError('NO_SPEECH')
        self.validate();self.executions+=1
        work=Path(tempfile.mkdtemp(prefix='m8d-local-whisper-' if self.private_scope else 'm7c-whisper-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
        if self.private_scope:
            from .local_private import owner_only,require_volume
            try:owner_only(work);require_volume(work)
            except BaseException:
                shutil.rmtree(work);raise
        source=work/'input.wav';source.write_bytes(data);source.chmod(0o600);profile=work/'sandbox.sb';profile.write_text(self.profile(work));output=work/'candidate'
        args=[str(self.sandbox),'-f',str(profile),str(self.binary),'-m',str(self.model),'-f',str(source),'-l','uk','-t','4','-ng','-nf','-oj','-of',str(output)]
        spec={'args':args,'cwd':str(work),'env':{'LANG':'en_US.UTF-8','TMPDIR':str(work)},'shell':False};self.last_spec=spec;process=None;sel=selectors.DefaultSelector();sizes={'stdout':0,'stderr':0}
        try:
            process=subprocess.Popen(**spec,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            for name in sizes:
                stream=getattr(process,name);os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
            while True:
                if cancel.is_set():raise SafeError('CANCELLED')
                if time.monotonic()>=deadline:raise SafeError('ASR_TIMEOUT')
                for key,_ in sel.select(.03):
                    chunk=os.read(key.fd,4096)
                    if not chunk:sel.unregister(key.fileobj)
                    else:
                        sizes[key.data]+=len(chunk)
                        if sizes[key.data]>65536:raise SafeError('ASR_OUTPUT_LIMIT')
                if process.poll() is not None and not sel.get_map():break
            if process.returncode:raise SafeError('LOCAL_ASR_PROCESS_FAILED')
            result=output.with_suffix('.json')
            if not result.is_file() or result.stat().st_size>65536:raise SafeError('ASR_OUTPUT_INVALID')
            value=json.loads(result.read_text());segments=value.get('transcription',[])
            if not isinstance(segments,list) or len(segments)>100:raise SafeError('ASR_OUTPUT_INVALID')
            text=''.join(s['text'] for s in segments).strip()
            if len(text)>8000:raise SafeError('ASR_OUTPUT_INVALID')
            return {'text':text,'language':'uk','speech_state':guard['state']}
        finally:
            sel.close()
            if process:
                if process.poll() is None:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=1)
                process.stdout.close();process.stderr.close()
            shutil.rmtree(work)
