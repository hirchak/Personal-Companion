"""Bounded genuine original-synthetic eval on exact C; no LLM judge or winner selection."""
import argparse,json,time,shutil,tempfile,hashlib,subprocess,statistics
from pathlib import Path
from uuid import uuid4
from apps.core.storage import REPO,Store
from apps.core.conversation import Conversations
from apps.core.conversation_controller import ConversationController
from apps.core.codex_conversation_provider import CodexConversationProvider
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.conversation_runtime_contracts import InferenceStart
from apps.core.reflection_contracts import GoalCreate
from apps.core.live_evaluation_budget import LiveEvaluationBudget

def own_attempt_count(budget,metadata,route,model):
 attempt_id=(metadata or {}).get('attempt_id')
 with budget.connect() as ledger:
  attempt=ledger.execute('SELECT route,model FROM attempts WHERE id=?',(attempt_id,)).fetchone() if attempt_id else None
 if attempt_id:assert attempt and attempt['route']==route and attempt['model']==model,'ATTEMPT_BINDING_MISMATCH'
 return int(attempt is not None)

def run(model,implementation_sha,case_ids=None):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==implementation_sha
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip(),'EXACT_C_REQUIRES_CLEAN_SOURCE'
 corpus_path=REPO/'research/evals/M7C_SYNTHETIC_CONVERSATION.json';corpus=json.loads(corpus_path.read_text());cases=[c for c in corpus['cases'] if not case_ids or c['id'] in case_ids]
 budget=LiveEvaluationBudget();required=sum(len(c['user_turns'])+(c['id']=='DEEP_GOAL') for c in cases)
 if budget.summary()['remaining']<required:raise RuntimeError('INSUFFICIENT_GOAL_WIDE_LIVE_BUDGET')
 folder=REPO/'generated/m7c-provider-eval';folder.mkdir(parents=True,exist_ok=True);rows=[];provider=CodexConversationProvider(model,budget=budget)
 for case in cases:
  root=Path(tempfile.mkdtemp(prefix='m7c-original-synthetic-eval-',dir=Path(tempfile.gettempdir()).resolve()))
  try:
   c=ConversationController(Conversations(Store(root/'data'),True),provider,timeout=90)
   g=c.context.create(GoalCreate(operation_id=uuid4(),text=case['goal'],user_agreed=True)) if case['goal'] else None
   for past in case['past_free_turns']:
    p=c.conversations.create(NewConversation(operation_id=uuid4()));c.conversations.send(p['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text=past),respond=False)
   page=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'] if g else None,goal_revision=g['revision'] if g else None))
   inputs=list(zip(case['user_turns'],case['purposes']))
   for turn_index,(text,purpose) in enumerate(inputs):
    started=time.monotonic()
    result=c.send(page['conversation']['id'],InferenceStart(operation_id=uuid4(),base_revision=page['conversation']['revision'],text=text,purpose=purpose,synthetic_test_ack=True));job_id=result['inference_job']['id'];c.workers[job_id].join(100)
    assert not c.workers[job_id].is_alive(),'BOUNDED_PROVIDER_WORKER_DID_NOT_STOP'
    with c.store.connect() as db:
     d=c.row(db,job_id);receipt=json.loads(db.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(d['request_metadata']['retrieval_receipt_id'],)).fetchone()[0]);no_downstream={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0 for table in ('entries','memories','health_records','practice_sessions','feedback_drafts')}
    own_attempts=own_attempt_count(budget,d['provider_result'],provider.route,model)
    row={'case_id':case['id'],'turn':turn_index+1,'category':case['category'],'synthetic_prompt':text,'provenance':'ORIGINAL_SYNTHETIC','mode':page['conversation']['mode'],'purpose':purpose,'goal_text':g['text'] if g else None,'goal_revision':g['revision'] if g else None,'selected_skills':d['request_metadata']['selected_skills'],'context_hash':d['request_metadata']['context_hash'],'request_hash':d['request_hash'],'source_bindings':receipt['sources'],'digest_versions':receipt['digest_versions'],'context_budget':{'tokens':receipt['token_budget'],'bytes':receipt['byte_budget']},'provider_route':'CODEX_SUBSCRIPTION','provider_model':model,'auth_type':'EXISTING_CHATGPT','new_billing_or_auth':False,'state':d['state'],'error':d['error'],'candidate':d['candidate'],'latency_ms':round((time.monotonic()-started)*1000,3),'provider_reported':d['provider_result'],'inference_attempts':own_attempts,'deterministic':{'structured_candidate_valid':d['state']=='COMPLETED','source_refs_in_supplied_receipt':d['state']=='COMPLETED','no_downstream_mutation':all(no_downstream.values()),'clinical_active':0,'goal_revision_unchanged':c.context.get(g['id'])['goal']['revision']==g['revision'] if g else True},'qualitative_review':'PENDING_OWNER_ARCHITECT; no LLM judge or clinical oracle'}
    rows.append(row);print(model,case['id'],turn_index+1,d['state'],d['error'],flush=True)
    (folder/(model+'-review-ignored.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    if d['state']!='COMPLETED':break
    page=c.conversations.get(page['conversation']['id'])
    if case['id']=='DEEP_GOAL' and purpose=='GOAL_PROPOSAL':
     suggestion=d['candidate']['goal_suggestion'];assert suggestion and not c.context.list()['items']
     g=c.context.create(GoalCreate(operation_id=uuid4(),text=suggestion,user_agreed=True));row['explicit_goal_candidate_acceptance']='SYNTHETIC_USER_ACTION_AFTER_PREVIEW; revision1'
     page=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=1));inputs.append(('ORIGINAL SYNTHETIC · Персонаж хоче повернутися до погодженої цілі й уточнити один можливий початок.','REFLECT'))
  finally:shutil.rmtree(root)
 successes=[r for r in rows if r['state']=='COMPLETED'];latencies=[r['latency_ms'] for r in successes]
 result={'implementation_sha':implementation_sha,'corpus_sha256':hashlib.sha256(corpus_path.read_bytes()).hexdigest(),'provider_route':'CODEX_SUBSCRIPTION','model':model,'auth_type':'EXISTING_CHATGPT','new_billing_or_auth':False,'requests':sum(r['inference_attempts'] for r in rows),'completed':len(successes),'failed':len(rows)-len(successes),'latency_ms':{'median':round(statistics.median(latencies),3) if latencies else None,'max':max(latencies) if latencies else None},'structured_adherence':{'valid':len(successes),'total':len(rows)},'qualitative_status':'OWNER_ARCHITECT_REVIEW_PENDING','provider_winner':'NOT_SELECTED','raw_hidden_reasoning_logged':False,'real_private_data':False,'clinical_active':0,'ledger':budget.summary(),'rows':rows}
 (folder/(model+'-result-ignored.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['gpt-6-luna','gpt-6-sol','gpt-6.1-sol'],required=True);parser.add_argument('--implementation-sha',required=True);parser.add_argument('--case',action='append');a=parser.parse_args();run(a.model,a.implementation_sha,a.case)
