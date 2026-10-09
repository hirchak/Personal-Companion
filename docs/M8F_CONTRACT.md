# M8F — standalone native Mac engineering candidate

Authority: [complete goal](../prompts/M8F_MACOS_APP_INSTALLER_UPDATES.md),
[ADR-018](adr/ADR-018-M8F-STANDALONE-MACOS.md). Executor status AWAITING_REVIEW.

| ID | Required behavior | Proof / gate |
|---|---|---|
| F01 | Real arm64 AppKit/WKWebView `.app` and `.dmg` | build_m8f.py; exact-C native smoke |
| F02 | Embedded interpreter/stdlib/exact runtime lock/UI | native manifest and no-dev-PATH probe |
| F03 | Native launch/quit/reopen; one user/root instance | anonymous pipe EOF, OS lock; real Mac |
| F04 | Explicit empty-root consent; no pilot discovery | native-managed container, initialization negative tests |
| F05 | Typed PRIVATE_LOCAL/FileVault/APFS/owner-only intact | reused release/private gates; original synthetic Mac root |
| F06 | Native session redemption without credential URL/log/args | origin-bound ephemeral WK closure; auth/CSRF/build regression |
| F07 | Sleep/session lock, durable entries/history/audio | native lock hooks + exact-C isolated lifecycle |
| F08 | Bundled pinned multilingual Whisper and notices | exact model/engine/licence hashes; packaged isolation/ASR |
| F09 | Recording independent of AI; no auto-send/raw audio provider | existing PCM/local voice contract; native permission + fixtures |
| F10 | Sparkle signed feed/archive before extraction | 2.10.0 pinned download; independent test public key |
| F11 | Product/channel/arch/build/source/manifest anti-rollback | signed item metadata; monotonic managed highwater |
| F12 | Quiesce → WAL/attachments backup → actual copy restore | prepare-update + existing format4; no in-place data rollback |
| F13 | Actual A→B copy/swap/relaunch; data identity preserved | real Sparkle local feed/application, not button mock |
| F14 | Tamper/wrong signer/downgrade/replay/offline fail closed | negative fixtures + actual local Sparkle failures |
| F15 | Failed migration/disk/interruption/concurrency recovery | prior code/verified copy retained; schema changes refused without plan |
| F16 | Backup/explicit fresh-root restore/keep-data uninstall | native menu + release contracts; original root retained |
| F17 | AI optional/default OFF; Q03/clinical/Health/phone preserved | no provider factory/runtime calls; full existing regressions |
| F18 | Exact source/licence/SBOM/scans/C/R/main FF | exact-C checks; evidence-only R; remote equality |

Test trust is separate from production: LOCAL_TEST is a compile-time profile with
a distinct bundle identifier, fresh test public key and fixed disposable home.
DEVELOPMENT has no feed/key and no mechanism to enable unsigned production updates.
Production channel DISABLED; Developer ID, notarization and hosting NOT_RUN/not authorized.
No keys/accounts/system install, autostart, real pilot or next milestone authorization.

PRIVATE_LOCAL test data retains its domain provenance, but every authored record is
ORIGINAL SYNTHETIC. Device-owner LocalAuthentication is exercised only after owner
action in the normal build; test-profile explicit unlock substitutes that OS challenge,
and this substitution must be labeled. A disposable directory is not a new macOS login
account or proof on all Macs. Actual microphone recording/human ASR quality must never
be inferred from authored PCM or a headless browser test.

Future schema changes require a separately reviewed migration plan run on a restored
copy; this release accepts only the current schema11 identity. Startup never silently
updates a different app source without a durable target-bound preparation receipt.
Prior app and backups remain available on installation failure. Successful higher
builds refuse ordinary downgrade; compatible code recovery is separate from fresh
root data restore. Unsaved editor/capture data must be saved before an update.

Build instructions, delivery gates and production signing design:
[M8F_BUILD_AND_DISTRIBUTION](M8F_BUILD_AND_DISTRIBUTION.md).
End-user steps: [M8F_USER_GUIDE](M8F_USER_GUIDE.md).
