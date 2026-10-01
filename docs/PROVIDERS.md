# Провайдери, моделі, reasoning і витрати

Перевірка зовнішніх джерел: 2026-09-30. Точна доступність залежить від клієнта й акаунта.
Цей документ не надає дозволу витрачати кошти або квоти.

## Два різні застосування Codex

Development Codex працює з кодом/синтетичними даними в repo.
Runtime adapter працює з мінімальним дозволеним контекстом власниці, окремо від repo.
Не запускати development agent із повним workspace-write над особистим vault.

Офіційний `codex exec` підтримує неінтерактивний виклик, JSON/schema output та збережену
авторизацію [S02]. Це технічна можливість для локального private adapter, не blanket
дозвіл перепродавати чужу підписку або відкривати публічний сервіс від її імені.
Підписний вхід ChatGPT і API-key billing — різні режими [S01]. Особисті auth credentials
не переносити в public CI, Vercel або іншому користувачу.

## Capability spike до runtime

Перевірити CLI version, login method (без виводу секретів), дозволені моделі, reasoning,
структурований output, timeout/cancel, інструменти та файлову ізоляцію. Перевірити,
чи поточний client/session retention можна налаштувати належно; `--ephemeral`
сам по собі не визначає політику retention провайдера. Не звертатися вручну до
приватних ChatGPT backend endpoints і не витягати OAuth token для стороннього gateway.

Smoke test — тільки synthetic data і тільки після scoped дозволу на один або інший
обмежений обсяг викликів. Якщо route не підтверджений, mock працює, cloud adapter OFF.
Особистий non-coding runtime треба окремо звірити з умовами сервісу: підтримка CLI
ще не є підтвердженням будь-якого дозволеного застосування підписки.

## Моделі розробки

Документація містить `gpt-6.1-sol` і `gpt-6-luna`; availability/effort перевіряються локально [S03].
Нижче — проектні рекомендації для старту, не бенчмарк.

| Задача | Модель | Reasoning | Plan Mode |
|---|---|---|---|
| M0 та architecture/security/sync design | GPT-6.1 Sol | High, якщо доступно | OFF для execution; ON тільки для окремого plan-goal |
| Реалізація чіткої підзадачі, docs, extraction | GPT-6 Luna | High, якщо доступно | OFF |
| Складний баг, міграція, інтеграційне рев’ю | GPT-6.1 Sol | High; вище тільки за потреби/дозволом | OFF |
| Незалежне технічне рев’ю | ChatGPT-архітектор | Вибір поточного чату | Не налаштовується чужим промптом |

Не просити модель удавати, що вона перемкнула себе. Користувач встановлює параметри
в UI/CLI, Codex звіряє фактичні. За недоступності — повідомити, не підміняти непомітно.
Не вводити неіснуючий `--plan-mode` або недокументовані provider flags.
Офіційний `/goal` має обмеження 4000 символів: довгі умови у файлі, goal вказує на файл [S04].

## MiniMax Token Plan

Це окремий subscription route, не звичайний PAYG API key. Актуальна документація
розрізняє Subscription Key і API Keys, описує 5-hour/weekly quota та автоматичне
використання доступних purchased Credits після квоти [S05]. Згаданий власником тариф
не приймати за актуальну загальну ціну або підтвердження конкретних прав акаунта.

M3 і довгий контекст присутні у матеріалах провайдера [S06]; це не причина відсилати
весь приватний vault. Початкова роль MiniMax: public research extraction, індексація
дозволених матеріалів і синтетичні задачі. Особисті записи — OFF до окремого consent.

Перед увімкненням: перевірити actual account/team seat, дозволені інтеграції, model ID,
endpoint, ресурси, права використання іншою людиною і Credits fallback. Не ділитися
особистою credential замість дозволеного seat/access. Підключення користувачці —
лише через дозволений провайдером механізм, не копіювання ключа «бо є підписка».
Якщо provider/account не дозволяє надійно виключити додаткові списання,
режим «тільки included quota» не можна обіцяти: adapter OFF або окремий spend consent.

## Внутрішній контракт adapter

`capabilities`, `auth_mode`, `data_destination`, `allowed_scopes`, `quota_state`,
`generate(request)`, `cancel(job_id)`, `usage_metadata`, `retention_note`.
Request: task type, model ID, effort, schema, selected context, maximum output,
timeout, retry policy, allowed tools і consent ID. Adapter не вирішує, що можна розкрити.

## Quota policy

Один foreground AI job за замовчуванням; background batching низького пріоритету.
Лише bounded retries для transient errors. Exhausted quota → QUEUED/WAITING_QUOTA,
видиме пояснення. No automatic provider failover: потрібні згода на новий destination
і фінансові умови. Нульові автоматичні PAYG top-ups. Немає оцінки витрат «на око» як факту.

## M3 implemented gate

[ADR-003](adr/ADR-003-M3-RUNTIME.md) records the actual implementation: local deterministic mock and
unconditionally disabled Codex candidate, unknown real model/auth/quota/retention/OS isolation.
No real CLI command flags are assumed or invoked; no login/auth credentials inspected.
Trusted fake subprocess tests do not authorize or prove real provider isolation/retention. M3-A14
NOT_RUN / PROVIDER_DISABLED. Runtime starts OFF; owner UI enables mock only. No MiniMax/PAYG/fallback.
