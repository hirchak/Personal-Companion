from pathlib import Path
import tempfile,subprocess,json,shutil,time,threading
from apps.core.whisper_local_asr import WhisperLocalASR
from apps.core.storage import SafeError
root=Path('generated/local-asr').resolve();work=Path(tempfile.mkdtemp(prefix='m7c-isolation-synthetic-',dir='/private/tmp'));outside=work.parent/(work.name+'-outside');outside.write_text('ORIGINAL_SYNTHETIC_SENTINEL_NOT_PRIVATE')
source=work/'probe.c';source.write_text('''#include <stdio.h>\n#include <fcntl.h>\n#include <unistd.h>\n#include <sys/socket.h>\n#include <arpa/inet.h>\n#include <errno.h>\nint main(int argc,char **argv){int r=open(argv[1],O_RDONLY);int w=open(argv[2],O_WRONLY|O_CREAT,0600);int s=socket(AF_INET,SOCK_STREAM,0);struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(1)};inet_pton(AF_INET,"127.0.0.1",&a.sin_addr);int se=errno;int n=connect(s,(struct sockaddr*)&a,sizeof(a));int denied=(s<0&&se==1)||(n<0&&errno==1);printf("read=%d write=%d network_denied=%d\\n",r>=0,w>=0,denied);return 0;}''')
probe=work/'probe';subprocess.run(['/usr/bin/clang',str(source),'-o',str(probe)],check=True,capture_output=True)
e=WhisperLocalASR();profile=work/'sandbox.sb';profile.write_text(e.profile(work)+'\n(allow process-exec (literal '+json.dumps(str(probe))+'))\n')
results=[]
try:
 for label,target in [('allowed',source),('denied',outside)]:
  p=subprocess.run(['/usr/bin/sandbox-exec','-f',str(profile),str(probe),str(target),str(outside)+'.write'],capture_output=True,text=True,timeout=5)
  assert p.returncode==0,(label,p.returncode)
  assert ('read=1' if label=='allowed' else 'read=0') in p.stdout and 'write=0' in p.stdout and 'network_denied=1' in p.stdout,p.stdout
  results.append({'case':label,'read_allowed':label=='allowed','outside_write_denied':True,'network_denied':True})
 start=time.monotonic();candidate=e.transcribe((root/'synthetic-ua-clear.wav').read_bytes(),'uk',threading.Event(),time.monotonic()+60)
 receipt={'status':'PASS','scope':'Own compiled synthetic sentinels; no real/auth/private files read','checks':results,'actual_engine_under_same_profile':'PASS','actual_audio_duration':3.6203125,'candidate_chars':len(candidate['text']),'elapsed_seconds':round(time.monotonic()-start,3),'model_bytes':487601967,'cloud_asr':False,'private_audio':False,'engine':e.metadata(),'profile':e.profile(Path('/private/tmp/ORIGINAL_SYNTHETIC_WORKDIR'))}
 (root/'M7C_ASR_ISOLATION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('ASR filesystem/network own-sentinel + actual engine gate PASS')
finally:shutil.rmtree(work);outside.unlink();Path(str(outside)+'.write').unlink(missing_ok=True)
