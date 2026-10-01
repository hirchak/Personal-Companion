"""Synthetic generated PCM only, temp roots, real SQLite/filesystem. No model or microphone voice."""
import base64,io,json,math,struct,threading,time,wave
from uuid import uuid4
import pytest
from apps.core.storage import Store,SafeError,digest,encode
from apps.core.domain import Journal
from apps.core.sync import SyncService,Pair
from apps.core.voice import Voice,CHUNK_SIZE
from apps.core.audio_format import PCMConverter
from apps.core.voice_contracts import AudioBegin,AudioChunk,ASRRequest,TranscriptEdit,TranscriptConfirm,AudioDelete
from test_m1_domain import isolated,create


def wav(seconds=1,signal='tone'):
    stream=io.BytesIO();rate=16000
    with wave.open(stream,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        values=[0 if signal=='silence' else (1 if i%2 else -1) if signal=='noise' else int(5000*math.sin(i*2*math.pi*330/rate)) for i in range(int(rate*seconds))]
        w.writeframes(struct.pack('<'+'h'*len(values),*values))
    return stream.getvalue()
@pytest.fixture
def voice(isolated):
    j=Journal(Store(isolated/'voice'));return Voice(j,SyncService(j))
def begin(data,**extra):
    return AudioBegin(audio_id=uuid4(),operation_id=uuid4(),content_hash=digest(data),byte_size=len(data),mime='audio/wav',created_at_utc='2099-01-01T12:00:00Z',local_date='2099-01-01',**extra)
def chunk(data,index):
    part=data[index*CHUNK_SIZE:(index+1)*CHUNK_SIZE]
    return AudioChunk(index=index,content_hash=digest(part),data=base64.b64encode(part).decode())
def save(v,data=None,auth=None):
    data=data or wav();b=begin(data);v.begin(b,auth)
    for i in range((len(data)+CHUNK_SIZE-1)//CHUNK_SIZE):v.chunk(b.audio_id,chunk(data,i),auth)
    return b.audio_id,v.finalize(b.audio_id,auth)
def candidate(v,id):
    result=v.enqueue(id,ASRRequest(mode='FAKE'));v.run(result['transcript_id']);return v.get(id)['transcript']
def paired(v):
    p=v.sync.pair(Pair(invitation=v.sync.invite()['invitation'],device_id=uuid4(),label='SYNTHETIC'))
    auth=(p['device_id'],p['credential'],p['epoch']);v.sync.finalize(*auth);return auth

def test_M4_A01_A03_restart_chunks_duplicate_durable(voice):
    data=wav(19);b=begin(data);auth=paired(voice);voice.begin(b,auth)
    result=voice.chunk(b.audio_id,chunk(data,0),auth);assert result['state']=='CHUNK_DURABLE'
    assert voice.chunk(b.audio_id,chunk(data,0),auth)==result
    # Real reopen with committed SQLite and staged chunk: next index resumes.
    j=Journal(Store(voice.store.root));other=Voice(j,SyncService(j));assert other.get(b.audio_id,auth)['received_chunks']==[0]
    for i in range(1,(len(data)+CHUNK_SIZE-1)//CHUNK_SIZE):other.chunk(b.audio_id,chunk(data,i),auth)
    receipt=other.finalize(b.audio_id,auth);assert receipt['state']=='MAC_AUDIO_CONFIRMED'
    assert other.finalize(b.audio_id,auth)['content_hash']==digest(data)
    assert other.path(b.audio_id).read_bytes()==data
    assert len(list(other.root.iterdir()))==1 and not list(other.staging.iterdir())
    assert other.begin(b,auth)['state']=='MAC_AUDIO_CONFIRMED'
    for p in [other.root,other.staging]:assert p.stat().st_mode&0o777==0o700
    assert other.path(b.audio_id).stat().st_mode&0o777==0o600

def test_M4_A02_commit_failure_no_receipt_restart_recovers_file(voice):
    data=wav();b=begin(data);voice.begin(b);voice.chunk(b.audio_id,chunk(data,0));voice.store.fail_commit=True
    import sqlite3
    with pytest.raises(sqlite3.OperationalError):voice.finalize(b.audio_id)
    voice.store.fail_commit=False
    assert voice.get(b.audio_id)['state']=='UPLOADING'
    other=Voice(voice.journal,voice.sync);assert other.get(b.audio_id)['state']=='MAC_AUDIO_CONFIRMED'
    assert other.path(b.audio_id).read_bytes()==data

def test_M4_A04_revoke_epoch_same_upload_and_other_device_denied(voice):
    data=wav(10);b=begin(data);auth=paired(voice);voice.begin(b,auth);voice.chunk(b.audio_id,chunk(data,0),auth)
    other=paired(voice)
    with pytest.raises(SafeError,match='AUDIO_NOT_FOUND'):voice.get(b.audio_id,other)
    voice.sync.revoke(auth[0])
    for fn in [lambda:voice.chunk(b.audio_id,chunk(data,1),auth),lambda:voice.finalize(b.audio_id,auth),lambda:voice.begin(b,auth)]:
        with pytest.raises(SafeError,match='DEVICE_REVOKED'):fn()
    fresh=paired(voice);x=begin(wav());voice.begin(x,fresh);voice.sync.rotate()
    with pytest.raises(SafeError,match='DEVICE_REVOKED|REPAIR_REQUIRED'):voice.chunk(x.audio_id,chunk(wav(),0),fresh)
    assert not voice.path(x.audio_id).exists()

@pytest.mark.parametrize('bad',[b'',b'RIFF',wav()[:-1],wav()+b'extra',b'OggS'+b'x'*100,wav(.1)])
def test_M4_A05_format_invalid(bad):
    with pytest.raises(SafeError):PCMConverter().normalize(bad,'audio/wav')
@pytest.mark.parametrize('mime',['audio/webm','audio/ogg','x;$(anything)'])
def test_M4_A05_unsupported_codec_no_global_tool(mime):
    with pytest.raises(SafeError,match='UNSUPPORTED'):PCMConverter().normalize(wav(),mime)

def test_M4_A05_checksum_order_reuse_path_symlink(voice,isolated):
    from pydantic import ValidationError
    data=wav(19);b=begin(data);voice.begin(b)
    with pytest.raises(SafeError,match='ORDER'):voice.chunk(b.audio_id,chunk(data,1))
    c=chunk(data,0);wrong=c.model_copy(update={'content_hash':'0'*64})
    with pytest.raises(SafeError,match='CHECKSUM'):voice.chunk(b.audio_id,wrong)
    voice.chunk(b.audio_id,c)
    different=bytearray(data[:CHUNK_SIZE]);different[-1]^=1
    with pytest.raises(SafeError,match='REUSE'):voice.chunk(b.audio_id,AudioChunk(index=0,content_hash=digest(different),data=base64.b64encode(different).decode()))
    with pytest.raises(ValidationError):AudioBegin.model_validate(dict(b.model_dump(mode='json'),destination='../escape'))
    voice.stage(b.audio_id).joinpath('000.part').write_bytes(b'corrupt')
    other=Voice(voice.journal,voice.sync);assert other.get(b.audio_id)['received_chunks']==[]
    voice.chunk(b.audio_id,c)
    for i in (1,2):voice.chunk(b.audio_id,chunk(data,i))
    target=isolated/'unknown';target.write_text('SYNTHETIC unrelated')
    voice.path(b.audio_id).symlink_to(target)
    with pytest.raises(SafeError,match='SYMLINK'):voice.finalize(b.audio_id)
    assert target.read_text()=='SYNTHETIC unrelated'

def test_M4_A07_edit_confirm_preserves_candidate_existing_note_revision(voice):
    id,_=save(voice);t=candidate(voice,id);original=t['candidate']
    assert not voice.journal.list()['items']
    voice.edit(t['id'],TranscriptEdit(revision=1,text='SYNTHETIC · Виправлено користувачем'))
    b=TranscriptConfirm(revision=2,operation_id=uuid4(),entry_id=uuid4(),base_revision=0,retention='KEEP')
    result=voice.confirm(t['id'],b)
    assert voice.journal.get(result['entry_id'])['raw_text']=='SYNTHETIC · Виправлено користувачем'
    current=voice.get(id)['transcript'];assert current['candidate']==original and current['edited']!=''
    assert current['engine']=='deterministic-fake-local' and current['audio_hash']==voice.get(id)['content_hash']
    assert voice.confirm(t['id'],b)['revision']==1 and len(voice.journal.list()['items'])==1
    # Explicit target with stale revision cannot overwrite unrelated edits; valid revision preserves history.
    id2,_=save(voice);t2=candidate(voice,id2);req,_=create(voice.journal,text='SYNTHETIC original raw journal')
    from apps.core.models import Patch
    voice.journal.write('edit',req.entry_id,Patch(operation_id=uuid4(),base_revision=1,changes={'tags':['SYNTHETIC']}))
    edit=TranscriptConfirm(revision=1,operation_id=uuid4(),entry_id=req.entry_id,base_revision=1,retention='KEEP')
    with pytest.raises(SafeError,match='REVISION_CONFLICT'):voice.confirm(t2['id'],edit)
    voice.confirm(t2['id'],edit.model_copy(update={'base_revision':2}))
    assert voice.journal.history(str(req.entry_id))['items'][0]['raw_text']=='SYNTHETIC original raw journal'
    with voice.store.connect() as c:assert c.execute('SELECT COUNT(*) FROM ai_jobs').fetchone()[0]==0

@pytest.mark.parametrize('signal',['silence','noise'])
def test_M4_A08_silence_low_energy_never_produces_note(voice,signal):
    id,_=save(voice,wav(signal=signal));t=candidate(voice,id)
    assert t['state']=='FAILED' and t['error']=='NOTHING_RECOGNIZED' and not t['candidate']
    assert not voice.journal.list()['items']
    with pytest.raises(SafeError):voice.confirm(t['id'],TranscriptConfirm(revision=1,operation_id=uuid4(),entry_id=uuid4(),base_revision=0,retention='KEEP'))

class Slow:
    def __init__(self):self.started=threading.Event();self.release=threading.Event()
    def metadata(self):return {'engine':'trusted-fake','model':'fake','model_hash':None,'available':True}
    def transcribe(self,*args):self.started.set();self.release.wait(2);return {'text':'SYNTHETIC late result','language':'uk'}

def test_M4_A09_cancel_restart_no_late_results(voice):
    data=wav();b=begin(data);voice.begin(b);voice.chunk(b.audio_id,chunk(data,0));voice.cancel_upload(b.audio_id)
    with pytest.raises(SafeError):voice.finalize(b.audio_id)
    id,_=save(voice);slow=Slow();voice.engines['FAKE']=slow
    t=voice.enqueue(id,ASRRequest(mode='FAKE'));thread=threading.Thread(target=voice.run,args=(t['transcript_id'],));thread.start();assert slow.started.wait(1)
    voice.cancel_transcript(t['transcript_id']);slow.release.set();thread.join(2)
    current=voice.get(id)['transcript'];assert current['state']=='CANCELLED' and current['candidate'] is None
    queued=voice.enqueue(id,ASRRequest(mode='FAKE'));Voice(voice.journal,voice.sync)
    assert voice.get(id)['transcript']['state']=='FAILED' and not voice.journal.list()['items']

@pytest.mark.parametrize('retention',['KEEP','DELETE_AFTER_CONFIRM'])
def test_M4_A10_retention_explicit(voice,retention):
    id,_=save(voice);t=candidate(voice,id)
    assert voice.path(id).exists()
    voice.confirm(t['id'],TranscriptConfirm(revision=1,operation_id=uuid4(),entry_id=uuid4(),base_revision=0,retention=retention))
    assert voice.path(id).exists()==(retention=='KEEP')
    assert voice.journal.list()['items']
    if retention=='KEEP':voice.delete(id,AudioDelete(confirm=True))
    assert not voice.path(id).exists() and voice.get(id)['state']=='DELETED'
    Voice(voice.journal,voice.sync)
    with voice.store.connect() as c:Store.check_audio(c)

def test_M4_A10_delete_during_running_removes_derived(voice):
    id,_=save(voice);slow=Slow();voice.engines['FAKE']=slow;t=voice.enqueue(id,ASRRequest(mode='FAKE'))
    thread=threading.Thread(target=voice.run,args=(t['transcript_id'],));thread.start();assert slow.started.wait(1)
    voice.delete(id,AudioDelete(confirm=True));slow.release.set();thread.join(2)
    assert voice.get(id)['transcript'] is None and not voice.path(id).exists()
    with voice.store.connect() as c:assert c.execute('SELECT COUNT(*) FROM audio_chunks').fetchone()[0]==0

@pytest.mark.parametrize('fault',[None,'missing','corrupt','manifest','traversal','symlink','reference'])
def test_M4_A11_backup_audio_roundtrip_or_safe_failure(voice,isolated,fault):
    id,_=save(voice);t=candidate(voice,id);voice.confirm(t['id'],TranscriptConfirm(revision=1,operation_id=uuid4(),entry_id=uuid4(),base_revision=0,retention='KEEP'))
    b=isolated/'backup';m=voice.store.backup(b);target=isolated/'restored';file=b/'audio'/m['attachments'][0]['file']
    assert m['backup_format']==2 and len(m['attachments'])==1
    if fault=='missing':file.unlink()
    if fault=='corrupt':file.write_bytes(b'SYNTHETIC corruption')
    if fault=='manifest':m['attachments']=[]
    if fault=='traversal':m['attachments'][0]['file']='../snapshot.sqlite3'
    if fault=='symlink':file.unlink();file.symlink_to(voice.path(id))
    if fault=='reference':
        import sqlite3
        with sqlite3.connect(b/'snapshot.sqlite3') as c:c.execute("UPDATE transcripts SET audio_hash=?",('0'*64,))
        m['files']['snapshot.sqlite3']=digest((b/'snapshot.sqlite3').read_bytes())
    (b/'manifest.json').write_text(encode(m))
    if fault:
        with pytest.raises(SafeError):Store.restore(b,target)
        assert not target.exists() and voice.path(id).read_bytes()==wav()
    else:
        restored=Store.restore(b,target);j=Journal(restored);v=Voice(j,SyncService(j))
        assert v.path(id).read_bytes()==wav() and v.get(id)['transcript']['candidate']==t['candidate']
        assert j.list()['items'] and restored.meta()['restore_epoch']==1

def test_M4_A14_real_backend_disabled(voice):
    id,_=save(voice)
    with pytest.raises(SafeError,match='LOCAL_ASR_BACKEND_NOT_RUN'):voice.enqueue(id,ASRRequest())
    assert voice.list()['actual_backend']['available'] is False


def test_M4_A04_repaired_new_epoch_cannot_reuse_old_audio_upload(voice):
    data=wav();auth=paired(voice);b=begin(data);voice.begin(b,auth);voice.chunk(b.audio_id,chunk(data,0),auth)
    voice.sync.rotate()
    p=voice.sync.pair(Pair(invitation=voice.sync.invite()['invitation'],device_id=auth[0],label='SYNTHETIC repair'))
    repaired=(p['device_id'],p['credential'],p['epoch']);voice.sync.finalize(*repaired)
    with pytest.raises(SafeError,match='REPAIR_REQUIRED'):voice.finalize(b.audio_id,repaired)
    with pytest.raises(SafeError,match='REPAIR_REQUIRED'):voice.begin(b,repaired)
    copy=begin(data);voice.begin(copy,repaired);voice.chunk(copy.audio_id,chunk(data,0),repaired)
    assert voice.finalize(copy.audio_id,repaired)['state']=='MAC_AUDIO_CONFIRMED'


def test_M4_A08_high_energy_noise_only_unconfirmed_candidate(voice):
    stream=io.BytesIO()
    with wave.open(stream,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(struct.pack('<'+'h'*16000,*[((i*1103515245+12345)%16000)-8000 for i in range(16000)]))
    id,_=save(voice,stream.getvalue());t=candidate(voice,id)
    assert t['state']=='TRANSCRIPT_READY' and not voice.journal.list()['items']
    assert voice.get(id)['signal']=='REVIEW_REQUIRED'


def test_M4_A06_late_result_after_deadline_is_failed(voice):
    id,_=save(voice);slow=Slow();slow.release.set();voice.engines['FAKE']=slow;voice.timeout=0
    t=candidate(voice,id);assert t['state']=='FAILED' and t['error']=='ASR_TIMEOUT' and not t['candidate']


@pytest.mark.parametrize('rate,channels,width',[(8000,1,2),(16000,2,2),(16000,1,1)])
def test_M4_A05_unsupported_pcm_parameters(rate,channels,width):
    stream=io.BytesIO()
    with wave.open(stream,'wb') as w:
        w.setnchannels(channels);w.setsampwidth(width);w.setframerate(rate);w.writeframes(b'\0'*(rate*channels*width))
    with pytest.raises(SafeError,match='PCM_UNSUPPORTED'):PCMConverter().normalize(stream.getvalue(),'audio/wav')
