from uuid import uuid4
import json
import pytest
from apps.core.reflection import Reflection
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.reflection_contracts import GoalCreate,GoalChange,ContextRequest,GoalRef,MessageEdit,Expansion
from apps.core.storage import Store,SafeError
from test_m1_domain import isolated

@pytest.fixture
def reflection(isolated):return Reflection(Conversations(Store(isolated/'deep'),synthetic_demo=True))
def goal(r):return r.create(GoalCreate(operation_id=uuid4(),text='SYNTHETIC paper city',user_agreed=True))
def free(r):
 c=r.conversations.create(NewConversation(operation_id=uuid4()));return r.conversations.send(c['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='SYNTHETIC paper city project'))
def deep(r,g):return r.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=g['revision']))
def request(g,c,**kw):return ContextRequest(operation_id=uuid4(),goal=GoalRef(id=g['id'],revision=g['revision']),conversation_id=c['conversation']['id'],**kw)


def test_goal_history_pinning_pause_complete_and_user_edit(reflection):
 r=reflection;g=goal(r);c=deep(r,g)
 b=GoalChange(operation_id=uuid4(),base_revision=1,text='SYNTHETIC changed goal',user_agreed=True);updated=r.change(g['id'],b);assert updated['revision']==2
 assert r.change(g['id'],b)==updated
 assert r.get(g['id'])['history'][0]['text']==g['text']
 assert r.conversations.get(c['conversation']['id'])['conversation']['goal_binding']['revision']==1
 paused=r.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=2,state='PAUSED',user_agreed=True))
 with pytest.raises(SafeError,match='GOAL_NOT_ACTIVE'):r.conversations.send(c['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='SYNTHETIC paused'))
 completed=r.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=3,state='COMPLETED',user_agreed=True));assert completed['completed_at']
 edited=r.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=4,text='SYNTHETIC edited completed goal',user_agreed=True));assert edited['state']=='COMPLETED'
 assert len(r.get(g['id'])['history'])==4


def test_context_fts_scoped_budget_raw_sources_and_expansion(reflection):
 r=reflection;g=goal(r);past=free(r);c=deep(r,g);b=request(g,c,prepare_synthetic_digests=True)
 result=r.build(b);receipt=result['receipt'];assert receipt['goal']['revision']==1 and receipt['used_tokens_upper_bound']<=b.token_budget
 assert receipt['sources'] and 'text' not in json.dumps(receipt['sources'])
 assert not receipt['raw_text_logged'] and not result['live_provider_calls']
 assert any(p['kind'].endswith('DIGEST') or p['kind']=='FTS_RAW' for p in result['context'])
 source=receipt['sources'][0];expanded=r.expand(Expansion(receipt_id=receipt['id'],sources=[GoalRef(**source)]));assert expanded['messages'][0]['id']==source['id']
 with pytest.raises(SafeError,match='SOURCE_EXPANSION_OUT_OF_SCOPE'):r.expand(Expansion(receipt_id=receipt['id'],sources=[GoalRef(id=uuid4(),revision=1)]))


def test_edit_delete_invalidate_digests_and_remove_fts(reflection):
 r=reflection;g=goal(r);past=free(r);c=deep(r,g);result=r.build(request(g,c,prepare_synthetic_digests=True));message=past['messages'][0]
 edited=r.edit_message(past['conversation']['id'],message['id'],MessageEdit(operation_id=uuid4(),base_conversation_revision=past['conversation']['revision'],base_message_revision=1,text='SYNTHETIC user edit'))
 with r.store.connect() as db:
  assert db.execute('SELECT count(*) FROM conversation_message_revisions').fetchone()[0]==1
  stale=[json.loads(x[0]) for x in db.execute('SELECT payload FROM conversation_digests WHERE status="STALE"')];assert stale and all(d['text'] is None for d in stale)
 from apps.core.conversation_contracts import ConversationAction
 r.conversations.action(past['conversation']['id'],ConversationAction(operation_id=uuid4(),base_revision=edited['conversation']['revision'],action='delete'))
 with r.store.connect() as db:
  assert db.execute('SELECT count(*) FROM conversation_fts').fetchone()[0]==0
  assert db.execute('SELECT count(*) FROM conversation_message_revisions').fetchone()[0]==0
 with pytest.raises(SafeError,match='SOURCE_CHANGED'):r.expand(Expansion(receipt_id=result['receipt']['id'],sources=[GoalRef(**result['receipt']['sources'][0])]))


