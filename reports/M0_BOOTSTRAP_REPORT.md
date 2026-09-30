# M0 — direct-main workflow finalization

Дата: 2026-09-30. Статус: **AWAITING_REVIEW**, не ACCEPTED. M1/app NOT_STARTED.

| Git field | Value |
|---|---|
| Repository | https://github.com/hirchak/Personal-Companion.git (public) |
| Owner intended default | `main` |
| Actual GitHub default | `main`, verified after update through `gh repo view` and GitHub API |
| Base B | `c891a49f17af190b84e2b4d70e85597bf3e3b1ba` |
| Implementation C3 | `bc5cf13c3a3569edd0e0c9d9d157889471d0a0bd` |
| Evidence R4 | `7ecd3f025793213089b801947deb91c4c800d658` (status/report/evidence-only) |
| Post-publication attestation R5 | status/evidence-only follow-up; SHA in final message to avoid self-hash |
| Current main before R5 | `origin/main` verified at R5 `175fc934ad16552759273d2ed6770835b6f28786` at M1 start |
| Review branch | historical `review/m0-bootstrap` remains at R3 `ca0e1fc3af42bcc31e4038a591f7356713718005` |
| Main workflow permission | `push_main=true`; `push_review_branch=false`; `merge_main/deploy/providers/private-data=false` |
| Push / CI | C3/R4 normal pushes and default-branch edit succeeded; R5 main publication verified at M1 start (see M0_ARCHITECT_REVIEW.md). CI NOT_RUN |

## Owner decision and schema update

The owner decision `M0 FINALIZATION — DIRECT MAIN WORKFLOW` permits normal fast-forward
development pushes directly to public `main` for every explicitly issued `/goal` after its
checks; no repeated approval is needed. Project metadata schema v2 adds `permissions.push_main`
and keeps it distinct from `merge_main`. The previous direct-main owner decision applies;
the review branch remains as history and is not the default development route.

`AGENTS.md`, `docs/WORKFLOW.md`, `STATE.md`, `HANDOFF.md`, README, START_HERE, project
instructions, ADR-014, config validators and tests now describe the same workflow. C3 is the
workflow/config/test change; R4 is state/handoff/report/evidence-only. R5 records the verified
publication state. C3→R4 and R4→R5 contain no application implementation changes.

## M0 history and scope

The existing chain B → initial C/R → corrective C2/R2 → publication R3 remains intact.
C3 and R4 extend that history on `main`; R3 remains on the historical review branch. No force
push, rebase rewrite, squash or deletion occurred. M1 is not implemented or authorized.

Canonical `.gitignore` and context map still match starter hashes. Canonical project identity,
authority and snapshot policy remain intact; schema v2 only adds the explicit main permission.
No raw research document, DOCX, private record, app code, provider call, data migration,
clinical activation, billing/auth change, deployment or release.

## Checks and evidence

| Check | SHA/tree | Result |
|---|---|---|
| Documentation/config consistency | C3 and R4 | PASS |
| `python3 -m unittest discover -s tests -v` | exact C3/R4 | 25 synthetic tooling tests, PASS |
| Direct-main versus merge permission | C3 | PASS; main allowed and merge denied/mismatch rejected |
| Raw `.docx/.pdf/.xlsx/.zip` exclusion | C3 | PASS using synthetic names only; no source content opened or copied |
| Context generation and source/output hashes | C3/R4 | PASS; four canonical names, 47 source entries, 5 outputs |
| Privacy scan | C3/R4 staged trees, all Git objects, generated snapshots | PASS, heuristic scope |
| R4/R5 path whitelist and `git diff --check` | R4/R5 | PASS; only status/evidence paths |
| C3/R4 main publication | GitHub API + `git ls-remote` | PASS; R4 on `origin/main`, GitHub actual default `main` |
| R5 post-publication push | verified at M1 start, exact R5 | normal fast-forward only to `main` |

Detailed evidence: `reports/evidence/M0/CANONICAL_STARTER_VERIFY.json`, `C3_RERUN_2026-10-01.json`,
`C3_SNAPSHOT_HASHES.json`, `R4_CHECKS.json`, `R4_SNAPSHOT_VERIFY.json`,
`GITHUB_MAIN_NORMALIZATION.json`, `MAIN_PUBLICATION_VERIFY.json`, and `R5_CHECKS.json`.

CI remains NOT_RUN. These engineering checks do not establish clinical efficacy, encryption
at rest, device compatibility, runtime egress, consent or copyright clearance. Architect
reviews the exact pushed C3/R4; the implementer does not self-assign ACCEPT. A separate owner
goal is required to begin M1.
