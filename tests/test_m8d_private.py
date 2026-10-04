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
from apps.core.local_private_contracts import PrivateContextPreview,PrivateInferenceStart
from apps.core.deep_session_contracts import ContextBinding
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
