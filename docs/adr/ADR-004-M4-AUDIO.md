# ADR-004 — M4 PCM capture, private attachment consistency and local ASR gate

Status: implementation decision within owner M4 synthetic engineering scope, 2026-10-01.
No clinical/runtime/provider/real-device authority follows from this decision.

Browser MediaRecorder codecs vary and would otherwise require a new codec/backend download.
Use existing Web Audio mono capture with bounded ScriptProcessor input and local PCM16 WAV
resampling to 16 kHz. This deprecated but available browser API is exercised on actual synthetic
Chromium; real Samsung/browser lifecycle is a separate gate. Pause skips samples; ended track or
background transition stops capture and attempts to save the available segment. Maximum 120 seconds.
No recording/background guarantee or arbitrary codec import. PCM parser is a separate explicit
converter boundary; no implicit ffmpeg dependency despite an installed binary being discoverable.

Phone separates ciphertext chunks from encrypted per-audio metadata, with AAD binding and one IDB
save transaction. Journal format 2 remains unchanged; physical DB 3 only adds stores. Exported audio
rescue uses the existing unlocked key and authenticated envelope; import is explicit and creates a new
copy, never credentials or hidden reconciliation. Phone cancellation/erasure is not a remote guarantee.

Mac schema 4 uses staged bounded chunks and per-chunk DB receipts. Hash+PCM validation precede
fsynced atomic file rename, followed by DB final state. Filesystem and SQLite cannot share one atomic
commit; deterministic startup recovery reconciles both directions and refuses corrupt confirmation.
Mutation/backup share a root lock in this process. This is a loopback synthetic single-service design,
not a distributed filesystem lock or a hostile-local-user sandbox. Backup copies finalized audio
with exact manifest/DB refs; old format-1 schema 2/3 snapshots remain supported. Upload staging is
not claimed as a completed backup original. Actual OS filesystem encryption remains unverified.

Default ASR is DisabledLocalASR. Explicit fake mode validates the full UX and lifecycle; a hash-pinned
trusted fake process validates argv/env/cwd/input/deadline/output/cancel/group cleanup. No installed
ASR executable or repo model was found in the bounded allowed inspection. Do not download/build an
engine/model or substitute cloud inference. Real activation requires owner-scoped permission, verified
source/license/checksum/argv and environment/egress isolation. Same-user CLI and sanitized env alone
cannot prove network/filesystem confinement. Real ASR and human Ukrainian accuracy remain NOT_RUN.

Preserve candidate text separately from edit and confirmed note/revision. Confirmation is transactional
and explicit; raw audio never enters M3 context. Low-energy blocks recognition; audible noise can still
produce a candidate and always requires review. This is not acoustic health inference or medical VAD.

References: [M4 contract](../M4_CONTRACT.md), [owner goal](../../prompts/M4_LOCAL_VOICE.md).
