"""Bounded SYNTHETIC measurement; no target-hardware performance claim."""
import json
import os
import platform
import resource
import shutil
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4
from apps.core.storage import Store
from apps.core.domain import Journal
from apps.core.models import Create

def main():
    root=Path(tempfile.mkdtemp(prefix='m1-measure-',dir=Path(tempfile.gettempdir()).resolve()))
    try:
        j=Journal(Store(root/'data')); saves=[]
        for i in range(200):
            r=Create(operation_id=uuid4(),entry_id=uuid4(),base_revision=0,payload={'raw_text':f'SYNTHETIC · Вигадана нотатка {i} 🦉'})
            t=time.perf_counter(); j.write('create',r.entry_id,r); saves.append((time.perf_counter()-t)*1000)
        searches=[]
        for _ in range(30):
            t=time.perf_counter(); assert j.list(q='нотатка',limit=100)['items']; searches.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); Journal(Store(root/'data')); restart=(time.perf_counter()-t)*1000
        cpu=time.process_time(); start=time.perf_counter(); time.sleep(.5)
        idle=(time.process_time()-cpu)/(time.perf_counter()-start)*100
        rss=subprocess_rss()
        result={'scope':'SYNTHETIC domain/repository, not target M2/16GB benchmark','N':200,'python':sys.version.split()[0],
                'sqlite':sqlite3.sqlite_version,'os':platform.system()+' '+platform.release(),'architecture':platform.machine(),
                'method':'200 committed SQLite saves; 30 literal searches(limit=100); same-process reopen; 0.5s idle CPU; ps RSS',
                'save_ms':{'median':statistics.median(saves),'max':max(saves)},'search_ms':{'median':statistics.median(searches),'max':max(searches)},
                'reopen_ms':restart,'rss_kib':rss,'idle_cpu_percent':idle,'measured_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:
        shutil.rmtree(root)

def subprocess_rss():
    import subprocess
    return int(subprocess.check_output(['ps','-o','rss=','-p',str(os.getpid())],text=True).strip())

if __name__=='__main__': main()
