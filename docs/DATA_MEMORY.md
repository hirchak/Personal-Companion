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
External embeddings приватного змісту у M7B заборонені; пізніша зміна потребує окремого ADR і scoped owner consent.
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

## Implemented M3 memory

See [M3 contract](M3_CONTRACT.md) and [runtime ADR](adr/ADR-003-M3-RUNTIME.md). SQLite memory now
supports explicit user preferences and neutral model proposals; source/provenance/revisions, confirm,
edit/reject/delete and downstream invalidation are working synthetic flows. Model confirmation keeps
MODEL_SUGGESTED provenance with USER_CONFIRMED status. Explicit user correction becomes USER_EDITED,
keeps originating job/suggestion but detaches obsolete active refs. Creative memory inference is denied.
No embeddings, whole-journal profile or clinical label inference.

## M7B: raw conversation authority і versioned goal/context

Окремі таблиці conversations / conversation_messages / conversation_message_revisions
зберігають точні UTC timestamps, provenance, PRIVATE_PERSONAL, CAS revision і source references.
FREE й DEEP відокремлені від journal/practice. Envelope schema9 додає ці та reflection таблиці;
entry schema2, health schema1 і practice schema1 не змінені. Старі дані мігруються лише на fixtures.

ReflectionGoal має явний user_agreed текст, ACTIVE/PAUSED/COMPLETED, created_at/updated_at/
completed_at та історію редакцій. Deep session goal_binding фіксує ID/revision; редагування
навіть завершеної цілі не змінює старі snapshots або completed_at. Нова сесія використовує
актуальну ACTIVE редакцію. Source message edit зберігає попередню редакцію; conversation delete
каскадно прибирає messages/revisions/FTS rows, стирає текст залежних дайджестів і лишає
мінімальні metadata receipts/tombstones. Старі backups/SQLite pages можуть містити копії;
forensic secure erase не заявляється.

conversation_digests — еквіваленти DailyConversationDigest і GoalContextDigest: ID, version,
source message IDs/revisions, UTC range, generator version, MODEL_DERIVED, CURRENT/STALE.
Source edit/delete або зміна goal робить залежний digest STALE з text=null. Raw message
залишається авторитетом. У M7B генератор лише explicit synthetic excerpt fixture
SYNTHETIC_EXCERPT_V1 / DETERMINISTIC_FIXTURE_NOT_LLM; це не модельний summary.

retrieval_receipts містять точну goal revision/window/source refs/digest versions/method і
serialized UTF8 JSON token/size budget, parts metadata без raw text. Retry з тим самим operation
повертає ту саму вибірку або SOURCE_CHANGED, а не непомітно іншу історію.
Локальне SQLite/filter/FTS5 retrieval bounded; зовнішні embeddings заборонені, mandatory
vector DB/embeddings у M7B немає. Пізніші vectors потребують виміряного gap ADR.
USER_CONFIRMED memory включається лише з explicit scope і точною revision. Journal/sleep/health
контракти лишаються separately authorized narrow tools, доступ OFF. Topic suggestions
MODEL_SUGGESTED, якщо будуть додані, не підтверджені memories/діагнози.
Немає автоматичного conversation→journal/memory promotion.

Один Conversation Controller + typed skills/одна model voice; live provider OFF, clinical active0,
real private data OFF; M7C/M8 NOT_STARTED. [Contract](M7B_CONTRACT.md), [ADR](adr/ADR-008-M7B-CONVERSATION-CONTEXT.md).


## M7C owner scope — 2026-10-04

Schema10 adds controller inference metadata tables and N01/N02 digest semantics; journal entry schema2, health schema1 and practice schema1 remain unchanged. Raw timestamped messages and exact user-goal revisions remain authoritative. One CURRENT digest per (kind,scope_key), superseded/stale text purged transactionally, source edit/delete invalidates dependencies. Daily identity is IANA_LOCAL_V1:<timezone>:<local-date>; Europe/Warsaw is the explicit reference default, not a discovered user timezone. UTC originals never shift; timezone changes preserve historical artifact identity. Legacy UTC daily digests become STALE. Existing FTS/filter and bounded builder are used; no mandatory vector DB/embeddings or external embedding calls. Digests remain deterministic synthetic fixtures, not real model summaries. Receipts are local metadata only. Inference stores request/context/skills hashes, receipt and candidate separately; partial stream never persists. Restart/backup cancels pending authority and never resumes external calls. Explicit journal-point copy revalidates source revision/preview hash in the accepted journal transaction; operation receipt hash binds that user action, and the resulting USER_REPORTED entry survives conversation deletion. No source ID is added to the journal schema. M7C does not wire confirmed-memory or journal/health-to-AI context.

## M8C root kind and domain provenance

PRIVATE_LOCAL is a storage/runtime classification, separate from domain privacy/provenance. Journal/creative records
keep PRIVATE_PERSONAL/USER_REPORTED and existing revision/source/tombstone contracts. Synthetic-content private-mode
tests label their content in fixtures/evidence only; no production synthetic-label bypass field is accepted.
Dual marker/SQLite root identity plus install receipt and backup4 attestations refuse loose-flag/cross-mode conversion.
Root identity renews after fresh protected restore; domain lineage/history remains. No existing-data discovery/import.
