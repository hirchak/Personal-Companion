# M8F — Personal Companion for macOS: standalone application, installer and safe updates

**Тип:** одна bounded **engineering execution-goal**. Наступний продуктово-інженерний етап після M8E-Q03, а **не** дозвіл на фактичну передачу застосунку іншій особі або на зовнішню публікацію. Codex автономно планує та реалізує в межах цього документа. Якщо відсутнє право/передумова для окремого кроку, продовжуй незалежну роботу та зафіксуй конкретний gate, не підмінюй результат імітацією.

**Канонічний репозиторій:** `https://github.com/hirchak/Personal-Companion.git`, гілка `main`.

**Відомий HEAD при постановці:** `f32038f62e276400c41fb21c76ce753316b7aaa7` (M8E-Q03 evidence R). **Перевір свіжий actual `origin/main` перед роботою; не покладайся на рухомий `main` або на цей історичний SHA.** Незалежний інженерний review для M8E-Q03: `ACCEPT` у розмові з власником, без клінічного/релізного/приватного допуску. Відмінності між review у чаті та `STATE.md` не виправдовують переписування історії.

**Рекомендований виконавець:** GPT-6.1 Sol / High, якщо саме цей профіль доступний у встановленому Codex. Перевір модель/effort локально; не вигадуй CLI flags і не роби тихої підміни. Plan Mode **OFF** для execution (самостійне планування всередині виконання). GPT-6 Luna / High підходить для окремих чітких підзадач, але ця ціль вимагає одного відповідального інтегратора.

## 1. Результат, який потрібен власнику

Перетвори нинішнє local-first ядро, React UI і локальні компоненти на **звичайну macOS-програму** з робочою назвою *Personal Companion*, яку людина встановлює через `.dmg` або інший обґрунтований нативний macOS-пакет, відкриває через Finder/Dock і використовує без Codex, Terminal, Git, Node чи окремо налаштованого Python. Якщо для обраної реалізації потрібні зовнішні ліцензовані/непередавані активи, чесно відокрем їхню готовність від готовності базового продукту.

Ключові сценарії: **перший запуск → локальне сховище → щоденник/творчість/розмова → локальний запис голосу та Whisper (за наявності законно пакованих активів) → закриття/повторний запуск → пропозиція «Доступна нова версія» → користувачка натискає «Оновити» → перевірена нова версія стартує зі збереженими даними**. Якщо update неможливий, стара версія і її приватні дані залишаються цілі.

**Ця goal має дати працюючий engineering-кандидат**, а не просто план або моковий скриншот: власна `.app` і тестовий `.dmg`, автономний запуск ядра, end-to-end сценарії пакування та update/rollback на оригінальних синтетичних даних. Підписаний/notarized зовнішній реліз і справжня доставка через мережу є **окремим gate**; без Developer ID, права на notarization, хостинг і permission їх **не оголошувати готовими**.

## 2. Перші inputs і архітектурний baseline

Перед будь-якими змінами: перевір repo/branch/clean tree, actual remote HEAD, `STATE.md`, `HANDOFF.md`, `.project/project.json`, `AGENTS.md`, `docs/WORKFLOW.md`, поточні goal/contract/report та diff від точного `last_reviewed_sha` до бази. Не переносити в цю goal стан іншого проєкту.

Особливо перечитай/повторно використай:

- `docs/INSTALL.md`, `docs/INSTALLATION.md`, `docs/UPGRADE.md`, `docs/RECOVERY.md`, `docs/UNINSTALL.md`, `docs/PILOT_HANDOFF.md`, `docs/TESTING.md`;
- `docs/M8A_CONTRACT.md`, `docs/M8B_CONTRACT.md`, `docs/M8C_CONTRACT.md`, `docs/M8E_CONTRACT.md`, `docs/M8E_Q03_CONTRACT.md`, `reports/M8E_Q03_SEMANTIC_RESPONSE_SAFETY_REPORT.md`;
- release implementation (`apps/core/release.py` і супутні manifest/backup/preflight/launcher), current `requirements.runtime.lock`, JS build pipeline і packaged assets;
- приватне сховище/permissions/OS isolation та ADR-011/012/013/014/016/017; local ASR receipt, engine/model licence і actual package profile;
- чинні локальні тести M8A–M8E, Mac synthetic lifecycle і source-vs-installed package compatibility.

