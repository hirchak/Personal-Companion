# M1 — повноцінний локальний щоденник без AI

**Goal ID:** M1_LOCAL_JOURNAL
**Версія ТЗ:** 1.0 · 2026-09-30
**Рекомендований repository path:** `prompts/M1_LOCAL_JOURNAL.md`
**Режим:** автономне виконання одного milestone, включно з перевіркою та виправленнями.
**Рекомендована модель:** GPT-6.1 Sol.
**Reasoning:** High, якщо підтримується фактичним установленим клієнтом.
**Plan Mode:** OFF. Внутрішній план потрібний; не завершуй роботу лише планом.

## 1. Мета і право виконання

Перетвори документаційний Personal Companion на реально працюючий локальний застосунок
M1: зручне введення українських нотаток, сон/день/творчість, редагування й історія,
пошук, видалення, захищений локальний API, переносимий експорт і перевірений backup/restore.
Працюй до цілісного review-ready результату, а не лише до створення skeleton або mock UI.

Власник передає цю goal для роботи без постійного супроводу протягом ночі. Це не вимога
працювати певну кількість годин: коли DoD виконано, завершуй. Не розширюй scope тільки
тому, що залишився час. Не переходь до M2 або іншої milestone без нового рішення.

Передавання власником цього ТЗ з `/goal` є дозволом виконати **M1 у визначених нижче
межах**, з проєктними залежностями, synthetic test data, локальними процесами та normal
push у main. Чинні client/OS permissions не обходити.

## 2. Перевірена стартова база і рішення архітектора

Repository: https://github.com/hirchak/Personal-Companion.git
Development/default branch: `main`.

| Ref | SHA |
|---|---|
| M0 C3, переглянута реалізація workflow | `bc5cf13c3a3569edd0e0c9d9d157889471d0a0bd` |
| M0 evidence R4 | `7ecd3f025793213089b801947deb91c4c800d658` |
| M0 R5, перевірений main tip / base M1 | `175fc934ad16552759273d2ed6770835b6f28786` |

**Рішення архітектора: M0 = ACCEPT у межах engineering/bootstrap.**
Main/default, конфігурацію direct-main, фактичні diffs і code/tests перевірено через
GitHub connector. Незалежно відтворено 25 tooling-тестів на source fixture зі звіреними
Git blob hashes scripts/tests. Усі 47 context sources звірено з R5. Повний exact Git
checkout/history scan у reviewer container не виконувався; це не app/clinical/hardware
validation. M1 на R5 ще не реалізований.

**Неблокуюче M0-N01:** звіт посилається на відсутній tracked
`reports/evidence/M0/C3_CHECKS.json`; точний GitHub fetch повернув 404. У R5 evidence також
залишились stale PENDING-поля. На початку M1 усунь недостовірні/мертві evidence pointers.
Віднови справжні збережені результати або зроби новий відтворюваний rerun точного C3 з
актуальною датою. Не вигадуй історичні логи, не підміняй C3 новим кодом. Не роби з цього
окремий цикл дозволів або серію post-push attestation commits.

Запиши це зовнішнє рішення в `reports/M0_ARCHITECT_REVIEW.md`; зазнач джерело — передане
архітектором ТЗ, а не self-approval Codex. `last_reviewed_sha` має відповідати C3.
Після цього активуй M1 у STATE/HANDOFF і працюй далі в цій самій goal.

На старті перевір actual HEAD, origin URL, main і worktree. Очікуваний base — R5.
Сам цей наданий файл ТЗ може бути єдиною новою untracked зміною; це не blocker.
Якщо origin/main має невідомі нові зміни — не reset/force-push: з'ясуй зміни, не
перезаписуй чужу роботу. За істотного конфлікту scope зафіксуй blocker.

## 3. Inputs і пріоритет контракту

