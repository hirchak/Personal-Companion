"""M8D native provider child OS read/write boundary, with no application/vault filesystem authority."""
import json,os,subprocess,sys,threading,selectors,signal
from pathlib import Path
from .codex_conversation_provider import CodexConversationProvider
from .storage import SafeError

class PrivateCodexConversationProvider(CodexConversationProvider):
 catalog_models=('gpt-6-luna','gpt-6.1-sol')
 def __init__(self,model='gpt-6-luna',executable=None,budget=None,effort='high'):
  from .local_private_ai import EFFORT_CEILINGS
  if effort not in EFFORT_CEILINGS.get(model,()):raise SafeError('OWNER_MODEL_EFFORT_NOT_AUTHORIZED',403)
  if budget is None:raise SafeError('PRIVATE_ATTEMPT_ACCOUNTING_REQUIRED',403)
  super().__init__(model=model,executable=executable,budget=budget,effort=effort,private_scope=True)
  self.transport=threading.local()
  self.sandbox=Path('/usr/bin/sandbox-exec')
  if not self.sandbox.is_file():raise SafeError('PRIVATE_PROVIDER_OS_ISOLATION_UNAVAILABLE',403)
 def os_profile(self,work,proxy_port=None):
  q=lambda value:json.dumps(str(value));executable=Path(self.executable).resolve();home=Path.home();codex=home/'.codex'
  # The native first-party client retains existing auth. No credential is extracted/copied by this adapter.
  # Global user data and workspace/vault roots are not permitted. Temporary client state is disposable.
  reads=['/System','/usr/lib','/Library/Apple','/private/var/db/dyld','/dev',str(executable.parent)]
  literals=['/','/etc/localtime','/etc/resolv.conf','/private/etc/resolv.conf',str(executable),str(work.parent),
   str(codex/'auth.json'),str(codex/'models_cache.json'),str(home/'.CFUserTextEncoding')]
  return '\n'.join(['(version 1)','(allow default)','(deny file-read-data)','(deny file-write*)','(deny process-exec)',
   '(deny network*)',
   '(allow network-outbound (remote tcp '+q('localhost:'+str(proxy_port))+'))' if proxy_port is not None else '(deny network-outbound)',
   '(allow process-fork)','(allow process-exec (literal '+q(executable)+'))','(allow sysctl-read)','(allow mach-lookup)',
   '(allow file-read-data '+' '.join('(subpath '+q(p)+')' for p in reads)+ ' '+' '.join('(literal '+q(p)+')' for p in literals)+' (subpath '+q(work)+'))',
   '(allow file-write* (subpath '+q(work)+') (literal "/dev/null"))'])
 def spec(self,work):
  from .local_private import owner_only,require_volume
  owner_only(work);require_volume(work)
  original=super().spec(work)
  # Native SDK reads its existing auth directly through a read-only reference. No credential bytes
  # are read, copied, returned or rewritten by the application. All other client state is disposable.
  client_home=work/'native-client';client_home.mkdir(mode=0o700)
  (client_home/'auth.json').symlink_to(Path.home()/'.codex/auth.json')
  if (Path.home()/'.codex/models_cache.json').is_file():
   original['args'] += ['-c','model_catalog_json='+json.dumps(str(Path.home()/'.codex/models_cache.json'))]
  original['env']['CODEX_HOME']=str(client_home)
  original['env']['TMPDIR']=str(work)
  proxy_port=self.start_transport(work)
  original['env']['HTTPS_PROXY']='http://127.0.0.1:'+str(proxy_port)
  original['env']['HTTP_PROXY']=original['env']['HTTPS_PROXY']
  original['env']['NO_PROXY']=''
  profile=work/'private-provider.sb';profile.write_text(self.os_profile(work,proxy_port));profile.chmod(0o600)
  original['args'] += ['-c','sqlite_home='+json.dumps(str(work/'state'))]
  original['args']=[str(self.sandbox),'-f',str(profile),*original['args']]
  return original
 def start_transport(self,work):
  q=lambda value:json.dumps(str(value))
  python=Path(sys.executable).resolve()
  framework=Path(sys.base_prefix)/'Resources/Python.app/Contents/MacOS/Python'
  if framework.is_file():python=framework.resolve()
  script=Path(__file__).with_name('local_provider_tunnel.py').resolve()
  reads=['/System','/usr/lib','/Library/Apple','/private/var/db/dyld','/private/var/db/timezone','/usr/share/locale','/dev',str(Path(sys.base_prefix)),str(python.parent)]
  rules=['(version 1)','(allow default)','(deny file-read-data)','(deny file-write*)','(deny process-exec)','(deny network*)',
   '(allow process-exec (literal '+q(python)+'))','(allow mach-lookup)','(allow sysctl-read)',
   '(allow file-read-data '+ ' '.join('(subpath '+q(p)+')' for p in reads)+' (literal '+q(script)+') (literal "/") (literal "/etc/resolv.conf") (literal "/private/etc/resolv.conf") (literal "/private/etc/hosts") (literal "/etc/localtime") (literal '+q(Path.home()/'.CFUserTextEncoding')+'))',
   '(allow network-bind (local tcp "localhost:*"))','(allow network-inbound (local tcp "localhost:*"))',
   '(allow network-outbound (remote tcp "*:443") (literal "/private/var/run/mDNSResponder"))']
  profile=work/'transport.sb';profile.write_text('\n'.join(rules));profile.chmod(0o600)
  process=subprocess.Popen([str(self.sandbox),'-f',str(profile),str(python),'-I','-S','-B',str(script)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env={'LANG':'en_US.UTF-8'},cwd=work,start_new_session=True)
  self.transport.process=process
  with selectors.DefaultSelector() as selector:
   selector.register(process.stdout,selectors.EVENT_READ)
   if not selector.select(5):raise SafeError('PRIVATE_PROVIDER_TRANSPORT_UNAVAILABLE',503)
   value=process.stdout.readline(8)
  try:port=int(value)
  except ValueError:raise SafeError('PRIVATE_PROVIDER_TRANSPORT_UNAVAILABLE',503) from None
  if not 1024<=port<=65535:raise SafeError('PRIVATE_PROVIDER_TRANSPORT_UNAVAILABLE',503)
  return port
 def stop_transport(self):
  process=getattr(self.transport,'process',None)
  if process is not None:
   if process.poll() is None:
    os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=2)
   process.stdout.close();self.transport.process=None
 def discover(self):
  try:return super().discover()
  finally:self.stop_transport()
 def readiness(self):
  try:return super().readiness()
  finally:self.stop_transport()
 def execute(self,*args,**kwargs):
  try:return super().execute(*args,**kwargs)
  finally:self.stop_transport()
 def metadata(self):
  return dict(super().metadata(),private_scope='THIS_OWNER_BOUNDED_ONLY',os_filesystem_boundary='DENY_DATA_BY_DEFAULT_NO_VAULT_ROOTS',retention='NOT_ZERO_RETENTION_CERTIFIED',network_boundary='NATIVE_CHILD_LOOPBACK_ONLY_TLS_BLIND_FIXED_CHATGPT_443_TUNNEL',host_policy='DISPOSABLE_CLIENT_STATE_NO_GLOBAL_CONFIG_HISTORY_OR_VAULT')
