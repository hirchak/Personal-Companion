# Приватність і безпека

## Класи даних

| Клас | Приклади | Типовий маршрут |
|---|---|---|
| PUBLIC_SYSTEM | Код, специфікація, синтетичні приклади | GitHub після перевірки |
| PUBLIC_RESEARCH | Бібліографія, власний синтез, ліцензовані фрагменти | GitHub після правового review |
| PRIVATE_PERSONAL | День, сон, стан, творчі ідеї, аудіо, wearable | Пристрої власниці |
| PRIVATE_DERIVED | Пам’ять, гіпотези, embeddings, summaries | Той самий захист, що в джерел |
| SHARE_DRAFT | Чернетка очищеного фідбеку | Локально до approval |
| SHARED_APPROVED | Точна затверджена версія повідомлення | Лише названий одержувач |
| SECRET | Provider/session/device keys | Keychain/Keystore, ніколи Git |

Похідний підсумок не стає анонімним лише тому, що він коротший за щоденник.
Публічний технічний пакет не містить цитат або конкретного анамнезу власниці.
Окремий приватний додаток існує лише як початковий людський контекст, не runtime seed.

## Дозволи

Розділити згоду на локальне збереження, pairing, sync, читання Health Connect,
передавання тексту конкретному AI, аудіо, Telegram, експорт, публікацію та backup target.
Власник розробки не може дати згоду замість власниці її щоденника.
Кожний provider consent має scope/expiry або спосіб відкликання. Відкликання блокує
нові відправлення й скасовує ще не виконані jobs; вже передане не можна «забрати назад».

Початкові режими: LOCAL_ONLY (без cloud AI); CLOUD_ASSISTED (мінімальний дозволений
контекст конкретному провайдеру); SHARE_ONCE (показати точний payload і одержувача).
Чутливі творчі нотатки не використовуються для аналізу самопочуття без окремого вибору.

## Зовнішні передачі, які не можна приховувати

Codex CLI запускається на Mac, але авторизоване використання OpenAI моделей не є
локальним inference; тип входу впливає на правила обробки даних [S01].
MiniMax також є зовнішнім провайдером. Доступ через підписку не дорівнює приватному
локальному обчисленню. Не зберігати ключі в frontend або GitHub Actions.
Telegram не використовувати для найбільш чутливих матеріалів за замовчуванням;
ботовий чат не є Telegram Secret Chat [S19].
Можливі системні backups, Samsung account sync, browser/OS dictation та журнали CLI
потрібно перевірити окремо. Відсутність нашого cloud backend їх не вимикає.

## Модель загроз

Захистити від випадкового public push, зловмисного issue/research prompt injection,
доступу стороннього сайта до localhost, XSS/небезпечного Markdown, викрадення пристрою,
компрометації update, переплутаних користувачів/пристроїв, дубльованого експорту,
витоку через логи/скриншоти, а також неочікуваного provider billing fallback.
Не обіцяти захист від повністю скомпрометованої OS або людини з розблокованою сесією.

## Технічні вимоги

Local API bind 127.0.0.1 до явного remote-access gate. Авторизація потрібна й локально;
Origin/Host allowlist, захист CSRF, без wildcard CORS, без токенів у URL.
HTTPS для телефона; pairing за одноразовим короткоживучим запрошенням; відкликання
окремого пристрою, rate limit, replay protection. Дані не передавати у query string.

На Mac перевірити FileVault, доступ до каталогу, UI auto-lock і backup encryption.
На телефоні IndexedDB/аудіо зашифровувати до запису на диск, ключ відкривати через
перевірений механізм локального unlock. Не зберігати і ключ, і ciphertext поруч відкритими.
Вибір бібліотеки/KDF/ключового життєвого циклу затвердити security ADR на M2;
власну криптографію не винаходити. Без пройденого gate — тільки synthetic demo.

