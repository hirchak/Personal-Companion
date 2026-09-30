"""SYNTHETIC application boundary tests; no auth or payload evidence is printed."""
import json
from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from apps.core.api import create_app, Auth
from apps.core.domain import Journal
from test_m1_domain import isolated

ORIGIN = 'http://127.0.0.1:8765'

@pytest.fixture
def client(isolated):
    app = create_app(isolated / 'api')
    with TestClient(app, base_url=ORIGIN, raise_server_exceptions=False) as c:
        response = c.post('/api/v1/auth/unlock', headers={'Origin': ORIGIN}, json={'code': app.state.auth.code})
        assert response.status_code == 200
        c.headers.update({'Origin': ORIGIN, 'X-CSRF-Token': response.json()['csrf_token']})
        yield c, app


def body(kind='inbox', **payload):
    return {'operation_id': str(uuid4()), 'entry_id': str(uuid4()), 'base_revision': 0, 'payload': {'type': kind, 'raw_text': 'SYNTHETIC · api text 🦉', **payload}}

@pytest.mark.parametrize('kind',['inbox','daily','sleep','creative'])
def test_A07_api_crud(client, kind):
    c, app = client; b = body(kind)
    r = c.post('/api/v1/entries',json=b); assert r.status_code == 201
    assert 'raw_text' not in r.json() and r.json()['result_code']=='MAC_SAVED'
    id = b['entry_id']
    assert c.get('/api/v1/entries/'+id).json()['raw_text'] == b['payload']['raw_text']
    assert c.post('/api/v1/entries',json=b).json()==r.json()
    edit = {'operation_id':str(uuid4()),'base_revision':1,'changes':{'raw_text':'SYNTHETIC edited'}}
    assert c.patch('/api/v1/entries/'+id,json=edit).status_code==200
    assert c.get('/api/v1/entries/'+id+'/revisions').json()['items'][0]['raw_text']==b['payload']['raw_text']
    edit['operation_id']=str(uuid4()); assert c.patch('/api/v1/entries/'+id,json=edit).status_code==409
    assert c.request('DELETE','/api/v1/entries/'+id,json={'operation_id':str(uuid4()),'base_revision':2}).status_code==200
    assert c.get('/api/v1/entries/'+id).status_code==410
    assert c.post('/api/v1/entries',json=b).status_code==410


def test_A07_auth_host_origin_csrf(client):
    c, app = client
    assert c.get('/api/v1/status').json()['provider']=='OFF'
    for headers in [{'Host':'evil.invalid:8765'}, {'Origin':'http://evil.invalid'}, {'Origin':'null'}, {'Sec-Fetch-Site':'cross-site'}]:
        assert c.get('/api/v1/status',headers=headers).status_code==403
    assert c.get('/').status_code==200
    c.headers.pop('Origin')
    assert c.get('/api/v1/status').status_code==200
    assert c.post('/api/v1/entries',json=body()).status_code==403
    c.headers['Origin']=ORIGIN; c.headers['X-CSRF-Token']='forged'
    assert c.post('/api/v1/entries',json=body()).status_code==403
    c.cookies.clear()
    r=c.get('/api/v1/status'); assert r.status_code==401 and r.headers['cache-control']=='no-store'
    assert c.get('/api/v1/entries').status_code==401


def test_A07_unlock_once_ttl_rate_and_cookies(isolated):
    t=[0]; auth=Auth(lambda:t[0]); code=auth.code
    token,s=auth.unlock(code)
    with pytest.raises(Exception,match='UNLOCK_DENIED'): auth.unlock(code)
    t[0]=900
    with pytest.raises(Exception,match='LOCKED'): auth.session(token)
    a=Auth(lambda:t[0]); a.code_until=t[0]
    with pytest.raises(Exception,match='UNLOCK_DENIED'): a.unlock(a.code)
    a=Auth(lambda:t[0])
    for _ in range(5):
        with pytest.raises(Exception,match='UNLOCK_DENIED'): a.unlock('wrong')
    with pytest.raises(Exception,match='RATE'): a.unlock(a.code)
    a=Auth(lambda:t[0]); token,s=a.unlock(a.code); a.sessions[token]['created']=-30000
    with pytest.raises(Exception,match='LOCKED'): a.session(token)
    app=create_app(isolated/'cookies')
    with TestClient(app,base_url=ORIGIN) as c:
        r=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code},headers={'Origin':ORIGIN})
        cookie=r.headers['set-cookie']; assert 'HttpOnly' in cookie and 'SameSite=strict' in cookie and 'Domain=' not in cookie
        assert c.post('/api/v1/auth/lock',headers={'Origin':ORIGIN,'X-CSRF-Token':r.json()['csrf_token']},json={}).status_code==200
        assert c.get('/api/v1/status').status_code==401


