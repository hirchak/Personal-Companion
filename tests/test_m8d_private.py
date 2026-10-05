"""M8D production private semantics on ORIGINAL SYNTHETIC fixtures only; no real-vault/provider access."""
import json,threading
from uuid import uuid4
import pytest
from apps.core.storage import Store,SafeError,encode
from apps.core.root_types import RootKind
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation
from apps.core.conversation_controller import ConversationController
from apps.core.local_private_ai import PrivatePilotGate,OwnerAcknowledgement,ACK_KEYS,PROFILE_ID
from apps.core.local_private_contracts import DurableConsentAcceptance,PrivateContextPreview,PrivateInferenceStart
from apps.core.reflection_contracts import GoalChange,GoalCreate
from apps.core.deep_session_contracts import ContextBinding,ContextSelection
from apps.core.live_evaluation_budget import M8DEvaluationBudget
from apps.core.domain import Journal
from test_m1_domain import isolated,create
from test_m8a_release import package
from test_m8b_readiness import runtime_package
from test_m8c_private import private_package,protected
from test_m7c_controller import finish


@pytest.fixture
def private_ai_package(private_package):
 from apps.core import release as r
 from apps.core.local_private_ai import PROFILE
 from apps.core.storage import digest
 pkg,_=private_package
 (pkg/'packages/pilot/MAC_PRIVATE_AI_VOICE_PROFILE.json').write_text(encode(PROFILE))
 m=r.read_json(pkg/'release-manifest.json');m.update(format=4,release_id='M8D-'+m['git_commit'])
 m['files']=r.file_hashes(pkg);m['manifest_hash']=r.identity(m);(pkg/'release-manifest.json').write_text(encode(m))
 return pkg,m['manifest_hash']

@pytest.fixture
def vault(private_ai_package,isolated,protected):
 from apps.core import release as r,local_private as p
 pkg,h=private_ai_package;app,data,b=isolated/'app',isolated/'PRIVATE_LOCAL_ORIGINAL_SYNTHETIC_ONLY',isolated/'protected backups'
 b.mkdir(mode=0o700)
 r.initialize_private(pkg,h,app,data,b,'INITIALIZE_PRIVATE_LOCAL:'+str(data),p.CONSENT,True)
 return pkg,h,app,data,b

class PrivateFixtureProvider:
 def __init__(self,model,effort):self.model=model;self.effort=effort;self.calls=[]
 def metadata(self):return {'route':'CODEX_SUBSCRIPTION','model':self.model,'effort':self.effort,'profile':self.model+':'+self.effort,'live':False,'fallback':False,'payg':False}
 def execute(self,payload,schema,cancel,deadline,on_delta=None):
  self.calls.append(payload)
  candidate={'assistant_text':'ORIGINAL SYNTHETIC · Один нейтральний наступний крок?','source_refs':[payload['current_message_ref']],'goal_suggestion':None,'closure':None,'topics':['self_reflection'],'working_map':None}
  return {'text':encode(candidate),'route':'CODEX_SUBSCRIPTION','model':self.model,'effort':self.effort,'profile':self.model+':'+self.effort,'profile_verified':True}

def acknowledgement():return dict(profile_id=PROFILE_ID,**{k:True for k in ACK_KEYS})

@pytest.fixture
def controller(vault):
 _,_,_,root,_=vault;store=Store(root,root_kind=RootKind.PRIVATE_LOCAL)
 gate=PrivatePilotGate(store,provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort))
 c=ConversationController(Conversations(store,synthetic_demo=False,mock_responses=False),private_gate=gate,timeout=120)
 gate.revocation_hooks.append(c.revoke_private)
 gate.profile_change_hooks.append(c.revoke_private)
 return c,gate


def test_private_default_off_ack_settings_env_no_bypass(controller,monkeypatch):
 c,g=controller
 monkeypatch.setenv('OPENAI_API_KEY','ORIGINAL_SYNTHETIC_NOT_A_KEY');monkeypatch.setenv('PC_PRIVATE_AI','ON')
 assert g.status()['state']=='PRIVATE_AI_OFF' and c.status()['responder']=='OFF'
 for key in ACK_KEYS:
  body=acknowledgement();body[key]=False
  with pytest.raises(ValueError):g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',body)
  body[key]=1
  with pytest.raises(ValueError):g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',body)
 g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 assert g.provider('FREE').model=='gpt-6-luna' and g.provider('FREE').effort=='high'
 assert g.provider('DEEP').model=='gpt-6.1-sol' and g.provider('DEEP').effort=='high'
 g.disable();assert c.status()['responder']=='OFF'


