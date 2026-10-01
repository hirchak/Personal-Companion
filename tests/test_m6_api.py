from uuid import uuid4
import pytest
from test_m1_api import client,body
from test_m1_domain import isolated
from m6_fixtures import batch,record

@pytest.mark.parametrize('route',['status','records'])
def test_health_private_read_boundary(client,route):
    c,app=client;assert c.get('/api/v1/health/'+route).status_code==200
    assert c.get('/api/v1/health/'+route,headers={'Origin':'https://evil.invalid'}).status_code==403
    c.cookies.clear();assert c.get('/api/v1/health/'+route).status_code==401

def request(c,b,reconnect=False):return {'batch':b.model_dump(),'generation':c.get('/api/v1/health/status').json()['generation'],'reconnect':reconnect}

def test_api_import_validation_csrf_replay_delete_and_self_report(client):
    c,app=client;b=batch(record());r=request(c,b)
    assert c.post('/api/v1/health/import',json=r,headers={'X-CSRF-Token':'bad'}).status_code==403
    assert c.post('/api/v1/health/import',json={**r,'shell':'SYNTHETIC'}).status_code==422
    assert c.post('/api/v1/health/import',json=r).json()['result']=='IMPORTED'
    assert c.post('/api/v1/health/import',json=r).json()['result']=='IDEMPOTENT_REPLAY'
    assert not c.get('/api/v1/entries').json()['items']
    gen=r['generation'];assert c.post('/api/v1/health/delete',json={'generation':gen}).status_code==200
    assert not c.get('/api/v1/health/records').json()['items']
    assert c.post('/api/v1/health/import',json=r).status_code==409
    assert c.post('/api/v1/health/import',json=request(c,b)).status_code==409
    assert c.post('/api/v1/health/import',json=request(c,b,True)).status_code==200
    assert app.state.runtime.status()['mode']=='OFF' and app.state.runtime.providers['mock'].executions==0

def test_health_sql_metadata_is_data_no_provider_or_memory(client):
    c,app=client;b=batch(record(origin="SYNTHETIC '; DROP TABLE entries; -- shell()"))
    assert c.post('/api/v1/health/import',json=request(c,b)).status_code==200
    assert not c.get('/api/v1/entries').json()['items']
    assert c.post('/api/v1/entries',json=body(raw_text='SYNTHETIC ordinary note')).status_code==201
    assert app.state.runtime.providers['mock'].executions==0
    with app.state.store.connect() as db:assert db.execute('SELECT count(*) FROM memories').fetchone()[0]==0
    # Imported opaque IDs cannot enter the journal-only M3 selector.
    from apps.core.ai_contracts import PreviewRequest
    from apps.core.storage import SafeError
    id=app.state.health.records()[0]['local_id']
    with pytest.raises(SafeError,match='NOT_FOUND'):
        app.state.runtime.preview(PreviewRequest(task='organize_selected',entries=[{'id':id,'revision':1}]), 'SYNTHETIC-session')

def test_import_commit_failure_preserves_checkpoint(client):
    c,app=client;b=batch(record());state=app.state.health.status();app.state.store.fail_commit=True
    assert c.post('/api/v1/health/import',json={'batch':b.model_dump(),'generation':state['generation']}).status_code==503
    app.state.store.fail_commit=False;assert app.state.health.records()==[] and app.state.health.status()==state

def test_no_write_or_ai_health_routes_and_phone_status_auth(client):
    c,app=client
    for path in ('health/write','health/source/delete','health/ai','health/background','health/history'):
        assert c.post('/api/v1/'+path,json={}).status_code in (404,405)
    assert c.get('/api/v1/device/health/status').status_code==403

def test_paired_phone_status_has_no_values_and_device_revoke_stops_access(isolated):
    from apps.core.api import create_app
    from fastapi.testclient import TestClient
    from test_m2_sync import pairing,ORIGIN
    app=create_app(isolated/'phone-status',m2=True);p=pairing(app);app.state.health.apply(batch(record()))
    headers={'Authorization':'Bearer '+p['credential'],'X-Device-ID':p['device_id'],'X-Sync-Epoch':p['epoch']}
    with TestClient(app,base_url=ORIGIN) as c:
        response=c.get('/api/v1/device/health/status',headers=headers)
        assert response.status_code==200;assert response.json()['availability']['steps']=='VALUE';assert 'count' not in response.text and 'source_id' not in response.text
        assert c.get('/api/v1/device/health/records',headers=headers).status_code==404
        app.state.sync.revoke(p['device_id'])
        assert c.get('/api/v1/device/health/status',headers=headers).status_code==403
