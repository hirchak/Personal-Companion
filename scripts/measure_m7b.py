"""Bounded synthetic local persistence/context overhead, no payloads in metrics."""
import json,shutil,tempfile,time,statistics
from pathlib import Path
from uuid import uuid4
from apps.core.storage import Store
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.reflection import Reflection
from apps.core.reflection_contracts import GoalCreate,ContextRequest,GoalRef

def measure():
 parent=Path(tempfile.mkdtemp(prefix='m7b-synthetic-bench-',dir=Path(tempfile.gettempdir()).resolve()))
 result={'provenance':'ORIGINAL_SYNTHETIC','unit':'milliseconds','limits':'Local service/store reopening, not provider latency, Galaxy, real ASR or full browser startup','runs':[]}
 try:
  for count in (25,100):
   s=Conversations(Store(parent/f'data-{count}'),True);r=Reflection(s)
   def timed(fn):
    start=time.perf_counter();v=fn();return v,round((time.perf_counter()-start)*1000,3)
   with s.store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   baseline=s.store.db.stat().st_size
   g=r.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC paper garden',user_agreed=True));times={'create':[],'send':[]}
   for _ in range(count):
    conversation,ms=timed(lambda:s.create(NewConversation(operation_id=uuid4())));times['create'].append(ms)
    conversation,ms=timed(lambda:s.send(conversation['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC paper garden fixture')));times['send'].append(ms)
   _,history=timed(s.list);_,reopen=timed(lambda:s.get(conversation['conversation']['id']))
   _,restart=timed(lambda:Conversations(Store(s.store.root)).get(conversation['conversation']['id']))
   deep=s.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=1))
   context,context_ms=timed(lambda:r.build(ContextRequest(operation_id=uuid4(),goal=GoalRef(id=g['id'],revision=1),conversation_id=deep['conversation']['id'],prepare_synthetic_digests=True)))
   with s.store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   result['runs'].append({'conversations':count,'messages':count*2,'actions_ms':{k:{'median':round(statistics.median(v),3),'max':max(v)} for k,v in times.items()},'history_50_ms':history,'reopen_ms':reopen,'service_restart_ms':restart,'context_builder_ms':context_ms,'context_sources':len(context['receipt']['sources']),'context_used_bytes_upper_bound':context['receipt']['used_bytes_estimate'],'context_budget':context['receipt']['token_budget'],'db_growth_bytes':s.store.db.stat().st_size-baseline})
  return result
 finally:shutil.rmtree(parent)

if __name__=='__main__':print(json.dumps(measure(),indent=2))
