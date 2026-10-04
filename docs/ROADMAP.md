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
M7B_CONVERSATION_HOME: external ACCEPT — synthetic engineering scope; binding longitudinal/deep-goal addenda included.
M7C: external ACCEPT — live-synthetic engineering + local ASR capability.
M7D: external ACCEPT — live-synthetic engineering + bounded provider-quality evaluation + synthetic local-ASR guard.
M8A: external ACCEPT — synthetic release/install/upgrade/restore/rollback/uninstall readiness only.
M8B: external ACCEPT — real-reference-Mac synthetic dry run (reports/M8B_ARCHITECT_REVIEW.md).
M8C: external ACCEPT — private-local Mac core engineering; separately authorized owner core pilot STARTED.
M8D: IN_PROGRESS — optional private AI/local voice; real owner vault NOT TOUCHED, actual AI activation NOT_STARTED.
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


## M7C owner scope — 2026-10-04

M7B external ACCEPT — synthetic engineering scope, C f143dc9f82bb356ca10cbb4034cb8126ecf42aa3 / R73ec6064107d3d25475bb7454d96a2bd964ee77c. M7C is AWAITING_REVIEW in the currently authorized bounded preparation/runtime-evaluation goal; earlier M7B “M7C NOT_STARTED/live OFF” text is its historical checkpoint. M7C implements neutral controller, N01/N02, genuine synthetic provider evaluation and local ASR. Deferred: human/private voice quality and final hardware gate, real-user/provider activation, model-derived digest generation/tokenizer, clinical skills and all27 research admissions, MiniMax pending safe existing route, optional embeddings pending measured-gap ADR. M7D/M8 NOT_STARTED; no automatic continuation.

M7C exact evidence: [runtime report](../reports/M7C_CONVERSATION_RUNTIME_REPORT.md). N01/N02 CLOSED engineering;94/100requests, private activation/clinical0 unchanged.

## M7D owner goal — 2026-10-04

M7C external ACCEPT is scoped live-synthetic engineering + local ASR capability only; see
`reports/M7C_ARCHITECT_REVIEW.md`. Earlier M7D NOT_STARTED entries are historical checkpoints.
M7D AWAITING_REVIEW: source-bound Working Map, session focus/phases and continuity, exact selected-context
preview, neutral skills2.0, supported stronger synthetic model evaluation48 ceiling, PCM non-speech guard,
five qualification metadata packages OFF. No clinical review/activation; all27 findings OPEN; real data OFF.
M7C-N02 provider privacy hard gate OPEN, M6-N01 final0.6.1hardware NOT_RUN; M8 NOT_STARTED.

M7D final evidence: reports/M7D_DEEP_SESSION_REPORT.md; C 56b03bd3594a6d6630864904b6d99e46242de95a. Native ledger48/48, all failures retained; provider choice/private/clinical/hardware gates pending. M8 NOT_STARTED.


## M8A owner goal — 2026-10-04

M7D external scoped ACCEPT: reports/M7D_ARCHITECT_REVIEW.md exact C56b03bd / R0eaac557.
M8A synthetic release engineering; current authority: prompts/M8A_RELEASE_PILOT_READINESS.md / docs/M8A_CONTRACT.md.
Exact source package + prerequisites, safe defaults, separated roots, preflight/backup/migration,
fresh-root rollback/restore, foreground lifecycle, stale-client refusal and KEEP DATA uninstall.
M7D-N01/N02 hardening results belong to M8A report; historical M7D checkpoint text above remains evidence.
M8B NOT_STARTED. Real Mac/private vault/phone/Health/human ASR/transport/provider/clinical gates separate.

M8A final C38d3ed69839a8fc876c50b900552ad38d965c5cd:648Python/43Chromium/50web/build plus actual
package lifecycle PASS; release manifest identity and exact outcomes in reports/evidence/M8A.
N01 CLOSED_ENGINEERING; N02 OPEN with formal policy implemented (verb/human register quality unverified).
M8A AWAITING_REVIEW; M8B NOT_STARTED. No public Release/tag/deploy/private or hardware acceptance.


## M8B owner goal — 2026-10-04

