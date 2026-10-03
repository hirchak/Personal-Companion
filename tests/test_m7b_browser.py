"""Built synthetic conversation UI. Generated audio only, no private recordings."""
import os,threading,time
from pathlib import Path
import uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.storage import REPO
from apps.core.models import Create
from uuid import uuid4
from test_m1_domain import isolated
OUT=REPO/'generated/m7b-ui';PORT=8774;ORIGIN=f'http://127.0.0.1:{PORT}'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))

def server(root,demo=True):
 app=create_app(root,port=PORT,synthetic_conversations=demo,synthetic_practices=demo)
 srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'));t=threading.Thread(target=srv.run,daemon=True);t.start();deadline=time.monotonic()+8
 while not srv.started and time.monotonic()<deadline:time.sleep(.02)
 assert srv.started;return app,srv,t

def unlock(p,app):
 p.goto(ORIGIN);p.get_by_label('Код розблокування').fill(app.state.auth.code);p.get_by_role('button',name='Відкрити щоденник').click();expect(p.get_by_role('heading',name='Про що хочеться поговорити?')).to_be_visible()
def stop(srv,t):srv.should_exit=True;t.join(8);assert not t.is_alive()
def capture(p,name):
 OUT.mkdir(parents=True,exist_ok=True)
 for width,label in [(1440,'desktop'),(390,'mobile')]:
  p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});p.evaluate('window.scrollTo(0,0)')
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  if p.locator('.conversation-composer').count():
   p.wait_for_function('() => document.querySelector(".conversation-composer").getBoundingClientRect().bottom<=visualViewport.height+1',timeout=3000)
  p.screenshot(path=str(OUT/f'{name}-{label}.png'),full_page=True)

def test_conversation_text_home_history_journal_and_practice(isolated):
 app,srv,t=server(isolated/'home')
 for kind in ['inbox','daily','sleep']:
  app.state.journal.write('create',uuid4(),Create(operation_id=uuid4(),entry_id=uuid4(),base_revision=0,payload={'type':kind,'raw_text':'SYNTHETIC · Тестова нотатка '+kind}))
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context(reduced_motion='reduce');p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));unlock(p,app);capture(p,'empty-conversation')
   assert p.get_by_role('navigation',name='Основна навігація').get_by_role('button').count()==3
   p.get_by_label('Повідомлення',exact=True).fill('SYNTHETIC · Тестовий рядок');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1);expect(p.get_by_label('Демо-відповідь помічника')).to_have_count(1)
   p.get_by_label('Повідомлення',exact=True).fill('SYNTHETIC · Другий рядок');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(2);capture(p,'multi-turn')
   p.reload();expect(p.get_by_label('Ваше повідомлення')).to_have_count(2)
   p.get_by_role('button',name='Розмови',exact=True).click();expect(p.get_by_role('dialog',name='Розмови')).to_be_visible();capture(p,'conversation-history');p.get_by_role('button',name='Закрити: Розмови').click()
   p.get_by_role('button',name='Практики',exact=True).last.click();expect(p.get_by_role('heading',name='Практики',exact=True)).to_be_visible();expect(p.get_by_role('button',name='Почати демо',exact=True)).to_be_visible();capture(p,'practice-entry')
   p.get_by_role('button',name='Щоденник',exact=True).click();expect(p.get_by_role('heading',name='Ваш щоденник')).to_be_visible();capture(p,'journal-tiles')
   p.get_by_role('button',name='Список',exact=True).click();capture(p,'journal-list');p.reload();p.get_by_role('button',name='Щоденник',exact=True).click();expect(p.get_by_role('button',name='Список',exact=True)).to_have_attribute('aria-pressed','true')
   p.get_by_role('button',name='День',exact=True).click();expect(p.locator('.journal-card')).to_have_count(1)
   p.get_by_role('button',name='Відкрити запис: День').click();expect(p.get_by_role('dialog',name='Запис',exact=True)).to_be_visible();capture(p,'journal-detail');p.get_by_role('button',name='Закрити: Запис').click()
   p.get_by_role('button',name='Більше',exact=True).click();capture(p,'simplified-menu');p.get_by_role('button',name='Налаштування',exact=True).click();capture(p,'settings-connections')
   assert not errors;b.close()
 finally:stop(srv,t)


