# M8F-F01 — Native GUI Voice Start: bounded forward fix

**Тип:** одна explicit execution goal в межах M8F Personal Companion, що виправляє вузький блокер F09 після незалежного engineering review M8F (вердикт **FIX_REQUIRED**). Це не новий milestone, не повторення повного M8F і не дозвіл на release/передачу застосунку користувачці.

**Canonical repo:** `https://github.com/hirchak/Personal-Companion.git`, development branch `main`.

**Останній незалежно перевірений GitHub `main` HEAD на момент постановки:** `1c09275937c6f152ad09efc8b781591d617359e2` (M8F evidence R). **Останній M8F implementation C11:** `23bcb16a0d33e4d86377ad60c4fcce216f8c808d`. На початку execution звір актуальні remote/local SHA та `git status`; не припускай, що `main` не рухався.

**Модель:** рекомендується **GPT-6.1 Sol / High**, якщо реально доступна у встановленому Codex; перевір actual model/effort. **Plan Mode OFF**. Codex автономно досліджує причину, обирає технічний fix, виконує нормальні перевірки і forward commits у межах цілі; не мікроменеджерити.

## 1. Причина цілі й чесний baseline

З M8F C11 вже отримано і підтверджено за source/evidence:

- Справжню ARM64 `.app`/`.dmg`, standalone Python/UI/Whisper, GUI/onboarding, збереження даних і реальне Sparkle A101→B102 на **synthetic** даних.
- Exact-C11 Python **1042 PASS**, web **53 PASS**, packaged Whisper і lifecycle PASS, native guard STARTING pre-update PASS.
- Але **C11 native GUI synthetic PCM voice-start двічі залишився в `STARTING` і був скасований**: **F09 ≠ PASS**. Раніший C10 native GUI PCM→Whisper→edit→confirmed save PASS — це лише evidence для C10, не C11. Backend packaged-ASR PASS не підмінює GUI-to-end PASS.
- В `apps/web/src/ComposerVoice.tsx` `start()` очікує `PCMRecorder.start()`, який очікує `getUserMedia` і `AudioContext.resume()`; це можливі точки зависання, **але причинність ще не встановлено**. Не оголошуй root cause до діагностики. `LOCAL_TEST` перехоплює getUserMedia через `WKUserScript` і блокує фізичний мікрофон через WK delegate — ці межі зберегти.
- C8 зафіксував матеріальний інцидент можливого не-синтетичного фізичного захоплення аудіо. Власник дозволив видалити лише точний інцидентний root без читання вмісту; **не відновлюй його, не повторюй фізичне захоплення й не оголошуй усю історію synthetic-only**.
- Тестове середовище фактично було Mac M2 / 8 GB / macOS 27, не заявлені M2/16 GB; інші Mac/OS, normal TCC/human UA ASR і production signing — NOT_VERIFIED.

## 2. Мета

На новому точному implementation SHA **довести нативний synthetic end-to-end F09**, не послаблюючи безпеку:

1. У справжній LOCAL_TEST `.app` (Finder/native WKWebView), новий окремий disposable test-home, вбудована **авторська synthetic PCM fixture**, фізичний мікрофон **достовірно заборонений**.
2. Контрольований цикл `IDLE → STARTING → RECORDING → stop → SAVING → LOCAL_AUDIO_SAVED → TRANSCRIBING → TRANSCRIPT_READY / REVIEW_REQUIRED → editable transcript → explicit user save/send → durable confirmation`, із підтвердженням після закриття/повторного відкриття або перевіреного перезапуску. Не вважати клік/напис «Зберегти» durable acknowledgement.
3. Помилки / відмови / повільний чи ніколи не завершений `getUserMedia` або `AudioContext` не залишають UI навічно у `STARTING`; `Cancel` є дієвим, пізній асинхронний callback не починає запис і не пише в сховище після скасування.
4. Нативне «Перевірити оновлення» / Sparkle **не можуть почати preparatory backup/update**, доки існує `STARTING`, `RECORDING`, `SAVING` або незбережений аудіодрафт — навіть коли strip/panel прихований. Перевір fail-closed і можливість подальшого нормального update після явного завершення/скасування, без змін production key/channel.
5. Зберегти `Q03` release boundary, `PRIVATE_LOCAL`/FileVault/APFS/owner-only, no cloud ASR, explicit consent, AI default OFF, five specialist skills OFF, Health/phone OFF.