def test_A07_owner_schema_errors_limits_logs(client, caplog):
    c, app=client; b=body()
    assert c.post('/api/v1/entries',json=b).status_code==201
    id=b['entry_id']
    with app.state.store.transaction() as db: db.execute('UPDATE entries SET owner_id=? WHERE id=?',(str(uuid4()),id))
    assert c.get('/api/v1/entries/'+id).status_code==404
    assert not c.get('/api/v1/entries').json()['items']
    bad=body(owner_id='SYNTHETIC_PRIVATE_SENTINEL')
    r=c.post('/api/v1/entries',json=bad); assert r.status_code==422
    assert 'SYNTHETIC_PRIVATE_SENTINEL' not in r.text and 'payload' not in r.text
    r=c.post('/api/v1/entries',content=b'x'*1048577,headers={'Content-Type':'application/json'}); assert r.status_code==413
    assert c.post('/api/v1/entries',json=body(raw_text='x'*100001)).status_code==422
    assert c.get('/api/v1/entries?q='+'x'*201).status_code==422
    assert c.get('/api/v1/entries?limit=101').status_code==422
    assert c.get('/api/v1/entries?type=invalid').status_code==422
    assert c.post('/api/v1/entries',content='secret=value',headers={'Content-Type':'application/x-www-form-urlencoded'}).status_code==415
    assert 'SYNTHETIC_PRIVATE_SENTINEL' not in caplog.text


@pytest.mark.parametrize('storage_error',['database or disk is full','attempt to write a readonly database','disk I/O error'])
def test_A02_storage_error_no_success(client,storage_error):
    c,app=client; b=body(); import sqlite3
    app.state.store.commit_error=sqlite3.OperationalError(storage_error)
    r=c.post('/api/v1/entries',json=b); assert r.status_code==503 and r.json()['code']=='STORAGE_UNAVAILABLE'
    assert 'raw_text' not in r.text
    app.state.store.commit_error=None
    assert c.post('/api/v1/entries',json=b).status_code==201


def test_A08_api_export_session_bound(client):
    c,app=client; b=body(); c.post('/api/v1/entries',json=b)
    assert c.post('/api/v1/exports/preview',json={}).status_code==422
    plan=c.post('/api/v1/exports/preview',json={'ids':[b['entry_id']]}).json()
    r=c.post('/api/v1/exports',json={'plan_id':plan['plan_id'],'format':'json'})
    assert r.status_code==200 and r.headers['cache-control']=='no-store' and r.json()['entries'][0]['id']==b['entry_id']
    token=c.cookies.get('m1_session'); app.state.journal.plans[plan['plan_id']]['session']='another'
    assert c.post('/api/v1/exports',json={'plan_id':plan['plan_id'],'format':'json'}).status_code==409
    app.state.journal.plans[plan['plan_id']]['session']=token
    c.request('DELETE','/api/v1/entries/'+b['entry_id'],json={'operation_id':str(uuid4()),'base_revision':1})
    assert c.post('/api/v1/exports',json={'plan_id':plan['plan_id'],'format':'json'}).status_code==409


