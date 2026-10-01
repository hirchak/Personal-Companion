# M2 — encrypted offline PWA/sync engineering candidate

Дата: 2026-10-01. Synthetic scope only. **AWAITING_REVIEW**; не private rollout/clinical approval.

| Ref / status | Value |
|---|---|
| Repository / branch | hirchak/Personal-Companion, main |
| Base M2 / externally accepted M1 R | b4c8af5f975e1a92c6d06fd023b82155cae6fc73 |
| Final implementation C | 67cb03969d344fe37f45f1d97d021405bea6b126 |
| R | Next evidence-only commit; exact R and post-push remote receipt in final handoff, no self-hash |
| Push checkpoint | PRE_PUSH, normal fast-forward allowed by owner + permissions.push_main=true |
| CI | NOT_RUN; no new workflows/runners/secrets |
| Actual Galaxy S24 Ultra / real transport | HARDWARE_UNVERIFIED / NOT_RUN |
| Real data / hardware secure storage | NOT_APPROVED / HARDWARE_SECURITY_UNVERIFIED |
| AI/health/watch/ASR/deploy/system trust/remote access/M3+ | OFF, not activated |

## Implementation

[M1 external review](M1_ARCHITECT_REVIEW.md) records owner-provided architect ACCEPT on exact
M1 C/R, with synthetic/engineering limitations, not self-approval. M1 default list now sorts
(created,id) descending and opaque cursor pages correctly; signed query-binding unchanged.

Mac schema 2 adds devices, epoch generation, checkpoints and minimal sync receipts. Existing
Journal business logic is shared through caller-owned SQLite transaction; domain change, receipt,
device receipt and checkpoint commit together. Client wall-clock is provenance, never LWW or
ordering authority. Schema 1 upgrade is transactional after consistent preupgrade snapshot.
MAC restore increments restore_epoch; backup excludes usable device credential material and
restored/rotated epochs force re-pair/reconciliation. Tombstone retention rotation invalidates
all old credentials before pruning. No deleted-ID resurrection. No private vault migration.

Owner-only one-time pairing invitations (5 min, 5 attempts/min), explicit Origin/Host/CSRF for
owner writes; scoped random device credential supplied in Authorization header, device id and
epoch checked on each transport request. Mac stores a hash of random credential, not a passphrase
or plaintext token. Revoke prevents new sync and does not erase phone copy. LOCAL_ONLY/default
keeps device routes/PWA disabled; M2_SYNTHETIC_HARNESS is explicit and still loopback-bound.

PWA inherits neutral UI/shared editor. Manifest/icons/standalone scope and precached shell;
SW never caches /api responses, no guaranteed background sync. IndexedDB version 2 stores
public KDF/schema/random-device metadata plus AES-256-GCM ciphertext. Passphrase-derived key
is nonextractable/memory-only; PBKDF2-HMAC-SHA256 600,000, random 128-bit salt and fresh 96-bit
IVs, authenticated schema/device/revision/purpose binding. No plaintext durable credentials in
localStorage/IDB/recovery, no plaintext notes/tags/outbox in IDB. No custom crypto primitive.
Entry+outbox share encrypted revision-CAS transaction; success only after transaction completion.
Crypto/cleartext state is discarded on lock/reload; browser/OS compromise and memory copies are
outside the claimed application-level protection. This is not Android Keystore acceptance.

Queued/syncing/Mac confirmed/conflict/failed/repair states are explicit. Foreground reconnect
retries same operation id, response loss cannot duplicate effect. Conflicts show local/current
Mac and allow explicit Mac/phone/manual decisions as new mutations from current revision. A
completion audit corrected the initial Mac-choice path that had accepted a snapshot locally
instead of queuing a new receipt-bound decision; final C contains this regression fix. Mac-deleted
conflicts cannot replay the ID; explicit new-copy option generates a new ID. Re-pair alone never
unlocks old epoch queue: explicit full snapshot/reconciliation choice is required.

Waiting SW activates only after user decision. Interrupted cache install leaves old shell;
structural IDB upgrade is additive and encrypted format 1→2 is explicit/transactional. Newer
unknown schema refuses without reset. Quota/open/upgrade failures leave current draft. Persistent
storage grant/denial displayed honestly, clearing storage shows empty/recovery without fake sync.
Encrypted recovery includes only unsynced records/outbox, excludes device credential, has schema
and checksum/GCM validation; explicit empty-target import, no silent Mac merge or replay.

## Evidence and gates

[Exact final C checks](evidence/M2/EXACT_FINAL_C_CHECKS.json) records actual commands, environment,
UTC time, exit code and sanitized output in a clean detached local source clone. Pinned project
Python/Node dependencies reused explicitly; tracked source remained untouched. Build/unit/browser/
docs/snapshot/privacy checks are actual runs, not inferred from hashes.
[Current requirement audit](evidence/M2/COMPLETION_AUDIT.json),
[final privacy](evidence/M2/PRIVACY_FINAL_R.json) and
[artifact/material review](evidence/M2/ARTIFACT_REVIEW.json) cover the current candidate. [Pre-C](evidence/M2/PRE_C_CHECKS.json)
and [initial C](evidence/M2/EXACT_C_CHECKS.json) remain historical evidence. Final counts: **120 Python tests** (M1 regression + M2 API/browser/UI) and **11 WebCrypto/IndexedDB tests**,
all exit0; no count substitutes for mapped coverage.
Environment: Python 3.13.2, Node 26.8.2, npm 11.19.1, Darwin 27.0.0/arm64, Chromium 140.0.7339.16.
Only known non-failing warning: Starlette TestClient/AnyIO deprecated BlockingPortal alias.

