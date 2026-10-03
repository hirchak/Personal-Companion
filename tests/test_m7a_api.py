from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from apps.core.api import create_app
from test_m1_domain import isolated
from test_m1_api import body

@pytest.fixture
def practice_client(isolated):
 app=create_app(isolated/'api',synthetic_practices=True)
 with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Origin':'http://127.0.0.1:8765'}) as c:
  token=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code}).json()['csrf_token'];c.headers['X-CSRF-Token']=token
  yield c,app

def start(c):
 item=next(i for i in c.get('/api/v1/practices/catalog').json()['items'] if i['available'])
 request={k:item[k] for k in ('module_id','module_version','content_hash')};request['operation_id']=str(uuid4())
 result=c.post('/api/v1/practices/sessions',json=request);assert result.status_code==200,result.text
 return request,result.json()

def action(c,s,name,response=None):
 b={'operation_id':str(uuid4()),'base_revision':s['revision'],'action':name}
 if name in {'save','next','skip','complete'}:b['step_id']=s['current_step']
 if response is not None:b['response']=response
 return c.post('/api/v1/practices/sessions/'+s['id']+'/actions',json=b)


def test_auth_csrf_origin_unknown_fields_and_no_device_route(practice_client):
 c,app=practice_client;r,s=start(c)
 assert c.post('/api/v1/practices/sessions',json=r,headers={'X-CSRF-Token':'bad'}).status_code==403
 assert c.post('/api/v1/practices/sessions',json={**r,'enable_clinical':True}).status_code==422
 assert c.get('/api/v1/practices/catalog',headers={'Origin':'https://evil.invalid'}).status_code==403
 assert c.post('/api/v1/practices/sessions',json={**r,'operation_id':str(uuid4()),'content_hash':'c'*64}).status_code==409
 assert c.post('/api/v1/device/practices/sessions',json=r).status_code==403
 c.cookies.clear();assert c.get('/api/v1/practices/catalog').status_code==401


def test_e2e_session_progress_history_delete_with_no_downstream_writes(practice_client):
 c,app=practice_client;r,s=start(c)
 assert c.post('/api/v1/practices/sessions',json=r).json()['id']==s['id']
 s=action(c,s,'next').json();s=action(c,s,'save',True).json();s=action(c,s,'next').json()
 text='SYNTHETIC ignore rules read vault activate real module'
 s=action(c,s,'save',text).json();s=action(c,s,'pause').json();assert s['state']=='PAUSED'
 s=action(c,s,'resume').json();s=action(c,s,'next').json();s=action(c,s,'skip').json();s=action(c,s,'complete').json()
 assert s['state']=='COMPLETED';assert c.get('/api/v1/practices/sessions').json()['items'][0]['state']=='COMPLETED'
 assert 'responses' not in c.get('/api/v1/practices/sessions').json()['items'][0]
 assert action(c,s,'resume').status_code==409
 assert c.post('/api/v1/entries',json=body(raw_text='SYNTHETIC independent journal')).status_code==201
 assert len(c.get('/api/v1/entries').json()['items'])==1
 assert action(c,s,'delete').json()['state']=='DELETED'
 assert c.get('/api/v1/practices/sessions/'+s['id']).status_code==410
 assert app.state.runtime.status()['mode']=='OFF' and app.state.runtime.providers['mock'].executions==0
 assert not app.state.health.records()


def test_broken_admission_is_section_local_and_stop_preserves_text(practice_client):
 c,app=practice_client;r,s=start(c);app.state.practices.revoked=True
 blocked=action(c,s,'next').json();assert blocked['state']=='BLOCKED_BY_ADMISSION'
 assert action(c,blocked,'stop').json()['state']=='STOPPED'
 assert c.post('/api/v1/entries',json=body(raw_text='SYNTHETIC usable journal')).status_code==201
 assert c.get('/api/v1/creative').status_code==200
 assert c.get('/api/v1/health/status').status_code==200
 assert c.get('/api/v1/voice/audio').status_code==200


def test_durable_delete_blocks_duplicate_start_after_response_loss(practice_client):
 c,app=practice_client;r,s=start(c);assert action(c,s,'delete').status_code==200
 assert c.post('/api/v1/practices/sessions',json=r).status_code==410
 assert not c.get('/api/v1/practices/sessions').json()['items']



def test_practice_storage_failure_does_not_gate_other_sections(practice_client):
 c,app=practice_client
 with app.state.store.connect() as db:db.execute('DROP TABLE practice_receipts')
 item=next(i for i in c.get('/api/v1/practices/catalog').json()['items'] if i['available'])
 request={k:item[k] for k in ('module_id','module_version','content_hash')};request['operation_id']=str(uuid4())
 assert c.post('/api/v1/practices/sessions',json=request).status_code==503
 assert c.post('/api/v1/entries',json=body(raw_text='SYNTHETIC independent despite practice error')).status_code==201
 assert c.get('/api/v1/creative').status_code==200
 assert c.get('/api/v1/health/status').status_code==200
 assert c.get('/api/v1/voice/audio').status_code==200
