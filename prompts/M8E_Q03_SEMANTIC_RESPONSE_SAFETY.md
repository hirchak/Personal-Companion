# M8E-Q03 — Semantic response-release safety for Free / Deep

**Тип:** одна bounded execution-goal у чинному Personal Companion / M8E; це не клінічна активація, не пакування macOS і не release.

**Канонічний репозиторій:** `https://github.com/hirchak/Personal-Companion.git`, development branch `main`.

**Останній перевірений `origin/main` при підготовці:** `5130e92e1454b95b5066ddb4fcd0b2212e142338` (M8E-Q02 evidence R, 2026-10-09). Перед будь-якою зміною перевірити фактичний HEAD, робоче дерево і exact SHA; не вважати наведений SHA незмінним.

**Модель-виконавець:** **GPT-6.1 Sol / High**, якщо підтверджується встановленим Codex. Немає потреби залучати Astra лише через назву задачі. Якщо профіль недоступний, повідомити конкретну перешкоду; без тихої підміни. **Plan Mode OFF** для виконання. Codex сам вирішує реалізаційні деталі та звичайні інженерні виправлення.

## 1. Мета

Зміцнити **реальну межу між генерацією, перевіркою, показом і збереженням AI-відповіді** в нейтральних `Free` та `Deep`. Відповідь, ще не допущена до показу, не повинна виходити в інтерфейс через streaming/partial previews, API polling, history, working map, closures, retry або інший side channel.

Забезпечити **обмежену, перевірювану semantic-safety політику** для психологічно підтримувальної розмови українською. Змістовна безпека не випливає з правильного JSON або відсутності доступу до клінічних скілів. Знайдені Q01/Q02 ризики мають отримати явні рішення та тести, а не формальне `PASS`.

**Не вимагати неможливого:** універсальна безпомилкова семантична класифікація без перевірених засобів і кваліфікованих критеріїв недосяжна. Якщо частина контент-рішень потребує фахового review або окремого model-based assessor із додатковими викликами, позначити її **OPEN / NOT_VERIFIED**, підготувати вузький fail-closed шлях та hard stop для відповідної активації, не вигадуючи захисту.

## 2. Канонічні inputs і baseline

1. `STATE.md`, `HANDOFF.md`, `.project/project.json`, `AGENTS.md`, `docs/WORKFLOW.md`, точний `main HEAD`, чинні Q02 goal/contract/report та diff від останнього reviewed implementation SHA.
2. `docs/M8E_Q02_SEMANTIC_SAFETY_PROPOSAL.md` — головний вихідний safety-дизайн, не реалізований захист; `docs/M8E_Q02_CONTRACT.md`, `reports/M8E_Q02_FIVE_SKILLS_REPORT.md`.
3. Q01 `reports/M8E_Q01_CONVERSATION_QUALITY_REPORT.md`, `reports/evidence/M8E_Q01/FINAL_CHARACTERIZATION.json`, Q02 `reports/evidence/M8E_Q02/SEMANTIC_CHARACTERIZATION.json`, вихідні synthetic fixtures/cases, `docs/SAFETY.md`, `docs/TESTING.md`, `docs/AI_ORCHESTRATION.md`, відповідні ADR і privacy/consent contracts.
4. Фактичний controller: `apps/core/conversation_controller.py`, provider adapter, relevant API/status/polling, web streaming/preview UI, local private AI gate, source/Deep/goal contracts і тести. Перевірити **усі** канали показу та персистенції, не покладатися на припущення про єдине поле `partial_candidate`.

На останньому перевіреному SHA `ConversationController.run()` накопичує `self.previews[id]` з часткового JSON `assistant_text` ще до `ConversationCandidate.model_validate_json`, `main_question_count`, `verify_address_form` та transaction commit. `get()` і `page()` можуть повернути `partial_candidate` під час `RUNNING`. Технічні структурні перевірки **не є** semantic-safety рішенням. Це конкретна вхідна проблема; повторно підтверди її на actual base.

Q01: **14** authored unsafe/unwanted outputs були структурно прийняті. Q02: ще **10** спеціалізованих authored unsafe outputs структурно прийняті; **10** спроб JSON dispatch клінічних скілів правильно відхилені. Це **характеризація тестових фікстур**, НЕ частота збоїв реальної моделі. Q02 specialist bundles залишаються локально поза Git; не треба читати їх для цієї goal.

