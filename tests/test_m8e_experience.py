"""M8E exact payload/consent/scope regressions. ORIGINAL SYNTHETIC private roots only."""
from uuid import uuid4
import json
import pytest
from apps.core.storage import SafeError, encode, digest
from apps.core.local_private_ai import PrivatePilotGate
from apps.core.local_private_contracts import DurableConsentAcceptance,PrivateInferenceStart,PrivateContextPreview
from apps.core.deep_session_contracts import ContextSelection,SessionAction,ContextBinding
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.reflection_contracts import GoalCreate
from test_m8d_private import controller,vault,private_ai_package,PrivateFixtureProvider,acknowledgement
from test_m8c_private import private_package,protected
from test_m8b_readiness import runtime_package
from test_m8a_release import package
from test_m1_domain import isolated,create
from test_m7c_controller import finish
from apps.core.domain import Journal

def accept(g):
 return g.accept_consent('ORIGINAL_SYNTHETIC_SESSION',DurableConsentAcceptance(version=1,privacy_version=g.consent.contract()['privacy_version'],accepted=True))

def request(page,**kw):
 return PrivateInferenceStart(operation_id=uuid4(),base_revision=page['conversation']['revision'],text='ORIGINAL SYNTHETIC current paper garden',owner_approved_external_text=True,standard_send=True,**kw)

def test_durable_consent_restart_disable_revoke_and_version(controller,monkeypatch):
 c,g=controller
 assert not g.consent.read()
 accept(g);assert g.status()['consent'] and 'NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER' in encode(g.status())
 g.disable();assert g.consent.read() and not g.adapters
 resumed=PrivatePilotGate(c.store,provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort))
 resumed.resume('ORIGINAL_SYNTHETIC_SECOND_SESSION');assert resumed.adapters
 resumed.user_disable();assert not resumed.consent.read()['ai_enabled']
 resumed.resume('ORIGINAL_SYNTHETIC_SECOND_SESSION',enable=True);assert resumed.adapters
 from apps.core import local_consent
 monkeypatch.setattr(local_consent,'PRIVACY_VERSION','ORIGINAL_SYNTHETIC_CHANGED_VERSION')
 assert resumed.consent.read() is None
 with pytest.raises(SafeError,match='PRIVATE_AI_CONSENT_CHANGED'):resumed.require()
 with pytest.raises(SafeError,match='DURABLE_CONSENT_REQUIRED'):resumed.resume('ORIGINAL_SYNTHETIC_SECOND_SESSION')
 monkeypatch.undo()
 resumed.revoke_consent();assert resumed.consent.read() is None and not resumed.adapters


def test_normal_send_exact_free_clean_new_resume_no_journal(controller):
 c,g=controller;accept(g)
 journal=Journal(c.store);create(journal,text='ORIGINAL SYNTHETIC HIDDEN_JOURNAL_SENTINEL')
 old=c.conversations.create(NewConversation(operation_id=uuid4()));c.conversations.send(old['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC OTHER_CHAT_SENTINEL'),respond=False)
 p=c.conversations.create(NewConversation(operation_id=uuid4()));id=p['conversation']['id']
 result=c.send(id,request(p));done=finish(c,result['inference_job']['id']);assert done['state']=='COMPLETED'
 payload=g.provider('FREE').calls[-1];assert 'SENTINEL' not in encode(payload)
 with c.store.connect() as db:job=json.loads(db.execute('SELECT payload FROM conversation_inferences WHERE id=?',(done['id'],)).fetchone()[0])
 assert payload==job['private_context']['provider_payload']
 assert job['request_hash']==digest(encode(payload).encode())
 p=c.conversations.get(id);result=c.send(id,request(p));assert finish(c,result['inference_job']['id'])['state']=='COMPLETED'
 assert len(g.provider('FREE').calls[-1]['context'])==3
 assert c.conversations.get(id)['conversation']['title'].startswith('ORIGINAL SYNTHETIC current')
 assert not c.conversations.get(old['conversation']['id'])['conversation']['title']==p['conversation']['title']