| Gate | Actual evidence | Scope status |
|---|---|---|
| M2-A01 | persistent real Chromium SW/cache/IDB offline create/edit/delete, reload and browser reopen | PASS synthetic |
| M2-A02 | actual commit/response-drop route.fetch+abort then retry; SQLite receipt/effect counts, restart and transaction failure | PASS synthetic |
| M2-A03 | two browser clients + Mac base revision, both variants/manual merge, new Mac/phone decision operation IDs and revisions | PASS synthetic |
| M2-A04 | Mac delete→stale offline edit, phone offline delete/reload/retry, content fingerprints purged and tombstones win | PASS synthetic |
| M2-A05 | M1 UTC/DST/midnight/TZ semantics retained; deliberately wrong 1900/2099 client clock and server ordering cursor | PASS synthetic |
| M2-A06 | invitation TTL/rate/replay, rollback/one-use, device binding, real owner invitation/revoke UI and retained phone copy | PASS synthetic |
| M2-A07 | native WebCrypto; persisted IDB/recovery plaintext-negative inspections, wrong passphrase, fresh IVs, encrypted CAS, lock | PASS synthetic, not OS security |
| M2-A08 | real waiting/interrupted/new SW activation with queued outbox, encrypted/physical DB migration rollback and future version refusal | PASS synthetic |
| M2-A09 | quota injection and retained draft, open/logical upgrade failure, persistent grant display, actual clear/eviction recovery state | PASS synthetic |
| M2-A10 | old Mac snapshot restore/epoch rotation/retention denial, real browser re-pair plus explicit new-copy reconciliation | PASS synthetic |
| M2-A11 | default loopback/Host/Origin/auth policy, no external browser requests, process deny-egress regression, staged/all-object/generated/artifact review | PASS in documented scope |
| M2-A12 | [Galaxy S24 manual runbook](../docs/M2_ANDROID_GATE.md), no actual phone access | HARDWARE_UNVERIFIED / NOT_RUN |

Tests: [backend](../tests/test_m2_sync.py), [real PWA/browser](../tests/test_m2_browser.py),
[owner UI/viewport](../tests/test_m2_ui.py), [crypto/store](../apps/web/tests/phone-store.test.ts).
M1 tests remain enabled. OpenAPI read/input schemas and standalone browser JSON validation
are generated from the app; no runtime eval under CSP. [Crypto ADR](../docs/adr/ADR-001-M2-PHONE-CRYPTO.md)
and [transport ADR](../docs/adr/ADR-002-M2-TRANSPORT.md) preserve boundaries/limitations.

## Transport and hardware

Candidate: owner-approved **private Tailscale Serve + MagicDNS HTTPS**, not Funnel. Primary docs
comparison includes local CA/private DNS, DNS-01 public leaf/private DNS and private tailnet route.
Account/client/trust/router/operational/cost/CT disclosure/revocation implications are explicit;
actual eligibility/account/environment not assumed. No candidate route activated or account created.
A test-only localhost HTTPS certificate/browser exception proves synthetic SW/manifest/offline
semantics; no OS trust installed. Localhost on a phone is not the Mac. Plain LAN HTTP/public Vercel
shell are not silently substituted for private origin. Real route/Android versions/Keystore/lock-wake,
private data-owner consent and threat review need a separate scoped gate. Watch/health untouched.

## Measurements

[Performance](evidence/M2/PERFORMANCE_FINAL_C.json): actual final-C built PWA + Mac API, N=20
invented notes; UI local-save completion includes encrypt+entry/outbox transaction, one 20-op
reconnect/pairing batch, encoded IDB/estimate/cache response bytes, SQLite bytes, own Mac harness
0.5s idle CPU/RSS. No Galaxy S24 or target M2/16GB benchmark/SLO claimed; see method/environment/raw
numeric results in the JSON. No long stress loops or disk filling.

## Launch / synthetic browser demo

```bash
./scripts/setup_demo.sh
./scripts/m2_demo.sh /private/tmp/personal-companion-m2-synthetic-demo
```

Mac `http://127.0.0.1:8765/`: terminal one-time code. PWA on desktop synthetic browser:
`http://127.0.0.1:8765/phone/`: local passphrase, then owner-issued invitation from Mac settings.
Offline capture works after first shell load. Stop Ctrl+C; no autostart. M1 local-only command
remains `./scripts/demo.sh /private/tmp/personal-companion-m1-synthetic-demo`.

```bash
npm --prefix apps/web test
.venv/bin/python -m pytest tests/test_m2_browser.py tests/test_m2_ui.py -q
```

Actual Android needs the approved transport gate; no instructions to bypass real certificate warnings.
[Runbook](../docs/INSTALLATION.md) documents optional test-only TLS harness, storage recovery,
forget/revoke/epoch boundaries. Unsaved draft is not durable, and encrypted browser storage can
be evicted. Lost passphrase has no bypass. Deletion is semantic purge, not forensic erase of old
SQLite/browser/backup bytes. This does not authorize real notes or release/deploy.

## Handoff

STATE/HANDOFF/roadmap/devlog point to this report/contract/goal. M1 external ACCEPT preserved;
M2 remains AWAITING_REVIEW. No synthetic implementation blocker after final checks. Remaining
hardware/transport/security actions are NOT_RUN/BLOCKED_FOR_PERMISSION as explicitly scoped,
not fake PASS. C→R contains status/report/evidence only; normal-main push receipt and exact R
are returned in final handoff without another attestation-only commit. Stop at independent review,
M3+ requires new explicit owner goal.