def test_explicit_window_budget_memory_scope_and_skills_off(reflection):
 r=reflection;g=goal(r);c=deep(r,g)
 with pytest.raises(SafeError,match='CONTEXT_WINDOW_INVALID'):r.build(request(g,c,window_start='2030-01-01T00:00:00+00:00',window_end='2020-01-01T00:00:00+00:00'))
 with pytest.raises(SafeError,match='MEMORY_SCOPE_REQUIRED'):r.build(request(g,c,confirmed_memories=[GoalRef(id=uuid4(),revision=1)]))
 assert all(not v['active'] for v in r.list()['skills'].values())
 b=request(g,c,query='" OR DROP TABLE',token_budget=256,byte_budget=512)
 out=r.build(b);assert out['receipt']['used_tokens_upper_bound']<=256
 assert out['narrow_tools']['health']=='SEPARATE_AUTHORIZATION_REQUIRED'


def test_receipt_retry_exact_selection_no_new_history_and_source_drift(reflection):
 r=reflection;g=goal(r);past=free(r);c=deep(r,g);b=request(g,c,prepare_synthetic_digests=True);first=r.build(b)
 free(r);same=r.build(b);assert same['receipt']==first['receipt'];assert same['context']==first['context']
 m=past['messages'][0];r.edit_message(past['conversation']['id'],m['id'],MessageEdit(operation_id=uuid4(),base_conversation_revision=past['conversation']['revision'],base_message_revision=1,text='SYNTHETIC drift'))
 with pytest.raises(SafeError,match='SOURCE_CHANGED'):r.build(b)


def test_goal_source_digest_stale_and_revision_exact(reflection):
 r=reflection;g=goal(r);free(r);c=deep(r,g);r.build(request(g,c,prepare_synthetic_digests=True))
 newer=r.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=1,text='SYNTHETIC new goal',user_agreed=True))
 with r.store.connect() as db:assert db.execute('SELECT count(*) FROM conversation_digests WHERE kind="GOAL" AND status="STALE"').fetchone()[0]>=1
 with pytest.raises(SafeError,match='DEEP_GOAL_BINDING_MISMATCH'):r.build(request(newer,c))
 assert r.build(request(g,c))['context'][0]['text']==g['text']


def test_fts_filter_window_and_budget_does_not_pull_entire_history(reflection):
 r=reflection;g=goal(r)
 for _ in range(12):free(r)
 c=deep(r,g);result=r.build(request(g,c,max_sources=2,token_budget=256,byte_budget=512,query='paper city'))
 assert len(result['receipt']['sources'])<=2 and result['receipt']['used_tokens_upper_bound']<=256
 empty=r.build(request(g,c,window_start='2000-01-01T00:00:00+00:00',window_end='2000-01-02T00:00:00+00:00'))
 assert empty['receipt']['sources']==[]


def test_goals_digests_receipts_backup_restore_off(reflection,isolated):
 r=reflection;g=goal(r);free(r);c=deep(r,g);result=r.build(request(g,c,prepare_synthetic_digests=True));r.store.backup(isolated/'deep-backup')
 restored=Reflection(Conversations(Store.restore(isolated/'deep-backup',isolated/'deep-restored')))
 assert restored.get(g['id'])['goal']==g
 assert restored.conversations.get(c['conversation']['id'])['conversation']['goal_binding']['revision']==1
 assert restored.conversations.mode()['responder']=='OFF'
 with restored.store.connect() as db:assert db.execute('SELECT count(*) FROM retrieval_receipts').fetchone()[0]==1



def test_budget_covers_serialized_context_not_only_raw_text(reflection):
 from apps.core.storage import encode
 r=reflection;g=goal(r);free(r);c=deep(r,g);x=r.build(request(g,c,token_budget=512,byte_budget=512))
 assert len(encode(x['context']).encode())<=512
 assert x['receipt']['used_bytes_estimate']>=len(encode(x['context']).encode())


def test_completion_timestamp_preserved_and_expansion_json_budget(reflection):
 from apps.core.storage import encode
 r=reflection;g=goal(r);past=free(r);c=deep(r,g);receipt=r.build(request(g,c))['receipt']
 expanded=r.expand(Expansion(receipt_id=receipt['id'],sources=[GoalRef(**receipt['sources'][0])],token_budget=2000,byte_budget=2000))
 assert len(encode(expanded['messages']).encode())<=expanded['used_tokens_upper_bound']<=2000
 completed=r.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=1,state='COMPLETED',user_agreed=True))
 edited=r.change(g['id'],GoalChange(operation_id=uuid4(),base_revision=2,text='ORIGINAL SYNTHETIC edited completed goal',user_agreed=True))
 assert edited['completed_at']==completed['completed_at']


def test_derived_backup_integrity_rejects_stale_text_and_fts_drift(reflection,isolated):
 r=reflection;g=goal(r);free(r);c=deep(r,g);r.build(request(g,c,prepare_synthetic_digests=True))
 with r.store.connect() as db:
  db.execute('UPDATE conversation_digests SET status="STALE",payload=json_set(payload,"$.status","STALE")')
 with pytest.raises(SafeError,match='GOAL_INTEGRITY'):r.store.backup(isolated/'invalid-derived')
