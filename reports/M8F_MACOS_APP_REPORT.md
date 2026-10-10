# M8F — standalone macOS engineering candidate

2026-10-10 · **AWAITING_REVIEW / READY_FOR_OWNER_REVIEW_WITH_LIMITS**.
Base `f32038f62e276400c41fb21c76ce753316b7aaa7`.
Final implementation C11 `23bcb16a0d33e4d86377ad60c4fcce216f8c808d`.
Prior C10 `af24526d1a5703dbbb197c5b8487360714c5d92b` retained, not relabeled.
Branch main. R hash is supplied after commit without recursive self-hash. Push NOT_PUSHED
at R formation; normalFF/remote equality verified afterward. CI NOT_CHECKED; no repo workflow.
Actual installed executor GPT-6.1 Sol/High, Plan OFF; push_main permission true independently
merge/deploy/provider/private-data false. Independent M8F ACCEPT is not claimed.

## Центральна відповідь

Реальна arm64 `.app`/`.dmg` з нативним AppKit/WKWebView, власними Python/UI/Whisper існує.
Exact-C11 readonly DMG → fresh disposable Applications → Finder launch, explicit empty-root
onboarding, local core та справжній Sparkle one-click A101→B102 перевірено. B автоматично
стартувала; domain fingerprint/vault identity,2 записи/1 повідомлення/1 authored WAV збережено;
pending clear/highwater102, verified backup/actual restored copy/previous code доступні.
Це **TEST_SIGNED_LOCAL_ONLY** на фактичному M2/8GB/macOS27, не запитаному M2/16GB.

Final full C11:1042 PASS,939.38s,одна existing warning, failure-only observer викликав original
assertions без skips/deadline змін; web53/targeted21 PASS. Попередні standard C10 flakes
не стерті. **C11 native GUI synthetic voice start stuck/canceled — NOT_PASS**; actual packaged
C11 ASR/lifecycle PASS; prior C10 native PCM→Whisper→edit→settled explicit save PASS з власним
SHA. Ці докази не підміняються один одним. Normal OS authentication/physical microphone,
human ASR/старші OS/інші Macs/atomic-swap kill і production distribution залишаються unverified.
Це working engineering candidate для review, не GIRLFRIEND_READY чи whole-product safety ACCEPT.

[Матриця](evidence/M8F/ACCEPTANCE_MATRIX.md), [команди/exit codes](evidence/M8F/VALIDATION.json),
[original failures/інцидент](evidence/M8F/FIRST_RUN_FINDINGS.md),
[контракт](../docs/M8F_CONTRACT.md), [ADR](../docs/adr/ADR-018-M8F-STANDALONE-MACOS.md),
[build/distribution](../docs/M8F_BUILD_AND_DISTRIBUTION.md), [інструкція](../docs/M8F_USER_GUIDE.md).

## Артефакти та реалізація

| Поза Git, тільки локально | Source/build |
|---|---|
| `generated/m8f/development-C11/Personal Companion.app` та `.dmg` | C11/102, DEVELOPMENT/no feed/key |
| `generated/m8f/A/Personal Companion.app` та `.dmg` | C11/101, LOCAL_TEST |
| `generated/m8f/B/Personal Companion.app` та `.dmg` | C11/102, LOCAL_TEST |
| Prior `development`, `A-C10`, `B-C10`, `no-asr` | C10 receipts/history retained |

[Exact manifests/bytes/hashes/12-package inventory](evidence/M8F/ARTIFACTS.json).
Final development DMG SHA256 `8e9b6d3899b2e82fa9d81d3e4850f7ceed53d48f96e134536e6d044cece6d1b1`.
App build contains actual relocated Python3.13.2 executable, stdlib and locked runtime packages,
built React, pinned CPU Whisper/small multilingual and notices. No runtime Node/Git/pip/project
`.venv` or required ChatGPT login. PATH=/var/empty packaged probe/lifecycle passed. No binary
upload/release/tag/deploy or installation into real pilot/another person's Mac occurred.