Спочатку прочитай AGENTS.md, STATE.md, HANDOFF.md, `.project/project.json`,
`docs/WORKFLOW.md`, це ТЗ та **`docs/M1_CONTRACT.md`**. Потім точково:
ARCHITECTURE, DATA_MEMORY, PRIVACY_SECURITY, TESTING, EXPERIENCE, INSTALLATION.
Не підвантажуй усі research-файли й історію чату заради повноти.

Основа M1 — контракт v1 на R5:
- Git blob: `7c302016749ff761b4f4a01f336369cd24da3048`.
- SHA-256: `5292d481d790b237d4b385339652f986de7e73682269276b8b07bddae8b66fa0`.

Це ТЗ явно дозволяє реалізацію M1 та уточнює нижче кілька engineering-семантик.
Внеси уточнення в контракт із change note/version; не змінюй його приховано.
Для несуттєвого внутрішнього refactor не потрібне погодження. Зміна trust boundary,
вмикання cloud/phone/clinical функцій або послаблення інваріантів не дозволені.

## 4. Кінцевий результат

| Частина | Потрібний результат |
|---|---|
| Локальний застосунок | Python/FastAPI/Pydantic + SQLite, React/TypeScript/Vite; одна логіка предметної області |
| Інтерфейс | Український capture через «+», записи `inbox`, `daily`, `sleep`, `creative`, пошук/фільтри/редагування/історія/видалення |
| Надійність | Підтвердження тільки committed save; restart durability, transaction rollback, idempotency, revision conflicts |
| Локальна безпека | Loopback-only API, auth, Host/Origin/CSRF, auto-lock, нейтральні errors/logs, інертний рендеринг тексту |
| Дані | Окремий explicit synthetic data root поза Git, schema version, перевірені migration failure cases |
| Переносимість | Selected JSON/Markdown export з preview; consistent SQLite backup та restore у новий root |
| Докази | Automated unit/contract/integration/browser tests, commands/versions/exit codes, відомі межі |
| Передавання | Простий запуск demo, README/runbook, STATE/HANDOFF/report, coherent C/R, normal push main |

Немає вимоги будувати складний installer або багатокористувацький SaaS. Достатні
надійні project-local setup/start/stop/verify та maintenance команди з чіткою інструкцією.

## 5. Домен, транзакції та часові дані

Реалізуй логічні сутності й інваріанти M1_CONTRACT: vault metadata, entries,
entry revisions, minimal tombstones, operation receipts, rebuildable live search index.
Фізичні таблиці, repository pattern та SQLAlchemy/Alembic чи інший простий спосіб — твій
вибір у межах стеку. Не створюй десятки порожніх сервісів на майбутнє.

Raw Unicode-текст зберігається точно, без trim/переписування/модельного виправлення.
Зміна типу/тегів не змінює текст. Втрата несумісних typed fields при type-change потребує
явного підтвердження в UI, попередня версія доступна в history до delete.

Повтор тієї самої operation має один ефект. Інший payload під тим самим operation_id
не перезаписує результат. Stale revision дає conflict, не last-writer-wins.
Delete атомарно прибирає current/history/index/content fingerprints; tombstone не містить
нотатку. Stale create/edit після delete не відновлюють текст. Тести мають звертатися і
до API, і до справжньої SQLite, а не доводити все лише mocks.

Nullable ratings і часові поля залишаються nullable; 0 не замінює unknown. Для sleep
всі timestamps — **оцінки користувача**, не wearable/клінічні вимірювання.
**Різницю wake−start називай часовим інтервалом за введеними оцінками**, а не точною
тривалістю фактичного сну, TST чи sleep efficiency. Усередині можуть бути пробудження,
які M1 не вимірює. Не додавай норм, діагностичних порогів, sleep restriction, кортизолу,
«5 хвилин на кожне пробудження» або розрахунків із неперевіреного R02.

