# M1 contract — локальний щоденник без AI

Дата: 2026-09-30. Версія контракту: 3. Статус: PROPOSED / AWAITING_REVIEW.
M1 execution authorized by owner goal M1_LOCAL_JOURNAL; M0 ACCEPT recorded externally.
Acceptance evidence lives in the M1 report, not in this requirements document.

Change note v2: explicit type-change confirmation; sleep interval is user-estimated,
not TST; static GET navigation may omit Origin but exact Host is always required.
Unlock requires exact Origin, JSON, one-use code and bounded attempts; all other private
API requires a session, writes/exports also CSRF. Canonical system temp parent is resolved
before fresh test root creation. Persistent explicitly SYNTHETIC demo root is allowed.
Backup is consistent SQLite snapshot; restore only into a fresh empty root.
UI drafts are memory-only and cleared at reload/lock. No trust-boundary changes.

Change note v3: original `recorded_at_utc` requirement is stored inside immutable
revision JSON in the same edit transaction; pre-correction synthetic development
history exposes null instead of inventing a historic timestamp. DB schema remains 1.
Read/receipt/history response models are generated into the shared TS contract.
Process-local deny-egress now covers datagram sends and alternative DNS APIs as well
as TCP; it remains defense in depth, not a claimed OS sandbox.

Baseline: [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_MEMORY.md](DATA_MEMORY.md),
[PRIVACY_SECURITY.md](PRIVACY_SECURITY.md), [TESTING.md](TESTING.md).

## Кінцевий результат і межі

Одна доросла користувачка на Mac: локальний UI українською дозволяє додати текст,
переглянути, відредагувати, змінити тип/теги, знайти, видалити, експортувати й
відновити synthetic записи після перезапуску. Збереження не потребує інтернету
або AI. Python/FastAPI/Pydantic + SQLite; React/TypeScript/Vite. Dependency versions
узгодити з фактичними Python/Node під час M1 й зафіксувати lockfiles у repo.
SQLAlchemy/Alembic — необов’язковий implementation choice, не нова архітектура.

Лише `inbox`, `daily`, `sleep`, `creative`. Exercise/product/custom types з PR-03
належать подальшим етапам. Немає PWA/outbox/телефонного sync, health/native bridge,
ASR/attachments upload, клінічних протоколів, AI orchestration/embeddings, billing,
гри, feedback publication, deploy, автозапуску чи реального vault. AI — `OFF`,
ніякого runtime provider dependency або відкриття credentials. M1 має працювати
на synthetic data. Дозвіл розробляти M1 не є дозволом на private rollout.

## Домен і інваріанти

Один локальний opaque `owner_id` UUID, створений для synthetic vault; не email/ПІБ.
Усі IDs — випадкові UUID без приватної інформації. Мінімальні логічні сутності:

| Сутність | Поля та правила |
|---|---|
| `vault_meta` | `vault_id`, `owner_id`, `schema_version`, `restore_epoch`, `created_at_utc`; не профіль/анамнез |
| `entries` | `id`, `owner_id`, `type`, `raw_text`, `tags`, `occurred_at_utc` nullable, `timezone`, `local_date` nullable, `time_precision`, `created_at_utc`, `updated_at_utc`, `revision`, `schema_version`, `privacy_class`, `provenance_type` |
| `entry_revisions` | `entry_id`, `revision`, попередній повний validated payload, `recorded_at_utc`; immutable під час звичайного edit, purge при delete |
| `tombstones` | `entry_id`, `owner_id`, `revision`, `deleted_at_utc`, `restore_epoch`; без тексту, тегів і journal fields |
| `operation_receipts` | `operation_id`, `owner_id`, `entry_id`, `action`, fingerprint validated request, `revision`, `result_code`; без копії тексту; видалення прибирає content fingerprints попередніх write-операцій |
| `search_index` | Локальний індекс лише живих записів; derived і rebuildable, не друге джерело істини |

Фізичні таблиці й JSON columns — вибір виконавця; тести мають довести інваріанти,
foreign keys і transaction boundaries. У M1 немає source citations, summaries,
memory або jobs; `provenance_type=USER_REPORTED`, `privacy_class=PRIVATE_PERSONAL`
фіксуються сервером навіть для synthetic fixtures. Клієнт не може задати owner,
privacy/provenance, server timestamps, revision або schema version довільно.