Native anonymous inherited pipe and ephemeral lexical unlock preserve existing Host/Origin/
CSRF/build/idle/source gates; credentials never URL/args/environment/log. Only127.0.0.1 API.
Nonpersistent WK session; EOF/Quit stops core, only one managed instance. New standalone data
container is outside bundle/Git; no pilot discovery/import. Explicit empty-root consent only;
format4/schema11/typed PRIVATE_LOCAL/FileVault/APFS/owner700/600/no ACL remain. Wrong old
permissions never silently repaired; failed initialization retries only a known empty marker.
No app-level archive-encryption claim; copies use verified FileVault/APFS policy.

C10 moved maintenance to serialized worker/pipe mutex with progress and stable recovery errors.
C11 adds only a Boolean unsaved signal for STARTING/RECORDING/SAVING/in-memory audio draft,
independent of visibility. Legacy panel is hidden in PRIVATE_LOCAL; its collapsed recorder is
characterized in the real Chromium fake-device producer test. Actual native C11 STARTING
refused before backup/pending/feed check. No raw draft crosses the native bridge.
[Guard receipt](evidence/M8F/NATIVE_VOICE_GUARD_C11.json).

Prior UI fixes remain resolved on C11, reviewer bounded disposition **ship**; main-loop pulses91
in actual update, native busy/disabled controls and settled error/recovery visible.
[Continuation review](evidence/M8F/UI_REVIEW_C11.md),
[incumbent design preservation](evidence/M8F/UI_DOCUMENTATION_C11.md).
PRODUCT/DESIGN/styles unchanged; existing schema/sidecar drift not repaired unasked. Verdict
covers the named fixes/integration, not all accessibility sizes, auth, voice quality or distribution.

## Runtime, голос і measurements

[Final actual packaged lifecycle](evidence/M8F/PACKAGED_LIFECYCLE.json): empty initial DB,
daily/creative/search, Free history AI OFF, lock, process restart, real backup and fresh-root
restore with new identity/prior root retained. Actual pinned ASR bytes process only existing
authored synthetic PCM; package sandbox inside sentinel readable, outside read/write/network
rejected. [Licences/locks/SBOM](evidence/M8F/ASSETS_AND_LICENSES.json) bind all inputs/notices.
[Prior C10 no-ASR backend smoke](evidence/M8F/NO_ASR.json) is explicitly prior/source-scoped.

[Prior native C10 voice](evidence/M8F/NATIVE_VOICE.json) records real authored PCM through
recorder, actual Whisper editable text/keyboard edit and durable settled save AI OFF. An early
Quit during pending save was not durable; correct awaited save persisted. C11 GUI simulation
stuck at STARTING twice and was safely canceled; hard physical denial remained. No C11 GUI
capture/ASR PASS inferred from backend or C10. Cycle's authored WAV uses unchanged validated
begin/chunk/finalize domain methods; it is not fake ASR or non-synthetic microphone content.

Actual Mac14,15/M2/8GB/macOS27.0 build26A428/arm64. Target macOS14 declared, not tested;
Intel/M2-16GB/other Macs NOT_VERIFIED. Final packaged bootstrap3064.66ms, initialization2738.51ms,
core start3463.7ms. Post-ASR backend point RSS31,936KiB/CPU12.7%; not whole-app/ASR peak.
Prior C10 native A window6440ms/B12800ms, stressed restart15466ms, retained at own source;
no C11 native latency guarantee. Observed encrypted swap11,322.94MiB; flake causality unproved.

## Update, negatives та recovery

Owner separately approved project-local official Sparkle2.10.0 only; archive SHA256
`c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c` matches official metadata.
Framework verifies ad-hoc/no TeamIdentifier; not DeveloperID publisher authentication.
Fresh independent Ed25519 test key is embedded as public trust; private keys only disposable
files, never Keychain/args/bundle/Git. Normal build has no feed/key/channel enablement.

[Actual C11 update](evidence/M8F/LOCAL_UPDATE.json): one Update, writers/jobs quiesced,
format4 WAL/attachments backup, actual verified restored copy, previous signed code retained,
Sparkle download/stage/copy/swap/autorelaunch.2 notes/1message/1audio and identity unchanged.
[Actual C11 wrong signer/archive tamper](evidence/M8F/SIGNATURE_NEGATIVES.json) rejects unknown
key/modified bytes. [Activation fault](evidence/M8F/ACTIVATION_RECOVERY.json) refuses mismatched
B receipt and really restarts retained A with unchanged DB/highwater. [Keep-data uninstall](evidence/M8F/KEEP_DATA_UNINSTALL.json)
removes only own verified disposable installed B; DB/identity/backup remain, generated apps retained.
[Cleanup](evidence/M8F/CLEANUP_C11.json) closes own test feed; native Quit closes own core/port.

