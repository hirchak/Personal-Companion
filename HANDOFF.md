# Передача контексту — M0

Дата: 2026-09-30. M0 AWAITING_REVIEW; застосунок/M1 NOT_STARTED.
Repository: https://github.com/hirchak/Personal-Companion.git.
Branch: `review/m0-bootstrap`, origin той самий; NOT_PUSHED, CI NOT_RUN.
Base: `c891a49f17af190b84e2b4d70e85597bf3e3b1ba`.
Implementation C: `18fefa8dd037fae1982dcc34a64f34325c10830c`.
Report R — commit, що містить фінальний evidence; SHA у фінальному повідомленні.

## Відновлення за кілька хвилин

Прочитати AGENTS/STATE, `.project/project.json`, `docs/WORKFLOW.md` та
`reports/M0_BOOTSTRAP_REPORT.md`. Далі — `docs/M1_CONTRACT.md`,
`docs/M0_ENVIRONMENT.md`, `docs/M0_SPEC_REVIEW.md`. Git status/HEAD/diff перевірити
окремо. Поточна goal лишається `prompts/M0_BOOTSTRAP.md`, наступна не дозволена.

## Зроблено та рішення

Збережено immutable supplied-starter baseline. Відсутні три hidden файли
reconstructed з public docs/interfaces; не hash-identical recovery.
Власницький URL записано у config/STATE/README/Git origin. Visibility/default
remote branch NOT_VERIFIED: ls-remote дав empty refs, gh API connection failed.
M1 proposal: Mac-only non-AI capture/CRUD/search, history, typed fields,
loopback auth/Origin/CSRF, tmp data-root isolation, migrations, JSON export,
consistent SQLite backup/restore. Real vault/Android/provider/protocols OFF.
Архітектурних відхилень немає; baseline ADR не отримали автоматичного ACCEPT.

## Перевірки та evidence

20 synthetic tooling tests, docs structure/metadata/links, snapshot generation,
SHA-256 source/output checks та heuristic worktree/staged/all-object privacy scan.
Exact C перевірений із `git archive C` у новому tmp directory; фінальні metadata
окремо перевірені в working tree перед R. Logs: `reports/evidence/M0/`.
Initial missing-files FAIL збережений. Initial snapshot check не містив report
через null STATE.report_path; pointer виправлено у final evidence та regenerated.
Dynamic-pointer regression test виправлено окремим локальним C commit.

Generated snapshots: `generated/chatgpt_context/`, ignored і не canonical.
Після R перегенерувати через `python3 scripts/build_chatgpt_context.py`, щоб
manifest показував R; hashes джерел важливіші за припущення про commit metadata.
Final delivery verification лежить там само, без нового recursive report commit.

## Межі і наступна дія

Active model/effort і RAM NOT_VERIFIED; hardware/Android/FileVault/crypto/runtime
NOT_RUN. CLI/tools перевірені, application dependencies не встановлювались.
Private data/auth/home inventory не читались; live inference, push/deploy,
paid route/billing changes та M1 execution не виконувались.
Наступний крок: архітектор review C/R/M1 contract; власник після review видає
окрему M1 goal. Подальші permissions автоматично не з’являються.
