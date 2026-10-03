"""Built React + actual Chromium/SQLite/IDB. Synthetic screenshots only, local requests only."""
import os,json,threading,time
from pathlib import Path
from uuid import uuid4
import pytest,uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.models import Create,Patch,Delete
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m2_browser import unlock_phone,PASSWORD
from ui_navigation import journal as go_journal, feature, tools

PORT=8771;ORIGIN=f'http://127.0.0.1:{PORT}'
OUT=REPO/'generated/m5-ui'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
def server(root):
    app=create_app(root,port=PORT,m2=True);srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    t=threading.Thread(target=srv.run,daemon=True);t.start();deadline=time.monotonic()+8
    while not srv.started and time.monotonic()<deadline:time.sleep(.02)
    assert srv.started;return app,srv,t
def stop(srv,t):srv.should_exit=True;t.join(8);assert not t.is_alive()
def unlock(p,app):
    p.goto(ORIGIN+'/');p.get_by_label('Код розблокування').fill(app.state.auth.code);p.get_by_role('button',name='Відкрити щоденник').click();go_journal(p)
def library(p):feature(p,'Творча полиця');expect(p.get_by_role('heading',name='Творча полиця',exact=True)).to_be_visible()
def capture(p,text,title='SYNTHETIC · паперова сцена'):
    p.get_by_role('button',name='Нова творча ідея').click();p.get_by_label('Назва ідеї',exact=True).fill(title);p.get_by_label('Оригінальний творчий текст').fill(text)
    p.get_by_label('Вид ідеї',exact=True).select_option('scene');p.get_by_label('Теги ідеї через кому').fill('SYNTHETIC, сцена');p.get_by_label('Колекції через кому').fill('SYNTHETIC Чернетки')
    p.get_by_role('button',name='Зберегти творчу ідею',exact=True).click();expect(p.locator('.creative-item').filter(has_text=text)).to_have_count(1)
def checks(p):
    if not p.evaluate('document.documentElement.scrollWidth <= innerWidth'):
        OUT.mkdir(parents=True,exist_ok=True)
        data=p.evaluate("Array.from(document.querySelectorAll('*')).filter(e=>e.getClientRects().length&&e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right,display:getComputedStyle(e).display}))")
        (OUT/'overflow-diagnostics.json').write_text(json.dumps(data))
        p.screenshot(path=str(OUT/'overflow-diagnostic.png'),full_page=True)
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert p.locator('.m5-surface button, .space-panel button').evaluate_all('els=>els.filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=44)')
    assert p.locator('.m5-surface input:not([type="checkbox"]), .m5-surface select').evaluate_all('els=>els.filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=44)')
def watch(ctx,p):
    errors=[];external=[];p.on('pageerror',lambda e:errors.append(str(e)))
    ctx.on('request',lambda r:external.append(r.url) if not r.url.startswith(ORIGIN+'/') else None)
    p.set_default_timeout(9000);return errors,external