`raw_text` — точний введений Unicode-текст, без автоматичного переписування,
trim або Markdown execution. При edit стара версія зберігається; первинний текст
доступний через history до delete. Секція/теги не змінюють текст. Перехід типу з
несумісними полями потребує явної дії користувачки й показує, які typed поля
приберуться з поточної версії; стара версія збережена. Немає silent coercion.

| Typed fields | Обмеження |
|---|---|
| `inbox` | Лише спільні поля |
| `daily` | `mood_rating` nullable int 0..10, `energy_rating` nullable int 0..10; добровільні самооцінки, без діагнозу |
| `sleep` | `sleep_start_utc`, `wake_at_utc` nullable, `sleep_quality` nullable int 0..10; відомий wake ≥ start; якщо обидва відомі, тривалість обчислюється в UTC |
| `creative` | `creative_kind` nullable enum `idea/scene/character/reference/other`; лише ручний вибір, без health interpretation |

`null` означає unknown, нуль — відоме значення. Типізовані поля чужого типу,
невідомі ключі, NaN/Infinity, неправильний enum та невідомий IANA timezone
відхиляються без часткових змін. `raw_text`: 1..100000 Unicode code points,
тільки whitespace не приймається, але валідний текст зберігається без trim.
`tags`: до 20 унікальних case-sensitive Unicode strings, кожний 1..64 code points,
без порожніх/whitespace-only значень; дублікати відхиляються. Write body ≤1 MiB;
query `q` ≤200 code points, page `limit` 1..100. Це engineering limits M1.

Час: server timestamps — UTC; event time окремо може бути невідомим.
Початкова zone `Europe/Warsaw`, зберігати IANA zone на кожному записі. API приймає
offset-aware event timestamps, нормалізує в UTC; naive/неоднозначний local time
без offset відхиляється. `time_precision`: `instant/date/unknown`: instant потребує
event timestamp та відповідної `local_date`; date — лише date без timestamp;
unknown — обидва null. Для sleep event time/date — wake time/date, якщо він відомий;
інакше явно введена дата або unknown. Не ставити північ замість unknown.
Зміна системної zone не змінює минулі dates; sleep через північ та DST перевіряються.

## Application/API boundary

Спільний domain service і repository для HTTP та локальних maintenance operations;
UI не має SQL/довільного доступу до файлів. Контракт `/api/v1`, JSON UTF-8;
OpenAPI та schema fixtures для Python↔TS, без drift між валідаціями. UI стан
`SAVING` → `MAC_SAVED` тільки після committed receipt; `FAILED` з можливістю повтору.
Немає «на телефоні», «синхронізовано» чи «очікує AI» без відповідного runtime.

| Операція | Контракт |
|---|---|
| `GET /api/v1/status` | Auth required; schema version, `provider=OFF`, `storage=LOCAL_MAC`; без OS paths/контенту |
| `POST /api/v1/entries` | `operation_id`, клієнтський `entry_id` UUID, `base_revision=0`, typed payload; 201 receipt після DB commit |
| `GET /api/v1/entries` | Фільтри type/tag/local-date range, literal text `q`, стабільний порядок `(created_at_utc,id)`, opaque cursor; немає довільного SQL/FTS expression |
| `GET /api/v1/entries/{id}` | 200 current entry, 404 unknown, 410 deleted; IDs не обходять owner scope |
| `GET /api/v1/entries/{id}/revisions` | Auth + owner scope, paginated chronological history; 410 після purge |
| `PATCH /api/v1/entries/{id}` | `operation_id`, `base_revision≥1`, changed allowed fields; 200 receipt, append попередньої версії + index update атомарно |
| `DELETE /api/v1/entries/{id}` | `operation_id`, `base_revision≥1`; 200 receipt; purge тексту/current/history/index + tombstone в одній transaction |
| `POST /api/v1/exports/preview` | Validated explicit selector types/date/IDs + `include_history`; count, chosen sections, disclosure warning; session-bound plan ID із exact IDs/revisions і TTL 5 хв; не читає файли за client path |
| `POST /api/v1/exports` | Plan ID та формат JSON/Markdown; явний click; changed/deleted revision або expired plan →409 і новий preview; local download, без зовнішнього destination |

Mutations: server перевіряє auth/owner, schema, limits, tombstone, revision,
idempotency до write. Receipt і всі domain changes — одна transaction. Повтор
ідентичної операції повертає той самий receipt без нового ефекту. Reuse operation_id
з іншим payload/action/entry →409; stale revision →409 `REVISION_CONFLICT` без overwrite.
Після delete tombstone має пріоритет над старим create/edit і колишнім receipt:
повтор delete повертає deletion receipt, старий create/edit →410, відновлення за тим
самим ID заборонено. При rollback receipt не існує; retry може виконати операцію.
Receipts не повертають текст, current entry отримується окремим GET.

