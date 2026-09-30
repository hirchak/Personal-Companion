# Інтеграції: Samsung, голос, Telegram, інші AI

## Samsung Health / Health Connect

Reference hardware: Samsung Galaxy Watch7 — модель повідомлена власником.
Версії Android/Samsung Health/firmware, available fields і hardware compatibility NOT_VERIFIED.
M1 не підключається до wearable.
Їх не вгадувати за назвою телефона. Базовий підтримуваний маршрут для дослідження:

```text
Wearable → Samsung Health на Android → Health Connect →
невеликий native Android bridge → приватний sync/API на Mac
```

Health Connect використовує Android SDK і IPC та дозволи на дані [S10]. Звичайна PWA
не отримує ці дані через JavaScript або REST «Samsung cloud API». Native bridge
необхідний для автоматичного читання через цей маршрут; це окремий маленький компонент,
не переписування всього frontend. Manual export/import — початковий fallback після
перевірки actual export format на пристрої. Не вигадувати CSV headers без прикладу.

Samsung Health Data SDK — альтернативний шлях до доступних даних Samsung Health [S11].
Його developer/production partnership process перевіряється окремо [S12]; не вважати
developer mode на одному телефоні готовим розповсюджуваним рішенням. Не використовувати
deprecated SDK або reverse engineering закритих cloud endpoints.

### Перший scope

Read-only: сон (доступні інтервали/оцінки), кроки та активність; пульс лише після
потреби/згоди. Не просити location, медичні записи чи всі дозволи «на майбутнє».
Додаткові показники залежать від wearable/app/API, а не лише від моделі нашої системи.

Зберігати джерело, provider record ID/revision, device type, часову зону, одиниці,
import time й available/not-available reason. Self-report зберігати окремо.
Не додавати кроки з двох джерел без dedup/priority rule; не заповнювати missing нулем.
Health Connect Changes потребують checkpoints, upsert/delete handling і resync strategy [S13].
Permission revoked → зупинити читання, повідомити, не обходити відмову.

Оцінки фаз сну — оцінки споживчого пристрою, не клінічний висновок. Не виводити з них
кортизол, депресію або точну причину виснаження. Валідність і межі конкретного wearable
має дослідити R12 до будь-якого аналітичного використання.

### Критерій приймання

На реальному телефоні: дозвіл лише на вибрані поля, імпорт, повторний імпорт без дублів,
оновлення/видалення джерела, revoke, offline queue, sleep-midnight/DST, missing data.
Без hardware test статус HARDWARE_UNVERIFIED, а не PASS. Bridge не блокує базовий щоденник.

## Голосове введення

Маршрут: натиснути мікрофон → запис на пристрої → локально зберегти → за доступності
Mac передати через private sync → локальний ASR → editable transcript → підтвердити.
Browser mic API потребує secure context і дозволу користувача [S15]. Запис не працює
у фоні без обмежень; screen lock/перехід між apps та interruptions тестуються.

ASR-кандидат: `whisper.cpp`, локальна реалізація з Apple Silicon support [S16].
Модель багатомовна (не `.en` для української), завантажується явно, не комітиться у Git.
Вибір small/base/іншого розміру — за українським validation set на M2/16 GB;
не обіцяти швидкість або якість без вимірювання. Перевірити ліцензії runtime і weights.

Не плутати Whisper model із ChatGPT-підпискою. Локальний ASR не має плати за кожний
виклик провайдера, але споживає диск/пам’ять/енергію. Голос на телефоні при вимкненому
Mac спочатку зберігається як аудіо; миттєвого локального Whisper на Samsung V1 не обіцяємо.

ASR: voice-activity detection, silent/noisy input checks, можливість виправити текст,
original audio retention за вибором, cancel/resume, обмеження тривалості/розміру за тестами.
ASR hallucination не може створити завдання/діагноз/публікацію автоматично.
Підтвердження тексту особливо важливе перед аналізом або передаванням іншій моделі.
Не вмикати Web Speech/OS cloud dictation під назвою «локальне» без перевірки.

## Telegram

Опційний канал після основної PWA: private-chat allowlist, long polling, нейтральні
повідомлення без health content на lock screen. Mac має бути активний.
Bot API не зберігає undelivered updates довше 24 годин [S18]; не обіцяти, що запис,
надісланий під час тривалої відсутності Mac, гарантовано буде отриманий.
Telegram не є основним offline vault. Не маршрутизувати звідти shell або git commands.

## Інші AI й екосистеми

Перший шлях — scoped export вибраних нотаток з preview. Пізніше локальний MCP API
з pairing, read-only за замовчуванням, вузькими scopes і явним записом provenance.
Жодна стороння AI не отримує весь vault через «підключення до папки» автоматично.
