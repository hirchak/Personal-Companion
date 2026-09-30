# M0 — direct-main workflow finalization

Дата: 2026-09-30. Статус виконавця: **AWAITING_REVIEW**, не ACCEPTED.
M0 завершено в межах workflow normalization; M1/app NOT_STARTED.

| Git field | Значення |
|---|---|
| Repository | https://github.com/hirchak/Personal-Companion.git (public) |
| Intended default branch | `main` |
| Actual GitHub default before normalization | `review/m0-bootstrap`, confirmed by `github_get_repo` |
| Actual GitHub default after C3 | `main`, verified using GitHub API and `gh repo view` |
| Actual `origin/main` before normalization | Ref absent; confirmed via branches API and `git ls-remote` |
| Current development branch | `main`, created at verified R3 ancestry |
| Historical review branch | `review/m0-bootstrap` at R3 `ca0e1fc3af42bcc31e4038a591f7356713718005` |
| Base B | `c891a49f17af190b84e2b4d70e85597bf3e3b1ba` |
| Existing corrective M0 | C2 `d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60`; R2 `6a17efbcfa1a941aa4afcd04e842cfacde8ce299`; R3 `ca0e1fc3af42bcc31e4038a591f7356713718005` |
| Implementation C3 | `bc5cf13c3a3569edd0e0c9d9d157889471d0a0bd` |
| Evidence R4 | following evidence-only commit; SHA in final handoff (no self-hash) |
| Direct-main permission | `push_main=true`; owner authorizes normal fast-forward per explicit `/goal` after checks |
| Separate gates | `merge_main`, deploy, providers, billing/auth, private data all false |
| Push / CI | C3 created `origin/main`; GitHub default is `main`; R4 fast-forward push after staged checks. CI NOT_RUN |

## Owner decision and durable policy

Owner decision `M0 FINALIZATION — DIRECT MAIN WORKFLOW` establishes direct-main development
for this test project. Each explicitly issued `/goal` may publish normal fast-forward commits
after its checks without a second confirmation. Config metadata is schema version 2 because
it adds `permissions.push_main` separately from `merge_main`. `push_review_branch=false` and
`review_branch=null` encode that review branches are not required by default; the existing
public M0 review branch remains intact as history.

AGENTS, WORKFLOW, STATE, HANDOFF, README, START_HERE, ChatGPT project instructions, ADR-014,
validators, report template and M0 goal record describe the same model. C/R discipline remains:
C3 contains workflow/config/checker/tests, R4 contains state/handoff/report/evidence only.
Direct push is not merge, release/tag or deploy. Architect reviews after publication.
M1 requires a new explicit owner goal.

## History and data boundaries

Local `main` was created as a ref at R3; all B/C/R/C2/R2/R3 commits remain ancestors.
C3 was normal-pushed as a fast-forward from R3. `gh repo edit --default-branch main`
completed successfully; `gh repo view` and the GitHub connector verify the actual default
is now main. No force-push, rebase, squash or history rewrite occurred. The prior
`review/m0-bootstrap` ref remains unchanged at R3.

Canonical hidden starter correction remains verified from the owner ZIP. The ZIP itself,
raw research files and private attachments were not added to the repository. Regression tests
use synthetic filenames/content to prove `.docx/.pdf/.xlsx/.zip` exclusion before copy/read.
No app/M1 implementation, real data, provider calls, migrations, billing/auth change, clinical
activation, launch automation or deployment occurred.

## C3 checks

| Check | Scope | Result |
|---|---|---|
| `python3 scripts/check_docs.py --json` | Exact C3 | PASS |
| `python3 -m unittest discover -s tests -v` | Exact C3 | 25 synthetic tests, PASS |
| Exact `git archive C3`: docs/tests/context generator | C3 | PASS; no `.git`; archive-generated `source_commit=null` expected |
| Canonical config/STATE and `push_main` vs `merge_main` consistency | C3 | PASS |
| Raw `.docx/.pdf/.xlsx/.zip` exclusion test | C3 | PASS using temp synthetic inputs only |
| Generated four canonical snapshots + source/output hashes | C3 | PASS, 47 sources / 5 outputs |
| `python3 scripts/check_privacy.py --include-generated` | C3 worktree and Git objects | PASS; heuristic scan scope |
| `git diff HEAD^ HEAD --check` | C3 | PASS |

## R4 gates

R4 містить лише поточний state/handoff/roadmap/report/devlog/evidence (environment/open-
question rows included); жодного workflow-code change після C3. Пройти staged docs/synthetic
tests/snapshot hashes/privacy scan over all local Git objects and generated snapshots. Потім
normal fast-forward push R4 та verify `origin/main` equals R4; GitHub default already main.
C3→R4 passed the staged path whitelist; docs validation, staged privacy scan and diff check
pass. R4 commit/push remains the only outstanding action; it is evidence/status-only.

CI is NOT_RUN. These engineering checks do not establish clinical efficacy, device readiness,
at-rest encryption, runtime egress, user consent or copyright clearance. No ACCEPT is claimed.