Інженерно прийняті механізми release-маніфесту, typed PRIVATE_LOCAL root, FileVault/APFS preflight, SQLite backup, migration та integrity **не переписуй без доказу необхідності**. Пакет M8C/M8D/M8E зараз **prerequisite-based unsigned source package**, а не готова standalone `.app`: це відома прогалина, яку закриваємо. Спочатку короткий ADR про обраний нативний shell, embedded runtime, ASR, update та signing model із trade-offs і перевірними рішеннями; сам вибір технології залишаю тобі.

## 3. Native shell і автономний запуск

1. Створи нативний macOS `.app` для насамперед **Apple Silicon**. Перевір на референтному MacBook Air M2/16 GB, наявній macOS та фактичних dev tools. Обрану мінімальну версію macOS, arch support і межі Intel визнач за перевіреним середовищем, не вгадуй.
2. Вікно застосунку із чинним українським UI, Dock icon, нормальним quit/reopen, фокусом, стандартними keyboard/selection/scroll/resize поведінками. Повідомлення про помилки й недоступні optional modules — зрозумілі, не технічні traceback/шляхи.
3. Embed/ship саме необхідні pinned локальні компоненти (UI assets, Python/backend/runtime dependencies, нативні helper binaries). **Запуск з Finder без Terminal, Homebrew, Git, Node та `.venv` проєкту.** Процес повинен бути scoped до поточного користувача, без root/admin daemon; один екземпляр; локальна доставка UI і API лише через loopback/дозволений ізольований канал; відсутність необґрунтованого LAN/зовнішнього listen.
4. Зроби безпечний механізм передачі локальної авторизованої сесії між оболонкою і backend; **не відкривай credential/token у URL, process args, console, browser history або логах**, не послаблюй existing Origin/Host/CSRF/auto-lock/source gates. Приватний сервер коректно завершується при Quit, не залишає orphan process, дозволи на мікрофон запитуються лише за дією людини. Autostart at login — opt-in/окремий контроль, не беззаперечний дефолт.
5. Залиш чинну local-first візуальну ідентичність. Ніякого нового редизайну великого масштабу та ніякої прихованої фонової хмари.

## 4. Перший запуск і локальні дані

1. Onboarding: пояснення «дані локально», обсяг резервних копій, privacy/AI boundaries, вибір власниці, а не згода від розробника. На чистій **синтетичній** тестовій установці створюється тільки новий порожній локальний сховок за явним підтвердженням. Жодних імпортованих `.env`, developer secrets, fixtures, чужого auth state або робочих записів.
2. `~/Library/Application Support/...` або обґрунтована macOS-конвенція для per-user app data **поза bundle і поза Git**. Поважай існуючі PRIVATE_LOCAL/FileVault-protected APFS, owner-only permissions, volume/data/backup security preflight та manual explicit data-owner consent. Невідповідність не виправляти через silent chmod/переміщення/послаблення політики: ясна помилка і шлях відновлення.
3. Локальна SQLite + attachments/audio та потрібні runtime assets не залежать від доступності мережі. Порожня DB ініціалізується only once; старий root ніколи не переписується. Restart/sleep/wake/lock crash handling із захистом цілісності, станом interrupted jobs і зрозумілим відновленням.
4. Мінімальний UI/меню для відкриття, діагностики, статусу компонентів, backup/export/restore, «Про програму», версії та перевірки оновлень. Функції не мають тихо торкатися довільних папок чи зовнішніх акаунтів.
5. Existing owner pilot **не інспектувати, не сканувати, не оновлювати, не мігрувати й не підключати як тестову базу**. Actual private-data activation/upgrade — окрема власницька згода після незалежного review; тут disposable original-synthetic Mac roots тільки.

