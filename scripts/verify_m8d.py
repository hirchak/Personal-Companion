"""Exact-C package/private lifecycle on disposable ORIGINAL SYNTHETIC roots. No provider/owner data.

M8D manager validates both target releases; old M8C runtime restarts the compatible pre-upgrade snapshot.
"""
import argparse,json,os,select,shutil,socket,subprocess,tempfile,time
from pathlib import Path
from uuid import uuid4
import httpx
from apps.core import release as r,local_private as p
from apps.core.storage import REPO,SafeError,digest
from scripts.verify_m8b import runtime_only_environment


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--package',type=Path,required=True);parser.add_argument('--previous-package',type=Path,required=True)
 parser.add_argument('--source-fixture',action='store_true');parser.add_argument('--output',type=Path,default=REPO/'generated/m8d-verification');a=parser.parse_args();a.package=a.package.resolve();a.previous_package=a.previous_package.resolve();a.output.mkdir(parents=True,exist_ok=True)
 m=r.read_json(a.package/'release-manifest.json');r.validate_package(a.package,m['manifest_hash']);assert m['format']==4
 if not a.source_fixture:subprocess.run(['git','cat-file','-e',m['git_commit']+'^{commit}'],cwd=REPO,check=True,capture_output=True)
 old=r.read_json(a.previous_package/'release-manifest.json');r.validate_package(a.previous_package,old['manifest_hash']);assert old['format']==3
 for name in m['files']:
  if name.startswith('apps/core/') and (REPO/name).is_file():assert digest((REPO/name).read_bytes())==m['files'][name],'EXACT_SOURCE_MISMATCH'
 work=Path(tempfile.mkdtemp(prefix='m8d-original-synthetic-lifecycle-',dir=Path(tempfile.gettempdir()).resolve()));os.chmod(work,0o700)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 app,data,b=work/'app',work/'PRIVATE_LOCAL_ORIGINAL_SYNTHETIC_ONLY',work/'protected backups';b.mkdir(mode=0o700)
 # A packaged manager rejects source-code Git roots as operational paths. Copy only the trusted
 # old software into the owned disposable container, never any installed owner app/data.
 old_package=work/'TRUSTED_M8C_SOFTWARE_ONLY';shutil.copytree(a.previous_package,old_package)
 a.previous_package=old_package
 checks={};process=client=None
 runtime_python,runtime_proof=runtime_only_environment(work/'runtime')
 def command(name,target=a.package,**values):
  args=[str(runtime_python),'-I','-B',str(a.package/'launch.py'),name]
  if name not in {'backup','uninstall','delete-private-data'}:args+=['--package',str(target),'--manifest-hash',r.read_json(target/'release-manifest.json')['manifest_hash']]
  if name!='delete-private-data':args+=['--mode','PRIVATE_LOCAL']
  for key,value in values.items():
   if value is True:args.append('--'+key.replace('_','-'))
   elif value is not None:args+=['--'+key.replace('_','-'),str(value)]
  result=subprocess.run(args,cwd=work,capture_output=True,text=True)
  if result.returncode:
   try:code=json.loads(result.stdout).get('code','EXACT_RELEASE_LIFECYCLE_FAILED')
   except ValueError:code='EXACT_RELEASE_LIFECYCLE_FAILED'
   raise SafeError(code)
  return json.loads(result.stdout)
 def init_kwargs(root):return dict(backup_directory=b,confirm='INITIALIZE_PRIVATE_LOCAL:'+str(root),data_owner_consent=p.CONSENT,acknowledge_no_cloud_directory=True,port=port)
 def boot(target,application,root):
  nonlocal process,client
  build=r.read_json(target/'release-manifest.json')['git_commit']
  args=[str(runtime_python),'-I','-B',str(target/'launch.py'),'start','--mode','PRIVATE_LOCAL','--app',str(application),'--data',str(root),'--port',str(port)]
  if target==a.package:args+=['--local-asr-assets',str(REPO/'generated/local-asr')]
  process=subprocess.Popen(args,cwd=work,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,env=dict(os.environ,OPENAI_API_KEY='ORIGINAL_SYNTHETIC_NOT_A_KEY',PC_CONVERSATION_PROVIDER='ON',PC_HEALTH_BRIDGE='ON'))
  if not select.select([process.stdout],[],[],20)[0]:raise SafeError('SYNTHETIC_RUNTIME_START_TIMEOUT')
  first=process.stdout.readline();assert first.startswith('Local private runtime:'),'SYNTHETIC_RUNTIME_START_FAILED'
  unlock=process.stdout.readline().strip().split(': ',1)[1]
  client=httpx.Client(base_url=f'http://127.0.0.1:{port}',headers={'Origin':f'http://127.0.0.1:{port}','X-PC-Build':build},timeout=10)
  for _ in range(100):
   try:
    assert client.get('/api/v1/entries').status_code==401
    response=client.post('/api/v1/auth/unlock',json={'code':unlock});assert response.status_code==200
    client.headers['X-CSRF-Token']=response.json()['csrf_token'];return
   except httpx.ConnectError:time.sleep(.05)
  raise SafeError('SYNTHETIC_RUNTIME_NOT_READY')
 def stop():
  nonlocal process,client
  if client:client.close();client=None
  if process:
   if process.poll() is None:process.terminate();process.wait(10)
   process.stdout.close();process=None
 try:
  pre=command('private-preflight',app=app,data=data,backup_directory=b,port=port);assert pre['status']=='PASS';checks['private_security_preflight']=True
  command('initialize-private',target=a.previous_package,app=app,data=data,**init_kwargs(data));boot(a.previous_package,app,data)
  entry=str(uuid4());body={'operation_id':str(uuid4()),'entry_id':entry,'base_revision':0,'payload':{'type':'daily','raw_text':'ORIGINAL SYNTHETIC exact release lifecycle','timezone':'Europe/Warsaw','local_date':'2099-01-01','time_precision':'date'}}
  assert client.post('/api/v1/entries',json=body).status_code==201
  response=client.patch('/api/v1/entries/'+entry,json={'operation_id':str(uuid4()),'base_revision':1,'changes':{'raw_text':'ORIGINAL SYNTHETIC persisted revision'}});assert response.status_code==200
  stop();checks['old_m8c_runtime_fixture']=True
  backup=b/'before upgrade';upgrade=command('upgrade',app=app,data=data,backup=backup,port=port);assert upgrade['status']=='PASS';checks['private_upgrade']=True
  provenance=r.verify_backup(backup,m['manifest_hash'],upgrade['backup_manifest_hash'])['release_provenance']
  assert provenance['producing_manifest']['release_id']==m['release_id'] and provenance['source_release']['release_id']==old['release_id'];checks['exact_backup_producer_and_old_source']=True
  boot(a.package,app,data);status=client.get('/api/v1/status').json()
  assert status['private_pilot']['state']=='PRIVATE_AI_OFF' and status['private_pilot']['local_voice']=='OFF'
  assert client.get('/api/v1/entries/'+entry).json()['raw_text']=='ORIGINAL SYNTHETIC persisted revision'
  assert client.get('/api/v1/entries/'+entry+'/revisions').status_code==200
  for path in ['health/import','practices/start','device/pair','ai/mode','cloud-sync']:
   assert client.post('/api/v1/'+path,json={}).status_code==403
  assert client.get('/runtime-mode.json').json()['private_optional_profile']=='MAC_PRIVATE_AI_VOICE_PILOT_V1'
  checks['new_runtime_restart_data_and_safe_default_off']=True;stop()
  full_backup=b/'after upgrade';receipt=command('backup',app=app,data=data,backup=full_backup)
  restored=work/'restored private';restored_app=work/'restored app'
  command('restore',app=restored_app,data=restored,backup=full_backup,producer_manifest_hash=m['manifest_hash'],backup_manifest_hash=receipt['backup_manifest_hash'],**init_kwargs(restored))
  boot(a.package,restored_app,restored);assert client.get('/api/v1/private-pilot/status').json()['state']=='PRIVATE_AI_OFF';assert client.get('/api/v1/entries/'+entry).status_code==200;stop();checks['private_restore_restart_default_off']=True
  rollback_data=work/'rollback private';rollback_app=work/'rollback app'
  command('rollback',target=a.previous_package,app=rollback_app,data=rollback_data,backup=backup,producer_manifest_hash=m['manifest_hash'],backup_manifest_hash=upgrade['backup_manifest_hash'],**init_kwargs(rollback_data))
  boot(a.previous_package,rollback_app,rollback_data);assert client.get('/api/v1/entries/'+entry).json()['raw_text']=='ORIGINAL SYNTHETIC persisted revision';assert client.get('/api/v1/status').json()['provider']=='OFF';stop();checks['fresh_root_old_m8c_rollback_restart']=True
  command('uninstall',app=app,data=data);assert data.exists() and full_backup.exists();checks['uninstall_keep_private_data']=True
  command('delete-private-data',data=data,confirm='DELETE_PRIVATE_LOCAL_DATA:'+str(data));assert not data.exists() and full_backup.exists();checks['separate_exact_delete_keeps_backup']=True
  result={'status':'PASS','scope':'PRIVATE_LOCAL_RUNTIME_WITH_ORIGINAL_SYNTHETIC_CONTENT','source_fixture':a.source_fixture,'release_id':m['release_id'],'implementation_sha':m['git_commit'],'manifest_hash':m['manifest_hash'],'runtime_input_hash':m['runtime_input_hash'],'previous_release':old['release_id'],'private_preflight':pre,'runtime_only_environment':runtime_proof,'checks':checks,'real_private_data_used':0,'live_provider_calls':0,'system_changes':0,'actual_private_ai_activation':'NOT_STARTED'}
  (a.output/'LIFECYCLE.json').write_text(json.dumps(result,indent=2)+'\n');(a.output/'RELEASE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n');print('M8D source-fixture lifecycle rehearsal PASS' if a.source_fixture else 'M8D exact-C private synthetic release lifecycle PASS')
 finally:stop();shutil.rmtree(work)

if __name__=='__main__':main()
