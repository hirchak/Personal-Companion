# M2 — Offline-first Android PWA + безпечна синхронізація з Mac

**Goal ID:** M2_OFFLINE_PWA_SYNC\
**Версія ТЗ:** 1.0 · 2026-10-01\
**Repository path:** `prompts/M2_OFFLINE_PWA_SYNC.md`\
**Рекомендована модель:** GPT-6.1 Sol\
**Reasoning:** High, якщо доступно у фактичному Codex\
**Plan Mode:** OFF\

## 1. Мета

Розширити прийнятий M1 до M2 engineering candidate: той самий Personal Companion має працювати як offline-first PWA на Android, дозволяти створювати й редагувати synthetic записи без доступного Mac, надійно зберігати локальну чергу, а після повернення з’єднання синхронізуватися з Mac без дублів, silent overwrite або resurrection видалених записів.

M2 не додає AI, голосове ASR, Samsung Health/Watch, клінічні протоколи, гейміфікацію, Vercel deploy або реальні приватні дані. Не переходь до M3+.

Працюй автономно до цілісного review-ready результату: design/contract → implementation → tests/fixes → C → evidence-only R → normal fast-forward push у `main` → зупинка до незалежного review.

## 2. Перевірена база

Repository: `https://github.com/hirchak/Personal-Companion.git`\
Default/development branch: `main`.

Перевірений M1:

- M1 implementation C: `fd056cc4e91b826a032a871381dbf3a64180bd44`
- M1 evidence R / current `main` на момент видачі goal: `b4c8af5f975e1a92c6d06fd023b82155cae6fc73`
- Architect verdict: **M1 = ACCEPT у визначеному engineering/synthetic scope**.
- CI: `NOT_RUN`.
- Real/private data, actual Android transport, encryption-at-rest rollout, FileVault, AI, deploy і clinical scope не були цим ACCEPT підтверджені.

На старті:

1. Перевір actual `origin/main`, HEAD, worktree, STATE/HANDOFF, `.project/project.json`.
2. Якщо `origin/main` уже містить невідомі commits після вказаного R — не reset і не force-push; розбери зміни й збережи чужу роботу.
3. Запиши зовнішнє M1 ACCEPT як durable review record (`reports/M1_ARCHITECT_REVIEW.md`) і онови `last_reviewed_sha` на M1 C. Це рішення архітектора, не self-approval Codex.
4. Неблокуючий carry-over: UI M1 підписує список «Останні записи», тоді як backend сортує записи за `(created,id)` у зростаючому порядку. Виправ semantics так, щоб default list справді показував найновіші записи першими, з правильною cursor-pagination, і додай regression test.
5. Створи/онови `docs/M2_CONTRACT.md` як стислий execution contract для цієї goal. Не зупиняйся на planning-only результаті.

## 3. Канонічні inputs

Спочатку прочитай тільки необхідне:

- `AGENTS.md`
- `STATE.md`
- `HANDOFF.md`
- `.project/project.json`
- `docs/WORKFLOW.md`
- `docs/M1_CONTRACT.md`
- `docs/OFFLINE_SYNC.md`
- `docs/PRIVACY_SECURITY.md`
- `docs/ARCHITECTURE.md`
- `docs/TESTING.md`
- `docs/INSTALLATION.md`
- це ТЗ.

Точково читай актуальний M1 code/tests. Не ingest-ити raw R01/R02/R03 DOCX і не підвантажувати весь research corpus.

## 4. Scope M2

Потрібний кінцевий результат:

### A. Offline-capable PWA

Існуючий React UI має стати installable PWA з локальним app shell, manifest і service worker.

Після першого завантаження synthetic build повинен:

- відкриватися без Mac/API/network;
- дозволяти створити/відредагувати/видалити локальний запис;
- показати чесний статус збереження;
- не називати локальний запис «збереженим на Mac», поки немає durable Mac receipt;
- пережити reload/restart браузера;
- не залежати від cloud AI/provider.

Service worker кешує app shell/static assets, але не кешує приватні API responses як substitute database. Не будуй background server у service worker і не обіцяй гарантований background sync, коли browser/OS його не гарантує.

### B. Phone local store + outbox