def test_voice_composer_generated_audio_unavailable_and_explicit_demo_insert(isolated):
 from test_m4_browser import context
 from test_m4_voice import wav
 app,srv,t=server(isolated/'voice');file=isolated/'generated-tone.wav';file.write_bytes(wav(8))
 try:
  with sync_playwright() as pw:
   ctx=context(pw,isolated/'profile',file);p=ctx.pages[0];p.set_default_timeout(8000);errors=[];external=[];p.on('pageerror',lambda e:errors.append(str(e)));ctx.on('request',lambda r:external.append(r.url) if not r.url.startswith(ORIGIN+'/') else None);unlock(p,app)
   capture(p,'mic-idle');p.get_by_role('button',name='Записати голосом',exact=True).click();expect(p.get_by_text('Записуємо ·',exact=False)).to_be_visible();capture(p,'recording')
   p.wait_for_timeout(800);p.get_by_role('button',name='Зупинити й зберегти аудіо').click();expect(p.locator('.voice-item')).to_have_count(1)
   p.get_by_role('button',name='Розпізнати локально').click();expect(p.get_by_role('alert')).to_contain_text('Локальна модель ще не встановлена');capture(p,'asr-unavailable')
   p.get_by_text('Локальне розпізнавання',exact=True).click();p.get_by_label('Використати synthetic fake ASR').check();p.get_by_role('button',name='Розпізнати локально').click();expect(p.get_by_label('Перевірити та виправити транскрипт')).to_be_visible()
   p.get_by_label('Перевірити та виправити транскрипт').fill('SYNTHETIC · Перевірений текст для composer');p.get_by_role('button',name='Вставити текст у розмову').click();expect(p.get_by_role('dialog',name='Голосовий ввід')).to_have_count(0)
   expect(p.get_by_label('Повідомлення',exact=True)).to_have_value('SYNTHETIC · Перевірений текст для composer');assert not app.state.conversations.list()['items'] and not app.state.journal.list()['items']
   p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1)
   stored=app.state.conversations.get(app.state.conversations.list()['items'][0]['id']);assert stored['messages'][0]['source_reference']['kind']=='VOICE_TRANSCRIPT';assert not errors and not external;ctx.close()
 finally:stop(srv,t)


def test_normal_home_off_fake_transcript_hidden_and_mic_cancel(isolated):
 from test_m4_browser import context
 from test_m4_voice import wav
 app,srv,t=server(isolated/'off',demo=False);file=isolated/'tone.wav';file.write_bytes(wav(5))
 try:
  with sync_playwright() as pw:
   ctx=context(pw,isolated/'profile-off',file,390);p=ctx.pages[0];unlock(p,app);expect(p.get_by_text('Помічник поки недоступний.',exact=False)).to_be_visible();capture(p,'normal-off')
   p.get_by_label('Повідомлення',exact=True).fill('SYNTHETIC · Локальний запис без AI');p.get_by_role('button',name='Зберегти у розмові').click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1);assert p.get_by_label('Демо-відповідь помічника').count()==0
   p.get_by_role('button',name='Записати голосом',exact=True).click();expect(p.get_by_text('Записуємо ·',exact=False)).to_be_visible();p.get_by_role('button',name='Скасувати запис',exact=True).click();expect(p.get_by_text('Незбережений запис відкинуто.')).to_be_visible();assert not app.state.voice.list()['items']
   p.get_by_text('Локальне розпізнавання',exact=True).click();assert p.get_by_label('Використати synthetic fake ASR').count()==0
   ctx.close()
 finally:stop(srv,t)


