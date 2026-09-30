# Перевірені технічні джерела й дослідницькі орієнтири

Дата перевірки: **2026-09-30**. Джерела нижче використано для вузької перевірки
архітектурних передумов. Це не завершений deep research і не список затверджених
клінічних протоколів. Документація/тарифи/доступи можуть змінюватися: перед інтеграцією
перевірити конкретну версію, аккаунт і дату. Де немає відповідного device test, сумісність
не підтверджена. Проєктні рішення й обмеження — наші вимоги, не обов’язково вимоги вендора.

У документах `[Sxx]` посилається на ID у цьому файлі.

## S01

**OpenAI — Authentication**

URL: https://developers.openai.com/codex/auth/

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено режими ChatGPT sign-in / API-key, відмінність обліку та credential storage. Локальний CLI не означає offline inference.

Рішення проєкту: Provider auth, секрети, окремий runtime gate.

## S02

**OpenAI — Non-interactive mode**

URL: https://developers.openai.com/codex/noninteractive/

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено codex exec, structured output, збережену авторизацію й ephemeral flag. Не підтверджує будь-яке довільне комерційне застосування підписки.

Рішення проєкту: Локальний private adapter після capability/terms перевірки.

## S03

**OpenAI — Models**

URL: https://developers.openai.com/codex/models

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Офіційний каталог містить gpt-6.1-sol і gpt-6-luna; доступні effort та доступність залежать від клієнта/акаунта.

Рішення проєкту: Перевіряти фактичну модель перед goal, не вигадувати ID.

## S04

**OpenAI — Developer commands**

URL: https://developers.openai.com/codex/cli/slash-commands

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено /goal та межу objective 4000 символів.

Рішення проєкту: Повне ТЗ у файлі; короткий goal-pointer.

## S05

**MiniMax — Token Plan Overview**

URL: https://platform.minimax.io/docs/token-plan/intro

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено Subscription Key ≠ PAYG API Key; 5-hour/weekly quota; доступні purchased Credits можуть покривати перевищення.

Рішення проєкту: Окремий billing/seat/consent gate, без непомітного fallback.

## S06

**MiniMax — M3 announcement**

URL: https://www.minimax.io/blog/minimax-m3

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Офіційний матеріал описує M3 і 1M context; дата матеріалу 2026-06-01. Старі launch prices не є ціною конкретного акаунта сьогодні.

Рішення проєкту: Довгий контекст не скасовує мінімізації даних.

## S07

**MDN — Service Worker API**

URL: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Service worker підтримує кешування/офлайн-механізми; це не постійний довільний background server.

Рішення проєкту: Cached shell; foreground resume як обов’язковий шлях.

## S08

**MDN — Storage quotas and eviction criteria**

URL: https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Browser storage має quota/eviction; persistence може бути не надана; явне очищення користувачем можливе.

Рішення проєкту: Не обіцяти абсолютну надійність phone-only data, додати backup/sync status.

## S09

**Chrome Developers — Local Network Access**

URL: https://developer.chrome.com/blog/local-network-access

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Офіційний опис локального мережевого доступу та browser permission. Перевіряти поведінку конкретного браузера.

Рішення проєкту: Не вважати public shell → local Mac автоматично працездатним.

## S10

**Android Developers — Health Connect architecture**

URL: https://developer.android.com/health-and-fitness/health-connect/architecture

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Архітектура Android SDK/IPC, дані на пристрої та дозволи. Не web REST API для PWA.

Рішення проєкту: Native bridge для автоматичного читання Health Connect.

## S11

**Samsung — Health Data SDK overview**

URL: https://developer.samsung.com/health/data/overview.html

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено доступ до вибраних даних Samsung Health і обмеження SDK. Не всі доступні типи гарантовані на будь-якому wearable.

Рішення проєкту: Альтернативний integration path з device/permission checks.

## S12

**Samsung — App creation process**

URL: https://developer.samsung.com/health/data/process.html

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено окремий development/verification/partnership процес.

Рішення проєкту: Не ототожнювати developer-mode прототип із production distribution.

## S13

**Android Developers — Synchronize data**

URL: https://developer.android.com/health-and-fitness/health-connect/sync-data

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Changes tokens, upsertion/deletion і resync потребують явної стратегії.