Мета — **конкретний fix у поточному M8F**, не нова voice-архітектура і не косметичний зелений тест.

## 3. Inputs, що треба прочитати

Перед змінами: actual `origin/main`, `STATE.md`, `HANDOFF.md`, `.project/project.json`, `AGENTS.md`, `docs/WORKFLOW.md`, this goal/contract/report та diff від останнього reviewed implementation SHA до HEAD.

За змістом: `prompts/M8F_MACOS_APP_INSTALLER_UPDATES.md`, `docs/M8F_CONTRACT.md`, `docs/adr/ADR-018-M8F-STANDALONE-MACOS.md`, `reports/M8F_MACOS_APP_REPORT.md`, `reports/evidence/M8F/{ACCEPTANCE_MATRIX.md,FIRST_RUN_FINDINGS.md,NATIVE_VOICE_GUARD_C11.json,NATIVE_VOICE.json,VALIDATION.json,INCIDENT_CONTAINMENT.json,LOCAL_UPDATE.json}`; `docs/M8F_BUILD_AND_DISTRIBUTION.md`, `docs/M8F_USER_GUIDE.md`, `docs/M8E_Q03_CONTRACT.md`, `docs/SAFETY.md`.

Релевантний код: `apps/macos/PersonalCompanion.swift`, `apps/web/src/{ComposerVoice.tsx,VoicePanel.tsx,pcm-recorder.ts,native-macos.ts}`, `apps/core/native_macos.py`, current voice storage/API/Whisper integration, `tests/test_m8f_{browser,native}.py`, `scripts/{build_m8f,verify_m8f}.py` та релевантні M4/M8F browser/voice tests. Не читай реальний vault/pilot, provider credentials або C8 incident raw content.

## 4. Execution boundaries і дослідні перевірки

- Спочатку відтворити `STARTING` **лише через LOCAL_TEST синтетичний канал**, зафіксувати **sanitized** state transitions/timestamps/exit codes та розділити hang у native fixture-enable, WKWebView `getUserMedia`, AudioContext, recorder lifecycle, UI callbacks, WebKit permissions або тестовій інфраструктурі. Не називати «бракує RAM» доведеним поясненням без вимірювань.
- Дозволені мінімально необхідні source fixes, перевірюваний bounded start/cancel/late-completion lifetime, стабільна UI-помилка/повторна спроба, narrow test harness correction. **Не прибирати тестову заборону фізичного мікрофона**, не давати WK `.grant` для реального пристрою, не створювати недостовірний «Recording» лише зміною стану, не підміняти Whisper fake-asr.
- Не змінювати глобальні timeout/deadlines чи asserts лише щоб приглушити flake. Якщо потрібен bounded wait, обґрунтувати його, зберегти можливість людині відповісти на macOS permission prompt у майбутньому, а пізній resolved stream обов'язково зупинити. Звичайні unit/browser fixtures не можуть підмінити **actual native GUI C-new end-to-end**.
- Виконати негативні сценарії: `getUserMedia` denies, promise never settles, cancel before approval/while starting, late stream after cancel, AudioContext failure, permission missing, interruption mid-recording, Save pending / Quit / attempted update, hidden producer, restart/retry, backend/ASR unavailable. Відокремити guaranteed durability після ack від memory-only/draft state; якщо система не має захисту певного незбереженого draft при Quit — чесно описати й не називати його durable.
- Позитивні сценарії: запуск із Finder, авторський PCM captured у WKWebView, реальний packaged Whisper, редагований transcript, explicit save/insert, потім persisted entry/message/audio verified after relaunch; не завантажувати і не надсилати тестовий текст на provider.
- Регресії: local update A→B підписаний **LOCAL_TEST**, previous backup/provenance/antirollback/guard, Free/Deep Q03, no negative API/UI leakage, existing owner-source profile, sandbox egress. Потрібні тести пропорційні diff; повний relevant Python/web/build/admission/qualification/docs/privacy, exact-C native end-to-end. За наявності транзитних C10 flakes чітко документувати команди/exit/rerun, не переписувати результати.

