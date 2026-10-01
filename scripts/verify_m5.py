"""M5 exact-C collector. Full active regressions, sanitized summaries, no live/hardware calls."""
import argparse,json,platform,re,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--scope',required=True);a=p.parse_args();root=Path.cwd()
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
if a.scope=='EXACT_C':
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],text=True)
    if dirty:raise SystemExit('EXACT_C requires a clean committed source tree')
commands=[['npm','--prefix','apps/web','run','build'],['npm','--prefix','apps/web','test'],[sys.executable,'-m','pytest','-q'],
 [sys.executable,'-m','scripts.measure_m5','--output','generated/m5-performance.json'],[sys.executable,'scripts/check_docs.py'],
 [sys.executable,'scripts/build_chatgpt_context.py'],[sys.executable,'scripts/check_privacy.py','--include-generated'],['git','diff','--check']]
records=[]
for command in commands:
 start=time.time();r=subprocess.run(command,cwd=root,text=True,capture_output=True)
 output=(r.stdout+r.stderr).replace(str(root),'<source-root>').replace(str(Path(sys.executable).parent.parent),'<python-env>')
 output=re.sub(r'/private/(?:var|tmp)/[^\s\"\']+','<synthetic-temp>',output)
 if r.returncode:
  (root/'generated').mkdir(exist_ok=True);(root/'generated/m5-failed-verification.txt').write_text(output)
  print('FAIL: '+' '.join(command[1:])+'; diagnostics in generated/m5-failed-verification.txt');raise SystemExit(r.returncode)
 records.append({'command':' '.join('python' if x==sys.executable else x for x in command),'scope':a.scope,
   'run_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(start)),'duration_seconds':round(time.time()-start,3),'exit_code':r.returncode,'output':output})
 print('PASS: '+records[-1]['command'],flush=True)
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps({'scope':a.scope,'head_sha':head,'base_sha':'dc6d6d80ed3f47046331432b446cf5c4081c3319',
 'actual_local_model':'LOCAL_ASR_BACKEND_NOT_RUN','human_UA_quality':'NOT_RUN','Galaxy':'HARDWARE_UNVERIFIED / NOT_RUN',
 'live_provider':'OFF / NOT_RUN','publication':'NO_RUNTIME_PUBLICATION','CI':'NOT_RUN','environment':{'python':platform.python_version(),
 'node':subprocess.check_output(['node','--version'],text=True).strip(),'npm':subprocess.check_output(['npm','--version'],text=True).strip(),
 'os':platform.system()+' '+platform.release(),'architecture':platform.machine()},'records':records},ensure_ascii=False,indent=2)+'\n')