def test_private_current_message_empty_journal_preview_and_personal_provenance(controller):
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 page=c.conversations.create(NewConversation(operation_id=uuid4()));id=page['conversation']['id']
 text='ORIGINAL SYNTHETIC · Перший нейтральний приватний-mode тест'
 preview=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=1,text=text))
 assert preview['journal_refs']==[]
 body=PrivateInferenceStart(operation_id=uuid4(),base_revision=1,text=text,owner_approved_external_text=True,context_binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash']))
 result=c.send(id,body);job=result['inference_job'];done=finish(c,job['id'])
 assert done['state']=='COMPLETED'
 payload=g.provider('FREE').calls[0];assert payload['synthetic'] is False and len(payload['context'])==1 and payload['tool_permissions']==[]
 page=c.conversations.get(id);assert not page['conversation']['synthetic'] and all(not m['synthetic'] for m in page['messages'])
 assert all(m['privacy_class']=='PRIVATE_PERSONAL' for m in page['messages'])


def test_private_no_preview_and_stale_journal_fail_before_transmission(controller):
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 page=c.conversations.create(NewConversation(operation_id=uuid4()));id=page['conversation']['id'];j=Journal(c.store)
 request,_=create(j,text='ORIGINAL SYNTHETIC selected journal')
 create(j,text='ORIGINAL SYNTHETIC unrelated hidden journal')
 text='ORIGINAL SYNTHETIC current draft'
 with pytest.raises(SafeError,match='PREVIEW_REQUIRED'):c.send(id,PrivateInferenceStart(operation_id=uuid4(),base_revision=1,text=text,owner_approved_external_text=True))
 preview=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=1,text=text,journal_entries=[{'id':request.entry_id,'revision':1}]))
 assert 'unrelated hidden' not in encode(preview)
 from apps.core.models import Patch
 j.write('edit',request.entry_id,Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'ORIGINAL SYNTHETIC changed'}))
 body=PrivateInferenceStart(operation_id=uuid4(),base_revision=1,text=text,owner_approved_external_text=True,context_binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash']))
 with pytest.raises(SafeError,match='JOURNAL_SELECTION_CHANGED'):c.send(id,body)
 assert not g.provider('FREE').calls and not c.conversations.get(id)['messages']


def test_m8d_ledger_budget_immutable_ceiling_checkpoint(isolated):
 path=isolated/'ORIGINAL_SYNTHETIC_budget.sqlite3';ledger=M8DEvaluationBudget(path)
 for i in range(4):
  id=str(uuid4());ledger.reserve(id,'CODEX_SUBSCRIPTION','gpt-6-luna');ledger.finish(id,'FAILED' if i==0 else 'COMPLETED')
 assert M8DEvaluationBudget(path).summary()['remaining']==0
 with pytest.raises(SafeError,match='LIVE_EVAL_LIMIT'):ledger.reserve(str(uuid4()),'CODEX_SUBSCRIPTION','gpt-6-sol')
 assert ledger.summary()['total_requests']==4


def test_private_api_ack_default_off_and_capability_boundary(vault):
 from fastapi.testclient import TestClient
 from apps.core.api import create_app
 _,_,_,root,_=vault
 app=create_app(root,root_kind=RootKind.PRIVATE_LOCAL,release_identity='ORIGINAL_SYNTHETIC_BUILD',m8d_private=True,private_provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort))
 with TestClient(app,base_url='http://127.0.0.1:8765') as c:
  c.headers.update({'Origin':'http://127.0.0.1:8765','X-PC-Build':'ORIGINAL_SYNTHETIC_BUILD'})
  response=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});c.headers['X-CSRF-Token']=response.json()['csrf_token']
  assert c.get('/api/v1/private-pilot/status').json()['state']=='PRIVATE_AI_OFF'
  body=acknowledgement();body.pop('codex_environments_off_confirmed')
  assert c.post('/api/v1/private-pilot/acknowledge',json=body).status_code==422
  assert c.post('/api/v1/private-pilot/acknowledge',json=acknowledgement()).status_code==200
  for path in ['health/import','sync/invitations','practices/start','device/pair','voice/audio','ai/mode','external-embeddings']:
   assert c.post('/api/v1/'+path,json={}).status_code==403
  assert c.post('/api/v1/private-pilot/disable',json={}).json()['state']=='PRIVATE_AI_OFF'


@pytest.mark.parametrize('model,effort',[('gpt-6.1-sol','xhigh'),('gpt-6.1-sol','max'),('gpt-6.1-sol','ultra'),('gpt-6-luna','ultra'),('gpt-6-sol','high')])
def test_final_owner_ceiling_rejected_before_any_process_or_attempt(model,effort,isolated):
 from apps.core.local_private_provider import PrivateCodexConversationProvider
 ledger=M8DEvaluationBudget(isolated/'ORIGINAL_SYNTHETIC_ceiling.sqlite3')
 with pytest.raises(SafeError,match='OWNER_MODEL_EFFORT_NOT_AUTHORIZED'):
  PrivateCodexConversationProvider(model=model,effort=effort,budget=ledger)
 assert ledger.summary()['total_requests']==0