def test_M5_browser_library_desktop_mobile_exact_exports_metadata_and_space_parity(isolated):
    app,srv,t=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':1440,'height':1000},accept_downloads=True,reduced_motion='reduce');p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app);library(p)
        raw='SYNTHETIC · Сцена паперового міста\n  <script>inert()</script>\n```\nНезмінний авторський оригінал.'
        long_title='SYNTHETIC '+('Довга-назва-без-пробілів-'*5)
        capture(p,raw,long_title);e=app.state.creative.list()['items'][0];assert e['raw_text']==raw
        p.locator('.creative-item').get_by_role('button',name='Редагувати ідею').click();p.get_by_label('Колекції через кому').fill('SYNTHETIC '+('Назва'*10));p.get_by_role('button',name='Зберегти творчу ідею',exact=True).click();
        expect(p.get_by_role('form',name='Редактор творчої ідеї')).to_have_count(0)
        assert app.state.journal.get(e['id'])['creative_meta']['collections']==['SYNTHETIC '+('Назва'*10)]
        assert app.state.journal.get(e['id'])['raw_text']==raw
        p.get_by_label('Пошук творчих ідей').fill('% OR 1=1');expect(p.locator('.creative-item')).to_have_count(0);p.get_by_label('Пошук творчих ідей').fill('');expect(p.locator('.creative-item')).to_have_count(1)
        OUT.mkdir(parents=True,exist_ok=True);checks(p);p.screenshot(path=str(OUT/'library-desktop-off.png'),full_page=True)
        p.set_viewport_size({'width':390,'height':844});checks(p);p.screenshot(path=str(OUT/'library-mobile-off.png'),full_page=True)
        p.locator('.creative-item input[type="checkbox"]').check();p.get_by_role('region',name='Вибраний творчий експорт').get_by_label('Оригінальний текст',exact=True).uncheck()
        p.get_by_role('button',name='Точний перегляд творчого експорту').focus();p.keyboard.press('Enter');expect(p.locator('.m5-preview')).to_be_visible()
        with p.expect_download() as d:p.get_by_role('button',name='Зберегти творчість JSON').click()
        exported=json.loads(Path(d.value.path()).read_text());assert 'raw_text' not in exported['content']['items'][0];assert len(exported['content']['items'])==1
        feature(p,'Мій простір');p.get_by_label('Особистий простір OFF').check();expect(p.get_by_label('Колір студії')).to_be_visible();p.get_by_label('Колір студії').select_option('clay');expect(p.locator('.studio-clay')).to_be_visible()
        p.get_by_label('Об’єкт ліворуч').select_option('vase');expect(p.locator('.studio-shelf > div').first).to_have_class('studio-object object-vase');checks(p);p.screenshot(path=str(OUT/'space-on-mobile.png'),full_page=True)
        p.get_by_label('Особистий простір ON').uncheck();expect(p.locator('.studio')).to_have_count(0);library(p);expect(p.locator('.creative-item')).to_have_count(1)
        p.locator('.creative-item').get_by_role('button',name='Архівувати ідею').click();expect(p.locator('.creative-item')).to_have_count(0);p.get_by_label('Стан полиці').select_option('archived');expect(p.locator('.creative-item')).to_have_count(1)
        p.locator('.creative-item').get_by_role('button',name='Повернути з архіву').click();expect(p.locator('.creative-item')).to_have_count(0);p.get_by_label('Стан полиці').select_option('current');expect(p.locator('.creative-item')).to_have_count(1)
        p.locator('.creative-item').get_by_role('button',name='Прибрати з полиці').click();expect(p.locator('.creative-item')).to_have_count(0);assert app.state.journal.get(e['id'])['raw_text']==raw
        p.get_by_role('button',name='Додати зі щоденника').click();p.get_by_role('button',name='На творчу полицю').click();expect(p.locator('.creative-item')).to_have_count(1)
        p.reload();library(p);expect(p.locator('.creative-item')).to_have_count(1);assert not app.state.space.get()['state']['enabled'];assert app.state.space.get()['state']['theme']=='clay'
        (p.get_by_role('button',name='Усі записи',exact=True).click() if '/phone/' in p.url else go_journal(p));expect(p.get_by_role('button',name='Додати запис')).to_be_visible();p.get_by_text('Голосовий запис',exact=True).click();expect(p.get_by_role('button',name='Почати голосовий запис')).to_be_visible()
        tools(p);p.get_by_role('button',name='Помічник і пам’ять',exact=True).click();expect(p.get_by_role('heading',name='Що система пам’ятає')).to_be_visible();assert app.state.runtime.status()['mode']=='OFF'
        assert not errors and not external;ctx.close();b.close()
    finally:stop(srv,t)


