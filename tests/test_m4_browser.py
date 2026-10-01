"""Built UI + real Chromium fake microphone, generated tone/silence WAV and temp profiles only."""
import os,threading,time,json
from pathlib import Path
import pytest,uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m4_voice import wav
from test_m2_browser import unlock_phone,pair

os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
PORT=8770;ORIGIN=f'http://127.0.0.1:{PORT}'
def server(root):
    app=create_app(root,port=PORT,m2=True)
    srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    t=threading.Thread(target=srv.run,daemon=True);t.start();deadline=time.monotonic()+8
    while not srv.started and time.monotonic()<deadline:time.sleep(.02)
    assert srv.started;return app,srv,t
def stop(srv,t):srv.should_exit=True;t.join(8);assert not t.is_alive()
def context(pw,profile,file,width=1440):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    return pw.chromium.launch_persistent_context(str(profile),headless=True,permissions=['microphone'],accept_downloads=True,
      args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream',f'--use-file-for-fake-audio-capture={file}'],viewport={'width':width,'height':1000 if width>500 else 844})
def mac_unlock(page,app):
    page.goto(ORIGIN+'/');page.get_by_label('Код розблокування').fill(app.state.auth.code);page.get_by_role('button',name='Відкрити щоденник').click()
    expect(page.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible()
    page.get_by_text('Голосовий запис',exact=True).click()
def record(page):
    page.get_by_role('button',name='Почати голосовий запис').click();expect(page.get_by_text('Записуємо ·',exact=False)).to_be_visible()
    page.wait_for_timeout(1400);page.get_by_role('button',name='Зупинити й зберегти аудіо').click()
def test_M4_browser_Mac_microphone_transcript_retention_and_accessibility(isolated):
    app,srv,t=server(isolated/'mac');file=isolated/'synthetic-tone.wav';file.write_bytes(wav(5))
    try:
      with sync_playwright() as pw:
        ctx=context(pw,isolated/'profile',file);p=ctx.pages[0];errors=[];external=[];p.on('pageerror',lambda e:errors.append(str(e)))
        ctx.on('request',lambda r:external.append(r.url) if not r.url.startswith(ORIGIN+'/') else None)
        p.set_default_timeout(7000);mac_unlock(p,app)
        p.get_by_role('button',name='Почати голосовий запис').focus();p.keyboard.press('Enter');expect(p.get_by_text('Записуємо ·',exact=False)).to_be_visible()
        p.wait_for_timeout(700);p.get_by_role('button',name='Пауза запису').click();expect(p.get_by_text('Пауза ·',exact=False)).to_be_visible()
        p.get_by_role('button',name='Продовжити запис').click();p.wait_for_timeout(800);p.get_by_role('button',name='Зупинити й зберегти аудіо').click()
        expect(p.locator('.voice-item')).to_have_count(1);expect(p.locator('.voice-item')).to_contain_text('Аудіо збережено на Mac')
        assert app.state.voice.list()['items'][0]['duration']>=.5 and not app.state.journal.list()['items']
        p.reload();p.get_by_text('Голосовий запис',exact=True).click();expect(p.locator('.voice-item')).to_have_count(1)
        p.get_by_role('button',name='Розпізнати локально').click();expect(p.get_by_role('alert')).to_contain_text('Локальна модель ще не встановлена')
        p.get_by_text('Локальне розпізнавання',exact=True).click();p.get_by_label('Використати synthetic fake ASR').check()
        p.get_by_role('button',name='Розпізнати локально').click();expect(p.get_by_label('Перевірити та виправити транскрипт')).to_be_visible()
        p.get_by_label('Перевірити та виправити транскрипт').fill('SYNTHETIC · Перевірений голосовий запис')
        p.get_by_role('button',name='Зберегти виправлення транскрипту').click()
        expect(p.get_by_text('Виправлення транскрипту збережено. Це ще не запис щоденника.',exact=True)).to_be_visible()
        assert not app.state.journal.list()['items']
        p.reload();p.get_by_text('Голосовий запис',exact=True).click()
        expect(p.get_by_label('Перевірити та виправити транскрипт')).to_have_value('SYNTHETIC · Перевірений голосовий запис')
        out=REPO/'generated/m4-ui';out.mkdir(parents=True,exist_ok=True)
        p.screenshot(path=str(out/'voice-desktop-review.png'),full_page=True)
        p.set_viewport_size({'width':390,'height':844});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert p.locator('.voice-panel button').evaluate_all('els=>els.every(e=>e.getBoundingClientRect().height>=44)')
        p.screenshot(path=str(out/'voice-mobile-review.png'),full_page=True)
        p.get_by_label('Оригінальне аудіо').select_option('DELETE_AFTER_CONFIRM');p.get_by_role('button',name='Підтвердити текст у щоденник').click()
        expect(p.locator('.entry')).to_contain_text('SYNTHETIC · Перевірений голосовий запис');expect(p.locator('.voice-item')).to_have_count(0)
        row=app.state.journal.list()['items'][0];assert row['raw_text']=='SYNTHETIC · Перевірений голосовий запис'
        with app.state.store.connect() as c:
            tr=dict(c.execute('SELECT * FROM transcripts').fetchone());assert tr['candidate'].startswith('SYNTHETIC · Кандидат') and tr['edited']==row['raw_text'] and tr['state']=='CONFIRMED'
        assert app.state.runtime.status()['mode']=='OFF' and not app.state.runtime.jobs()['items']
        assert not errors and not external;ctx.close()
    finally:stop(srv,t)

def test_M4_browser_phone_offline_encrypted_restart_upload_lost_response(isolated):
    app,srv,t=server(isolated/'mac');file=isolated/'synthetic-tone.wav';file.write_bytes(wav(5));profile=isolated/'phone'
    try:
      with sync_playwright() as pw:
        ctx=context(pw,profile,file,390);p=ctx.pages[0];p.set_default_timeout(10000);p.goto(ORIGIN+'/phone/');unlock_phone(p);p.get_by_text('Голосовий запис',exact=True).click()
        p.wait_for_function('navigator.serviceWorker.controller!==null');ctx.set_offline(True)
        p.evaluate("""()=>{window.syntheticAudioEncryptMs=[];window.syntheticAudioWriteMs=[];
          const original=crypto.subtle.encrypt.bind(crypto.subtle);crypto.subtle.encrypt=async(...args)=>{const t=performance.now();const result=await original(...args);syntheticAudioEncryptMs.push(performance.now()-t);return result;};
          const transaction=IDBDatabase.prototype.transaction;IDBDatabase.prototype.transaction=function(...args){const t=performance.now(),tx=transaction.apply(this,args);
            if(args[1]==='readwrite'&&Array.from(tx.objectStoreNames).includes('audio'))tx.addEventListener('complete',()=>syntheticAudioWriteMs.push(performance.now()-t));return tx;};}""")
        record(p)
        expect(p.locator('.voice-item')).to_contain_text('Аудіо збережено на телефоні · очікує Mac')
        serialized=p.evaluate('''async()=>{const db=await new Promise(resolve=>{const r=indexedDB.open('personal-companion-synthetic-phone');r.onsuccess=()=>resolve(r.result)});
          const result={};for(const name of ['audio','audioChunks'])result[name]=await new Promise(resolve=>{const r=db.transaction(name).objectStore(name).getAll();r.onsuccess=()=>resolve(r.result)});db.close();return JSON.stringify(result)}''')
        assert 'audio/wav' not in serialized and '"data"' not in serialized and 'content_hash' not in serialized
        assert not app.state.voice.list()['items']
        metrics=p.evaluate("({encryption_ms:syntheticAudioEncryptMs,atomic_audio_write_ms:syntheticAudioWriteMs})")
        performance=REPO/'generated/m4-browser-performance.json'
        performance.write_text(json.dumps({'scope':'SYNTHETIC_CHROMIUM_FAKE_MIC_NATIVE_WEBCRYPTO_INDEXEDDB',**metrics,
          'limitations':'One browser recording, bounded AES-GCM timing and IDB transaction timing. No Galaxy or real speech inference.'},indent=2)+'\n')
        ctx.close()
        ctx=context(pw,profile,file,390);ctx.set_offline(True);p=ctx.pages[0];p.set_default_timeout(10000);p.goto(ORIGIN+'/phone/');unlock_phone(p);p.get_by_text('Голосовий запис',exact=True).click()
        expect(p.locator('.voice-item')).to_contain_text('Аудіо збережено на телефоні')
        out=REPO/'generated/m4-ui';out.mkdir(parents=True,exist_ok=True);p.screenshot(path=str(out/'phone-offline-audio.png'),full_page=True)
        assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');ctx.set_offline(False);pair(p,app,'SYNTHETIC voice phone')
        dropped=[False]
        def lose(route):
            if not dropped[0]:dropped[0]=True;route.fetch();route.abort()
            else:route.continue_()
        ctx.route('**/api/v1/device/voice/audio/*/chunks',lose)
        p.get_by_role('button',name='Передати аудіо на Mac').click();expect(p.locator('.voice-item')).to_contain_text('Потрібна повторна спроба')
        ctx.unroute('**/api/v1/device/voice/audio/*/chunks',lose)
        p.get_by_role('button',name='Передати аудіо на Mac').click();expect(p.locator('.voice-item')).to_contain_text('Аудіо збережено на Mac')
        assert len(app.state.voice.list()['items'])==1
        p.get_by_text('Локальне розпізнавання',exact=True).click();p.get_by_label('Використати synthetic fake ASR').check();p.get_by_role('button',name='Розпізнати локально').click()
        expect(p.get_by_label('Перевірити та виправити транскрипт')).to_be_visible();p.get_by_label('Перевірити та виправити транскрипт').fill('SYNTHETIC · Телефонний голосовий текст')
        p.get_by_role('button',name='Підтвердити текст у щоденник').click();expect(p.locator('.entry')).to_contain_text('SYNTHETIC · Телефонний голосовий текст')
        expect(p.locator('.voice-item')).to_contain_text('Текст підтверджено')
        p.on('dialog',lambda d:d.accept());p.get_by_role('button',name='Видалити аудіо зараз').click();expect(p.locator('.voice-item')).to_have_count(0)
        assert not app.state.voice.list()['items'] and app.state.journal.list()['items']
        assert app.state.runtime.providers['mock'].executions==0;ctx.close()
    finally:stop(srv,t)

def test_M4_browser_phone_quota_retains_recording_retry_export_cancel(isolated):
    app,srv,t=server(isolated/'mac');file=isolated/'synthetic-tone.wav';file.write_bytes(wav(5))
    try:
      with sync_playwright() as pw:
        ctx=context(pw,isolated/'phone',file,390);p=ctx.pages[0];p.set_default_timeout(7000);p.goto(ORIGIN+'/phone/');unlock_phone(p);p.get_by_text('Голосовий запис',exact=True).click()
        p.evaluate('''()=>{window.originalAudioAdd=IDBObjectStore.prototype.add;IDBObjectStore.prototype.add=function(){throw new DOMException('SYNTHETIC audio quota','QuotaExceededError')}}''')
        record(p);expect(p.get_by_role('alert')).to_be_visible();expect(p.locator('.voice-draft')).to_be_visible();expect(p.locator('.voice-item')).to_have_count(0)
        with p.expect_download() as event:p.get_by_role('button',name='Експортувати аудіочернетку').click()
        rescue=Path(event.value.path()).read_text();assert 'SYNTHETIC_AUDIO_RESCUE_V1' in rescue and 'content_hash' not in rescue
        p.evaluate('IDBObjectStore.prototype.add=window.originalAudioAdd;delete window.originalAudioAdd')
        p.get_by_role('button',name='Повторити збереження аудіо').click();expect(p.locator('.voice-item')).to_have_count(1);expect(p.locator('.voice-draft')).to_have_count(0)
        p.get_by_role('button',name='Почати голосовий запис').click();expect(p.get_by_text('Записуємо ·',exact=False)).to_be_visible();p.get_by_role('button',name='Скасувати запис').click()
        expect(p.locator('.voice-item')).to_have_count(1);assert not app.state.voice.list()['items'];ctx.close()
    finally:stop(srv,t)

@pytest.mark.parametrize('failure',['permission','start','track','background'])
def test_M4_browser_recording_interruptions(isolated,failure):
    app,srv,t=server(isolated/'mac');file=isolated/'synthetic-tone.wav';file.write_bytes(wav(5))
    try:
      with sync_playwright() as pw:
        ctx=context(pw,isolated/'profile',file);p=ctx.pages[0];p.set_default_timeout(7000);mac_unlock(p,app)
        if failure=='permission':p.evaluate("()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Permission denied','NotAllowedError')}}")
        elif failure=='start':p.evaluate("()=>{window.AudioContext=class{constructor(){throw new Error('SYNTHETIC recorder start failure')}}}")
        else:p.evaluate('''()=>{const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=async(...args)=>{const s=await original(...args);window.syntheticMicTrack=s.getAudioTracks()[0];return s;}}''')
        p.get_by_role('button',name='Почати голосовий запис').click()
        if failure in ('permission','start'):
            expect(p.get_by_role('alert')).to_be_visible();expect(p.locator('.voice-item')).to_have_count(0)
        else:
            expect(p.get_by_text('Записуємо ·',exact=False)).to_be_visible();p.wait_for_timeout(1000)
            if failure=='track':p.evaluate('syntheticMicTrack.onended(new Event("ended"))')
            else:p.evaluate('''()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));}''')
            expect(p.locator('.voice-item')).to_have_count(1)
            expect(p.get_by_role('button',name='Почати голосовий запис')).to_be_visible()
        ctx.close()
    finally:stop(srv,t)

def test_M4_browser_synthetic_silent_mic_no_meaningful_note(isolated):
    app,srv,t=server(isolated/'mac');file=isolated/'synthetic-silence.wav';file.write_bytes(wav(5,'silence'))
    try:
      with sync_playwright() as pw:
        ctx=context(pw,isolated/'profile',file);p=ctx.pages[0];p.set_default_timeout(7000);mac_unlock(p,app);record(p)
        expect(p.locator('.voice-item')).to_have_count(1);p.get_by_text('Локальне розпізнавання',exact=True).click();p.get_by_label('Використати synthetic fake ASR').check()
        p.get_by_role('button',name='Розпізнати локально').click();expect(p.locator('.voice-item')).to_contain_text('Нічого не розпізнано')
        expect(p.get_by_role('button',name='Підтвердити текст у щоденник')).to_have_count(0)
        assert not app.state.journal.list()['items'] and app.state.voice.engines['FAKE'].executions==0;ctx.close()
    finally:stop(srv,t)
