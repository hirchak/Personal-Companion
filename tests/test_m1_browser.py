"""SYNTHETIC real browser + built React + real HTTP + temporary SQLite."""
import os
import time
import threading
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse
import pytest
import uvicorn
from playwright.sync_api import sync_playwright, expect
from apps.core.api import create_app
from apps.core.storage import REPO
from test_m1_domain import isolated

PORT=8766
ORIGIN=f'http://127.0.0.1:{PORT}'

def start(root):
    app=create_app(root,port=PORT)
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    thread=threading.Thread(target=server.run,daemon=True); thread.start()
    deadline=time.monotonic()+10
    while not server.started and time.monotonic()<deadline:
        time.sleep(.02)
    assert server.started
    return app,server,thread

def stop(server,thread):
    server.should_exit=True; thread.join(timeout=10); assert not thread.is_alive()


def test_A09_browser_end_to_end(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(REPO/'generated/chromium'))
    app,server,thread=start(isolated/'browser')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
            requests,errors,external=[],[],[]
            def route(r):
                parsed=urlparse(r.request.url)
                if parsed.hostname!='127.0.0.1': external.append(r.request.url); r.abort()
                else: requests.append((r.request.method,parsed.path)); r.continue_()
            context.route('**/*',route)
            page=context.new_page(); page.set_default_timeout(5000); page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('console',lambda msg: errors.append(msg.text) if msg.type=='error' and 'Failed to load resource' not in msg.text else None)
            page.clock.install()
            page.goto(ORIGIN); expect(page.get_by_role('heading',name='Місце для ваших думок.')).to_be_visible()
            page.get_by_label('Код розблокування').fill(app.state.auth.code)
            page.get_by_role('button',name='Відкрити щоденник').click()
            expect(page.get_by_role('heading',name='Ваш щоденник')).to_be_visible()
            expect(page.get_by_text('Почніть із кількох слів')).to_be_visible()
            raw='SYNTHETIC · Сад із паперу 🦉 <script>window.injected=1</script>'
            page.get_by_role('button',name='Додати запис').click()
            expect(page.get_by_label('Текст',exact=True)).to_be_focused()
            page.get_by_label('Текст',exact=True).fill(raw)
            page.get_by_label('Розділ',exact=True).select_option('daily')
            page.get_by_label('Настрій',exact=True).fill('0')
            # Real storage failure must leave draft, without a success notice.
            app.state.store.fail_commit=True
            page.get_by_role('button',name='Зберегти на Mac').click()
            expect(page.get_by_role('alert')).to_be_visible()
            assert page.get_by_label('Текст',exact=True).input_value()==raw
            assert not app.state.journal.list()['items']
            app.state.store.fail_commit=False
            page.get_by_role('button',name='Зберегти на Mac').click()
            expect(page.get_by_text('Збережено на Mac',exact=True)).to_be_visible()
            expect(page.locator('.entry-text')).to_have_text(raw)
            assert page.evaluate('window.injected') is None
            assert page.evaluate('localStorage.length + sessionStorage.length')==0
            page.get_by_role('button',name='Редагувати',exact=True).click()
            page.get_by_label('Текст',exact=True).fill(raw+'\nSYNTHETIC зміна')
            page.get_by_role('button',name='Зберегти на Mac').click()
            expect(page.locator('.entry-text')).to_contain_text('SYNTHETIC зміна')
            page.get_by_role('button',name='Історія',exact=True).click()
            expect(page.locator('.history .entry-text')).to_have_text(raw)
            page.get_by_role('button',name='Закрити історію').click()
            page.get_by_label('Пошук',exact=True).fill('Сад')
            expect(page.locator('.entry')).to_have_count(1)
            page.get_by_label('Пошук',exact=True).fill('відсутня фраза')
            expect(page.get_by_text('Поки нічого не знайдено')).to_be_visible()
            page.get_by_label('Пошук',exact=True).fill('')
            expect(page.locator('.entry')).to_have_count(1)
            # Optimistic conflict from a real second API writer.
            page.get_by_role('button',name='Редагувати',exact=True).click()
            e=app.state.journal.list()['items'][0]
            from apps.core.models import Patch
            app.state.journal.write('edit',e['id'],Patch(operation_id=uuid4(),base_revision=e['revision'],changes={'tags':['SYNTHETIC']}))
            page.get_by_label('Текст',exact=True).fill('SYNTHETIC stale draft')
            page.get_by_role('button',name='Зберегти на Mac').click()
            expect(page.get_by_role('button',name='Завантажити актуальну версію')).to_be_visible()
            assert page.get_by_label('Текст',exact=True).input_value()=='SYNTHETIC stale draft'
            page.get_by_role('button',name='Завантажити актуальну версію').click()
            expect(page.get_by_label('Текст',exact=True)).to_have_value(raw+'\nSYNTHETIC зміна')
            page.get_by_label('Розділ',exact=True).select_option('creative')
            page.get_by_label('Вид ідеї',exact=True).select_option('scene')
            dialogs=[]
            def dialog(d): dialogs.append(d.message); d.accept()
            page.on('dialog',dialog)
            page.get_by_role('button',name='Зберегти на Mac').click()
            expect(page.locator('.entry .metadata').first).to_contain_text('Творчість')
            assert dialogs and 'Настрій' in dialogs[0]
            page.get_by_label('Вибрати',exact=True).check()
            page.get_by_label('Додати історію').check()
            page.get_by_role('button',name='Переглянути експорт').click()
            expect(page.get_by_text('Точний склад:',exact=False)).to_be_visible()
            with page.expect_download() as download:
                page.get_by_role('button',name='Завантажити JSON').click()
            from apps.core.domain import validate_portable
            content=validate_portable(Path(download.value.path()).read_text())
            assert len(content['entries'])==1 and len(content['revisions'])==3
            with page.expect_download() as download:
                page.get_by_role('button',name='Завантажити Markdown').click()
            assert '<script>' not in Path(download.value.path()).read_text()
            # Viewport captures contain only synthetic UI, never code/terminal/desktop.
            out=REPO/'generated/ui'; out.mkdir(parents=True,exist_ok=True)
            page.get_by_role('button',name='Скасувати експорт').click()
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(out/'desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/'mobile.png'),full_page=True)
            page.set_viewport_size({'width':1440,'height':1000})
            # Exact bootstrap cross-origin request is denied by real backend.
            evil=context.new_page()
            evil.route('http://127.0.0.1:8767/**',lambda r:r.fulfill(body='<html><body>synthetic cross-origin fixture</body></html>',content_type='text/html'))
            evil.goto('http://127.0.0.1:8767')
            denied=evil.evaluate("""async () => { try { const r=await fetch('http://127.0.0.1:8766/api/v1/auth/unlock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:'SYNTHETIC-invalid'})}); return r.status; } catch { return 'browser-denied'; } }""")
            assert denied=='browser-denied' or denied==403
            evil.close()
            # Restart invalidates sessions but preserves committed entries/history.
            stop(server,thread)
            app,server,thread=start(isolated/'browser')
            page.reload(); expect(page.get_by_label('Код розблокування')).to_be_visible()
            page.get_by_label('Код розблокування').fill(app.state.auth.code)
            page.get_by_role('button',name='Відкрити щоденник').click()
            expect(page.locator('.entry-text')).to_contain_text('SYNTHETIC зміна')
            page.get_by_role('button',name='Видалити',exact=True).click()
            expect(page.locator('.entry')).to_have_count(0)
            page.get_by_role('button',name='Додати запис').click()
            page.get_by_label('Текст',exact=True).fill('SYNTHETIC unsaved must disappear')
            page.get_by_role('button',name='Заблокувати').click()
            expect(page.get_by_label('Код розблокування')).to_be_visible()
            assert 'unsaved must disappear' not in page.locator('body').inner_text()
            page.reload(); expect(page.get_by_label('Код розблокування')).to_be_visible()
            # Browser idle expiry must unmount text, including unsaved draft.
            stop(server,thread)
            app,server,thread=start(isolated/'browser')
            page.reload(); page.get_by_label('Код розблокування').fill(app.state.auth.code)
            page.get_by_role('button',name='Відкрити щоденник').click()
            page.get_by_role('button',name='Додати запис').click()
            page.get_by_label('Текст',exact=True).fill('SYNTHETIC idle draft')
            page.clock.fast_forward(900001)
            expect(page.get_by_label('Код розблокування')).to_be_visible()
            assert 'idle draft' not in page.locator('body').inner_text()
            # Deliberate negative external attempt, blocked at the browser session boundary.
            probe=context.new_page()
            with pytest.raises(Exception): probe.goto('https://example.invalid',timeout=3000)
            assert len(external)==1
            assert not errors
            assert ('POST','/api/v1/entries') in requests and ('DELETE','/api/v1/entries/'+e['id']) in requests
            context.close(); browser.close()
    finally:
        if thread.is_alive(): stop(server,thread)