Шифрування at-rest не зупиняє шкідливий JS під час unlocked session. Мінімальний CSP,
локальні залежності/шрифти, відсутність сторонніх скриптів, санітизація рендерингу,
перевірені збірки та ручне оновлення критичних версій зменшують ризик, не усувають його.

Runtime tools не мають shell/git/sudo і не відкривають довільні файли. Навіть read-only
Codex sandbox може читати більше, ніж потрібно; synthetic escape-тести обов’язкові.
Якщо обмеження не доведені — AI adapter залишається вимкненим.

## Публікація фідбеку

Private note → локальний очищений draft → користувачка бачить точний текст,
вкладення, destination і видимість → explicit approval прив’язаний до hash/version →
експорт або створення issue → receipt. Будь-яка правка після approval скасовує approval.
Не використовувати raw audio, транскрипти, health context або screenshot без окремого дозволу.
Публічну копію після поширення неможливо гарантовано вилучити з усіх fork/cache.

## Видалення та резервування

Видаляти джерело, похідні summaries/embeddings, search index, кеш і незавершені jobs.
Передавати tombstones авторизованим пристроям, не «воскресати» записи зі старого телефона.
Після відкликання offline device неможливо обіцяти дистанційне стирання його копії.
Окремо описати retention backup і provider logs. Для immutable backup — expiry або
видалення всього snapshot, не хибна обіцянка часткового фізичного стирання.

Privacy gate включає аналіз всіх Git objects, staged diff, CI artifacts, screenshots,
source maps і журналів; `.gitignore` — запобіжник, не гарантія.

## M8C bounded PRIVATE_LOCAL core policy

[ADR-013](adr/ADR-013-M8C-PRIVATE-LOCAL-CORE.md) implements the separate Mac-only mode; earlier synthetic-only
security gates remain historical. Native read-only target-volume verification requires APFS FileVault, Encryption
and EncryptionThisVolumeProper all true. Hardware encryption/global FileVault status alone is insufficient.
Directories0700/files0600/current-owner/no extended ACL, safe separate app/vault/backup outside Git/cloud, localhost,
auth/auto-lock/CSRF/Host/Origin/CSP/build match/deny-egress. Invalid/unverified security blocks readiness/init/start/
backup/restore, never changes OS settings. Same owner editing DB/code or an unlocked/compromised OS outside scope.

SQLite/database and backup application encryption **NOT_IMPLEMENTED**. Private archives rely on verified protected
volume, not independent archive keys. Copying to unencrypted storage removes that protection. Backup target explicit/
local/owner-only/reverified; no automatic uploads/retention deletion. Third-party sync agents/OS backups are not
controlled by app; owner explicitly acknowledges local folders/no cloud routing. Local export retains exact preview/
selection/session safeguards and becomes an owner-controlled private plaintext file; destination outside app needs
owner protection. No provider/env/Health/voice/phone/AI/clinical enablement in this profile. Root receipts remain local,
contain no personal identity; public evidence excludes paths/root IDs/real consent/contents/native disk IDs/unlock.
Exact operator activation after independent ACCEPT: [PILOT_HANDOFF](PILOT_HANDOFF.md). M8C uses synthetic content only.


## M8D optional owner pilot

M8D is a separate owner-bounded optional profile, defaultOFF. [ADR-014](adr/ADR-014-M8D-OWNER-PRIVATE-AI-VOICE.md) defines seven explicit disclosures/settings confirmations, exact text/context previews, isolated native client and fixed-destination TLS-blind local transport. Existing subscription only, no credential extraction/copy, provider fallback/PAYG/new auth. Current message/bounded same-conversation history; journal explicit selection only; raw audio NEVER sent. Consumer route is NOT zero-retention/commercial/third-party certified. TRAINING_CONTROL_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
CODEX_ENVIRONMENTS_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT. Explicit runtime confirmation remains required; account settings are not inspected. At-rest/FileVault/permissions/backup policy remains ADR-013. No real owner-vault access during M8D.