def test_A10_process_egress_denial():
    import subprocess,sys
    code='''
from apps.core.network import deny_egress
import socket
from apps.core.storage import Store
from apps.core.domain import Journal
from apps.core.models import Create
from uuid import uuid4
import tempfile, pathlib
root=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path(tempfile.gettempdir()).resolve(),prefix='m1-egress-'))
deny_egress()
for address in [('203.0.113.1',443), ('example.invalid',443)]:
 try: socket.create_connection(address,timeout=.1)
 except PermissionError: pass
 else: raise AssertionError('egress not blocked')
actions=[
 lambda:socket.gethostbyname('example.invalid'),
 lambda:socket.gethostbyname_ex('example.invalid'),
 lambda:socket.gethostbyaddr('203.0.113.1'),
 lambda:socket.getnameinfo(('203.0.113.1',9),0),
 lambda:socket.getaddrinfo(None,9),
]
udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
actions += [lambda:udp.bind(('',0)), lambda:udp.bind(('0.0.0.0',0))]
actions += [lambda:udp.sendto(b'SYNTHETIC',('203.0.113.1',9))]
if hasattr(udp,'sendmsg'):
 actions += [lambda:udp.sendmsg([b'SYNTHETIC'],[],0,('203.0.113.1',9))]
for action in actions:
 try: action()
 except PermissionError: pass
 else: raise AssertionError('UDP/DNS egress not blocked')
udp.close()
s=Store(root/'data'); j=Journal(s)
r=Create(operation_id=uuid4(),entry_id=uuid4(),base_revision=0,payload={'raw_text':'SYNTHETIC offline'})
assert j.write('create',r.entry_id,r)['result_code']=='MAC_SAVED'
assert j.list(q='offline')['items']
import shutil; shutil.rmtree(root)
print('EGRESS_DENIED; offline save/search PASS')
'''
    r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert 'EGRESS_DENIED' in r.stdout


def test_openapi_fixture_matches_actual_adapter(client):
    from pathlib import Path
    from apps.core.storage import REPO
    _,app=client
    assert json.loads((REPO/'packages/contracts/openapi.json').read_text())==app.openapi()


def test_A01_response_and_recorded_history_contract(client):
    c, app = client
    b = body('sleep', sleep_start_utc='2026-10-25T02:30:00+02:00', wake_at_utc='2026-10-25T02:30:00+01:00',
             occurred_at_utc='2026-10-25T02:30:00+01:00', local_date='2026-10-25', time_precision='instant')
    assert c.post('/api/v1/entries', json=b).status_code == 201
    id = b['entry_id']
    original = c.get('/api/v1/entries/' + id).json()
    assert original['reported_interval_seconds'] == 3600
    assert 'mood_rating' not in original
    assert c.patch('/api/v1/entries/' + id, json={'operation_id':str(uuid4()),'base_revision':1,'changes':{'tags':['SYNTHETIC']}}).status_code == 200
    h = c.get('/api/v1/entries/' + id + '/revisions').json()['items'][0]
    assert h.pop('recorded_at_utc').endswith('Z') and h == original
    schema = app.openapi()['components']['schemas']
    assert 'recorded_at_utc' in schema['EntryRevisionOutput']['properties']
    assert 'revision' in schema['EntryOutput']['required']


@pytest.mark.parametrize('changes', [{'type':[]}, {'type':None}, {'mood_rating':float('nan')}, {'energy_rating':float('inf')}, {'owner_id':'SYNTHETIC-forbidden'}])
def test_A07_patch_invalid_values_are_schema_errors_without_changes(client, changes):
    c, app = client; b = body('daily')
    assert c.post('/api/v1/entries',json=b).status_code == 201
    original = c.get('/api/v1/entries/'+b['entry_id']).json()
    encoded = json.dumps({'operation_id':str(uuid4()),'base_revision':1,'changes':changes})
    r = c.patch('/api/v1/entries/'+b['entry_id'],content=encoded,headers={'Content-Type':'application/json'})
    assert r.status_code == 422
    assert r.json()['code'] == 'SCHEMA_INVALID'
    assert c.get('/api/v1/entries/'+b['entry_id']).json() == original
    assert c.get('/api/v1/entries/'+b['entry_id']+'/revisions').json()['items'] == []
