# M0 — Bootstrap специфікації та контрольованого workflow

Рекомендовано: GPT-6.1 Sol; reasoning High, якщо доступно; Plan Mode OFF.
Не змінюй модель/налаштування удаваною інструкцією: перевір фактичний client state.

## Мета

Підготуй цей новий репозиторій до поетапної розробки Personal Companion. Прочитай
специфікацію, перевір її внутрішню узгодженість і локальне dev-середовище, зафіксуй
рішення/невизначеності й створи точний контракт наступного M1. Сам застосунок зараз
не реалізуй. Працюй автономно до цілісного review-ready результату.

## Контекст

Система local-first: Mac + приватний vault; offline Android PWA; сон/самопочуття,
творчі нотатки, opt-in self-help; Codex subscription first, MiniMax optional;
дані користувачки не входять у dev repo. Поточні docs — baseline proposals, не готовий код.
ChatGPT буде архітектором/рев’юером; ти підтримуєш durable state і evidence.

## Прочитати

`AGENTS.md`, `STATE.md`, `HANDOFF.md`, `.project/project.json`, `docs/PRODUCT.md`,
`docs/ARCHITECTURE.md`, `docs/PRIVACY_SECURITY.md`, `docs/OFFLINE_SYNC.md`,
`docs/WORKFLOW.md`, `docs/ROADMAP.md`, `docs/PROVIDERS.md`, `docs/TESTING.md`.
Інші матеріали — вибірково, коли потрібні. Не читай чужі або приватні директорії.

## Очікуваний результат

A. Environment capability report: OS/architecture/tool versions, git state/remote,
model/effort availability з доступного інтерфейсу або чесне NOT_VERIFIED. Без секретів,
серійних номерів, account IDs, списку домашніх файлів або приватного auth.json.
Не роби live inference лише заради цієї перевірки.

B. Пройдені documentation consistency checks, виправлені звичайні суперечності.
Для суттєвого відхилення від baseline — proposal ADR, не прихована заміна архітектури.
Список нерозв’язних зараз питань розділи на blocking-for-M1 і later-stage.

C. `docs/M1_CONTRACT.md`: scope, доменна схема M1, API boundary, non-AI capture/CRUD,
data-root isolation, міграції, export/backup/restore, fixtures, tests, acceptance evidence.
Задавай кінцеві результати, не багатосторінковий список команд. Не включай клінічні
протоколи, телефонний sync, native bridge, оплату або складну гру в M1.

D. Оновлені STATE/HANDOFF/короткий devlog, звіт `reports/M0_BOOTSTRAP_REPORT.md`,
локальний coherent commit і generated ChatGPT context. Ніяких фіктивних PASS.
Власна оцінка завершення — AWAITING_REVIEW, не ACCEPTED.

## Дозволені дії

Читати/редагувати тільки system repo, виконувати read-only environment probes,
стандартні local documentation checks, додавати потрібні невеликі dev-only validation
scripts і synthetic tests, робити локальні коміти. Якщо Git не ініціалізований,
допустимо `git init` у явно відкритій папці цього проєкту; не чіпай чужий repo.
Не встановлюй dependencies на всю систему; відсутній інструмент відзнач, не обходь sudo.

## Hard stops

Немає дозволу на remote push, створення GitHub repo, merge, Vercel deploy, launchd install,
network exposure, real user data, live provider calls, auth/billing зміни або M1 execution.
Не копіюй приватний додаток у repo чи test fixtures. Не використовуй особисті токени
власника для тестів. Не запускай destructive commands над невідомим worktree.

## Definition of Done

Пакет читається без суперечливих current-state claims; реальне середовище відрізнено
від припущень; M1 має перевірювані критерії; docs checks пройшли; privacy-scan result
задокументований із межами перевірки; state/report посилаються на implementation SHA.
Наступний milestone не почався. Поверни один підсумок: зроблено, тести, зміни,
C/R SHA, git/push status, blockers, потрібне рішення для продовження.
