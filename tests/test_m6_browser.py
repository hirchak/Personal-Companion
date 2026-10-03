"""Built React/Chromium + SQLite health workflows. Fixtures and screenshots exclusively SYNTHETIC."""
import os,json
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from test_m1_domain import isolated
from test_m5_browser import server,stop,unlock,watch,ORIGIN
from test_m2_browser import unlock_phone
from m6_fixtures import batch,record
from ui_navigation import feature, journal as go_journal
from apps.core.storage import REPO
OUT=REPO/'generated/m6-ui'

def health(p):feature(p,'Дані з годинника');expect(p.get_by_role('heading',name='Дані з Health Connect',exact=True)).to_be_visible()
def upload(p,payload):p.get_by_label('Локальний файл передавання',exact=True).set_input_files({'name':'SYNTHETIC-bridge.json','mimeType':'application/json','buffer':json.dumps(payload).encode()});p.get_by_role('button',name='Імпортувати локальну копію',exact=True).click()
def checks(p):
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert p.locator('.health-panel button').evaluate_all('els=>els.filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=44)')

def test_health_browser_import_delete_explicit_reimport_desktop_mobile(isolated):
    app,srv,t=server(isolated/'mac')
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app);health(p)
            expect(p.get_by_text('Потрібне явне підключення',exact=True)).to_be_visible();assert not app.state.health.records()
            fixture=batch(record('sleep'),record()).model_dump();upload(p,fixture);expect(p.get_by_role('status')).to_contain_text('Локальну копію імпортовано')
            assert len(app.state.health.records())==2 and not app.state.journal.list()['items'];checks(p)
            OUT.mkdir(parents=True,exist_ok=True);p.screenshot(path=str(OUT/'health-desktop.png'),full_page=True)
            p.set_viewport_size({'width':390,'height':844});checks(p);p.screenshot(path=str(OUT/'health-mobile.png'),full_page=True)
            p.get_by_role('button',name='Видалити імпортовану копію',exact=True).click();p.get_by_role('button',name='Так, видалити лише копію').click();expect(p.get_by_role('status')).to_contain_text('Імпортовану копію видалено');assert not app.state.health.records()
            upload(p,fixture);expect(p.get_by_role('alert')).to_contain_text('Операцію не завершено');assert not app.state.health.records()
            p.get_by_label('Явно підключити джерело',exact=False).check();p.get_by_role('button',name='Імпортувати локальну копію').click();expect(p.get_by_role('status')).to_contain_text('Локальну копію імпортовано');assert len(app.state.health.records())==2
            (p.get_by_role('button',name='Усі записи',exact=True).click() if '/phone/' in p.url else go_journal(p));expect(p.get_by_role('heading',name='Ваш щоденник')).to_be_visible();assert not errors and not external;b.close()
    finally:stop(srv,t)

def test_health_browser_malformed_partial_revoke_keeps_journal(isolated):
    app,srv,t=server(isolated/'mac')
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();errors,external=watch(ctx,p);unlock(p,app);health(p)
            upload(p,{'schema_version':1,'shell':'SYNTHETIC DO NOT EXECUTE'});expect(p.get_by_role('alert')).to_be_visible();assert not app.state.health.records()
            payload=batch(record(),permissions={'sleep':'PERMISSION_DENIED','exercise':'READ_FAILED'}).model_dump();upload(p,payload);expect(p.get_by_role('status')).to_contain_text('Локальну копію імпортовано');expect(p.get_by_text('Частковий доступ',exact=True)).to_be_visible()
            expect(p.locator('.health-status')).to_contain_text('Читання не дозволено');expect(p.locator('.health-status')).to_contain_text('Доступність невідома')
            feature(p,'Заблокувати');expect(p.get_by_label('Код розблокування')).to_be_visible();assert p.locator('.health-panel').count()==0;assert not errors and not external;b.close()
    finally:stop(srv,t)

def test_phone_health_truthful_offline_without_fake_copy(isolated):
    app,srv,t=server(isolated/'mac')
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':390,'height':844});p=ctx.new_page();errors,external=watch(ctx,p);p.goto(ORIGIN+"/phone/");unlock_phone(p);health(p)
            p.get_by_role('button',name='Перевірити стан копії на Mac').click();expect(p.get_by_role('status')).to_contain_text('копія на Mac недоступна')
            ctx.set_offline(True);expect(p.get_by_role('button',name='Перевірити стан копії на Mac')).to_be_disabled();expect(p.get_by_text('Офлайн: стан джерела невідомий.',exact=False)).to_be_visible();checks(p);OUT.mkdir(parents=True,exist_ok=True);p.screenshot(path=str(OUT/'health-phone-offline.png'),full_page=True)
            (p.get_by_role('button',name='Усі записи',exact=True).click() if '/phone/' in p.url else go_journal(p));expect(p.get_by_role('heading',name='Ваш щоденник')).to_be_visible();assert not errors and not external;b.close()
    finally:stop(srv,t)

def test_phone_health_pairing_reads_only_status_and_disconnects_normally(isolated):
    from test_m2_browser import pair
    app,srv,t=server(isolated/'mac');app.state.health.apply(batch(record()))
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':390,'height':844});p=ctx.new_page();p.set_default_timeout(9000);p.goto(ORIGIN+'/phone/');unlock_phone(p);pair(p,app,'SYNTHETIC health-status phone');health(p)
            p.get_by_role('button',name='Перевірити стан копії на Mac').click();expect(p.locator('.health-status')).to_contain_text('Кроки');expect(p.locator('.health-status')).to_contain_text('Дані доступні')
            assert p.locator('.health-panel').get_by_text('42',exact=True).count()==0
            ctx.set_offline(True);expect(p.locator('.health-status')).to_have_count(0);expect(p.get_by_text('Офлайн: стан джерела невідомий.',exact=False)).to_be_visible();b.close()
    finally:stop(srv,t)

def test_health_delayed_record_response_cannot_restore_deleted_ui_copy(isolated):
    app,srv,t=server(isolated/'mac');app.state.health.apply(batch(record()))
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page();p.set_default_timeout(9000);unlock(p,app);health(p)
            old={'items':app.state.health.records()};held=[]
            p.route('**/api/v1/health/records',lambda route:held.append(route))
            p.get_by_text('Переглянути окремі імпортовані записи',exact=True).click();p.wait_for_timeout(100);assert held
            p.get_by_role('button',name='Видалити імпортовану копію',exact=True).click();p.get_by_role('button',name='Так, видалити лише копію').click();expect(p.get_by_role('status')).to_contain_text('Імпортовану копію видалено')
            held[0].fulfill(status=200,content_type='application/json',body=json.dumps(old));p.wait_for_timeout(100);assert p.locator('.health-panel li').count()==0 and not app.state.health.records();b.close()
    finally:stop(srv,t)