def test_explicit_deep_choice_luna_max_sol_high_and_stale_preview(controller):
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 assert g.provider('DEEP').model=='gpt-6.1-sol' and g.provider('DEEP').effort=='high'
 page=c.conversations.create(NewConversation(operation_id=uuid4()));id=page['conversation']['id']
 text='ORIGINAL SYNTHETIC unchanged draft'
 preview=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=1,text=text))
 g.select_deep('ORIGINAL_SYNTHETIC_SESSION','DEEP_ECONOMICAL')
 assert g.provider('DEEP').model=='gpt-6-luna' and g.provider('DEEP').effort=='max'
 with pytest.raises(SafeError,match='PRIVATE_PROVIDER_BINDING_CHANGED'):
  c.send(id,PrivateInferenceStart(operation_id=uuid4(),base_revision=1,text=text,owner_approved_external_text=True,context_binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash'])))
 with pytest.raises(SafeError,match='PRIVATE_PROFILE_NOT_AVAILABLE'):g.select_deep('ORIGINAL_SYNTHETIC_SESSION','AUTOMATIC_FALLBACK')
 with pytest.raises(SafeError,match='PRIVATE_OWNER_ACK_REQUIRED'):g.select_deep('WRONG_SYNTHETIC_SESSION','DEEP_QUALITY')
 g.select_deep('ORIGINAL_SYNTHETIC_SESSION','DEEP_QUALITY')
 assert g.provider('DEEP').model=='gpt-6.1-sol'
 assert not any(p.calls for p in g.adapters.values())


def private_turn(c,id,text,refs=None,launch=True):
 page=c.conversations.get(id)
 preview=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,journal_entries=refs or []))
 body=PrivateInferenceStart(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,owner_approved_external_text=True,context_binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash']))
 result=c.send(id,body,launch=launch)
 return finish(c,result['inference_job']['id']) if launch else result['inference_job']


def test_private_journal_exact_selection_no_extra_conversation_context(controller):
 from apps.core.conversation_contracts import SendMessage
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 j=Journal(c.store);entry,_=create(j,text='ORIGINAL SYNTHETIC approved journal')
 create(j,text='ORIGINAL SYNTHETIC hidden journal')
 other=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 c.conversations.send(other,SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC hidden other conversation'),respond=False)
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 assert private_turn(c,id,'ORIGINAL SYNTHETIC current',refs=[{'id':entry.entry_id,'revision':1}])['state']=='COMPLETED'
 text=encode(g.provider('FREE').calls[-1]);assert 'approved journal' in text and 'hidden' not in text
 assert 'JOURNAL_SELECTED' in text and 'audio_hash' not in text
 with c.store.connect() as db:assert not db.execute('SELECT count(*) FROM memories').fetchone()[0]


@pytest.mark.parametrize('profile',['DEEP_ECONOMICAL','DEEP_QUALITY'])
def test_private_deep_agreed_goal_focus_journal_and_continuity(controller,profile):
 from apps.core.reflection_contracts import GoalCreate
 from apps.core.deep_session_contracts import SessionAction
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement());g.select_deep('ORIGINAL_SYNTHETIC_SESSION',profile)
 goal=c.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC agreed paper garden goal',user_agreed=True))
 id=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=goal['id'],goal_revision=1))['conversation']['id']
 c.deep.session_action(id,SessionAction(operation_id=uuid4(),base_revision=1,action='focus',focus='ORIGINAL SYNTHETIC agreed focus'))
 assert private_turn(c,id,'ORIGINAL SYNTHETIC first bounded step')['state']=='COMPLETED'
 assert private_turn(c,id,'ORIGINAL SYNTHETIC second step')['state']=='COMPLETED'
 payload=g.provider('DEEP').calls[-1]
 assert goal['text'] in encode(payload['context']) and payload['reflection_state']['focus']=='ORIGINAL SYNTHETIC agreed focus'
 assert 'first bounded step' in encode(payload) and payload['synthetic'] is False


def test_restart_interruption_and_no_auto_enable(controller):
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 job=private_turn(c,id,'ORIGINAL SYNTHETIC interrupted',launch=False)
 restarted_gate=PrivatePilotGate(c.store,provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort))
 restarted=ConversationController(Conversations(c.store,False,mock_responses=False),private_gate=restarted_gate)
 assert restarted.get(id,job['id'])['state']=='FAILED'
 assert restarted_gate.status()['state']=='PRIVATE_AI_OFF' and restarted.status()['responder']=='OFF'
 assert len(restarted.conversations.get(id)['messages'])==1


def test_private_backup_restore_default_off_preserves_conversation(controller,vault,isolated):
 from apps.core import release as r,local_private as p
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 assert private_turn(c,id,'ORIGINAL SYNTHETIC durable private conversation')['state']=='COMPLETED'
 pkg,h,app,root,b=vault;backup=b/'ORIGINAL_SYNTHETIC_M8D_BACKUP'
 result=r.backup(app,root,backup,root_kind=RootKind.PRIVATE_LOCAL)
 provenance=r.verify_backup(backup,h,result['backup_manifest_hash'])['release_provenance']
 assert provenance['producing_manifest']['release_id'].startswith('M8D-') and provenance['root_kind']=='PRIVATE_LOCAL'
 restored=isolated/'ORIGINAL_SYNTHETIC_RESTORED_PRIVATE';restored_app=isolated/'restored app'
 r.restore(pkg,h,backup,restored_app,restored,expected_producer_hash=h,expected_backup_hash=result['backup_manifest_hash'],root_kind=RootKind.PRIVATE_LOCAL,backup_directory=b,confirmation='INITIALIZE_PRIVATE_LOCAL:'+str(restored),consent=p.CONSENT,acknowledge_no_cloud=True)
 store=Store(restored,root_kind=RootKind.PRIVATE_LOCAL)
 gate=PrivatePilotGate(store,provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort))
 ctrl=ConversationController(Conversations(store,False,mock_responses=False),private_gate=gate)
 assert gate.status()['state']=='PRIVATE_AI_OFF' and len(ctrl.conversations.get(id)['messages'])==2
 assert all(not m['synthetic'] for m in ctrl.conversations.get(id)['messages'])


