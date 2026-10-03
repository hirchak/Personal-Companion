from uuid import uuid4
import time
import pytest
from fastapi.testclient import TestClient
from apps.core.api import create_app
from apps.core.storage import digest
from apps.core.voice_contracts import TranscriptEdit
from test_m1_domain import isolated
from test_m4_voice import wav

@pytest.fixture
def client(isolated):
 app=create_app(isolated/'api',synthetic_conversations=True,synthetic_practices=True)
 with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Origin':'http://127.0.0.1:8765'}) as c:
  auth=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});c.headers['X-CSRF-Token']=auth.json()['csrf_token'];yield c,app

def new(c):
 body={'operation_id':str(uuid4())};r=c.post('/api/v1/conversations',json=body);assert r.status_code==200;return body,r.json()

def test_auth_csrf_origin_schema_role_and_practice_permission(client):
 c,app=client;b,x=new(c);id=x['conversation']['id'];m={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC payload'}
 assert c.post('/api/v1/conversations/'+id+'/messages',json=m,headers={'X-CSRF-Token':'bad'}).status_code==403
 assert c.post('/api/v1/conversations/'+id+'/messages',json={**m,'role':'ASSISTANT'}).status_code==422
 import json
 assert c.post('/api/v1/conversations/'+id+'/messages',content=json.dumps({**m,'text':'\ud800'},ensure_ascii=True),headers={'Content-Type':'application/json'}).status_code==422
 assert c.get('/api/v1/conversations',headers={'Origin':'https://evil.invalid'}).status_code==403
 r=c.post('/api/v1/conversations/'+id+'/messages',json=m);assert r.status_code==200 and len(r.json()['messages'])==2
 assert app.state.runtime.providers['mock'].executions==0 and not app.state.journal.list()['items']
 assert not app.state.practices.history()['items'] and app.state.practices.catalog()['production_active_clinical']==0
 c.cookies.clear();assert c.get('/api/v1/conversations/status').status_code==401


def test_malformed_responder_candidate_rollback(client):
 c,app=client;b,x=new(c)
 class Unsafe:
  def candidate(self):return {'role':'ASSISTANT','text':'fixture','provenance':'MOCK_SYNTHETIC','synthetic':True,'tool':'shell'}
 app.state.conversations.responder=Unsafe()
 # Domain validation rejects candidate before commit, never activates a tool.
 assert c.post('/api/v1/conversations/'+x['conversation']['id']+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC fixture'}).status_code==422
 assert not app.state.conversations.get(x['conversation']['id'])['messages']



def test_voice_source_exact_revision_and_fake_requires_demo(client):
 from test_m4_voice import save,candidate
 c,app=client;audio,_=save(app.state.voice);t=candidate(app.state.voice,audio)
 b,x=new(c);id=x['conversation']['id']
 source={'kind':'VOICE_TRANSCRIPT','transcript_id':t['id'],'revision':t['revision'],'audio_hash':t['audio_hash'],'text_hash':digest(t['candidate'].encode())}
 r=c.post('/api/v1/conversations/'+id+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC explicit user edited insertion','source_reference':source})
 assert r.status_code==200 and not app.state.journal.list()['items']
 source['revision']+=1
 assert c.post('/api/v1/conversations/'+id+'/messages',json={'operation_id':str(uuid4()),'base_revision':2,'text':'ORIGINAL SYNTHETIC stale','source_reference':source}).status_code==409
 source['revision']-=1;app.state.conversations.synthetic_demo=False
 assert c.post('/api/v1/conversations/'+id+'/messages',json={'operation_id':str(uuid4()),'base_revision':2,'text':'ORIGINAL SYNTHETIC fake cannot become real','source_reference':source}).status_code==409


def test_reflection_api_goal_context_csrf_and_source_scope(client):
 c,app=client
 body={'operation_id':str(uuid4()),'text':'ORIGINAL SYNTHETIC goal','user_agreed':True}
 assert c.post('/api/v1/reflection/goals',json=body,headers={'X-CSRF-Token':'bad'}).status_code==403
 g=c.post('/api/v1/reflection/goals',json=body).json();assert g['revision']==1
 cbody={'operation_id':str(uuid4()),'goal_id':g['id'],'goal_revision':1}
 created=c.post('/api/v1/conversations',json=cbody).json()
 request={'operation_id':str(uuid4()),'goal':{'id':g['id'],'revision':1},'conversation_id':created['conversation']['id']}
 built=c.post('/api/v1/reflection/context',json=request);assert built.status_code==200
 receipt=built.json()['receipt'];assert g['text'] not in str(receipt) and all('text' not in p for p in receipt['parts_meta']) and receipt['raw_text_logged'] is False
 assert c.post('/api/v1/reflection/expand',json={'receipt_id':receipt['id'],'sources':[{'id':str(uuid4()),'revision':1}]}).status_code==409
 assert c.post('/api/v1/reflection/context',json={**request,'shell':'inert'}).status_code==422
