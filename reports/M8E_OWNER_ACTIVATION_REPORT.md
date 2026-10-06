# M8E existing-owner pilot activation — PREFLIGHT_BLOCKED

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

## Sanitized operation checkpoint

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
