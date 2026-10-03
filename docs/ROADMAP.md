# Roadmap і критерії переходу

M0 engineering/bootstrap: ACCEPT за зовнішнім architect review. M1: external engineering/synthetic ACCEPT за M2 goal.
M2: external ACCEPT for synthetic engineering (reports/M2_ARCHITECT_REVIEW.md).
M3: external ACCEPT for synthetic engineering (reports/M3_ARCHITECT_REVIEW.md).
M4: external ACCEPT for synthetic engineering (reports/M4_ARCHITECT_REVIEW.md); A14/A15 NOT_RUN.
M5: external ACCEPT for synthetic engineering (reports/M5_ARCHITECT_REVIEW.md).
M6: external ACCEPT — engineering + bounded early hardware за C6/R6
(reports/M6_ARCHITECT_REVIEW.md). M6-N01 OPEN: early0.6.0 PASS не закриває final0.6.1 hardware NOT_RUN.
M7_PREP_EVIDENCE_ADMISSION: external ACCEPT preparation/tooling scope (reports/M7_PREP_ARCHITECT_REVIEW.md); clinical active=0.
M7A_GENERIC_PRACTICE_ENGINE: external ACCEPT — synthetic engineering scope (reports/M7A_ARCHITECT_REVIEW.md).
M7B_CONVERSATION_HOME: IN_PROGRESS — same goal includes binding longitudinal/deep-goal addenda.
M7C/clinical activation і M8: NOT_STARTED; наступної goal/permission немає.
M6 early Galaxy USB/Health Connect verified; private HTTPS/Tailscale remains NOT_RUN.
Порядок нижче — рекомендований; optional модулі не повинні затримувати корисне ядро.

| ID | Результат | Залежності | Основна модель |
|---|---|---|---|
| M0 | Bootstrap, верифікація специфікації, середовища, M1 contract | Пакет + явна ціль | Sol / High |
| M1 | Локальний щоденник без AI, vault, пошук, export/backup | Прийнятий M0 | Luna / High; Sol для складних рішень |
| M2 | Телефонна PWA, encrypted outbox, private HTTPS sync | M1, transport/security ADR | Sol / High |
| M3 | Runtime adapter, дозволений AI, пам’ять, просте сортування | M1; M2 для cross-device тестів | Sol / High |
| M4 | Голос → локальне ASR → editable transcript | M1; M2 для телефона | Luna / High |
| M5 | Творча бібліотека, feedback export, м’який optional game layer | M1/M2; M3 для AI suggestions | Luna / High |
| M6 | Read-only Samsung integration / native bridge | M2, R12, реальний hardware | Sol / High |
| M7 | Reviewed self-help modules, homework, обережний weekly review | M3 + потрібні R01–R11 gates | Sol / High |
| M8 | Пакування, install/restore/upgrade, контрольований особистий пілот | Обраний release scope + відповідні gates | Sol / High |

M7 дозволено планувати одразу після M3, щойно готові дослідження; не потрібно чекати M4–M6.
M8 може випустити journal-only версію без клінічних модулів і hardware, якщо вони чесно
позначені DISABLED/DEFERRED. Research виконується паралельно з engineering.
Кожний milestone має окрему явну /goal і review, а не одну команду «зробити все».

## M0 — Bootstrap

Перевірити repo/структуру/середовище без читання приватних директорій та live calls.
Виявити суперечності, підтвердити рішення або створити ADR proposals. Налаштувати
відтворювані documentation checks, описати M1 data/API/security contracts і tests.
Результат: environment report без secrets, M1 contract, оновлені state/handoff, локальний
coherent commit. M1 не починається. Детальний goal — `prompts/M0_BOOTSTRAP.md`.

## M1 — Корисний локальний мінімум

Створення/редагування/видалення нотаток, типи sleep/daily/creative/inbox, пошук,
короткі щоденникові поля, SQLite migrations, backup/restore та portable export.
Provider mock/OFF. Показувати реальні стани; немає клінічних висновків.
DoD: синтетичний CRUD round-trip, restart durability, timezone, schema validation,
consistent backup restore, приватний data root поза Git, docs/UI smoke tests.

