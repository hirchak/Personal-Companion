# M0 corrective — review report

Date: 2026-09-30. Status: corrective work in progress; M1 NOT_STARTED.
Repository: https://github.com/hirchak/Personal-Companion.git. GitHub connector verified
it as public, default branch `main`; the repository was empty before publication.
Review branch: `review/m0-bootstrap`; owner authorized normal push to this branch.
Merge/main, deploy, provider calls and private data remain disabled.

## Canonical starter correction

Owner supplied an owner-provided Repo Starter ZIP (local path omitted from public report).
Archive SHA-256: `469c2e998c5076c9b2d522ed0fa0e8579d76745006eec7039de79e18b5e074e9`.
Only `.gitignore`, `.project/context_map.json`, and `.project/project.json` were read.
Canonical SHA checks PASS:

| File | Expected/original SHA-256 | Corrected value |
|---|---|---|
| `.gitignore` | `92e8adf6bde8f43f9dcef971fc29e82f9722eb39c03cd917953c5bc1aa400545` | exact original bytes |
| `.project/context_map.json` | `86fdc85997b35959450ed6e96008c6fa0c2e3d848b221b4e155814c07ab7107d` | exact original bytes |
| `.project/project.json` | `4edb5d0454cba5bba611455802d970f07ca564b5a5a2653156143f66a4bbad9a` | original fields/structure preserved; authorized values applied |

Canonical project fields `schema_version`, `display_name`, `name_status`, `authority`,
and `snapshot_policy` were preserved exactly. Applied `repo_url`, default `main`, review
branch `review/m0-bootstrap`, push permission true, and merge/deploy/provider/private-data
permissions false. The context map names remain `01_PROJECT_CONTEXT.md`,
`02_TECHNICAL_SPEC.md`, `03_RESEARCH_AND_SAFETY.md`, and
`04_DELIVERY_AND_CURRENT_STATE.md`.

Archive index contained 62 entries and zero DOCX. Raw research contents were not opened
or added. No ZIP/archive, user attachments, or provider credentials are staged.
The history from B is preserved; no force-push or main branch operation is planned.

## M1 boundary

`docs/M1_CONTRACT.md` remains a proposal for local non-AI capture/CRUD/search, typed
records, root isolation, migrations, export and backup/restore. No M1 application code,
real-user data, runtime provider calls, Android sync, clinical protocol, deployment,
main merge or launch automation.

## Corrective checks

Exact C2/R2 SHAs and final evidence tables will be written at R2. Repeated commands:
`python3 scripts/check_docs.py --json`; `python3 -m unittest discover -s tests -v`;
`python3 scripts/build_chatgpt_context.py`; `python3 scripts/check_privacy.py --include-generated`;
canonical hash verification; generated source/output manifest hash verification;
`.gitignore` behavioral probes; `git diff --check`. Synthetic results only. The C2→R2
path whitelist must contain STATE/HANDOFF/roadmap/devlog/report/evidence paths only.

Privacy scan scope: public worktree, staged entries, every local Git object, and generated
snapshots. It is heuristic and does not prove absence of arbitrary personal data, copyright
problems or runtime exfiltration. GitHub ref and permission will be checked after push.
CI status is NOT_RUN. Technical ACCEPT and M1 authorization are not implied.
