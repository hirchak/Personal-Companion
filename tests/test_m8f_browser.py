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
