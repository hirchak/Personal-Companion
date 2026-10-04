"""Synthetic private attachments and explicit transcripts. No network, AI or clinical dispatch."""
import base64
import json
import os
import shutil
import sqlite3
import threading
import time
from uuid import UUID, uuid4
from .storage import SafeError, digest, encode, now, safe_path
from .audio_format import PCMConverter, MAX_AUDIO, CHUNK_SIZE
from .local_asr import DisabledLocalASR, FakeLocalASR
from .voice_contracts import AudioBegin
from .models import Create, Patch

VOICE_TABLES = (
 'CREATE TABLE IF NOT EXISTS audio(id TEXT PRIMARY KEY,operation_id TEXT UNIQUE NOT NULL,device_id TEXT,epoch TEXT,content_hash TEXT NOT NULL,byte_size INTEGER NOT NULL,mime TEXT NOT NULL,state TEXT NOT NULL,metadata TEXT NOT NULL,duration REAL,signal TEXT,retention TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS audio_chunks(audio_id TEXT NOT NULL REFERENCES audio(id) ON DELETE CASCADE,chunk_index INTEGER NOT NULL,content_hash TEXT NOT NULL,byte_size INTEGER NOT NULL,PRIMARY KEY(audio_id,chunk_index))',
 'CREATE TABLE IF NOT EXISTS transcripts(id TEXT PRIMARY KEY,audio_id TEXT NOT NULL REFERENCES audio(id),audio_hash TEXT NOT NULL,engine TEXT NOT NULL,model TEXT,model_hash TEXT,language_setting TEXT NOT NULL,language_result TEXT,candidate TEXT,edited TEXT,state TEXT NOT NULL,revision INTEGER NOT NULL,entry_id TEXT,entry_revision INTEGER,error TEXT,created TEXT NOT NULL,updated TEXT NOT NULL,elapsed REAL,confirmation_op TEXT)',
 'CREATE UNIQUE INDEX IF NOT EXISTS voice_one_active ON transcripts((1)) WHERE state IN ("TRANSCRIPTION_QUEUED","TRANSCRIBING")',
)

