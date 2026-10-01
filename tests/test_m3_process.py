"""Trusted fake executable integration only. Does not assert host OS isolation."""
import hashlib
import os
import threading
import time
import pytest
from apps.core.fake_process import FakeProcessProvider
from apps.core.storage import SafeError
from test_m3_runtime import rt, entry, execute
from test_m1_domain import isolated

FIXTURE = '''import json,os,sys,time
assert sys.argv[1] == '--synthetic-provider'
p=json.load(sys.stdin);mode=sys.argv[2]
if mode=='timeout':time.sleep(10)
if mode=='nonzero':raise SystemExit(7)
if mode=='malformed':print('SYNTHETIC invalid json');raise SystemExit(0)
if mode=='oversized':print('x'*12000);raise SystemExit(0)
if mode=='environment':
 assert not any(k in os.environ for k in ('OPENAI_API_KEY','CODEX_HOME','HOME','PATH','GITHUB_TOKEN'))
r={'task':p['task'],'sources':p['entry_refs'],'type':p['entries'][0]['type'],'tags':['нотатка'],'reason':'selected_entry'}
if mode=='tool':r['execute_shell']='denied command'
if mode=='path':r['read_arbitrary_path']='~/.ssh'
print(json.dumps(r))
'''

def fake(rt,isolated,scenario):
    root=isolated/('process-'+scenario);root.mkdir(mode=0o700)
    fixture=root/'fixture.py';fixture.write_text(FIXTURE);fixture.chmod(0o400)
    provider=FakeProcessProvider(root,hashlib.sha256(FIXTURE.encode()).hexdigest(),scenario)
    rt.providers['mock']=provider
    return provider

@pytest.mark.parametrize('scenario,state,error',[('valid','DONE',None),('environment','DONE',None),('malformed','FAILED','OUTPUT_INVALID'),('nonzero','FAILED','PROCESS_NONZERO'),('oversized','FAILED','OUTPUT_LIMIT'),('tool','FAILED','OUTPUT_INVALID'),('path','FAILED','OUTPUT_INVALID'),('timeout','FAILED','JOB_TIMEOUT')])
def test_M3_A10_fake_process_exact_command_env_bounded_output(rt,isolated,scenario,state,error,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','SYNTHETIC-not-a-key')
    monkeypatch.setenv('GITHUB_TOKEN','SYNTHETIC-not-a-token')
    provider=fake(rt,isolated,scenario);rt.timeout=.15
    ref=entry(rt);_,j,_=execute(rt,[ref]);assert j['state']==state and j['error']==error
    assert provider.last_spec['shell'] is False
    assert provider.last_spec['args'][1:3]==['-I','-S']
    assert set(provider.last_spec['env'])=={'PYTHONIOENCODING'}
    assert provider.last_spec['cwd']==str(isolated/('process-'+scenario))
    assert rt.journal.get(ref['id'])['revision']==1
    if state!='DONE':assert not rt.suggestions()['items'] and not rt.memories()['items']


def test_M3_A10_fake_process_cancel_terminates_without_effect(rt,isolated):
    from test_m3_runtime import queue
    provider=fake(rt,isolated,'timeout');rt.timeout=1;rt.set_mode('MOCK')
    _,job,_=queue(rt,[entry(rt)])
    thread=threading.Thread(target=rt.run_one);thread.start()
    deadline=time.monotonic()+1
    while provider.last_spec is None and time.monotonic()<deadline:time.sleep(.005)
    rt.cancel(job['id']);thread.join(1)
    assert not thread.is_alive() and rt.jobs()['items'][0]['state']=='CANCELLED'
    assert not rt.suggestions()['items']


def test_M3_A10_process_fixture_integrity_and_request_tools_denied(rt,isolated):
    from test_m3_runtime import preview
    provider=fake(rt,isolated,'valid')
    p=preview(rt,[entry(rt)])['package'];p['tools']=['execute_shell']
    with pytest.raises(SafeError,match='PROCESS_REQUEST_DENIED'):provider.execute(p,threading.Event(),time.monotonic()+1)
    provider.fixture.chmod(0o600);provider.fixture.write_text('raise SystemExit(0)')
    with pytest.raises(SafeError,match='FAKE_FIXTURE_DENIED'):provider.execute({},threading.Event(),time.monotonic()+1)
    assert provider.executions==0
