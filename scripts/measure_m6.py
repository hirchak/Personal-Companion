"""Deterministic synthetic health import operational benchmark, not personal health metrics."""
import json,tempfile,time,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from m6_fixtures import batch,record
from apps.core.health import HealthImport
from apps.core.storage import Store

def measure():
    parent=Path(tempfile.mkdtemp(prefix='m6-synthetic-bench-',dir=Path(tempfile.gettempdir()).resolve()));result={'fixture_provenance':'ORIGINAL_SYNTHETIC','unit':'milliseconds','runs':[]}
    try:
        for n in (100,1000):
            h=HealthImport(Store(parent/f'data-{n}'));b=batch(*[record(id=f'SYNTHETIC-{i}') for i in range(n)])
            def timed(fn):start=time.perf_counter();value=fn();return value,round((time.perf_counter()-start)*1000,3)
            _,initial=timed(lambda:h.apply(b));_,replay=timed(lambda:h.apply(b))
            updated=batch(*[record(id=f'SYNTHETIC-{i}',modified='2025-01-02T12:00:00Z',fields={'count':43,'unit':'count'}) for i in range(min(100,n))],sequence=2,epoch=b.epoch,mode='INCREMENTAL')
            _,update=timed(lambda:h.apply(updated));_,lookup=timed(lambda:h.records());_,restart=timed(lambda:HealthImport(Store(h.store.root)).status())
            with h.store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            result['runs'].append({'synthetic_records':n,'initial_import_ms':initial,'idempotent_replay_ms':replay,'incremental_update_ms':update,'bounded_lookup_ms':lookup,'restart_checkpoint_ms':restart,'db_bytes':h.store.db.stat().st_size})
        return result
    finally:shutil.rmtree(parent)
if __name__=='__main__':print(json.dumps(measure(),indent=2))