## 5. Whisper / голос / AI без прихованих залежностей

1. Native microphone → локальний PCM/audio record → durable local storage → pinned **whisper.cpp** і перевірена multilingual модель → **редагований** український transcript draft → лише явний Send text. Без cloud ASR, raw audio provider payload, автонадсилання, фонового розпізнавання без дії.
2. Перевір наявні exact engine/model binaries, версії, SHA, архітектуру, права на **redistribution**, модельне джерело та обсяг. **Якщо юридично/технічно можна включити — пакуй потрібний Whisper engine і weights**, щоб користувачці не треба було їх встановлювати; тестуй з пакованими байтами, не з dev-cache. Якщо license/пакування/потреба нового download невідомі, познач `ASR_BUNDLE_BLOCKED` із точним blocker, не підставляй fake ASR і не завантажуй приховано. Навіть за недоступного ASR запис/історія локального аудіо має працювати зі зрозумілим відновленням.
3. AI optional і default OFF. Збережи існуючі Free Luna/high і Deep Luna/max або Sol6.1/high, explicit scope/consent, Q03 response-release safety, source/Deep hashes та відсутність PAYG/fallback. **Standalone app core/voice не повинні вимагати логіну ChatGPT.** Наявний Codex subscription/provider route можна використовувати лише як окремо активований, реально доступний і підтверджений route; відсутня на Mac Codex-інсталяція/авторизація — явна `AI_UNAVAILABLE`, не автоматичне встановлення чи копіювання credentials. Новий «Sign in with ChatGPT», MiniMax Token Plan / API і provider-key UI — **поза цією goal**, окремі дозволи/перевірка термінів та приватності.
4. П'ять Q02 specialist candidates **CANDIDATE/OFF**, `runtime_instructions=null`; Health, clinical, phone transport, remote/cloud sync, telemetry і зовнішні embeddings — OFF. Q03 universal semantic safety OPEN; not a licensed therapist, no clinical claims/automatic escalation promise. Знайдений гострий ризик має узгоджуватися з Q03's чинним fail-closed маршрутом, доки немає належного qualified content review.

## 6. Installer, оновлення й rollback

**Installer:** обраний `.dmg` має містити реальну `.app` з однозначною версією, build ID, exact source SHA, залежностями, asset/lock/licence receipts. Відтворюваний packaging contract із known inputs; output під `generated/`/ignored, не в public git. Developer/test build не називати notarized чи production-ready. Перевір `codesign`, entitlements, hardened runtime, Gatekeeper і notarization readiness за документованими Apple requirements; signing/notarization credentials не створювати й не підбирати без owner action.

**Updater:** інтерфейс «Перевірити оновлення», «Доступна нова версія» → **одна кнопка «Оновити»** + зрозумілий прогрес/перезапуск. Архітектура — перевірені release artifacts та authenticity/integrity, не `git pull main`, не виконання remote shell scripts, не ненадійний `latest`/checksum із того самого непідтвердженого джерела. Вибери підтримуваний macOS updater (наприклад Sparkle 2 або інший обґрунтований безпечний варіант) із незалежно прив'язаним signing verification, channel/version/build identity і anti-rollback. Не винаходь неперевірений власний downloader/updater із привілеями. Signing private keys ніколи не потрапляють у код, app bundle або публічні артефакти.

**Локальний simulation end-to-end:** підготуй два release candidates A→B і test-only feed/signatures у ізольованій локальній sandbox, аби перевірити реальне staged update/copy/swap/relaunch flow, а не лише текст кнопки. Test-only signing identity **не є** production trust і ніколи не дозволяє приймати production updates; не додавати можливість увімкнути непідписане production update одним прапорцем. Offline/absent feed → стара версія працює. Wrong signer, corrupted/tampered archive, downgrade, replay, wrong product/channel/arch, migration error, disk full, interrupted download/swap, concurrent app instance → fail closed без втрати даних і без напівакивного застосунку.

