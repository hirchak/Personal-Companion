# M0 — direct-main workflow finalization

Дата: 2026-09-30. Статус під час роботи над C3: IN_PROGRESS; після R4 — AWAITING_REVIEW.
M1/app NOT_STARTED; implementation target — лише durable workflow/config/validator/tests.

| Git field | Значення |
|---|---|
| Repository | https://github.com/hirchak/Personal-Companion.git (public) |
| Intended/configured default branch | `main` |
| Actual origin/main before this goal | Ref absent; confirmed with GitHub branches API and `git ls-remote` |
| Current local branch | `main`, створена від verified R3 fast-forward history |
| Existing historical review branch | `review/m0-bootstrap` at `ca0e1fc3af42bcc31e4038a591f7356713718005` |
| Base B | `c891a49f17af190b84e2b4d70e85597bf3e3b1ba` |
| Corrected M0 C2/R2 | `d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60` / `6a17efbcfa1a941aa4afcd04e842cfacde8ce299` |
| Post-publication R3 | `ca0e1fc3af42bcc31e4038a591f7356713718005` |
| New C3 | recorded in R4/final message after commit |
| New R4 | evidence-only commit after C3; SHA omitted here to avoid self-hash |
| Owner authorization | normal direct-main push for explicit `/goal`, after local tests/privacy checks |
| Separate permissions | `push_main=true`; `merge_main/deploy/provider/private-data=false` |
| Push/CI | push `origin/main` after R4 checks; CI NOT_RUN |

## Owner decision and durable workflow

The owner decision `M0 FINALIZATION — DIRECT MAIN WORKFLOW` establishes the normal
fast-forward direct-main development model for this test project. It applies to an
explicit `/goal`; routine push does not require a second approval. The updated config and
STATE distinguish `push_main` from `merge_main`. Review-branch push is not the default;
the existing public review branch remains available as history. ADR-014 records the change.

The durable cycle is goal → local implementation/tests → C commit → R evidence commit →
privacy/public-data scan → normal direct push to `main` → architect reviews exact pushed
SHA. FIX_REQUIRED uses a new forward commit. Force-push/history rewrite, merge, release/tag,
deploy, live provider/billing/auth change, private data, and automatic next milestone remain
outside this authorization. M1 requires a new owner goal.

## History and M0 boundaries

Existing history B → original C/R → corrective C2/R2 → publication R3 is preserved.
C3/R4 build on local main at R3; remote historical `review/m0-bootstrap` remains intact.
C3 changes project metadata to schema v2 with one explicit `push_main` permission, separate
from `merge_main`. Other canonical identity, authority and snapshot-policy values remain
unchanged; workflow, validator, regression tests and M0 report are updated.
No application feature/M1 implementation, raw research document, real-user data, migration,
provider call, clinical-protocol activation, launch automation, or deployment.

Canonical `.gitignore` and `.project/context_map.json` were restored from the owner starter
with the expected exact hashes; original project schema/authority/snapshot-policy fields
are preserved. Four snapshot names remain canonical. Evidence remains at
`reports/evidence/M0/`; old C2/R2/R3 push records are historical facts, not current policy.

## Checks

| Check | Commit/tree | Result |
|---|---|---|
| Documentation/config validation | C3 | Exact command and exit code in R4 evidence |
| Full synthetic tooling suite | C3 | Includes separate `push_main` vs `merge_main` tests and direct-main mismatch regression |
| Raw `.docx/.pdf/.xlsx/.zip` exclusion | C3 | Synthetic filenames only, denied before read/copy; no raw source ingested |
| Context generation + source/output hashes | C3/R4 | Four canonical names, manifest verified against exact tree |
| Privacy scan | staged C3 and R4, all local Git objects and generated snapshots | Heuristic result and scope in R4 evidence |
| `git diff --check`; C3→R4 evidence-only allowlist | C3/R4 | Run before push |
| Normal `git push -u origin main` | R4 | Verify origin/main SHA and actual GitHub default branch afterward |

CI remains NOT_RUN. Automated checks do not establish clinical safety, at-rest encryption,
actual runtime egress, device compatibility, consent or copyright clearance. The architect
will review the published SHA; the implementer does not self-assign ACCEPT.
