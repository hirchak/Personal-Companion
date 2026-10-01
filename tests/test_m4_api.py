"""Actual HTTP boundary via test client, synthetic PCM and credentials only."""
import base64,time
from uuid import uuid4
import pytest
from test_m1_api import client,ORIGIN
from test_m1_domain import isolated
from test_m4_voice import wav,begin,chunk
from apps.core.sync import Pair
from apps.core.storage import digest

def save_http(c,prefix='/api/v1/voice',headers=None):
    data=wav();b=begin(data).model_dump(mode='json')
    r=c.post(prefix+'/audio',json=b,headers=headers);assert r.status_code==200,r.text
    id=b['audio_id'];r=c.post(f'{prefix}/audio/{id}/chunks',json=chunk(data,0).model_dump(),headers=headers);assert r.status_code==200,r.text
    r=c.post(f'{prefix}/audio/{id}/finalize',json={},headers=headers);assert r.status_code==200,r.text
    return id,r.json()

def test_M4_A07_A12_HTTP_candidate_confirm_provider_OFF(client):
    c,app=client;id,r=save_http(c)
    assert r['state']=='MAC_AUDIO_CONFIRMED'
    assert c.get('/api/v1/voice/audio').headers['permissions-policy']=='camera=(), microphone=(self), geolocation=()'
    r=c.post(f'/api/v1/voice/audio/{id}/transcribe',json={'mode':'DISABLED'});assert r.status_code==409 and r.json()['code']=='LOCAL_ASR_BACKEND_NOT_RUN'
    r=c.post(f'/api/v1/voice/audio/{id}/transcribe',json={'mode':'FAKE','language':'uk'});assert r.status_code==200,r.text
    deadline=time.monotonic()+2
    while time.monotonic()<deadline:
        t=c.get(f'/api/v1/voice/audio/{id}').json()['transcript']
        if t['state']=='TRANSCRIPT_READY':break
        time.sleep(.01)
    assert t['state']=='TRANSCRIPT_READY' and not app.state.journal.list()['items']
    assert c.post(f"/api/v1/voice/transcripts/{t['id']}/edit",json={'revision':1,'text':'SYNTHETIC explicit user text'}).status_code==200
    request={'revision':2,'operation_id':str(uuid4()),'entry_id':str(uuid4()),'base_revision':0,'retention':'KEEP'}
    assert c.post(f"/api/v1/voice/transcripts/{t['id']}/confirm",json=request).status_code==200
    assert app.state.journal.get(request['entry_id'])['raw_text']=='SYNTHETIC explicit user text'
    assert app.state.runtime.status()['mode']=='OFF' and not app.state.runtime.jobs()['items']
    assert app.state.runtime.providers['mock'].executions==0

@pytest.mark.parametrize('case',['path','query','mime','body','auth'])
def test_M4_A05_A12_HTTP_bounds_paths_credentials(client,case):
    c,app=client;b=begin(wav()).model_dump(mode='json');path='/api/v1/voice/audio'
    if case=='path':b['destination']='../../not-allowed'
    if case=='mime':b['mime']='audio/webm'
    if case=='query':path+='?token=SYNTHETIC-forbidden'
    if case=='body':b['extra']='x'*400001
    if case=='auth':c.cookies.clear()
    r=c.post(path,json=b);assert r.status_code in {401,403,413,422}
    assert not app.state.voice.list()['items']
    assert 'SYNTHETIC-forbidden' not in r.text and '../../not-allowed' not in r.text

def test_M4_A04_HTTP_device_finalization_revocation(client):
    c,app=client;app.state.m2=True
    # create_app m2 boundary is closure, so use separate explicitly m2 harness.
    from apps.core.api import create_app
    from fastapi.testclient import TestClient
    app2=create_app(app.state.store.root.parent/'paired',m2=True)
    p=app2.state.sync.pair(Pair(invitation=app2.state.sync.invite()['invitation'],device_id=uuid4(),label='SYNTHETIC'))
    app2.state.sync.finalize(p['device_id'],p['credential'],p['epoch'])
    headers={'Origin':ORIGIN,'Authorization':'Bearer '+p['credential'],'X-Device-ID':p['device_id'],'X-Sync-Epoch':p['epoch']}
    with TestClient(app2,base_url=ORIGIN) as phone:
        id,_=save_http(phone,'/api/v1/device/voice',headers)
        assert phone.get('/api/v1/device/voice/audio',headers=headers).status_code==200
        app2.state.sync.revoke(p['device_id'])
        assert phone.post(f'/api/v1/device/voice/audio/{id}/finalize',headers=headers,json={}).status_code==403