Error body: stable `code`, synthetic/random `request_id`, bounded field names;
ніякого echo body, SQL, stacktrace або абсолютних шляхів. 401 unauthenticated,
403 origin/CSRF policy, 404 unknown, 409 conflict, 410 tombstone, 413 body limit,
422 schema, 503 storage unavailable/maintenance. Disk-full/read-only/commit error
не дає success receipt; введений текст лишається в UI memory для повтору.

Bind лише `127.0.0.1`, exact Host/Origin allowlists з явним портом. UI та API same
origin у кінцевому локальному build; dev proxy — exact origin, без wildcard CORS.
Навіть local API потребує auth. Перед server start локальний launcher створює
короткоживучий one-time unlock code, показує його локально; UI вводить у POST body.
Session credential — випадкова, host-only HttpOnly SameSite=Strict cookie, idle
expiry/auto-lock 15 хв, absolute expiry 8 год, server-side logout/revocation;
auth/entry content не логуються. Unlock endpoint також має Host/Origin validation,
bounded attempts (5/minute), one-time code TTL 5 хв. Не токен у URL/localStorage.
Mutations вимагають explicit allowed Origin і session-bound CSRF header, зокрема
export. Cross-site requests, missing/forged Origin, DNS-rebinding Host →deny.
HTTP допустимий лише на loopback у synthetic M1; HTTPS/real-data gate — окремо.

UI рендерить plain text, без raw HTML/active Markdown, remote images/fonts/analytics;
локальний CSP. Keyboard navigation, labels, pending/error/conflict states й
підтвердження delete обов’язкові. Auto-lock приховує контент і очищує UI memory;
reload без auth не отримує журнал. Підтримка Mac asleep/browser-server stopped
чесна: M1 не зберігає offline browser drafts на диск, unsaved ≠ saved.

## Data root і міграції

Explicit data root обов’язковий, без fallback у cwd/repo. Для M1 — newly-created
synthetic temp directory поза repo, з lifecycle, контрольованим test harness.
Ніколи не підставляти існуючий реальний vault. Resolve/canonicalize root до write:
відхилити repo/subtree, будь-який Git worktree, symlink components, недоступний шлях;
all resolved storage children всередині root, без `..`/symlink escape. При заданому
невідомому існуючому root з іншим manifest — STOP, не перезаписувати.
Directory permissions 0700, файли 0600; logs теж приватні, без payload/auth.
Поділ каталогів не є OS sandbox або доведеним encryption-at-rest.

Schema version + forward transactional migrations. New vault →version 1; same
version restart →no-op; newer unsupported version →refuse без write. Перед
upgrade — consistent backup; exception/failure leaves previous schema usable;
ніякого автоматичного downgrade/reset. Перевірити `foreign_keys` та DB integrity.
M1 додасть synthetic old-schema fixture і failure injection, не реальну міграцію.

## Export, backup, restore і deletion

Portable JSON: versioned manifest (`export_schema_version`, source vault ID,
UTC export time, selector, record counts, content SHA-256), exact current entries,
optional revisions. JSON — lossless portable format; Markdown — лише читабельне
представлення з escaped filenames (opaque ID), не незалежна canonical DB.
Raw Unicode, unknown/null і timestamp semantics зберігаються. Експорт не включає
sessions/auth, live tombstone journal, logs/OS paths або приховані deleted тексти.
Preview та явне локальне підтвердження; UI повідомляє, що файл містить чутливі дані.
Portable round-trip у synthetic standalone validator/repository доводить рівність;
public import endpoint і автоматичний merge не потрібні в M1.

Backup — full current vault, schema metadata, tombstones, revisions, manifest і
hashes; auth secrets excluded. SQLite consistent backup API, не raw copy лише DB
при активному WAL. Поля attachments у manifest — порожні: їх capture поза M1.
Тест DB+manifest integrity та явне reject unexpected attachments/missing files;
attachments consistency до появи attachment module не називати протестованою.
Backup write — temporary artifact →atomic completion; partial файл не валідний.

