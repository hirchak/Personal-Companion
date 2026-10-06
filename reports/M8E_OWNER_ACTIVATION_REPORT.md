# M8E existing-owner pilot activation — IN_PROGRESS

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
| Existing-root private security preflight | NOT_RUN |
| Protected pre-upgrade backup | NOT_RUN |
| Existing-app upgrade | NOT_RUN |
| Existing vault preserved | UNVERIFIED; no root was selected or opened |
| Schema/integrity after upgrade | NOT_RUN |
| UI/profile/assets/feature verification | NOT_RUN |
| Local app started / browser opened | NO / NO |

The accepted sanitized activation record does not expose the existing pilot's app/data/backup/local-ASR root
bindings, and no listener is available to resolve the bindings from its foreground command. A path-free lookup
checked only for an installation marker under the single Application Support layout documented by the project;
it found no match. No receipt or vault content was read, and no recursive filesystem/content search or path
guess was performed. Activation awaits an owner-approved local root resolver/manager entry point; private path
values are not requested in chat or recorded here.

No new vault, restore, data migration, message, conversation, microphone capture, AI/provider call, account
setting, phone transport, system package, deploy, tag, or GitHub Release was created or changed. Existing external
controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone transport remains OFF; clinical and Health remain
OFF; HUMAN_UA_ASR remains `PARTIAL_OWNER_PILOT / OPEN`.
