"""Chromium offline queued voice on synthetic PWA; not physical Galaxy acceptance."""
import os
from playwright.sync_api import sync_playwright,expect
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m2_browser import server,stop,PASSWORD,ORIGIN
from test_m4_browser import context
from test_m4_voice import wav

def test_offline_composer_audio_encrypted_reload_no_transport(isolated):
 os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
 app,srv,thread=server(isolated/'ORIGINAL_SYNTHETIC_OFFLINE_MAC');file=isolated/'ORIGINAL_SYNTHETIC_TONE.wav';file.write_bytes(wav(6))
 try:
  with sync_playwright() as pw:
   ctx=context(pw,isolated/'ORIGINAL_SYNTHETIC_BROWSER',file,390);page=ctx.pages[0];requests=[];errors=[]
   page.on('pageerror',lambda _:errors.append('PAGE_ERROR'))
   ctx.on('request',lambda request:requests.append(request.url) if '/voice/' in request.url or not request.url.startswith(ORIGIN+'/') else None)
   page.goto(ORIGIN+'/phone/');page.get_by_label('Локальний пароль').fill(PASSWORD);page.get_by_role('button',name='Створити encrypted сховище',exact=True).click();expect(page.get_by_role('heading',name='Розмова',exact=True)).to_be_visible();page.wait_for_function('() => navigator.serviceWorker.controller!==null')
   ctx.set_offline(True);page.get_by_role('button',name='Записати голосом',exact=True).click();expect(page.locator('[data-voice-state=RECORDING]')).to_be_visible();page.wait_for_timeout(1800);page.get_by_role('button',name='Завершити',exact=True).click();expect(page.locator('[data-voice-state=WAITING_FOR_LOCAL_ASR]')).to_be_visible();expect(page.locator('.voice-history-item')).to_have_count(1)
   rows=page.evaluate('''async () => {const db=await new Promise(resolve=>{const r=indexedDB.open('personal-companion-synthetic-phone');r.onsuccess=()=>resolve(r.result)});const read=name=>new Promise(resolve=>{const r=db.transaction(name).objectStore(name).getAll();r.onsuccess=()=>resolve(r.result)});const value=JSON.stringify([await read('audio'),await read('audioChunks')]);db.close();return value;}''')
   assert 'audio/wav' not in rows and PASSWORD not in rows and 'LOCAL_AUDIO_SAVED' not in rows
   page.reload();page.get_by_label('Локальний пароль').fill(PASSWORD);page.get_by_role('button',name='Розблокувати телефон',exact=True).click();expect(page.locator('.voice-history-item')).to_have_count(1);expect(page.get_by_text('Очікує розпізнавання',exact=True)).to_be_visible()
   ctx.set_offline(False);page.wait_for_timeout(500);assert not requests and not errors and not app.state.voice.list()['items']
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.on('dialog',lambda d:d.accept());page.get_by_role('button',name='Видалити аудіо',exact=True).click();expect(page.locator('.voice-history-item')).to_have_count(0);ctx.close()
 finally:stop(srv,thread)