## 3. Обов'язковий інженерний результат

### A. Safe response-release boundary

- Розділити внутрішній `GENERATING / AWAITING_VALIDATION` і зовнішній `RELEASED / FAILED / CANCELLED` стани. Реалізаційні назви обери автономно; не ламай чинні публічні API-контракти без версійованого обґрунтування.
- До успішного завершення **всіх** потрібних structural, source/context/freshness і застосовних content-release перевірок показувати лише нейтральний progress indicator, **не** `assistant_text`/JSON/deltas/partial candidate. Знайди та закрий фактичний backend→API→web витік, а не тільки CSS-маскування.
- Після погодженого рішення оприлюднювати лише **точно перевірену й незмінну відповідь**, узгоджену з request/context/goal/source/skill/model/version/release-policy hashes. Не «виправляти» текст після review непомітно, не міняти контекст, не робити інший provider call для підміни відповіді.
- При помилці, timeout, відсутньому або протермінованому content-decision, скасуванні, AI OFF/revocation, restart, змінах джерел/цілі/consent/profile — **не показувати і не записувати** недопущений текст. Оригінальне повідомлення користувача зберігати за чинним контрактом, показати безпечний статус/пояснення; не витікати через помилки, history, map, closure або retry.
- Перевірити потокові дельти, polling, snapshots/page, browser UI, session race, а також відсутність сирих текстів у логах і public reports. Довести, що при жодному негативному переході кандидат не стає видимим/збереженим поза контрольованим шляхом.
- Врахувати latency/UX: delayed final text допускається, але явний статус «AI формує/перевіряє» має бути зрозумілим. Не обіцяти миттєвий streaming, якщо для цього треба випускати неперевірене.

### B. Content-safety policy і обмежена реалізація

Створити **версійовану, відтворювану й тестовану** модель рішень для нейтральної підтримки. Вона має розрізняти принаймні:

1. звичайну безпечну рефлексію, корисне уточнення або повагу до «не ставте запитань»;
2. явне `ні / стоп / не пропонуйте вправу`, яке забороняє примусове продовження;
3. неоднозначний ризик, коли доречне мінімальне ненавідне уточнення, а не автоматичний діагноз;
4. повідомлення про **наявну безпосередню небезпеку**: без підміни екстреної/людської допомоги звичайною Deep-аналітикою;
5. цитату, художнього персонажа або гіпотетичну сцену, які **не** слід автоматично приписувати людині;
6. недопустимі претензії на роль фахівця, діагнози/призначення, нав'язану вправу, неможливі гарантії, безумовне підтвердження хибного переконання, цикли запевнень.

**Важливо:** проста таблиця заборонених слів, самодекларація `safe=true` від основної моделі або той самий LLM як єдиний суддя без незалежного review **не** закривають змістовий gap. Визначити чесний діапазон детермінованого захисту, failure modes, false positives/negatives та `UNVERIFIED` частини. Не перетворювати кожну складну фразу на відмову і не карати людину за художній текст.

Самостійно обери адекватну в межах дозволів інженерну реалізацію boundary/policy (наприклад review adapter із strict default-deny за відсутності потрібного рішення, а також вузько визначені й перевірені критерії там, де це можливо). Якщо реальна семантична оцінка за обраною архітектурою потребує **додаткової AI inference, нових залежностей, професійно затверджених текстів чи клінічного рішення**, не підключай це без дозволу: ізолюй, зафіксуй blocker, збережи відповідний gate OFF. Обережний випуск нешкідливих звичайних відповідей не повинен видаватися за 100% захист.

Не активувати терапевтичні практики й не змінювати `skills/qualification/*` / Q02 кандидатів. Зберегти чинний стиль української та `FORMAL_VY` без переписування цитат.

### C. Регресії та вимірювані докази

