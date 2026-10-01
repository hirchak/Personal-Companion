#!/usr/bin/env python3
"""Finite synthetic exact-C checks. Full logs ignored; evidence has status/commands only."""
import argparse,json,os,platform,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/evidence/M6/EXACT_C_CHECKS.json');a=p.parse_args()
    logdir=ROOT/'generated/m6-exact';logdir.mkdir(parents=True,exist_ok=True)
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    before=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    results=[]
    checks=[('web_build',['npm','--prefix','apps/web','run','build']),('web_tests',['npm','--prefix','apps/web','test']),('python',['.venv/bin/python','-m','pytest','-q']),('android',['apps/android-health/gradlew','--offline',':app:assembleDebug',':app:testDebugUnitTest']),('benchmark',['.venv/bin/python','-m','scripts.measure_m6']),('hardware_sanitizer',['.venv/bin/python','scripts/m6_evidence.py']),('docs',['.venv/bin/python','scripts/check_docs.py']),('snapshot',['.venv/bin/python','scripts/build_chatgpt_context.py']),('privacy',['.venv/bin/python','scripts/check_privacy.py','--include-generated']),('diff',['git','diff','--check'])]
    for label,cmd in checks:
        start=time.monotonic();log=logdir/(label+'.log')
        with log.open('wb') as out:run=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
        row={'name':label,'command':' '.join(cmd),'exit_code':run.returncode,'status':'PASS' if run.returncode==0 else 'FAIL','elapsed_seconds':round(time.monotonic()-start,3),'full_log':'generated/m6-exact/'+log.name}
        content=log.read_text(errors='replace')
        if label=='python':
            match=re.search(r'(\d+) passed',content);row['passed_tests']=int(match.group(1)) if match else None
        if label=='web_tests':
            match=re.search(r'Tests\s+(\d+) passed',content);row['passed_tests']=int(match.group(1)) if match else None
        if label=='android':
            import xml.etree.ElementTree as ET
            files=list((ROOT/'apps/android-health/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml'))
            row['passed_tests']=sum(int(ET.parse(f).getroot().get('tests','0'))-int(ET.parse(f).getroot().get('failures','0'))-int(ET.parse(f).getroot().get('errors','0')) for f in files)
        results.append(row);print(f"{label}: {row['status']} exit={run.returncode}",flush=True)
        if run.returncode!=0:break
    evidence={'implementation_sha':sha,'clean_worktree_at_start':not before.strip(),'environment':{'python':platform.python_version(),'node':subprocess.check_output(['node','--version'],text=True).strip(),'platform':platform.system(),'architecture':platform.machine()},'fixture_provenance':'SYNTHETIC_ONLY_NO_REAL_HEALTH_ROOT','hardware_scope':'EARLY_ACTUAL_0.6.0_SEPARATE_FROM_FINAL_0.6.1_SYNTHETIC','checks':results,'status':'PASS' if len(results)==len(checks) and all(r['exit_code']==0 for r in results) else 'FAIL'}
    a.output.write_text(json.dumps(evidence,indent=2)+'\n')
    return int(evidence['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
