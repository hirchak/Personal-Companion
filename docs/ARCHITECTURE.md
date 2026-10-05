# Архітектура

## Рішення

Модульний моноліт на Mac + offline-capable клієнт. Одна логіка предметної області,
кілька адаптерів доступу. Не мікросервісна мережа, не агентний «рой».

```text
                     ПУБЛІЧНИЙ КОНТУР РОЗРОБКИ
 GitHub: код / специфікації / синтетичні тести / очищені reports
                      ↓ встановлення перевіреної версії
                    ПРИВАТНИЙ КОНТУР КОРИСТУВАЧКИ
 Mac UI ──────────────┐
 Android PWA + outbox ├── authenticated application API
 Optional Android    │                 ↓
 Health bridge ──────┘    capture / sync / sessions / analytics
                                       ↓
                       SQLite vault + private attachments
                                       ↓
                 jobs → allowed context → provider adapter
                                       ↓
                   Codex CLI cloud inference [за згодою]
                   MiniMax Token Plan [окрема згода]
                   Local ASR [без відправлення аудіо]
```

## Стек і межі модулів

Запропоновано Python + FastAPI/Pydantic, SQLite з міграціями, React/TypeScript + Vite,
IndexedDB у PWA, один persistent job runner. Конкретні версії lockfiles обирає Codex
після перевірки сумісності, а не бере найновіші навмання. SQLAlchemy/Alembic допустимі,
якщо спрощують тестовані міграції; це implementation decision в межах baseline.
SQLite призначена, зокрема, для локальних embedded-сценаріїв [S17].

Предметні модулі: identity/consent, capture, journals, creative library, protocols,
sessions/homework, memory, analytics, sync, jobs, providers, export/feedback.
Інтерфейси: HTTP API, локальний command adapter, згодом вузький MCP або Telegram.
Транспорт не дублює бізнес-логіку.

```text
repo/
  apps/core/              # сервер, домен, repository, jobs
  apps/web/               # один UI з local/offline adapters
  apps/android-bridge/    # лише після M6, не потрібен старту
  packages/contracts/    # схеми API/подій, узгоджені Python↔TS
  protocols/             # затверджені версії, спочатку порожній registry
  skills/                # статичні інструкції та контракти
  research/              # лише дозволений публічний дослідницький контент
  tests/                 # синтетичні дані
  docs/ reports/ prompts/ scripts/
```

Це цільова структура, не вимога створювати порожні десятки пакетів у M0.

## Control plane і data plane

Control plane розробки: Git, state, ADR, milestones, research review.
Data plane користувачки: vault, записи, аудіо, транскрипти, чати, wearable history.
Runtime читає підписану/версійовану бібліотеку, але не пише в репозиторій.
Розробницький Codex не отримує vault як робочу директорію. Поділ папок сам по собі
не є sandbox: процес під тим самим OS-користувачем може мати ширші права.
Для реального runtime потрібні least privilege, обмежені tools, чистий env,
відокремлені робочі директорії та перевірені правила файлового/мережевого доступу.

## Робота без AI

CRUD, локальний пошук, видимі завдання, перегляд дозволених статичних матеріалів,
запис голосу й створення feedback draft доступні без провайдера. Сервер не чекає
LLM, щоб прийняти запис. AI працює через чергу з timeout, cancellation і чітким статусом.
Не виконувати безконтрольні цикли ретраїв і не запускати повний аналіз vault на кожну правку.

## Відкритий/закритий ноутбук

Mac online: sync, ASR, jobs та авторизований AI можуть працювати.
Mac asleep/offline: встановлена PWA веде локальні записи; Mac jobs не виконуються.
Після пробудження — відновлення черги без дублів і без шквалу старих нагадувань.
Не обіцяти фонове виконання браузера: foreground-resume є обов’язковим сценарієм.

## Vercel

У першому baseline Vercel — необов’язковий public demo/documentation/static build,
не backend приватного vault. Особиста PWA спочатку обслуговується Mac через перевірений
приватний HTTPS-origin і кешує оболонку. Це зменшує залежність приватного виконання від
публічного хостингу. Перше встановлення потребує доступного Mac.