## M2 — Offline-first на телефоні

Transport ADR, TLS/pairing/device revocation; локальна PWA-пам’ять та outbox,
ідемпотентний sync, conflicts/tombstones, safe update, storage-pressure поведінка.
DoD: сценарії `docs/OFFLINE_SYNC.md`; особисті дані заборонені до encryption/security gates.
Public Vercel demo допустимий лише за окремого deploy approval і тільки із synthetic data.

## M3 — AI без прихованих повноважень

Mock-contract, capability spike, мінімальний provider adapter, consent/context gates,
пам’ять і editable suggestions, jobs/timeouts/retry/usage. Спочатку нейтральна
організація щоденника/ідей, не неперевірені терапевтичні протоколи.
DoD: quota exhaustion, deny egress, prompt injection, no-shell escape, correction/deletion
propagation, resume state. Live smoke test потребує окремого обмеженого дозволу.

## M4–M6 — Додаткові можливості

M4: ASR benchmark UA, тиша/шум/переривання, audio retention, cancellation.
M5: бібліотека/теги, оригінал і proposal окремо, share approval, neutral-mode parity;
відсутність затвердженої game theme не блокує корисні творчі нотатки.
M6: permission/read-only/import/dedup/delete/revoke на реальному Android.
Неіснуюче/недоступне поле годинника не повинно зламати журнал або породити вигадане значення.

## M7 — Зміст, а не імпровізований «терапевт»

Підключити тільки protocol IDs з approved scope. Перевірити language fidelity,
step state machine, stop/pause, homework burden, risk routing, uncertain analytics.
DoD: evidence matrix, права на матеріали, потрібний професійний content review,
позитивні/негативні safety evals українською, регресія при model change.
Без clinical review — journal/creative release, не фіктивне «CBT-certified».

## M8 — Передача й особистий пілот

Install на чистому сумісному Mac-профілі, restart/wake, upgrade, rollback, restore
і перенесення на інше середовище. Інструкція видалення з опцією зберегти vault.
Власниця погоджує data flow, providers, retention, доступи. Пілот добровільний,
не доказ клінічної ефективності; можна зупинити без втрати даних/прогресу.

## Позарелізний backlog

Hosted personal shell, приватний relay, SaaS, native full app, shared accounts,
додаткові AI, інтеграції календарів, sophisticated game world. Немає дозволу будувати
їх, доки це не стало окремою ціллю й не пройшло privacy/rights review.

## M7B — bounded conversation-first engineering

Розмова/Щоденник/Більше; Free Conversation і Deep Session; versioned editable agreed goal/history,
exact revision binding, timestamped persistent messages, source-bound DailyConversationDigest /
GoalContextDigest, raw authority, edit/delete invalidation, local RetrievalReceipt і bounded
SQLite/filter/FTS5 goal-scoped retrieval. One Conversation Controller + typed skill contracts,
one future model voice; no swarm, no automatic journal/memory promotion. Mandatory embeddings/vector
DB та external embeddings відсутні. Live provider OFF, clinical active0, real private data OFF.
DoD: full synthetic regression, built desktop/390px UX, generated audio/explicit insertion, backup,
restart, privacy, final C→evidence R→normal main push. AWAITING_REVIEW не означає ACCEPT.

DEFERRED: genuine model-generated digest inference/provider tokenizer (live runtime permission OFF),
clinical typed skill execution (all27 findings OPEN; rights/content/admission gates), separately consented
journal/sleep/health tool activation (real private data permission OFF), vector retrieval (no measured gap ADR),
real local ASR/device keyboard smoke (no installed authorized model/private audio/phone test).
Foundation/stubs and synthetic tests виконуються зараз; ці gaps не блокують незалежні M7B tests.
M7C/M8 NOT_STARTED. [Contract](M7B_CONTRACT.md), [ADR](adr/ADR-008-M7B-CONVERSATION-CONTEXT.md).
