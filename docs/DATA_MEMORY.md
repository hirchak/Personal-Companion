# Дані, provenance і довготривала пам’ять

## Принцип

Mac vault — основне сховище синхронізованих даних. Телефон до sync є єдиним власником
ще не переданих записів. Бібліотека наукових джерел відокремлена від особистої пам’яті.
Жодний chat transcript або LLM summary не є єдиною базою даних.

## Логічні сутності

| Сутність | Призначення |
|---|---|
| profile/preferences/consents | Самостійно підтверджені цілі, доступи, вподобання |
| entries + entry_revisions | Оригінал і версії; тип, авторський час, теги, секція |
| sleep_entries | Часові оцінки й самопочуття, optional поля, unknown ≠ zero |
| checkins | Добровільні оцінки стану без діагностичного висновку |
| creative_items | Ідея, сцена, персонаж, insight, reference, власні зв’язки |
| attachments/transcripts | Аудіо/файл, модель ASR, мова, редакторські виправлення |
| sessions/session_steps | Поточний стан протоколу, версія, відповіді, pause/resume |
| assignments | Погоджене завдання, навантаження, статус і досвід виконання |
| memory_items | Підтверджений факт/перевага або непідтверджена пропозиція |
| observations/hypotheses | Похідні підрахунки й обережні гіпотези з джерелами |
| wearable_records | Source ID, source app/device, type, time, units, revision |
| jobs/receipts | Черга, idempotency, retry, cancellation, usage metadata |
| devices/sync_changes/tombstones | Pairing, sync checkpoint, конфлікти та delete |
| feedback_drafts/approvals | Окремий процес підготовки й дозволу публікації |
| protocol_registry/evidence_refs | Версії контенту, статус review, локатори джерел |

Це доменна модель. Не обов’язково створювати окрему SQL-таблицю для кожного імені.
Міграції й invariant tests важливіші за буквальну кількість таблиць.

## Загальні поля

`id`, `owner_id`, `created_at`, `occurred_at`, `timezone`, `updated_at`, `revision`,
`schema_version`, `privacy_class`, `provenance_type`, `source_refs`, `deleted_at`.
Ідентифікатори не повинні містити ПІБ, email або медичну інформацію.
Вкладення: `sha256`, MIME, byte_size, duration за потреби, integrity status.
Raw transcription відокремлена від користувацької поправки; AI не переписує оригінал.

## Provenance

USER_REPORTED — слова людини; USER_CONFIRMED — підтверджена пам’ять;
DEVICE_RECORDED — імпорт із конкретного джерела; COMPUTED — детермінований підрахунок;
MODEL_SUGGESTED — припущення; CLINICIAN_DOCUMENT — лише добровільно наданий документ,
не висновок системи. Джерело може мати помилки незалежно від типу.

Не перетворювати припущення про діагноз, гормони, травми або особистість у факт профілю.
Проєкт не містить формули визначення кортизолу із снів або wearable data.

## Memory lifecycle

Capture → classification proposal → permission/scope check → user-confirmed memory
або непідтверджена короткоживуча пропозиція → revision/expiry/deletion.
«Що система пам’ятає» доступно людині для перегляду та виправлення.
Memory має evidence refs, confidence/status, актуальність і domain scope.
Не копіювати весь щоденник у великий профіль і не додавати негативні ярлики.

## Context package для AI

Пакет містить тільки потрібне: цілі/межі, поточний session state, активне завдання,
релевантні записи, потрібний protocol version, мінімальні підтверджені preferences.
Він фіксує source IDs/revisions, consent scope і token budget. Виклик не виконується,
якщо mandatory context не вміщується: запропонувати звузити задачу, не обрізати правила.
Не використовувати пошук по творчій бібліотеці для психологічної інтерпретації за замовчуванням.

## RAG і пошук

Почати з SQL/filter/FTS. Обрані джерела з бібліотеки знаходяться за протоколом/claim ID,
а не за випадковим similarity. Embeddings/vector DB — тільки після виміряного retrieval gap.
Embeddings приватних нотаток також приватні; не надсилати їх без дозволу провайдеру.
Obsidian/Markdown export — зручне представлення, не друге незалежне сховище стану.

## Аналітика

Код рахує, модель пояснює. Кожна observation має вікно дат, N, missingness, формулу,
вхідні revision IDs, одиниці й аналітичну версію. Дані годинника й самооцінки показуються
окремо, без автоматичного «виправлення» одного іншим. Мінімальний N не вигадувати як
універсальну наукову межу: критерії висновку обґрунтовує R10 і тести.
Кореляція не є причиною; множинні перебори й confounding роблять цікаву історію ненадійною.
Показувати альтернативи, невизначеність і можливість відмовитися від аналізу.

## Export і сторонній AI

Portable JSON/Markdown + schema version + manifest + локальні вкладення за вибором.
Вибірка за секціями/періодами/типами; preview. Немає прямого довільного SQL від агента.
Майбутній MCP — read-only scoped tools за замовчуванням; recording/deletion/sharing
окремі повноваження. Імпортована відповідь AI лишається зовнішньою пропозицією.
