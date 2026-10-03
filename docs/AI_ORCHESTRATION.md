# Оркестратор, скіли та runtime

## Кількість ролей

Один основний співрозмовник. Один orchestration skill. До 12 предметних скілів,
що підвантажуються за потреби. Окремі запуски для тижневого огляду, extraction або
перевірки — jobs, не постійні автономні персонажі. Без «консиліуму лікарів».

| Skill | Функція | Gate |
|---|---|---|
| onboarding_goals | Згода, цілі, межі, навантаження | M3 |
| capture_classify | Структурувати введений текст, запропонувати секцію | M3 |
| sleep_diary | Уточнення щоденника й нейтральна психоосвіта | M3/R02 |
| dream_irt | Строго обраний сценарій самодопомоги | M7/R03/clinical review |
| thought_record | Запис ситуації, думок, емоцій і альтернатив | M7/R05 |
| worry_rumination | Відрізняти корисне осмислення від зациклення | M7/R06 |
| activity_self_kindness | Посильні дії, самокритика, бар’єри без осуду | M7/R07 |
| grounding_relaxation | Обрана низькоризикова практика й stop | M7/R08 |
| homework_review | Один погоджений крок і розбір досвіду | M7/R09 |
| weekly_review | Перевірені підрахунки, питання, невизначеність | M7/R10 |
| creative_library | Ідеї, зв’язки, теги, добірки без психологізації | M3/R15 |
| feedback_prepare | Лише чернетка очищеного повідомлення | M5/privacy gate |

Attention/routines можна реалізувати пізніше всередині відповідного предметного модуля;
не створювати нових agents лише заради кількості.

## Decision pipeline

1. Отримати intent і доступний consent scope; оригінал запису вже збережений.
2. Детерміновано перевірити допустимість інструментів/протоколу та стан сесії.
3. Для неоднозначної або ризикової ситуації — обережне уточнення/безпечний маршрут.
4. Зібрати мінімальний context package; перевірити token і quota budget.
5. Викликати конкретний provider adapter із timeout і allowlisted tools.
6. Перевірити JSON/schema, джерела, дозволені переходи й межі відповіді.
7. За потреби окремий reviewer call; він не заміняє deterministic validation.
8. Показати результат і лише дозволені зміни записати транзакційно.

Risk classifier помиляється. Ні regex, ні ще одна LLM не гарантують безпеки.
Критичні обмеження tools, data scope й активації сценаріїв знаходяться поза LLM.

## State machine сесії

CREATED → CHECK_IN → REVIEW_PREVIOUS → AGREE_FOCUS → EXERCISE_STEP →
CHECK_RESPONSE → NEXT_STEP_OR_PAUSE → CLOSED. З будь-якого кроку PAUSED/STOPPED.
Фактичний сценарій може мати менше кроків, але не пропускає потрібні safety gates.
Навіть після перезапуску продовжує ту саму версію протоколу; оновлення не підміняє
вправу посеред сесії без міграції та пояснення.

Текст кроків, допустимі параметри й stop conditions визначені reviewed protocol.
Модель адаптує мову, не самочинно вигадує дозу, клінічне рішення чи приховану мету.
Обговорення завдання не є оцінкою слухняності. Пропуск → спростити/змінити/припинити.

## Skills vs tools

Skill — інструкції, протокол, input/output schema, перелік джерел та тестів.
Tool — вузька функція ядра (`save_entry`, `read_selected_entries`, `pause_session`).
Не надавати `execute_shell`, `run_sql`, `git_push`, `read_arbitrary_path` runtime-боту.
Навіть feedback publisher відокремлений і приймає тільки дійсне approval exact payload.

## Неправильний output або недоступний provider

Не перетворювати невалідний текст у DB update. Зберегти безпечний error code,
повторити тільки в межах retry policy; не міняти модель/платіжний маршрут мовчки.
Проста підтримувальна відповідь і доступ до статичних reviewed матеріалів залишаються.
Не «симулювати терапевтичний крок», якщо потрібний protocol не завантажився.

## Спостережуваність

Без raw private prompts у dev logs. Метадані: job ID, provider/model/version,
тривалість, usage при доступності, outcome, protocol version і trace IDs.
Читабельне пояснення рішення можна зберігати; приховані міркування моделі не потрібні.
Реальні logs, summaries і оцінки не включати в GitHub-репорти.

## Implemented M3 scope

The working synthetic foundation is [M3 contract](M3_CONTRACT.md) / [ADR-003](adr/ADR-003-M3-RUNTIME.md).
Three neutral tasks, canonical selected context/approval, strict schemas, bounded jobs and user review
are implemented. No general tool dispatcher, free assistant chat or active clinical protocol. No live
provider, hidden files/network/tools or automatic phone-triggered AI. Future architecture above is not
an activation authorization.

## M7B: один Conversation Controller, bounded longitudinal context

Попередній M3 розділ описує історичний selected-journal runtime. M7B додає Free Conversation
і Deep Session, не активуючи старі чи нові клінічні сценарії. Conversation Controller
(`Conversations` + deterministic `Reflection` context service) керує permission/CAS/context/candidate
validation. Один provider adapter/одна model voice у майбутньому; жодного multi-agent swarm.

Контракти typed skills: core_reflection, deep_session, goal_setting, cbt_reflection,
worry_rumination, sleep_review, nightmare_review, grounding, session_closure.
Усі CONTRACT_ONLY_NOT_ACTIVE. Наявність контракту не дозволяє clinical content execution.

Context Builder order: user-agreed ReflectionGoal exact revision → recent current turns →
GoalContextDigest → DailyConversationDigest → локальні SQLite/FTS5/filter raw messages →
narrow exact-source expansion; USER_CONFIRMED memory тільки explicit scope. Default range
від goal.created_at до now або explicit user-selected window. Whole history у кожному prompt
заборонена. Journal/sleep/health — окремо авторизовані вузькі tools; у M7B лише deny/stub contracts.

Raw messages authority; digests MODEL_DERIVED/versioned/source-bound, edit/delete invalidates.
Local RetrievalReceipt записує refs, digest versions, method, time window і serialized context
budget без raw text logging. UTF8 byte upper bound є консервативним estimator, не model tokenizer.
Mandatory embeddings/vector DB відсутні; external embeddings заборонені; later vector retrieval
потребує measured gap ADR. No automatic conversation→journal/memory promotion.

Deep UX показує ціль/revision і відмінність current conversation / relevant past context;
editable goals/history/pause/complete працюють незалежно від provider. Responder OFF у звичайному
режимі, explicit synthetic-only deterministic candidate у demo. Live provider OFF, clinical active0,
real private data OFF, M7C/M8 NOT_STARTED. [Contract](M7B_CONTRACT.md), [ADR](adr/ADR-008-M7B-CONVERSATION-CONTEXT.md).