**Data migration:** перед несумісною зміною застосунок зупиняє локальні writers/jobs, перевіряє source root/version/volume, створює узгоджений verified pre-update backup SQLite **з WAL + attachments + receipt**, перевіряє restore у копію і migration plan. Тільки тоді atomic/versioned upgrade; помилка залишає prior app і backup доступними без silent data loss, destructive downgrade або reset. **Код rollback і дані rollback — різні операції.** Приватні резервні копії за чинною FileVault/APFS політикою; не стверджуй, що вони криптографічно зашифровані самим застосунком, якщо такої функції немає.

**Доставка «нам → їй»:** розділи `private/public source repository`, `reviewed release artifacts`, `signed update feed/hosting` і `private user vault`. Наявний repo public; зміна visibility — не в межах цієї goal. Підготуй два підтримувані deployment design options (signed binaries у дозволеному downloads host та authenticated private distribution) й рекомендацію, але **не створюй сервіс, не публікуй binaries, не роби GitHub Release, tag, upload, domain/DNS/deploy**. Жодних GitHub PAT у клієнті. Production update-channel enablement має залишатися DISABLED до окремого дозволу і signing/hosting acceptance.

## 7. Тести та Definition of Done

Потрібен об'єктивний, відтворюваний **exact implementation-C** доказ:

- `.app` відкривається кліком на референтному Mac із **чистого disposable профілю**, ізольованого від репозиторію/dev runtime, без `python`/`node`/`git` у runtime PATH; паковані backend і frontend реально працюють. Виміряй cold start, memory/disk/CPU на перевіреному hardware; unknown підтримку інших Macs познач NOT_VERIFIED.
- Clean first-run GUI, local DB, записи/редагування/видалення, пошук, творчість, Free/Deep history з AI OFF, autolock, restart/wake, voice recording, local Whisper **тільки якщо реально bundled**, no audio provider traffic, consent/ASR independent toggle. Для optional private AI — deterministic synthetic adapter/mock readiness; жодних фактичних provider calls.
- Browser/native-window/UI end-to-end без Terminal; responsive Mac, permission-denied microphone, no local ASR, application already running, app quit and relaunch, no ghost processes/ports, only approved loopback traffic. Browser/JS UI tests не підмінюють native Finder application smoke.
- Synthetic A→B one-button update, progress/install/restart, previous user notes/history/audio and vault identity preserved, schema/receipts/backup/restore; atomic rollback/failed update; keep-data uninstall. Verify signatures/tamper/channel/anti-rollback and exact source/asset manifest before applying; explicitly mark production notarization `NOT_RUN` якщо немає легітимних credentials/permission.
- Q03 regression: no unreviewed partial text, 24 known bad fixtures fail to publish, normal positives still work. Existing M1–M8E full relevant Python, web/build, Playwright/Chromium, schema/admission/qualification, local security/backup/upgrade/restore/rollback, privacy/rights/public-Git object checks. Preserve original failures; false-green prohibited.
- Explicit external permissions matrix: no network downloads/account use, provider inference 0, no trial private vault, no remote upload/telemetry, no code auto-update from Git, five clinical flags OFF, Health/phone OFF. Distinguish `ENGINEERING_PASS`, `TEST_SIGNED_LOCAL_ONLY`, `DISTRIBUTION_BLOCKED`, `NOT_RUN` та `READY_FOR_OWNER_REVIEW`; не оголошуй GIRLFRIEND_READY без independent release acceptance і data-owner consent.
- Документація: architecture/ADR, build instructions, signing/notarization plan, license/SBOM/runtime inventory, how first install works, update feed contract, support/uninstall/keep data/backup/restore/recovery; компактний український end-user guide without terminal, exact known unknowns and handoff for future signed release/host.