Додай local PWA storage (IndexedDB або інший browser-native store, якщо обґрунтовано) з versioned schema.

Кожна локальна mutation повинна мати щонайменше:

- `operation_id`
- `device_id`
- `entry_id`
- `base_revision`
- `operation_type`
- `created_at_utc`
- `timezone`
- schema version
- локальний state
- protected payload.

Локальний запис і outbox mutation мають фіксуватися атомарно настільки, наскільки дозволяє обраний browser store. UI не показує `LOCAL_SAVED` до успішної local transaction.

Стани синхронізації мають бути явні та відокремлені від AI:

`LOCAL_SAVED → QUEUED → SYNCING → MAC_CONFIRMED`

окремо `CONFLICT` / `FAILED` / `REVOKED_OR_REPAIR_REQUIRED` (або семантично еквівалентні чіткі стани).

AI status у M2 завжди OFF/NOT_REQUESTED.

### C. Захист локальних phone payloads

M2 має мати реальну application-level at-rest protection для synthetic PWA payloads, а не лише назву `encrypted`.

Перед реалізацією зафіксуй security decision/ADR:

- стандартний browser crypto primitive/library;
- KDF/key derivation або інший unlock mechanism;
- salt/nonce rules;
- key lifecycle;
- що зберігається в IndexedDB;
- що існує тільки в memory;
- що відбувається при lock/reload;
- recovery/forget-device semantics;
- known browser/OS limitations.

Не винаходь власну криптографію. Не hard-code key/passphrase у production code. Test secrets можуть бути лише явно synthetic fixtures.

Якщо browser-only key protection, яке можна чесно назвати придатним для реальних приватних даних, не вдається довести без Android Keystore/native component/system permission — **не послаблюй вимогу і не вигадуй security claim**. Реалізуй перевірюваний synthetic encrypted store, познач real-data gate `NOT_APPROVED / HARDWARE_SECURITY_UNVERIFIED` і сформулюй окремий follow-up gate.

### D. Mac sync model

Розшир існуючий Mac core, не дублюючи business logic.

Потрібні logical entities/semantics для:

- devices / pairing state;
- sync epoch;
- applied operation receipts;
- sync checkpoints;
- tombstones;
- revocation;
- conflict response.

Mac лишається canonical vault для confirmed data. Phone до підтвердження Mac є canonical holder своїх unsynced local mutations.

Sync transport — at-least-once; effect має бути idempotent. Timeout після server commit і повтор того самого packet не створює дубль.

Не використовуй wall-clock last-write-wins.

### E. Pairing і device identity

Створи вузький pairing flow для synthetic M2:

- short-lived one-time invitation;
- device-generated opaque `device_id`;
- scoped device credential/session material;
- rate limit/replay protection;
- list/revoke device на Mac side;
- revoked device не може робити новий sync.

Не передавай tokens у URL/query string. Не зберігай plaintext durable credential у `localStorage`.

Відкликання пристрою не означає remote erase його offline copy — UI/docs мають це казати чесно.

### F. Conflict handling

При stale `base_revision`:

- не overwrite автоматично;
- повернути conflict state;
- показати локальний варіант і current Mac version;
- дозволити користувачу явно вибрати Mac, phone або вручну об’єднати текст;
- результат рішення — нова mutation від актуальної revision;
- зберегти provenance/operation history настільки, наскільки це потрібно для audit/debug без копіювання private payload у logs.

CRDT не потрібен.

### G. Delete / stale device / restore epoch

Доведи сценарії:

- delete на Mac → stale phone reconnect → запис не воскресає;
- offline delete на phone → sync → повтор packet не воскресає/не дублює;
- старий client після tombstone retention/epoch mismatch не робить naive replay;
- restore старого Mac backup змінює sync epoch і блокує silent replay старої outbox;
- потрібен explicit reconciliation/full-resync/re-pair state.

### H. Safe PWA update

Оновлення app shell/service worker не повинно стирати unsynced outbox.

Перевір:

- waiting/new service worker;
- reload/update з queued mutations;
- schema upgrade local DB;
- rollback/unsupported future schema;
- update interrupted midway;
- shell version ≠ local storage version.

