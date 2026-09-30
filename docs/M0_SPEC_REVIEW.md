# M0 — consistency review специфікації

> Corrective update: висновок нижче передував зовнішньому архітектурному review.
> Canonical `.gitignore`/context map hashes і project schema тепер перевірені за
> owner-provided Repo Starter; актуальні C2/R2 статуси — в M0 report.

2026-09-30. Результат виконавця: AWAITING_REVIEW, не ACCEPTED. Прочитано обов’язкові
M0 документи, додатково DATA_MEMORY, індекси, tooling/templates та відкриті питання.
Research briefs збережені й перевірені структурно; clinical research не виконувалось.

## Findings і виправлення

| Finding | Рішення M0 / доказ |
|---|---|
| У початковому unpack бракувало трьох hidden files | У corrective goal exact `.gitignore` і `context_map.json` відновлено з owner ZIP; оригінальний `project.json` підтверджено source SHA й усі canonical fields збережено. Hash evidence у M0 report |
| Starter inventory мав 61 file, у working unpack збігалося 58 | Усі 61 canonical files нині присутні; 2 задані hidden SHA відповідають PACKAGE_MANIFEST |
| Push workflow після M0 | Standing owner decision дозволяє direct-main pushes після local checks; permission `push_main` не дає `merge_main`, deploy/provider/private-data. Review branch optional |
| Documentation validator читав forbidden-файл після finding | Inventory/prune до read; forbidden/env/symlink regression tests |
| Tests copytree могли копіювати приватний каталог | Копіювання лише inventory дозволених public files; unsafe source tree →fail |
| Generated output міг пройти через symlink `generated` назовні | Reject symlink/output escape до write; synthetic regression test |
| STATE contract/report pointers не перевірялись | Path/prefix/existence/private/symlink validation; M1 contract pointer у current state |
| PACKET_VALIDATION — історичний report starter | Не підмінили. Початковий corrective check FAIL за відсутніх files; наразі hash-pinned docs validator та повторені synthetic suite |
| Baseline не задавав точних M1 schema/API/restore criteria | [M1 contract](M1_CONTRACT.md): domain, auth, idempotency, revision, deletion, root isolation, migration, export/backup/restore, acceptance matrix |

## Уточнення scope без архітектурного відхилення

PR-01/03/04 описують увесь продукт: чотири типи M1, Mac-only saved state;
phone offline/outbox/повний набір типів з’являються пізніше. T03/04 — у M1 лише локальна
concurrency/delete перевірка, cross-device deferred до M2. T06 — SQLite частина M1,
attachments deferred. Restore epoch — metadata для майбутнього M2, не виконаний sync.

Preserve-original при edit не означає зберігати private text після delete: contract
purges revisions/index/content fingerprints; tombstone не має тексту. Старий backup
може явно відновити попередній стан локально, але не дозволяє automatic replay/sync.
Secure erase і actual encryption не проголошуються за логічним delete чи tmp test.

M1 без at-rest/HTTPS/device gates — лише synthetic local development. Authorised M0
не є user-data consent. Localhost auth/Origin/Host/CSRF лишаються обов’язковими в M1.
Розробка SQLite/React/Python не підмінена іншим стеком. No substantive deviation;
новий proposal ADR не потрібен, базові ADR лишаються PROPOSED_BASELINE.

## Питання для наступних рішень

Blocking-for-M1: архітектор має review M0/M1 contract, власник — видати окрему M1 goal.
Engineering unknowns без owner decision: конкретні project-local dependency versions,
test harness і measurements/SLO вибирає M1 виконавець після verification.

Later-stage: ліцензія/бренд;
TLS/private DNS/encryption/KDF/key recovery (M2/real-use gate); Codex runtime scope,
retention/entitlement та MiniMax quota/credits (M3); wearable (M6); clinical reviewer
і content rights (M7); backup target/FileVault/consent/private pilot (M8).
Питань про симптоми або приватних даних для M0 немає. Всі detailed unresolved
questions — у [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Evidence limits

Automated docs checks перевіряють структуру, metadata, links, pointers і token patterns,
не повну семантичну несуперечність. Таблиці вище — ручний engineering review baseline.
Privacy scan: public worktree, staged/all local Git objects і regenerated snapshots;
heuristic token/key/private IPv4/URL credentials + denied paths. Synthetic tests
доводять тільки конкретні detector behaviors. Немає доказу clinical safety, real
runtime egress, at-rest security, copyright clearance або фактичної готовності UI.
