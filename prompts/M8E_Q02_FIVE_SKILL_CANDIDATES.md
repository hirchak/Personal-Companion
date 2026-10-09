# M8E-Q02 — Five specialist skills: source-bound drafts and isolated evaluation

**Тип:** окрема bounded execution-goal у межах Personal Companion. **Це НЕ активація клінічних протоколів і НЕ реліз.**

**Canonical repository:** `https://github.com/hirchak/Personal-Companion.git`, default development branch `main`.

**Останній перевірений remote HEAD при підготовці ТЗ (2026-10-09):** `140a52f2ddc36abbeae957385cf54cf83abf01f5` (Q01 evidence R). Перед початком перевір фактичний `origin/main`, точні SHA та робоче дерево; не вважай цей SHA незмінним. Q01 отримав незалежний інженерний verdict **ACCEPT у чаті**; `STATE.md` може ще містити історичний `AWAITING_REVIEW`, це не дозвіл переписувати історію або самостійно оголошувати клінічний ACCEPT.

**Виконавець:** GPT-6 Astra, якщо доступна у встановленому Codex; бажаний підтримуваний reasoning **High**, якщо модель/інтерфейс дозволяють. Фактичні модель/effort зафіксувати, без вигаданих CLI flags і тихої підміни. **Plan Mode OFF** для execution; Astra сама обирає деталі реалізації й виконує звичайні тести/виправлення автономно.

## 1. Мета

Створити **п'ять змістовних, оригінально написаних українською кандидатних скілів**, оперти їх на простежувані джерела, конкретні безпечні сценарії розмови й перевірити у **строго ізольованому shadow/offline test mode**:

1. `cbt_reflection` — добровільне розрізнення події, думки/інтерпретації, емоцій і того, що невідомо; без примусового «спростування думок» чи терапії.
2. `worry_rumination` — помічати повторне прокручування, відділяти дійсну задачу від невизначеності та за потреби допомагати обрати паузу/нейтральний крок; без нав'язаної методики чи циклів запевнення.
3. `sleep_review` — обережна розмова про добровільно внесені відомості щоденника сну; немає виведення невідомих показників, причин або лікувальних рекомендацій.
4. `nightmare_review` — делікатне обговорення переживання після сну, якщо людина сама цього хоче; без символічних «істин», діагнозу травми, IRT/exposure без допуску.
5. `grounding` — добровільна низькоінтенсивна підтримка орієнтації/паузи та пояснення можливостей; жодних неперевірених доз, лікувальних обіцянок або нав'язаних інструкцій вправи.

Мета — **змістовні живі діалоги**, що слухають, розуміють запит, ставлять *одне доречне ненавідне запитання або жодного*, поважають «ні/стоп», не приписують прихованих мотивів, допомагають користувачу з власним осмисленням і не створюють залежності від бота. Ціль — максимально корисний wellness/self-reflection companion **без претензій на професійне лікування, діагностику чи клінічну валідацію**.

Результат цієї цілі: **CANDIDATE / OFF, готовий для наступного rights/evidence/qualified content review**, а не активні скіли в застосунку.

## 2. Inputs та порядок читання

1. `git status`, verified remote SHA, `STATE.md`, `HANDOFF.md`, `.project/project.json`, `AGENTS.md`, `docs/WORKFLOW.md`; поточна goal/contract/report і точний diff від `last_reviewed_sha` до фактичної бази.
2. `docs/M8E_Q01_CONTRACT.md`, `reports/M8E_Q01_CONVERSATION_QUALITY_REPORT.md`, `research/evals/m8e_q01/skill_audit.json`, `research/evals/m8e_q01/clinical_shadow_proposals.json`, Q01 `FINAL_CHARACTERIZATION.json`, `LIVE_SKILL_REVIEW.json`, `CASE_COVERAGE.json`, `rubric.json` і за потреби `LIVE_QUALITY_REVIEW.json`.
3. `docs/SAFETY.md`, `docs/AI_ORCHESTRATION.md`, `docs/M7_PREP_CONTRACT.md`, `docs/M7D_CONTRACT.md`, `docs/TESTING.md`, потрібні ADR; `research/admission/registry.json`, `research/admission/external/REVIEW_FINDINGS.json`, `PRIMARY_SOURCE_CHECKS.json`; `skills/qualification/*.json`, чинні `skills/conversation/*.json`, `scripts/qualify_m7d_skills.py`, admission/validation код.
4. Тільки **наданий власником локальний каталог RAW-досліджень**, без автообходу домашніх чи приватних директорій, без будь-якого доступу до Personal Companion vault. Каталог укажуть окремо (`PC_Q02_RAW_DIR` або прямий шлях). Вимагай стабільні оригінальні назви `Rxx_RAW.docx`; перевір SHA-256 і описуй тільки санітизовані назви, а не реальні приватні шляхи.