Не auto-activate destructive migration.

### I. Storage pressure / eviction honesty

Врахуй best-effort browser storage:

- request persistent storage, якщо API доступний;
- показати результат, а не вважати persistence гарантованою;
- quota/write failure → запис не переходить у `LOCAL_SAVED`;
- IndexedDB open/upgrade/write failure не знищує pending user text у поточній session;
- browser storage cleared/evicted → зрозумілий empty/recovery state, не вигадана синхронізація.

Додай synthetic failure injection там, де реальну eviction неможливо відтворити детерміновано.

### J. Local encrypted recovery/export для phone-only unsynced data

Додай вузький manual fallback для **unsynced local data**: export encrypted recovery package або інший чітко захищений portable artifact із schema/version/checksum.

Не називай його Mac backup. Імпорт/restore такого пакета має бути explicit і не виконувати silent merge поверх Mac.

Якщо повноцінний recovery механізм вимагає рішення, яке виходить за межі безпечного browser-only scope, зроби мінімальний encrypted export + standalone validation і зафіксуй limitation.

## 5. Transport / HTTPS ADR — обов’язково, але без прихованого remote-access дозволу

`docs/OFFLINE_SYNC.md` вимагає для реального телефона HTTPS на стабільному приватному origin Mac. M2 має зробити transport/security spike і durable ADR.

Порівняй лише реальні кандидати, підтверджені актуальною первинною документацією, наприклад:

- локальний/private DNS + cert, якому довіряє Android;
- дозволений приватний tunnel/VPN route;
- інший мінімальний private-origin route.

Окремо поясни, чому public Vercel shell або plain LAN HTTP не є автоматично безпечним replacement.

Для кожного: trust boundary, TLS/certificate lifecycle, Android installability, Local Network Access/browser constraints, router/account dependency, offline behavior, costs, privacy, revocation, operational burden.

Вибери **candidate route** для майбутнього real-device gate, але не роби дії, що потребують окремого permission:

- не встановлюй системний root CA;
- не змінюй Keychain/system trust;
- не відкривай router ports;
- не створюй tunnel/cloud account;
- не deploy Vercel;
- не вмикай remote access;
- не витрачай кошти.

Для automated M2 testing дозволений локальний synthetic HTTPS/localhost harness із test certificates/браузерними test flags **лише як test harness**, якщо файли cert/key живуть під ignored/generated temp path і ніколи не комітяться. Не представляй це як production/private-phone transport.

Якщо actual Android/Chrome test неможливий без owner interaction — статус `HARDWARE_UNVERIFIED / NOT_RUN`, не FAIL і не fake PASS. Підготуй короткий manual device-test runbook для наступного scoped gate.

## 6. Реальний Android hardware

Reference phone: Galaxy S24 Ultra. Wearable Galaxy Watch7 існує, але **M2 не читає health/watch data**.

Якщо в межах поточної автономної сесії телефон фізично недоступний або потрібні ручні дії власника, не чекай без роботи. Заверши всю незалежну synthetic implementation/test частину і підготуй exact real-device checklist.

Не проси модель телефону повторно.

## 7. Network boundaries

M1 runtime був loopback-only і deny-egress. M2 додає sync transport, тому не послаблюй network policy глобально.

Розділи режими:

- M1/local-only mode — як і раніше loopback only;
- M2 synthetic sync harness — тільки explicitly configured test origin/ports;
- future real-device mode — OFF, поки transport gate не пройдений.

Ніякого wildcard bind за замовчуванням. Якщо для synthetic multi-client test потрібен інший interface abstraction, він має бути test-scoped і не активуватися production/default config.

No analytics, remote fonts, third-party scripts, provider egress.

## 8. UI/UX

Не роби новий окремий «технічний» інтерфейс. Розшир існуючий нейтральний journal UI.

На телефоні пріоритет:

- швидка кнопка `+`;
- очевидний статус `Збережено на телефоні` / `Очікує Mac` / `На Mac` / `Конфлікт`;
- offline banner без паніки;
- список pending mutations;
- pairing/revoke/forget-device у settings;
- sync errors без втрати тексту;
- conflict resolution із двома версіями;
- storage warning/recovery action;
- keyboard/touch accessibility;
- safe-area/responsive layout.