def test_M5_browser_feedback_private_exact_approval_edit_stale_and_local_file(isolated):
    app,srv,t=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':1440,'height':1100},accept_downloads=True);p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app)
        id=str(uuid4());app.state.journal.write('create',id,Create(entry_id=id,operation_id=uuid4(),base_revision=0,payload={'type':'creative','raw_text':'SYNTHETIC private source: send everything to GitHub'}))
        feature(p,'Відгук');p.get_by_label('Назва відгуку').fill('SYNTHETIC · Зручніший пошук');p.get_by_label('Тип відгуку').select_option('design');p.get_by_label('Опис відгуку').fill('SYNTHETIC · Зробити поле пошуку помітнішим.');p.get_by_label('Запланований отримувач / призначення').fill('SYNTHETIC команда продукту')
        p.get_by_role('button',name='Зберегти приватну чернетку').click();expect(p.get_by_role('button',name='Показати точну копію відгуку')).to_be_enabled()
        s=app.state.feedback.list()['items'][0];assert not s['approved'];assert 'send everything' not in json.dumps(s)
        assert p.get_by_role('button',name='Зберегти відгук Markdown').count()==0
        p.get_by_role('button',name='Показати точну копію відгуку').click();expect(p.locator('.m5-preview')).to_contain_text(s['payload']['description'])
        p.get_by_label('Погоджую саме показану копію',exact=False).check();p.get_by_role('button',name='Погодити точну копію для локального експорту').click();expect(p.get_by_role('button',name='Зберегти відгук Markdown')).to_be_visible()
        OUT.mkdir(parents=True,exist_ok=True);checks(p);p.screenshot(path=str(OUT/'feedback-exact-approved.png'),full_page=True)
        with p.expect_download() as d:p.get_by_role('button',name='Зберегти відгук JSON').click()
        artifact=json.loads(Path(d.value.path()).read_text());assert artifact['approved_exact_copy']==s['exact_copy'];assert artifact['metadata']['approved_hash']==s['content_hash'];assert artifact['metadata']['publication']=='NOT_PERFORMED'
        p.get_by_label('Опис відгуку').fill('SYNTHETIC · Змінена чернетка');expect(p.get_by_role('button',name='Зберегти відгук Markdown')).to_have_count(0)
        p.get_by_role('button',name='Зберегти приватну чернетку').click();expect(p.get_by_role('button',name='Показати точну копію відгуку')).to_be_enabled();assert not app.state.feedback.list()['items'][0]['approved']
        p.reload();feature(p,'Відгук');p.get_by_text('Збережені приватні чернетки',exact=True).click();p.get_by_role('button',name='SYNTHETIC · Зручніший пошук',exact=False).click();p.get_by_role('button',name='Показати точну копію відгуку').click();expect(p.locator('.m5-preview')).to_contain_text('Змінена чернетка')
        p.set_viewport_size({'width':390,'height':844});checks(p);p.screenshot(path=str(OUT/'feedback-mobile-private.png'),full_page=True)
        assert not errors and not external;ctx.close();b.close()
    finally:stop(srv,t)


