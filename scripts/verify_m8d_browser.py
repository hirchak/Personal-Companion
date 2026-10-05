"""Real Chromium private UI on ORIGINAL SYNTHETIC disposable roots; fixture inference, native local ASR.

Before C, --source-fixture checks uncommitted UI only. After C, --package validates exact release.
No owner vault, operator terminal, real microphone, auth extraction or live provider call.
"""
import argparse,json,os,shutil,socket,subprocess,tempfile,threading,time
from pathlib import Path
from uuid import uuid4
import uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core import release as r,local_private as p
from apps.core.storage import REPO,encode,digest
from apps.core.root_types import RootKind
from apps.core.api import create_app
from apps.core.whisper_local_asr import WhisperLocalASR
from apps.core.local_private_ai import PROFILE

class FixtureProvider:
 def __init__(self,model,effort):self.model=model;self.effort=effort;self.calls=[]
 def metadata(self):return {'route':'CODEX_SUBSCRIPTION','model':self.model,'effort':self.effort,'profile':self.model+':'+self.effort,'live':False,'fallback':False,'payg':False}
 def execute(self,payload,*args):
  self.calls.append(payload)
  value={'assistant_text':'ORIGINAL SYNTHETIC · Який невеликий крок ви обираєте?','source_refs':[payload['current_message_ref']],'goal_suggestion':None,'closure':None,'topics':['self_reflection'],'working_map':None}
  return {'text':encode(value),'route':'CODEX_SUBSCRIPTION','model':self.model,'effort':self.effort,'profile':self.model+':'+self.effort,'profile_verified':True}


