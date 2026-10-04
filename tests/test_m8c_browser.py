"""Real Chromium PRIVATE_LOCAL path with ORIGINAL SYNTHETIC data only; native security in separate Mac dry-run."""
import os
import threading
import time
import pytest
import uvicorn
from playwright.sync_api import sync_playwright, expect
from apps.core.api import create_app
from apps.core.storage import REPO
from apps.core.root_types import RootKind
from test_m1_domain import isolated
from test_m8a_release import package
from test_m8b_readiness import runtime_package
from test_m8c_private import private_package,protected,vault
from ui_navigation import feature

PORT=8882;ORIGIN=f'http://127.0.0.1:{PORT}'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))

@pytest.mark.parametrize('scenario',['private_core','idle_lock'])
def test_private_browser_mode_core_and_lock(vault,scenario):
    _,_,_,data,_=vault
    app=create_app(data,port=PORT,root_kind=RootKind.PRIVATE_LOCAL,release_identity='DEVELOPMENT')
    srv=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    thread=threading.Thread(target=srv.run,daemon=True);thread.start()
    deadline=time.monotonic()+10
    while not srv.started and time.monotonic()<deadline:time.sleep(.03)
    assert srv.started
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);ctx=browser.new_context(viewport={'width':1440,'height':1000})
            external=[];errors=[]
            ctx.on('request',lambda request:external.append('EXTERNAL_REQUEST') if not request.url.startswith(ORIGIN+'/') else None)
            page=ctx.new_page();page.on('pageerror',lambda _:errors.append('PAGE_ERROR'))
            page.clock.install();page.goto(ORIGIN)
            expect(page.get_by_text('Локальний приватний пілот · лише цей Mac.',exact=False)).to_be_visible()
            expect(page.get_by_text('Synthetic demo',exact=False)).to_have_count(0)
            page.get_by_label('Код розблокування').fill(app.state.auth.code)
            page.get_by_role('button',name='Відкрити щоденник').click()
            expect(page.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible()
            expect(page.get_by_role('button',name='Розмова',exact=True)).to_have_count(0)
            expect(page.locator('.voice-disclosure,.journal-tools')).to_have_count(0)
            if scenario=='idle_lock':
                page.clock.fast_forward(900001)
                expect(page.get_by_label('Код розблокування')).to_be_visible()
                expect(page.locator('.journal')).to_have_count(0)
            else:
                page.get_by_role('button',name='Додати запис',exact=True).click()
                page.get_by_label('Текст',exact=True).fill('ORIGINAL SYNTHETIC · M8C browser fixture')
                page.get_by_role('button',name='Зберегти на Mac').click()
                expect(page.get_by_text('ORIGINAL SYNTHETIC · M8C browser fixture',exact=True)).to_be_visible()
                feature(page,'Творча полиця')
                page.get_by_role('button',name='Нова творча ідея').click()
                page.get_by_label('Назва ідеї',exact=True).fill('ORIGINAL SYNTHETIC M8C idea')
                page.get_by_label('Оригінальний творчий текст').fill('ORIGINAL SYNTHETIC creative content')
                page.get_by_role('button',name='Зберегти творчу ідею',exact=True).click()
                expect(page.locator('.creative-item')).to_have_count(1)
                for width in [1440,390]:
                    page.set_viewport_size({'width':width,'height':844})
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.get_by_role('button',name='Більше',exact=True).click()
                for label in ['Розмова','Практики','Дані з годинника','Відгук']:
                    expect(page.get_by_role('button',name=label,exact=True)).to_have_count(0)
                page.get_by_role('button',name='Заблокувати',exact=True).click()
                expect(page.get_by_label('Код розблокування')).to_be_visible()
                expect(page.get_by_text('ORIGINAL SYNTHETIC creative content',exact=True)).to_have_count(0)
            assert not external and not errors
            ctx.close();browser.close()
    finally:
        srv.should_exit=True;thread.join(10);assert not thread.is_alive()
