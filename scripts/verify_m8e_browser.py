"""M8E real Chromium/native ASR, ORIGINAL SYNTHETIC disposable PRIVATE_LOCAL only.
Provider is deterministic fixture; no owner vault, native inference or physical phone.
"""
import argparse,json,os,shutil,socket,subprocess,tempfile,threading,time
from pathlib import Path
from uuid import uuid4
import uvicorn
from playwright.sync_api import sync_playwright,expect
from scripts.verify_m8d_browser import source_package,FixtureProvider
from apps.core import release as r,local_private as p
from apps.core.storage import REPO,encode,digest,SafeError
from apps.core.root_types import RootKind
from apps.core.api import create_app
from apps.core.whisper_local_asr import WhisperLocalASR

class DelayedASR:
 def __init__(self):self.engine=WhisperLocalASR(REPO/'generated/local-asr',private_scope=True)
 def metadata(self):return self.engine.metadata()
 def transcribe(self,*args):time.sleep(1.5);return self.engine.transcribe(*args)

class BrowserFixtureProvider(FixtureProvider):
 def __init__(self,model,effort,state):super().__init__(model,effort);self.readiness_state=state
 def readiness(self):
  if self.readiness_state['failure_code']:raise SafeError(self.readiness_state['failure_code'],503)
  if self.readiness_state['blocked']:raise SafeError('EXISTING_CHATGPT_AUTH_REQUIRED',403)
  return super().readiness()

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-fixture',action='store_true');parser.add_argument('--package',type=Path);parser.add_argument('--output',type=Path,default=REPO/'generated/m8e-browser');a=parser.parse_args()
 if bool(a.package)==bool(a.source_fixture):raise ValueError('Exactly one source required')
 a.output.mkdir(parents=True,exist_ok=True)
 work=Path(tempfile.mkdtemp(prefix='m8e-original-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
 server=None;thread=None;providers=[];checks={};errors=[];external=[];readiness_state={'blocked':False,'failure_code':None}
 try:
  if a.source_fixture:package,m=source_package(work);build='DEVELOPMENT'
  else:package=a.package;m=r.read_json(package/'release-manifest.json');r.validate_package(package,m['manifest_hash']);build=m['git_commit']
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  app_root,data,backup=work/'app',work/'PRIVATE_LOCAL_ORIGINAL_SYNTHETIC',work/'backups';backup.mkdir(mode=0o700)
  assert p.preflight(package,m['manifest_hash'],app_root,data,backup,port)['status']=='PASS'
  r.initialize_private(package,m['manifest_hash'],app_root,data,backup,'INITIALIZE_PRIVATE_LOCAL:'+str(data),p.CONSENT,True,port=port)
  wav=work/'ORIGINAL_SYNTHETIC.wav';aiff=work/'ORIGINAL_SYNTHETIC.aiff';asr_available={'value':True}
  subprocess.run(['/usr/bin/say','-v','Lesya','-o',str(aiff),'Це оригінальний синтетичний тест. Сьогодні я малюю паперовий сад.'],check=True,capture_output=True)
  subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@16000','-c','1',str(aiff),str(wav)],check=True,capture_output=True)
  engine=DelayedASR()
  def asr_factory():
   if not asr_available['value']:raise SafeError('LOCAL_ASR_ASSET_UNAVAILABLE',503)
   return engine
  def factory(mode,model,effort):
   adapter=BrowserFixtureProvider(model,effort,readiness_state);providers.append(adapter);return adapter
  app=create_app(data,port=port,web=package/'apps/web/dist',root_kind=RootKind.PRIVATE_LOCAL,release_identity=build,m8d_private=True,private_provider_factory=factory,private_asr_factory=asr_factory,conversation_timeout=120)
  from apps.core.models import Create
  selected_id=uuid4();app.state.journal.write('create',selected_id,Create(operation_id=uuid4(),entry_id=selected_id,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC selected garden note'}))
  hidden_id=uuid4();app.state.journal.write('create',hidden_id,Create(operation_id=uuid4(),entry_id=hidden_id,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC UNSELECTED_SENTINEL'}))
  server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,access_log=False,log_level='critical'));thread=threading.Thread(target=server.run,daemon=True);thread.start()
  for _ in range(100):
   if server.started:break
   time.sleep(.05)
  assert server.started
  os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'));origin=f'http://127.0.0.1:{port}'
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+str(wav)])
   ctx=browser.new_context(viewport={'width':1440,'height':960},permissions=['microphone'])
   def route(rt):
    if rt.request.url.startswith(origin+'/'):rt.continue_()
    else:external.append('DENIED_NONLOOPBACK');rt.abort()
   ctx.route('**/*',route);page=ctx.new_page();page.on('pageerror',lambda _:errors.append('PAGE_ERROR'))
   def shot(name):
    page.screenshot(path=str(a.output/(name+'.png')))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),name
   def unlock():
    page.get_by_label('Код розблокування').fill(app.state.auth.code);page.get_by_role('button',name='Відкрити Особистий простір',exact=True).click();expect(page.get_by_role('heading',name='Розмова',exact=True)).to_be_visible()
   page.goto(origin);unlock();shot('desktop-empty');checks['conversation_landing']=True
   page.get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('dialog',name='Приватність розмови')).to_be_visible();assert page.locator('dialog input[type=checkbox]').count()==0
   assert page.get_by_role('dialog').get_by_role('button',name='Увімкнути AI',exact=True).count()==1
   assert page.get_by_role('dialog').get_by_text('Зовнішні налаштування',exact=False).count()==0
   readiness_state['blocked']=True
   page.get_by_role('dialog').get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('dialog')).to_have_count(0)
   expect(page.get_by_role('alert')).to_contain_text('Перевірте вхід у Codex')
   expect(page.get_by_role('alert')).to_contain_text('EXISTING_CHATGPT_AUTH_REQUIRED')
   assert '/private/' not in page.get_by_role('alert').inner_text() and 'ORIGINAL_SYNTHETIC_ACCOUNT_SENTINEL' not in page.get_by_role('alert').inner_text()
   readiness_state['blocked']=False
   page.get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Luna · High');assert page.get_by_role('dialog').count()==0;checks['single_sheet_consent_and_retry_no_repeat']=True
   page.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC Мій паперовий сад починається з одного аркуша.')
   page.get_by_role('button',name='Надіслати',exact=True).click();expect(page.get_by_label('Відповідь помічника',exact=True)).to_have_count(1);assert page.get_by_role('dialog').count()==0
   payload=next(p.calls[-1] for p in providers if p.calls);assert len(payload['context'])==1 and 'UNSELECTED_SENTINEL' not in encode(payload);checks['normal_send_no_modal_exact']=True;shot('desktop-active')
   page.get_by_role('button',name='Додати контекст щоденника',exact=True).click();expect(page.get_by_role('dialog',name='Додати записи до розмови')).to_be_visible();page.get_by_label('ORIGINAL SYNTHETIC selected garden note',exact=True).check();page.get_by_role('button',name='Готово',exact=True).click()
   page.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC Додаю вибрану нотатку до цього повідомлення.');page.get_by_role('button',name='Надіслати',exact=True).click();expect(page.get_by_role('dialog',name='Додати 1 записів щоденника?')).to_be_visible()
   from apps.core.models import Patch
   app.state.journal.write('edit',selected_id,Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'ORIGINAL SYNTHETIC revised selected garden note'}))
   page.get_by_role('button',name='Підтвердити й надіслати',exact=True).click();expect(page.get_by_role('dialog').get_by_role('alert')).to_contain_text('Вибраний запис змінився');assert sum(len(p.calls) for p in providers)==1
   page.get_by_role('button',name='Оновити вибрані записи',exact=True).click();expect(page.get_by_role('dialog',name='Додати записи до розмови')).to_be_visible();expect(page.get_by_label('ORIGINAL SYNTHETIC revised selected garden note',exact=True)).to_be_checked();page.get_by_role('button',name='Готово',exact=True).click();page.get_by_role('button',name='Надіслати',exact=True).click();page.get_by_role('button',name='Підтвердити й надіслати',exact=True).click();expect(page.get_by_label('Відповідь помічника',exact=True)).to_have_count(2);checks['stale_journal_visible_fresh_approval']=True
   payload=next(p.calls[-1] for p in providers if p.calls);assert payload['context'][-1]['kind']=='JOURNAL_SELECTED' and 'UNSELECTED_SENTINEL' not in encode(payload);checks['journal_expansion_explicit_exact']=True
   page.get_by_role('button',name='Вимкнути AI',exact=True).click();expect(page.get_by_role('button',name='Увімкнути AI',exact=True)).to_be_visible();assert page.get_by_role('dialog').count()==0;checks['ai_on_to_off_one_click']=True
   page.get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Luna · High');assert page.get_by_role('dialog').count()==0;checks['ai_off_to_on_existing_consent_one_click']=True
   page.get_by_role('button',name='Вимкнути AI',exact=True).click();readiness_state['failure_code']='PROVIDER_CAPABILITY_MISSING';page.get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('LOCAL_SERVICE_UNAVAILABLE');assert 'PROVIDER_CAPABILITY_MISSING' not in page.get_by_role('alert').inner_text();checks['unknown_backend_code_suppressed']=True
   readiness_state['failure_code']=None;page.get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Luna · High');assert page.get_by_role('dialog').count()==0
   page.get_by_role('button',name='Розмови',exact=True).click();expect(page.locator('.conversation-history li')).to_have_count(1);shot('desktop-history');expect(page.get_by_text('Звичайна',exact=True).last).to_be_visible();page.get_by_role('button',name='Закрити: Розмови',exact=True).click()
   page.get_by_role('button',name='Нова розмова',exact=True).click();expect(page.get_by_label('Ваше повідомлення',exact=True)).to_have_count(0)
   page.set_viewport_size({'width':390,'height':844});shot('mobile-empty')
   nav=page.get_by_role('navigation',name='Основна навігація');assert nav.bounding_box()['y']>700;checks['mobile_bottom_nav']=True
   page.get_by_role('button',name='Вимкнути AI',exact=True).click();expect(page.get_by_role('button',name='Увімкнути AI',exact=True)).to_be_visible()
   asr_available['value']=False
   page.get_by_role('button',name='Записати голосом',exact=True).click();expect(page.locator('[data-voice-state=RECORDING]')).to_be_visible();shot('mobile-recording');page.get_by_role('button',name='Скасувати',exact=True).click();assert not app.state.voice.list()['items'];checks['cancel_no_audio']=True
   page.get_by_role('button',name='Записати голосом',exact=True).click();expect(page.locator('[data-voice-state=RECORDING]')).to_be_visible();page.wait_for_timeout(4000);page.get_by_role('button',name='Завершити',exact=True).click();expect(page.locator('[data-voice-state=WAITING_FOR_LOCAL_ASR]')).to_be_visible();expect(page.get_by_text('Локальне розпізнавання недоступне',exact=False)).to_be_visible();assert len(app.state.voice.list()['items'])==1;checks['record_preserved_when_local_asr_unavailable']=True
   asr_available['value']=True
   page.get_by_role('button',name='Записати голосом',exact=True).click();expect(page.locator('[data-voice-state=RECORDING]')).to_be_visible();page.wait_for_timeout(4000);page.get_by_role('button',name='Завершити',exact=True).click();expect(page.locator('[data-voice-state=TRANSCRIBING]')).to_be_visible();shot('mobile-transcribing')
   expect(page.get_by_label('Повідомлення',exact=True)).not_to_have_value('',timeout=90000);expect(page.get_by_role('button',name='Зберегти у розмові',exact=True)).to_be_enabled();assert len(app.state.voice.list()['items'])==2 and app.state.conversations.list()['items'] and sum(len(p.calls) for p in providers)==2
   assert page.get_by_label('Відповідь помічника',exact=True).count()==0
   checks['native_local_asr_draft_with_ai_off_no_auto_send']=True
   page.get_by_role('button',name='Увімкнути AI',exact=True).click();expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Luna · High');assert page.get_by_role('dialog').count()==0
   expect(page.get_by_role('button',name='Надіслати',exact=True)).to_be_enabled()
   page.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC Перевірений голосовий текст про паперовий сад.');page.get_by_role('button',name='Надіслати',exact=True).click();expect(page.get_by_label('Відповідь помічника',exact=True)).to_have_count(1);shot('mobile-active')
   latest=next(p.calls[-1] for p in providers if p.calls);serialized=encode(latest);assert all(v not in serialized for v in ('audio_hash','VOICE_TRANSCRIPT','TRANSCRIPT_READY','audio/wav'));checks['raw_audio_never_provider']=True
   page.set_viewport_size({'width':390,'height':540});page.wait_for_function('() => document.querySelector(".conversation-composer").getBoundingClientRect().bottom<=innerHeight-62+1');checks['resized_viewport_composer']=True;page.set_viewport_size({'width':390,'height':844})
   page.reload();expect(page.get_by_label('Ваше повідомлення',exact=True)).to_have_count(1);expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Luna · High');checks['reload_resume_consent']=True
   page.get_by_role('button',name='Глибока',exact=True).click();expect(page.get_by_role('dialog',name='Глибока розмова · оберіть мету')).to_be_visible();page.get_by_label('Текст цілі',exact=True).fill('ORIGINAL SYNTHETIC Завершити ескіз паперового саду');page.get_by_label('Це моя погоджена ціль').check();page.get_by_role('button',name='Створити ціль',exact=True).click();page.get_by_role('button',name='Почати глибоку розмову',exact=True).click();expect(page.get_by_role('dialog',name='Сфера глибокої розмови')).to_be_visible();page.get_by_role('button',name='Погоджую сферу сесії').click();expect(page.get_by_role('dialog',name='Сфера глибокої розмови')).to_have_count(0);shot('mobile-deep');checks['deep_goal_scope']=True
   page.get_by_label('Модель глибокої розмови').select_option('DEEP_ECONOMICAL');expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Deep · Luna Max');page.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC Почну з маленького ескізу.');page.get_by_role('button',name='Надіслати',exact=True).click();expect(page.get_by_label('Відповідь помічника',exact=True)).to_have_count(1);assert any(p.effort=='max' and p.calls for p in providers);checks['explicit_deep_luna_max']=True
   page.get_by_label('Модель глибокої розмови').select_option('DEEP_QUALITY');expect(page.get_by_role('button',name='Вимкнути AI',exact=True)).to_have_text('Deep · Sol 6.1 High');page.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC Оберу один простий контур.');page.get_by_role('button',name='Надіслати',exact=True).click();expect(page.get_by_label('Відповідь помічника',exact=True)).to_have_count(2);assert any(p.model=='gpt-6.1-sol' and p.effort=='high' and p.calls for p in providers);checks['explicit_deep_sol_high']=True
   page.get_by_role('button',name='Розмови',exact=True).click();shot('mobile-history');page.get_by_role('button',name='Закрити: Розмови',exact=True).click()
   page.get_by_role('button',name='Більше',exact=True).click();page.get_by_role('button',name='AI & Privacy · Налаштування',exact=True).click();expect(page.get_by_text('Зовнішні налаштування OpenAI/Codex',exact=False)).to_be_visible();shot('mobile-settings');page.set_viewport_size({'width':1440,'height':960});shot('desktop-settings')
   page.get_by_role('button',name='Відкликати згоду',exact=True).click();expect(page.get_by_text('Локальної згоди ще немає',exact=False)).to_be_visible();checks['revoke']=True
   page.get_by_role('button',name='Розмова',exact=True).click();expect(page.get_by_label('Відповідь помічника',exact=True)).to_have_count(2);expect(page.get_by_role('button',name='Увімкнути AI',exact=True)).to_be_visible();checks['historical_assistant_visible_ai_off']=True
   page.get_by_role('button',name='Більше',exact=True).click();expect(page.get_by_role('button',name='Голосові записи',exact=True)).to_be_visible();page.get_by_role('button',name='Голосові записи',exact=True).click();expect(page.get_by_role('heading',name='Голосові записи',exact=True)).to_be_visible();expect(page.locator('.voice-history-item')).to_have_count(2);expect(page.get_by_role('button',name='Повторити розпізнавання',exact=True)).to_be_visible();checks['voice_history_recovery_available']=True
   ctx.close();browser.close()
  assert not errors and not external
  result={'provenance':'ORIGINAL_SYNTHETIC_ONLY','build':build,'checks':checks,'page_errors':len(errors),'nonloopback_requests':len(external),'live_provider_calls':0,'physical_phone':'NOT_RUN_NEEDS_TRANSPORT_GATE','human_ua':'PARTIAL_OWNER_PILOT_OPEN','native_asr':'SYNTHETIC_TTS_ONLY','real_vault_inspected':False}
  (a.output/'CHROMIUM.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 finally:
  if server:server.should_exit=True
  if thread:thread.join(5)
  shutil.rmtree(work)
if __name__=='__main__':main()