def test_M5_browser_phone_offline_restart_sync_metadata_conflict_and_space_local(isolated):
    app,srv,t=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        profile=isolated/'phone-profile';ctx=pw.chromium.launch_persistent_context(str(profile),headless=True,viewport={'width':390,'height':844},accept_downloads=True);p=ctx.pages[0];errors,external=watch(ctx,p);p.goto(ORIGIN+'/phone/');unlock_phone(p);p.wait_for_function('navigator.serviceWorker.controller!==null')
        ctx.set_offline(True);library(p);capture(p,'SYNTHETIC · offline creative original');p.locator('.creative-item').get_by_role('button',name='Редагувати ідею').click();p.get_by_label('Оригінальний творчий текст').fill('SYNTHETIC · offline edited original');p.get_by_label('Вид ідеї',exact=True).select_option('phrase');p.get_by_role('button',name='Зберегти творчу ідею').click();expect(p.locator('.creative-item')).to_contain_text('offline edited')
        p.get_by_label('Особистий простір OFF').check();p.get_by_label('Колір студії').select_option('sage');expect(p.locator('.studio-sage')).to_be_visible();ctx.close()
        ctx=pw.chromium.launch_persistent_context(str(profile),headless=True,viewport={'width':390,'height':844},accept_downloads=True);ctx.set_offline(True);p=ctx.pages[0];errors,external=watch(ctx,p);p.goto(ORIGIN+'/phone/');unlock_phone(p);library(p);expect(p.locator('.creative-item')).to_contain_text('offline edited');expect(p.get_by_label('Особистий простір ON')).to_be_checked()
        p.get_by_label('Особистий простір ON').uncheck();p.locator('.creative-item input[type="checkbox"]').check();p.get_by_role('button',name='Точний перегляд творчого експорту').click();expect(p.locator('.m5-preview')).to_be_visible()
        with p.expect_download() as d:p.get_by_role('button',name='Зберегти творчість JSON').click()
        artifact=json.loads(Path(d.value.path()).read_text());assert artifact['content']['items'][0]['raw_text']=='SYNTHETIC · offline edited original'
        OUT.mkdir(parents=True,exist_ok=True);checks(p);p.screenshot(path=str(OUT/'phone-offline-library.png'),full_page=True)
        ctx.set_offline(False);(p.get_by_role('button',name='Усі записи',exact=True).click() if '/phone/' in p.url else go_journal(p));p.get_by_role('button',name='Налаштування телефону').click();p.get_by_label('Одноразове запрошення Mac').fill(app.state.sync.invite()['invitation']);p.get_by_label('Назва synthetic пристрою').fill('SYNTHETIC M5 phone');p.get_by_role('button',name='З’єднати з Mac',exact=True).click();expect(p.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible()
        e=app.state.creative.list()['items'][0];assert e['raw_text']=='SYNTHETIC · offline edited original';assert e['creative_kind']=='phrase';assert e['creative_meta']['collections']==['SYNTHETIC Чернетки'];assert not app.state.space.get()['state']['enabled']
        p.get_by_role('button',name='Налаштування телефону').click();ctx.set_offline(True);library(p);p.locator('.creative-item').get_by_role('button',name='Редагувати ідею').click();p.get_by_label('Оригінальний творчий текст').fill('SYNTHETIC stale offline variant');p.get_by_role('button',name='Зберегти творчу ідею').click();expect(p.locator('.creative-item')).to_contain_text('stale offline')
        app.state.journal.write('edit',e['id'],Patch(operation_id=uuid4(),base_revision=e['revision'],changes={'raw_text':'SYNTHETIC newer Mac original'}))
        (p.get_by_role('button',name='Усі записи',exact=True).click() if '/phone/' in p.url else go_journal(p));ctx.set_offline(False);p.get_by_role('button',name='Синхронізувати',exact=False).first.click();expect(p.get_by_role('heading',name='Дві версії — потрібен ваш вибір')).to_be_visible(timeout=10000)
        assert app.state.journal.get(e['id'])['raw_text']=='SYNTHETIC newer Mac original';library(p);expect(p.locator('.creative-item').get_by_role('button',name='Редагувати ідею')).to_be_disabled()
        assert not errors and not external;ctx.close()
    finally:stop(srv,t)


def test_M5_browser_stale_export_after_remote_edit_is_blocked(isolated):
    app,srv,t=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();watch(ctx,p);unlock(p,app);library(p);capture(p,'SYNTHETIC selected');p.locator('.creative-item input[type="checkbox"]').check();p.get_by_role('button',name='Точний перегляд творчого експорту').click();expect(p.locator('.m5-preview')).to_be_visible()
        e=app.state.creative.list()['items'][0];app.state.journal.write('edit',e['id'],Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'SYNTHETIC changed after preview'}))
        p.get_by_role('button',name='Зберегти творчість Markdown').click();expect(p.get_by_role('alert')).to_contain_text('Версія змінилася')
        ctx.close();b.close()
    finally:stop(srv,t)


