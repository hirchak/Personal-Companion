"""Exact-C original synthetic longitudinal comparison. No retries, no sole LLM judge."""
import argparse,json,time,tempfile,shutil,subprocess,statistics
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timedelta,timezone
from apps.core.storage import REPO,Store,encode,digest
from apps.core.conversation import Conversations
from apps.core.conversation_controller import ConversationController
from apps.core.codex_conversation_provider import CodexConversationProvider
from apps.core.live_evaluation_budget import M7DEvaluationBudget
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.reflection_contracts import GoalCreate,GoalChange
from apps.core.deep_session_contracts import SessionAction,MapAction,DeepContextPreview,ContextSelection
from apps.core.conversation_runtime_contracts import InferenceStart

OUT=REPO/'generated/m7d-provider-eval'
def run(model,effort,sha):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==sha
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip(),'EXACT_C_REQUIRES_CLEAN_SOURCE'
 corpus_path=REPO/'research/evals/M7D_SYNTHETIC_DEEP.json';corpus=json.loads(corpus_path.read_text());budget=M7DEvaluationBudget()
 assert budget.summary()['remaining']>=corpus['per_model_attempts'],'INSUFFICIENT_PERSISTENT_M7D_BUDGET'
 provider=CodexConversationProvider(model,budget=budget,effort=effort);catalog=provider.discover()
 assert effort in next(m['supported_efforts'] for m in catalog['models'] if m['model']==model)
 OUT.mkdir(parents=True,exist_ok=True);rows=[];controls=[];file=OUT/(model+'-'+effort+'.json')
 for scenario in corpus['runs']:
  root=Path(tempfile.mkdtemp(prefix='m7d-original-synthetic-eval-',dir=Path(tempfile.gettempdir()).resolve()))
  try:
   c=ConversationController(Conversations(Store(root/'data'),True),provider,timeout=120)
   g=c.context.create(GoalCreate(operation_id=uuid4(),text=scenario['goal'],user_agreed=True)) if scenario['goal'] else None
   if g:
    # Fictional history dates are explicit original fixtures, never real/replay evidence.
    with c.store.transaction() as db:
     g['created_at']=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat();db.execute('UPDATE reflection_goals SET payload=? WHERE id=?',(encode(g),g['id']))
   for past in scenario['free_history']:
    p=c.conversations.create(NewConversation(operation_id=uuid4()));p=c.conversations.send(p['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text=past),respond=False)
    if scenario['id']=='RANGE':
     with c.store.transaction() as db:
      m=p['messages'][0];m['created_utc']=(datetime.now(timezone.utc)-timedelta(days=20)).isoformat();db.execute('UPDATE conversation_messages SET payload=? WHERE id=?',(encode(m),m['id']))
   for session_index,turns in enumerate(scenario['sessions']):
    p=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'] if g else None,goal_revision=g['revision'] if g else None));id=p['conversation']['id']
    if g:
     s=c.deep.read(id)['session'];c.deep.session_action(id,SessionAction(operation_id=uuid4(),base_revision=s['revision'],action='focus',focus='ORIGINAL SYNTHETIC · Розмова про чернетку / сесія '+str(session_index+1)))
    for turn_index,text in enumerate(turns):
     if scenario['id']=='REVISION' and session_index==0 and turn_index==1:
      g=c.context.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC · Зрозуміти, як хочу обговорювати дедлайни.',user_agreed=True))
     p=c.conversations.get(id);purpose='CLOSURE' if 'Явно прошу підсумувати' in text else 'REFLECT';selection=ContextSelection(type='LAST_7_DAYS') if scenario['id']=='RANGE' and turn_index==0 else ContextSelection(type='CUSTOM',window_start=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat(),window_end=datetime.now(timezone.utc).isoformat()) if scenario['id']=='RANGE' else ContextSelection()
     before=c.deep.read(id) if scenario['kind']=='DEEP' else None;preview=None
     if before:preview=c.preview_context(id,DeepContextPreview(operation_id=uuid4(),base_revision=p['conversation']['revision'],text=text,selection=selection))
     started=time.monotonic();result=c.send(id,InferenceStart(operation_id=uuid4(),base_revision=p['conversation']['revision'],text=text,purpose=purpose,synthetic_test_ack=True,context_binding={k:preview[k] for k in ('receipt_id','context_hash','preview_hash')} if preview else None));job=result['inference_job']['id'];c.workers[job].join(130);assert not c.workers[job].is_alive(),'BOUNDED_WORKER_NOT_STOPPED'
     with c.store.connect() as db:
      d=c.row(db,job);counts={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('entries','memories','health_records','practice_sessions')}
     after=c.deep.read(id) if before else None
     reported=d['provider_result'] or {};attempt_id=reported.get('attempt_id')
     if attempt_id:
      with budget.connect() as ledger:assert ledger.execute('SELECT 1 FROM attempts WHERE id=? AND goal=?',(attempt_id,budget.goal)).fetchone(),'ATTEMPT_BINDING_MISMATCH'
     if d['state']!='COMPLETED' and attempt_id:budget.finish(attempt_id,'CANCELLED' if d['state']=='CANCELLED' else 'FAILED')
     row={'scenario_id':scenario['id'],'case_ids':scenario['case_ids'],'synthetic_session_day':session_index+1,'turn':turn_index+1,'model':model,'effort':effort,'profile':provider.profile,'goal':c.context.get(p['conversation']['goal_binding']['id']) if g else None,'pinned_goal_revision':p['conversation']['goal_binding'],'session_focus':before['session']['focus'] if before else None,'selected_context':preview['selection'] if preview else 'FREE_RECENT','relevant_prior_context':preview['context'] if preview else [],'working_map_before':before['map'] if before else None,'user_text':text,'assistant_candidate':d['candidate'],'working_map_after':after['map'] if after else None,'closure':d['candidate']['closure'] if d['candidate'] else None,'state':d['state'],'error':d['error'],'request_metadata':d['request_metadata'],'provider_reported':reported,'attempt_count':int(bool(attempt_id)),'wall_ms':round((time.monotonic()-started)*1000,3),'deterministic_violations':[] if d['state']=='COMPLETED' else [d['error']],'no_downstream_mutation':all(v==0 for v in counts.values()),'qualitative_review':'PENDING_OWNER_ARCHITECT','real_private_data':False,'hidden_reasoning':False}
     rows.append(row);file.write_text(json.dumps({'implementation_sha':sha,'catalog':catalog,'corpus_sha256':digest(corpus_path.read_bytes()),'rows':rows,'controls':controls,'ledger':budget.summary()},ensure_ascii=False,indent=2)+'\n');print(model,effort,scenario['id'],session_index+1,turn_index+1,d['state'],d['error'],flush=True)
     if d['state']!='COMPLETED':
      category=reported.get('provider_failure',{}).get('category')
      if category in {'INVALID_STRUCTURED_SCHEMA','REASONING_EFFORT_REJECTED','SUBSCRIPTION_LIMIT_REACHED','EXISTING_AUTH_ROUTE_UNAVAILABLE'}:
       raise RuntimeError('CONFIGURATION_STOP:'+category+'; preserved rows and persistent ledger')
      break
     if scenario['id']=='LONGITUDINAL' and session_index==0 and turn_index==0:
      m=after['map'];hyp=next((i for i in (m or {}).get('items',[]) if i['kind']=='HYPOTHESIS' and i['state']=='CURRENT'),None)
      if hyp:
       c.deep.action(id,MapAction(operation_id=uuid4(),base_version=m['version'],item_id=hyp['id'],action='reject',user_confirmed=True));controls.append({'scenario':'LONGITUDINAL','explicit_synthetic_user_rejection':hyp,'after_version':m['version']+1})
      else:controls.append({'scenario':'LONGITUDINAL','rejection_control':'NOT_RUN_NO_MODEL_HYPOTHESIS; deterministic rejection test still applies'})
     if scenario['id']=='LONGITUDINAL' and purpose=='CLOSURE':
      s=c.deep.read(id)['session'];c.deep.session_action(id,SessionAction(operation_id=uuid4(),base_revision=s['revision'],action='close'));assert c.context.get(g['id'])['goal']['state']=='ACTIVE'
  finally:shutil.rmtree(root)
 valid=[r for r in rows if r['state']=='COMPLETED'];lat=[r['wall_ms'] for r in valid]
 result={'implementation_sha':sha,'catalog':catalog,'corpus_sha256':digest(corpus_path.read_bytes()),'model':model,'effort':effort,'profile':provider.profile,'attempt_count':sum(r['attempt_count'] for r in rows),'valid':len(valid),'failed':len(rows)-len(valid),'latency_ms':{'median':statistics.median(lat) if lat else None,'max':max(lat) if lat else None},'rows':rows,'controls':controls,'ledger':budget.summary(),'quality_dimensions':corpus['human_dimensions'],'qualitative_review':'PENDING_OWNER_ARCHITECT; deterministic compliance does not establish quality','new_auth':False,'PAYG':False,'private_provider_suitability':'NOT_VERIFIED_M7C_N02','hidden_reasoning_logged':False}
 file.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True,choices=['gpt-6-luna','gpt-6-sol','gpt-6.1-sol']);p.add_argument('--effort',required=True);p.add_argument('--implementation-sha',required=True);a=p.parse_args();run(a.model,a.effort,a.implementation_sha)
