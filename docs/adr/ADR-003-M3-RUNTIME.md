# ADR-003 — Synthetic runtime, exact consent and pending pairing

Date: 2026-10-01. Status: implemented engineering decision; M3 AWAITING_REVIEW.
Scope: modular monolith, synthetic data, no live provider permission.

## Decisions

1. SQLite schema 3 adds consents, metadata-only jobs, validated suggestions and memory. Journal
   entry/sync wire schema stays 2. Existing synthetic schema 2 migrates transactionally after a
   preupgrade snapshot; old schema-2 backups restore then migrate. No real vault migration.
2. The runtime starts OFF on every process start. Owner UI can enable only the local deterministic
   mock. A narrow Provider protocol accepts data-only context, cancellation signal/deadline and
   returns bounded JSON. No tool dispatch, credential discovery, file/browser/SQL/git/HTTP access.
3. `DisabledCodex` is a candidate contract. It rejects unconditionally before any process. There
   are no actual CLI command/flags/model/auth claims or inspected credentials. OS filesystem and
   network isolation for a real subprocess is UNVERIFIED. Activating it requires a new scoped live
   goal, verified provider terms/auth/destination/retention and actual isolation. M3-A14 NOT_RUN.
4. The hash-pinned FakeProcessProvider is a trusted fixture harness, not a deployable provider or
   sandbox. No HTTP/config registration. Exact Python `-I -S` argv, no shell, isolated temp cwd,
   environment allowlist, capped stdin/stdout, process-group kill, timeout/cancel/nonzero handling.
   Unknown path/tool outputs are rejected by schema; same-user OS authority is NOT proven safe.
5. Context is canonical JSON, 24,000-byte budget; no truncation. Includes explicitly selected
   IDs/revisions, raw text/type/tags, explicitly selected confirmed preferences, neutral constraints,
   schema/task/provider identity, approval scope/consent ID/expiry. Dynamic consent ID/expiry mean
   different previews have different hashes; serialization of the same immutable package is stable.
   Every field delivered is shown in full-package UI. Byte/character sizes are estimates, not tokens.
6. Consent is one job, one exact package/provider/task, 300 seconds and a hashed owner session
   identity. Validation happens on approve/enqueue/dispatch/retry/result/user acceptance. Changes
   revoke dependent consents, cancel queued/running jobs and mark pending proposals STALE via
   SQLite triggers, including sync/CLI edits. No phone sync can enqueue AI.
7. A single DB foreground slot + bounded on-demand thread: total 2-second default deadline,
   maximum three attempts for TRANSIENT_UNAVAILABLE only. Quota/error never selects another model
   or billing route. Waiting/disabled/failed jobs remain explicit; retry needs a new preview/approval.
   Restart marks interrupted work FAILED and revokes approvals; no unattended replay. Idle has no
   polling worker. Mock/trusted fixture operations are bounded; arbitrary Python providers are not
   accepted from configuration. A future untrusted live adapter must be process-isolated.
8. Output schemas contain neutral allowlisted types/tags/groups/preferences and exact source refs,
   not arbitrary commands or narrative psychological inference. Duplicate keys, unknown fields,
   clinical labels, wrong revisions/tasks/groups and >8,000 bytes fail before domain effects.
9. Original text, validated pending output and accepted structure remain separate. Classification
   acceptance uses Journal.write_in transaction/revision history. Undo restores earlier structure
   only if the accepted revision is current. Rejected/ignored same-context/model/version proposals
   are suppressed; changed source revisions allow a fresh explicit proposal. Organization is a
   selected-section summary with source refs, not invented free-text interpretation.
10. Memory starts MODEL_SUGGESTED for model output. Explicit confirmation changes status, retains
    MODEL_SUGGESTED provenance and source refs. User editing records USER_EDITED, detaches active
    source dependency; immutable originating job/suggestion preserves original refs. Source edits
    mark unedited model memory REVIEW_REQUIRED. Reject/delete invalidates downstream packages/jobs.
    Creative input is never accepted for memory_propose. Manual owner preferences are USER_ENTERED.
11. M2-N01: invitation atomically creates PENDING hashed device credential with five-minute deadline.
    It cannot sync. Phone encrypts/commits credential before sending authenticated idempotent finalize.
    Local write failure leaves visible/revocable PENDING state; fresh owner invitation replaces it.
    Lost confirmation response is recoverable from encrypted state; foreground sync re-confirms.
    Revocation/epoch/restore/replay semantics remain enforced. Existing active schema-2 devices remain
    active on migration. No server plaintext credential persistence or logging.

## Limits

Synthetic mock proves deterministic engineering boundaries, not model safety, real-provider latency,
retention/auth/subscription terms or OS sandboxing. Exact selected source content exists only in the
explicit synthetic SQLite private context tables, never generic jobs/devlogs. SQLite backups retain
private context/suggestion data but strip device credentials and revoke consent; no secure-erasure
claim. Galaxy/Android hardware storage and private HTTPS/Tailscale remain HARDWARE_UNVERIFIED.
Clinical/research/voice/health/deploy/M4+ remain OFF. No arbitrary assistant chat or therapy added.