Початкова IANA zone Europe/Warsaw; зберігай UTC, zone і local_date за контрактом.
Не домислюй годину для запису лише з датою. DST, ніч через північ, offset-aware input,
редагування часу, unknown/date/instant і зміна системної timezone мають бути тестами.
Не називай reference hardware реально перевіреним, коли тестував лише на іншій машині.

## 6. API, локальний доступ і UI

Реалізуй `/api/v1` та операції з M1_CONTRACT. Для auth додай мінімальні зрозумілі
unlock/session/lock маршрути й задокументуй схеми. `owner_id` визначається сервером;
клієнт не отримує способу довільно вибирати власника/версію/клас приватності.
OpenAPI та Python↔TypeScript contract fixtures не повинні розходитися.

Loopback `127.0.0.1`, exact Host і дозволені Origins з портом; ніякого `0.0.0.0`, wildcard
CORS, LAN/tunnel чи public URL. Підсумковий UI/API same-origin. Dev proxy допустимий
із точним allowlist; development convenience не потрапляє як обхід у normal build.

One-time unlock code показується локальним launcher, не у URL і не в persistent logs.
HttpOnly host-only SameSite=Strict session cookie, revocation/logout, idle/absolute
expiry за контрактом. Дозволений локальний HTTP — тільки synthetic loopback M1,
без заяв про production HTTPS або шифрування сховища.

**Уточнення origin/CSRF:** перевірки застосовуй до конкретних типів запитів.
Звичайний same-origin GET може не містити Origin: не ламай початкове завантаження.
Mutations/exports вимагають exact allowed Origin і session-bound CSRF. Unlock ще не
має session CSRF, тому захищається one-time code, exact Host/Origin, request format,
TTL та bounded attempts; не роби постійного auth-exempt bypass. Опиши bootstrap flow
і протестуй його браузером, включно з cross-origin negative cases.

Приватні API/auth відповіді — `Cache-Control: no-store`; не клади entries у browser
storage, service worker або кеш статичних ресурсів. PWA та persistent offline drafts
належать M2. Auto-lock прибирає відображений текст і очищує пам'ять UI за контрактом.
Не обіцяй збереження незбереженої чернетки після reload/lock. За звичайної save-помилки
текст лишається в поточному unlocked UI для повтору.

Інтерфейс має виглядати як невеликий закінчений продукт, а не технічна таблиця:
простора читабельна типографіка, одна очевидна кнопка додавання, поступове відкриття
optional fields, добрі empty/loading/error/conflict стани, keyboard/focus/labels.
Мінімальний «Сьогодні» може показувати останні записи без health score чи streak.
Не заповнюй екрани несправжніми AI/chat/мікрофон/watch кнопками.

Текст відображається як інертний plain text; user Markdown/HTML/скрипти не виконуються.
Немає зовнішніх fonts/images/analytics. Ресурси локальні; CSP сумісний із зібраним UI.
Існуючі доступні UI skills можна використати в їхніх межах; відсутність певного skill
не є blocker. Не встановлюй невідомий plugin і не підключай зовнішній design provider.

## 7. Data root, backup, restore, export

Весь data plane M1 — **новостворені synthetic каталоги поза repo**. Дозволений чітко
позначений persistent synthetic demo root для ручного ранкового перегляду; tests
використовують ізольовані disposable roots. Ніколи не відкривай реальний vault.
Demo initializer не перезаписує невідомий існуючий root, не сканує домашні папки.

Directory/file permissions, path canonicalization, symlink/escape/інший Git worktree
відхиляються за контрактом. macOS має системні alias paths на кшталт temp-каталогів:
отримай canonical системний temp parent перед створенням нового test-root, не
послаблюючи захист довільних user-supplied symlink roots. Cleanup видаляє тільки явно
створені цим test harness каталоги; не використовуй широку очистку чужих temp/data.

Migration: new schema, no-op restart, unsupported-newer refuse; rollback на injection
failure; consistent backup перед upgrade. Ніякого implicit reset при помилці.