[Prior C10 native truncated download/wrong product/offline/downgrade/concurrency](evidence/M8F/NATIVE_NEGATIVES.json)
retain own source receipts; Python native mechanisms rerun in C11 full suite. Disk-full/restore
failure/schema/replay are fault-injection fixtures, not all GUI executions. Kill during atomic
Sparkle swap NOT_RUN. Future incompatible schema migration blocked until reviewed plan proved
on restored copy; current-schema cycle not general migration proof. Code recovery and fresh-root
data restore are distinct; ordinary downgrade after successful higher build is refused.

## Tests, privacy, rights та incident

[Final C11 validation](evidence/M8F/VALIDATION.json), [original log hashes/statuses](evidence/M8F/TEST_LOG_RECEIPTS.json):
full1042 PASS with unchanged-assertion failure observer; web53 one-worker,21 targeted native/browser,
Swift/web build, packaged lifecycle, actual update/recovery/signatures, independent Ajv7/12/14,
qualification/admission/Q03 PASS in stated scopes. Prior C10 plain full1039 PASS/2 FAIL and focused
unchanged recheck2 PASS retained; original parallel web timeout and diagnostic-import failures
not erased. C11 Q03 first script lacked PYTHONPATH and failed before run; corrected invocation PASS.
No original failure relabeled green; standard prior flakiness and C11 GUI fixture issue remain OPEN.

[Q03 C11](evidence/M8F/Q03_REGRESSION.json):24/24 known bad excluded,32/32 authored positives
released,live calls0. Universal semantic safety OPEN; qualified content/human review NOT_RUN.
Five specialist candidates OFF/runtime_instructions null; clinical/Health/phone/sync/telemetry/
external embeddings OFF; AI unavailable/OFF with no provider factory, credentials or PAYG/fallback.
[External permissions](evidence/M8F/EXTERNAL_PERMISSIONS.json) distinguish scoped local Sparkle
approval from unapproved production/account/data actions. No system installs or new weights.
Pinned MIT engine/weights487,601,967 bytes reused; Python notice includes OpenSSL Apache2/libffi,
12 dist-info/React/Sparkle notices, original icon/authored fixture. Rights/diff inspected.

[Signing assessment](evidence/M8F/SIGNING_READINESS.json): nested deep/strict codesign PASS,
ad-hoc hardened runtime/development library-validation exception, Gatekeeper rejected exit3.
No quarantine bypass; DeveloperID/notarization/stapling/upload NOT_RUN. [Privacy C11](evidence/M8F/PRIVACY_C.json)
scans public source/all local Git objects incl staged/unreachable plus snapshot/built UI; final R
scan repeated. Heuristics are not universal personal-data/security/material-rights proof.

**C8 material scope incident:** physical microphone unexpectedly captured potentially non-synthetic
audio and local ASR ran; possible transcript entered accessibility output. It was not reused as
evidence, uploaded to a provider or committed. Candidate stopped; exact root removed without
file-content reads after explicit scoped owner permission. [Containment](evidence/M8F/INCIDENT_CONTAINMENT.json)
does not erase tool history. Entire run is not called synthetic-only. Owner pilot/vault never
inspected/modified. C9+ native/page physical denial plus authored PCM is the final test boundary;
public R contains metadata only, no raw capture/transcript/key content.

## Gate для реальної передачі

Separate release acceptance, authorized DeveloperID/entitlements, notarization/Gatekeeper,
reviewed production key/channel/host and data-owner consent required. Normal OS auth/physical
mic/human ASR, M2-16GB/older OS/atomic-swap kill remain unverified; C11 GUI simulation issue
needs review before voice acceptance. Recommend approved HTTPS signed downloads/feed; private
authenticated distribution is documented alternative. No service/hosting/activation occurred.
STOP AWAITING_REVIEW; no automatic next milestone.
