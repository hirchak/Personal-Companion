"""Two actual CLI HTTP processes; fresh synthetic data only, codes never evidence."""
import subprocess,sys,time,select
from uuid import uuid4
import httpx
from apps.core.storage import REPO,Store
from test_m1_domain import isolated


def test_http_process_restart_durable_messages_and_no_restored_permission(isolated):
 root=isolated/'cli-restart';Store(root);origin='http://127.0.0.1:8778'
 def boot(demo):
  args=[sys.executable,'-m','apps.core.cli','serve','--root',str(root),'--port','8778']
  if demo:args+=['--synthetic-conversations']
  process=subprocess.Popen(args,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
  try:
   assert select.select([process.stdout],[],[],8)[0]
   process.stdout.readline();code=process.stdout.readline().strip().split(': ')[-1]
   client=httpx.Client(base_url=origin,headers={'Origin':origin},timeout=5)
   for _ in range(60):
    try:
     auth=client.post('/api/v1/auth/unlock',json={'code':code})
     assert auth.status_code==200;client.headers['X-CSRF-Token']=auth.json()['csrf_token'];return process,client
    except httpx.ConnectError:time.sleep(.05)
   raise AssertionError('SYNTHETIC_CLI_NOT_READY')
  except BaseException:process.terminate();process.wait(8);raise
 def stop(process,client):client.close();process.terminate();process.wait(8)
 p,c=boot(True)
 try:
  created=c.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json();id=created['conversation']['id']
  sent=c.post('/api/v1/conversations/'+id+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC durable CLI fixture'}).json()
  assert len(sent['messages'])==2
 finally:stop(p,c)
 p,c=boot(False)
 try:
  reopened=c.get('/api/v1/conversations/'+id).json();assert reopened['messages']==sent['messages']
  assert c.get('/api/v1/conversations/status').json()['responder']=='OFF'
  result=c.post('/api/v1/conversations/'+id+'/messages',json={'operation_id':str(uuid4()),'base_revision':2,'text':'ORIGINAL SYNTHETIC second process'}).json()
  assert len(result['messages'])==3 and result['messages'][-1]['role']=='USER'
 finally:stop(p,c)