### Відповідність скіл → дослідження

Це **поточні canonical залежності з `skills/qualification/*.json`**, а не свідчення про затверджені докази:

| Скіл | Потрібні локальні RAW | Основні питання перевірки |
|---|---|---|
| `cbt_reflection` | **R05, R06, R11** | Thought records, перекручення/«когнітивна реструктуризація», citation16 у R05, авторська українська адаптація, права на шкали/шаблони |
| `worry_rumination` | **R06, R09, R11** | Rumination vs problem solving, межі reassurance, неконфліктний stop/skip, доказовість конкретних вправ та методологія R09 |
| `sleep_review` | **R01, R02, R04**; **R12 лише як межі Health** | Відсутні sleep-поля — UNKNOWN, WASO не заповнювати, жодної персоналізованої sleep restriction/compression чи CBT-I titration |
| `nightmare_review` | **R01, R03, R11** | IRT/популяція/протипоказання, зіткнення посилань R03, травма/кошмари/образи не є діагнозами |
| `grounding` | **R01, R08, R09** | PMR vs grounding vs breathing, відмінності evidence, без приписаної «ефективності» довільної техніки/дози, добровільність |

Отже, для цього завдання потрібна **локальна десятка** `R01`, `R02`, `R03`, `R04`, `R05`, `R06`, `R08`, `R09`, `R11`, `R12`. R12 **не** дає дозвіл на доступ до Health. R07/R10/R13–R16 не є автоматичними вхідними залежностями цих п'яти; якщо виявиш точну додаткову залежність, зафіксуй і попроси відповідний пакет, не скануй довільні папки.

RAW-документи — **unreviewed research**, часто вторинні/згенеровані звіти. Наявність DOI, бібліографії, PDF-цитати чи висновку у RAW **не дорівнює** перевірці першоджерела, прав, професійному review або дозволу на використання протоколу.

## 3. Стадії роботи в межах однієї goal

### A. Приймання та карта доказів (без фіктивного review)

- Побудуй local-only inventory: ідентифікатор, ім'я, SHA-256, дата/версія якщо зазначена, які розділи/твердження релевантні. Не копіюй DOCX у Git, web assets або synthetic fixtures.
- Для кожної майбутньої змістовної поради/питання/переходу запиши **claim-to-source матрицю** з точним locator (пакет, заголовок/таблиця/параграф, джерело/DOI якщо у RAW), applicable population/scope, достовірність перевірки, права/мову/ліцензійний статус, невизначеність і відповідний `RG-xx`. Не вигадуй точних сторінок чи перевірених DOI, яких немає.
- Розрізняй `RAW_ASSERTION`, `SOURCE_LOCATED`, `PRIMARY_VERIFIED` (лише якщо реально перевірено), `RIGHTS_UNKNOWN/RESTRICTED/EXACT_PERMISSION_EVIDENCED`, `CONTENT_REVIEW_PENDING`. Якщо немає права/перевірки — це GAP, а не автоматичний PASS.
- Збережи та явно пропрацюй особливо ризикові чинні findings: R05 citation16, R03 citation20/популяції/IRT, R02 WASO/пропуски/сонні інтервали, R08 помилкове перенесення pooled effects, R09 provenance, copy/translation/questionnaire rights, R01/R04 заборонені sleep-window protocols, R11 semantic safety. Інші застосовні `RG-xx` не губити.
- Read-only первинні джерела перевіряй тільки коли вони вже доступні через дозволений маршрут і scope; якщо потрібні сторонні завантаження, обхід paywall, нові обліковки/ліцензії чи непідтверджені права — познач `NOT_VERIFIED` і продовжуй незалежні ділянки.

### B. П'ять повних draft-пакетів (тільки локально поза Git)

Для **кожного** скіла підготуй придатний для рев'ю **оригінально сформульований** кандидатний пакет:

