# M8E existing-owner pilot activation — ACTIVE

## Accepted implementation

External M8E ACCEPT is recorded in `reports/M8E_ARCHITECT_REVIEW.md`: C4
`55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d`, review R2
`519bac8f77965ae7165ff536391dd75f19af284b`. Live GitHub `main` was verified at R2 before the operation.

Exact package `M8D-55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` was built from a clean detached clone at C4 using
existing dependencies only. Manifest hash `4c8cfd0d2e827dc3d50c21614c51f076a878207c8792a5cebab7fc69226136b0`;
embedded `git_commit` equals C4, release format is 4, and the complete package file-hash set verified. The
attempted Git worktree creation was denied because repository `.git` is read-only; the isolated clone fallback
succeeded and was removed after validation. An initial misdirected build was rejected by its manifest check and
removed before use; no R2-built package was used for activation.

## Initial sanitized operation checkpoint — 2026-10-06

| Check | Result |
|---|---|
| Live `origin/main == R2` | PASS, read-only GitHub branch API |
| Starting worktree clean at R2 | PASS |
| Exact C4 local package | PASS; manifest above |
| Existing app process on the accepted loopback port | NONE LISTENING; nothing to stop |
| Existing-root C4 private security preflight | FAIL: `INVALID_METADATA` |
| Protected pre-upgrade backup | PASS; active accepted M8D C2 manager verified it |
| Existing-app upgrade | NOT_RUN |
| Existing vault preserved across upgrade | UNVERIFIED; upgrade did not run |
| Root receipt / schema / SQLite integrity / foreign-key checks before upgrade | PASS / schema 11 |
| Schema/integrity after upgrade | NOT_RUN |
| C4 profile declarations / local whisper assets | PASS; installed pilot UI not upgraded |
| Local app started / browser opened | NO / NO |

One matching PRIVATE_LOCAL install was located by a bounded install-marker lookup under Application Support.
Its paths, root identity, backup location and backup hashes remain local and are absent from this report. The
accepted manager verified the protected backup. C4's application preflight failed with `INVALID_METADATA`, even
under elevated execution, so the accepted upgrade was not attempted. A separate read-only check returned schema
11, SQLite integrity PASS and foreign-key PASS; it does not override the failed application preflight. No
row-level content diagnosis or repair was attempted.

No new vault, restore, data migration, message, conversation, microphone capture, AI/provider call, account
setting, phone transport, system package, deploy, tag, or GitHub Release was created or changed. No private
content was printed, exported or retained in evidence. Existing external controls remain
`NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone transport remains OFF; clinical and Health remain OFF;
HUMAN_UA_ASR remains `PARTIAL_OWNER_PILOT / OPEN`.

## Resume authorization checkpoint — 2026-10-07

The owner reports independent verdict `M8E_PREFLIGHT_DIAGNOSTIC = ACCEPT`, scoped to sanitized preflight
observability only. Diagnostic C `1edacfb4749205cf1ccdc22f0601b5dac43a0d27` and publication R
`d7de88f33db77c6dbb86971fce1d2b4c514e0eb1` are recorded as accepted. The original `INVALID_METADATA` cause remains
UNCONFIRMED; no claim is made that it was fixed.

This resume begins from clean repository `main` at `d7de88f33db77c6dbb86971fce1d2b4c514e0eb1`, verified against
live `origin/main`. The accepted C4 product package remains the owner runtime target. At this checkpoint the fresh
read-only diagnostic run, exact-C4 preflight for this resume, new protected backup, and upgrade were NOT_RUN. The
prior protected backup was preserved. No private content or private path is included in this report.

## Completed activation — 2026-10-07

| Check | Result |
|---|---|
| Durable diagnostic review | `M8E_PREFLIGHT_DIAGNOSTIC = ACCEPT`; sanitized observability only |
| Original `INVALID_METADATA` cause | UNCONFIRMED |
| Accepted diagnostic validator on existing root | PASS / `COMPLETE` |
| Exact C4 private-preflight immediately before upgrade | PASS |
| Exact product package and manager | PASS; release `M8D-55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` |
| New protected pre-upgrade backup | PASS; new target, prior backup preserved |
| Existing-root upgrade | PASS |
| Post-upgrade schema/integrity | PASS |
| Root identity and active C4 release | PASS / PASS |
| Existing vault preserved | YES; root identity, schema and content-free table-count checks stable |
| Conversation landing, Free/Deep profiles, journal/creative | PASS |
| Local whisper assets | AVAILABLE; validated without transcription |
| Provider and consent default | AI OFF, voice OFF; no consent or provider action performed |
| Phone / clinical / Health | OFF / OFF / OFF |
| Local app and browser | RUNNING / OPEN at `http://127.0.0.1:8765` |

The exact accepted C4 manager created and verified the new backup as part of the upgrade. All prior backup artifacts
were left intact. No real conversation was opened or created; no AI message was sent; no microphone was used; no live
provider call or external account-setting check occurred. No private paths, root IDs, backup names/hashes, record
values, unlock code, or exception messages are recorded here. External controls remain
`NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; HUMAN_UA_ASR remains `PARTIAL_OWNER_PILOT / OPEN`.