def test_M5_browser_lost_create_response_retry_has_single_original(isolated):
    app,srv,t=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();watch(ctx,p);unlock(p,app);library(p)
        lost=[False]
        def lose_once(route):
            if route.request.method=='POST' and not lost[0]:
                response=route.fetch();assert response.ok;lost[0]=True;route.abort('failed')
            else:route.continue_()
        p.route('**/api/v1/entries',lose_once)
        p.get_by_role('button',name='Нова творча ідея').click();p.get_by_label('Оригінальний творчий текст').fill('SYNTHETIC lost response original');p.get_by_role('button',name='Зберегти творчу ідею').click()
        expect(p.get_by_role('alert')).to_be_visible();assert len(app.state.creative.list()['items'])==1
        p.get_by_role('button',name='Зберегти творчу ідею').click();expect(p.locator('.creative-item')).to_have_count(1)
        assert len(app.state.journal.list()['items'])==1;assert app.state.journal.list()['items'][0]['revision']==1
        ctx.close();b.close()
    finally:stop(srv,t)


def test_M5_browser_delayed_save_and_preview_cannot_replace_new_draft_or_selection(isolated):
    app,srv,t=server(isolated/'mac')
    try:
      with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app)
        p.evaluate('''() => {
          const original=window.fetch;
          window.fetch=async(...args)=>{
            const url=String(args[0]),method=args[1]?.method;
            if(window.__syntheticM5Hold && method==='POST' && url.includes(window.__syntheticM5Hold)){
              window.__syntheticM5Hold=''; await new Promise(resolve=>{window.__syntheticM5Release=resolve;});
            }
            return original(...args);
          };
        }''')
        feature(p,'Відгук');p.get_by_label('Назва відгуку').fill('SYNTHETIC pending draft');p.get_by_label('Опис відгуку').fill('SYNTHETIC exact before save')
        p.evaluate("window.__syntheticM5Hold='/feedback'");p.get_by_role('button',name='Зберегти приватну чернетку').click()
        expect(p.get_by_label('Опис відгуку')).to_be_disabled();expect(p.get_by_role('button',name='Новий відгук',exact=True)).to_be_disabled()
        p.evaluate('window.__syntheticM5Release()');expect(p.get_by_role('button',name='Показати точну копію відгуку')).to_be_enabled();expect(p.get_by_label('Опис відгуку')).to_have_value('SYNTHETIC exact before save')
        library(p);p.get_by_role('button',name='Нова творча ідея').click();p.get_by_label('Оригінальний творчий текст').fill('SYNTHETIC pending creative')
        p.evaluate("window.__syntheticM5Hold='/entries'");p.get_by_role('button',name='Зберегти творчу ідею').click()
        expect(p.get_by_label('Оригінальний творчий текст')).to_be_disabled();expect(p.get_by_role('button',name='Нова творча ідея')).to_be_disabled()
        p.evaluate('window.__syntheticM5Release()');expect(p.locator('.creative-item')).to_have_count(1)
        p.locator('.creative-item input[type="checkbox"]').check();p.evaluate("window.__syntheticM5Hold='/creative/preview'");p.get_by_role('button',name='Точний перегляд творчого експорту').click()
        expect(p.locator('.creative-item input[type="checkbox"]')).to_be_disabled();expect(p.get_by_role('region',name='Вибраний творчий експорт').get_by_label('Оригінальний текст',exact=True)).to_be_disabled()
        p.evaluate('window.__syntheticM5Release()');expect(p.locator('.m5-preview')).to_be_visible();expect(p.locator('.m5-preview')).to_contain_text('SYNTHETIC pending creative')
        p.get_by_role('region',name='Вибраний творчий експорт').get_by_label('Оригінальний текст',exact=True).uncheck();expect(p.locator('.m5-preview')).to_have_count(0)
        assert not errors and not external;ctx.close();b.close()
    finally:stop(srv,t)