Варіант public static shell на Vercel для реальних записів можливий пізніше як окремий
security-reviewed mode: IndexedDB на телефоні, sync напряму до приватного endpoint,
без server actions, forms, functions, analytics та приватних payload на Vercel.
Завантажуваний JavaScript має доступ до розшифрованих даних, тому компрометація
deployment/update все одно є загрозою. «Лише static hosting» не гарантує нульового ризику.
Git integration створює deployments із push; тому її не підключати до приватного runtime
або неперевіреної review-гілки за замовчуванням [S14].

## Подальша переносимість

Repository/storage/provider interfaces, schema migrations і versioned exports дозволяють
змінювати реалізації. PostgreSQL, relay, desktop shell, кілька користувачів — окремі ADR,
а не приховані залежності V1. Контейнери, Redis і vector DB зараз не потрібні.

## Чинна M7B conversation-first foundation

Free Conversation / Deep Session є окремим local-first доменом. `conversation.py` — єдиний
Conversation Controller для persistence/CAS/idempotency і responder boundary;
`reflection.py` — deterministic goal/retrieval helper, не другий agent. React ConversationHome
використовує той самий API й M4 PCMRecorder/VoicePanel/storage, без другого audio/ASR stack.
Native modal sheets, internal journal filters і grid/list зберігають існуючий CRUD/export/history.

SQLite envelope schema9 додає conversations/messages/revisions, ReflectionGoal/history,
FTS5 unicode61 index, versioned source-bound DailyConversationDigest / GoalContextDigest equivalents
і metadata-only RetrievalReceipt. Entry2/health1/practice1 contracts незмінні. Triggers атомарно
оновлюють FTS і invalidation; backup integrity перевіряє goals/derived artifacts/receipts/index.
Restore не відновлює synthetic/provider authorization. Розмова прив’язана до exact agreed goal
revision, історія не переписується. Raw messages — source authority; digest MODEL_DERIVED.

Context Builder bounded за serialized JSON UTF8 bytes/консервативним token budget:
exact goal → current/recent turns → goal digest → daily digest → scoped FTS/filter raw sources;
narrow source expansion та explicit USER_CONFIRMED memory. Default goal-created→now або
explicit date range. Journal/sleep/health лише через separately authorized narrow tool contracts,
у M7B OFF. Вся історія не вантажиться на кожний prompt. SQLite/filter/FTS first; mandatory
vectors/embeddings відсутні, external embeddings заборонені. Later vectors тільки після measured-gap ADR.

Один controller/одна model voice, typed skill stubs, no swarm; no automatic conversation→journal/memory.
Live provider OFF, clinical active0, real private data OFF; M7C/M8 NOT_STARTED.
Канонічний [contract](M7B_CONTRACT.md), [owner ADR](adr/ADR-008-M7B-CONVERSATION-CONTEXT.md).


## M7C owner scope — 2026-10-04

M7C retains the Python/React/SQLite modular monolith, M7B raw/context/goal domains and M4 PCM/candidate pipeline. conversation_controller.py is the only model dispatch authority; conversation_runtime_contracts.py defines strict typed input/output, conversation_skills.py deterministic composition. Codex adapter uses current app-server stdio with ephemeral no-root thread, disabled tool features, deny-root/minimal-read permission profile, sanitized environment, fixed argv/shell=False, bounded IO/timeout/cancel and no fallback. Existing ChatGPT auth stays in the installed CLI. Host CLI working agreements are still injected: this is disclosed rather than claimed to be pure payload-only. Local whisper.cpp runs CPU through the M4 engine interface with pinned binary/model, filesystem and network sandbox and no cloud. ASR downloads/cache/corpus are ignored. Application defaults remain provider OFF; --m7c-synthetic plus explicit route is required. No auth/transport/crypto/storage permission weakening, PWA recorder rewrite, deployment or real-vault migration.

## M8E bounded UX refinement

[ADR-015](adr/ADR-015-M8E-CONSENT-AND-CONVERSATION-UX.md) and [M8E contract](M8E_CONTRACT.md) supersede
M8D's repeated checkbox/per-message popup UX for new consented ordinary sends, retaining its exact canonical
provider payload and source/profile checks. Additive local consent/scope tables stay in protected SQLite;
restore epoch invalidates durable acceptance. ComposerVoice reuses M4 PCM/Mac Voice/PWA encrypted PhoneStore.
No phone transport activation or provider call is part of engineering. Historical account-setting confirmation
claims are corrected forward by the owner's M8E clarification; no private transcript is used as evidence.
