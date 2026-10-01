"""Bounded synthetic measurements on real built PWA/IDB/SQLite, never S24 benchmark."""
import os,json,time,statistics,tempfile,threading,shutil,platform,subprocess
from pathlib import Path
import uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.storage import REPO

def main():
    root=Path(tempfile.mkdtemp(prefix='m2-measure-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app=create_app(root/'mac',port=8770,m2=True)
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8770,access_log=False,log_level='critical'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    while not server.started:time.sleep(.02)
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);context=browser.new_context();page=context.new_page();page.goto('http://127.0.0.1:8770/phone/')
        page.get_by_label('Локальний пароль').fill('SYNTHETIC measurement passphrase');page.get_by_role('button',name='Створити encrypted сховище').click();expect(page.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible();page.wait_for_function('navigator.serviceWorker.controller!==null')
        context.set_offline(True);latency=[]
        for i in range(20):
          page.get_by_role('button',name='Додати запис').click();page.get_by_label('Текст',exact=True).fill(f'SYNTHETIC · measured note {i} 🦉')
          start=time.perf_counter();page.get_by_role('button',name='Зберегти на телефоні',exact=True).click();expect(page.locator('.entry')).to_have_count(i+1);latency.append((time.perf_counter()-start)*1000)
        estimate=page.evaluate('async()=>navigator.storage.estimate()')
        storage_bytes=page.evaluate("async()=>{const db=await new Promise(resolve=>{const r=indexedDB.open('personal-companion-synthetic-phone');r.onsuccess=()=>resolve(r.result)});const all=await new Promise(resolve=>{const r=db.transaction('vault').objectStore('vault').getAll();r.onsuccess=()=>resolve(r.result)});db.close();return new TextEncoder().encode(JSON.stringify(all)).length}")
        cache_bytes=page.evaluate("async()=>{let n=0;for(const c of await caches.keys())for(const r of await(await caches.open(c)).keys())n+=(await(await(await caches.open(c)).match(r)).arrayBuffer()).byteLength;return n}")
        context.set_offline(False);page.get_by_role('button',name='Налаштування телефону').click();page.get_by_label('Одноразове запрошення Mac').fill(app.state.sync.invite()['invitation']);start=time.perf_counter();page.get_by_role('button',name='З’єднати з Mac').click();expect(page.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible(timeout=15000);sync_ms=(time.perf_counter()-start)*1000
        cpu=time.process_time();clock=time.perf_counter();time.sleep(.5);idle=(time.process_time()-cpu)/(time.perf_counter()-clock)*100
        rss=int(subprocess.check_output(['ps','-o','rss=','-p',str(os.getpid())],text=True).strip())
        result={'scope':'Real built synthetic desktop Chromium PWA + loopback Mac API, not actual Android or target M2/16GB benchmark','N':20,'environment':{'python':platform.python_version(),'os':platform.system()+' '+platform.release(),'architecture':platform.machine(),'chromium':browser.version},'method':'20 UI save completions include encryption+atomic entry/outbox; one pairing+20-op reconnect batch; encoded IDB envelope, estimate and Cache API response bytes; own Mac harness 0.5s idle/process RSS','local_save_enqueue_ms':{'median':statistics.median(latency),'max':max(latency)},'reconnect_pair_and_sync_20_ms':sync_ms,'idb_envelope_bytes':storage_bytes,'browser_origin_estimate':estimate,'shell_cache_bytes':cache_bytes,'sqlite_db_bytes':app.state.store.db.stat().st_size,'mac_harness_idle_cpu_percent':idle,'mac_harness_rss_kib':rss,'measured_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        print(json.dumps(result,ensure_ascii=False,indent=2));browser.close()
    finally:
        server.should_exit=True;thread.join(8);shutil.rmtree(root)
if __name__=='__main__':main()
