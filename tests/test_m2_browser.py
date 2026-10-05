"""SYNTHETIC built PWA + SW + IndexedDB + real Mac API/SQLite, two isolated browsers."""
import os,time,threading,json
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse
import pytest,uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.storage import REPO
from test_m1_domain import isolated

PORT=8768
ORIGIN=f'http://127.0.0.1:{PORT}'
PASSWORD='SYNTHETIC browser fixture unlock passphrase'

def server(root):
    app=create_app(root,port=PORT,m2=True)
    srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    thread=threading.Thread(target=srv.run,daemon=True);thread.start()
    deadline=time.monotonic()+8
    while not srv.started and time.monotonic()<deadline:time.sleep(.02)
    assert srv.started
    return app,srv,thread

def stop(srv,thread):srv.should_exit=True;thread.join(8);assert not thread.is_alive()

def unlock_phone(page):
    page.get_by_label('Локальний пароль').fill(PASSWORD)
    button=page.get_by_role('button',name='Створити encrypted сховище')
    if button.count():button.click()
    else:page.get_by_role('button',name='Розблокувати телефон',exact=True).click()
    expect(page.get_by_role('heading',name='Розмова',exact=True)).to_be_visible()
    page.get_by_role('button',name='Щоденник',exact=True).click()
    expect(page.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible()

def capture(page,text):
    page.get_by_role('button',name='Додати запис').click()
    page.get_by_label('Текст',exact=True).fill(text)
    page.get_by_role('button',name='Зберегти на телефоні',exact=True).click()
    expect(page.locator('.entry').filter(has_text=text)).to_have_count(1)

def pair(page,app,label):
    from apps.core.sync import Pair
    page.get_by_role('button',name='Налаштування телефону').click()
    page.get_by_label('Одноразове запрошення Mac').fill(app.state.sync.invite()['invitation'])
    page.get_by_label('Назва synthetic пристрою').fill(label)
    page.get_by_role('button',name='З’єднати з Mac',exact=True).click()
    expect(page.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible(timeout=10000)
    page.get_by_role('button',name='Налаштування телефону').click()


def test_M2_A01_A02_A03_A04_A07_A09_offline_sync_conflict_and_storage(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app,srv,thread=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        profiles=[isolated/'phone-a',isolated/'phone-b']; contexts=[]
        for profile in profiles:
            context=pw.chromium.launch_persistent_context(str(profile),headless=True,viewport={'width':390,'height':844},accept_downloads=True)
            contexts.append(context)
        a=contexts[0].pages[0];b=contexts[1].pages[0]
        errors=[];a.on('pageerror',lambda e:errors.append(str(e)));b.on('pageerror',lambda e:errors.append(str(e)))
        for page in (a,b):page.set_default_timeout(6000);page.goto(ORIGIN+'/phone/');unlock_phone(page);page.wait_for_function('navigator.serviceWorker.controller!==null')
        text='SYNTHETIC · offline paper note 🦉'
        contexts[0].set_offline(True)
        capture(a,text)
        a.get_by_role('button',name='Редагувати',exact=True).click();a.get_by_label('Текст',exact=True).fill(text+' edited');a.get_by_role('button',name='Зберегти на телефоні',exact=True).click()
        expect(a.get_by_text('Збережено на телефоні · Очікує Mac',exact=True).first).to_be_visible()
        a.reload();unlock_phone(a)
        expect(a.locator('.entry-text')).to_have_text(text+' edited')
        # Restart persistent browser, including IndexedDB and service worker, while Mac unreachable.
        contexts[0].close();contexts[0]=pw.chromium.launch_persistent_context(str(profiles[0]),headless=True,viewport={'width':390,'height':844},accept_downloads=True)
        contexts[0].set_offline(True);a=contexts[0].pages[0];a.set_default_timeout(6000);a.goto(ORIGIN+'/phone/');unlock_phone(a)
        expect(a.locator('.entry-text')).to_have_text(text+' edited')
        assert a.evaluate('localStorage.length+sessionStorage.length')==0
        persisted=a.evaluate("""async () => { const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('personal-companion-synthetic-phone');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject()}); const rows=await new Promise(resolve=>{const r=db.transaction('vault').objectStore('vault').getAll();r.onsuccess=()=>resolve(r.result)});db.close();return JSON.stringify(rows)}""")
        assert text not in persisted and PASSWORD not in persisted
        contexts[0].set_offline(False)
        pair(a,app,'SYNTHETIC A')
        assert len(app.state.journal.list()['items'])==1
        assert app.state.journal.list()['items'][0]['revision']==2
        pair(b,app,'SYNTHETIC B')
        expect(b.locator('.entry-text')).to_have_text(text+' edited')
        # Concurrent offline variants on identical base revision.
        contexts[0].set_offline(True);contexts[1].set_offline(True)
        for page,variant in [(a,'SYNTHETIC A variant'),(b,'SYNTHETIC B variant')]:
            page.get_by_role('button',name='Редагувати',exact=True).click();page.get_by_label('Текст',exact=True).fill(variant);page.get_by_role('button',name='Зберегти на телефоні',exact=True).click()
        contexts[0].set_offline(False);a.get_by_role('button',name='Синхронізувати з Mac',exact=True).click()
        expect(a.locator('.entry .metadata').first).to_contain_text('На Mac')
        contexts[1].set_offline(False);b.get_by_role('button',name='Синхронізувати з Mac',exact=True).click()
        expect(b.get_by_role('heading',name='Дві версії — потрібен ваш вибір')).to_be_visible()
        expect(b.locator('.conflict')).to_contain_text('SYNTHETIC A variant')
        b.get_by_label('Об’єднаний текст').fill('SYNTHETIC explicit merged')
        b.get_by_role('button',name='Зберегти об’єднаний текст',exact=True).click();b.get_by_role('button',name='Синхронізувати з Mac',exact=True).click()
        expect(b.locator('.entry .metadata').first).to_contain_text('На Mac')
        assert app.state.journal.list()['items'][0]['raw_text']=='SYNTHETIC explicit merged'
        # Dropped response after genuine commit: retry same operation, no duplicate.
        contexts[0].set_offline(True);capture(a,'SYNTHETIC dropped response')
        dropped=[False]
        def route(r):
            if r.request.method=='POST' and not dropped[0]:
                dropped[0]=True;r.fetch();r.abort()
            else:r.continue_()
        contexts[0].route('**/api/v1/device/operations',route)
        contexts[0].set_offline(False);a.get_by_role('button',name='Синхронізувати з Mac',exact=True).click()
        expect(a.get_by_role('alert')).to_be_visible()
        contexts[0].unroute('**/api/v1/device/operations',route)
        a.get_by_role('button',name='Синхронізувати з Mac',exact=True).click()
        expect(a.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible()
        assert len(app.state.journal.list(q='dropped response')['items'])==1
        # Synthetic quota failure keeps the unlocked draft and never gives local save.
        contexts[0].set_offline(True);a.get_by_role('button',name='Додати запис').click();a.get_by_label('Текст',exact=True).fill('SYNTHETIC quota draft')
        a.evaluate("() => {window.syntheticOriginalPut=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(){throw new DOMException('SYNTHETIC quota','QuotaExceededError')};return true;}")
        a.get_by_role('button',name='Зберегти на телефоні',exact=True).click();expect(a.get_by_role('alert')).to_be_visible();expect(a.get_by_label('Текст',exact=True)).to_have_value('SYNTHETIC quota draft')
        a.evaluate('IDBObjectStore.prototype.put=window.syntheticOriginalPut;delete window.syntheticOriginalPut')
        a.get_by_role('button',name='Зберегти на телефоні',exact=True).click();expect(a.locator('.entry').filter(has_text='SYNTHETIC quota draft')).to_have_count(1)
        a.get_by_role('button',name='Налаштування телефону').click()
        with a.expect_download() as download:a.get_by_role('button',name='Encrypted recovery для unsynced',exact=True).click()
        recovery=Path(download.value.path()).read_text();assert 'SYNTHETIC quota draft' not in recovery and PASSWORD not in recovery
        a.get_by_role('button',name='Налаштування телефону').click()
        a.get_by_role('button',name='Більше',exact=True).click();a.get_by_role('button',name='Заблокувати телефон',exact=True).click();expect(a.get_by_label('Локальний пароль')).to_be_visible();assert 'SYNTHETIC quota draft' not in a.locator('body').inner_text()
        # Mac delete wins over stale offline edit; local variant remains explicit conflict.
        entry=app.state.journal.list(q='explicit merged')['items'][0]
        from apps.core.models import Delete
        app.state.journal.write('delete',entry['id'],Delete(operation_id=uuid4(),base_revision=entry['revision']))
        contexts[1].set_offline(True);b.locator('.entry').filter(has_text='SYNTHETIC explicit merged').get_by_role('button',name='Редагувати',exact=True).click();b.get_by_label('Текст',exact=True).fill('SYNTHETIC stale deleted');b.get_by_role('button',name='Зберегти на телефоні',exact=True).click()
        contexts[1].set_offline(False);b.get_by_role('button',name='Синхронізувати з Mac',exact=True).click();expect(b.locator('.conflict')).to_contain_text('Mac видалив цей ID')
        assert not app.state.journal.list(q='stale deleted')['items']
        assert not errors
        for c in contexts:c.close()
    finally:
        if thread.is_alive():stop(srv,thread)


def test_M2_A08_waiting_worker_interrupted_update_preserves_outbox(isolated):
    import shutil
    web=isolated/'web';shutil.copytree(REPO/'apps/web/dist',web)
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app=create_app(isolated/'update-mac',port=PORT,m2=True,web=web)
    srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    thread=threading.Thread(target=srv.run,daemon=True);thread.start()
    deadline=time.monotonic()+8
    while not srv.started and time.monotonic()<deadline:time.sleep(.02)
    assert srv.started
    try:
      with sync_playwright() as pw:
        context=pw.chromium.launch_persistent_context(str(isolated/'update-phone'),headless=True,viewport={'width':390,'height':844})
        page=context.pages[0];page.goto(ORIGIN+'/phone/');unlock_phone(page);page.wait_for_function('navigator.serviceWorker.controller!==null')
        context.set_offline(True);capture(page,'SYNTHETIC pending before shell update');context.set_offline(False)
        sw=web/'phone/sw.js';original=sw.read_text()
        interrupted=original.replace('pc-phone-shell-','pc-phone-shell-interrupted-').replace("self.addEventListener('install'", "FILES.push('/phone/missing-install-asset');self.addEventListener('install'")
        sw.write_text(interrupted)
        page.evaluate("async()=>{const r=await navigator.serviceWorker.getRegistration('/phone/');try{await r.update()}catch{}}")
        page.wait_for_timeout(700)
        page.reload();unlock_phone(page);expect(page.locator('.entry-text')).to_have_text('SYNTHETIC pending before shell update')
        sw.write_text(original.replace('pc-phone-shell-','pc-phone-shell-next-'))
        page.evaluate("async()=>{const r=await navigator.serviceWorker.getRegistration('/phone/');await r.update()}")
        expect(page.get_by_role('button',name='Оновити PWA')).to_be_visible(timeout=10000)
        page.on('dialog',lambda d:d.accept());page.get_by_role('button',name='Оновити PWA').click()
        expect(page.get_by_label('Локальний пароль')).to_be_visible(timeout=10000);unlock_phone(page)
        expect(page.locator('.entry-text')).to_have_text('SYNTHETIC pending before shell update')
        expect(page.get_by_text('1 очікують',exact=True)).to_be_visible()
        cached=page.evaluate("async()=>{const urls=[];for(const name of await caches.keys())for(const r of await(await caches.open(name)).keys())urls.push(new URL(r.url).pathname);return urls}")
        assert not any(p.startswith('/api/') for p in cached)
        context.close()
    finally:
        if thread.is_alive():stop(srv,thread)


def test_M2_A10_browser_epoch_mismatch_requires_explicit_repair(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app,srv,thread=server(isolated/'epoch-mac')
    try:
      with sync_playwright() as pw:
        context=pw.chromium.launch_persistent_context(str(isolated/'epoch-phone'),headless=True)
        page=context.pages[0];page.goto(ORIGIN+'/phone/');unlock_phone(page);pair(page,app,'SYNTHETIC epoch device')
        context.set_offline(True);capture(page,'SYNTHETIC old epoch unsynced')
        app.state.sync.rotate()
        context.set_offline(False)
        expect(page.get_by_role('heading',name='Потрібне явне узгодження')).to_be_visible()
        assert not app.state.journal.list()['items']
        page.get_by_role('button',name='Налаштування телефону').click()
        page.get_by_label('Одноразове запрошення Mac').fill(app.state.sync.invite()['invitation'])
        page.get_by_role('button',name='З’єднати з Mac',exact=True).click()
        expect(page.get_by_text('Pairing збережено encrypted.',exact=True)).to_be_visible()
        assert not app.state.journal.list()['items']
        page.on('dialog',lambda d:d.accept());page.get_by_role('button',name='Зберегти локальні новими копіями').click()
        page.get_by_role('button',name='Синхронізувати з Mac',exact=True).click()
        expect(page.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible()
        assert len(app.state.journal.list()['items'])==1
        context.close()
    finally:
        if thread.is_alive():stop(srv,thread)


def test_M2_synthetic_https_manifest_and_worker_gate(isolated):
    import subprocess
    tls=isolated/'tls';tls.mkdir(mode=0o700);cert,key=tls/'test-cert.pem',tls/'test-key.pem'
    result=subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1,DNS:localhost','-keyout',str(key),'-out',str(cert)],capture_output=True)
    assert result.returncode==0
    os.chmod(cert,0o600);os.chmod(key,0o600)
    app=create_app(isolated/'https-mac',port=PORT,m2=True,scheme='https')
    srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,ssl_keyfile=str(key),ssl_certfile=str(cert),access_log=False,log_level='critical'))
    thread=threading.Thread(target=srv.run,daemon=True);thread.start()
    deadline=time.monotonic()+8
    while not srv.started and time.monotonic()<deadline:time.sleep(.02)
    assert srv.started
    try:
      os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
      with sync_playwright() as pw:
        # Ephemeral test-only certificate exception, not installed OS/browser trust.
        browser=pw.chromium.launch(headless=True,args=['--ignore-certificate-errors'])
        context=browser.new_context(ignore_https_errors=True,viewport={'width':390,'height':844})
        page=context.new_page();page.goto(f'https://127.0.0.1:{PORT}/phone/');unlock_phone(page)
        page.wait_for_function('navigator.serviceWorker.controller!==null')
        cdp=context.new_cdp_session(page);manifest=cdp.send('Page.getAppManifest')
        assert not manifest['errors']
        parsed=json.loads(manifest['data']);assert parsed['display']=='standalone' and parsed['start_url']=='/phone/' and len(parsed['icons'])==2
        capture(page,'SYNTHETIC HTTPS loopback note')
        context.set_offline(True);page.reload();unlock_phone(page)
        expect(page.locator('.entry-text')).to_have_text('SYNTHETIC HTTPS loopback note')
        browser.close()
    finally:
        if thread.is_alive():stop(srv,thread)


def test_M2_A09_evicted_store_and_offline_delete_restart(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app,srv,thread=server(isolated/'eviction-mac')
    try:
      with sync_playwright() as pw:
        context=pw.chromium.launch_persistent_context(str(isolated/'eviction-phone'),headless=True)
        page=context.pages[0];page.goto(ORIGIN+'/phone/');unlock_phone(page);page.wait_for_function('navigator.serviceWorker.controller!==null')
        context.set_offline(True);capture(page,'SYNTHETIC local delete fixture')
        page.on('dialog',lambda d:d.accept());page.get_by_role('button',name='Видалити',exact=True).click();expect(page.locator('.entry')).to_have_count(0)
        page.reload();unlock_phone(page);expect(page.locator('.entry')).to_have_count(0);expect(page.get_by_text('2 очікують',exact=True)).to_be_visible()
        page.get_by_role('button',name='Більше',exact=True).click();page.get_by_role('button',name='Заблокувати телефон').click()
        page.evaluate("async()=>new Promise((resolve,reject)=>{const r=indexedDB.deleteDatabase('personal-companion-synthetic-phone');r.onsuccess=()=>resolve(true);r.onerror=()=>reject();})")
        page.reload();expect(page.get_by_text('Локальне сховище порожнє:',exact=False)).to_be_visible();expect(page.get_by_label('Відкрити encrypted recovery')).to_be_visible()
        context.close()
    finally:
        if thread.is_alive():stop(srv,thread)