Maintenance backup/restore — локальний CLI/service boundary, не HTTP довільний
filesystem path. Source/target явні; canonicalization і symlink checks перед read;
тільки відомі synthetic inputs у dev. Restore лише в новий порожній root: reject
non-empty/current active root; validate manifest/version/checksums/integrity до
activation. Fail не змінює source/live root. Restore increment `restore_epoch`
і помітити `RESTORED_REQUIRES_RECONCILIATION`; навіть до M2 нема silent future replay.
Відновлення старого backup може повернути тодішній текст локально — це явний
результат restore з підтвердженням; автоматична синхронізація до reconciliation
заборонена. Transport/full-resync/re-pair реалізуються лише в M2.

Delete прибирає current/revisions/derived index та content fingerprints і залишає
мінімальну tombstone; тести перевіряють API, SQL та rebuild index. SQLite pages/WAL,
OS snapshots, exported files і старі backups можуть містити попередні байти:
не обіцяти forensic secure erase. M1 документує retention/whole-backup deletion,
не змінює чужі backups. Encryption/key recovery/FileVault verification та дозвіл
власниці — gates перед real use, не привід дозволити приватні дані на M1.

## Fixtures, перевірки й acceptance evidence

Fixtures явно `SYNTHETIC`, вигадані короткі українські тексти без запозичень із
приватного контексту. Coverage: чотири типи, Unicode/emoji, null і zero, tags,
midnight/DST, duplicate IDs, stale revisions, deleted entry, malformed exports,
injection-shaped inert text, huge/invalid inputs, disk/transaction failure.
Тести використовують лише нові tmp roots; cleanup не торкається невідомих шляхів.

| Gate | Відтворюваний результат M1 | Зв’язок із загальною матрицею |
|---|---|---|
| M1-A01 | Create/read/edit/type-change/search/delete усіх типів, збережений original/history, purge після delete | PR-01/02/05/10, T12/13 |
| M1-A02 | No internet/provider + restart/crash; committed запис є, failed transaction не дає receipt | T01, provider OFF |
| M1-A03 | Duplicate operation →one effect; payload reuse і stale revision →409; delete+stale write →410 | T02, локальна частина T03/04 |
| M1-A04 | Offset-aware DST, midnight, zone change, unknown≠zero; sleep day та UTC duration | T05 |
| M1-A05 | Live-WAL backup/reopen/restore + checksum failure + unsupported schema + non-empty target reject | DB частина T06; metadata частина T07 |
| M1-A06 | Repo/symlink/escape/unknown root denied; invalid migration rollback; no private-root writes | T11/12/30 локально |
| M1-A07 | API rejects unauth, foreign owner, malicious Host/Origin/CSRF, oversized fields; no payload in errors/logs | T10/12/16 |
| M1-A08 | Lossless selected JSON round-trip; Markdown text escaped; preview selectors не розширюються | PR-05/13 частково |
| M1-A09 | Browser UI capture/search/edit/delete/export, keyboard, restart, failure/conflict/lock; inert HTML/script text | UI smoke, T16 |
| M1-A10 | Public tracked/staged/all-object privacy scan + no provider/network egress за negative test | T08 лише OFF, T16 |

T03/04 cross-device, T07 sync, T08 live consent, T09 billing, T11 AI sandbox,
T14/15 feedback, T17–29 ASR/health/clinical/game/PWA — DEFERRED з milestone refs,
ніколи PASS за локальними fixtures. Performance: виміряти save/search, memory/idle
на synthetic dataset, записати environment/N/method; SLO запропонувати після виміру,
без вигаданого hardware benchmark. Real Android/hardware/private security — NOT_RUN.

M1 handoff: exact base/C/R/branch, reproducible commands з versions/exit codes,
OpenAPI/schema fixtures, migration/backup manifest evidence, synthetic browser
screenshots + console/network check, test output, privacy scan та відомі обмеження.
Оновити STATE/HANDOFF/roadmap/devlog/report і regenerated context. Статус виконавця
`AWAITING_REVIEW`. Data-loss/auth-bypass/schema-corruption test failure — hard stop
для acceptance; звичайні engineering помилки виправляються в межах M1.

## Рішення для старту

M0 review and M1 execution goal supplied; no start authorization blocker. Відсутні
FastAPI/Uvicorn/pytest/Alembic не блокують M0: у M1 обрати сумісні versions,
project-local environment і lockfiles; якщо dependency fetch недоступний — exact
blocker без global install/sudo. Візуальний стиль M1 — нейтральний мінімум,
Impeccable при реалізації UI. Ліцензія, бренд, private HTTPS, encryption/key recovery,
retention/права runtime Codex/MiniMax та clinical review — later gates,
не потрібні для synthetic local CRUD. Архітектурного відхилення немає.
