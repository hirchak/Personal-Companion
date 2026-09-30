# Робочий процес: власник → ChatGPT → Codex → GitHub

## Джерела істини

Для вимог: явне рішення власника та прийняті ADR. Для реалізації: реальні файли/diff,
Git-коміти й відтворювані тести. Для навігації: короткий `STATE.md` та `HANDOFF.md`.
Для клінічного змісту: затверджений protocol registry з accountable review.
Старий чат або snapshot не може довести, що код уже зроблений або тест пройшов.

Перед рев’ю читати через доступний GitHub connector за конкретним repo/ref/SHA.
Якщо connector недоступний після спроби — public GitHub або переданий diff/архів.
Не називати роботу verified, якщо видно лише повідомлення виконавця.
При недоступності джерел висновок `UNVERIFIED`, не припущення про успіх.

## Ролі й межі

Власник продукту: цілі, пріоритети, public/paid/deploy permissions, прийняття ризику,
standing direct-main development permission для цього test project та початок наступного етапу.
Власниця приватних даних: consent на її дані.
ChatGPT-архітектор: відновлення контексту, ТЗ, рекомендований model/reasoning/Plan Mode,
перевірка реалізації і вердикт. Це не фоновий працівник і не клінічний reviewer.
Codex: автономне виконання чітко обмеженої цілі, tests/fixes/docs/локальний commit.

## Цикл milestone

1. Архітектор читає актуальний стан і evidence останнього етапу.
2. Дає goal card: мета, межі, inputs, DoD, hard stops, модель/effort/Plan Mode.
3. Codex перевіряє actual environment, планує, реалізує, тестує, виправляє без
   погодження кожної дрібниці. Створює coherent implementation commit.
4. Codex оновлює state/handoff/report, зберігає evidence й повертає один звіт.
5. Створи implementation commit C і наступний evidence-only commit R на локальному `main`.
6. Після local checks, privacy/public-data scan та staged review — звичайний fast-forward
   push безпосередньо `origin/main`.
7. Architect читає точний pushed C/R SHA з GitHub і дає ACCEPT / FIX_REQUIRED / BLOCKED /
   UNVERIFIED. FIX_REQUIRED виправляється forward commit; опублікована історія не ховається.
8. Нова milestone goal усе одно потребує окремої явної цілі власника.

## Owner decision: test-stage direct-main workflow

Власник установив: нормальні development pushes `main` дозволені для кожного явно виданого
`/goal` після успішних перевірок. Це standing permission і не вимагає окремого погодження
для кожного звичайного push. `permissions.push_main` є окремим від `permissions.merge_main`:
прямий push не означає merge через PR чи дозвіл на інші merge-операції. Review branch не
потрібна за замовчуванням; goal може явно задати її, якщо це потрібно.

Ця згода дозволяє публікувати перевірений development commit у public `main`. Вона не
дозволяє release/tag, Vercel чи інший deploy, public runtime activation, витрати,
provider calls, billing/auth зміни або доступ до private data. Force-push/rewrite history
заборонені; `main` рухається тільки fast-forward. GitHub visibility/public-data privacy
scan залишається обов’язковим перед push. Architect review відбувається після публікації,
але ACCEPT не припускається й M1 автоматично не починається.

## SHA без рекурсивної пастки

C — implementation commit, включає код/контракти поточного етапу.
R — наступний evidence-only commit, містить STATE/HANDOFF/report/devlog, де записано C.
Report не може достовірно містити SHA власного R до створення коміту.
Після R виконавець у фінальному повідомленні наводить C, R, branch, base і push status.
Перевірка R−C має показати лише дозволені evidence-файли, без прихованих code changes.
Якщо після C змінено код — створити новий C, повторити релевантні тести та evidence.

`last_reviewed_sha` — останній реально переглянутий implementation commit; `implementation_sha`
— поточний кандидат. Null не замінювати фіктивними hashes. CI result прив’язаний до
того SHA, на якому він запускався; чітко показувати, чи це C або R.

## State discipline

STATE — компактний поточний стан, не щоденник усіх думок. HANDOFF — відновлення роботи
за кілька хвилин. Devlog — датовані короткі записи; reports — повні докази етапів.
Одночасно одна implementation-goal; паралельні research tasks допустимі з окремим scope.
Після context compaction Codex перечитує поточну ціль і state до нових мутацій.
Оновлення state робиться на checkpoint і перед завершенням, не після кожної команди.

Статуси реалізації: NOT_STARTED, IN_PROGRESS, BLOCKED, AWAITING_REVIEW, ACCEPTED.
NOT_RUN, HARDWARE_UNVERIFIED, MOCK_ONLY — статуси evidence, не синоніми ACCEPTED.
Слово PASS стосується конкретного тесту/набору, не всього продукту.

## Research workflow

Власник готує research за окремим файлом ТЗ. Вхідні файли спочатку quarantine/rights review,
потім бібліографія/синтез/claims index у дозволений research path. Завантажена робота не
стає активним skill. Evidence review, content review і engineering implementation окремі.

## Розбіжності й blockers

Перевірений код може суперечити опису state: виправити state, не ігнорувати код.
Нова вимога не переписує стару silently: додати рішення й вплив на milestone.
За справжнього blocker повернути виконане, точну причину, альтернативи й необхідний дозвіл.
Не питати повторно те, що вже є в репозиторії; не блокувати етап майбутньою косметикою.

## Свіжість ChatGPT Project

Чотири generated context documents — snapshots, а не live sync. Їх regenerated metadata
містить source file SHA-256 і repo commit, якщо він відомий. На початку нового чату
архітектор перевіряє STATE/HANDOFF/останній report через repo за потреби.
Не обіцяти абсолютну «пам’ять назавжди»: система дає відтворюване відновлення контексту.

`current_goal_path`, `current_contract_path` і `report_path` у STATE вказують на поточні
публічні документи. Генератор додає їх до delivery snapshot, щоб новий чат не отримав
лише старий M0 замість актуального ТЗ. Після завершення етапу підтримувати ці pointers.