**Обов'язкові артефакти:** buildable native shell sources, packaged development `.app` and test `.dmg` (поза Git), local updater-test artifacts (поза Git), bounded acceptance matrix, exact-C test log receipts, `docs/M8F_CONTRACT.md`, `reports/M8F_MACOS_APP_REPORT.md`, `STATE.md`, `HANDOFF.md`, append-only devlog, потрібні ADR. Якщо signing/ASR assets/integration truly blocked — опиши часткову реальну готовність, точні blocking prerequisites та implementable safe shell без fake PASS.

## 8. Дозволи і hard stops

**Дозволяю лише** писати/редагувати код застосунку, нативний launcher, local bundled packaging logic, локальний GUI/update harness, synthetic disposable Mac smoke й dev `.app`/`.dmg` build із вже наявними дозволеними інструментами/залежностями, документацію і routine C/R fast-forward push у `main` після перевірок. Нові Mac app artifacts / source не означають дозвіл їх виконати над старим приватним пілотом.

**НЕ дозволено без окремої згоди власника:** системні інсталяції (Homebrew/Xcode/глобальні tools), неузгоджені нові network downloads/dependencies/model weights, Developer ID account/cert access або підпис production identity, notarization upload, GitHub Releases або інший artifact hosting/deploy/publication, зміна repo visibility, domain/remote services, система background daemons/login item без opt-in, реальний owner vault/backup/pilot migration, installation on another person's Mac, provider/auth/key/paid calls, Sign in with ChatGPT OAuth, MiniMax, phone/Health/sync, нові clinical practices чи safety-gate послаблення. Якщо потрібна нова project-local third-party залежність, звір її exact license/source/version/signing і **спитай окремий scoped дозвіл до завантаження**; не став глобально й не обходь Gatekeeper.

Відсутність signing identity не блокує чесні локальні synthetic app/update tests, але блокує `DISTRIBUTABLE_NOTARIZED`. Відсутність Whisper redistribution clearance не блокує offline журнал, але блокує claim про «full ASR package». Немає approved update host — tests локально, `LIVE_UPDATE_DISTRIBUTION_NOT_AUTHORIZED`.

Нормальні engineering помилки, тести й невеликі рішення вирішуй сам. Якщо виникла фундаментальна неможливість виконати мету без окремого дозволу — оформлюй `BLOCKED_PARTIAL` із точним запитом рішення, не роби небезпечного workaround і не підмінюй native app web shortcut-ом.

## 9. Delivery workflow

1. Повторно перевір actual remote `main`, local status, reviewed implementation SHA і exact diff; реалізуй та тестуй автономно, не мікроменеджеруй кожну підзадачу.
2. Зроби один coherent implementation **C** (або forward C2 при реальному fix); exact-C synthetic Mac/native tests, package validation, source/rights/privacy scans і безпекові інваріанти.
3. Evidence-only **R** містить report/state/handoff/devlog/evidence; після normal fast-forward push у **main** verify remote HEAD == точний R. Без force-push, rewrite history, окремого review branch за замовчуванням або повторного owner дозволу на routine push.
4. STOP `AWAITING_REVIEW`, передай точні base/C/R SHA, verified outcomes, реальні `.app`/`.dmg` локальні шляхи **лише власнику**, blockers для майбутньої distribution і питання до owner. **Не встановлюй у реальний pilot, не відправляй дівчині й не починай наступний milestone**. Інженерний ACCEPT у ChatGPT — окрема дія після exact diff review.

**Центральне питання фінального звіту:** «Чи можна інсталювати, запустити і безпечно оновити Personal Companion як самостійну macOS-програму на чистому синтетичному середовищі референтного Mac, а якщо ні — які саме незалежні blocked gates лишилися для першої реальної передачі користувачці?»
