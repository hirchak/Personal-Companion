# M8F bounded acceptance matrix

Exact implementation C11: 23bcb16a0d33e4d86377ad60c4fcce216f8c808d.
Executor status AWAITING_REVIEW; no independent product/release ACCEPT claimed.

| Contract | Result | Evidence and practical boundary |
|---|---|---|
| F01 native app/DMG | PASS_LOCAL | Actual arm64 AppKit/WKWebView app; readonly DMG → disposable Applications → Finder launch. Actual M2/8GB/macOS27; requested16GB and other Macs NOT_VERIFIED. |
| F02 embedded runtime | PASS | Relocated Python3.13.2, stdlib,12 pinned packages, built React assets. Anonymous-pipe lifecycle with PATH=/var/empty; no developer Python/Node/Git required at runtime. |
| F03 launch/quit/instance | PASS_BOUNDED | Actual native launch/relaunch, scoped EOF/Quit and closed port; actual second embedded process ALREADY_RUNNING. Dock/minimum-size/VoiceOver breadth not fully verified. |
| F04 first-run consent | PASS_TEST_PROFILE | Explicit GUI consent → empty SQLite; no import/discovery; retry only known empty failed initialization. Test OS unlock substitutes LocalAuthentication; normal OS authentication NOT_RUN. |
| F05 private root protection | PASS_ORIGINAL_SYNTHETIC | Actual FileVault/APFS + owner700/600; prior permissions not repaired. No owner-pilot/vault access. Whole-run synthetic-only claim prohibited by contained C8 incident. |
| F06 authenticated native session | PASS | Inherited pipe/ephemeral lexical code; no secret URL/args/log. Existing Host/Origin/CSRF/build gates regressed. |
| F07 local durability/lock | PASS_BOUNDED | Native lock and actual process restart/restore; entries/search/creative/Free history AI OFF; full synthetic Free/Deep regressions. Actual OS sleep/wake challenge NOT_RUN; source hooks not mislabeled hardware proof. |
| F08 packaged Whisper | PASS_PACKAGED | Actual pinned CPU engine + small multilingual bytes/notices; real ASR plus inside/outside read/write/network sandbox sentinels. Human/noisy-speech quality OPEN. |
| F09 voice/edit/send | PARTIAL_GUI_VOICE_C11 | Prior C10 native PCM/edit/save PASS retained at own source. C11 GUI start stuck/canceled NOT_PASS; actual packaged C11 ASR PASS, native STARTING guard PASS; controlled authored WAV preserved A→B. Physical TCC/human quality NOT_RUN. |
| F10 supported signed updater | PASS_TEST_SIGNED_LOCAL_ONLY | Actual Sparkle2.10.0 signed feed/archive, independently embedded ephemeral test public key; normal build has no channel/key. Upstream framework signature ad-hoc, not DeveloperID publisher authentication. |
| F11 identity/antirollback | PASS_BOUNDED | Real wrong-product/downgrade feed checks; unit wrong arch/channel/schema/replay/hash guards. Signed target identity rechecked at activation; higher successful builds refuse ordinary downgrade. |
| F12 preupdate backup | PASS | Stop writers/jobs → real format4 WAL/attachments backup → verified actual restored copy → retained prior signed code. Future incompatible schema blocked until reviewed plan. |
| F13 one-click A→B | PASS_REAL_SPARKLE | A101→B102 actual download/stage/copy/swap/autorelaunch;2 entries/1 message/1 audio and vault identity preserved; pending cleared/highwater102. Same exact C, distinct build identities. |
| F14 failed/tampered/offline updates | PASS_BOUNDED | Actual wrong signer, signed wrong product, truncated download and offline feed retain old app/data; real archive verifier rejects modified bytes/wrong key. Not all negative fixtures are native GUI executions. |
| F15 recovery/disk/migration/interruption | PASS_FAULT_INJECTION_WITH_LIMITS | Disk-full/restore failure unit guards; real packaged wrong target receipt refuses B activation and retained A restarts without DB change. Kill during atomic Sparkle swap NOT_RUN; no destructive data rollback or incompatible migration claimed. |
| F16 backup/restore/uninstall | PASS | Actual native backup; actual packaged fresh-root restore with renewed identity and prior root retained; remove only verified disposable installed apps, keep DB/identity/3 backups. |
| F17 AI/Q03/flags | PASS_BOUNDED_WITH_REGRESSION_FLAKES | No provider factory/live calls;24 known bad excluded/32 positives released.5 specialists/clinical/Health/phone OFF; semantic safety/qualified review OPEN. Final C11 full1042 PASS with failure-only observer; web53/targeted21 PASS. Prior C10 standard full flakes retained OPEN. |
| F18 source/artifacts/rights/scans/C/R | LOCAL_C_PASS_R_DELIVERY | Exact manifests/asset/lock/notices and public-source/all-local-Git-object checks. Evidence-only R/normalFF/remote equality finalized after commit; CI NOT_CHECKED. No binary upload/tag/release/deploy. |

Distribution: BLOCKED independently by DeveloperID/signing policy, notarization/stapling,
approved production key/channel/host, clean-Mac release acceptance and data-owner consent.
Requested16GB host, older supported OS, normal auth/physical microphone/human ASR quality and
atomic-swap kill coverage remain unverified. These gates are not closed by test signatures,
synthetic fixtures, UI ship verdict or source main push. Not GIRLFRIEND_READY.