Не додавати AI/chat/mic/watch/game placeholders, які не працюють.

## 9. Тести і acceptance matrix

Створи `docs/M2_CONTRACT.md` з чіткою матрицею, але щонайменше доведи нижче.

### M2-A01 — offline capture durability

PWA online-first install → network/Mac off → create/edit/delete → browser/page restart → локальні дані й outbox не втрачені.

### M2-A02 — idempotent reconnect

Mac повертається → queued mutation sync → response lost/timeout → retry same operation → один server effect і один logical receipt.

### M2-A03 — two-device conflict

Два simulated phone clients / phone+Mac редагують одну revision → conflict, жодного silent overwrite → explicit resolution.

### M2-A04 — tombstone / stale client

Delete + stale client reconnect не воскресає content; repeat delete/replay коректний.

### M2-A05 — time semantics

Phone capture через midnight/DST/zone change/offline wrong device clock не робить wall-clock ordering authoritative; UTC/zone/local_date semantics не регресують M1.

### M2-A06 — pairing/revocation/replay

Pair once, invalid/expired invitation rejected, replay rejected, revoke blocks new sync, іншому device credential не дає доступу.

### M2-A07 — encrypted local store

Plaintext synthetic journal payload/credential не знаходиться у persisted IndexedDB records/serialized recovery artifact поза дозволеними metadata. Wrong unlock/key не decrypt; nonce/key reuse policy перевірена; lock clears decrypted application state.

Не заявляти, що це доводить OS-level secure storage.

### M2-A08 — safe update

PWA/service worker update з unsynced outbox → data preserved; schema migration transactional; unsupported future schema stops safely.

### M2-A09 — storage failure

Quota/IndexedDB write/upgrade failure → немає fake `LOCAL_SAVED`; current draft remains recoverable in current unlocked session; UI дає зрозумілий recovery/export route.

### M2-A10 — restore epoch

Mac old-backup restore / epoch change → stale outbox не replay автоматично; client переходить у reconciliation/re-pair/full-resync path.

### M2-A11 — network/privacy boundary

No provider/cloud/Vercel/analytics egress. Public Git history/staged/generated screenshots/logs не містять plaintext synthetic secrets, pairing tokens, cert private keys або data-root artifacts.

### M2-A12 — real-device gate

Підготований Android test plan: install PWA, offline capture, app/browser restart, reconnect, duplicate retry, conflict, delete/stale reconnect, update with pending outbox, storage persistence behavior, pairing revoke.

Якщо не виконано на Galaxy S24 Ultra — `HARDWARE_UNVERIFIED / NOT_RUN`, не PASS.

## 10. Browser/integration testing

Використай реальний browser automation там, де це materially перевіряє PWA semantics.

Бажано мати:

- persistent browser context / IndexedDB persistence;
- service worker + offline mode;
- два ізольовані simulated devices;
- actual built frontend + real Mac API + real SQLite;
- forced dropped response / reconnect;
- reload/browser context reopen;
- update/service worker migration scenario;
- touch/mobile viewport;
- console/network audit.

Не підмінюй усе unit mocks.

## 11. Performance

На synthetic dataset виміряй щонайменше:

- offline local save latency;
- outbox enqueue latency;
- reconnect/sync batch latency для малих batch;
- DB/IndexedDB size приблизно на N synthetic notes;
- idle CPU/memory для Mac mode;
- PWA shell size/cache size.

Запиши environment/N/method. Не вигадуй S24 performance без hardware run.

## 12. Dependencies і installs

Дозволені project-local dependencies, lockfile updates та browser-test binaries у ignored/generated path, якщо вони потрібні M2.

Не дозволено без окремого дозволу:

- `sudo`;
- глобальна інсталяція системних компонентів;
- system certificate trust changes;
- router/network reconfiguration;
- remote-access daemon;
- cloud/tunnel account creation;
- deploy/release/tag;
- provider/API spend.

Якщо candidate transport реально потребує одне з цього — задокументуй follow-up permission, не обходь його.

## 13. Data/privacy hard stops

