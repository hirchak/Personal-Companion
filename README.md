# Personal Companion — local-first personal workspace

**Робоча назва, не затверджений бренд.** Пакет специфікації v0.1.0 · 30 вересня 2026.

Репозиторій власника: [hirchak/Personal-Companion](https://github.com/hirchak/Personal-Companion.git).
GitHub підтверджено як public, actual default branch `main`. Owner дозволив normal
fast-forward development pushes у `main` для явно виданих goals після local checks.
`push_main` відокремлений від merge, deploy, provider і приватних даних.

Локальний особистий простір: щоденники сну й самопочуття, структурована самодопомога,
творчі нотатки, голосове введення та добровільна м’яка гейміфікація. Mac зберігає
основний приватний vault; телефон може накопичувати власні локальні записи до синхронізації.
AI — додаткова можливість, а не умова збереження запису.

**M1/M2 engineering/synthetic ACCEPT за зовнішнім review; M3 AWAITING_REVIEW.**
CRUD чотирьох типів, історія, пошук/фільтри, selected export/backup, encrypted offline PWA/sync
та локальний mock runtime із exact consent, jobs, memory й reversible suggestions. Зовнішній AI,
deploy, реальні записи, клінічні протоколи та M4+ OFF. AI mode починає роботу OFF.

```bash
./scripts/setup_demo.sh
./scripts/demo.sh /private/tmp/personal-companion-m1-synthetic-demo
```

Відкрити `http://127.0.0.1:8765`, ввести одноразовий код із термінала. Stop: Ctrl+C.
Повторний запуск зберігає synthetic записи й створює новий код; після lock потрібен restart.
Незбережений текст не переживає reload/lock. [Runbook](docs/INSTALLATION.md),
`reports/M1_LOCAL_JOURNAL_REPORT.md`, [M1 contract](docs/M1_CONTRACT.md).

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

## M2 synthetic PWA

`./scripts/m2_demo.sh /private/tmp/personal-companion-m2-synthetic-demo` після setup.
Mac UI `/`, PWA `/phone/` на `http://127.0.0.1:8765`; local passphrase + one-use Mac invitation.
Offline encrypted entry/outbox, explicit sync/conflicts/reconciliation, safe shell updates,
recovery and storage warnings. Це desktop localhost simulation, не real Android transport.
[Contract](docs/M2_CONTRACT.md), [crypto ADR](docs/adr/ADR-001-M2-PHONE-CRYPTO.md),
[transport candidate](docs/adr/ADR-002-M2-TRANSPORT.md), [hardware gate](docs/M2_ANDROID_GATE.md).
`reports/M2_OFFLINE_PWA_SYNC_REPORT.md` містить актуальні evidence/limitations.

## M3 synthetic runtime candidate

M2 external ACCEPT is recorded in `reports/M2_ARCHITECT_REVIEW.md` (synthetic engineering only).
M3 adds working local mock/explicit exact-context consent, bounded jobs, reversible proposals and
user-controlled provenance memory inside the Mac UI; pending/finalized pairing fixes M2-N01.
`docs/M3_CONTRACT.md`, `docs/adr/ADR-003-M3-RUNTIME.md` and `reports/M3_SAFE_RUNTIME_REPORT.md`
carry scope/evidence. AI starts OFF; actual Codex runtime calls remain PROVIDER_DISABLED/NOT_RUN.
No real-data/hardware/clinical/deploy/M4+ approval. Run existing M2 demo script with a new synthetic root.

## M4 local voice candidate

[Contract](docs/M4_CONTRACT.md): synthetic microphone capture, encrypted offline phone audio,
private Mac attachment/resume, editable ASR candidate and explicit journal confirmation/retention.
Open «Голосовий запис» near the heading. Actual ASR model and Galaxy gate remain NOT_RUN;
explicit synthetic fake ASR does not establish speech accuracy. No cloud speech/automatic M3 calls.

```bash
./scripts/m4_demo.sh /private/tmp/personal-companion-m4-synthetic-demo
npm --prefix apps/web run build
.venv/bin/python -m pytest -q tests/test_m4_browser.py
```

Use generated fake media only during M4 acceptance. [Follow-up ASR](docs/M4_LOCAL_ASR_RUNBOOK.md)
and [Galaxy microphone](docs/M4_ANDROID_MIC_GATE.md) require their separately scoped permissions.


M5 synthetic candidate: [contract](docs/M5_CONTRACT.md), [report](reports/M5_CREATIVE_FEEDBACK_SPACE_REPORT.md).
After `npm --prefix apps/web run build`, run
`./scripts/m5_demo.sh /private/tmp/personal-companion-m5-synthetic-demo` and open loopback Mac `/`
or encrypted phone `/phone/`. Use «Творча полиця», «Відгук» and optional device-local cosmetics.
Feedback produces exact-approved local files only. At the M5 checkpoint Health was OFF; M6 scoped
read-only verification is described below. Providers/clinical/deploy and M7+ remain OFF.

## M6 Health Connect

Read-only Sleep/Steps/Exercise bridge + separate imported-health copy, neutral Mac controls and
truthful PWA status. No source writes, health AI, background/history/location permissions or clinical
inference. Early real Galaxy debug gate verified private import/replay/incremental and Sleep revoke;
Exercise NO_RECORDS. Later native recovery/cancellation changes are build/unit checked, hardware
follow-up NOT_RUN. [Contract](docs/M6_CONTRACT.md), [Galaxy runbook](docs/M6_GALAXY_HEALTH_GATE.md),
[report](reports/M6_HEALTH_CONNECT_REPORT.md). Synthetic demo: `./scripts/m6_demo.sh`.
