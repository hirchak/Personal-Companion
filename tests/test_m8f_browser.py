"""Real fake-device recording remains protected while its legacy panel is hidden."""
from playwright.sync_api import sync_playwright, expect
from test_m1_domain import isolated
from test_m4_browser import server, stop, context, mac_unlock
from test_m4_voice import wav


def test_native_unsaved_signal_covers_collapsed_legacy_recording(isolated):
    app, srv, thread = server(isolated/'mac')
    audio = isolated/'ORIGINAL_SYNTHETIC_TONE.wav'
    audio.write_bytes(wav(5))
    try:
        with sync_playwright() as pw:
            ctx = context(pw, isolated/'browser', audio)
            page = ctx.pages[0]
            mac_unlock(page, app)
            page.get_by_role('button', name='Почати голосовий запис').click()
            panel = page.locator('.voice-panel')
            expect(panel).to_have_attribute('data-native-unsaved', 'true')
            expect(page.get_by_text('Записуємо ·', exact=False)).to_be_visible()
            page.get_by_text('Голосовий запис', exact=True).click()
            expect(panel).not_to_be_visible()
            # Native guard sees the Boolean even while the recorder UI is collapsed.
            expect(panel).to_have_attribute('data-native-unsaved', 'true')
            page.get_by_text('Голосовий запис', exact=True).click()
            page.wait_for_timeout(1000)
            page.get_by_role('button', name='Зупинити й зберегти аудіо').click()
            expect(page.locator('.voice-item')).to_have_count(1)
            expect(panel).to_have_attribute('data-native-unsaved', 'false')
            ctx.close()
    finally:
        stop(srv, thread)


def test_composer_cancel_late_permission_retry_and_pending_save(isolated):
    """Chromium-only negative lifecycle; never substitutes native/Whisper proof."""
    app, srv, thread = server(isolated/'mac')
    audio = isolated/'ORIGINAL_SYNTHETIC_TONE.wav'
    audio.write_bytes(wav(5))
    try:
        with sync_playwright() as pw:
            ctx = context(pw, isolated/'browser', audio)
            page = ctx.pages[0]
            mac_unlock(page, app)
            page.get_by_role('button', name='Розмова', exact=True).click()
            page.evaluate("""() => {
              const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
              window.syntheticRealCapture=original;
              navigator.mediaDevices.getUserMedia=()=>Promise.reject(new DOMException('Denied','NotAllowedError'));
            }""")
            page.get_by_role('button', name='Записати голосом').click()
            expect(page.get_by_text('Не вдалося почати запис.', exact=False)).to_be_visible()
            page.evaluate("""() => {
              navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>{window.syntheticLate=resolve;});
            }""")
            page.get_by_role('button', name='Записати голосом').click()
            producer = page.locator('.composer-voice')
            expect(producer).to_have_attribute('data-voice-state', 'STARTING')
            page.get_by_role('button', name='Скасувати', exact=True).click()
            expect(producer).to_have_attribute('data-voice-state', 'CANCELLED')
            page.evaluate("""async () => {
              const stream=await window.syntheticRealCapture({audio:true,video:false});
              window.syntheticLateTrack=stream.getAudioTracks()[0];window.syntheticLate(stream);
              navigator.mediaDevices.getUserMedia=window.syntheticRealCapture;
            }""")
            page.wait_for_function("window.syntheticLateTrack.readyState==='ended'")
            assert not app.state.voice.list()['items']
            page.get_by_role('button', name='Записати голосом').click()
            expect(producer).to_have_attribute('data-voice-state', 'RECORDING')
            page.wait_for_timeout(700)
            # A real local API failure leaves the in-memory audio draft recoverable.
            page.route('**/api/v1/voice/audio', lambda route: route.fulfill(status=503,body='{}',content_type='application/json'))
            page.get_by_role('button', name='Завершити', exact=True).click()
            expect(producer).to_have_attribute('data-voice-state', 'FAILED')
            expect(producer).to_have_attribute('data-native-unsaved', 'true')
            page.evaluate("document.querySelector('.composer-voice').style.display='none'")
            expect(producer).not_to_be_visible()
            assert page.locator('[data-native-unsaved=true]').count() == 1
            page.evaluate("document.querySelector('.composer-voice').style.display=''")
            page.unroute('**/api/v1/voice/audio')
            page.get_by_role('button',name='Повторити збереження').click()
            expect(producer).to_have_attribute('data-voice-state','WAITING_FOR_LOCAL_ASR')
            assert len(app.state.voice.list()['items']) == 1
            expect(producer).to_have_attribute('data-native-unsaved','false')
            ctx.close()
    finally:
        stop(srv, thread)