Export: explicit selector, preview exact IDs/revisions, session binding і expiry;
зміна/видалення після preview скасовує план. JSON — lossless portable representation,
Markdown — escaped readable representation. Збережи Unicode, null і часові семантики.
Немає зовнішнього destination, автоматичного імпорту або передачі іншій AI.

Backup виконується механізмом узгодженого SQLite snapshot із активним WAL, а не
копією лише основного DB-файла. Manifest/checksums, partial-file rejection; auth/session
секрети виключити. Attachments у M1 відсутні — не вигадуй пройдених media-тестів.

Restore — тільки новий порожній root, після перевірки manifest/schema/checksums/DB
integrity. Пошкоджений backup не торкається live/source root. Інкремент restore_epoch,
позначка reconciliation для майбутнього sync. Ніяких phone transports у M1.

Технічний M1 використовує лише synthetic дані; encryption/key recovery/FileVault та
реальний private rollout залишаються окремими gates. Документація не обіцяє forensic
erase: видалені SQLite байти/старі backups/exports можуть зберігатися поза current DB.

## 8. Дозволені ресурси та мережа для розробки

Дозволено налаштувати project-local Python environment, Node dependencies і lockfiles;
завантажити потрібні звичайні open-source packages із офіційних registries, офіційну
документацію та один необхідний Chromium runtime для browser tests, якщо його немає.
Вибирай сумісні підтримувані версії й фіксуй їх; не оновлюй усе до latest без потреби.

Це **build-time** доступ. Runtime app не виконує зовнішніх запитів. Верифікуй deny-egress
для свого backend/browser session після встановлення. Не відключай інтернет на всьому
Mac, не змінюй глобальний firewall і не заважай поточній development-сесії Codex.

Не використовуй sudo/global install/Homebrew system upgrade. Потрібні custom cache
locations можуть бути project-local або новим dedicated synthetic/dev-cache root;
не читай чужі caches/auth/private folders. Не виводь секрети з environment або Keychain.

Виконання цієї engineering-goal в уже обраній development-сесії Codex дозволене.
Заборона provider calls нижче означає **додаткові runtime/API/CLI smoke виклики моделей
із застосунку/скриптів**, не заборону самому Codex виконувати видану goal. Не запускай
вкладені codex exec/provider jobs, не підключай MiniMax, не обходь квоти.

Нові GitHub Actions workflows, self-hosted runners, CI secrets і витрати не потрібні
для M1 і не дозволяються цим ТЗ. Наявні run results можна прочитати; CI NOT_RUN не
підмінює локальні тести. Vercel/deploy/release/account зміни — OFF.

## 9. Що врахувати з нових вимог, не розширюючи реалізацію

Онови **технічний reference hardware** в PRODUCT/INTEGRATIONS/OPEN_QUESTIONS:
Samsung Galaxy Watch7 — модель повідомлена власником; app/firmware versions,
available fields і hardware compatibility **NOT_VERIFIED**. Не проси модель годинника
повторно й не пробуй підключатися до нього в M1.

Власник уже завантажив R01/R02/R03 DOCX у ChatGPT Project. Дозволена лише metadata
позначка «отримані зовні; evidence/content review не завершено; до repo не ingest-овані».
Не відкривати їх за цією goal, не витягувати claims/tests і не публікувати файли.
Доступність research не перетворює neutral journal M1 на validated sleep diary.

Для майбутнього UX можна зафіксувати **знеособлений design backlog**:
optional evolving personal space / life-simulation, creative-studio metaphor,
fantasy/medieval cosmetics, travel/culture-inspired themes з neutral-mode parity.
Це відкладені кандидати, не затверджена тема. Не переносити точні персональні
вподобання, улюблені фільми/ігри або плани подорожей у public profile, fixtures чи assets.
M1 лишається нейтральним і корисним без гри.

## 10. Перевірки й критерії приймання

