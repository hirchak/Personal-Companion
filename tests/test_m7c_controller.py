"""Deterministic offline controller tests. Fixture responses never claim live-provider quality."""
import json,threading,time
from uuid import uuid4
import pytest
from apps.core.storage import Store,SafeError,encode
from apps.core.conversation import Conversations
from apps.core.conversation_controller import ConversationController
from apps.core.conversation_contracts import NewConversation
from apps.core.conversation_runtime_contracts import InferenceStart,InferenceAction
from apps.core.reflection_contracts import GoalCreate
from test_m1_domain import isolated

class FixtureProvider:
 live=False
 def __init__(self,scenario='valid'):self.calls=0;self.scenario=scenario;self.started=threading.Event();self.release=threading.Event()
 def metadata(self):return {'route':'OFFLINE_FIXTURE','model':'original-synthetic-fixture','live':False,'auth_type':'NONE'}
 def execute(self,payload,response_schema,cancel,deadline,on_delta=None):
  self.calls+=1;self.started.set()
  if self.scenario=='wait':
   while not self.release.wait(.01):
    if cancel.is_set():raise SafeError('CANCELLED')
    if time.monotonic()>=deadline:raise SafeError('PROVIDER_TIMEOUT')
  if self.scenario=='fail':raise SafeError('PROVIDER_UNAVAILABLE')
  value={'assistant_text':'ORIGINAL SYNTHETIC fixture. Один нейтральний крок?','source_refs':[payload['current_message_ref']],'goal_suggestion':'ORIGINAL SYNTHETIC agreed wording' if payload['purpose']=='GOAL_PROPOSAL' else None,'closure':{'discussed':['ORIGINAL SYNTHETIC topic'],'clearer':'fixture','unresolved':'fixture','possible_steps':['fixture']} if payload['purpose']=='CLOSURE' else None,'topics':['self_reflection']}
  if self.scenario=='tool':value['tool']={'shell':'inert'}
  if self.scenario=='source':value['source_refs']=['s99']
  if self.scenario=='question':value['assistant_text']='one? two?'
  if on_delta:on_delta('{"assistant_text":"ORIGINAL SYNTHETIC partial')
  return {'text':encode(value),'elapsed_ms':1,'usage':None,'route':'OFFLINE_FIXTURE','model':'original-synthetic-fixture','auth_type':'NONE','streaming_actual':False}

@pytest.fixture
def controller(isolated):
 c=Conversations(Store(isolated/'controller'),True);return ConversationController(c,FixtureProvider(),timeout=1)
def new(c):return c.conversations.create(NewConversation(operation_id=uuid4()))
def body(page,purpose='REFLECT'):return InferenceStart(operation_id=uuid4(),base_revision=page['conversation']['revision'],text='ORIGINAL SYNTHETIC paper garden',purpose=purpose,synthetic_test_ack=True)
def finish(c,id):
 c.workers[id].join(3);assert not c.workers[id].is_alive()
 with c.store.connect() as db:return c.row(db,id)


def test_free_live_interface_fixture_binding_no_downstream_and_duplicate_send(controller):
 c=controller;p=new(c);b=body(p);result=c.send(p['conversation']['id'],b);id=result['inference_job']['id'];d=finish(c,id)
 assert d['state']=='COMPLETED' and c.provider.calls==1
 assert d['request_metadata']['selected_skills'][0]['skill_id']=='core_reflection'
 assert c.send(p['conversation']['id'],b)['inference_job']['id']==id and c.provider.calls==1
 assert len(c.conversations.get(p['conversation']['id'])['messages'])==2
 with c.store.connect() as db:
  for table in ('entries','memories','health_records','practice_sessions','feedback_drafts'):assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
  receipt=json.loads(db.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(d['request_metadata']['retrieval_receipt_id'],)).fetchone()[0]);assert receipt['goal'] is None
  assert 'text' not in d['request_metadata'] and 'payload' not in d['request_metadata']


def test_deep_goal_context_skills_and_explicit_closure(controller):
 c=controller;g=c.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC explicit goal',user_agreed=True));p=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=1))
 result=c.send(p['conversation']['id'],body(p,'CLOSURE'));d=finish(c,result['inference_job']['id']);assert d['state']=='COMPLETED'
 assert [s['skill_id'] for s in d['request_metadata']['selected_skills']]==['core_reflection','deep_session','session_closure']
 assert d['candidate']['closure'] and c.context.get(g['id'])['goal']['revision']==1
 assert c.conversations.get(p['conversation']['id'])['conversation']['state']=='ACTIVE'


@pytest.mark.parametrize('scenario,error',[('tool','MODEL_OUTPUT_INVALID'),('source','MODEL_SOURCE_OUT_OF_SCOPE'),('question','MAIN_QUESTION_LIMIT')])
def test_model_data_no_tool_write_or_authoritative_invalid_output(controller,scenario,error):
 c=controller;c.provider=FixtureProvider(scenario);p=new(c);r=c.send(p['conversation']['id'],body(p));d=finish(c,r['inference_job']['id']);assert d['state']=='FAILED' and d['error']==error
 assert len(c.conversations.get(p['conversation']['id'])['messages'])==1