- `purpose / in_scope / out_of_scope`, показання як межі *самого продукту*, а не клінічні діагнози;
- початкова розмова: як розрізнити «хочу виговоритися», «хочу краще зрозуміти», «хочу один вибір/крок», «хочу нічого не робити»;
- українська тональність і приклади *доречних* запитань, альтернативи без запитань, наслідки виправлення користувачем та відхилення гіпотези;
- versioned **draft instructions**, state/step transitions тільки для добровільного self-reflection scope, `stop/pause/skip`, заборонені фрази та граничні ситуації;
- `input contract`, `proposed output`, source-aware uncertainty, reject/pause/no-health/no-private-data/no-auto-write;
- окремий reviewable `practice proposal` (якщо потрібна особлива методика), але **не** невалідуваний treatment script, «доза» або механізм автономного виконання;
- оригінальні синтетичні приклади позитивних/негативних діалогів із reasoning *у поясненні авторки*, не прихованим chain-of-thought провайдера;
- `evidence/rights/qualified reviewer/technical/activation` статуси та точні unresolved gates.

Два рівні: **нейтральні питання для обговорення** можуть бути якісно опрацьовані вже зараз; **методоспецифічний терапевтичний зміст** залишай кандидатною концепцією, якщо джерело/доза/права/протипоказання не підтверджені. Не створюй удавано «повністю готовий CBT/IRT» там, де немає прав і review.

Складай candidate drafts **у спеціальній локальній позарепозиторній, не-синхронізованій папці, визначеній власником** (окремо від входу RAW, app vault та Git). Її зміст призначений для owner+qualified review; не показуй у публічному repo жодних full RAW, захищених цитат, неочищених витягів, реальних нотаток чи raw third-party форм. У public Git можна зберігати тільки оригінальні synthetic case inputs, структури тестів, санітизовані review summaries, draft ID/version/hash, статуси/локатори і загальні safe design propositions. Для незалежного огляду детальних кандидатів власник **окремо передасть локальний review bundle**, без особистих даних.

### C. Ізольоване тестування й рекомендації

- Підготуй суттєву синтетичну матрицю для всіх п'яти, включно з багатокроковими «виправив вас», «передумав», «стоп», «просто послухай», «не знаю/бракує даних», «повернувся через тиждень», порушенням дозволених джерел і меж. Врахуй реалістичність живої бесіди, не тільки форму JSON.
- Відтворити критичні Q01 контрприклади (14 структурно валідних, але змістовно неприйнятних відповідей) і додати тести на 5 окремих ризиків: нав'язана CBT-диспутація, reassurance loop, вигадана діагностика/сонна метрика, символічний «діагноз сну», непогоджена релаксація/вправа. Реальна гостра криза vs художня цитата — різні випадки; поважати STOP та відмову.
- **Shadow / offline** може перевіряти draft wording, contracts, sanitized routing, відхилення/версіонування, фіктивні модельні відповіді й fail-closed OFF на реальному контролері. **Scripted fixture ≠ live-model behavior ≠ clinical effectiveness.** Не подавай естетичну оцінку Astra як незалежну клінічну валідацію.
- Вимірюй корисність через anchored rubric, точні відповіді/уривки, `NOT_EVALUATED`, окремі critical safety failures; порівнюй пропоновані правила з Q01 baseline лише там, де постановки й умови реально еквівалентні. Підготуй blinded packet для подальшого незалежного якісного review.
- Перевір, що звичайний controller **досі не підвантажує** ці п'ять скілів, не отримує нових `runtime_instructions`, не відкриває доступ до vault/Health, не запускає вправ, не записує нічого автоматично в journal/memory/goal. Можливість обійти OFF через довільний JSON/prompt injection має давати FAILURE.
- Для семантичного safety-gap із Q01 підготуй чіткий risk/safety architecture proposal і приклади негативних тестів: **не** позначай gap CLOSED тільки тому, що п'ять скілів OFF, або тому, що модель один раз дала безпечну відповідь. Будь-яка продукційна модифікація safety routing/semantic response gate — **окрема reviewable implementation goal**; не внось її приховано зараз.

### D. Готовність до наступних етапів

Для кожного кандидата дай чесний статус за незалежними gates:

`SOURCE_RECEIVED / SOURCE_MISSING` → `EVIDENCE_SCREENED / UNVERIFIED` → `RIGHTS_REVIEW_REQUIRED` → `DRAFT_PREPARED` → `SHADOW_TECH_TESTED / NOT_RUN` → `QUALIFIED_CONTENT_REVIEW_REQUIRED` → `ACTIVATION_OFF`.

