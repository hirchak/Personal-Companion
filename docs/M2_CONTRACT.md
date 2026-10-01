# M2 execution contract v1

Authority: prompts/M2_OFFLINE_PWA_SYNC.md. Synthetic-only engineering candidate.
M1 externally ACCEPT; M2 executor status AWAITING_REVIEW only after verification.

Mac remains canonical after a committed receipt; phone is canonical for unsynced mutations.
One Journal domain transaction is shared by owner HTTP and device sync. Devices are opaque
UUIDs; random scoped credentials are hashed on Mac and encrypted in phone storage. Invitations
are owner-issued, one-use, 5-minute TTL, 5 attempts/minute. No URL tokens or wildcard CORS.
Device id + credential + epoch must match on every sync/pull. Revocation does not remote erase.

Schema 2 adds device/epoch/checkpoint/minimal sync receipts; migration is transactional after
consistent preupgrade backup. Epoch is opaque generation plus restore_epoch. Restore sanitizes
credentials and requires explicit re-pair/reconciliation. Rotation before retention forbids
naive replay. Deleted IDs cannot be recreated. Optimistic base_revision, never wall-clock LWW.

Phone IndexedDB version 2 contains only public crypto/schema metadata and AES-GCM encrypted
state. An entry and its operation are one encrypted compare-and-swap transaction. Each operation
has UUID operation/device/entry, base revision, local sequence, created UTC, IANA zone, schema,
action and explicit state. LOCAL_SAVED is shown only after transaction completion; queued,
syncing, Mac confirmed, conflict, failed and repair/revoked are distinct. AI always OFF.

No service-worker API caching. Versioned precached shell; waiting worker activates only by
explicit user action. Structural DB migration adds stores transactionally; incompatible newer
schema refuses without reset. Persistent storage request result is displayed, not guaranteed.
Write/quota/upgrade failure keeps current unlocked draft. Clearing all storage yields honest
empty/recovery state. Recovery exports only encrypted unsynced data, not a Mac backup, no
credential and no silent merge. Recovered operations require explicit pairing/reconciliation.

| Gate | Required proof |
|---|---|
| M2-A01 | built SW offline create/edit/delete + reload/persistent browser restart |
| M2-A02 | commit response dropped, exact op retry, one domain effect/receipt |
| M2-A03 | two devices/Mac stale edit; explicit Mac/phone/manual resolution |
| M2-A04 | Mac and offline phone delete, stale reconnect/replay, tombstone priority |
| M2-A05 | M1 time regression, midnight/DST/zone/wrong clock; ordering by revision/sequence |
| M2-A06 | pairing TTL/rate/one-use/replay/device binding/revoke |
| M2-A07 | actual WebCrypto encryption; IDB/recovery inspection, wrong key/nonce/lock |
| M2-A08 | waiting/update/offline/interrupted shell install + IDB migration/future schema |
| M2-A09 | quota/open/upgrade/write failure, retained draft, persistence/clear recovery |
| M2-A10 | backup restore/epoch rotation, no automatic replay; explicit reconciliation |
| M2-A11 | no external egress, no secrets/DB/keys in worktree/staged/history/artifacts |
| M2-A12 | Galaxy S24 Ultra manual runbook; HARDWARE_UNVERIFIED/NOT_RUN unless actual run |

References: security and transport ADRs, actual tests/evidence and final M2 report.
Real private data, AI/health/watch/ASR/deploy/system trust/remote access/M3+ OFF.
