# M4 — Local voice capture, offline audio and editable ASR transcript

Owner execution goal issued 2026-10-01. Base/main: `40b33a05248353b910acf733db99e21242ee0bd2`.
External M3 synthetic engineering ACCEPT: `reports/M3_ARCHITECT_REVIEW.md`.

## Owner specification received — all 29 sections

Final owner message supplied section 21 and sections 22–29. Complete specification received.
The requirements below preserve the full implementation and acceptance scope.

## Required engineering scope

- Ukrainian Mac/phone capture: mic/start/elapsed/pause where reliable/stop/cancel, honest local
  durability, Mac queue/upload progress, transcription queue/run/failure and editable candidate.
  Durability starts only after committed local transaction; in-memory capture can be lost on crash.
  Permission denial/start failure/ended track/reload/background interruptions tested; no background promise.
- PRIVATE_PERSONAL audio, opaque IDs/hash/format/duration/size/UTC/timezone/local date/source/state/
  transcript/retention metadata. No real recordings in Git/logs, voice profiling or clinical inference.
- Phone application AES-GCM encryption, separate bounded blobs/chunks rather than whole journal
  rewrites; atomic integrity binding to upload operation. No raw audio/credentials in Web Storage,
  Cache API or plaintext IDB metadata. Offline save/reopen/upload. Write/quota failure retains memory
  draft with explicit retry/export/discard; storage eviction caveat remains.
- Private synthetic Mac attachment root outside Git: staged fsynced writes, checksums, atomic
  finalize, restrictive permissions, opaque paths, DB/file consistency, crash/restart and interrupted
  cleanup/resume/idempotency. Reject unknown/symlink/Git paths and unverified corrupted files.
  No unverified filesystem encryption claim.
- M2 authenticated device audio transfer: bounded chunks/resume, deterministic order/idempotent
  retry/checksums/durable final receipt/cancel/restart, revoked/old epoch blocked, token only headers,
  explicit total/body limits, no client filesystem destination or expanded network exposure.
- Narrow local ASR identity/model/hash/language/availability/input/transcribe/cancel/timing/error.
  DisabledLocalASR + deterministic FakeLocalASR if real model unavailable. Trusted fake executable
  exercises exact argv/no shell/sanitized env/controlled paths/deadline/process-group cleanup/bounded
  stdout+stderr. Same-user CLI is not proof of isolation/local inference; no endpoint/cloud fallback.
  Real engine args cannot be invented. No backend/model download/build without scoped permission.
- Explicit parsable format/normalization boundary; no implicit global ffmpeg dependency. Validate
  MIME/format/sample rate/channels/duration/bytes/zero/truncation/malformed input. Converter abstraction
  and synthetic fixtures when needed; unrun codec/backend paths honestly NOT_RUN.
- Audio original → separate ASR candidate → edited/confirmed transcript → journal note, provenance
  preserved. Store transcript/audio/hash/engine/model/language/candidate/edit/status/timestamps/
  journal revision/error. Explicit edit/confirm/retry/cancel/discard/retention; never overwrite a raw
  journal note automatically. Keep M3 exact selection/preview/consent; audio excluded from AI context.
- Silence/low-energy/noise/empty/implausible outputs get deterministic engineering checks and clear
  nothing-recognized/review-text handling; no automatic meaningful note/tasks/memory/send/publication.
- Retention KEEP / DELETE_AFTER_CONFIRM / DELETE_NOW with confirmation. No silent original deletion
  before required Mac durable receipt, transcript availability and explicit user retention action.
  Delete active metadata/derived state/jobs/attachment/locally requested phone copy; offline/revoked
  erase not guaranteed; backups/snapshots may retain bytes, no forensic secure erase claim.
- Consistent DB+attachment-manifest/checksum/schema/app-version/atomic backup; restore verifies DB,
  manifest/files/hashes/schema/references/no traversal/symlinks before active mutation. Prior schema
  backup/migration regressions remain supported.
- Existing neutral responsive accessible UI; labels/keyboard/44px phone targets/no overflow; main
  flow is simple recording/review, not audio debugging. Synthetic Chromium fake media tests only.
- Manual Galaxy S24 Ultra runbook: secure private origin, OS/Chrome, permission/start/stop/screen
  lock/app switch/interruption/offline/save/force-close/reopen/reconnect/review/retention. Actual
  Galaxy HARDWARE_UNVERIFIED/NOT_RUN unless run with separate scoped rollout permission.