Ніколи не підвищуй ці статуси до `APPROVED`/`ACTIVE` на підставі технічних тестів чи оцінки Astra. Дійсний protocol activation потребує точного вмісту/версії/hash, застосовності, rights/license scope, accountable **кваліфікованого** reviewer, позитивних/негативних тестів після змістового review та окремого дозволу власника; термінальні `clinical flags = OFF` залишаються незмінними.

## 4. Permissions та hard stops

**Цією Q02 дозволені:** читання лише явно вибраних RAW research-файлів у наданому локальному каталозі; підготовка local-only п'яти draft-бандлів; публічні санітизовані metadata/tests/evidence, автономне локальне тестування зі synthetic fixtures; допустимі зміни research/eval tooling та docs. Рутинний normal fast-forward push перевірених **public-safe** C/R комітів у `main` дозволений уже standing owner workflow.

**НЕ дозволені:** жодні нові live AI inference attempts через ChatGPT/Codex, MiniMax чи API (залишок 12/24 спроб **Q01 goal-scoped**, не переносити на Q02); витрати, token-plan маршрути, додаткові account/auth/key/credit/billing зміни; системні інсталяції/downloads, remote access; реальні приватні повідомлення, vault, запис голосу, Health, owner pilot, phone; клінічні claims, тест з реальними пацієнтами/людьми, активація терапевтичного змісту; macOS packaging, release/tag/deploy/publication. За потреби live synthetic model evaluation сформулюй окремий точний запит власнику з route/models/budget/attempt cap, але не виконуй до дозволу.

**Не змінюй** `skills/qualification/{cbt_reflection,worry_rumination,sleep_review,nightmare_review,grounding}.json` із `runtime_instructions:null` на виконуваний payload, не розмикай production gates, не переписуй історію, не роби force-push, не створюй новий milestone за замовчуванням.

**Hard stop лише залежної частини:** бракує потрібного DOCX/підтвердження локального каталогу; немає rights/primary source; потрібна фахова думка; система бажає витратити квоту чи додати системні компоненти. Продовжуй незалежні безпечні підзадачі; не вигадуй missing evidence або дозвіл.

## 5. Definition of Done (реальні докази)

1. Для кожного з 5 скілів — локально окремий повний **оригінальний review-ready candidate draft**, revision/hash, source/claim/gap matrix, українські варіанти питань, refusal/stop/uncertainty, limits/contraindications як *кандидат на фаховий розгляд*. Якщо якихось джерел немає, конкретне `BLOCKED_PARTIAL`/`NOT_VERIFIED` замість вигаданої завершеності.
2. Повний публічно безпечний індекс усіх п'яти з `CANDIDATE_OFF`, без runtime clinical instructions і без RAW/docx; мінімальний offline/shadow test harness і case-level evidence для позитивних, негативних і провокативних синтетичних кейсів.
3. Відтворюваний доказ, що clinical OFF, Q01 semantic gap не приховано, production controller/consent/context/source/privacy boundaries не змінено, жодного зовнішнього inference attempt і жодної приватної інформації.
4. Реальні команди/exit codes для релевантних тестів (включно з повним Python/web/build, якщо сфера змін вимагає), M7 admission, qualification, docs/context/privacy/public-tree scan; `NOT_RUN` чесно зафіксовано. Не вимагати безкінечних self-hash commits.
5. `docs/M8E_Q02_CONTRACT.md`, `reports/M8E_Q02_FIVE_SKILLS_REPORT.md`, актуальні `STATE.md`, `HANDOFF.md`, append-only devlog; локальний **review bundle index** із SHA (без приватних шляхів/вмісту в public звіті). Звіт відповідає: *що можна вже тестувати в sandbox, що не перевірено, які exact sources потрібні, що чекає qualified review, і які обов'язкові наступні goals?*
6. Класичний test-stage цикл: exact base → **implementation C** → exact-C tests → **evidence-only R** → privacy+rights check → normal fast-forward push у `main` → verify exact `origin/main==R` → **STOP: AWAITING_REVIEW**. `ACCEPT` визначає тільки незалежний reviewer, не Astra.

**Принцип:** якість діалогу важлива не менше, ніж безпека. Але кращі промпти й офлайн-стабільність не є доказом лікувальної ефективності та не дозволяють використовувати неапробовані практики на реальній людині.
