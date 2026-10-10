"""Trusted fixture executable: verifies process mechanics, not hostile OS confinement or real ASR."""
import threading,time
import pytest
from apps.core.local_asr import ProcessLocalASR
from apps.core.storage import SafeError,digest
from test_m4_voice import wav
from test_m1_domain import isolated

FIXTURE='''import json,os,sys,time
assert sys.argv[1]=='--synthetic-asr'
assert os.path.basename(sys.argv[2])=='input.wav'
assert os.path.dirname(sys.argv[2])==os.getcwd()
assert open(sys.argv[2],'rb').read(4)==b'RIFF'
mode=sys.argv[3]
if mode=='environment':assert set(os.environ) <= {'PYTHONIOENCODING','LC_CTYPE','__CF_USER_TEXT_ENCODING'}
if mode=='timeout':time.sleep(10)
if mode=='nonzero':raise SystemExit(7)
if mode=='malformed':print('SYNTHETIC malformed');raise SystemExit(0)
if mode=='oversized':print('x'*20000);raise SystemExit(0)
if mode=='stderr':sys.stderr.write('x'*20000);sys.stderr.flush();raise SystemExit(0)
if mode=='child':
 import subprocess
 p=subprocess.Popen([sys.executable,'-I','-S','-c','import time;time.sleep(10)'])
 open('../child.pid','w').write(str(p.pid));time.sleep(10)
r={'text':'SYNTHETIC trusted fake executable transcript','language':'uk'}
if mode=='tool':r['execute_shell']='never executable'
if mode=='path':r['filename']='../../never'
print(json.dumps(r))
'''
def adapter(root,scenario):
    root.mkdir();(root/'asr_fixture.py').write_text(FIXTURE)
    return ProcessLocalASR(root,digest(FIXTURE.encode()),scenario)
@pytest.mark.parametrize('scenario,error',[('valid',None),('environment',None),('nonzero','ASR_PROCESS_FAILED'),('malformed','ASR_OUTPUT_INVALID'),('oversized','ASR_OUTPUT_LIMIT'),('stderr','ASR_OUTPUT_LIMIT'),('timeout','ASR_TIMEOUT'),('tool','ASR_OUTPUT_INVALID'),('path','ASR_OUTPUT_INVALID')])
def test_M4_A06_exact_command_sanitized_bounded_process(isolated,scenario,error,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','SYNTHETIC never inherited')
    p=adapter(isolated/'process',scenario)
    # Successful protocol/exit checks tolerate interpreter spawn jitter; the
    # intentional ten-second stall still verifies its original 200ms deadline.
    # ProcessLocalASR production limits are unchanged.
    deadline=time.monotonic()+(.2 if scenario=='timeout' else 1)
    if error:
        with pytest.raises(SafeError,match=error):p.transcribe(wav(),'uk',threading.Event(),deadline)
    else:assert p.transcribe(wav(),'uk',threading.Event(),deadline)['text'].startswith('SYNTHETIC')
    assert p.last_spec['shell'] is False and p.last_spec['args'][1:3]==['-I','-S']
    assert set(p.last_spec['env'])=={'PYTHONIOENCODING'}
    assert not list((isolated/'process').glob('run-*'))

def test_M4_A06_cancel_process_group_children_and_fixture_hash(isolated):
    p=adapter(isolated/'process','child');cancel=threading.Event();result=[]
    def execute():
        try:p.transcribe(wav(),'uk',cancel,time.monotonic()+4)
        except SafeError as e:result.append(e.code)
    t=threading.Thread(target=execute);t.start();pidfile=p.root/'child.pid'
    deadline=time.monotonic()+2
    while not pidfile.exists() and time.monotonic()<deadline:time.sleep(.01)
    assert pidfile.exists();child=int(pidfile.read_text());cancel.set();t.join(2)
    assert not t.is_alive() and result==['CANCELLED']
    import subprocess
    # Child may briefly remain a zombie, but cannot execute after process-group SIGKILL.
    state=subprocess.run(['ps','-o','stat=','-p',str(child)],capture_output=True,text=True).stdout.strip()
    assert not state or state.startswith('Z')
    p.fixture.write_text('raise SystemExit(0)')
    with pytest.raises(SafeError,match='FIXTURE_DENIED'):p.transcribe(wav(),'uk',threading.Event(),time.monotonic()+1)
