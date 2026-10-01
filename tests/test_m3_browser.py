"""Built Ukrainian React against actual HTTP/SQLite, synthetic only, no external egress."""
import os
import time
import threading
from uuid import uuid4
import pytest,uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.models import Create
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m2_browser import unlock_phone, capture
from test_m3_runtime import Controlled

PORT=8769
ORIGIN=f'http://127.0.0.1:{PORT}'

def serve(root):
    app=create_app(root,port=PORT,m2=True)
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    deadline=time.monotonic()+8
    while not server.started and time.monotonic()<deadline:time.sleep(.02)
    assert server.started
    return app,server,thread

def unlock(page,app):
    page.goto(ORIGIN+'/');page.get_by_label('Код розблокування').fill(app.state.auth.code);page.get_by_role('button',name='Відкрити щоденник').click()
    expect(page.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible()

def propose(page,task):
    page.get_by_label('Завдання',exact=True).select_option(task)
    page.get_by_role('button',name='Переглянути точний контекст').click()
    expect(page.get_by_role('heading',name='Що отримає provider')).to_be_visible()
    page.get_by_role('button',name='Погодити цей контекст і створити завдання').click()


def test_M3_browser_consent_suggestions_memory_and_viewports(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app,server,thread=serve(isolated/'browser-runtime')
    id=str(uuid4());raw='SYNTHETIC · План паперового саду 🦉'
    app.state.journal.write('create',id,Create(operation_id=uuid4(),entry_id=id,base_revision=0,payload={'raw_text':raw}))
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];external=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        context.on('request',lambda r:external.append(r.url) if not r.url.startswith(ORIGIN+'/') else None)
        page.set_default_timeout(7000);unlock(page,app)
        expect(page.get_by_text('AI вимкнено · записи зберігаються незалежно')).to_be_visible()
        page.get_by_role('button',name='Помічник і пам’ять',exact=True).click()
        expect(page.get_by_role('heading',name='Що система пам’ятає')).to_be_visible()
        page.get_by_label('Додати власне налаштування').fill('SYNTHETIC · Показувати коротко')
        page.get_by_role('button',name='Зберегти пам’ять',exact=True).click();expect(page.locator('.memory-row')).to_have_count(1)
        assert app.state.runtime.providers['mock'].executions==0
        page.get_by_label('Вибрати',exact=True).check();page.get_by_label('Увімкнути локальний synthetic mock').check()
        page.get_by_label('SYNTHETIC · Показувати коротко',exact=True).check()
        page.get_by_role('button',name='Переглянути точний контекст').click()
        preview=page.get_by_role('region',name='Точний контекст');expect(preview).to_contain_text(raw);expect(preview).to_contain_text(id);expect(preview).to_contain_text('кількість provider tokens невідома')
        assert app.state.runtime.providers['mock'].executions==0
        page.get_by_role('button',name='Відкликати згоду').click();expect(preview).to_have_count(0)
        propose(page,'capture_classify');expect(page.locator('.suggestion-row')).to_have_count(1)
        page.get_by_role('button',name='Редагувати пропозицію').click();page.get_by_label('Розділ пропозиції').select_option('daily')
        page.get_by_role('group',name='Теги пропозиції').get_by_label('план',exact=True).check()
        page.get_by_role('button',name='Прийняти виправлену структуру').click();expect(page.locator('.entry .metadata')).to_contain_text('День')
        assert app.state.journal.get(id)['raw_text']==raw
        page.get_by_role('button',name='Повернути попередню структуру').click();expect(page.locator('.entry .metadata')).to_contain_text('Думки')
        propose(page,'organize_selected');expect(page.locator('.suggestion-row')).to_have_count(2)
        page.locator('.suggestion-row').first.get_by_role('button',name='Прийняти пропозицію',exact=True).click()
        propose(page,'memory_propose');expect(page.locator('.memory-row')).to_have_count(2)
        model=page.locator('.memory-row').filter(has_text='Пропозиція mock — ще не підтверджена')
        expect(model).to_be_visible();model.get_by_role('button',name='Підтвердити пам’ять').click()
        expect(page.get_by_role('button',name='Підтвердити пам’ять')).to_have_count(0)
        user=page.locator('.memory-row').filter(has_text='SYNTHETIC · Показувати коротко')
        user.get_by_role('button',name='Редагувати пам’ять').click();user.get_by_label('Виправити пам’ять').fill('SYNTHETIC · Показувати джерела')
        user.get_by_role('button',name='Зберегти виправлення').click();expect(page.locator('.memory-row')).to_contain_text(['SYNTHETIC · Показувати джерела','Показувати короткі відповіді.'])
        # Both viewports contain only allowed synthetic product UI, no owner credential/terminal.
        expect(page.get_by_role('region',name='Точний контекст')).to_have_count(0)
        out=REPO/'generated/m3-ui';out.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(out/'assistant-desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'assistant-mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.on('dialog',lambda d:d.accept());page.locator('.memory-row').first.get_by_role('button',name='Видалити пам’ять').click();expect(page.locator('.memory-row')).to_have_count(1)
        page.get_by_label('Увімкнути локальний synthetic mock').uncheck();expect(page.get_by_text('AI вимкнено · записи зберігаються незалежно')).to_be_visible()
        page.get_by_role('button',name='Заблокувати',exact=True).click();expect(page.get_by_label('Код розблокування')).to_be_visible();assert 'Показувати джерела' not in page.locator('body').inner_text()
        assert not errors and not external
        browser.close()
    finally:
      server.should_exit=True;thread.join(8);assert not thread.is_alive()


def test_M3_browser_job_cancel_and_phone_AI_independent_after_IDB_pair_failure(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app,server,thread=serve(isolated/'cancel-phone')
    id=str(uuid4());app.state.journal.write('create',id,Create(operation_id=uuid4(),entry_id=id,base_revision=0,payload={'raw_text':'SYNTHETIC cancellation note'}))
    provider=Controlled(block=True);app.state.runtime.providers['mock']=provider
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);owner=browser.new_context();page=owner.new_page();unlock(page,app)
        page.get_by_label('Вибрати',exact=True).check();page.get_by_role('button',name='Помічник і пам’ять',exact=True).click();page.get_by_label('Увімкнути локальний synthetic mock').check()
        propose(page,'capture_classify');expect(page.get_by_role('button',name='Скасувати завдання')).to_be_visible();page.get_by_role('button',name='Скасувати завдання').click();provider.release.set()
        expect(page.locator('.runtime-row')).to_contain_text('Скасовано');assert not app.state.runtime.suggestions()['items']
        app.state.runtime.set_mode('OFF')
        phone=browser.new_context(viewport={'width':390,'height':844});p=phone.new_page();p.goto(ORIGIN+'/phone/');unlock_phone(p)
        p.get_by_role('button',name='Налаштування телефону').click()
        invite=app.state.sync.invite()['invitation'];p.get_by_label('Одноразове запрошення Mac').fill(invite)
        # Real HTTP commits PENDING before actual browser IndexedDB put throws.
        p.evaluate("""() => { window.originalPut = IDBObjectStore.prototype.put; IDBObjectStore.prototype.put = function(){throw new DOMException('SYNTHETIC local write failure','QuotaExceededError');}; }""")
        p.get_by_role('button',name='З’єднати з Mac',exact=True).click();expect(p.get_by_role('alert')).to_be_visible()
        assert app.state.sync.devices()['items'][0]['state']=='PENDING'
        p.evaluate('IDBObjectStore.prototype.put = window.originalPut; delete window.originalPut')
        # New owner invite explicitly retries same device; old pending credential is replaced.
        p.get_by_label('Одноразове запрошення Mac').fill(app.state.sync.invite()['invitation'])
        p.get_by_role('button',name='З’єднати з Mac',exact=True).click();expect(p.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible()
        assert app.state.sync.devices()['items'][0]['state']=='ACTIVE'
        p.get_by_role('button',name='Налаштування телефону').click();phone.set_offline(True)
        capture(p,'SYNTHETIC phone capture with AI OFF');expect(p.get_by_text('Офлайн. Записи зберігаються на телефоні;',exact=False)).to_be_visible()
        phone.set_offline(False);expect(p.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible()
        deadline=time.monotonic()+5
        while len(app.state.journal.list()['items'])<2 and time.monotonic()<deadline:time.sleep(.03)
        assert len(app.state.journal.list()['items'])==2
        assert len(app.state.runtime.jobs()['items'])==1 and app.state.runtime.providers['mock'].executions==1
        browser.close()
    finally:
      provider.release.set();server.should_exit=True;thread.join(8);assert not thread.is_alive()


def test_M3_mobile_long_memory_pending_confirmation_wraps(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app,server,thread=serve(isolated/'long-mobile')
    from apps.core.ai_contracts import MemoryCreate
    content='SYNTHETIC · Показувати короткі відповіді та джерела для вибраних записів. '*5
    app.state.runtime.create_memory(MemoryCreate(content=content))
    id=str(uuid4());app.state.journal.write('create',id,Create(operation_id=uuid4(),entry_id=id,base_revision=0,payload={'raw_text':'SYNTHETIC · довга пам’ять і pending proposal'}))
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();unlock(page,app)
        page.get_by_label('Вибрати',exact=True).check();page.get_by_role('button',name='Помічник і пам’ять',exact=True).click();page.get_by_label('Увімкнути локальний synthetic mock').check()
        propose(page,'capture_classify');expect(page.get_by_role('button',name='Прийняти пропозицію',exact=True)).to_be_visible()
        labels=page.locator('.assistant-content label.check');assert labels.count()>=3
        assert labels.evaluate_all("els => els.every(e => getComputedStyle(e).whiteSpace === 'normal' && e.getBoundingClientRect().height >= 44)")
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        out=REPO/'generated/m3-ui';out.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out/'assistant-mobile-pending.png'),full_page=True)
        expect(page.locator('footer')).to_contain_text('Зовнішній AI вимкнено · цей demo використовує лише вигадані записи.')
        browser.close()
    finally:
      server.should_exit=True;thread.join(8);assert not thread.is_alive()
