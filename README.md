# Personal Companion — local-first personal workspace

**Робоча назва, не затверджений бренд.** Пакет специфікації v0.1.0 · 30 вересня 2026.

Репозиторій власника: [hirchak/Personal-Companion](https://github.com/hirchak/Personal-Companion.git).
GitHub підтверджено як public, default branch `main`. Для явно виданих test-stage goals
owner дозволив normal fast-forward development pushes у `main` після перевірок.
`push_main` відокремлений від merge, deploy, provider і приватних даних.

Локальний особистий простір: щоденники сну й самопочуття, структурована самодопомога,
творчі нотатки, голосове введення та добровільна м’яка гейміфікація. Mac зберігає
основний приватний vault; телефон може накопичувати власні локальні записи до синхронізації.
AI — додаткова можливість, а не умова збереження запису.

**Цей репозиторій зараз містить технічну документацію та допоміжні скрипти документації,
а не реалізований застосунок. Жодний програмний milestone ще не прийнято.**

## Початок

Прочитати [START_HERE.md](START_HERE.md), потім [AGENTS.md](AGENTS.md),
[STATE.md](STATE.md), [HANDOFF.md](HANDOFF.md).
Поточний стан завжди перевіряти на конкретній Git-гілці та commit SHA, а не за пам’яттю чату.

## Документи

| Задача | Джерело |
|---|---|
| Продукт, межі, вимоги | [PRODUCT.md](docs/PRODUCT.md) |
| Архітектура | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Приватність і довіра | [PRIVACY_SECURITY.md](docs/PRIVACY_SECURITY.md) |
| Телефон і синхронізація | [OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md) |
| Дані й довготривала пам’ять | [DATA_MEMORY.md](docs/DATA_MEMORY.md) |
| Оркестратор і скіли | [AI_ORCHESTRATION.md](docs/AI_ORCHESTRATION.md) |
| Codex, MiniMax, доступ і витрати | [PROVIDERS.md](docs/PROVIDERS.md) |
| UX, творчість, гейміфікація, фідбек | [EXPERIENCE.md](docs/EXPERIENCE.md) |
| Samsung Health і голос | [INTEGRATIONS.md](docs/INTEGRATIONS.md) |
| Межі самодопомоги | [SAFETY.md](docs/SAFETY.md) |
| Дослідження | [RESEARCH_PLAN.md](research/RESEARCH_PLAN.md) |
| Послідовність розробки | [ROADMAP.md](docs/ROADMAP.md) |
| Робота ChatGPT ↔ Codex ↔ GitHub | [WORKFLOW.md](docs/WORKFLOW.md) |
| Перевірки | [TESTING.md](docs/TESTING.md) |
| M0 evidence, workflow decision і M1 proposal | [M0 report](reports/M0_BOOTSTRAP_REPORT.md), [direct-main goal](prompts/M0_DIRECT_MAIN_FINALIZATION.md), [M1 contract](docs/M1_CONTRACT.md) |
| Встановлення і перенесення | [INSTALLATION.md](docs/INSTALLATION.md) |
| Рішення й відкриті питання | [DECISIONS.md](docs/DECISIONS.md), [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) |
| Перевірені технічні джерела | [SOURCES.md](research/SOURCES.md) |

## Базові принципи

- Public GitHub містить лише код, очищену документацію, дозволені дослідження та синтетичні тести.
- Особистий vault не є Git-репозиторієм. Відгук для розробників — окрема погоджена копія.
- Збереження на пристрої, синхронізація, хмарний AI та публікація — чотири різні дії зі своїми дозволами.
- Поведінка AI обмежується кодом, версійованими сценаріями й перевірками. Ніякого автономного лікування.
- Один явно виданий milestone → local checks → C/R commits → direct-main push → architect review.
- Наступний milestone все одно потребує нової owner goal; direct push не є release/deploy.

## Ліцензування

Ліцензію коду ще не обрано. Public repository сам по собі не означає open-source ліцензію.
Не додавати чужі платні PDF, книги, шкали, ігрові ассети чи повні тексти без перевірки прав.
