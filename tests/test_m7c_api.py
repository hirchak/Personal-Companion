from uuid import uuid4
import time
import pytest
from fastapi.testclient import TestClient
from apps.core.api import create_app
from test_m1_domain import isolated
from test_m7c_controller import FixtureProvider

@pytest.fixture
def client(isolated):
 app=create_app(isolated/'runtime-api',synthetic_conversations=True,m7c_synthetic=True,conversation_provider=FixtureProvider())
 with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Origin':'http://127.0.0.1:8765'}) as c:
  r=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});c.headers['X-CSRF-Token']=r.json()['csrf_token'];yield c,app

def test_runtime_endpoint_csrf_origin_scope_and_closure_no_goal_mutation(client):
 c,app=client;p=c.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json();id=p['conversation']['id'];body={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC explicit closure','purpose':'CLOSURE','synthetic_test_ack':True}
 assert c.post('/api/v1/conversations/'+id+'/inference',json=body,headers={'X-CSRF-Token':'bad'}).status_code==403
 assert c.post('/api/v1/conversations/'+id+'/inference',json={**body,'synthetic_test_ack':False}).status_code==422
 assert c.post('/api/v1/conversations/'+id+'/inference',json={**body,'skills':['sleep_review']}).status_code==422
 r=c.post('/api/v1/conversations/'+id+'/inference',json=body);assert r.status_code==200;j=r.json()['inference_job'];app.state.conversation_controller.workers[j['id']].join(2)
 d=c.get('/api/v1/conversations/'+id+'/inference/'+j['id']).json();assert d['state']=='COMPLETED' and d['candidate']['closure']
 assert not app.state.reflection.list()['items'] and not app.state.journal.list()['items']
 assert c.get('/api/v1/conversations/status',headers={'Origin':'https://evil.invalid'}).status_code==403
 c.cookies.clear();assert c.get('/api/v1/conversations/'+id+'/inference/'+j['id']).status_code==401


def test_provider_off_normal_default_has_no_live_activation(isolated):
 app=create_app(isolated/'normal')
 with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Origin':'http://127.0.0.1:8765'}) as c:
  r=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});c.headers['X-CSRF-Token']=r.json()['csrf_token']
  assert c.get('/api/v1/conversations/status').json()['responder']=='OFF'
  assert c.post('/api/v1/conversations/'+str(uuid4())+'/inference',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC','synthetic_test_ack':True}).status_code==403

def test_explicit_user_journal_preview_confirm_replay_and_stale_source(client):
 c,app=client;p=c.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json();id=p['conversation']['id'];url='/api/v1/conversations/'+id
 p=c.post(url+'/inference',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC · Власна думка про паперовий сад','synthetic_test_ack':True}).json();app.state.conversation_controller.workers[p['inference_job']['id']].join(2)
 messages=c.get(url).json()['messages'];user=messages[0];assistant=messages[1];source={'message_id':user['id'],'source_revision':1}
 assert c.post(url+'/journal-point/preview',json={'message_id':assistant['id'],'source_revision':1}).status_code==403
 preview=c.post(url+'/journal-point/preview',json=source).json();assert preview['raw_text']==user['raw_text'];assert not app.state.journal.list()['items']
 confirm={**source,'operation_id':str(uuid4()),'preview_hash':preview['preview_hash'],'user_confirmed':True}
 assert c.post(url+'/journal-point/confirm',json={**confirm,'user_confirmed':False}).status_code==422
 assert c.post(url+'/journal-point/confirm',json={**confirm,'preview_hash':'0'*64}).status_code==409
 r=c.post(url+'/journal-point/confirm',json=confirm);assert r.status_code==200;assert c.post(url+'/journal-point/confirm',json=confirm).json()==r.json()
 assert len(app.state.journal.list()['items'])==1 and app.state.journal.get(r.json()['entry_id'])['raw_text']==user['raw_text']
 with app.state.store.transaction() as db:db.execute('UPDATE conversation_messages SET payload=json_set(payload,"$.revision",2) WHERE id=?',(user['id'],))
 assert c.post(url+'/journal-point/confirm',json={**confirm,'operation_id':str(uuid4())}).status_code==409
