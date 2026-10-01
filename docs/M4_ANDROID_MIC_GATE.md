# M4-A15 — Galaxy S24 Ultra microphone manual gate

Status: **HARDWARE_UNVERIFIED / NOT_RUN**. Reference phone is Galaxy S24 Ultra. Automated
Chromium fake microphone, desktop phone viewport and localhost secure-context behavior are not
actual Galaxy acceptance. No real private data, phone rollout, system certificate/Keychain/Tailscale/
LAN/router/deploy changes are authorized by M4. Existing [M2 transport gate](M2_ANDROID_GATE.md)
stays in force; obtain a separately scoped secure private-origin rollout permission first.

Record exact reviewed C/R, actual Android/One UI/Chrome/PWA versions, device model, secure origin
trust and test-media provenance. Use generated/cleared synthetic test sound, not personal speech.
Do not publish origin, device identifiers, credentials, real audio or lock-screen/private screenshots.

1. At the approved secure private origin, install/open PWA; create/unlock encrypted phone store and
   pair. Deny microphone permission first: show actionable error, no saved recording. Allow it and
   retry; start timer/state, pause/resume, stop, cancel. Confirm no monitoring or background promise.
2. Record synthetic input offline with Mac unavailable. Stop and wait for actual local save; verify
   no claim of Mac receipt. Force-close/reopen Chrome/PWA, unlock and locate the pending recording.
3. Repeat with screen lock, app switch, visibility/background change and unexpectedly ended track.
   Record actual behavior and precise durability point; current in-memory audio may be lost before
   save. Do not mark reliable background capture merely because one foreground recording worked.
4. Exercise storage pressure/quota/rejection using scoped test harness; verify no fake save, available
   draft retained, encrypted rescue export/import or explicit discard. Inspect application encryption
   with controlled test storage; no audio/hash/transcript/credential plaintext in IDB metadata, Web
   Storage or Cache API. Browser/OS eviction and hardware secure key storage remain separate limits.
5. Restore route and transfer: chunk progress, interruption/lost response/retry/restart, one final
   verified Mac attachment/hash. Revoke device and rotate epoch: no old transfer continuation.
   Re-pair/reconcile explicitly, then new audio copy if needed; no silent old-epoch replay.
6. With explicit fake ASR or separately approved verified local engine, inspect candidate, persist an
   edit, reopen, confirm into journal. Original candidate/provenance remain separate. No automatic M3
   jobs/memory/provider dispatch; raw audio never enters an AI context. Silence yields nothing recognized.
7. Verify KEEP, DELETE_AFTER_CONFIRM and confirmed DELETE_NOW. Phone original is not silently removed
   before durable receipt/confirmed transcript/selected action. Test phone-only deletion while offline;
   no claim to erase remote Mac jobs/files, revoked devices, snapshots or backups.
8. Confirm keyboard/assistive labels/44px targets/layout, PWA safe update, foreground recording and
   storage unlock/lock. Lock/wake removes displayed/decrypted content. Watch/Health are not accessed.

Evidence records expected/actual per action, PASS/FAIL/NOT_RUN, exact versions/SHAs, timing and
sanitized screenshots. Missing real hardware run keeps A15 HARDWARE_UNVERIFIED / NOT_RUN.