def test_deep_scope_first_material_change_and_unrelated_fts(controller):
 c,g=controller;accept(g)
 free=c.conversations.create(NewConversation(operation_id=uuid4()));c.conversations.send(free['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC paper garden UNRELATED_FTS_SENTINEL'),respond=False)
 goal=c.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC paper garden',user_agreed=True))
 p=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=goal['id'],goal_revision=1));id=p['conversation']['id']
 with pytest.raises(SafeError,match='DEEP_SCOPE_APPROVAL_REQUIRED'):c.send(id,request(p))
 assert not c.conversations.get(id)['messages']
 scope=g.consent.scope(c,id,ContextSelection());g.consent.approve_scope(c,id,ContextSelection(),scope['scope_hash'])
 result=c.send(id,request(p));assert finish(c,result['inference_job']['id'])['state']=='COMPLETED'
 assert 'UNRELATED_FTS_SENTINEL' not in encode(g.provider('DEEP').calls[-1])
 session=c.deep.read(id)['session'];c.deep.session_action(id,SessionAction(operation_id=uuid4(),base_revision=session['revision'],action='focus',focus='ORIGINAL SYNTHETIC revised focus'))
 p=c.conversations.get(id)
 with pytest.raises(SafeError,match='DEEP_SCOPE_APPROVAL_REQUIRED'):c.send(id,request(p))
 assert c.conversations.get(id)['conversation']['goal_binding']=={'id':goal['id'],'revision':1}


def test_standard_send_cannot_silently_add_journal_explicit_approval_stale(controller):
 c,g=controller;accept(g)
 j=Journal(c.store);record,_=create(j,text='ORIGINAL SYNTHETIC selected paper note')
 p=c.conversations.create(NewConversation(operation_id=uuid4()));id=p['conversation']['id']
 # No journal field exists on the ordinary send contract.
 with pytest.raises(ValueError):PrivateInferenceStart.model_validate(dict(request(p).model_dump(mode='json'),journal_entries=[{'id':str(record.entry_id),'revision':1}]))
 exact=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=1,text=request(p).text,journal_entries=[{'id':record.entry_id,'revision':1}]))
 from apps.core.models import Patch
 j.write('edit',record.entry_id,Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'ORIGINAL SYNTHETIC revised paper note'}))
 body=request(p).model_copy(update={'context_binding':ContextBinding(receipt_id=exact['receipt_id'],context_hash=exact['context_hash'],preview_hash=exact['preview_hash'])})
 with pytest.raises(SafeError,match='JOURNAL_SELECTION_CHANGED'):c.send(id,body)
 assert not g.provider('FREE').calls


def test_private_capture_available_without_asr_and_waiting_history(vault):
 from fastapi.testclient import TestClient
 from apps.core.api import create_app
 from test_m4_voice import wav
 import base64
 _,_,_,root,_=vault
 app=create_app(root,root_kind=__import__('apps.core.root_types',fromlist=['RootKind']).RootKind.PRIVATE_LOCAL,release_identity='ORIGINAL_SYNTHETIC_BUILD',m8d_private=True,private_provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort))
 with TestClient(app,base_url='http://127.0.0.1:8765') as browser:
  browser.headers.update({'Origin':'http://127.0.0.1:8765','X-PC-Build':'ORIGINAL_SYNTHETIC_BUILD'})
  browser.headers['X-CSRF-Token']=browser.post('/api/v1/auth/unlock',json={'code':app.state.auth.code}).json()['csrf_token']
  assert browser.post('/api/v1/private-pilot/consent',json={'version':1,'privacy_version':app.state.private_gate.consent.contract()['privacy_version'],'accepted':True}).status_code==200
  data=wav(1);id=str(uuid4());meta={'audio_id':id,'operation_id':str(uuid4()),'content_hash':digest(data),'byte_size':len(data),'mime':'audio/wav','created_at_utc':'2026-10-05T10:00:00+00:00','timezone':'Europe/Warsaw','local_date':'2026-10-05','linked_entry_id':None}
  assert browser.post('/api/v1/voice/audio',json=meta).status_code==200
  assert browser.post('/api/v1/voice/audio/'+id+'/chunks',json={'index':0,'content_hash':digest(data),'data':base64.b64encode(data).decode()}).status_code==200
  assert browser.post('/api/v1/voice/audio/'+id+'/finalize',json={}).status_code==200
  assert browser.post('/api/v1/voice/audio/'+id+'/transcribe',json={'mode':'LOCAL','language':'uk'}).json()['code']=='LOCAL_ASR_BACKEND_NOT_RUN'
  assert browser.get('/api/v1/voice/audio').json()['items'][0]['ux_state']=='WAITING_FOR_LOCAL_ASR'
  assert app.state.voice.path(id).read_bytes()==data
  assert browser.post("/api/v1/private-pilot/revoke",json={}).status_code==200
  assert len(browser.get("/api/v1/voice/audio").json()["items"])==1
  assert browser.post("/api/v1/voice/audio",json=meta).status_code==403
  assert browser.post("/api/v1/voice/audio/"+id+"/delete",json={"confirm":True}).status_code==200
  assert not browser.get("/api/v1/voice/audio").json()["items"]
