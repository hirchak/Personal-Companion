# M4 — Local voice, encrypted offline audio and editable transcript contract

Owner scope: [complete goal](../prompts/M4_LOCAL_VOICE.md), base
`40b33a05248353b910acf733db99e21242ee0bd2`. External M3 synthetic ACCEPT:
[review record](../reports/M3_ARCHITECT_REVIEW.md). M4 is an engineering candidate for independent
review; it is never self-ACCEPTED. Only synthetic data, loopback runtime and generated fake microphone.

## Data and durability

Audio is PRIVATE_PERSONAL. Browser capture emits mono PCM16 WAV at 16 kHz, at most 120 seconds.
No cloud speech, global codec dependency or voice/acoustic wellbeing inference. The explicit Python
PCM boundary validates RIFF length, MIME, PCM width/channels, rate (16/24/44.1/48 kHz), exact frame
length, minimum .25 seconds, maximum 120 seconds and 8 MiB. Unsupported formats are rejected;
other codecs and actual engine-specific normalization remain NOT_RUN. Capture itself provides
16 kHz directly. Silent/very low-energy PCM (<.004 normalized RMS) skips ASR and returns
NOTHING_RECOGNIZED. This is a deliberately simple engineering heuristic, not VAD. Audible noise
can still yield an untrusted candidate; every candidate requires user review and explicit confirmation.

Phone physical IndexedDB version 3 adds separate `audio`/`audioChunks` stores. Journal encryption
format/schema stays 2; existing migrations remain explicit. Every audio has immutable encrypted
chunks and an encrypted metadata/upload operation in one atomic transaction. Public envelope
fields are revision/IV/ciphertext and opaque keys; hashes, MIME, timestamps, transcript, receipt,
retention and operation are inside AES-GCM. AAD binds device/salt/audio ID/hash/chunk index or
metadata revision. Fresh random nonces, unlocked M2 key, no durable plaintext key/credential.
Chunk save does not rewrite the journal envelope. Metadata updates use revision CAS; swapped
chunks/IDs or altered hashes fail authenticated integrity checks.

LOCAL_AUDIO_SAVED begins after IDB transaction completion. Failed quota/write has no partial
metadata/chunks and retains current in-memory bytes for retry, encrypted rescue export or discard.
Encrypted rescue can be imported explicitly with its original passphrase into an unlocked store,
creating a new local audio copy without restoring credentials. Journal recovery and audio export
are separate. Browser eviction can remove either; neither storage persistence nor background
recording/sync is guaranteed. Reload/crash before durable save can lose current capture. Permission,
start failure, ended track and background transition have explicit paths; background stops capture
and attempts to save its available segment. Pause excludes paused samples/time.

Mac SQLite schema 4 migrates schema 2/3 transactionally with preupgrade DB snapshot/rollback.
Audio lives under the explicitly marked synthetic root outside Git: `audio/<UUID>.wav` and
`audio-staging/<UUID>/<index>.part`. Root/directories 0700, files 0600. Staging/final writes fsync
file and directory, verify content, then atomic rename; DB final state commits after durable file.
A lost response repeats without duplicate effect. Crash after rename/before DB commit is recovered
by hash+format validation. Missing/corrupted confirmed files become FAILED; incomplete invalid
chunks are removed and retried from the first missing index; orphan staging/final files in the
owned synthetic root are cleaned. Unknown roots/content, symlinks and Git paths are rejected.
No claim of filesystem encryption or OS sandboxing follows from permissions/synthetic markers.

## Transfer and authority

Owner session+CSRF routes `/api/v1/voice`; phone routes `/api/v1/device/voice` use M2 active pairing,
Bearer header, opaque device ID header and epoch header. Authentication is rechecked inside each
transaction, including finalization. Other-device audio, revoked device and old epoch cannot be
read/uploaded/finalized/replayed. Normal re-pair/reconciliation precedes an explicit new audio copy;
old-epoch audio IDs are never silently reused. Header credentials only, query strings rejected.

Chunks are exactly 256 KiB except the last, total at most 8 MiB/32 chunks, canonical ascending
index, per-chunk SHA-256 and final SHA-256. Repeating an identical committed chunk is idempotent;
conflicting duplicate/order/length fails. Voice request body max 400,000 bytes; strict schemas forbid
client destination paths/extra fields. At most 100 active uploading/finalized recordings. There is
no LAN/Tailscale/certificate/deploy change. Cancellation persists a terminal server state and removes
staging. A finalize that already committed precedes cancellation; it remains a saved attachment
requiring explicit deletion. Phone upload fails/retries with its original encrypted bytes retained;
no silent deletion after receipt. A late finalize response after local cancellation does not automatically
apply to phone state; an explicit Mac status check can reconcile a finalize that committed first.
An explicit check also shows Mac deletion while preserving the phone copy. A local offline cancellation
cannot guarantee remote erasure.

## ASR and journal authority

DisabledLocalASR is default and exposes LOCAL_ASR_BACKEND_NOT_RUN. FakeLocalASR requires an
explicit UI checkbox and returns labeled deterministic synthetic text, never an accuracy claim.
One persistent queued/running ASR job; restart turns unfinished jobs into FAILED requiring explicit
retry. State: TRANSCRIPTION_QUEUED → TRANSCRIBING → TRANSCRIPT_READY / FAILED / CANCELLED.
Late/cancelled/deleted/revoked/timeout results cannot apply. Bounded output accepts only text/language,
UTF-8/plain data; tools/paths/extra actions rejected. All candidates are untrusted text, never commands.

