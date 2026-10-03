"""Actually terminate/restart the loopback server on a disposable synthetic root."""
import subprocess,sys,time
from uuid import uuid4
import httpx
from test_m1_domain import isolated
from apps.core.storage import Store

ORIGIN='http://127.0.0.1:8772'

def launch(root):
 p=subprocess.Popen([sys.executable,'-m','apps.core.cli','serve','--root',str(root),'--port','8772','--synthetic-practices'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 # The only printed secret is a disposable synthetic unlock code; keep it local, never evidence.
 code=None
 for _ in range(5):
  line=p.stdout.readline()
  if 'One-time unlock code' in line:code=line.split(': ',1)[1].strip();break
 assert code
 client=httpx.Client(base_url=ORIGIN,headers={'Origin':ORIGIN},timeout=5)
 for _ in range(100):
  try:
   if client.get('/').status_code==200:break
  except httpx.TransportError:pass
  time.sleep(.02)
 auth=client.post('/api/v1/auth/unlock',json={'code':code});assert auth.status_code==200
 client.headers['X-CSRF-Token']=auth.json()['csrf_token']
 return p,client

def stop(p,c):
 c.close();p.terminate();p.wait(8)

def action(c,s,name,response=None):
 body={'operation_id':str(uuid4()),'base_revision':s['revision'],'action':name}
 if name in {'next','save'}:body['step_id']=s['current_step']
 if response is not None:body['response']=response
 r=c.post('/api/v1/practices/sessions/'+s['id']+'/actions',json=body);assert r.status_code==200
 return r.json()

def test_server_termination_restart_resume_saved_exact_step(isolated):
 root=isolated/'server';Store(root);p,c=launch(root)
 try:
  item=next(x for x in c.get('/api/v1/practices/catalog').json()['items'] if x['available'])
  s=c.post('/api/v1/practices/sessions',json={**{k:item[k] for k in ('module_id','module_version','content_hash')},'operation_id':str(uuid4())}).json()
  s=action(c,s,'next');s=action(c,s,'save',True);s=action(c,s,'next');s=action(c,s,'save','SYNTHETIC server restart text');s=action(c,s,'pause')
 finally:stop(p,c)
 p,c=launch(root)
 try:
  recovered=c.get('/api/v1/practices/sessions/'+s['id']).json()
  for key in ['state','responses','current_step','revision','admission_binding','package_hash']:assert recovered[key]==s[key]
  resumed=action(c,recovered,'resume');assert resumed['state']=='ACTIVE' and resumed['responses']==s['responses']
 finally:stop(p,c)
