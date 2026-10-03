"""Bounded local synthetic engine overhead; no clinical/device/provider metrics."""
import json,shutil,tempfile,time,statistics
from pathlib import Path
from uuid import uuid4
from apps.core.storage import Store
from apps.core.practice import PracticeEngine
from apps.core.practice_contracts import Start,Action

def measure():
 parent=Path(tempfile.mkdtemp(prefix='m7a-synthetic-bench-',dir=Path(tempfile.gettempdir()).resolve()))
 result={'provenance':'ORIGINAL_SYNTHETIC','unit':'milliseconds','limits':'Local service/store reopening, not Galaxy or full browser startup; no clinical/provider metrics','runs':[]}
 try:
  for count in (25,100):
   e=PracticeEngine(Store(parent/f'data-{count}'),synthetic_demo=True)
   def timed(fn):
    start=time.perf_counter();v=fn();return v,round((time.perf_counter()-start)*1000,3)
   with e.store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   baseline=e.store.db.stat().st_size
   cat,catalog=timed(e.catalog);item=cat['items'][0];times={'start':[],'response_save':[],'transition':[]}
   def act(s,name,response=None):return e.act(s['id'],Action(operation_id=uuid4(),base_revision=s['revision'],action=name,step_id=s['current_step'] if name in {'next','save'} else None,response=response))
   for _ in range(count):
    s,ms=timed(lambda:e.start(Start(operation_id=uuid4(),module_id=item['module_id'],module_version=item['module_version'],content_hash=item['content_hash'])));times['start'].append(ms)
    s,ms=timed(lambda:act(s,'next'));times['transition'].append(ms)
    s,ms=timed(lambda:act(s,'save',True));times['response_save'].append(ms)
   _,history=timed(e.history);s=act(s,'pause')
   def restart():
    reopened=PracticeEngine(Store(e.store.root),synthetic_demo=True);state=reopened.get(s['id'])
    return reopened.act(s['id'],Action(operation_id=uuid4(),base_revision=state['revision'],action='resume'))
   _,restart_ms=timed(restart)
   with e.store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   stats={k:{'median':round(statistics.median(v),3),'max':max(v)} for k,v in times.items()}
   result['runs'].append({'synthetic_sessions':count,'catalog_validation_ms':catalog,'actions_ms':stats,'history_list_50_ms':history,'service_restart_resume_ms':restart_ms,'initial_db_bytes':baseline,'db_bytes':e.store.db.stat().st_size,'db_growth_bytes':e.store.db.stat().st_size-baseline})
  return result
 finally:shutil.rmtree(parent)

if __name__=='__main__':print(json.dumps(measure(),indent=2))
