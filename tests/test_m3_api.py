"""M3 same-origin authenticated API and M2-N01 server protocol regressions."""
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from apps.core.api import create_app
from apps.core.ai_contracts import MemoryCreate
from apps.core.sync import Pair
from apps.core.storage import SafeError
from test_m1_domain import isolated
from test_m1_api import client, body, ORIGIN


def test_M3_api_full_mock_context_memory_suggestion_flow(client):
    c,app=client;app.state.runtime.autostart=False
    b=body();assert c.post('/api/v1/entries',json=b).status_code==201
    ref={'id':b['entry_id'],'revision':1}
    assert c.get('/api/v1/ai/status').json()['mode']=='OFF'
    assert c.post('/api/v1/ai/mode',json={'mode':'LIVE'}).status_code==422
    assert c.post('/api/v1/ai/mode',json={'mode':'MOCK'}).status_code==200
    p=c.post('/api/v1/ai/preview',json={'task':'capture_classify','entries':[ref]}).json()
    assert c.post('/api/v1/ai/jobs',json={'consent_id':p['id'],'operation_id':str(uuid4())}).status_code==403
    assert c.post('/api/v1/ai/consents/'+p['id']+'/approve',json={'context_hash':p['context_hash']}).status_code==200
    j=c.post('/api/v1/ai/jobs',json={'consent_id':p['id'],'operation_id':str(uuid4())});assert j.status_code==201
    app.state.runtime.run_one()
    s=c.get('/api/v1/ai/suggestions').json()['items'][0]
    assert c.post('/api/v1/ai/suggestions/'+s['id'],json={'action':'edit','type':'daily','tags':['план']}).status_code==200
    assert c.get('/api/v1/entries/'+b['entry_id']).json()['raw_text']==b['payload']['raw_text']
    m=c.post('/api/v1/ai/memories',json={'content':'SYNTHETIC preference'}).json()
    assert c.get('/api/v1/ai/memories?q=preference').json()['items'][0]['provenance']=='USER_ENTERED'
    assert c.post('/api/v1/ai/memories/'+m['id'],json={'action':'edit','revision':1,'content':'SYNTHETIC correction'}).status_code==200
    assert c.post('/api/v1/ai/memories/'+m['id'],json={'action':'delete','revision':1}).status_code==409
    assert c.post('/api/v1/ai/memories/'+m['id'],json={'action':'delete','revision':2}).status_code==200
    assert c.post('/api/v1/ai/consents/'+p['id']+'/revoke',json={}).status_code==200


def test_M3_api_privacy_unknown_tools_invalid_unicode_and_boundaries(client,caplog):
    c,app=client
    sentinel='SYNTHETIC request data never in generic logs'
    assert c.post('/api/v1/ai/preview',json={'task':'run_sql','entries':[],'execute_shell':sentinel}).status_code==422
    r=c.post('/api/v1/ai/memories',content=b'{"content":"\\ud800"}',headers={'Content-Type':'application/json'});assert r.status_code==422
    assert sentinel not in caplog.text and 'execute_shell' not in r.text
    for route in ('mode','preview','jobs','memories'):
        assert c.post('/api/v1/ai/'+route,json={},headers={'X-CSRF-Token':'forged'}).status_code==403
    c.cookies.clear();assert c.get('/api/v1/ai/memories').status_code==401


def test_M2_N01_server_pending_write_failure_retry_revoke_restart(isolated):
    app=create_app(isolated/'pair',m2=True);sync=app.state.sync
    invite=sync.invite();req=Pair(invitation=invite['invitation'],device_id=uuid4(),label='SYNTHETIC persistence failed')
    p=sync.pair(req)
    assert sync.devices()['items'][0]['state']=='PENDING'
    # Phone fails its local encrypted commit: no finalize is sent. Pending is unusable.
    with pytest.raises(SafeError,match='PAIR_PENDING'):sync.snapshot(p['device_id'],p['credential'],p['epoch'])
    with pytest.raises(SafeError,match='PAIR_DENIED'):sync.pair(req)
    restarted=create_app(app.state.store.root,m2=True).state.sync
    with pytest.raises(SafeError,match='PAIR_PENDING'):restarted.snapshot(p['device_id'],p['credential'],p['epoch'])
    restarted.revoke(p['device_id'])
    with pytest.raises(SafeError,match='DEVICE_REVOKED'):restarted.finalize(p['device_id'],p['credential'],p['epoch'])
    # Owner gives a fresh one-use invitation; same device ID receives replacement credential.
    new=restarted.pair(Pair(invitation=restarted.invite()['invitation'],device_id=req.device_id,label='SYNTHETIC retry'))
    assert new['credential']!=p['credential']
    with pytest.raises(SafeError,match='DEVICE_DENIED'):restarted.finalize(p['device_id'],p['credential'],p['epoch'])
    assert restarted.finalize(new['device_id'],new['credential'],new['epoch'])['state']=='ACTIVE'
    assert restarted.finalize(new['device_id'],new['credential'],new['epoch'])['state']=='ACTIVE'
    assert restarted.snapshot(new['device_id'],new['credential'],new['epoch'])['entries']==[]


def test_M2_N01_pending_expiry_and_api_finalize_only_scope(isolated):
    app=create_app(isolated/'expired',m2=True);sync=app.state.sync
    p=sync.pair(Pair(invitation=sync.invite()['invitation'],device_id=uuid4(),label='SYNTHETIC pending'))
    with app.state.store.transaction() as db:db.execute('UPDATE devices SET pending_until=0')
    assert sync.devices()['items'][0]['state']=='PENDING_EXPIRED'
    with pytest.raises(SafeError,match='PAIR_PENDING'):sync.finalize(p['device_id'],p['credential'],p['epoch'])
    sync.revoke(p['device_id']);assert sync.devices()['items'][0]['state']=='REVOKED'


def test_M3_A11_phone_scope_never_inherits_ai_authority(isolated):
    app=create_app(isolated/'device',m2=True);sync=app.state.sync
    p=sync.pair(Pair(invitation=sync.invite()['invitation'],device_id=uuid4(),label='SYNTHETIC phone'))
    with TestClient(app,base_url=ORIGIN) as c:
        c.headers.update({'Origin':ORIGIN,'Authorization':'Bearer '+p['credential'],'X-Device-ID':p['device_id'],'X-Sync-Epoch':p['epoch']})
        assert c.get('/api/v1/device/snapshot').status_code==409
        assert c.post('/api/v1/device/finalize',json={}).status_code==200
        assert c.post('/api/v1/device/finalize',json={}).status_code==200
        assert c.get('/api/v1/device/snapshot').status_code==200
        assert c.post('/api/v1/ai/mode',json={'mode':'MOCK'}).status_code==401
        assert c.get('/api/v1/ai/memories').status_code==401
        assert c.get('/api/v1/device/ai/jobs').status_code==404
    assert app.state.runtime.providers['mock'].executions==0