def test_cancel_retry_exact_request_no_duplicate_and_ephemeral_partial(controller):
 c=controller;c.provider=FixtureProvider('wait');p=new(c);r=c.send(p['conversation']['id'],body(p));id=r['inference_job']['id'];assert c.provider.started.wait(1)
 with c.store.connect() as db:d=c.row(db,id)
 c.action(p['conversation']['id'],id,InferenceAction(operation_id=uuid4(),base_revision=d['revision'],action='cancel'));d=finish(c,id);assert d['state']=='CANCELLED'
 assert len(c.conversations.get(p['conversation']['id'])['messages'])==1
 c.provider=FixtureProvider();b=InferenceAction(operation_id=uuid4(),base_revision=d['revision'],action='retry');c.action(p['conversation']['id'],id,b);d=finish(c,id);assert d['state']=='COMPLETED'
 c.action(p['conversation']['id'],id,b);assert c.provider.calls==1 and len(c.conversations.get(p['conversation']['id'])['messages'])==2
 assert id not in c.previews


def test_context_drift_before_execution_fails_without_provider_call(controller):
 from apps.core.reflection_contracts import MessageEdit
 c=controller;p=new(c);r=c.send(p['conversation']['id'],body(p),launch=False);id=r['inference_job']['id'];page=c.conversations.get(p['conversation']['id']);m=page['messages'][0]
 c.context.edit_message(p['conversation']['id'],m['id'],MessageEdit(operation_id=uuid4(),base_conversation_revision=page['conversation']['revision'],base_message_revision=1,text='ORIGINAL SYNTHETIC user correction'))
 c.run(id)
 with c.store.connect() as db:d=c.row(db,id)
 assert d['state']=='FAILED' and c.provider.calls==0


def test_off_truth_and_specialized_skill_denial(controller):
 c=controller;c.provider=None;p=new(c);r=c.send(p['conversation']['id'],body(p));assert r['inference_job'] is None and r['responder']=='OFF' and len(r['messages'])==1
 with pytest.raises(SafeError,match='SKILL_OFF'):c.skills.read('sleep_review')

def test_restart_pending_and_backup_completed_receipts(controller,isolated):
 from apps.core.conversation_controller import check_inferences
 c=controller;p=new(c);r=c.send(p['conversation']['id'],body(p));finish(c,r['inference_job']['id'])
 with c.store.connect() as db:check_inferences(db)
 c.store.backup(isolated/'runtime-backup');restored=Store.restore(isolated/'runtime-backup',isolated/'runtime-restored')
 resumed=ConversationController(Conversations(Store(isolated/'runtime-restored'),True),FixtureProvider())
 assert resumed.provider.calls==0 and len(resumed.conversations.get(p['conversation']['id'])['messages'])==2
 p2=new(c);queued=c.send(p2['conversation']['id'],body(p2),launch=False)
 restarted=ConversationController(c.conversations,FixtureProvider());job=restarted.get(p2['conversation']['id'],queued['inference_job']['id'])
 assert job['state']=='FAILED' and job['error']=='PROCESS_INTERRUPTED' and restarted.provider.calls==0
 with c.store.transaction() as db:db.execute('UPDATE conversation_inferences SET payload=json_set(payload,"$.request_metadata.clinical_active",1) WHERE id=?',(queued['inference_job']['id'],))
 with c.store.connect() as db:
  with pytest.raises(SafeError,match='INFERENCE_INTEGRITY'):check_inferences(db)


def test_provider_model_cannot_silently_change(controller):
 c=controller;original=c.provider.execute
 def changed(*args,**kwargs):
  result=original(*args,**kwargs);result['model']='unexpected-model';return result
 c.provider.execute=changed;p=new(c);r=c.send(p['conversation']['id'],body(p));d=finish(c,r['inference_job']['id'])
 assert d['state']=='FAILED' and d['error']=='PROVIDER_BINDING_CHANGED'
 assert len(c.conversations.get(p['conversation']['id'])['messages'])==1

def test_invalid_output_preserves_text_free_usage_attempt_receipt(controller):
 c=controller;c.provider=FixtureProvider('tool');original=c.provider.execute;attempt=str(uuid4())
 def observed(*args,**kwargs):
  result=original(*args,**kwargs);result['attempt_id']=attempt;result['usage']={'inputTokens':7,'outputTokens':3};return result
 c.provider.execute=observed;p=new(c);r=c.send(p['conversation']['id'],body(p));d=finish(c,r['inference_job']['id'])
 assert d['state']=='FAILED' and d['provider_result']['attempt_id']==attempt
 assert d['provider_result']['usage']=={'inputTokens':7,'outputTokens':3} and 'text' not in d['provider_result']
 assert len(c.conversations.get(p['conversation']['id'])['messages'])==1