@pytest.mark.parametrize('wire_request',[b'CONNECT example.com:443 HTTP/1.1',b'CONNECT chatgpt.com:80 HTTP/1.1',b'CONNECT localhost:8765 HTTP/1.1',b'GET https://chatgpt.com/ HTTP/1.1',b'CONNECT chatgpt.com.evil:443 HTTP/1.1',b'CONNECT 127.0.0.1:443 HTTP/1.1'])
def test_fixed_transport_denies_every_other_destination(wire_request):
 from apps.core.local_provider_tunnel import connect_request
 assert not connect_request(wire_request+b'\r\n\r\n')


def test_fixed_transport_preserves_tls_blind_route():
 from apps.core.local_provider_tunnel import connect_request,DESTINATION
 assert DESTINATION==('chatgpt.com',443)
 assert connect_request(b'CONNECT chatgpt.com:443 HTTP/1.1\r\n\r\n')


def test_private_provider_actual_os_sentinels_outside_read_write_network_denied(isolated):
 import sys,subprocess
 from pathlib import Path
 from apps.core.local_private_provider import PrivateCodexConversationProvider
 if sys.platform!='darwin':pytest.skip('Native macOS OS boundary has separate reference-Mac evidence')
 work=isolated/'ORIGINAL_SYNTHETIC_PROVIDER_WORK';work.mkdir(mode=0o700)
 outside=isolated/'ORIGINAL_SYNTHETIC_PRIVATE_SENTINEL';outside.write_text('ORIGINAL SYNTHETIC ONLY');outside.chmod(0o600)
 source=work/'probe.c';probe=work/'probe'
 source.write_text('#include <stdio.h>\n#include <fcntl.h>\n#include <sys/socket.h>\n#include <arpa/inet.h>\n#include <errno.h>\nint main(int argc,char **argv){int r=open(argv[1],O_RDONLY);int w=open(argv[2],O_WRONLY|O_CREAT,0600);int s=socket(AF_INET,SOCK_STREAM,0);struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(443)};inet_pton(AF_INET,"192.0.2.1",&a.sin_addr);int n=connect(s,(struct sockaddr*)&a,sizeof(a));printf("read=%d write=%d network_denied=%d\\n",r>=0,w>=0,n<0&&errno==1);return 0;}')
 subprocess.run(['/usr/bin/clang',str(source),'-o',str(probe)],check=True,capture_output=True)
 provider=PrivateCodexConversationProvider(model='gpt-6-luna',effort='high',budget=M8DEvaluationBudget(work/'ORIGINAL_SYNTHETIC_budget.sqlite3'))
 policy=work/'probe.sb';policy.write_text(provider.os_profile(work)+'\n(allow process-exec (literal '+json.dumps(str(probe))+'))\n')
 result=subprocess.run(['/usr/bin/sandbox-exec','-f',str(policy),str(probe),str(outside),str(outside)+'.write'],capture_output=True,text=True,timeout=5)
 assert result.returncode==0 and 'read=0 write=0 network_denied=1' in result.stdout
 assert outside.read_text()=='ORIGINAL SYNTHETIC ONLY' and not Path(str(outside)+'.write').exists()
 assert provider.budget.summary()['total_requests']==0


@pytest.mark.parametrize('mode',['FAKE','DISABLED','CLOUD'])
def test_private_voice_gate_rejects_non_local_modes(vault,mode):
 from fastapi.testclient import TestClient
 from apps.core.api import create_app
 from apps.core.local_private_ai import LocalVoiceAcknowledgement
 class Engine:
  def metadata(self):return {'engine':'whisper.cpp','cloud_asr':False}
 _,_,_,root,_=vault
 app=create_app(root,root_kind=RootKind.PRIVATE_LOCAL,release_identity='ORIGINAL_SYNTHETIC_BUILD',m8d_private=True,private_asr_factory=Engine)
 with TestClient(app,base_url='http://127.0.0.1:8765') as c:
  c.headers.update({'Origin':'http://127.0.0.1:8765','X-PC-Build':'ORIGINAL_SYNTHETIC_BUILD'})
  r=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});c.headers['X-CSRF-Token']=r.json()['csrf_token']
  body={k:True for k in LocalVoiceAcknowledgement.model_fields}
  assert c.post('/api/v1/private-pilot/local-voice',json=body).status_code==200
  assert c.post('/api/v1/voice/audio/'+str(uuid4())+'/transcribe',json={'mode':mode,'language':'uk'}).status_code==403
  assert c.post('/api/v1/auth/lock',json={}).status_code==200
  assert app.state.private_gate.status()['local_voice']=='OFF' and 'LOCAL' not in app.state.voice.engines
  assert c.get('/api/v1/voice/audio').status_code==401