План реалізації та порядок підзадач вибери сам. Обов'язково покрий gates
**M1-A01–M1-A10** існуючого M1_CONTRACT з посиланням на конкретні тести/докази.

| Gate | Що має бути доведено |
|---|---|
| A01 | CRUD/type-change/history/search/delete для всіх 4 типів; original text і purge |
| A02 | Save/restart/process failure на справжній SQLite; failed commit не видає success |
| A03 | Duplicate operation, payload reuse, stale revision, race/concurrent write, tombstone precedence |
| A04 | Unicode/emoji, ratings null/zero, timestamps/midnight/DST/IANA, interval не клінічний TST |
| A05 | Backup активного WAL → restore; corruption/version/non-empty target/partial artifact rejection |
| A06 | Data-root isolation, permissions, symlink/path escape/невідомий root, migration rollback |
| A07 | Auth/unlock/expiry/revoke, owner boundary, Host/Origin/CSRF, limits, без private payload у errors/logs |
| A08 | Preview-bound selected JSON round-trip, Markdown escaping, cancelled stale/expired export |
| A09 | Справжній browser flow create/edit/search/history/delete/export/restart/lock; console/network; інертний HTML |
| A10 | Public-data/secrets scan worktree/staged/Git objects/generated + окремий runtime no-egress test |

Синтетичні приклади — явно вигадані короткі українські тексти без запозичення з особистої
історії, research кейсів або чужих книг. Не вимірюй успіх кількістю tests замість покриття.
Додай failure injection для disk/storage/transaction проблем у контрольованих тестах;
не заповнюй справжній диск і не змінюй права чужих каталогів.

Browser tests не замінюй скриншотом статичного mock. Smoke має використовувати справжній
backend і temporary SQLite. Local-only test screenshots можна додати в явно названий
`reports/evidence/M1/ui/` лише після перевірки, що це viewport synthetic demo без desktop,
auth-кодів, account IDs і локальних приватних шляхів. Великі videos/traces/DB/ZIP —
лише ignored generated artifacts, не public repo. Не послаблюй broad deny rules заради screenshots.

Проведи короткі відтворювані вимірювання save/search/restart та memory/idle на обмеженому
synthetic наборі. Укажи фактичне середовище, N, метод і результати; не називай вимір на
іншому стенді benchmark цільового M2/16GB. Не роби багатогодинний stress-loop заради ночі.

Documentation tooling можна адаптувати для source code/lockfiles/свідомо дозволених
synthetic fixtures: додай вузькі тести і пояснення. Не обходь checks видаленням тестів,
підміною expected values без аргументів або глобальним ігноруванням findings. Особливо
не знімай захист raw/private/secrets. Snapshot source map не міняй без потреби;
динамічні goal/contract/report pointers вже підтримуються.

## 11. Автономність і відновлення роботи

Самостійно плануй, реалізуй, перевіряй та виправляй звичайні engineering помилки всередині
scope. Не запитуй власника про назви CSS-класів, внутрішні таблиці, порядок робіт або
косметику. За відсутності рішення майбутнього етапу обери задокументований safe default.

Працюй послідовними coherent checkpoints; після compaction перечитуй STATE/HANDOFF,
це ТЗ та фактичний diff. Не записуй приховані міркування; потрібні лише рішення,
виконаний результат, blocker і next step. Не запускай нескінченні retry/benchmark loops.

На істинному blocker зупини тільки залежну/небезпечну частину; незалежні безпечні
підзадачі M1 продовж. Якщо повний DoD недосяжний у доступній сесії, залиш працездатний
перевірений піднабір, точний статус незавершених gates і команду відновлення. Не
називай повний M1 завершеним і не починай M2. Ліміти клієнта не обходити іншим billing route.

## 12. Публікація й evidence без зайвих циклів

Owner standing permission: normal fast-forward push **безпосередньо `main`** після
перевірок поточної goal. Не проси ще один дозвіл на цей routine push.