Рішення проєкту: Ідемпотентний importer із source IDs/checkpoints.

## S14

**Vercel — Deploying Git Repositories**

URL: https://vercel.com/docs/git

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено Git-triggered deployments та production/preview workflow.

Рішення проєкту: Не підключати неперевірену гілку до особистого runtime automatic deploy.

## S15

**MDN — getUserMedia**

URL: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Mic capture потребує secure context і дозволу.

Рішення проєкту: HTTPS і consent; тестувати interruptions на Samsung.

## S16

**whisper.cpp — official project repository**

URL: https://github.com/ggml-org/whisper.cpp

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Офіційний проєкт описує локальне ASR та Apple Silicon/Core ML support.

Рішення проєкту: Кандидат для Mac ASR; UA benchmark потрібен окремо.

## S17

**SQLite — Appropriate Uses**

URL: https://www.sqlite.org/whentouse.html

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: SQLite підходить для embedded/local application storage в описаних межах.

Рішення проєкту: Локальна DB без окремого сервера як baseline.

## S18

**Telegram — Bot API**

URL: https://core.telegram.org/bots/api

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Long polling; невидані updates зберігаються не довше 24 годин.

Рішення проєкту: Не робити Telegram гарантованим offline journal при тривалому sleep Mac.

## S19

**Telegram — FAQ**

URL: https://telegram.org/faq

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Secret Chats і cloud chats мають різні властивості. Ботовий канал не слід називати Secret Chat.

Рішення проєкту: Opt-in channel, не primary private vault.

## S20

**OpenAI — Usage policies**

URL: https://openai.com/policies/usage-policies/

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Перевірено обмеження порад, що потребують професійної ліцензії, без належної участі фахівця.

Рішення проєкту: Safety boundaries в поведінці, а не лише дисклеймер.

## S21

**NHS — Depression in adults overview**

URL: https://www.nhs.uk/mental-health/conditions/depression-in-adults/overview/

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Сторінка радить звернутися до лікаря при підозрі на депресію. Це не діагностика користувачки.

Рішення проєкту: Не відкладати людську оцінку заради розробки застосунку.

## S22

**OpenAI — Projects in ChatGPT**

URL: https://help.openai.com/en/articles/10169521-projects-in-chatgpt

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Офіційні project files/instructions. Наші generated files залишаються snapshots до регенерації.

Рішення проєкту: Чотири context файли + project instructions, Git для актуального стану.

## S23

**SQLite — Backup API**

URL: https://www.sqlite.org/backup.html

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Узгоджене резервування живої SQLite через передбачений механізм.

Рішення проєкту: Backup/restore тест, а не naive file copy.

## S24

**Apple — Controlling app access to files in macOS**

URL: https://support.apple.com/guide/security/controlling-app-access-to-files-secddd1d86a6/web

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Файлові дозволи macOS мають перевірятися як окрема частина установки.

Рішення проєкту: Не обіцяти безумовний доступ/автозапуск на чужому Mac.

## S25

**GitHub — Licensing a repository**

URL: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository

Статус: PAGE_CHECKED · 2026-09-30.

Перевірено: Public visibility і надання open-source license — не одне й те саме.

Рішення проєкту: Ліцензія коду та права на research/assets потребують явного вибору.

## Клінічні seed-джерела, що ще НЕ пройшли review цього пакета

- AASM, Position Paper for the Treatment of Nightmare Disorder in Adults (2018):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5991964/ — full-text fetch під час підготовки
  зупинився на browser challenge. Не позначено як прочитаний клінічний огляд.
- NICE NG222, Depression in adults: https://www.nice.org.uk/guidance/ng222 — seed для R07;
  recommendations fetch не був доступний. Потрібен окремий повнотекстовий перегляд.
- NICE CG113, Generalised anxiety disorder and panic disorder in adults:
  https://www.nice.org.uk/guidance/cg113 — seed для R01/R06; recommendations fetch 403.
- Consensus Sleep Diary, CBT-I guidelines, сучасні IRT meta-analyses: знайти й перевірити
  в R02–R04; не вигадувати DOI, результати, dosage або права на адаптацію.

Ці seeds не є evidence approval. Під час research фіксувати причину відсутності
повного тексту та не робити claim лише з назви або AI-конспекту.