- Separate real-ASR runbook: genuinely local engine+multilingual model, verified source/license/hash,
  project-local path and exact permissions; no unverified model size/performance estimates. Real
  model NOT_RUN/PERMISSION_REQUIRED when unavailable; never claim fake proves real inference.
- Ukrainian benchmark only if real backend available: synthetic/cleared clear speech/silence/noise/
  short phrase, reference transcript, wall time/duration/RTF/WER/CER/RSS/model hash. Synthetic/TTS
  not human accuracy evidence; HUMAN_UA_QUALITY NOT_RUN when no cleared human material.

## Minimum acceptance mapping supplied so far

A01 durability; A02 no fake save; A03 authenticated resumable single attachment;
A04 revoke/epoch; A05 malformed/hash/duplicate/path integrity; A06 process boundary cases;
A07 separate edit/confirm/provenance; A08 silence/noise; A09 cancel/no late apply/restart;
A10 explicit retention/no premature phone delete; A11 attachment backup/restore;
A12 privacy/AI independence; A13 all earlier regressions; A14 actual model separately
LOCAL_ASR_BACKEND_NOT_RUN; A15 actual Galaxy gate HARDWARE_UNVERIFIED / NOT_RUN unless actually run.

Synthetic-only; no cloud/provider calls or system installs. No new model/engine downloads/builds,
private user data, clinical protocols, deployment or M5+. Normal verified C/R main push authorized.

## Sections 22–29: validation, evidence and completion

- Keep all M1/M2/M3 tests; add domain/storage/crash/transfer/retry/encrypted-phone/browser fake mic/
  ASR-process/cancel/timeout/silence/noise/edit/confirm/retention/backup/privacy checks, real SQLite,
  built React and actual synthetic Chromium. No real-user voice fixtures.
- Measure synthetic encryption/write latency, loopback chunk throughput/latency, finalize/hash time,
  fake ASR lifecycle, attachment disk bytes/DB metadata growth/idle CPU-memory where possible.
  Actual ASR separately if run; no Galaxy/cloud/token/cost numbers or invented metrics.
- Privacy scan includes Git objects, generated context, built UI and retained synthetic screenshots;
  no raw/private recordings, model weights, DB/IDB data, auth/cert keys or private filesystem paths.
  Audio artifacts generated in ignored/generated/temp, never committed.
- Do not open R01_RAW.docx/R02_RAW.docx/R03_RAW.docx or implement R04/clinical protocols.
- Durable M3 review, M4 contract, audio/ASR ADR, real-ASR follow-up and Galaxy mic runbooks,
  reports/M4_LOCAL_VOICE_ASR_REPORT.md, reports/evidence/M4, STATE/HANDOFF/roadmap/devlog/
  regenerated snapshots. No unrelated Impeccable/init migration.
- Final implementation C; exact-C suite/build/browser/privacy; code fixes require new final C and
  relevant rerun; evidence-only R; verify C→R no implementation changes; privacy scan; normal
  fast-forward main push; verify origin/main==R; stop. No review branch/rewrite/force/M5.
- DoD: complete working pipeline, A01–A13 synthetic PASS, A14 actual backend PASS or honest
  LOCAL_ASR_BACKEND_NOT_RUN, A15 real Galaxy PASS or HARDWARE_UNVERIFIED/NOT_RUN;
  relevant checks PASS or exact blocker, C/R pushed and remote verified, all private/cloud/clinical/
  Health/M5+ gates OFF. M4 AWAITING_REVIEW, never self-ACCEPTED.
- Final concise handoff: base/final C/R/origin SHA, M4 status, Python/web/browser counts/privacy,
  capture/ASR pipeline and actual model executed? engine/model/hash only if run, UA benchmark,
  A14/A15/CI, exact demo and synthetic browser/mic commands, remaining blockers/permissions.

## Execution plan

1. Read the M1/M2 storage/sync and M3 integration contracts needed for M4; inspect installed
   local ASR tooling without private data and define M4 acceptance mapping/architecture.
2. Implement Mac attachment/recovery and resumable authenticated transfer, encrypted phone
   persistence and recording UI, bounded ASR and explicit editable transcript confirmation.
3. Run synthetic domain/storage/API/browser/offline/failure/regression checks and fix failures.
4. Update contracts/state/handoff/roadmap/devlog/report/snapshot; privacy and exact-diff checks;
   create implementation C and evidence-only R, normal fast-forward push main and verify receipt.