def fsync_dir(path):
    fd=os.open(path,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def durable_write(path, data):
    temp=path.with_name(path.name+'.writing')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out: out.write(data);out.flush();os.fsync(out.fileno())
    os.replace(temp,path);fsync_dir(path.parent)

class Voice:
    def __init__(self,journal,sync):
        self.journal,self.store,self.sync=journal,journal.store,sync
        self.store.attachment_lock=getattr(self.store,'attachment_lock',threading.RLock())
        self.lock=self.store.attachment_lock
        self.engines={'DISABLED':DisabledLocalASR(),'FAKE':FakeLocalASR(),'LOCAL':DisabledLocalASR()}
        self.converter=PCMConverter();self.cancel_events={};self.timeout=15
        self.root=self.store.root/'audio';self.staging=self.store.root/'audio-staging'
        with self.lock:
            for p in (self.root,self.staging): p.mkdir(mode=0o700,exist_ok=True);os.chmod(p,0o700)
            self.recover()

    def _auth(self,c,auth):
        return self.sync.authenticate(c,*auth) if auth else None
    def _row(self,c,id,auth=None):
        device=self._auth(c,auth)
        row=c.execute('SELECT * FROM audio WHERE id=?',(str(id),)).fetchone()
        if not row or device and row['device_id']!=device: raise SafeError('AUDIO_NOT_FOUND',404)
        if device and row['epoch']!=auth[2]:raise SafeError('REPAIR_REQUIRED',409)
        return row
    def path(self,id):
        return self.root/(str(UUID(str(id)))+'.wav')
    def stage(self,id):
        return self.staging/str(UUID(str(id)))
    def view(self,c,row):
        x=dict(row);x['metadata']=json.loads(x['metadata']);x['privacy_class']='PRIVATE_PERSONAL'
        x['source_device']=x.pop('device_id') or 'MAC'
        x['received_chunks']=[r[0] for r in c.execute('SELECT chunk_index FROM audio_chunks WHERE audio_id=? ORDER BY chunk_index',(row['id'],))]
        x['chunk_size']=CHUNK_SIZE
        t=c.execute('SELECT * FROM transcripts WHERE audio_id=? ORDER BY created DESC,id DESC LIMIT 1',(row['id'],)).fetchone()
        x['transcript']=dict(t) if t else None
        return x
    def list(self,auth=None):
        with self.lock,self.store.connect() as c:
            device=self._auth(c,auth)
            rows=c.execute('SELECT * FROM audio WHERE state!=?'+(' AND device_id=?' if device else '')+' ORDER BY created DESC LIMIT 100', ['DELETED']+([device] if device else [])).fetchall()
            return {'items':[self.view(c,r) for r in rows],'actual_backend':self.engines['LOCAL'].metadata()}
    def get(self,id,auth=None):
        with self.lock,self.store.connect() as c:return self.view(c,self._row(c,id,auth))

    def begin(self,body,auth=None):
        values=body.model_dump(mode='json');id=str(body.audio_id)
        with self.lock,self.store.transaction() as c:
            device=self._auth(c,auth)
            old=c.execute('SELECT * FROM audio WHERE id=? OR operation_id=?',(id,str(body.operation_id))).fetchone()
            if old:
                if device and old['epoch']!=auth[2]:raise SafeError('REPAIR_REQUIRED',409)
                if old['id']!=id or old['device_id']!=device or json.loads(old['metadata'])!=values or old['state'] in {'CANCELLED','DELETED'}:
                    raise SafeError('AUDIO_OPERATION_REUSE',409)
                return self.view(c,old)
            if c.execute("SELECT COUNT(*) FROM audio WHERE state IN ('UPLOADING','MAC_AUDIO_CONFIRMED')").fetchone()[0]>=100:
                raise SafeError('AUDIO_STORE_LIMIT',413)
            c.execute('INSERT INTO audio VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,?,?,?)',
                      (id,str(body.operation_id),device,auth[2] if auth else None,body.content_hash,body.byte_size,body.mime,'UPLOADING',encode(values),'KEEP',now(),now()))
            self.stage(id).mkdir(mode=0o700,exist_ok=True);fsync_dir(self.staging)
            return self.view(c,self._row(c,id,auth))

    def chunk(self,id,body,auth=None):
        try: data=base64.b64decode(body.data,validate=True)
        except (ValueError,TypeError): raise SafeError('AUDIO_CHUNK_INVALID') from None
        if not data or len(data)>CHUNK_SIZE or digest(data)!=body.content_hash: raise SafeError('AUDIO_CHECKSUM')
        with self.lock,self.store.transaction() as c:
            row=self._row(c,id,auth)
            if row['state']!='UPLOADING': raise SafeError('AUDIO_NOT_UPLOADING',409)
            total=(row['byte_size']+CHUNK_SIZE-1)//CHUNK_SIZE
            required=CHUNK_SIZE if body.index<total-1 else row['byte_size']-CHUNK_SIZE*(total-1)
            if body.index>=total or len(data)!=required: raise SafeError('AUDIO_CHUNK_SIZE')
            existing=c.execute('SELECT * FROM audio_chunks WHERE audio_id=? AND chunk_index=?',(str(id),body.index)).fetchone()
            if existing:
                if existing['content_hash']!=body.content_hash: raise SafeError('AUDIO_CHUNK_REUSE',409)
                if digest((self.stage(id)/f'{body.index:03}.part').read_bytes())!=body.content_hash: raise SafeError('AUDIO_CHECKSUM')
            else:
                # Canonical order; idempotent retries accepted, later chunks rejected until predecessors persist.
                count=c.execute('SELECT COUNT(*) FROM audio_chunks WHERE audio_id=?',(str(id),)).fetchone()[0]
                if body.index!=count: raise SafeError('AUDIO_CHUNK_ORDER',409)
                durable_write(self.stage(id)/f'{body.index:03}.part',data)
                c.execute('INSERT INTO audio_chunks VALUES(?,?,?,?)',(str(id),body.index,body.content_hash,len(data)))
            return {'audio_id':str(id),'index':body.index,'content_hash':body.content_hash,'state':'CHUNK_DURABLE'}

    def finalize(self,id,auth=None):
        with self.lock,self.store.transaction() as c:
            row=self._row(c,id,auth)
            if row['state']=='MAC_AUDIO_CONFIRMED':
                self.verify_file(row);return self.view(c,row)
            if row['state']!='UPLOADING': raise SafeError('AUDIO_NOT_UPLOADING',409)
            expected=(row['byte_size']+CHUNK_SIZE-1)//CHUNK_SIZE
            chunks=c.execute('SELECT * FROM audio_chunks WHERE audio_id=? ORDER BY chunk_index',(str(id),)).fetchall()
            if len(chunks)!=expected: raise SafeError('AUDIO_INCOMPLETE',409)
            pieces=[]
            for index,r in enumerate(chunks):
                data=(self.stage(id)/f'{index:03}.part').read_bytes()
                if r['chunk_index']!=index or digest(data)!=r['content_hash']: raise SafeError('AUDIO_CHECKSUM')
                pieces.append(data)
            data=b''.join(pieces)
            if len(data)!=row['byte_size'] or digest(data)!=row['content_hash']: raise SafeError('AUDIO_CHECKSUM')
            normalized,measure=self.converter.normalize(data,row['mime'])
            durable_write(self.path(id),normalized)
            c.execute("UPDATE audio SET state='MAC_AUDIO_CONFIRMED',duration=?,signal=?,updated=? WHERE id=?",(measure['duration_seconds'],measure['signal'],now(),str(id)))
            result=self.view(c,self._row(c,id,auth))
        # Receipt follows both durable file and DB commit; redundant staging cleanup is recoverable.
        with self.lock:
            if self.stage(id).exists():shutil.rmtree(self.stage(id));fsync_dir(self.staging)
        return result

    def verify_file(self,row):
        p=self.path(row['id'])
        if not p.is_file() or p.stat().st_size!=row['byte_size'] or digest(p.read_bytes())!=row['content_hash']:
            raise SafeError('AUDIO_CHECKSUM')

    def cancel_upload(self,id,auth=None):
        with self.lock,self.store.transaction() as c:
            row=self._row(c,id,auth)
            if row['state'] not in {'UPLOADING','CANCELLED'}: raise SafeError('AUDIO_ALREADY_SAVED',409)
            c.execute("UPDATE audio SET state='CANCELLED',updated=? WHERE id=?",(now(),str(id)))
            c.execute('DELETE FROM audio_chunks WHERE audio_id=?',(str(id),))
        with self.lock:
            if self.stage(id).exists():shutil.rmtree(self.stage(id));fsync_dir(self.staging)
        return {'audio_id':str(id),'state':'CANCELLED'}

    def enqueue(self,id,body,auth=None):
        engine=self.engines[body.mode];tid=str(uuid4());meta=engine.metadata()
        with self.lock,self.store.transaction() as c:
            row=self._row(c,id,auth)
            if row['state']!='MAC_AUDIO_CONFIRMED':raise SafeError('AUDIO_UNAVAILABLE',409)
            self.verify_file(row)
            if not meta['available']:raise SafeError('LOCAL_ASR_BACKEND_NOT_RUN',409)
            if c.execute("SELECT 1 FROM transcripts WHERE state IN ('TRANSCRIPTION_QUEUED','TRANSCRIBING')").fetchone():raise SafeError('ASR_BUSY',409)
            c.execute('INSERT INTO transcripts VALUES(?,?,?,?,?,?,?,NULL,NULL,NULL,?,1,NULL,NULL,NULL,?,?,NULL,NULL)',
                      (tid,str(id),row['content_hash'],meta['engine'],meta['model'],meta['model_hash'],body.language,'TRANSCRIPTION_QUEUED',now(),now()))
            self.cancel_events[tid]=threading.Event()
        return {'transcript_id':tid,'state':'TRANSCRIPTION_QUEUED'}

    def run(self,tid,mode='FAKE',auth=None):
        start=time.monotonic();cancel=self.cancel_events.setdefault(tid,threading.Event())
        try:
            with self.lock,self.store.transaction() as c:
                t=c.execute('SELECT * FROM transcripts WHERE id=?',(tid,)).fetchone()
                if not t or t['state']!='TRANSCRIPTION_QUEUED':return
                row=self._row(c,t['audio_id'],auth);self.verify_file(row)
                c.execute("UPDATE transcripts SET state='TRANSCRIBING',updated=? WHERE id=?",(now(),tid))
                data=self.path(row['id']).read_bytes()
            # Legacy energy precheck for fixture engines; guarded local ASR handles quiet signals separately.
            if row['signal']=='LOW_ENERGY' and not self.engines[mode].metadata().get('speech_guard'):raise SafeError('NOTHING_RECOGNIZED')
            value=self.engines[mode].transcribe(data,t['language_setting'],cancel,start+self.timeout)
            if time.monotonic()>=start+self.timeout:raise SafeError('ASR_TIMEOUT')
            if not isinstance(value,dict) or set(value) not in ({'text','language'},{'text','language','speech_state'}) or value['language'] not in {'uk',None} or not isinstance(value['text'],str) or len(value['text'])>8000:
                raise SafeError('ASR_OUTPUT_INVALID')
            speech=value.get('speech_state','SPEECH_DETECTED')
            if speech not in {'SPEECH_DETECTED','UNCERTAIN','NO_SPEECH'}:raise SafeError('ASR_OUTPUT_INVALID')
            if speech=='NO_SPEECH':raise SafeError('NO_SPEECH')
            text=value['text'];text.encode('utf-8')
            if not text.strip() or any(ord(x)<32 and x not in '\n\t\r' for x in text):raise SafeError('NOTHING_RECOGNIZED')
            with self.lock,self.store.transaction() as c:
                row=self._row(c,t['audio_id'],auth)
                current=c.execute('SELECT state FROM transcripts WHERE id=?',(tid,)).fetchone()
                if cancel.is_set() or not current or current[0]!='TRANSCRIBING' or row['state']!='MAC_AUDIO_CONFIRMED':return
                self.verify_file(row)
                c.execute("UPDATE transcripts SET state=?,candidate=?,language_result=?,error=?,elapsed=?,updated=? WHERE id=?",('REVIEW_REQUIRED' if speech=='UNCERTAIN' else 'TRANSCRIPT_READY',text,value['language'],'SPEECH_UNCERTAIN' if speech=='UNCERTAIN' else None,time.monotonic()-start,now(),tid))
        except (SafeError, OSError, sqlite3.Error, ValueError, UnicodeError) as exc:
            code=exc.code if isinstance(exc,SafeError) else 'ASR_FAILED'
            with self.lock,self.store.transaction() as c:
                c.execute("UPDATE transcripts SET state='FAILED',error=?,elapsed=?,updated=? WHERE id=? AND state IN ('TRANSCRIPTION_QUEUED','TRANSCRIBING')",(code,time.monotonic()-start,now(),tid))
        finally:self.cancel_events.pop(tid,None)

    def _transcript(self,c,tid,auth):
        t=c.execute('SELECT * FROM transcripts WHERE id=?',(str(tid),)).fetchone()
        if not t:raise SafeError('TRANSCRIPT_NOT_FOUND',404)
        self._row(c,t['audio_id'],auth)
        return t
    def edit(self,tid,body,auth=None):
        with self.lock,self.store.transaction() as c:
            t=self._transcript(c,tid,auth)
            if t['state'] not in {'TRANSCRIPT_READY','REVIEW_REQUIRED'} or t['revision']!=body.revision:raise SafeError('TRANSCRIPT_CHANGED',409)
            c.execute("UPDATE transcripts SET state='TRANSCRIPT_READY',error=NULL,edited=?,revision=revision+1,updated=? WHERE id=?",(body.text,now(),str(tid)))
        return {'state':'TRANSCRIPT_READY','revision':body.revision+1}
    def cancel_transcript(self,tid,auth=None):
        with self.lock,self.store.transaction() as c:
            t=self._transcript(c,tid,auth)
            if t['state']=='CONFIRMED':raise SafeError('TRANSCRIPT_CONFIRMED',409)
            event=self.cancel_events.get(str(tid))
            if event:event.set()
            c.execute("UPDATE transcripts SET state='CANCELLED',candidate=NULL,edited=NULL,revision=revision+1,updated=? WHERE id=?",(now(),str(tid)))
        return {'state':'CANCELLED'}
    def confirm(self,tid,body,auth=None):
        with self.lock,self.store.transaction() as c:
            t=self._transcript(c,tid,auth);row=self._row(c,t['audio_id'],auth)
            if t['state']=='CONFIRMED':
                if t['confirmation_op']!=digest(encode(body.model_dump(mode='json')).encode()) or t['entry_id']!=str(body.entry_id):raise SafeError('TRANSCRIPT_CONFIRMED',409)
                return {'entry_id':t['entry_id'],'revision':t['entry_revision'],'state':'CONFIRMED'}
            if t['state']!='TRANSCRIPT_READY' or t['revision']!=body.revision or row['state']!='MAC_AUDIO_CONFIRMED':raise SafeError('TRANSCRIPT_CHANGED',409)
            text=t['edited'] if t['edited'] is not None else t['candidate']
            if not text or not text.strip():raise SafeError('NOTHING_RECOGNIZED')
            meta=json.loads(row['metadata'])
            if body.base_revision:
                request=Patch(operation_id=body.operation_id,base_revision=body.base_revision,changes={'raw_text':text})
                result=self.journal.write_in(c,'edit',body.entry_id,request)
            else:
                request=Create(operation_id=body.operation_id,entry_id=body.entry_id,base_revision=0,payload={'raw_text':text,'timezone':meta['timezone'],'local_date':meta['local_date'],'time_precision':'date' if meta['local_date'] else 'unknown'})
                result=self.journal.write_in(c,'create',body.entry_id,request)
            c.execute("UPDATE transcripts SET state='CONFIRMED',entry_id=?,entry_revision=?,confirmation_op=?,updated=? WHERE id=?",(str(body.entry_id),result['revision'],digest(encode(body.model_dump(mode='json')).encode()),now(),str(tid)))
            c.execute('UPDATE audio SET retention=? WHERE id=?',(body.retention,t['audio_id']))
            if body.retention=='DELETE_AFTER_CONFIRM':c.execute("UPDATE audio SET state='DELETE_PENDING' WHERE id=?",(t['audio_id'],))
        if body.retention=='DELETE_AFTER_CONFIRM':self._purge(t['audio_id'],keep_confirmed=True)
        return dict(result,state='CONFIRMED')
    def delete(self,id,body,auth=None):
        with self.lock,self.store.transaction() as c:
            self._row(c,id,auth)
            for t in c.execute('SELECT id FROM transcripts WHERE audio_id=?',(str(id),)):
                event=self.cancel_events.get(t[0])
                if event:event.set()
            c.execute("UPDATE audio SET state='DELETE_PENDING',retention='DELETE_NOW' WHERE id=?",(str(id),))
        self._purge(str(id),keep_confirmed=False)
        return {'state':'DELETED','remote_erase':False,'secure_erase':False}
    def _purge(self,id,keep_confirmed=False):
        with self.lock:
            safe_path(self.store.root)
            for p in (self.path(id),):
                if p.exists():p.unlink();fsync_dir(self.root)
            if self.stage(id).exists():shutil.rmtree(self.stage(id));fsync_dir(self.staging)
            with self.store.transaction() as c:
                c.execute('DELETE FROM audio_chunks WHERE audio_id=?',(str(id),))
                # Confirmed note remains normal user content; raw audio and nonconfirmed derivatives gone.
                c.execute("DELETE FROM transcripts WHERE audio_id=?"+(' AND state!=\'CONFIRMED\'' if keep_confirmed else ''),(str(id),))
                c.execute("UPDATE audio SET state='DELETED',metadata=?,updated=? WHERE id=?",(encode({'audio_id':str(id),'deleted':True}),now(),str(id)))

    def recover(self):
        safe_path(self.store.root)
        with self.store.transaction() as c:
            c.execute("UPDATE transcripts SET state='FAILED',error='ASR_RESTART_RETRY_REQUIRED',updated=? WHERE state IN ('TRANSCRIBING','TRANSCRIPTION_QUEUED')",(now(),))
            rows=c.execute('SELECT * FROM audio').fetchall()
            for row in rows:
                id=row['id']
                if row['state']=='MAC_AUDIO_CONFIRMED':
                    try:self.verify_file(row)
                    except SafeError:c.execute("UPDATE audio SET state='FAILED' WHERE id=?",(id,));continue
                elif row['state']=='UPLOADING' and self.path(id).exists():
                    try:
                        self.verify_file(row);_,measure=self.converter.normalize(self.path(id).read_bytes(),row['mime'])
                        c.execute("UPDATE audio SET state='MAC_AUDIO_CONFIRMED',duration=?,signal=? WHERE id=?",(measure['duration_seconds'],measure['signal'],id))
                    except SafeError:
                        self.path(id).unlink();c.execute("UPDATE audio SET state='FAILED' WHERE id=?",(id,))
                if row['state']=='UPLOADING' and not self.path(id).exists():
                    self.stage(id).mkdir(mode=0o700,exist_ok=True)
                    chunks=c.execute('SELECT * FROM audio_chunks WHERE audio_id=? ORDER BY chunk_index',(id,)).fetchall();broken=False
                    for r in chunks:
                        file=self.stage(id)/f"{r['chunk_index']:03}.part"
                        if broken or not file.is_file() or digest(file.read_bytes())!=r['content_hash']:
                            broken=True;c.execute('DELETE FROM audio_chunks WHERE audio_id=? AND chunk_index=?',(id,r['chunk_index']))
                    keep={f'{r[0]:03}.part' for r in c.execute('SELECT chunk_index FROM audio_chunks WHERE audio_id=?',(id,))}
                    for p in self.stage(id).iterdir():
                        if p.name not in keep and p.is_file():p.unlink()
            active={r['id'] for r in c.execute("SELECT id FROM audio WHERE state='UPLOADING'")}
        for p in self.staging.iterdir():
            if p.name not in active:
                if p.is_dir():shutil.rmtree(p)
                else:p.unlink()
        with self.store.connect() as c:pending=[r[0] for r in c.execute("SELECT id FROM audio WHERE state IN ('DELETE_PENDING','DELETED')")]
        for id in pending:
            with self.store.connect() as c:r=c.execute('SELECT retention FROM audio WHERE id=?',(id,)).fetchone()
            self._purge(id,keep_confirmed=r[0]=='DELETE_AFTER_CONFIRM')
        # Remove finalized orphans after an aborted begin/finalize. Only this synthetic store is scanned.
        with self.store.connect() as c:known={r[0] for r in c.execute("SELECT id FROM audio WHERE state IN ('MAC_AUDIO_CONFIRMED','UPLOADING')")}
        for p in self.root.iterdir():
            if p.name.removesuffix('.wav') not in known:p.unlink()
