# Встановлення, робота на Mac і перенесення

Ціль — інсталятор, який Codex або користувач запускає за повною інструкцією.
Зараз такого інсталятора ще немає; цей документ є його контрактом.

## Розкладка

```text
~/Projects/personal-companion/              # Git: лише система
~/Library/Application Support/PersonalCompanion/
  vault/                                  # приватна SQLite + local indices
  attachments/                            # аудіо й інші приватні файли
  exports/                                # приватні exports, не Git
  backups/                                # encrypted snapshots за політикою
  runtime/                                # черга/санітизовані метадані
  models/                                 # завантажені ASR weights
```

Custom data directory можливий після перевірки, що він поза Git, не всередині public
folder і не хмарно синхронізований без згоди. Для переносимого режиму можна мати app і
private як сусідні каталоги; app root є Git, private — ні. Саме розділення не шифрує дані.

Keychain зберігає секрети. LaunchAgent/config працюють у системній області відповідного
користувача; не обіцяти буквально всі файли лише в одній папці. macOS permissions
потребують реальної перевірки на пристрої [S24]. Немає admin/root daemon за замовчуванням.

## Installer contract

Перевірити OS/architecture/free space/dependencies. Встановити pinned runtime в контрольоване
середовище, збірку UI, створити лише чисту DB, перевірити data root і базові permissions.
Не копіювати developer `.env`, реальні fixtures або auth state. Показати потрібні дозволи,
data flow, backup location; налаштування AI/Health/mic/autostart лише після вибору власниці.
Network downloads/dependencies вимагають заздалегідь дозволеного installation goal.

Після setup: локальний launcher «Відкрити», status/diagnostics, start/stop/update/export.
Autostart — opt-in LaunchAgent; при login/wake перевіряє single instance, відновлює чергу,
не утримує ноутбук постійно awake. Після перезавантаження/виходу користувача режим може
відрізнятися від простого відкриття кришки; це треба протестувати, а не обіцяти.

## Backup

DB snapshot робити SQLite backup API або еквівалентним узгодженим методом [S23].
Не копіювати лише `database.sqlite`, ігноруючи WAL/attachments.
Пакет backup: schema version, app version, content manifest/checksums, DB snapshot,
потрібні attachments; ключ/пароль зберігається окремо. Restore verification обов’язкова.
Місце backup обирає власниця; encrypted external drive/cloud target — лише explicit choice.

## Update/rollback

Перед міграцією — перевірений backup; dry-run на копії, версійований migration plan,
forward compatibility/відмова від downgrade при небезпечній схемі. Немає auto-pull main
і виконання неперевіреного коду з повноваженнями runtime. Оновлення reviewed release.
PWA shell/DB schema version узгоджені; unsynced outbox не втрачається при activation.
Rollback коду і rollback даних — різні процедури; не підміняти одну іншою.

## Перенесення

На новому комп’ютері: встановити чистий release, перевірити сумісність,
імпортувати explicit encrypted export, перевірити integrity, знову авторизувати провайдерів
і спарити телефон. Не копіювати чужі auth tokens, launchd paths чи machine-bound keys.
Sync device IDs/epoch узгодити, щоб два Mac не стали незалежними «основними серверами».
Репозиторій сам по собі переносить систему, не приватну історію.

## Видалення

Зупинити jobs, відключити LaunchAgent/device tokens, видалити app. Окремі вибори:
зберегти vault, export, видалити vault, очистити backups. Не стирати історію автоматично
при uninstall. Повідомити про phone/provider/Telegram copies, які лишилися поза Mac.

## Публічний запуск

Перед SaaS або hosted runtime потрібні нові threat model, tenant isolation, data processing
і медико-правова оцінка intended use. Особисті підписки не стають комерційним backend
без перевірки умов. Вибір ліцензії до public release — окреме рішення [S25].

## M1 synthetic demo (implemented)

Python 3.13 and Node 26 were used for local checks; pinned project dependencies are in
`requirements.lock` and `apps/web/package-lock.json`. No global install, autostart or deploy.
From the repository root:

```bash
./scripts/setup_demo.sh
./scripts/demo.sh /private/tmp/personal-companion-m1-synthetic-demo
```

Open `http://127.0.0.1:8765`. Enter the one-time code displayed by the launcher (5-minute TTL).
The demo contains four explicitly SYNTHETIC notes. Stop with Ctrl+C. Restart the same command
for durability and a fresh code; any previous session is invalid. After manual/idle lock,
restart the launcher for a new code. Unknown existing roots are refused; initializer never
reseeds an existing root. The demo root is persistent until OS temp cleanup; it is not a backup.

Maintenance uses explicit newly named paths outside Git (do not use existing real folders):