## 5. Безумовні hard stops

**Заборонено:** будь-яке реальне/несинтетичне захоплення мікрофона або аудіо, доступ до owner pilot/приватного vault/backup, читання чи відновлення інцидентного C8 root, SDK/provider inference або account calls, нові кредити/PAYG/auth/keys, доступ до чужого Mac, системні інсталяції, нові model/runtime downloads без окремого дозволу, activation clinical/Health/phone, зняття Q03 safety, production signing/Apple account/notarization/GitHub Releases/upload/hosting/deploy/tag, autostart чи production feed. GitHub `main` push у перевірених scope залишається дозволеним. Не додавати RAW, приватні audio/transcripts, test keys, absolute private paths у public Git.

Якщо неможливо гарантувати **фізично ізольовану synthetic recording fixture**, **не запускай GUI capture** і відзвітуй `BLOCKED_PHYSICAL_MIC_ISOLATION`, виконуючи незалежні unit/browser tasks. Якщо нативний GUI тест після обмеженої діагностики не завершено — `F09 NOT_VERIFIED/FIX_REQUIRED`, а не PASS. Не обходь macOS privacy permissions. Для runtime downloads/install/release потрібна нова явна owner authorization.

## 6. DoD і доставка

1. Пояснена й відтворена фактична причина або чесна `ROOT_CAUSE_NOT_VERIFIED` із конкретними доказами; coherent forward fix на базі C11/R, без приховування C8, C10 flakes.
2. Новий точний **C-forward** із реальним `LOCAL_TEST .app/.dmg`; bounded GUI start/cancel/retry; screenshot/state receipts без приватних media; **actual same-C native PCM→Whisper→edit→durable save**. Якщо немає actual GUI PASS — не закривати F09.
3. Negative evidence: нуль фізичного мікрофона, no raw audio provider/egress, blocked update while unsaved/STARTING/RECORDING/SAVING, cancellation late callback/no stale save, approved update remains working after settled state.
4. Звіт із відокремленими `PASS`, `NOT_RUN`, `FAIL`, `BLOCKED` для browser-only, packaged-ASR-only, current-native-GUI, старого C10 та normal macOS TCC/human ASR. Немає відновлення реальних записів/owner-пілота.
5. Повні релевантні exact-C тести (Python/web/build/Chromium, local app/Whisper/update, privacy/public-source/rights/admission/qualification), фіксація environment/exit/log hashes. Виправ звичайні engineering regressions автономно, але не обходь legitimate hard stop.
6. `docs/M8F_F01_CONTRACT.md` (або узгоджений forward addendum), `reports/M8F_F01_NATIVE_VOICE_REPORT.md`, оновлені `STATE.md`/`HANDOFF.md`/roadmap за реальним статусом, append-only devlog/ADR лише при значущій архітектурній зміні. Публічні evidence без RAW.
7. Визначена одна мета → implementation **C** → exact-C checks → evidence-only **R** → staged public/privacy scan → **normal fast-forward push прямо в main** → verify `origin/main==R` → STOP `AWAITING_REVIEW` для ChatGPT. Не вимагай review branch, ще одного routine push-дозволу, force-push або рекурсивного self-hash status commit. Якщо не вдалося виконати обов'язковий native gate — чіткий `BLOCKED_PARTIAL/FIX_REQUIRED` звіт замість імітації завершення.

**Немає дозволу на наступний milestone, production release або встановлення на Mac дівчини.** Engineering ACCEPT після рев’ю — окремо від release/data-owner/clinical review. Перевірити: *«Чи працює весь шлях нативного голосового запису на тому самому новому SHA, і чи не може незавершений запис загубитися або потрапити в оновлення?»*