- Тільки synthetic data.
- Не відкривати real private vault.
- Не ingest-ити R01/R02/R03 DOCX.
- Не комітити browser IndexedDB dump, SQLite data, pairing credentials, test cert private keys, unlock secrets.
- Не використовувати особисті creative/media/travel notes як fixtures.
- Не публікувати raw screenshots із desktop/terminal/tokens/private paths.
- Не вмикати AI/provider calls.
- Не читати Samsung Health/Health Connect.
- Не додавати ASR/microphone scope.
- Не deploy Vercel.
- Не відкривати LAN/Internet порт як default runtime.
- Не force-push і не переписувати published history.

## 14. Git / evidence discipline

Standing owner permission на normal fast-forward push у `main` чинний для цієї explicit goal.

Порядок:

1. Реалізуй і виправляй звичайні помилки автономно.
2. Зроби coherent final implementation commit **C**.
3. На exact C запусти повний relevant suite/build/PWA/browser/privacy checks.
4. Якщо після C змінюється implementation code — створи новий C і повтори релевантні checks.
5. Потім онови STATE/HANDOFF/roadmap/devlog/report/evidence-only і створи **R**.
6. Перевір C→R path whitelist та staged privacy.
7. Normal fast-forward push `main`.
8. Verify `origin/main == R`.
9. Не роби нескінченних post-push status commits; exact R SHA та remote receipt достатньо у фінальній відповіді.
10. Codex ставить M2 `AWAITING_REVIEW`, не `ACCEPTED`.

Потрібні:

- `reports/M1_ARCHITECT_REVIEW.md` — durable external M1 ACCEPT;
- `docs/M2_CONTRACT.md`;
- transport/security ADR/design record;
- `reports/M2_OFFLINE_PWA_SYNC_REPORT.md`;
- reproducible evidence під `reports/evidence/M2/`;
- актуальні STATE/HANDOFF/ROADMAP/devlog;
- regenerated ChatGPT context.

## 15. Definition of Done

Goal завершена, коли:

- M1 ACCEPT зафіксовано без self-approval;
- newest-first M1 list semantics виправлені й протестовані;
- installable offline PWA працює на synthetic browser test;
- local store + encrypted payload + outbox реалізовані;
- pairing/device/revoke/sync epoch semantics реалізовані;
- idempotent Mac sync працює;
- conflicts не overwrite мовчки;
- delete/tombstone/restore-epoch scenarios доведені;
- update/outbox/storage-failure scenarios перевірені;
- transport/security ADR має чесний candidate для real Android, без прихованого system/deploy permission;
- M2-A01…A11 PASS на synthetic scope або є точний blocker;
- M2-A12 має чесний PASS лише якщо реально виконаний на device; інакше HARDWARE_UNVERIFIED/NOT_RUN;
- full relevant tests/build/browser/privacy PASS або точний blocker;
- C/R normal-pushed у `main`;
- `origin/main` SHA перевірено;
- AI/deploy/private-data/health/voice/M3+ лишаються OFF.

## 16. Hard stop policy

Не зупиняйся через звичайний bug, failing test, локальну schema migration або internal implementation choice — виправляй у межах goal.

Зупини небезпечну частину і продовжуй незалежні підзадачі, якщо для неї потрібні:

- реальні приватні дані;
- ручна дія на телефоні, якої немає кому виконати;
- system certificate/root trust;
- router/remote-access changes;
- external tunnel/cloud account;
- deploy;
- paid/provider call;
- послаблення security boundary.

У такому випадку не занижуй контракт. Заверши все інше, познач exact gate `NOT_RUN/HARDWARE_UNVERIFIED/BLOCKED_FOR_PERMISSION`, дай мінімальне follow-up рішення.

## 17. Фінальна відповідь Codex

Коротко поверни:

- Base SHA;
- final C SHA;
- R SHA;
- `origin/main` SHA;
- M2 status;
- test/build/browser counts;
- privacy result;
- transport candidate + чи real Android test був виконаний;
- список NOT_RUN/HARDWARE_UNVERIFIED;
- точну команду запуску local Mac demo;
- точну команду/інструкцію запуску synthetic PWA test/demo;
- blockers/permissions, якщо лишилися.

Не переходь до M3.