M8A external ACCEPT exact C38d3ed6/R08d8efdd durable in reports/M8A_ARCHITECT_REVIEW.md.
Authorized actual Mac only/SYNTHETIC dry run. New release-aware backup/runtime-only lock, sanitized preflight,
exact-C Mac install/recovery lifecycle and inactive operator profile/handoff. Current authority:
prompts/M8B_REAL_HARDWARE_SYNTHETIC_DRY_RUN.md / docs/M8B_CONTRACT.md.
Actual private pilot NOT_STARTED; current Store is synthetic-only (PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED).
Phone NEEDS_TRANSPORT_GATE; optional provider/human ASR/Health/clinical remain independent OFF/NOT_RUN gates.

M8B final C434b1cd5ad857776bbfd9b3799a0abddec2858f6:667Python/43Chromium/19M8B/50web/build plus actual Mac
runtime-only/lifecycle and accepted old M8A cross-release upgrade/rollback PASS. N01/N02 CLOSED_ENGINEERING.
MAC_SYNTHETIC_DRY_RUN READY; MAC_CORE_PILOT NOT_READY / PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED;
PHONE_PILOT NEEDS_TRANSPORT_GATE. Independent optional AI/ASR/Health/clinical gates unchanged. No actual private pilot.

## M8B external ACCEPT / M8C owner goal — 2026-10-04

M8B external ACCEPT exact C434b1cd5ad857776bbfd9b3799a0abddec2858f6 / R1533a69c40c1eaa0a8f67a867724a8835101e0af
recorded in reports/M8B_ARCHITECT_REVIEW.md. M8A-N01/N02 CLOSED_ENGINEERING; historical evidence unchanged.
M8C IN_PROGRESS: final private-local core engineering gate, distinct mode/explicit consent/verified volume+permissions/
protected backups/core-only runtime/UI, actual reference Mac private path using ORIGINAL SYNTHETIC content only.
Current goal/contract prompts/M8C_PRIVATE_LOCAL_PILOT_RUNTIME.md / docs/M8C_CONTRACT.md. Actual private root
NOT_CREATED/pilot NOT_STARTED; phone/AI/ASR/Health/clinical/language gates carried independently.

M8C final implementation `a00a14277974b7f6c25846d0eb7a23879f86183a` — AWAITING_REVIEW.751Python/45Chromium/84M8C/50web/build and exact native
private-mode/synthetic-content full lifecycle/genuine rollback PASS. Core/storage/backup/activation READY
engineering-only; independent ACCEPT + owner/data-owner activation required. Actual private rootNOT_CREATED/
pilotNOT_STARTED; optional gates unchanged. No additional core milestone if acceptance/preflight pass.

## M8C external ACCEPT / explicit owner activation — 2026-10-04

External architect M8C ACCEPT, scope private-local Mac core engineering, exact Ca00a1427/R4eb8188;
reports/M8C_ARCHITECT_REVIEW.md. Separate explicit owner/data-owner goal authorizes own NEW EMPTY
core-only local vault/preflight/init/start/browser; activation IN_PROGRESS, pilot NOT_STARTED until init.
No further engineering milestone; all optional module gates unchanged. No private content access or import.

Owner/data-owner post-ACCEPT activation COMPLETE: native private-preflight PASS, new empty vault initialized,
protected backup target ready, accepted core app running locally; ACTUAL_PRIVATE_PILOT STARTED.
No samples/import/private-content reading; future developer content access remains NONE. Optional modules OFF.


## M8D optional owner integration — IN_PROGRESS

M8C external ACCEPT / real core activation remain durable. M8D adds owner-gated private conversation and pinned local voice using synthetic engineering roots; final cost binding FREE Luna/high, explicit Deep Luna/max or Sol6.1/high, four new native attempts total. No real-vault access or AI/voice activation before independent review. M7C-N02 bounded owner route pending exact-C native evidence; universal/zero-retention gate remains open. M7C-N03 OPEN_HUMAN_TEST, M7D-N02 OPEN_HUMAN_LANGUAGE_REVIEW, M6-N01 final0.6.1 hardware NOT_RUN, 27findingsOPEN/all5OFF/clinical0/phone separate.