def test_deep_goal_context_ux_exact_revision_history_and_budget(isolated):
 app,srv,t=server(isolated/'deep-ux')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();unlock(p,app)
   p.get_by_role('button',name='Цілі',exact=True).click();expect(p.get_by_role('dialog',name='Цілі')).to_be_visible();p.get_by_label('Текст цілі',exact=True).fill('SYNTHETIC paper city');p.get_by_label('Це моя погоджена ціль').check();p.get_by_role('button',name='Створити ціль').click();expect(p.get_by_role('button',name='Почати глибоку розмову')).to_be_enabled();p.get_by_role('button',name='Закрити: Цілі').click()
   p.get_by_label('Повідомлення',exact=True).fill('SYNTHETIC paper city in a free conversation');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1)
   p.get_by_role('button',name='Цілі',exact=True).click();p.get_by_role('button',name='Почати глибоку розмову').click();expect(p.get_by_role('heading',name='Глибока розмова')).to_be_visible();expect(p.get_by_label('Глибока розмова',exact=True)).to_contain_text('SYNTHETIC paper city');capture(p,'deep-goal')
   p.get_by_text('Минулий контекст',exact=True).click();p.get_by_role('button',name='Підготувати демо-контекст').click();expect(p.get_by_text('Вибрано джерел:',exact=False)).to_be_visible();capture(p,'deep-context');p.set_viewport_size({'width':390,'height':540});p.wait_for_function('() => document.querySelector(".conversation-composer").getBoundingClientRect().bottom<=visualViewport.height+1',timeout=3000);p.set_viewport_size({'width':390,'height':844})
   p.get_by_role('button',name='Цілі',exact=True).click();p.get_by_role('button',name='Редагувати ціль').click();p.get_by_label('Текст цілі',exact=True).fill('SYNTHETIC revised paper city');p.get_by_label('Це моя погоджена ціль').check();p.get_by_role('button',name='Зберегти нову редакцію').click();p.get_by_role('button',name='Історія цілі').click();expect(p.get_by_label('Історія цілі')).to_contain_text('SYNTHETIC paper city');capture(p,'goal-history')
   p.get_by_role('button',name='Закрити: Цілі').click();assert app.state.conversations.list()['items'][0]['goal_binding']['revision']==1
   ctx.close();b.close()
 finally:stop(srv,t)


def test_response_loss_retry_and_stale_preserve_draft(isolated):
 from apps.core.conversation_contracts import SendMessage
 app,srv,t=server(isolated/'lost-response')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();unlock(p,app)
   def lost(route):
    route.fetch();route.abort()
   p.route('**/conversations/*/messages',lost,times=1)
   p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC lost response');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_role('alert')).to_be_visible()
   expect(p.get_by_label('Повідомлення',exact=True)).to_have_value('ORIGINAL SYNTHETIC lost response')
   p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1)
   c=app.state.conversations.list()['items'][0];app.state.conversations.send(c['id'],SendMessage(operation_id=uuid4(),base_revision=c['revision'],text='ORIGINAL SYNTHETIC second writer'))
   p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC stale retained draft');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_role('alert')).to_be_visible();expect(p.get_by_label('Повідомлення',exact=True)).to_have_value('ORIGINAL SYNTHETIC stale retained draft')
   expect(p.get_by_label('Ваше повідомлення')).to_have_count(2)
   p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(3);b.close()
 finally:stop(srv,t)


def test_journal_grid_list_bounded_render_metrics(isolated):
 import json
 app,srv,t=server(isolated/'ui-metrics')
 for _ in range(50):
  id=uuid4();app.state.journal.write('create',id,Create(operation_id=uuid4(),entry_id=id,base_revision=0,payload={'raw_text':'ORIGINAL SYNTHETIC paper note'}))
 metrics={'provenance':'ORIGINAL_SYNTHETIC','unit':'milliseconds','limit':'Headless local Chromium render, not physical phone/virtual keyboard','viewports':[]}
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();unlock(p,app)
   for width in (1440,390):
    p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});start=time.perf_counter();p.get_by_role('button',name='Щоденник',exact=True).click();expect(p.locator('.journal-card')).to_have_count(30);grid=(time.perf_counter()-start)*1000
    start=time.perf_counter();p.get_by_role('button',name='Список',exact=True).click();expect(p.get_by_role('button',name='Список',exact=True)).to_have_attribute('aria-pressed','true');lst=(time.perf_counter()-start)*1000
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
    metrics['viewports'].append({'width':width,'grid_ms':round(grid,3),'list_switch_ms':round(lst,3),'cards_first_page':30,'total_synthetic_records':50})
    p.get_by_role('button',name='Плитки',exact=True).click();p.get_by_role('button',name='Розмова',exact=True).click()
   OUT.mkdir(parents=True,exist_ok=True);(OUT/'RENDER_METRICS.json').write_text(json.dumps(metrics,indent=2));b.close()
 finally:stop(srv,t)
