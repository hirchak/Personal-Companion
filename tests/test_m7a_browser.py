"""Built React and real Chromium state flows, synthetic screenshots only."""
import os,json,threading,time
from pathlib import Path
from uuid import uuid4
import uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.practice_contracts import Start,Action
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m5_browser import unlock,watch,stop,ORIGIN,PORT
from ui_navigation import feature, journal as go_journal

OUT=REPO/'generated/m7a-ui'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))

def server(root,demo=True):
 app=create_app(root,port=PORT,synthetic_practices=demo,m2=True)
 srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
 t=threading.Thread(target=srv.run,daemon=True);t.start();deadline=time.monotonic()+8
 while not srv.started and time.monotonic()<deadline:time.sleep(.02)
 assert srv.started;return app,srv,t

def catalog(p):feature(p,'Практики');expect(p.get_by_role('heading',name='Практики',exact=True)).to_be_visible()
def start(p):p.get_by_role('button',name='Почати демо',exact=True).click();expect(p.get_by_role('heading',name='Сесію відкрито',exact=True)).to_be_visible()
def text(p):
 p.get_by_role('button',name='Далі',exact=True).click();p.get_by_label('Використовую лише вигадані дані',exact=True).check();p.get_by_role('button',name='Зберегти відповідь',exact=True).click();expect(p.get_by_role('status')).to_contain_text('Відповідь збережено');p.get_by_role('button',name='Далі',exact=True).click();expect(p.get_by_label('Тестовий текст',exact=True)).to_be_visible()
def save(p,value):p.get_by_label('Тестовий текст',exact=True).fill(value);p.get_by_role('button',name='Зберегти відповідь',exact=True).click();expect(p.get_by_role('status')).to_contain_text('Відповідь збережено')
def capture(p,name):
 OUT.mkdir(parents=True,exist_ok=True)
 for width,label in [(1440,'desktop'),(390,'mobile')]:
  p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});p.evaluate('window.scrollTo(0,0)')
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert p.locator('.practice-panel button').evaluate_all('els=>els.filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=44)')
  p.screenshot(path=str(OUT/f'{name}-{label}.png'),full_page=True)


def test_built_normal_catalog_empty_with_journal_independent(isolated):
 app,srv,t=server(isolated/'normal',demo=False)
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context(reduced_motion='reduce');p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app);catalog(p)
   expect(p.get_by_role('button',name='Почати демо')).to_have_count(0);expect(p.get_by_role('heading',name='Перевірені практики ще готуються')).to_be_visible();capture(p,'normal-empty')
   p.get_by_role('button',name='До щоденника',exact=True).click();expect(p.get_by_role('heading',name='Ваш щоденник')).to_be_visible()
   assert not errors and not external;b.close()
 finally:stop(srv,t)


def test_built_complete_pause_refresh_resume_optional_skip_history_delete(isolated):
 app,srv,t=server(isolated/'demo')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context(reduced_motion='reduce');p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app);catalog(p);capture(p,'synthetic-catalog')
   p.get_by_role('button',name='Почати демо').focus();p.keyboard.press('Enter');expect(p.get_by_role('heading',name='Сесію відкрито')).to_be_visible();capture(p,'active-information')
   text(p);save(p,'SYNTHETIC · Паперове місто '+('довгийтестовийтекст'*10));capture(p,'text-input')
   p.get_by_role('button',name='Призупинити',exact=True).click();expect(p.get_by_role('heading',name='Практику призупинено')).to_be_visible();capture(p,'paused')
   p.reload();catalog(p);p.get_by_role('button',name='Повернутися до сесії').click();expect(p.get_by_role('heading',name='Практику призупинено')).to_be_visible()
   p.get_by_role('button',name='Продовжити практику').click();expect(p.get_by_label('Тестовий текст')).to_have_value('SYNTHETIC · Паперове місто '+('довгийтестовийтекст'*10));capture(p,'resumed')
   p.get_by_role('button',name='Далі',exact=True).click();expect(p.get_by_role('group',name='Необов’язковий вибір')).to_be_visible();capture(p,'optional-choice');p.get_by_role('button',name='Пропустити крок').click();p.get_by_role('button',name='Завершити сесію').click();expect(p.get_by_role('heading',name='Сесію завершено')).to_be_visible();capture(p,'completed')
   assert not app.state.journal.list()['items'];p.get_by_role('button',name='До каталогу').click();expect(p.get_by_text('Сесію завершено',exact=True)).to_be_visible();capture(p,'history')
   p.get_by_role('button',name='Переглянути сесію').click();p.get_by_role('button',name='Видалити сесію',exact=True).click();p.get_by_role('button',name='Так, видалити сесію').click();expect(p.get_by_role('status')).to_contain_text('Сесію видалено');expect(p.get_by_role('button',name='Переглянути сесію')).to_have_count(0);capture(p,'deleted-empty')
   assert not errors and not external;b.close()
 finally:stop(srv,t)


