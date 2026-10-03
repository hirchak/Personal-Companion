"""Built synthetic runtime UX; offline fixture clearly labeled, actual live checks separate."""
import os,time,threading
from pathlib import Path
from uuid import uuid4
import uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m7c_controller import FixtureProvider
PORT=8779;ORIGIN=f'http://127.0.0.1:{PORT}';OUT=REPO/'generated/m7c-ui'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
def serve(root,provider=True):
 app=create_app(root,port=PORT,synthetic_conversations=True,synthetic_practices=True,m7c_synthetic=True,conversation_provider=FixtureProvider() if provider else None)
 s=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'));t=threading.Thread(target=s.run,daemon=True);t.start();end=time.monotonic()+8
 while not s.started and time.monotonic()<end:time.sleep(.02)
 assert s.started;return app,s,t

def stop(s,t):s.should_exit=True;t.join(8);assert not t.is_alive()
def unlock(p,app):
 p.goto(ORIGIN);p.get_by_label('Код розблокування').fill(app.state.auth.code);p.get_by_role('button',name='Відкрити щоденник').click();expect(p.get_by_role('heading',name='Про що хочеться поговорити?')).to_be_visible()
def capture(p,name):
 OUT.mkdir(parents=True,exist_ok=True)
 for width,tag in [(1440,'desktop'),(390,'mobile')]:
  p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});p.evaluate('window.scrollTo(0,0)')
  if name=='closure-review':p.get_by_role('button',name='Зберегти свою думку').scroll_into_view_if_needed()
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  if p.locator('.conversation-composer').count():p.wait_for_function('() => document.querySelector(".conversation-composer").getBoundingClientRect().bottom<=visualViewport.height+1')
  p.screenshot(path=str(OUT/f'{name}-{tag}.png'),full_page=True)


def test_free_deep_closure_goal_history_and_diagnostics(isolated):
 app,s,t=serve(isolated/'browser')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);ctx=b.new_context(reduced_motion='reduce');p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));unlock(p,app);capture(p,'fixture-home')
   p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC paper garden');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Відповідь помічника',exact=True)).to_be_visible();capture(p,'free-response')
   p.get_by_role('button',name='Цілі',exact=True).click();p.get_by_label('Текст цілі',exact=True).fill('ORIGINAL SYNTHETIC · Дослідити початок паперового саду');p.get_by_label('Це моя погоджена ціль').check();p.get_by_role('button',name='Створити ціль').click();expect(p.get_by_role('button',name='Почати глибоку розмову')).to_be_enabled();p.get_by_role('button',name='Почати глибоку розмову').click();expect(p.get_by_role('heading',name='Глибока розмова')).to_be_visible()
   p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC · Вигаданий персонаж відкладає макет');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Відповідь помічника',exact=True)).to_be_visible();capture(p,'deep-response')
   p.get_by_role('button',name='Підсумувати',exact=True).click();expect(p.get_by_label('Кандидат підсумку')).to_be_visible();capture(p,'closure-review')
   assert app.state.reflection.list()['items'][0]['revision']==1 and not app.state.journal.list()['items']
   p.get_by_role('button',name='Зберегти свою думку').click();p.locator('input[name="journal-point"]').first.check();p.get_by_role('button',name='Переглянути запис').click();expect(p.get_by_label('Перегляд запису у щоденник')).to_be_visible();capture(p,'journal-point-preview')
   assert not app.state.journal.list()['items'];expect(p.get_by_role('button',name='Підтвердити запис у щоденник')).to_be_disabled();p.get_by_label('Я хочу додати саме цей текст у щоденник').check();p.get_by_role('button',name='Підтвердити запис у щоденник').click();expect(p.get_by_text('Вашу думку збережено у щоденник.')).to_be_visible();assert len(app.state.journal.list()['items'])==1;p.get_by_role('button',name='Закрити: Власна думка у щоденник').click()
   p.get_by_role('button',name='Завершити на сьогодні').click();expect(p.get_by_role('heading',name='Про що хочеться поговорити?')).to_be_visible();assert app.state.conversations.list(True)['items']
   assert not errors;b.close()
 finally:stop(s,t)


def test_goal_proposal_preview_requires_separate_agreement(isolated):
 app,s,t=serve(isolated/'proposal')
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);p=b.new_page();unlock(p,app);p.get_by_role('button',name='Цілі',exact=True).click();p.get_by_label('Текст цілі',exact=True).fill('ORIGINAL SYNTHETIC · Хочу зрозуміти початок паперового макета');p.get_by_role('button',name='Запропонувати формулювання').click();expect(p.get_by_role('button',name='Переглянути формулювання')).to_be_visible();capture(p,'goal-candidate');assert not app.state.reflection.list()['items']
   p.get_by_role('button',name='Переглянути формулювання').click();expect(p.get_by_label('Текст цілі',exact=True)).to_have_value('ORIGINAL SYNTHETIC agreed wording');expect(p.get_by_label('Це моя погоджена ціль')).not_to_be_checked();capture(p,'goal-preview');p.get_by_label('Це моя погоджена ціль').check();p.get_by_role('button',name='Створити ціль').click();expect(p.get_by_role('button',name='Почати глибоку розмову')).to_be_enabled();assert len(app.state.reflection.list()['items'])==1;b.close()
 finally:stop(s,t)


def test_off_and_cancel_retry_truth(isolated):
 app,s,t=serve(isolated/'off',provider=False)
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);p=b.new_page();unlock(p,app);capture(p,'provider-off');p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC off');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1);assert not app.state.conversation_controller.provider;b.close()
 finally:stop(s,t)
 app,s,t=serve(isolated/'cancel');provider=FixtureProvider('wait');app.state.conversation_controller.provider=provider
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);p=b.new_page();unlock(p,app);p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC queued response');p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_role('button',name='Скасувати відповідь')).to_be_visible();capture(p,'response-pending');p.get_by_role('button',name='Скасувати відповідь').click();expect(p.get_by_text('Запит скасовано. Незавершена відповідь не збережена.')).to_be_visible();capture(p,'response-cancelled');provider.release.set();p.wait_for_timeout(300);app.state.conversation_controller.provider=FixtureProvider();p.get_by_role('button',name='Повторити цей запит').click();expect(p.get_by_label('Відповідь помічника',exact=True)).to_be_visible();expect(p.get_by_label('Ваше повідомлення')).to_have_count(1);b.close()
 finally:stop(s,t)