```bash
.venv/bin/python -m apps.core.cli backup --root /private/tmp/personal-companion-m1-synthetic-demo --artifact /private/tmp/personal-companion-m1-synthetic-backup
.venv/bin/python -m apps.core.cli restore --artifact /private/tmp/personal-companion-m1-synthetic-backup --root /private/tmp/personal-companion-m1-synthetic-restored
```

Backup destination must be new; restore target new/empty. No arbitrary-path HTTP endpoint.
JSON export preserves selected current/history records; Markdown is escaped readable text.
Use `validate_portable` for standalone synthetic round-trip checks, not a public import.

M1 is synthetic-only. No encryption-at-rest/key recovery/FileVault acceptance or private rollout.
Deletion purges current/history/search and prior write fingerprints; minimal operation metadata
and tombstones remain to prevent replay. SQLite free pages/WAL, previous backups/exports/OS
snapshots may retain older bytes. This is not forensic erase. Keep/delete entire backups by
explicit owner choice; no automatic cleanup of unknown artifacts.

## M2 synthetic PWA

M1/local-only remains `./scripts/demo.sh`; it does not enable device transport. M2 is explicit:

```bash
./scripts/setup_demo.sh
./scripts/m2_demo.sh /private/tmp/personal-companion-m2-synthetic-demo
```

Mac UI: `http://127.0.0.1:8765/`, one-time terminal unlock. Phone simulation on the same desktop
browser/origin: `http://127.0.0.1:8765/phone/`. Create a local passphrase (12+ characters), then
Mac «Пристрої та PWA» → «Створити запрошення»; enter it in phone settings. It expires in 5 min.
No passphrase/token in URL or plaintext durable browser storage. Pairing material stays inside
AES-GCM state. Lock/reload clears key; reopen with passphrase. Stop server with Ctrl+C.

This localhost flow is **not a Galaxy phone route**. Real private-origin HTTPS and Android
remain OFF/NOT_RUN. For controlled TLS testing only:

```bash
.venv/bin/python -m apps.core.cli serve --root /private/tmp/personal-companion-m2-synthetic-demo --port 8765 --mode m2-synthetic --test-tls
```

Generates short-lived cert/key in a new private temp path, never installs trust. Automated tests
use ephemeral browser flags; do not tell real users to ignore TLS warnings. See
[transport ADR](adr/ADR-002-M2-TRANSPORT.md) and [Android gate](M2_ANDROID_GATE.md).

Verification:

```bash
npm --prefix apps/web run build
npm --prefix apps/web test
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.measure_m2
```

Offline/PWA: first online shell load is required. After that the service worker caches only
static resources. Capture/edit/delete store entry+outbox as one encrypted transaction; queued
text is canonical on phone until committed Mac receipt. Conflicts show two variants and need
explicit choice. Revocation does not remote erase. Restore/epoch rotation block old queue until
re-pair and explicit reconciliation; phone-copy choice creates new IDs rather than replaying old
IDs/deletes. Recovery is an encrypted file of unsynced data, not Mac backup. Import only into an
empty store, validate checksum/decryption/schema and require pairing/reconciliation. No lost-
passphrase bypass. Forget browser requires an explicit warning; export pending data first.

Mac DB schema 2 upgrades synthetic schema 1 transactionally after backup; no unknown/private
roots. Owner backup sanitizes device credential verifiers; restored vault requires new pairing.
Local IDB structural upgrade is additive; encrypted 1→2 needs explicit confirmation and atomic
rewrite. Newer unknown schema refuses safely. Waiting service worker activates explicitly and
never resets outbox. Browser persistence is best effort even if granted; all storage may be
cleared/evicted. Uncommitted draft remains only in current unlocked memory on write failure.

## M3 synthetic organization and memory

The existing `./scripts/m2_demo.sh /private/tmp/personal-companion-m3-synthetic-demo` starts both Mac
journal and phone shell. No real vault or private transport: loopback desktop synthetic harness only.
AI starts OFF. On Mac select notes, expand «Помічник і пам’ять», enable local synthetic mock and
preview exact context before approving a task. Review proposals, edit/confirm/delete preferences in
«Що система пам’ятає». Codex option is disabled, never invokes a model. Nothing runs AI on phone sync.
Only mock job activity polls the UI; no background browser guarantee. Restart returns AI to OFF.

Schema 3 migration applies only to explicit synthetic roots. M2 schema-2 backup restores then migrates;
preupgrade copy/transaction failure preserve source. No downgrade into old code. Pending phone pairing
becomes active only after encrypted credential commit; on local failure use a fresh owner invitation
or revoke the visible PENDING device. Lost finalize response retries on foreground sync.
