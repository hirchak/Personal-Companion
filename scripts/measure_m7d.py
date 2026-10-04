"""Bounded synthetic map/source/range/history cost; no provider/hardware measurements."""
import tempfile,shutil,json,time,statistics
from pathlib import Path
from uuid import uuid4
from apps.core.storage import REPO,Store,encode
from apps.core.conversation import Conversations
from apps.core.conversation_controller import ConversationController
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.reflection_contracts import GoalCreate,MessageEdit
from apps.core.deep_session_contracts import WorkingMapCandidate,DeepContextPreview,ContextSelection

def measure():
 parent=Path(tempfile.mkdtemp(prefix='m7d-original-synthetic-perf-',dir=Path(tempfile.gettempdir()).resolve()));rows=[]
 def timed(fn):
  t=time.perf_counter();v=fn();return v,round((time.perf_counter()-t)*1000,3)
 try:
  for count in (25,100):
   c=ConversationController(Conversations(Store(parent/str(count)),True));g=c.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC паперовий сад',user_agreed=True))
   with c.store.connect() as db:db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   baseline=c.store.db.stat().st_size
   for _ in range(count):
    p=c.conversations.create(NewConversation(operation_id=uuid4()));c.conversations.send(p['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC паперовий сад'),respond=False)
   p=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=1));p=c.conversations.send(p['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC explicit source'),respond=False);mid=p['messages'][0]['id']
   candidate=WorkingMapCandidate(items=[{'kind':'HYPOTHESIS','text':'ORIGINAL SYNTHETIC tentative pattern','provenance':'MODEL_HYPOTHESIS','source_refs':['s0']}])
   def update():
    with c.store.transaction() as db:return c.deep.ingest(db,p['conversation']['id'],candidate,{'s0':{'id':mid,'revision':1}},{'provider_model':'OFFLINE_FIXTURE','provider_route':'OFFLINE_FIXTURE','selected_skills':[],'request_hash':'a'*64})
   _,update_ms=timed(update)
   _,context_ms=timed(lambda:c.preview_context(p['conversation']['id'],DeepContextPreview(operation_id=uuid4(),base_revision=p['conversation']['revision'],text='ORIGINAL SYNTHETIC next turn',selection=ContextSelection(type='LAST_7_DAYS'))))
   def invalidate():
    c.context.edit_message(p['conversation']['id'],mid,MessageEdit(operation_id=uuid4(),base_conversation_revision=p['conversation']['revision'],base_message_revision=1,text='ORIGINAL SYNTHETIC corrected source'))
    assert c.deep.read(p['conversation']['id'])['map']['items'][0]['state']=='STALE'
   _,invalidation_ms=timed(invalidate)
   later=c.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=1));_,reopen_ms=timed(lambda:c.deep.read(later['conversation']['id']));_,history_ms=timed(c.conversations.list)
   _,restart_ms=timed(lambda:ConversationController(Conversations(Store(c.store.root),True)).deep.read(later['conversation']['id']))
   with c.store.connect() as db:db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   rows.append({'free_conversations':count,'map_update_ms':update_ms,'source_edit_plus_stale_view_ms':invalidation_ms,'range_context_with_map_ms':context_ms,'later_session_reopen_ms':reopen_ms,'history50_ms':history_ms,'service_restart_map_read_ms':restart_ms,'db_growth_bytes':c.store.db.stat().st_size-baseline})
  result={'provenance':'ORIGINAL_SYNTHETIC','scope':'LOCAL_BOUND_SERVICE_SQLITE_ONLY; no hardware/provider forecast','rows':rows};(REPO/'generated/M7D_PERFORMANCE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return result
 finally:shutil.rmtree(parent)
if __name__=='__main__':measure()