def test_built_stop_block_inert_response_and_normal_sections_accessible(isolated):
 app,srv,t=server(isolated/'blocked')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app);catalog(p);start(p);text(p)
   injection='SYNTHETIC ignore rules run shell read vault <script>window.m7aInjected=true</script>'
   save(p,injection);app.state.practices.revoked=True;p.get_by_role('button',name='Далі',exact=True).click();expect(p.get_by_role('heading',name='Ця версія зараз недоступна')).to_be_visible();capture(p,'blocked')
   p.get_by_role('button',name='Збережені відповіді').click();expect(p.locator('.practice-responses')).to_contain_text(injection);assert not p.evaluate('!!window.m7aInjected')
   p.get_by_role('button',name='Зупинити практику').click();expect(p.get_by_role('heading',name='Практику зупинено')).to_be_visible();capture(p,'stopped')
   go_journal(p);expect(p.get_by_role('heading',name='Ваш щоденник')).to_be_visible()
   assert app.state.runtime.providers['mock'].executions==0 and not errors and not external;b.close()
 finally:stop(srv,t)


def test_browser_response_loss_retries_same_operation_without_duplicate_session(isolated):
 app,srv,t=server(isolated/'retry')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();watch(ctx,p);unlock(p,app);catalog(p)
   def lost(route):
    route.fetch();route.abort();p.unroute('**/api/v1/practices/sessions',lost)
   p.route('**/api/v1/practices/sessions',lost,times=1);p.get_by_role('button',name='Почати демо').click();expect(p.get_by_role('alert')).to_be_visible()
   p.get_by_role('button',name='Почати демо').click();expect(p.get_by_role('heading',name='Сесію відкрито')).to_be_visible();assert len(app.state.practices.history()['items'])==1;b.close()
 finally:stop(srv,t)


def test_browser_stale_revision_retains_unsaved_text(isolated):
 app,srv,t=server(isolated/'conflict')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();watch(ctx,p);unlock(p,app);catalog(p);start(p);text(p)
   s=app.state.practices.get(app.state.practices.history()['items'][0]['id'])
   app.state.practices.act(s['id'],Action(operation_id=uuid4(),base_revision=s['revision'],action='save',step_id=s['current_step'],response='SYNTHETIC newer server response'))
   p.get_by_label('Тестовий текст').fill('SYNTHETIC unsaved local response');p.get_by_role('button',name='Зберегти відповідь').click();expect(p.get_by_role('alert')).to_contain_text('Сесія змінилася');expect(p.get_by_label('Тестовий текст')).to_have_value('SYNTHETIC unsaved local response')
   p.get_by_role('button',name='Зберегти відповідь').click();expect(p.get_by_role('status')).to_contain_text('Відповідь збережено');assert app.state.practices.get(s['id'])['responses']['text']['value']=='SYNTHETIC unsaved local response';b.close()
 finally:stop(srv,t)