- Зберегти **14 Q01 + 10 Q02** відомих semantic counterexamples. Додати варіанти перефразування, заперечення, цитування, художній і реальний контекст, «стоп», нові дані, безпечні мінімальні пари; розрізняти механічний **блок показу** від правильної **змістової класифікації**.
- Негативні перевірки: malformed/rejected response, decision timeout/failure/staleness, model/source/consent drift, race/cancel/retry/restart, streaming progress і фінальне persistence ordering. Перевірити **відсутність передчасного тексту в API, DOM, history, map, closure**, відсутність витоку в error/log/public report.
- Позитивні перевірки: корисна Free/Deep рефлексія, одна доречна відповідь на пряме питання, відсутність питання на прохання, слухання, зрозуміле завершення, виправлення старої хибної гіпотези, цитати художніх текстів, неризиковий сон, source-bound Deep context. Не перетворити систему на суцільну відмову/недієздатний чат.
- Для кожної safety категорії вести точні `ACCEPTED / REJECTED / NOT_EVALUATED` спостереження та інженерні/змістові limitations. Авторські фікстури — не live model output і не клінічний gold standard. За відсутності кваліфікованого review — `QUALIFIED_CONTENT_REVIEW_PENDING`.
- Верифікувати повний relevant Python/web/build/browser і pinned exact-C runtime, M7 admission/qualification, docs/context/privacy scan та fallback/non-network invariants. При first-run infrastructure failure документувати точні reruns; не називати часткові повторні перевірки «один повний PASS».

## 4. Межі та hard stops

**Дозволено:** потрібні зміни в neutral backend/controller/UI, synthetic fixtures і sandbox tests, response-release mechanism, версійовані policy/config contracts, docs/ADR (за архітектурної зміни), локальні тести, normal development C/R commits і normal fast-forward push у `main` після перевірок.

**Заборонено:** нові реальні AI inference calls (включно з Q01 unused12 attempts), використання MiniMax/API/покупок/кредитів, нова auth/billing схема, збирання приватного vault/аудіо/Health, читання owner pilot, інсталяція чи оновлення його без окремого дозволу, зміна clinical flags/OFF, нові терапевтичні протоколи, автоматичне записування в журнал/пам'ять/Health, нові системні компоненти або скачування, phone transport, розгортання/публікація/release/tag, force-push.

Якщо робочий implementation потребує зовнішнього незалежного content-owner, платної/підписної оцінки, чинної provider permission, нового model route або реальних даних — **hard stop лише залежної частини**, продовжити незалежний engineering scope і чесно описати `BLOCKED/NOT_VERIFIED`. Не вимагати додаткових погоджень для рутинних тестів/виправлень чи normal main FF push.

Перший Mac-пілот уже існує; **ця goal не змінює його конфігурацію**. Інженерний `ACCEPT` Q03 **не** підтверджує клінічну ефективність, не схвалює всіх ризикових ситуацій і не дозволяє новий приватний runtime deployment.

## 5. Definition of Done

1. Зафіксовані exact base/reviewed SHA, diff, фактичні канали leakage й testable architecture decision (ADR за потреби).
2. **Відсутність недопущеного AI-тексту** у streaming/polling/UI/history/map/closure за негативних scripted synthetic тестів; не лише відсутність DB commit.
3. Реалізована й задокументована **bounded** semantic release policy, версія/хеш binding, failure/unknown paths і окрема таблиця `KNOWN_COVERED / OPEN / QUALIFIED_REVIEW_REQUIRED` без універсальних гарантій.
4. Відтворювана матриця небезпечних і безпечних мінімальних пар, 24 попередні bad fixtures, normal Free/Deep positive flows, UI/browser failure/abort/restart/drift tests, критичні помилки як окремий результат.
5. Усі п'ять спеціалізованих скілів залишаються OFF / `runtime_instructions=null`. Немає додаткових provider calls чи приватних даних, не порушено consent/source/Deep/map/audit/backup/contracts.
6. Public-safe `reports/M8E_Q03_SEMANTIC_RESPONSE_SAFETY_REPORT.md`, контракт `docs/M8E_Q03_CONTRACT.md`, актуальні `STATE.md`, `HANDOFF.md`, devlog, тестові logs/exit codes і явний список наступних content/release gates. `NOT_RUN` ніколи не називати `PASS`.
7. Звичайний власницький процес: exact `main` → coherent implementation **C** → exact-C tests → evidence-only **R** → staged privacy/public-source scan → normal FF push у `main` → exact remote verification → **STOP: AWAITING_REVIEW**. Не починати macOS packaging / іншу goal самостійно.

**Центральне питання звіту:** «Які саме небезпечні або недопущені відповіді система технічно не показує до перевірки, що лишається змістовно неперевіреним, і чи може людина нормально користуватися Free/Deep без зайвих блокувань?»