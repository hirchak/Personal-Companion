"""Final-C four-attempt native engineering ceiling. ORIGINAL SYNTHETIC disposable PRIVATE_LOCAL only.

Comparable Deep goal/focus/continuity cases are functional checks, not repeated benchmarking.
Fourth case combines confirmed genuine local-ASR text with explicit selected journal preview.
No owner vault, real microphone, new auth, account/billing route, fallback or LLM judge.
"""
import argparse,io,json,os,shutil,socket,subprocess,tempfile,threading,time,wave
from pathlib import Path
from uuid import uuid4
from apps.core import release as r,local_private as p
from apps.core.storage import REPO,Store,encode,digest,SafeError
from apps.core.root_types import RootKind
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation,SendMessage,VoiceSource
from apps.core.conversation_controller import ConversationController
from apps.core.local_private_ai import PrivatePilotGate,ACK_KEYS,PROFILE_ID
from apps.core.local_private_contracts import PrivateContextPreview,PrivateInferenceStart
from apps.core.local_private_provider import PrivateCodexConversationProvider
from apps.core.live_evaluation_budget import M8DEvaluationBudget
from apps.core.reflection_contracts import GoalCreate
from apps.core.deep_session_contracts import SessionAction,MapItem
from apps.core.domain import Journal
from apps.core.models import Create
from apps.core.voice import Voice,CHUNK_SIZE
from apps.core.sync import SyncService
from apps.core.voice_contracts import AudioBegin,AudioChunk,ASRRequest,TranscriptEdit,AudioDelete
from apps.core.whisper_local_asr import WhisperLocalASR


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--package',type=Path,required=True)
 parser.add_argument('--offline-fixture',action='store_true');parser.add_argument('--output',type=Path,default=REPO/'generated/m8d-native');a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=True);os.umask(0o077)
 manifest=r.read_json(a.package/'release-manifest.json');r.validate_package(a.package,manifest['manifest_hash']);assert manifest['format']==4
 if not a.offline_fixture:
  subprocess.run(['git','cat-file','-e',manifest['git_commit']+'^{commit}'],cwd=REPO,check=True,capture_output=True)
 for name in manifest['files']:
  if name.startswith('apps/core/') or name.startswith('skills/conversation/'):
   assert (REPO/name).is_file() and digest((REPO/name).read_bytes())==manifest['files'][name],'EXACT_C_NATIVE_SOURCE_REQUIRED'
 work=Path(tempfile.mkdtemp(prefix='m8d-original-synthetic-native-',dir=Path(tempfile.gettempdir()).resolve()));os.chmod(work,0o700)
 budget=M8DEvaluationBudget(work/'ORIGINAL_SYNTHETIC_OFFLINE_LEDGER.sqlite3' if a.offline_fixture else REPO/'generated/m8d-live-evaluation-ledger.sqlite3')
 if budget.summary()['total_requests']!=0:
  shutil.rmtree(work);raise SafeError('M8D_NATIVE_ATTEMPTS_ALREADY_RECORDED_NO_REPEAT',403)
 data,app,b=work/'PRIVATE_LOCAL_ORIGINAL_SYNTHETIC_ONLY',work/'app',work/'protected backups';b.mkdir(mode=0o700)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 results=[];comparisons=[];asr_proof=None
 def save_results():
  result={'scope':'PRIVATE_LOCAL_RUNTIME_WITH_ORIGINAL_SYNTHETIC_CONTENT','offline_fixture':a.offline_fixture,'implementation_sha':manifest['git_commit'],'release_id':manifest['release_id'],'manifest_hash':manifest['manifest_hash'],'budget':budget.summary(),'final_owner_profiles':{'FREE':'gpt-6-luna/high','DEEP_ECONOMICAL':'gpt-6-luna/max','DEEP_QUALITY':'gpt-6.1-sol/high'},'cases':results,'deep_comparison':comparisons,'local_asr':asr_proof,'real_private_data_used':0,'real_human_audio_used':0,'sol_above_high_attempts':0,'automatic_fallback':'NONE','payg':'NONE','new_billing_auth_account_route':'NONE','actual_private_ai_activation':'NOT_STARTED','human_ua_quality':'OPEN_HUMAN_TEST','llm_judge':'NOT_USED'}
  (a.output/'NATIVE_PRIVATE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 def send_case(label,id,text,refs=None,voice_source=None):
  page=controller.conversations.get(id);preview=controller.private_preview(id,PrivateContextPreview(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,journal_entries=refs or []))
  body=PrivateInferenceStart(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,owner_approved_external_text=True,source_reference=voice_source,context_binding={'receipt_id':preview['receipt_id'],'context_hash':preview['context_hash'],'preview_hash':preview['preview_hash']})
  before=budget.summary()['total_requests'];start=time.monotonic();response=controller.send(id,body,launch=False);job=response['inference_job']
  with store.connect() as c:
   internal=controller.row(c,job['id']);payload=controller.request_for(c,internal)
  assert payload['synthetic'] is False and not payload['tool_permissions']
  assert 'UNSELECTED_SENTINEL_MUST_NEVER_BE_SENT' not in encode(payload) and 'audio_hash' not in encode(payload)
  controller.launch(job['id']);print(label+' STARTED',flush=True)
  controller.workers[job['id']].join(125);d=controller.get(id,job['id']);assert d['state'] not in {'QUEUED','RUNNING'},'BOUNDED_WORKER_DID_NOT_STOP'
  value={'case':label,'state':d['state'],'error':d['error'],'model':d['request_metadata']['provider_model'],'effort':d['request_metadata']['provider_effort'],'profile':d['request_metadata']['provider_profile'],'request_hash':internal['request_hash'],'context_hash':d['request_metadata']['context_hash'],'context_parts':[part['kind'] for part in preview['context']],'journal_selection_count':len(refs or []),'raw_audio_in_payload':False,'synthetic_content_only':True,'production_record_synthetic':False,'elapsed_seconds':round(time.monotonic()-start,3),'new_attempts':budget.summary()['total_requests']-before,'candidate':d.get('candidate'),'provider_result':d.get('provider_result')}
  results.append(value);save_results();print(label+' '+d['state'],flush=True)
  if d['state']!='COMPLETED':raise SafeError(d['error'] or 'PRIVATE_NATIVE_FAILURE_STOP_NO_RETRY')
  assert value['new_attempts']==1
  return d
 try:
  preflight=p.preflight(a.package,manifest['manifest_hash'],app,data,b,port);assert preflight['status']=='PASS'
  r.initialize_private(a.package,manifest['manifest_hash'],app,data,b,'INITIALIZE_PRIVATE_LOCAL:'+str(data),p.CONSENT,True,port=port)
  from apps.core.network import deny_egress
  deny_egress()
  store=Store(data,root_kind=RootKind.PRIVATE_LOCAL)
  def factory(mode,model,effort):
   if not a.offline_fixture:return PrivateCodexConversationProvider(model=model,effort=effort,budget=budget)
   from scripts.verify_m8d_browser import FixtureProvider
   class OfflineProvider(FixtureProvider):
    def execute(self,payload,*args):
     attempt=str(uuid4());budget.reserve(attempt,'ORIGINAL_SYNTHETIC_OFFLINE_FIXTURE',self.model)
     result=super().execute(payload,*args);candidate=json.loads(result['text'])
     if payload['mode']=='DEEP':candidate['working_map']={'items':[{'kind':'QUESTION','text':'ORIGINAL SYNTHETIC · Посильний наступний крок?','provenance':'MODEL_DERIVED_SUMMARY','source_refs':[payload['current_message_ref']]}]}
     result['text']=encode(candidate);budget.finish(attempt,'COMPLETED');return result
   return OfflineProvider(model,effort)
  gate=PrivatePilotGate(store,provider_factory=factory)
  controller=ConversationController(Conversations(store,False,mock_responses=False),private_gate=gate,timeout=120);gate.revocation_hooks.append(controller.revoke_private);gate.profile_change_hooks.append(controller.revoke_private)
  gate.acknowledge('ORIGINAL_SYNTHETIC_ENGINEERING_OWNER_SESSION',dict(profile_id=PROFILE_ID,**{k:True for k in ACK_KEYS}))
  id=controller.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id']
  controller.conversations.send(id,SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC · Я працюю над паперовим садом і хочу почати з маленької чернетки.'),respond=False)
  send_case('FREE_LUNA_HIGH_CONTINUITY',id,'ORIGINAL SYNTHETIC · Сьогодні хочу зробити один малий крок до тієї чернетки. Допоможіть обрати його без вимоги ідеальності.')
  draft='ORIGINAL SYNTHETIC · Я вже вирішив, що малий крок достатній. Сьогодні знову відкладаю чернетку паперового саду. Допоможіть повернутися до погодженого фокусу й можливого наступного кроку; не оголошуйте причину встановленим фактом.'
  for profile,label in [('DEEP_ECONOMICAL','DEEP_LUNA_MAX_GOAL_FOCUS_CONTINUITY'),('DEEP_QUALITY','DEEP_SOL_HIGH_GOAL_FOCUS_CONTINUITY')]:
   gate.select_deep('ORIGINAL_SYNTHETIC_ENGINEERING_OWNER_SESSION',profile)
   goal=controller.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC · Починати маленьку чернетку паперового саду без вимоги ідеального результату.',user_agreed=True))
   cid=controller.conversations.create(NewConversation(operation_id=uuid4(),goal_id=goal['id'],goal_revision=1))['conversation']['id']
   page=controller.conversations.send(cid,SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC · Мені допомагає почати з одного невеликого кроку.'),respond=False);source=page['messages'][0]
   controller.deep.session_action(cid,SessionAction(operation_id=uuid4(),base_revision=1,action='focus',focus='ORIGINAL SYNTHETIC · Обрати посильний перший крок сьогодні.'))
   # Explicit original synthetic fixture state, not another LLM request or claimed real user acceptance.
   with store.transaction() as c:
    session=controller.deep.session(c,cid)
    item=MapItem(id=uuid4(),kind='TAKEAWAY',text='ORIGINAL SYNTHETIC · Один невеликий крок допомагає почати.',provenance='USER_CONFIRMED',sources=[{'id':source['id'],'revision':1}]).model_dump(mode='json')
    controller.deep.write(c,session,[item],{'provider_model':'ORIGINAL_SYNTHETIC_LOCAL_FIXTURE','provider_route':'LOCAL_EXPLICIT_FIXTURE','selected_skills':[],'request_hash':'a'*64})
   d=send_case(label,cid,draft);comparisons.append({'case':label,'same_goal_text_focus_draft_seeded_takeaway':True,'seed':'ORIGINAL_SYNTHETIC_USER_CONFIRMED_FIXTURE_NO_EXTRA_LLM','working_map_present':bool(d['candidate']['working_map']),'candidate_is_human_review_material':True});save_results()
  # Existing local Lesya TTS only; no human voice or cloud TTS. Confirm/edit before one explicit send.
  aiff=work/'ORIGINAL_SYNTHETIC.aiff';wav=work/'ORIGINAL_SYNTHETIC.wav'
  subprocess.run(['/usr/bin/say','-v','Lesya','-o',str(aiff),'Це оригінальний синтетичний тест. Маленький крок допомагає почати паперовий сад.'],check=True,capture_output=True)
  subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@16000','-c','1',str(aiff),str(wav)],check=True,capture_output=True)
  audio=wav.read_bytes();engine=WhisperLocalASR(REPO/'generated/local-asr',private_scope=True);voice=Voice(Journal(store),SyncService(Journal(store)));voice.engines['LOCAL']=engine;voice.timeout=120
  body=AudioBegin(audio_id=uuid4(),operation_id=uuid4(),content_hash=digest(audio),byte_size=len(audio),mime='audio/wav',created_at_utc='2099-01-01T12:00:00Z',local_date='2099-01-01');voice.begin(body)
  import base64
  for i in range((len(audio)+CHUNK_SIZE-1)//CHUNK_SIZE):
   chunk=audio[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE];voice.chunk(body.audio_id,AudioChunk(index=i,content_hash=digest(chunk),data=base64.b64encode(chunk).decode()))
  voice.finalize(body.audio_id);job=voice.enqueue(body.audio_id,ASRRequest(mode='LOCAL'));voice.run(job['transcript_id'],'LOCAL');t=voice.get(body.audio_id)['transcript'];assert t['state'] in {'TRANSCRIPT_READY','REVIEW_REQUIRED'}
  edited='ORIGINAL SYNTHETIC · Локальний транскрипт перевірено та відредаговано: хочу обрати малий крок для паперового саду. Врахуйте лише явно вибраний запис щоденника.'
  voice.edit(t['id'],TranscriptEdit(revision=t['revision'],text=edited));t=voice.get(body.audio_id)['transcript']
  asr_proof={'status':'PASS','scope':'ORIGINAL_SYNTHETIC_LESYA_TTS_PRIVATE_LOCAL','engine':engine.metadata(),'native_executions':engine.executions,'candidate_chars':len(t['candidate'] or ''),'reviewed_edited':True,'automatic_send':False,'raw_audio_external':False,'human_quality':'NOT_RUN'}
  journal=Journal(store);entry=uuid4();journal.write('create',entry,Create(operation_id=uuid4(),entry_id=entry,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC · У цьому явно вибраному записі я домовився дозволити собі коротку чернетку.'}))
  unselected=uuid4();journal.write('create',unselected,Create(operation_id=uuid4(),entry_id=unselected,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC UNSELECTED_SENTINEL_MUST_NEVER_BE_SENT'}))
  source=VoiceSource(kind='VOICE_TRANSCRIPT',transcript_id=t['id'],revision=t['revision'],audio_hash=t['audio_hash'],text_hash=digest(edited.encode()))
  cid=controller.conversations.create(NewConversation(operation_id=uuid4()))['conversation']['id'];send_case('CONFIRMED_LOCAL_ASR_EXPLICIT_JOURNAL_LUNA_HIGH',cid,edited,refs=[{'id':entry,'revision':1}],voice_source=source)
  voice.delete(body.audio_id,AudioDelete(confirm=True));gate.disable();assert budget.summary()['total_requests']==4
  save_results();print('M8D OFFLINE_FIXTURE four-scenario rehearsal completed' if a.offline_fixture else 'M8D exact-C bounded native private synthetic checks completed, attempts4',flush=True)
 except SafeError as exc:
  save_results();print('M8D NATIVE STOP '+exc.code+'; no automatic retry/fallback',flush=True);raise SystemExit(1)
 finally:
  if 'gate' in locals():gate.disable()
  shutil.rmtree(work)

if __name__=='__main__':main()