The hash-pinned trusted fake ProcessLocalASR exercises exact absolute argv, isolated Python flags,
no shell, fresh controlled input/cwd, sanitized environment, timeout, cancellation, process-group
SIGKILL and separate bounded stdout/stderr (12,000 bytes each). Host Python/macOS may add locale
variables; provider/auth/HOME/PATH/Git variables are not inherited. Fixed `input.wav`, no user paths.
This verifies process mechanics with a trusted fixture; it does not prove hostile executable isolation,
filesystem/network denial or actual local model inference. Real activation requires inspected executable
flags/output contract, pinned model/license/checksum and separate isolation verification; see runbook.
No whisper CLI flags are asserted from an unavailable executable. No cloud fallback exists.

Audio original → transcript candidate → separately edited text/revision → explicit confirmed journal
entry. Transcript stores audio hash, engine/model/hash if known, requested/result language, candidate,
edited text, status/revision/timestamps/error/timing and confirmed entry/revision. Explicit save-edit,
confirm, retry, cancel/discard and retention are supported. Journal create/edit plus provenance commits
in one transaction, preserving existing note revision on explicit edit; exact repeated confirmation is
idempotent. Candidate cannot silently overwrite a journal entry. Confirmed notes use normal M1/M2
behavior. M3 jobs/memory/context never run automatically; raw audio never enters M3 context. Only a
later independent explicit selection+preview+consent can send confirmed journal text to M3 mock.

## Retention and consistent maintenance

KEEP is default. DELETE_AFTER_CONFIRM is explicit and requires verified Mac audio and a ready
transcript; confirmation commits before deletion. DELETE_NOW requires a user confirmation, cancels
active ASR and removes attachment/staging/chunk refs/active derived transcript state. A completed
journal note remains user content. Delete-after-confirm preserves confirmed candidate/edit provenance
against a deleted-audio tombstone. Phone delete-after-confirm requires both stored durable receipt and
confirmed transcript. Separate explicit phone-only deletion works offline and does not promise Mac
job/file/backup deletion. Offline/revoked devices cannot be remotely erased; no forensic secure erase.

Backup format 2: SQLite consistent snapshot + exact finalized-audio manifest (UUID/hash/size) + DB
checksum/schema/app version; staged output atomically finalized. Attachment mutation/backup share
an in-process lock; snapshot files are verified, fsynced and copied with checksums. Incomplete upload
staging is excluded and marked CANCELLED in the backup, not represented as a complete recording.
Restore validates DB, manifest equality against DB refs, exact files, hashes, formats, schema and
no traversal/symlink before creating a new empty target. Damaged backups leave active data untouched.
Legacy schema 2/3 format-1 no-attachment backups remain supported; no live vault migration.
Device credentials are sanitized/revoked and M3 consent/unfinished ASR require reapproval/retry.

## Acceptance map

Final exact-C results and counts live in the [M4 report](../reports/M4_LOCAL_VOICE_ASR_REPORT.md)
and its evidence, not inferred from this matrix or mock success.

| Gate | Authoritative synthetic verification |
|---|---|
| M4-A01 | test_m4_voice restart/chunk/final file tests; test_m4_browser Mac capture/reload + persistent phone offline close/reopen |
| M4-A02 | SQLite commit-failure recovery; phone-audio atomic quota test; actual browser quota/retry/encrypted export |
| M4-A03 | multi-chunk restart/idempotency/domain; encrypted client interrupted resume; browser real HTTP chunk response lost/retry |
| M4-A04 | domain revoke/epoch/other-device/new-epoch repair + actual HTTP device denial |
| M4-A05 | PCM/MIME/size/truncation/order/hash/duplicate/path/schema/symlink/backup validation |
| M4-A06 | test_m4_process valid/environment/nonzero/malformed/stdout/stderr/timeout/cancel/children/tool/path/hash; late deadline test |
| M4-A07 | candidate/edit/confirm/idempotency/provenance/revision tests + built React Mac/phone review/confirm |
| M4-A08 | silence/low-energy/high-energy noise tests; fake silent microphone produces no note |
| M4-A09 | upload terminal cancel, queued/running/restart/late-result/delete tests; recording cancel/interruptions |
| M4-A10 | keep/delete-after-confirm/delete-now, active ASR delete, phone retention gates and explicit delete browser |
| M4-A11 | DB+audio backup/restore; missing/corrupt/manifest/traversal/symlink/reference failures; old migrations/backups |
| M4-A12 | no automatic M3 jobs/provider executions; synthetic-only fixtures/screenshots/public-data+Git-object scans |
| M4-A13 | complete existing M1/M2/M3 suites and current contract/schema/build checks |
| M4-A14 | LOCAL_ASR_BACKEND_NOT_RUN, REAL_LOCAL_ASR_MODEL NOT_RUN / PERMISSION_REQUIRED |
| M4-A15 | Galaxy S24 Ultra HARDWARE_UNVERIFIED / NOT_RUN; manual microphone runbook |

Audio/ASR choices: [ADR](adr/ADR-004-M4-AUDIO.md). Follow-up:
[real ASR](M4_LOCAL_ASR_RUNBOOK.md), [Galaxy](M4_ANDROID_MIC_GATE.md).