C — фінальний coherent implementation commit, який включає код/контракт/тести та
нові чи змінені правила tooling. R — наступний status/report/evidence-only commit.
Додаткові implementation checkpoints дозволені, але фінальний C позначає останній
код; будь-який code change після нього вимагає нового C і релевантного rerun.

Перед фінальним C і push перевір правильний repository/ref, clean дозволений diff,
secrets/privacy/materials. Після C перевір exact C у контрольованому clean source
workspace; його tests мають пройти без читання чужих даних. Artifact-local paths
у звіті санітизуй. Опублікуй потрібні компактні evidence, а не лише слова PASS.

Кожний evidence record: actual command, environment/version, SHA або чесно позначений
staged-tree scope, run time, exit code, короткий stdout/stderr/result і реальний path.
Перевір існування всіх referenced evidence paths. Відсутнє — NOT_RUN/NOT_AVAILABLE,
не вигадана назва. Hash manifest не підтверджує факт запуску сам по собі.

Після R зроби normal push, перевір remote SHA. **Не створюй R+1/R+2 лише для запису
власного SHA чи підтвердження попереднього push.** R містить pre-push status; post-push
receipt і точні C/R/remote SHA поверни у фінальному повідомленні. Наступна реальна goal
може записати ці факти. Місцеві regenerated snapshots не треба комітити.

`main` після push містить development candidate, не accepted release. На завершенні:
M1 implementation/review = AWAITING_REVIEW або чесний BLOCKED; M0 accepted record
збережений; M2+ NOT_STARTED. Codex не підписує ACCEPT за власну роботу.

## 13. Hard stops

Не читати/імпортувати/seed-ити реальний vault, приватний додаток, raw research, auth
storage чи чужі home folders. Не публікувати особисті нотатки, source PDFs/DOCX, книги,
запозичені game/media assets, secrets або generated private payload.

Не робити live runtime/provider/API/ASR calls, nested model jobs, billing fallback,
нові accounts/credentials, транскрипцію реального голосу, Health Connect, Telegram,
PWA/phone sync, LAN/tunnels/TLS-install, launchd/autostart, deployment/tag/release,
CI setup, глобальні установки або sudo. Не вмикати жодного clinical module.

Не force-push, не переписувати published history, не стирати невідомі local changes,
не merge-ити паралельну чужу роботу. Якщо захист даних/auth/schema ще має невиправлені
блокуючі дефекти, **не публікуй це як готовий застосунок**. Виправ у scope; якщо не
вдається — safe checkpoint/звіт, без небезпечної app delivery у main. Дозволений
окремий safe documentation-only forward checkpoint з описом blocker.

## 14. Definition of Done і фінальний handoff

Повний M1 вважається готовим для review, коли працює локальний end-to-end сценарій,
M1-A01–A10 мають фактичні докази, app не потребує зовнішнього inference, data root
ізольований, backup/restore перевірений, UI запускається з інструкції, фінальні C/R
нормально pushed у main й STATE/HANDOFF/report відображають реальність.

Основний звіт: `reports/M1_LOCAL_JOURNAL_REPORT.md`.
STATE pointers: `current_goal_path=prompts/M1_LOCAL_JOURNAL.md`,
`current_contract_path=docs/M1_CONTRACT.md`, `report_path` — фактичний M1 report.
Онови roadmap/devlog/README та згенеруй context snapshots через поточний скрипт.

У фінальній короткій відповіді власнику наведи:
- зроблено / не зроблено, без клінічних чи device claims;
- exact base, C, R, origin/main SHA і push status;
- tests/critical gates/privacy/CI, з чесними NOT_RUN;
- repository-relative report path;
- **точну команду setup/start synthetic demo**, спосіб unlock і stop;
- що власник побачить у браузері, та blockers, якщо лишились.

Використання реальних записів — окремий наступний дозвіл і security gate.
На цьому завершуй роботу й чекай незалежного review; нічого більше автоматично не починай.
