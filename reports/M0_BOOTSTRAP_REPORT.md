# M0 corrective — report для архітектора

Дата: 2026-09-30. Статус виконавця: **AWAITING_REVIEW**, не ACCEPTED.
M0 FIX_REQUIRED виправлено. M1/app NOT_STARTED; нової M1 goal немає.

| Git field | Значення |
|---|---|
| Repository | https://github.com/hirchak/Personal-Companion.git |
| Branch | `review/m0-bootstrap` |
| Base B | `c891a49f17af190b84e2b4d70e85597bf3e3b1ba` |
| Previous reviewed C/R | `18fefa8dd037fae1982dcc34a64f34325c10830c` / `2d267d17b45d8d873131181f5a52ff2601a6b2a0` |
| Corrective C2 | `d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60` |
| Corrective report commit R2 | буде наведений у фінальному повідомленні; не посилається на власний SHA |
| Push permission | Owner authorized normal push тільки review branch; main/merge/release/deploy OFF |
| Push / CI | R2 буде commit-нуто до push; після push remote ref перевірити. CI NOT_RUN |

GitHub connector підтвердив repository public і configured default branch `main`;
перед corrective push repository був порожній. Через це default `main` branch/ref не
створювався; push scope обмежено `review/m0-bootstrap`.

## Canonical files

Owner-provided Repo Starter ZIP: 62 entries, zero DOCX. Архів SHA-256:
`469c2e998c5076c9b2d522ed0fa0e8579d76745006eec7039de79e18b5e074e9`. Відкривалися
лише `.gitignore`, `.project/context_map.json`, `.project/project.json`; raw research
зміст не читали й не додавали.

| File | Expected/original SHA-256 | Result |
|---|---|---|
| `.gitignore` | `92e8adf6bde8f43f9dcef971fc29e82f9722eb39c03cd917953c5bc1aa400545` | exact canonical bytes restored |
| `.project/context_map.json` | `86fdc85997b35959450ed6e96008c6fa0c2e3d848b221b4e155814c07ab7107d` | exact canonical bytes restored |
| `.project/project.json` | original `4edb5d0454cba5bba611455802d970f07ca564b5a5a2653156143f66a4bbad9a` | canonical fields/shape preserved; authorized values overlaid |

`schema_version`, `display_name`, `name_status`, `authority`, `snapshot_policy` and
all original JSON field names were kept. Applied repo URL, default `main`, review branch,
`push_review_branch=true`, and `merge_main/deploy/live_provider_calls/access_real_user_data=false`.
Context outputs restored as `01_PROJECT_CONTEXT.md`, `02_TECHNICAL_SPEC.md`,
`03_RESEARCH_AND_SAFETY.md`, `04_DELIVERY_AND_CURRENT_STATE.md`. Validator now pins the
two expected source hashes; snapshot generator removes only the three named legacy derived
outputs. The canonical source files are not regenerated or reformatted.

## Changes and scope

C2 updates the hidden starter files/permission metadata, durable status/docs, snapshot
validation/generation, and synthetic regression checks. The canonical M1 proposal is
unchanged. No raw research DOCX, private data, app implementation, migration, provider
call, billing/auth edit, main/merge, deploy, or launchd action.

## Checks

| Command / evidence | SHA scope | Result |
|---|---|---|
| `python3 scripts/check_docs.py --json` | Exact C2 | exit 0; 76 files, 12 JSON, 49 local links, 16 research briefs |
| `python3 -m unittest discover -s tests -v` | Exact C2 | exit 0; 24 synthetic tooling tests |
| `python3 scripts/build_chatgpt_context.py` | Exact C2 | exit 0; four canonical Markdown outputs + instructions, manifest source C2 |
| Source/output SHA-256 verification | Exact C2 | PASS; 47 source entries and 5 output entries |
| `python3 scripts/check_privacy.py --include-generated` | Exact C2 | exit 0; worktree, staged/all Git objects, generated snapshots; heuristic scope |
| `.gitignore` synthetic behavior probes | Exact C2 | PASS; 18 private/runtime/raw classes ignored; `.env.example` remains allowed |
| `git diff HEAD^ HEAD --check` | C2 | exit 0 |
| Exact `git archive C2` docs/test/generator commands | C2 | all exit 0; archive has no `.git`, null generated source_commit is expected |
| C2→R2 path whitelist | R2 staged diff | PASS; only state/handoff/roadmap/devlog/report/evidence |
| Normal push and remote ref verification | post-R2 | authorized; result follows after push; never main |

Detailed logs: `reports/evidence/M0/CANONICAL_STARTER_VERIFY.json`, `C2_CHECKS.json`,
`C2_SNAPSHOT_HASHES.json`, `R2_CHECKS.json`, and `R2_SNAPSHOT_VERIFY.json`.
Heuristic scan is not an exhaustive personal-data/copyright/security audit; no runtime
network egress test was run. No real device, FileVault, wearable, ASR, clinical, private
vault or user-consent verification is claimed. Active model/effort and hardware RAM remain
NOT_VERIFIED. M1 remains unauthorized pending a new owner goal.
