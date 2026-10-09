"""Built loopback synthetic UI: no generated prose before release, including fake wire partials."""
import json
import os
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import sync_playwright, expect

from apps.core.api import create_app
from apps.core.conversation_controller import ConversationController
from apps.core.conversation_release import ReleasePolicy
from apps.core.storage import REPO
from test_m1_domain import isolated
from test_m8e_q03_release import Provider, HeldReviewer

PORT=8793;ORIGIN=f'http://127.0.0.1:{PORT}'
MARK='ORIGINAL_SYNTHETIC_NEVER_RELEASED_BROWSER_MARK'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))


def unlock(page,app):
    page.goto(ORIGIN)
    page.get_by_label('Код розблокування').fill(app.state.auth.code)
    page.get_by_role('button',name='Відкрити Особистий простір').click()
    expect(page.get_by_role('heading',name='Що у вас сьогодні на думці?')).to_be_visible()


def serve(root):
    provider=Provider('Я ваш ліцензований психолог. '+MARK)
    reviewer=HeldReviewer()
    # A longer test barrier; there is no external reviewer/provider process.
    def held(item):
        from apps.core.conversation_release import BoundedReviewer
        reviewer.started.set();reviewer.release.wait(15)
        return BoundedReviewer().review(item)
    reviewer.review=held
    app=create_app(root,port=PORT,synthetic_conversations=True,m7c_synthetic=True,
                   conversation_provider=provider,conversation_timeout=30)
    app.state.conversation_controller.release_policy=ReleasePolicy(reviewer)
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,access_log=False,log_level='critical'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    end=time.monotonic()+8
    while not server.started and time.monotonic()<end:time.sleep(.02)
    assert server.started
    return app,server,thread,provider,reviewer


def stop(server,thread,reviewer):
    reviewer.release.set();server.should_exit=True;thread.join(8)
    assert not thread.is_alive()


def no_mark(page):
    if MARK in page.content():raise AssertionError('UNRELEASED_DOM_TEXT_DETECTED')
    assert page.get_by_label('Чернетка відповіді').count()==0


@pytest.mark.parametrize('width,mode',[(1440,'FREE'),(390,'DEEP')])
def test_pending_rejected_and_retried_response_in_built_dom(isolated,width,mode):
    app,server,thread,provider,reviewer=serve(isolated/'q03-ui')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);page=browser.new_page(viewport={'width':width,'height':900})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            unlock(page,app)
            if mode=='DEEP':
                page.get_by_role('button',name='Глибока',exact=True).click()
                page.get_by_label('Текст цілі',exact=True).fill('ORIGINAL SYNTHETIC · Обрати формат макета.')
                page.get_by_label('Це моя погоджена ціль').check()
                page.get_by_role('button',name='Створити ціль',exact=True).click()
                page.get_by_role('button',name='Почати глибоку розмову',exact=True).click()
            page.get_by_label('Повідомлення',exact=True).fill('Хочу просто висловити думку.')
            page.get_by_role('button',name='Надіслати',exact=True).click()
            expect(page.get_by_text('Перевіряємо відповідь…',exact=True)).to_be_visible()
            no_mark(page)
            controller=app.state.conversation_controller
            conv=app.state.conversations.list()['items'][0]['id']
            job=controller.page(conv)['inference_job']['id']
            wire=page.evaluate('async (url) => (await fetch(url)).json()',f'/api/v1/conversations/{conv}/inference/{job}')
            assert wire['partial_candidate'] is None and wire['candidate'] is None
            out=REPO/'generated/m8e-q03-ui';out.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(out/f'awaiting-{width}.png'),full_page=True)
            reviewer.release.set()
            expect(page.get_by_text('Відповідь недоступна.',exact=False)).to_be_visible()
            no_mark(page);page.reload();no_mark(page)
            assert len(app.state.conversations.get(conv)['messages'])==1
            provider.text='Можна залишити думку без наступного кроку.'
            page.get_by_role('button',name='Повторити цей запит',exact=True).click()
            expect(page.get_by_label('Відповідь помічника',exact=True)).to_be_visible()
            expect(page.get_by_label('Відповідь помічника',exact=True)).to_contain_text(provider.text)
            no_mark(page);assert len(app.state.conversations.get(conv)['messages'])==2
            assert not errors and provider.calls==2 and provider.partial_callback is None
            browser.close()
    finally:stop(server,thread,reviewer)


