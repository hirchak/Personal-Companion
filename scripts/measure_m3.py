"""Local synthetic measurements; no model inference, content output or Galaxy claims."""
import json,platform,shutil,statistics,tempfile,time,sys
from pathlib import Path
from uuid import uuid4
from apps.core.storage import Store
from apps.core.domain import Journal
from apps.core.models import Create
from apps.core.runtime import Runtime
from apps.core.ai_contracts import PreviewRequest,Enqueue,MemoryCreate

root=Path(tempfile.mkdtemp(prefix='m3-synthetic-measure-',dir=Path(tempfile.gettempdir()).resolve()))
try:
    store=Store(root/'data');runtime=Runtime(Journal(store),autostart=False);runtime.set_mode('MOCK')
    empty_bytes=store.db.stat().st_size
    id=str(uuid4());runtime.journal.write('create',id,Create(operation_id=uuid4(),entry_id=id,base_revision=0,payload={'raw_text':'SYNTHETIC local measurement entry'}))
    ref={'id':id,'revision':1};memory=runtime.create_memory(MemoryCreate(content='SYNTHETIC measurement preference'))
    times={k:[] for k in ('context_build','enqueue','mock_execute_validate_commit','memory_list_search','structured_validation')}
    for _ in range(30):
        start=time.perf_counter();p=runtime.preview(PreviewRequest(task='organize_selected',entries=[ref],memories=[memory]),'measurement');times['context_build'].append((time.perf_counter()-start)*1000)
        runtime.approve(p['id'],p['context_hash'],'measurement')
        start=time.perf_counter();runtime.enqueue(Enqueue(consent_id=p['id'],operation_id=uuid4()),'measurement');times['enqueue'].append((time.perf_counter()-start)*1000)
        start=time.perf_counter();runtime.run_one();times['mock_execute_validate_commit'].append((time.perf_counter()-start)*1000)
        start=time.perf_counter();runtime.memories('measurement');times['memory_list_search'].append((time.perf_counter()-start)*1000)
        import threading
        output=runtime.providers['mock'].execute(p['package'],threading.Event(),time.monotonic()+1)
        start=time.perf_counter();runtime._validate(output,p['package']);times['structured_validation'].append((time.perf_counter()-start)*1000)
    cpu=time.process_time();start=time.perf_counter();time.sleep(.25);idle_cpu=(time.process_time()-cpu)/(time.perf_counter()-start)*100
    with store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    # Payload estimates distinguish tables' logical bytes from allocated DB pages.
    with store.connect() as c:
        ai_bytes=sum(c.execute(f"SELECT COALESCE(sum(length(CAST({expr} AS BLOB))),0) FROM {table}").fetchone()[0] for table,expr in
          [('ai_consents','package'),('ai_jobs','source_refs'),('suggestions','output'),('memories','content')])
    print(json.dumps({'scope':'30 synthetic local iterations on actual SQLite; no external provider or hardware performance evidence',
        'environment':{'python':platform.python_version(),'os':platform.system()+' '+platform.release(),'architecture':platform.machine()},
        'N':30,'milliseconds':{k:{'median':round(statistics.median(v),4),'max':round(max(v),4)} for k,v in times.items()},
        'empty_schema3_db_bytes':empty_bytes,'after_30_jobs_db_bytes':store.db.stat().st_size,'allocated_growth_bytes':store.db.stat().st_size-empty_bytes,
        'logical_context_refs_suggestion_memory_bytes':ai_bytes,'idle_sample_seconds':.25,'own_process_idle_cpu_percent':round(idle_cpu,4),
        'idle_worker_count':len(runtime.active),'mode_on_restart':'OFF','provider_tokens_latency_cost':'NOT_RUN',
        'measured_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
finally:shutil.rmtree(root)
