# M3 — Safe synthetic runtime contract

Owner goal: [M3_SAFE_RUNTIME](../prompts/M3_SAFE_RUNTIME.md). Base:
`e437de0f41872cbb0c9b0e5b6b940dd781de0735`. External M2 ACCEPT applies only to synthetic
engineering; [durable review](../reports/M2_ARCHITECT_REVIEW.md). M3 ends **AWAITING_REVIEW**.
Runtime/provider/pairing decisions: [ADR-003](adr/ADR-003-M3-RUNTIME.md).

## Working flows

Start the existing loopback synthetic demo; UI starts AI OFF. Save/search/edit/export/sync work
independently. Expand «Помічник і пам’ять», enable **local synthetic mock**, select existing notes,
choose a neutral task and optional confirmed memory. Preview shows every source ID/revision, exact
raw text/type/tags, memory content, model/destination/retention, creative flag, expiry/hash and complete
serialized package. Approval creates one bounded job; result is a proposal requiring another explicit
user decision. Codex candidate remains disabled even in mock mode; no provider activation endpoint.

Capture classification suggests one existing section and allowlisted tags. Organization gives selected
sections with IDs/revisions. Memory proposal gives a neutral response-format preference to review,
never facts extracted from fiction. «Що система пам’ятає» permits local explicit creation, confirmation,
editing, rejection and deletion. Tags/type acceptance leaves raw_text byte-for-byte unchanged; undo
restores structure using another journal revision if no intervening edit. Retained history is explicit.

No shell/file/browser/SQL/git/network tools; no LLM-to-tool execution. Context cannot contain arbitrary
vault access. Every request/response schema forbids extra fields; output wrong source/schema/action,
duplicate JSON keys, oversize, dangerous labels or invalid transition causes no journal/memory effect.
Selected contexts and model suggestions are private synthetic domain data. Jobs contain audit metadata
only; usage UNKNOWN/null, never invented zero tokens/cost. Session binding is hashed, not a stored cookie.

## Acceptance matrix

PASS below refers only to the recorded deterministic synthetic assertions. Full commands/exits/tool
versions/source SHA are in [report](../reports/M3_SAFE_RUNTIME_REPORT.md) and evidence/M3. No self-ACCEPT.

| Gate | Verification | Scope/status |
|---|---|---|
| M3-A01 AI OFF | runtime OFF local CRUD/search/memory, disabled job zero executions; all M1/M2 | Synthetic PASS |
| M3-A02 Exact consent | missing/wrong hash/session, edited/deleted/expired memory/source, revoked/expired approval, provider/task tampering, zero calls | Synthetic PASS |
| M3-A03 Structured boundary | all three valid tasks, malformed/null/array/oversize, duplicate keys, extra shell, unknown task/clinical tags, revision coercion/mismatch; no mutation | Synthetic PASS |
| M3-A04 Lifecycle | queue/run/done/fail/timeout/cancel, foreground unique index, transient success + 3-attempt cap, permanent no retry, restart reapproval, transaction rollback, idempotency | Synthetic PASS |
| M3-A05 No fallback | quota WAITING_PROVIDER, error/disabled stays same provider/model; no PAYG/fallback route | Synthetic PASS |
| M3-A06 Minimization | unrelated journal/creative/memory absent; only explicitly selected fields/confirmed preferences; deterministic ordering/hash; oversize fails without truncation | Synthetic PASS |
| M3-A07 Memory | MODEL_SUGGESTED stays unconfirmed; confirm/edit/reject/delete; provenance/refs preserved, source edit REVIEW_REQUIRED, dependent consent invalidation | Synthetic PASS |
| M3-A08 Reversible structure | accept/edit/reject/ignore/undo; original bytes unchanged; summary source IDs/revisions; dedup reviewed context | Synthetic PASS |
| M3-A09 Injection | hostile note remains raw data; zero shell/network dispatch/provider changes; no runtime tool vocabulary | Synthetic PASS |
| M3-A10 Tool/process | trusted fake executable exact argv/env/cwd, pinning/request tool rejection, unknown path/tool output, malformed/nonzero/limit/timeout/cancel; actual adapter rejects before subprocess | Synthetic boundary PASS; real OS isolation UNVERIFIED |
| M3-A11 Device independence | all M2 browser/domain/web tests retained; actual browser offline capture/reconnect AI OFF; device credential cannot access AI owner API; no automatic AI on MAC_CONFIRMED | Synthetic PASS; Galaxy NOT_RUN |
| M3-A12 Cancel/stale | running cancellation/revocation/source edit/delete/memory edit/OFF prevents result; completed stale proposal blocked | Synthetic PASS |
| M3-A13 Privacy | caplog/job metadata sentinel assertions, provider exception sanitized to code; public worktree/all local Git objects/generated snapshots/built UI scan; manually inspected synthetic screenshots | Synthetic PASS with heuristic-scan limits |
| M3-A14 Actual live | live_provider_calls=false; unconditional candidate rejection; no inference/login/auth inspection | **NOT_RUN / PROVIDER_DISABLED** |

Primary tests: `tests/test_m3_runtime.py`, `test_m3_api.py`, `test_m3_process.py`, `test_m3_browser.py`;
M2-N01 additionally in `apps/web/tests/phone-store.test.ts`. M1/M2 suites remain part of full target.
Browser M3 uses actual built React/loopback HTTP/SQLite/IndexedDB/native WebCrypto, synthetic notes.

## M2-N01 forward fix

Server response commits PENDING only; local encrypted commit failure sends no finalize, so sync is
denied. Owner UI lists/revokes pending state. Recovery: fresh one-use invite replaces credential; or,
if local encrypted credential did commit but confirmation response was lost, foreground sync repeats
idempotent finalize. Pending expires in five minutes; old invitation/token replay is denied. Tests cover
SQLite commit failure, browser IDB write failure after real server response, retry/restart/revoke/expiry,
lost response and actual encrypted persisted state. No credentials in logs/screenshots/public evidence.

## Budgets and recovery

24,000 bytes max canonical context, 8,000 bytes max output, 20 selected entries/10 memory refs;
mandatory rules/sources never silently truncated. 300-second exact approval, one job per consent,
2-second total timeout, ≤3 transient attempts. One foreground SQLite slot. No endless poll/retry or
provider failover. Process restart starts OFF and fails queued/running jobs with RESTART_REAPPROVAL_REQUIRED;
new preview required. Cancel/off/dependency triggers plus final transaction check prevent late apply.
SQLite transaction/receipt idempotency protects domain effects and accepted structure. Schema 3 synthetic
migration/rollback/preupgrade snapshot and schema-2 backup restore preserve earlier journal/sync wire v2.

## Deferred gates

No actual Galaxy/Tailscale/private HTTPS, hardware Keystore claim, real vault, real provider/auth/
subscription isolation/retention, clinical content, microphone/watch/health, publishing/deploy, M4+.
Fake child has ambient same-user OS authority; it is a hash-pinned trusted test fixture, not proof of
filesystem/network sandboxing. Codex runtime candidate remains disabled until separately authorized
and verified. Consent does not turn M3 synthetic acceptance into real-data or clinical approval.