def test_private_voice_review_edit_explicit_send_no_audio_to_provider(vault):
 from apps.core.api import create_app
 from apps.core.voice_contracts import ASRRequest,TranscriptEdit
 from apps.core.conversation_contracts import VoiceSource
 from apps.core.storage import digest
 from test_m4_voice import save
 class Engine:
  def metadata(self):return {'engine':'whisper.cpp','cloud_asr':False,'model':'ORIGINAL_SYNTHETIC_FIXTURE','model_hash':'a'*64,'available':True}
  def transcribe(self,*args):return {'text':'ORIGINAL SYNTHETIC candidate only','language':'uk'}
 _,_,_,root,_=vault
 app=create_app(root,root_kind=RootKind.PRIVATE_LOCAL,release_identity='ORIGINAL_SYNTHETIC_BUILD',m8d_private=True,private_provider_factory=lambda mode,model,effort:PrivateFixtureProvider(model,effort),private_asr_factory=Engine)
 voice=app.state.voice;c=app.state.conversation_controller;g=app.state.private_gate
 g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 g.enable_voice('ORIGINAL_SYNTHETIC_SESSION',{'local_audio_only':True,'review_before_send':True,'manual_audio_deletion_understood':True});voice.engines['LOCAL']=g.asr
 audio,_=save(voice);job=voice.enqueue(audio,ASRRequest(mode='LOCAL'));voice.run(job['transcript_id'],'LOCAL');t=voice.get(audio)['transcript']
 assert not c.conversations.list()['items'] and not g.provider('FREE').calls
 voice.edit(t['id'],TranscriptEdit(revision=t['revision'],text='ORIGINAL SYNTHETIC owner reviewed and edited'));t=voice.get(audio)['transcript']
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 preview=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=1,text=t['edited']))
 source=VoiceSource(kind='VOICE_TRANSCRIPT',transcript_id=t['id'],revision=t['revision'],audio_hash=t['audio_hash'],text_hash=digest(t['edited'].encode()))
 body=PrivateInferenceStart(operation_id=uuid4(),base_revision=1,text=t['edited'],source_reference=source,owner_approved_external_text=True,context_binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash']))
 result=c.send(id,body);assert finish(c,result['inference_job']['id'])['state']=='COMPLETED'
 payload=encode(g.provider('FREE').calls[-1]);assert t['edited'] in payload and t['audio_hash'] not in payload and 'VOICE_TRANSCRIPT' not in payload
 assert not app.state.journal.list()['items']



def test_private_sdk_temporary_volume_gate_before_auth_reference_or_process(isolated,monkeypatch):
 from apps.core import local_private as p
 from apps.core.local_private_provider import PrivateCodexConversationProvider
 work=isolated/'ORIGINAL_SYNTHETIC_TEMPORARY_CLIENT';work.mkdir(mode=0o700)
 budget=M8DEvaluationBudget(isolated/'ORIGINAL_SYNTHETIC_TEMP_BUDGET.sqlite3')
 provider=object.__new__(PrivateCodexConversationProvider);provider.budget=budget
 monkeypatch.setattr(p,'volume_protection',lambda path:'NOT_RUN')
 with pytest.raises(SafeError,match='VOLUME_PROTECTION_REQUIRED'):provider.spec(work)
 assert not (work/'native-client').exists() and budget.summary()['total_requests']==0


def exact_preview_request(c,id,text,refs=None,purpose='REFLECT'):
 page=c.conversations.get(id)
 preview=c.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,purpose=purpose,journal_entries=refs or []))
 request=PrivateInferenceStart(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,purpose=purpose,owner_approved_external_text=True,context_binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash']))
 return preview,request


def assert_approved_provider_context(preview,payload,job):
 from apps.core.storage import digest
 assert preview['context']==payload['context']
 assert encode(preview['context'])==encode(payload['context'])
 assert preview['reflection_state']==payload['reflection_state']
 expected=digest(encode({'context':payload['context'],'reflection_state':payload['reflection_state']}).encode())
 assert preview['context_hash']==job['request_metadata']['context_hash']==expected
 assert preview['provider_request_hash']==digest(encode(payload).encode())
 assert [p['kind'] for p in payload['context']][-2:]==['CURRENT_TURN','JOURNAL_SELECTED']


@pytest.mark.parametrize('history',[0,2])
def test_R01_free_exact_order_and_request_hash_including_explicit_journal(controller,history):
 from apps.core.conversation_contracts import SendMessage
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 for i in range(history):
  p=c.conversations.get(id);c.conversations.send(id,SendMessage(operation_id=uuid4(),base_revision=p['conversation']['revision'],text=f'ORIGINAL SYNTHETIC bounded history {i}'),respond=False)
 journal=Journal(c.store);selected,_=create(journal,text='ORIGINAL SYNTHETIC explicitly selected journal')
 create(journal,text='ORIGINAL SYNTHETIC UNSELECTED_SENTINEL_NO_TRANSMISSION')
 preview,body=exact_preview_request(c,id,'ORIGINAL SYNTHETIC exact current turn',[{'id':selected.entry_id,'revision':1}])
 job=c.send(id,body,launch=False)['inference_job']
 with c.store.connect() as db:
  data=c.row(db,job['id']);actual=c.request_for(db,data)
  assert actual==data['private_context']['provider_payload']
 assert_approved_provider_context(preview,actual,job)
 c.launch(job['id']);assert finish(c,job['id'])['state']=='COMPLETED'
 transmitted=g.provider('FREE').calls[0]
 assert_approved_provider_context(preview,transmitted,job)
 assert 'UNSELECTED_SENTINEL' not in encode(transmitted)
 for i in range(history):assert f'bounded history {i}' in encode(transmitted)
 assert len(transmitted['context'])==history+2
 assert 'audio_hash' not in encode(transmitted) and 'source_reference' not in encode(transmitted)


def test_R01_deep_exact_goal_focus_map_journal_and_reflection_approval(controller):
 from apps.core.reflection_contracts import GoalCreate
 from apps.core.conversation_contracts import SendMessage
 from apps.core.deep_session_contracts import SessionAction,MapItem
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 goal=c.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC agreed goal',user_agreed=True))
 id=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=goal['id'],goal_revision=1))['conversation']['id']
 p=c.conversations.send(id,SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC exact map source'),respond=False);source=p['messages'][0]
 c.deep.session_action(id,SessionAction(operation_id=uuid4(),base_revision=1,action='focus',focus='ORIGINAL SYNTHETIC agreed focus'))
 with c.store.transaction() as db:
  session=c.deep.session(db,id)
  item=MapItem(id=uuid4(),kind='TAKEAWAY',text='ORIGINAL SYNTHETIC confirmed fixture takeaway',provenance='USER_CONFIRMED',sources=[{'id':source['id'],'revision':1}]).model_dump(mode='json')
  c.deep.write(db,session,[item],{'provider_model':'ORIGINAL_SYNTHETIC_LOCAL_FIXTURE','provider_route':'LOCAL_EXPLICIT_FIXTURE','selected_skills':[],'request_hash':'a'*64})
 selected,_=create(Journal(c.store),text='ORIGINAL SYNTHETIC selected Deep journal')
 preview,body=exact_preview_request(c,id,'ORIGINAL SYNTHETIC Deep current',[{'id':selected.entry_id,'revision':1}])
 job=c.send(id,body)['inference_job'];assert finish(c,job['id'])['state']=='COMPLETED'
 payload=g.provider('DEEP').calls[0];assert_approved_provider_context(preview,payload,job)
 assert payload['reflection_state']['focus']=='ORIGINAL SYNTHETIC agreed focus'
 assert payload['reflection_state']['items'][0]['text']=='ORIGINAL SYNTHETIC confirmed fixture takeaway'
 assert goal['text'] in encode(payload['context'])
 assert payload['reflection_state']['items'][0]['source_refs']==['s0']


@pytest.mark.parametrize('phase',['before_send','queued'])
@pytest.mark.parametrize('mutation',['ordered_context','reflection_state','frame_hash'])
def test_R01_changed_approved_representation_fails_before_fixture_transmission(controller,phase,mutation):
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 selected,_=create(Journal(c.store),text='ORIGINAL SYNTHETIC selected journal')
 preview,body=exact_preview_request(c,id,'ORIGINAL SYNTHETIC current',[{'id':selected.entry_id,'revision':1}])
 if phase=='queued':job=c.send(id,body,launch=False)['inference_job']
 with c.store.transaction() as db:
  if phase=='before_send':
   data=json.loads(db.execute('SELECT payload FROM deep_context_previews WHERE receipt_id=?',(preview['receipt_id'],)).fetchone()[0]);target=data
  else:
   data=c.row(db,job['id']);target=data['private_context']
  if mutation=='ordered_context':target['provider_payload']['context'].reverse()
  elif mutation=='reflection_state':target['provider_payload']['reflection_state']={'focus':'ORIGINAL SYNTHETIC unapproved focus','phase':'OPEN','map_version':0,'items':[],'prior_closures':[]}
  else:target['provider_payload']['controller_frame_hash']='0'*64
  if phase=='before_send':db.execute('UPDATE deep_context_previews SET payload=? WHERE receipt_id=?',(encode(data),preview['receipt_id']))
  else:c.persist(db,data)
 if phase=='before_send':
  with pytest.raises(SafeError,match='PRIVATE_PREVIEW_CHANGED'):c.send(id,body)
 else:
  c.run(job['id']);assert c.get(id,job['id'])['state']=='FAILED'
 assert not g.provider('FREE').calls


@pytest.mark.parametrize('change',['draft','profile','journal','history'])
def test_R01_source_draft_profile_changes_invalidate_exact_approval(controller,change):
 from apps.core.conversation_contracts import SendMessage
 from apps.core.models import Patch
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 j=Journal(c.store);selected,_=create(j,text='ORIGINAL SYNTHETIC journal revision')
 preview,body=exact_preview_request(c,id,'ORIGINAL SYNTHETIC current draft',[{'id':selected.entry_id,'revision':1}])
 if change=='draft':body=body.model_copy(update={'text':'ORIGINAL SYNTHETIC unapproved draft'})
 elif change=='profile':g.select_deep('ORIGINAL_SYNTHETIC_SESSION','DEEP_ECONOMICAL')
 elif change=='journal':j.write('edit',selected.entry_id,Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'ORIGINAL SYNTHETIC edited journal'}))
 else:c.conversations.send(id,SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC history after preview'),respond=False)
 with pytest.raises(SafeError):c.send(id,body)
 assert not g.provider('FREE').calls


def test_R01_reordered_constructor_cannot_replace_frozen_approved_payload(controller,monkeypatch):
 from apps.core import local_private_context as private
 c,g=controller;g.acknowledge('ORIGINAL_SYNTHETIC_SESSION',acknowledgement())
 id=c.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
 selected,_=create(Journal(c.store),text='ORIGINAL SYNTHETIC selected journal')
 preview,body=exact_preview_request(c,id,'ORIGINAL SYNTHETIC current',[{'id':selected.entry_id,'revision':1}])
 original=private.canonical_private_payload
 def reordered(*args,**kwargs):
  payload,skills,aliases=original(*args,**kwargs);payload['context'].reverse();return payload,skills,aliases
 monkeypatch.setattr(private,'canonical_private_payload',reordered)
 with pytest.raises(SafeError,match='PRIVATE_EXACT_CONTEXT_CHANGED'):c.send(id,body)
 assert not g.provider('FREE').calls


# M8E-R01: preserve M7D-pinned goal revisions in durable Deep scope.
class PinnedGoalMapProvider(PrivateFixtureProvider):
    def __init__(self, model, effort, calls):
        super().__init__(model, effort)
        self.shared_calls = calls

    def execute(self, payload, schema, cancel, deadline, on_delta=None):
        result = super().execute(payload, schema, cancel, deadline, on_delta)
        self.shared_calls.append(payload)
        if payload['mode'] == 'DEEP':
            current = next(part for part in reversed(payload['context']) if part['kind'] == 'CURRENT_TURN')
            marker = 'REVISION_ONE' if 'REVISION_ONE' in current['text'] else 'REVISION_TWO'
            candidate = json.loads(result['text'])
            candidate['working_map'] = {'items': [{
                'kind': 'OBSERVATION',
                'text': 'ORIGINAL SYNTHETIC MAP_FROM_' + marker,
                'provenance': 'MODEL_DERIVED_SUMMARY',
                'source_refs': [payload['current_message_ref']],
            }]}
            result['text'] = encode(candidate)
        return result


def accept_private(gate):
    gate.accept_consent('ORIGINAL_SYNTHETIC_REVIEW_SESSION', DurableConsentAcceptance(
        version=gate.consent.contract()['version'],
        privacy_version=gate.consent.contract()['privacy_version'],
        accepted=True,
    ))

def deep_request(page, text):
    return PrivateInferenceStart(
        operation_id=uuid4(),
        base_revision=page['conversation']['revision'],
        text=text,
        owner_approved_external_text=True,
        standard_send=True,
    )


def completed(controller, conversation_id, text):
    page = controller.conversations.get(conversation_id)
    result = controller.send(conversation_id, deep_request(page, text))
    assert result['inference_job'] is not None
    final = finish(controller, result['inference_job']['id'])
    assert final['state'] == 'COMPLETED'
    return controller.conversations.get(conversation_id), final


def new_controller(store, calls):
    gate = PrivatePilotGate(
        store,
        provider_factory=lambda mode, model, effort: PinnedGoalMapProvider(model, effort, calls),
    )
    conversations = Conversations(store, synthetic_demo=False, mock_responses=False)
    controller = ConversationController(conversations, private_gate=gate, timeout=120)
    gate.revocation_hooks.append(controller.revoke_private)
    gate.profile_change_hooks.append(controller.revoke_private)
    gate.resume('ORIGINAL_SYNTHETIC_RESTART_SESSION')
    return controller, gate


def test_pinned_deep_revision_survives_goal_edit_reload_and_new_session(controller):
    current, gate = controller
    accept_private(gate)
    calls = []
    gate.adapters['DEEP_QUALITY'] = PinnedGoalMapProvider('gpt-6.1-sol', 'high', calls)

    goal_v1_text = 'ORIGINAL SYNTHETIC agreed goal revision one'
    goal_v2_text = 'ORIGINAL SYNTHETIC edited goal revision two'
    goal = current.context.create(GoalCreate(operation_id=uuid4(), text=goal_v1_text, user_agreed=True))
    old = current.conversations.create(NewConversation(
        operation_id=uuid4(), goal_id=goal['id'], goal_revision=1,
    ))
    old_id = old['conversation']['id']
    selection = ContextSelection()

    scope_v1 = gate.consent.scope(current, old_id, selection)
    assert scope_v1['goal']['revision'] == 1
    assert scope_v1['goal_text'] == goal_v1_text
    gate.consent.approve_scope(current, old_id, selection, scope_v1['scope_hash'])
    _, first = completed(current, old_id, 'ORIGINAL SYNTHETIC REVISION_ONE initial source')
    first_map = current.deep.read(old_id)['map']
    assert first_map['goal']['revision'] == 1
    assert first_map['items'][0]['text'] == 'ORIGINAL SYNTHETIC MAP_FROM_REVISION_ONE'

    changed = current.context.change(goal['id'], GoalChange(
        operation_id=uuid4(), base_revision=1, text=goal_v2_text, user_agreed=True,
    ))
    assert changed['revision'] == 2 and changed['state'] == 'ACTIVE'
    with current.store.connect() as db:
        assert current.context.row(db, goal['id'], 1).text == goal_v1_text

    # Simulate process restart/reload: consent, pinned binding, session, and map are read from SQLite.
    reopened_store = Store(current.store.root, root_kind=RootKind.PRIVATE_LOCAL)
    reopened, reopened_gate = new_controller(reopened_store, calls)
    resumed = reopened.conversations.get(old_id)
    resumed_session = reopened.deep.read(old_id)['session']
    resumed_scope = reopened_gate.consent.scope(reopened, old_id, selection)
    reopened_gate.consent.require_scope(reopened, old_id, selection)
    assert resumed['conversation']['goal_binding'] == {'id': goal['id'], 'revision': 1}
    assert resumed_session['goal'] == {'id': goal['id'], 'revision': 1}
    assert reopened.deep.read(old_id)['goal']['text'] == goal_v1_text
    assert resumed_scope['goal_text'] == goal_v1_text
    assert resumed_scope['scope_hash'] == scope_v1['scope_hash']
    assert resumed_scope['working_map']['items'][0]['text'] == 'ORIGINAL SYNTHETIC MAP_FROM_REVISION_ONE'

    _, continued = completed(reopened, old_id, 'ORIGINAL SYNTHETIC REVISION_ONE continuation')
    continued_payload = calls[-1]
    assert continued_payload['goal_revision'] == 1
    assert continued_payload['context'][0]['text'] == goal_v1_text
    assert continued_payload['reflection_state']['items'][0]['text'] == 'ORIGINAL SYNTHETIC MAP_FROM_REVISION_ONE'
    assert goal_v2_text not in encode(continued_payload)

    # A new conversation after the edit pins revision two and receives a separate map.
    fresh = reopened.conversations.create(NewConversation(
        operation_id=uuid4(), goal_id=goal['id'], goal_revision=2,
    ))
    fresh_id = fresh['conversation']['id']
    scope_v2 = reopened_gate.consent.scope(reopened, fresh_id, selection)
    assert scope_v2['goal']['revision'] == 2
    assert scope_v2['goal_text'] == goal_v2_text
    assert scope_v2['scope_hash'] != scope_v1['scope_hash']
    assert scope_v2['working_map'] is None
    reopened_gate.consent.approve_scope(reopened, fresh_id, selection, scope_v2['scope_hash'])
    _, second = completed(reopened, fresh_id, 'ORIGINAL SYNTHETIC REVISION_TWO new session source')
    second_payload = calls[-1]
    second_map = reopened.deep.read(fresh_id)['map']
    assert second_payload['goal_revision'] == 2
    assert second_payload['context'][0]['text'] == goal_v2_text
    assert second_map['goal']['revision'] == 2
    assert second_map['items'][0]['text'] == 'ORIGINAL SYNTHETIC MAP_FROM_REVISION_TWO'
    assert 'MAP_FROM_REVISION_TWO' not in encode(reopened.deep.read(old_id)['map'])
    assert 'MAP_FROM_REVISION_ONE' not in encode(second_map)


def test_pinned_deep_fails_closed_when_current_goal_is_paused(controller):
    current, gate = controller
    accept_private(gate)
    goal = current.context.create(GoalCreate(
        operation_id=uuid4(), text='ORIGINAL SYNTHETIC lifecycle goal', user_agreed=True,
    ))
    old = current.conversations.create(NewConversation(
        operation_id=uuid4(), goal_id=goal['id'], goal_revision=1,
    ))
    old_id = old['conversation']['id']
    selection = ContextSelection()
    scope = gate.consent.scope(current, old_id, selection)
    gate.consent.approve_scope(current, old_id, selection, scope['scope_hash'])
    current.context.change(goal['id'], GoalChange(
        operation_id=uuid4(), base_revision=1, state='PAUSED', user_agreed=True,
    ))
    assert current.conversations.get(old_id)['conversation']['goal_binding'] == {
        'id': goal['id'], 'revision': 1,
    }
    with pytest.raises(SafeError, match='GOAL_NOT_ACTIVE'):
        gate.consent.scope(current, old_id, selection)
    with pytest.raises(SafeError, match='GOAL_NOT_ACTIVE'):
        current.send(old_id, deep_request(current.conversations.get(old_id), 'ORIGINAL SYNTHETIC paused goal turn'))
    assert current.conversations.get(old_id)['messages'] == []
    assert gate.provider('DEEP').calls == []
