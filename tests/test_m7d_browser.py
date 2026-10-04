"""Real Chromium using offline ORIGINAL_SYNTHETIC fixtures; no provider quality claim."""
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m7c_browser import serve,stop,unlock
from test_m7d_deep import MapProvider
OUT=REPO/'generated/m7d-ui'

def test_working_map_focus_range_preview_confirm_reject_mobile_desktop(isolated):
 app,s,t=serve(isolated/'m7d-browser');app.state.conversation_controller.provider=MapProvider()
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True);p=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');errors=[];p.on('pageerror',lambda e:errors.append(str(e)));unlock(p,app)
   p.get_by_role('button',name='Цілі',exact=True).click();p.get_by_label('Текст цілі',exact=True).fill('ORIGINAL SYNTHETIC паперовий сад');p.get_by_label('Це моя погоджена ціль').check();p.get_by_role('button',name='Створити ціль').click();p.get_by_role('button',name='Почати глибоку розмову').click()
   p.get_by_text('Змінити фокус і контекст',exact=True).click();p.get_by_label('Фокус цієї сесії',exact=True).fill('ORIGINAL SYNTHETIC вчорашній початок');p.get_by_role('button',name='Зберегти фокус').click();expect(p.get_by_role('button',name='Зберегти фокус')).to_be_disabled()
   p.get_by_label('Контекст',exact=True).select_option('LAST_7_DAYS');p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC паперовий сад');p.get_by_role('button',name='Переглянути контекст перед відправленням').click();expect(p.get_by_role('dialog',name='Контекст цього повідомлення')).to_be_visible();p.get_by_role('button',name='Закрити: Контекст цього повідомлення').click();p.get_by_text('Змінити фокус і контекст',exact=True).click()
   p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_label('Відповідь помічника',exact=True)).to_be_visible();p.get_by_role('button',name='Карта сесії',exact=True).click();expect(p.get_by_role('button',name='Відхилити припущення')).to_be_visible();p.get_by_role('button',name='Відхилити припущення').click();expect(p.get_by_text('Припущення помічника · Відхилено вами',exact=True)).to_be_visible()
   p.get_by_role('button',name='Переглянути й підтвердити').click();p.get_by_label('Мій висновок').fill('ORIGINAL SYNTHETIC можу почати з чернетки');p.get_by_role('button',name='Підтвердити мій висновок').click();expect(p.get_by_text('Ви підтвердили · Актуально',exact=True)).to_be_visible()
   OUT.mkdir(parents=True,exist_ok=True)
   for width,height,tag in [(1440,1000,'desktop'),(390,844,'mobile')]:
    p.set_viewport_size({'width':width,'height':height});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.screenshot(path=str(OUT/('map-'+tag+'.png')),full_page=True)
   p.get_by_role('button',name='Закрити: Карта сесії').click();p.get_by_label('Повідомлення',exact=True).fill('ORIGINAL SYNTHETIC наступне питання');p.screenshot(path=str(OUT/'session-mobile.png'),full_page=True)
   with app.state.store.connect() as db:
    job=app.state.conversation_controller.row(db,db.execute('SELECT id FROM conversation_inferences').fetchone()[0]);assert job['request_metadata']['selection_type']=='LAST_7_DAYS' and job['request_metadata']['selected_receipt_id']
   assert not errors and not app.state.journal.list()['items'];b.close()
 finally:stop(s,t)
