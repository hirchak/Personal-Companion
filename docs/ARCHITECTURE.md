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
