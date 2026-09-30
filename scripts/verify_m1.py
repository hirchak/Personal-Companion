"""Capture sanitized reproducible evidence; never print unlock codes or raw failures."""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
p.add_argument('--scope',required=True)
a=p.parse_args()
root=Path.cwd()
commands=[
 ['npm','--prefix','apps/web','run','build'],
 [sys.executable,'-m','pytest','-q'],
 [sys.executable,'scripts/check_docs.py'],
 [sys.executable,'scripts/build_chatgpt_context.py'],
 [sys.executable,'scripts/check_privacy.py','--include-generated'],
 ['git','diff','--check']
]
records=[]
for command in commands:
 start=time.time()
 result=subprocess.run(command,text=True,capture_output=True,cwd=root)
 stdout=(result.stdout+result.stderr).replace(str(root),'<source-root>').replace(str(Path(sys.executable).parent.parent),'<python-env>')
 # If tests fail, preserve full diagnostics only in ignored local output and stop.
 if result.returncode:
  (root/'generated').mkdir(exist_ok=True)
  (root/'generated/failed-verification.txt').write_text(stdout)
  print('FAIL:', ' '.join(command[1:]), '; diagnostics in generated/failed-verification.txt')
  raise SystemExit(result.returncode)
 records.append({'command':' '.join(['python' if x==sys.executable else x for x in command]),
                 'scope':a.scope,'run_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(start)),
                 'duration_seconds':round(time.time()-start,3),'exit_code':result.returncode,'output':stdout})
 print('PASS:',records[-1]['command'],flush=True)
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps({'scope':a.scope,'environment':{'python':sys.version.split()[0],'node':subprocess.check_output(['node','--version'],text=True).strip(),'npm':subprocess.check_output(['npm','--version'],text=True).strip(),'os':platform.system()+' '+platform.release(),'architecture':platform.machine()},'records':records},ensure_ascii=False,indent=2)+'\n')