def source_package(work):
 package=work/'ORIGINAL_SYNTHETIC_SOURCE_PACKAGE';package.mkdir(mode=0o700)
 for directory in ('apps/core','skills/conversation','research/admission','packages/practices/synthetic'):
  shutil.copytree(REPO/directory,package/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 files=['requirements.lock','requirements.runtime.lock','packages/pilot/MAC_CORE_PROFILE.json','packages/pilot/MAC_PRIVATE_CORE_PROFILE.json','packages/pilot/MAC_PRIVATE_AI_VOICE_PROFILE.json','apps/web/package-lock.json','scripts/m7_admission.py','apps/web/src/PracticePanel.tsx','apps/web/src/practice-model.ts','apps/web/src/style.css']
 for name in files:
  target=package/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
 shutil.copytree(REPO/'apps/web/dist',package/'apps/web/dist')
 (package/'launch.py').write_text("import sys\nfrom pathlib import Path\nsys.dont_write_bytecode=True\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom apps.core.release import main\nmain()\n")
 m={'format':4,'release_id':'M8D-'+'a'*40,'git_commit':'a'*40,'schema_version':11,'python_input_hash':digest((package/'requirements.lock').read_bytes()),'runtime_input_hash':digest((package/'requirements.runtime.lock').read_bytes()),'web_lock_hash':digest((package/'apps/web/package-lock.json').read_bytes()),'platform':{'os':'Darwin','architecture':'arm64','python':'3.13','dependencies':'EXACT_RUNTIME_LOCK','self_contained':False},'defaults':r.DEFAULTS,'compatibility':{'schema_min':2,'schema_max':11,'web_contract':2,'downgrade':'FRESH_ROOT_BACKUP_ONLY'},'files':r.file_hashes(package)}
 m['manifest_hash']=r.identity(m);(package/'release-manifest.json').write_text(encode(m));return package,m


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--package',type=Path);parser.add_argument('--source-fixture',action='store_true')
 parser.add_argument('--output',type=Path,default=REPO/'generated/m8d-browser');a=parser.parse_args()
 if bool(a.package)==bool(a.source_fixture):raise ValueError('Exactly one explicit source required')
 a.output.mkdir(parents=True,exist_ok=True)
 work=Path(tempfile.mkdtemp(prefix='m8d-original-synthetic-browser-',dir=Path(tempfile.gettempdir()).resolve()))
 server=thread=None;browser=None
 try:
  if a.source_fixture:package,m=source_package(work);build='DEVELOPMENT'
  else:package=a.package;m=r.read_json(package/'release-manifest.json');r.validate_package(package,m['manifest_hash']);build=m['git_commit']
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  app_root,data,backup=work/'app',work/'PRIVATE_LOCAL_WITH_ORIGINAL_SYNTHETIC_CONTENT',work/'protected backups';backup.mkdir(mode=0o700)
  preflight=p.preflight(package,m['manifest_hash'],app_root,data,backup,port)
  assert preflight['status']=='PASS'
  r.initialize_private(package,m['manifest_hash'],app_root,data,backup,'INITIALIZE_PRIVATE_LOCAL:'+str(data),p.CONSENT,True,port=port)
  wav=work/'ORIGINAL_SYNTHETIC_LESYA.wav';aiff=work/'ORIGINAL_SYNTHETIC_LESYA.aiff'
  subprocess.run(['/usr/bin/say','-v','Lesya','-o',str(aiff),'Це оригінальний синтетичний тест. Маленький крок допомагає почати паперовий сад.'],check=True,capture_output=True)
  subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@16000','-c','1',str(aiff),str(wav)],check=True,capture_output=True)
  engine=WhisperLocalASR(REPO/'generated/local-asr',private_scope=True)
  providers=[]
  def factory(mode,model,effort):
   adapter=FixtureProvider(model,effort);providers.append(adapter);return adapter
  application=create_app(data,port=port,web=package/'apps/web/dist',root_kind=RootKind.PRIVATE_LOCAL,release_identity=build,m8d_private=True,private_provider_factory=factory,private_asr_factory=lambda:engine,conversation_timeout=120)
  # Exact ordered journal preview regression; ORIGINAL SYNTHETIC content in the owned test vault only.
  from apps.core.models import Create
  selected_id=uuid4()
  application.state.journal.write('create',selected_id,Create(operation_id=uuid4(),entry_id=selected_id,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC explicitly selected browser journal'}))
  hidden_id=uuid4()
  application.state.journal.write('create',hidden_id,Create(operation_id=uuid4(),entry_id=hidden_id,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC UNSELECTED_BROWSER_JOURNAL_SENTINEL'}))
  server=uvicorn.Server(uvicorn.Config(application,host='127.0.0.1',port=port,access_log=False,log_level='critical'))
  thread=threading.Thread(target=server.run,daemon=True);thread.start()
  for _ in range(100):
   if server.started:break
   time.sleep(.05)
  assert server.started
  os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
  origin=f'http://127.0.0.1:{port}';nonloopback=[];errors=[];checks={}
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+str(wav)])
   ctx=browser.new_context(viewport={'width':1440,'height':1000},permissions=['microphone'])
   def route(request_route):
    if request_route.request.url.startswith(origin+'/'):request_route.continue_()
    else:nonloopback.append('NONLOOPBACK_DENIED');request_route.abort()
   ctx.route('**/*',route)
   page=ctx.new_page();page.on('pageerror',lambda error:errors.append(type(error).__name__))
   page.goto(origin);page.get_by_label('Код розблокування').fill(application.state.auth.code)
   page.get_by_role('button',name='Відкрити щоденник',exact=True).click()
   expect(page.get_by_role('button',name='Щоденник',exact=True)).to_be_visible();checks['journal_landing']=True
   assert 'Synthetic demo' not in page.inner_text('body')
   for name in ('Практики','Health Connect'):assert page.get_by_role('button',name=name,exact=True).count()==0
   page.get_by_role('button',name='Розмова',exact=True).click()
   page.locator('.private-pilot-controls summary').click()
   expect(page.get_by_role('button',name='Увімкнути AI для цієї сесії')).to_be_disabled()
   controls=page.locator('.private-pilot-controls')
   for box in controls.locator('fieldset').first.locator('input[type=checkbox]').all():box.check()
   page.get_by_role('button',name='Увімкнути AI для цієї сесії').click()
   expect(controls.locator('select')).to_be_visible();checks['owner_ack_and_default_off']=True
   controls.locator('select').select_option('DEEP_ECONOMICAL')
   expect(controls.locator('select')).to_have_value('DEEP_ECONOMICAL')
   controls.locator('select').select_option('DEEP_QUALITY');checks['explicit_deep_profiles']=True
   for box in controls.locator('fieldset input[type=checkbox]').all():box.check()
   page.get_by_role('button',name='Увімкнути локальний голос').click()
   expect(controls.locator('summary')).to_contain_text('голос увімкнено');controls.locator('summary').click()
   page.get_by_role('button',name='Записати голосом',exact=True).click()
   # Existing VoicePanel requires its own explicit microphone action.
   mic=page.get_by_role('button',name='Увімкнути мікрофон',exact=True)
   if mic.count():mic.click()
   start=page.get_by_role('button',name='Почати голосовий запис',exact=True)
   if start.count():start.click()
   expect(page.get_by_role('button',name='Зупинити й зберегти аудіо')).to_be_visible(timeout=10000)
   page.wait_for_timeout(5000);page.get_by_role('button',name='Зупинити й зберегти аудіо').click()
   recognize=page.get_by_role('button',name='Розпізнати локально',exact=True)
   expect(recognize).to_be_enabled(timeout=15000);recognize.click()
   expect(page.get_by_role('button',name='Вставити текст у розмову')).to_be_visible(timeout=120000)
   assert sum(len(adapter.calls) for adapter in providers)==0
   transcript=page.locator('.voice-panel textarea').last
   if not transcript.count():transcript=page.get_by_role('dialog').get_by_role('textbox').last
   transcript.fill('ORIGINAL SYNTHETIC · Перевірений та відредагований текст для паперового саду.')
   page.get_by_role('button',name='Вставити текст у розмову').click()
   checks['microphone_native_asr_review_edit_no_auto_send']=engine.executions>0
   # Close existing voice sheet before explicit preview/send.
   dialog=page.get_by_role('dialog')
   if dialog.count():page.keyboard.press('Escape')
   page.locator('.private-journal-selection summary').click()
   page.get_by_role('button',name='Вибрати записи щоденника').click()
   selected_label=page.locator('.private-journal-selection label').filter(has_text='explicitly selected browser journal')
   expect(selected_label).to_be_visible();selected_label.get_by_role('checkbox').check()
   page.locator('.private-journal-selection summary').click()
   approved_preview=[]
   def capture_preview(response):
    if response.url.endswith('/private-context/preview') and response.status==200:approved_preview.append(response.json())
   page.on('response',capture_preview)
   page.get_by_role('button',name='Переглянути перед надсиланням').click()
   expect(page.get_by_role('heading',name='Підтвердити текст для OpenAI')).to_be_visible()
   assert sum(len(adapter.calls) for adapter in providers)==0
   expect(page.get_by_role('dialog')).to_contain_text('ORIGINAL SYNTHETIC')
   page.screenshot(path=str(a.output/'PRIVATE_CONTEXT_PREVIEW.png'),full_page=True)
   page.get_by_role('button',name='Підтверджую · надіслати цей текст до AI').click()
   expect(page.locator('.conversation-messages')).to_contain_text('Який невеликий крок',timeout=15000)
   assert sum(len(adapter.calls) for adapter in providers)==1
   payload=next(adapter.calls[0] for adapter in providers if adapter.calls)
   assert payload['synthetic'] is False and 'audio_hash' not in encode(payload) and 'VOICE_TRANSCRIPT' not in encode(payload)
   assert approved_preview and approved_preview[-1]['context']==payload['context']
   assert approved_preview[-1]['reflection_state']==payload['reflection_state']
   assert [part['kind'] for part in payload['context']][-2:]==['CURRENT_TURN','JOURNAL_SELECTED']
   assert 'UNSELECTED_BROWSER_JOURNAL_SENTINEL' not in encode(payload)
   exact=digest(encode({'context':payload['context'],'reflection_state':payload['reflection_state']}).encode())
   assert approved_preview[-1]['context_hash']==exact
   checks['R01_exact_ordered_preview_provider_context_reflection_hash']=True
   checks['explicit_preview_send_text_only']=True
   for width,height,name in [(1440,1000,'PRIVATE_DESKTOP.png'),(390,844,'PRIVATE_NARROW.png')]:
    page.set_viewport_size({'width':width,'height':height});page.locator('.conversation-messages').evaluate('(el)=>{el.scrollTop=el.scrollHeight}');page.screenshot(path=str(a.output/name),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
   checks['desktop_narrow_no_horizontal_overflow']=True
   assert not nonloopback and not errors
   checks['nonloopback_requests']=0;checks['page_errors']=0
   ctx.close();browser.close();browser=None
  result={'status':'PASS','scope':'PRIVATE_LOCAL_RUNTIME_WITH_ORIGINAL_SYNTHETIC_CONTENT','release_id':m['release_id'],'implementation':build,'source_fixture':a.source_fixture,'checks':checks,'provider':'OFFLINE_ORIGINAL_SYNTHETIC_FIXTURE_NOT_LIVE_ENTITLEMENT','native_local_asr':engine.metadata(),'live_provider_attempts':0,'real_private_data_used':0,'real_human_voice_used':0,'system_changes':0}
  (a.output/'BROWSER.json').write_text(json.dumps(result,indent=2)+'\n');print('M8D synthetic Chromium/native local-ASR checks PASS')
 finally:
  if browser:
   try:browser.close()
   except Exception:pass
  if server:server.should_exit=True
  if thread:thread.join(5)
  shutil.rmtree(work)

if __name__=='__main__':main()