@pytest.mark.parametrize('event',['cancel','restart'])
def test_wire_partial_candidate_auxiliary_fields_never_render_after_abort(isolated,event):
    app,server,thread,provider,reviewer=serve(isolated/'q03-abort')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);page=browser.new_page(viewport={'width':390,'height':844})
            unlock(page,app)
            def poll(route):
                response=route.fetch();value=response.json()
                if value.get('state')=='RUNNING':
                    value['partial_candidate']=MARK
                    value['candidate']={'assistant_text':MARK,'goal_suggestion':MARK,
                        'closure':{'discussed':[MARK],'clearer':MARK,'unresolved':MARK,'possible_steps':[MARK]},'topics':[],'source_refs':[]}
                route.fulfill(response=response,body=json.dumps(value))
            page.route('**/inference/*',poll)
            page.get_by_label('Повідомлення',exact=True).fill('Просто одна синтетична думка.')
            page.get_by_role('button',name='Надіслати',exact=True).click()
            expect(page.get_by_text('Перевіряємо відповідь…',exact=True)).to_be_visible();no_mark(page)
            if event=='cancel':
                with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/actions')) as acknowledgement:
                    page.get_by_role('button',name='Скасувати відповідь',exact=True).click()
                assert acknowledgement.value.status==200
                assert acknowledgement.value.json()['state']=='CANCELLED'
            else:ConversationController(app.state.conversations,provider)
            reviewer.release.set()
            expect(page.get_by_text('Запит скасовано.' if event=='cancel' else 'Відповідь недоступна.',exact=False)).to_be_visible()
            no_mark(page);page.reload();no_mark(page)
            conv=app.state.conversations.list()['items'][0]['id']
            assert len(app.state.conversations.get(conv)['messages'])==1
            browser.close()
    finally:stop(server,thread,reviewer)


def test_delayed_final_history_cannot_reselect_old_conversation(isolated):
    app,server,thread,provider,reviewer=serve(isolated/'q03-selection-race')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);page=browser.new_page()
            unlock(page,app);provider.text='ORIGINAL SYNTHETIC · Approved old conversation.'
            page.get_by_label('Повідомлення',exact=True).fill('Перша синтетична думка.')
            page.get_by_role('button',name='Надіслати',exact=True).click()
            expect(page.get_by_text('Перевіряємо відповідь…',exact=True)).to_be_visible()
            old=app.state.conversations.list()['items'][0]['id'];held=[]
            def delay(route):held.append((route,route.fetch()))
            page.route(ORIGIN+'/api/v1/conversations/'+old,delay)
            reviewer.release.set()
            end=time.monotonic()+5
            while not held and time.monotonic()<end:page.wait_for_timeout(20)
            assert held
            page.get_by_role('button',name='Нова розмова',exact=True).click()
            provider.text='ORIGINAL SYNTHETIC · Approved new conversation.'
            page.get_by_label('Повідомлення',exact=True).fill('Друга синтетична думка.')
            page.get_by_role('button',name='Надіслати',exact=True).click()
            expect(page.get_by_label('Відповідь помічника',exact=True)).to_contain_text(provider.text)
            for route,response in held:route.fulfill(response=response)
            page.wait_for_timeout(450)
            expect(page.get_by_label('Відповідь помічника',exact=True)).to_contain_text(provider.text)
            if 'Approved old conversation' in page.content():raise AssertionError('STALE_CONVERSATION_RESELECTED')
            browser.close()
    finally:stop(server,thread,reviewer)
