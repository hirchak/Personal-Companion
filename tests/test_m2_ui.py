"""Synthetic viewport UI inspection and actual Mac pairing management."""
import os,time,threading
from pathlib import Path
import pytest,uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m2_browser import PASSWORD,unlock_phone,capture
from ui_navigation import journal as go_journal, feature


def test_M2_owner_pairing_revoke_ui_and_synthetic_viewports(isolated):
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
    app=create_app(isolated/'ui-mac',port=8768,m2=True)
    srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8768,access_log=False,log_level='critical'));thread=threading.Thread(target=srv.run,daemon=True);thread.start()
    deadline=time.monotonic()+8
    while not srv.started and time.monotonic()<deadline:time.sleep(.02)
    assert srv.started
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);owner=browser.new_context();phone=browser.new_context(viewport={'width':390,'height':844})
        root=owner.new_page();root.goto('http://127.0.0.1:8768/');root.get_by_label('Код розблокування').fill(app.state.auth.code);root.get_by_role('button',name='Відкрити щоденник').click();go_journal(root)
        feature(root,'Налаштування');root.get_by_role('button',name='Пристрої та PWA',exact=True).click();root.get_by_role('button',name='Створити запрошення').click();invite=root.locator('.pair-code').inner_text()
        page=phone.new_page();external=[];errors=[]
        phone.on('request',lambda r:external.append(r.url) if not r.url.startswith('http://127.0.0.1:8768/') else None)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8768/phone/');unlock_phone(page);page.get_by_role('button',name='Налаштування телефону').click();page.get_by_label('Одноразове запрошення Mac').fill(invite);page.get_by_label('Назва synthetic пристрою').fill('SYNTHETIC managed device');page.get_by_role('button',name='З’єднати з Mac',exact=True).click();expect(page.get_by_text('Синхронізацію перевірено за Mac receipts',exact=True)).to_be_visible();page.get_by_role('button',name='Налаштування телефону').click()
        phone.set_offline(True);capture(page,'SYNTHETIC · паперовий сад 🦉');expect(page.get_by_text('Офлайн. Записи зберігаються на телефоні;',exact=False)).to_be_visible()
        out=REPO/'generated/m2-ui';out.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out/'phone-offline.png'),full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path=str(out/'desktop-phone.png'),full_page=True)
        # Refresh Mac settings, revoke is explicit and does not erase cached phone data.
        feature(root,'Налаштування');root.get_by_role('button',name='Пристрої та PWA',exact=True).click();feature(root,'Налаштування');root.get_by_role('button',name='Пристрої та PWA',exact=True).click();root.on('dialog',lambda d:d.accept());root.get_by_role('button',name='Відкликати SYNTHETIC managed device').click()
        phone.set_offline(False);expect(page.get_by_role('heading',name='Потрібне явне узгодження')).to_be_visible();expect(page.locator('.entry-text').first).to_have_text('SYNTHETIC · паперовий сад 🦉')
        assert not external and not errors
        browser.close()
    finally:
      srv.should_exit=True;thread.join(8);assert not thread.is_alive()
