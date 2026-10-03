"""Explicit exact-C live synthetic voice check; consumes one goal-wide inference attempt."""
import os,threading,time,tempfile,shutil,json,argparse,subprocess
from pathlib import Path
import uvicorn
from playwright.sync_api import sync_playwright,expect
from apps.core.api import create_app
from apps.core.codex_conversation_provider import CodexConversationProvider
from apps.core.whisper_local_asr import WhisperLocalASR
from apps.core.storage import REPO
parser=argparse.ArgumentParser();parser.add_argument('--implementation-sha',required=True);args=parser.parse_args()
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==args.implementation_sha
assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'EXACT_C_REQUIRES_CLEAN_SOURCE'
root=Path(tempfile.mkdtemp(prefix='m7c-actual-voice-original-synthetic-',dir='/private/tmp'));port=8780;origin=f'http://127.0.0.1:{port}';provider=CodexConversationProvider();engine=WhisperLocalASR();app=create_app(root/'data',port=port,synthetic_conversations=True,m7c_synthetic=True,conversation_provider=provider,local_asr=engine);server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,access_log=False,log_level='critical'));thread=threading.Thread(target=server.run,daemon=True);thread.start();end=time.monotonic()+8
while not server.started and time.monotonic()<end:time.sleep(.02)
assert server.started
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'));out=REPO/'generated/m7c-ui';out.mkdir(exist_ok=True)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+str(REPO/'generated/local-asr/synthetic-ua-clear.wav')]);ctx=browser.new_context(permissions=['microphone'],viewport={'width':1440,'height':1000});p=ctx.new_page();p.set_default_timeout(15000);p.goto(origin);p.get_by_label('Код розблокування').fill(app.state.auth.code);p.get_by_role('button',name='Відкрити щоденник').click();expect(p.get_by_text('Тест із вигаданими даними · помічник доступний')).to_be_visible();p.get_by_role('button',name='Записати голосом').click();expect(p.get_by_text('Записуємо ·',exact=False)).to_be_visible();p.wait_for_timeout(3700);p.get_by_role('button',name='Зупинити й зберегти аудіо').click();expect(p.locator('.voice-item')).to_have_count(1);p.get_by_role('button',name='Розпізнати локально').click();expect(p.get_by_label('Перевірити та виправити транскрипт')).to_be_visible(timeout=20000)
  for width,tag in [(1440,'desktop'),(390,'mobile')]:
   p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});p.screenshot(path=str(out/f'actual-local-asr-candidate-{tag}.png'),full_page=True)
  assert not app.state.conversations.list()['items']
  p.get_by_label('Перевірити та виправити транскрипт').fill('ORIGINAL SYNTHETIC · Вигаданий персонаж малює паперовий сад і хоче почати з малої чернетки.');p.get_by_role('button',name='Вставити текст у розмову').click();p.wait_for_function('() => document.querySelector("#conversation-text").value.startsWith("ORIGINAL SYNTHETIC")');assert not app.state.conversations.list()['items'];p.get_by_role('button',name='Надіслати',exact=True).click();expect(p.get_by_role('article',name='Відповідь помічника',exact=True)).to_be_visible(timeout=65000)
  for width,tag in [(1440,'desktop'),(390,'mobile')]:
   p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});p.wait_for_function('() => document.querySelector(".conversation-composer").getBoundingClientRect().bottom<=visualViewport.height+1');p.screenshot(path=str(out/f'actual-live-voice-response-{tag}.png'),full_page=True)
  conversation=app.state.conversations.list()['items'][0];messages=app.state.conversations.get(conversation['id'])['messages'];assert len(messages)==2 and messages[0]['source_reference'] and messages[1]['provenance']=='MODEL_GENERATED'
  with app.state.store.connect() as c:job=json.loads(c.execute('SELECT payload FROM conversation_inferences').fetchone()[0])
  assert not app.state.journal.list()['items'];receipt={'phase':'EXACT_C','implementation_sha':args.implementation_sha,'status':'PASS','provenance':'ORIGINAL_SYNTHETIC_APPLE_TTS_FAKE_BROWSER_CAPTURE','voice_engine':engine.metadata(),'route':provider.metadata(),'provider_result':job['provider_result'],'raw_audio_in_provider':False,'automatic_insert_or_send':False,'no_journal_mutation':True,'messages':2,'ledger':provider.budget.summary()};(REPO/'generated/m7c-actual-voice-e2e.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Actual synthetic local ASR/edit/insert/explicit send/genuine provider E2E PASS');browser.close()
finally:
 for event in app.state.conversation_controller.events.values():event.set()
 for worker in app.state.conversation_controller.workers.values():worker.join(5)
 server.should_exit=True;thread.join(10);assert not thread.is_alive();shutil.rmtree(root)
