# M8F-F01 — native voice forward fix

Implementation C: da2003f783a077a4173323f523981efec82101b3.
Base R: 1c09275937c6f152ad09efc8b781591d617359e2; branch main.
Report commit: evidence-only child of C, resolve with `git log -1 --format=%H -- reports/M8F_F01_NATIVE_VOICE_REPORT.md`.
Written before R/push; actual R and remote equality are reported in the delivery message.
CI: NOT_RUN; no repository workflow configured. Independent acceptance pending.

F09 **PASS on final exact C**, using LOCAL_TEST A141/B142, a new empty protected
synthetic home, Finder/native WKWebView and the existing authored PCM fixture.
Actual hardware: Mac14,15/M2/8GB, macOS27.0/26A428, arm64; SDK26.5, Python3.13.2.
Installed config/catalog confirm gpt-6.1-sol/high availability/settings; provider
routing telemetry is not attested. Plan OFF. No production release or next milestone.

## Diagnosis and changes

Historical C11 STARTING cause: **ROOT_CAUSE_NOT_VERIFIED**. Diagnostic C b2be555
reached RECORDING twice (1070/3711ms), so those observations do not reproduce the
old hang or prove a RAM explanation. Its safe trace distinguishes fixture fetch,
decode, AudioContext state/resume, user activation and actual UI state.

Source contained unbounded getUserMedia/resume waits and shared resource cleanup.
Recorder now resumes its own AudioContext synchronously in the explicit record
gesture, owns stream/graph/context per attempt, and bounds start to45s. This
preserves human permission-prompt opportunity; Cancel settles immediately. Late
streams are stopped, late context completion cannot dispose another attempt, and
stale UI completion cannot reset a newer recorder. Failures show recovery/retry.
Track/context interruption saves the captured part once; stale PCM is inert.

Interim f22b347 proved full native voice/save/relaunch, but after relaunch its test
hook could be bypassed: native delegate denied an original media call while no
fixture-requested event occurred. No physical audio was captured in that call.
Forward d151505 installs at document end on wrapper/prototype, verifies and
reinstalls the fixture through fixed LOCAL_TEST menu actions; failure never claims
fixture readiness. Final da2003f additionally scopes the visibility helper in a
closure after a repeated toggle failed on a global lexical redeclaration.
Both native/page physical-denial boundaries remain. No WK `.grant` was added.

Native Quit/update fail closed for unsaved text/audio, STARTING/RECORDING/SAVING,
including hidden producers. LOCAL_TEST never-media/held-save/visibility controls
are mechanism test tools, absent from normal builds. Production update remains OFF.

## Final same-C native proof

- Before fixture opt-in, capture fails; physical-device requests0.
- Never-media Cancel settles; hidden STARTING blocks update before any backup.
  Actual bounded failure reaches IDLE after45093ms with actionable retry text.
  Repeated hidden/show toggle works; all owned contexts close.
- Explicit PCM opt-in/retry reaches real RECORDING, then stop/held SAVING.
  Update refuses in RECORDING and SAVING; Quit refuses during memory-only SAVING.
  No preparatory backup/update began before the refusal gates.
- Released save receives MAC_AUDIO_CONFIRMED:379606 bytes,11.8613125s PCM16/WAV.
  Actual packaged whisper.cpp/small-multilingual finishes TRANSCRIPT_READY in
  5.1315735s, and the result enters an editable native composer.
  LOCAL_AUDIO_SAVED and TRANSCRIBING batch into one React paint; durable audio
  receipt/database confirmation is verified, not a claimed separate screenshot.
- Explicit edit/save receives the server acknowledgement, not an optimistic label.
  Message hash2d06adb6a4b53bfe6c1ab017e5dd35fdd3998e362709c13165c4e7f07c63fd54,
  VOICE_TRANSCRIPT source reference; inference_reference remains null.
- Full Quit/relaunch shows the edited message in history. Fixture after relaunch
  again reaches real RECORDING; Cancel creates no second audio row.
- Signed actual native A141→B142 installs and restarts; edited message/audio/
  transcript persist; installed bundle validates and highwater142 commits.
  Native maintenance remained responsive (26 timer pulses in this observation).
  Real retained A141 is subsequently rejected with UPDATE_IDENTITY_INVALID.
  Test feed and native GUI processes were stopped after verification.

Machine receipts: `reports/evidence/M8F_F01/`; local screenshots/audio/keys/archives
stay ignored. Root700/database600, actual protected APFS/FileVault/no-ACL checks
remain required by unchanged native private profile. Clinical/Health/phone/AI OFF;
five specialist packages CANDIDATE/OFF. No provider calls/new download bytes.

## Verification and preserved failures

Final exact-C Python **1044 PASS**, exit0,337.65s, one existing Starlette deprecation warning.
Web62 PASS (one worker), build A141/B142 PASS, native/packaged Whisper and signed
update PASS. Q03 original authored characterization24 negative/32 positive,
zero live calls; independent schemas7/12/14, admission and qualification PASS.
This is bounded synthetic characterization, not general semantic/clinical safety.
Normal and LOCAL_TEST Swift branches compile/typecheck; strict nested codesign
verification passes. Gatekeeper restricted assessment failed with subsystem
error; one unsandboxed read-only retry rejected the ad-hoc candidate (exit3).
No quarantine/trust policy was changed; production distribution is not verified.

Original f22 full suite:1040 PASS/3 FAIL in1404.58s, three unchanged M4 seven-second
click timeouts. Focused same-C rerun:3 PASS/23.86s; original logs/hashes retained.
Final full suite runs after native/build workloads stop, without assertion/deadline
changes. No causal claim about those transient timeouts is made.
Packaged runner initially failed before runtime because a relative app path was
resolved under its fresh cwd; absolute-path rerun passed actual sandbox/API/Whisper/
backup/restart/restore. Both runner results remain in validation evidence.

Staged public/privacy scan **PASS**, including all local Git objects/staged/unreachable,
public source, snapshots and built UI; manual diff/rights review found only own source/
synthetic mechanism evidence. Heuristics are not proof of absence of all sensitive data.
Docs and regenerated snapshot checks PASS. Binaries, keys, audio and screenshots stay ignored.

## Limits and handoff

Normal macOS TCC/human microphone/UA ASR quality, other Macs/OS/16GB reference,
production signing/notarization/hosting/distribution, real-user/private activation,
clinical review and owner acceptance remain NOT_VERIFIED/NOT_RUN/separate gates.
The prior C8 possible physical-capture incident remains material in historical
M8F evidence. Its authorized exact-root removal was verified absent; this goal
never read or restored C8 content/history, real pilot/vault/backup or credentials.
Past C10 and C11 results retain their original SHA/scope and are not current proof.
Only acknowledged audio/message is durable; pending audio/text remains in memory
and Quit/update guards preserve the chance to save/cancel. OS/process crash is not
proof of draft durability. No new ADR: existing M8F architecture preserved.

STOP AWAITING_REVIEW after evidence-only R/privacy/normal main push and remote
verification. No independent ACCEPT, next milestone, deployment or release.
