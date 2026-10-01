"""Synthetic loopback HTTP/files/ASR overhead; no model, real voice, cloud or hardware benchmark."""
import argparse,base64,io,json,math,platform,resource,shutil,struct,sys,tempfile,threading,time,wave
from pathlib import Path
from uuid import uuid4
import httpx,uvicorn
from apps.core.api import create_app
from apps.core.storage import digest
from apps.core.voice import CHUNK_SIZE

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(tempfile.mkdtemp(prefix='m4-synthetic-measure-',dir=Path(tempfile.gettempdir()).resolve()))
port=8771;origin=f'http://127.0.0.1:{port}';app=create_app(root/'data',port=port,m2=True)
srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='critical',access_log=False))
thread=threading.Thread(target=srv.run,daemon=True);thread.start()
try:
    deadline=time.monotonic()+5
    while not srv.started and time.monotonic()<deadline:time.sleep(.01)
    if not srv.started:raise RuntimeError('SYNTHETIC_HARNESS_START_FAILED')
    stream=io.BytesIO();rate=16000;duration=19
    with wave.open(stream,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(struct.pack('<'+'h'*(rate*duration),*[int(5000*math.sin(i*2*math.pi*330/rate)) for i in range(rate*duration)]))
    data=stream.getvalue();base=app.state.store.db.stat().st_size
    with httpx.Client(base_url=origin,headers={'Origin':origin},timeout=15) as c:
        response=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});response.raise_for_status()
        c.headers['X-CSRF-Token']=response.json()['csrf_token']
        id=str(uuid4());body={'audio_id':id,'operation_id':str(uuid4()),'content_hash':digest(data),'byte_size':len(data),'mime':'audio/wav','created_at_utc':'2099-01-01T00:00:00Z'}
        c.post('/api/v1/voice/audio',json=body).raise_for_status();latencies=[];start=time.perf_counter()
        for index in range((len(data)+CHUNK_SIZE-1)//CHUNK_SIZE):
            part=data[index*CHUNK_SIZE:(index+1)*CHUNK_SIZE];tick=time.perf_counter()
            r=c.post(f'/api/v1/voice/audio/{id}/chunks',json={'index':index,'content_hash':digest(part),'data':base64.b64encode(part).decode()});r.raise_for_status()
            latencies.append((time.perf_counter()-tick)*1000)
        transfer=time.perf_counter()-start;tick=time.perf_counter();c.post(f'/api/v1/voice/audio/{id}/finalize',json={}).raise_for_status();finalize=(time.perf_counter()-tick)*1000
        tick=time.perf_counter();c.post(f'/api/v1/voice/audio/{id}/transcribe',json={'mode':'FAKE'}).raise_for_status()
        while time.perf_counter()-tick<5:
            t=c.get(f'/api/v1/voice/audio/{id}').json()['transcript']
            if t['state']=='TRANSCRIPT_READY':break
            time.sleep(.005)
        if t['state']!='TRANSCRIPT_READY':raise RuntimeError('SYNTHETIC_ASR_FAILED')
        lifecycle=(time.perf_counter()-tick)*1000
    with app.state.store.connect() as db:
        logical=sum(len(json.dumps(dict(r),ensure_ascii=False).encode()) for table in ('audio','audio_chunks','transcripts') for r in db.execute('SELECT * FROM '+table))
    usage=resource.getrusage(resource.RUSAGE_SELF);cpu_start=usage.ru_utime+usage.ru_stime;idle_start=time.perf_counter();time.sleep(.4)
    idle=time.perf_counter()-idle_start;u=resource.getrusage(resource.RUSAGE_SELF)
    memory=u.ru_maxrss if platform.system()=='Darwin' else u.ru_maxrss*1024
    result={'scope':'SYNTHETIC_GENERATED_TONE_LOOPBACK_HTTP_FAKE_ASR_ONLY','audio_seconds':duration,'audio_bytes':len(data),
      'loopback_chunk_latency_ms':[round(x,3) for x in latencies],'loopback_upload_seconds':round(transfer,6),
      'loopback_payload_bytes_per_second':round(len(data)/transfer),'finalize_checksum_parse_fsync_db_ms':round(finalize,3),
      'fake_asr_lifecycle_http_ms':round(lifecycle,3),'fake_asr_worker_ms':round(t['elapsed']*1000,3),
      'attachment_disk_bytes':sum(f.stat().st_size for f in app.state.voice.root.iterdir()),
      'db_bytes_before':base,'db_bytes_after':app.state.store.db.stat().st_size,'db_growth_bytes':app.state.store.db.stat().st_size-base,'voice_logical_metadata_utf8_bytes':logical,
      'idle_observation_seconds':round(idle,3),'idle_process_cpu_seconds':round(u.ru_utime+u.ru_stime-cpu_start,6),
      'harness_max_rss_bytes':memory,'real_model':'LOCAL_ASR_BACKEND_NOT_RUN','UA_accuracy':'NOT_RUN','Galaxy':'NOT_RUN',
      'limitations':'One synthetic local harness observation, not real inference latency, hardware quality, accuracy or a cross-version idle regression guarantee.'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
    srv.should_exit=True;thread.join(8);shutil.rmtree(root)
