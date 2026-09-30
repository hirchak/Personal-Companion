# M0 — bootstrap report для архітектора

Дата: 2026-09-30. Статус: **AWAITING_REVIEW**, review NOT_REVIEWED.
Тільки M0 за `prompts/M0_BOOTSTRAP.md`; застосунок і M1 NOT_STARTED.

| Git field | Значення |
|---|---|
| Repository / origin | https://github.com/hirchak/Personal-Companion.git |
| Branch | `review/m0-bootstrap`, локальна |
| Base B | `c891a49f17af190b84e2b4d70e85597bf3e3b1ba` — supplied-starter root commit |
| Implementation C | `18fefa8dd037fae1982dcc34a64f34325c10830c` |
| Report commit R | SHA у фінальному повідомленні після commit; визначається Git history, без recursive self-hash |
| Push / CI | NOT_PUSHED / NOT_RUN, CI SHA=null |
| Remote | Empty advertised refs від ls-remote; gh API connection failed; visibility/default remote branch NOT_VERIFIED |

## Зроблено і M0 DoD

| Requirement | Результат / evidence |
|---|---|
| A — capabilities | [Environment](../docs/M0_ENVIRONMENT.md): observed OS/tools, explicit NOT_VERIFIED для unavailable probes |
| B — consistency | [Spec review](../docs/M0_SPEC_REVIEW.md), docs checks PASS; semantic engineering review, clinical review NOT_RUN |
| C — M1 contract | [Contract](../docs/M1_CONTRACT.md): domain/time/schema, API/CRUD/history/search, auth/CSRF, revisions/delete, root isolation, migrations, export/backup/restore, acceptance gates |
| D — durable delivery | STATE/HANDOFF/roadmap/devlog, C/R evidence, generated context; AWAITING_REVIEW, не ACCEPTED |

Усі 58 наявних canonical starter файлів збігалися з PACKAGE_MANIFEST. Git був
відсутній; збережено окремий baseline. Три missing hidden файли reconstructed
за документами/interfaces, не hash-identical recovery. PACKAGE_MANIFEST — історичний
inventory. URL власника записано у config/STATE/README/local origin. Усі permissions OFF.

Tooling: denied/env/symlink paths перевіряються до read; tests копіюють лише public
inventory; snapshot output не проходить через symlinks; STATE pointers перевіряються.
Додано scanner усіх local Git objects, включно зі staged/unreachable, без виводу
значень finding. Стек Python/React/SQLite збережено; нового architecture ADR не потрібно.
M1 contract — proposal; M1 execution і application acceptance tests NOT_RUN.

## Команди і докази

Environment: macOS 27.0 arm64; Python 3.13.2; Git 2.50.1; Node 26.8.2; npm 11.19.1;
SQLite CLI 3.54.0; Codex CLI 0.159.0. Cwd у logs — sanitized `repo/` або archive of C.

| Command / метод | Tree / exit | Outcome |
|---|---|---|
| `python3 scripts/check_docs.py --json` | Exact C через `git archive C`, 0 | PASS, C_CHECKS.json |
| `python3 -m unittest discover -s tests -v` | Exact C archive, 0 | PASS, 20 synthetic tooling tests |
| `python3 scripts/build_chatgpt_context.py` | Exact C archive, 0 | PASS; source_commit=null в archive без .git очікуваний |
| Docs + 20 tests + generator | C tooling + final evidence overlay перед R, 0 | PASS, FINAL_CHECKS.json; не удавана exact-C metadata |
| SHA-256 source/output + dynamic goal/contract/report presence | Final evidence overlay, 0 | PASS, FINAL_SNAPSHOT_CHECK.json |
| `python3 scripts/check_privacy.py --include-generated` | Worktree/snapshot/all local objects, 0 | Heuristic PASS, FINAL_CHECKS.json; staged scan перед R |
| `git diff --check` / `git diff --cached --check` | Final working/staged diff, 0 | PASS |
| C→R changed paths whitelist | Final evidence overlay, 0 | Лише STATE/HANDOFF/roadmap/devlog/reports/evidence |
| Delivery regeneration/hash check після R | R | Result у ignored delivery verification і фінальному повідомленні |

Logs: [C_CHECKS.json](evidence/M0/C_CHECKS.json),
[INITIAL_OBSERVATIONS.json](evidence/M0/INITIAL_OBSERVATIONS.json),
[C_SNAPSHOT_CHECK.json](evidence/M0/C_SNAPSHOT_CHECK.json),
`INITIAL_C_CHECKS.json`, `FINAL_CHECKS.json`, `FINAL_SNAPSHOT_CHECK.json`.

Initial docs FAIL exit 1: missing hidden files; виправлено. Initial snapshot check
на попередньому C `62c2e5e...` FAIL exit 1: STATE.report_path=null, тому report omitted;
listed hashes збігалися. Final pointer заповнено і snapshot regenerated. Тест dynamic
pointer припускав null; виправлення окремим local C commit, повтор suite на exact C.
Initial FAIL збережені, не перейменовані на historical PASS.

## Privacy, права й NOT_RUN

Real vault/приватні записи/auth.json/ключі/токени/private endpoints/account IDs/home
inventory не читались. Fixtures synthetic, без private додатка. Full local history
починається зі supplied packet; unknown remote history не imported. Scanner покриває
worktree, staged/all local objects і snapshots, не remote Git/CI artifacts/app runtime.
Patterns token/key/private IPv4/URL credentials та denied names — heuristic, не доказ
відсутності будь-яких private texts/IDs або правових проблем. Нові матеріали власні;
third-party full texts/assets не додавались. Research baseline не отримав content ACCEPT.

Live AI/Codex exec/MiniMax, dependencies install, billing/auth changes, server/port
exposure, launchd, real migrations, push/merge/deploy — NOT_RUN. Docs web reads і
read-only GitHub probes не inference. FileVault/crypto/Android/wearable/browser/ASR/
clinical acceptance — NOT_RUN. Active model/reasoning/RAM — NOT_VERIFIED; observed
client catalog Sol/high не доводить account-specific entitlement чи runtime retention.

## Review і наступний крок

Generated delivery: `generated/chatgpt_context/` — чотири Markdown snapshots,
PROJECT_INSTRUCTIONS та SHA-256 manifest, ignored і не canonical. Після R generator
повторно прив’язує source_commit до R; outputs перевіряються окремо локальним artifact.
Source hashes доводять фактичний текст, сам source_commit не доводить clean tree.
R−C — лише status/evidence (roadmap включно), без прихованих code/contract changes.

Архітектору передати B/C/R, report, logs та локальний evidence bundle/diff. GitHub
ще не містить цієї роботи: push OFF; remote review не виконаний. Bundle дозволяє
review точних SHA без publication. Git worktree має бути clean після R; snapshots ignored.
Blocking-for-M1: review M0/M1 contract та окрема goal власника. Інших M0 blockers немає.
Later gates: visibility/license, transport/encryption/key recovery, runtime rights/
retention/quotas, hardware/clinical review, user-data consent/private pilot.
