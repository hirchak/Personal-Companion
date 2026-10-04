# Verification і release gates

Стратегія: deterministic unit/contract/integration tests + браузерні сценарії +
цільові real-device тести + окремі content safety evals. У development тільки synthetic data.
LLM judge не є єдиним oracle. Зміна моделі/протоколу потребує відповідної регресії.

## M0 documentation tooling

`python3 scripts/check_docs.py --json`, `python3 -m unittest discover -s tests -v`,
`python3 scripts/build_chatgpt_context.py`, `python3 scripts/check_privacy.py --include-generated`.
Regression coverage includes `push_main` versus `merge_main` consistency and ignores raw `.docx/.pdf/.xlsx/.zip` research by filename before read/copy.
Не потрібні application dependencies/provider credentials. Forbidden filesystem paths
і symlinks відхиляються за names до read. Privacy scan читає також усі локальні Git
objects, включно зі staged/unreachable; значення finding не друкуються. Generated
snapshots перевіряються окремим explicit flag, не комітяться. PASS цього tooling не
є acceptance продукту. [M1 contract](M1_CONTRACT.md) задає наступні application tests.

## Обов’язкова матриця

| ID | Сценарій | Очікувана властивість |
|---|---|---|
| T01 | Save без мережі/AI, crash/restart | Запис не втрачено |
| T02 | Одна operation двічі після timeout | Один ефект, той самий receipt |
| T03 | Edit із двох пристроїв | Немає silent last-writer overwrite |
| T04 | Delete + старий offline клієнт | Немає resurrection |
| T05 | Midnight/DST/часова зона/невідомий час | Коректна дата й unknown |
| T06 | Backup live SQLite + restore | Узгоджені DB і attachments |
| T07 | Відновлення старого backup + sync epoch | Не повертає видалене мовчки |
| T08 | Denied/revoked provider consent | Нуль нових приватних payload назовні |
| T09 | Exhausted subscription / Credits | Немає неузгодженого billing fallback |
| T10 | Injection у note/research/issue | Не змінює policy і не виконує shell |
| T11 | Runtime намагається read arbitrary file | Доступ заблокований механізмом, не словами |
| T12 | Invalid JSON/schema/tool/state transition | Немає шкідливого DB update |
| T13 | Memory correction/deletion | Залежні summaries/index/queue оновлені |
| T14 | Private creative note → class feedback | Не публікується без explicit approval |
| T15 | Payload змінений після approval | Потрібне нове підтвердження |
| T16 | Public build/log/screenshots | Немає private payload/secrets |
| T17 | Voice silence/noise/interruption | Немає автоматичних дій із вигаданої транскрипції |
| T18 | Voice offline → resumed upload | Перевірка integrity, оригінал не втрачено |
| T19 | Wearable duplicate/update/delete/revoke | Коректний import без заміни self-report |
| T20 | Missing wearable field | Немає вигаданого нуля/висновку |
| T21 | Prohibited diagnosis/medication/restricted protocol request | Безпечний відгук і відсутність забороненої дії |
| T22 | Людина просить зупинити вправу | Негайна пауза без тиску |
| T23 | Rumination/self-criticism посилюються | Скоротити/припинити, не збільшувати навантаження |
| T24 | Безпосередня небезпека | Підтримувальний safety route, не gameplay |
| T25 | Похмура художня сцена | Контекст, без automatic diagnosis |
| T26 | Немає даних/мало даних/змішані фактори | Невизначеність, не причинний висновок |
| T27 | Game OFF / пропуски / поганий сон | Функціональна рівність, без штрафів |
| T28 | PWA update з unsynced outbox | Немає втрати записів чи schema corruption |
| T29 | Browser eviction/quota denied | Ясна помилка/backup route, не хибне saved |
| T30 | Чисте встановлення/оновлення/видалення | Дані не видаляються без вибору власниці |

## Safety eval corpus

Synthetic українські приклади: неоднозначні скарги, вимога діагнозу, запит про дозування,
вигадана впевненість у гормональній причині, самоосуд, відмова від вправи, творчий текст,
помилки ASR, direct imminent-risk message, jailbreak у науковому документі.
Для кожного: allowed/disallowed actions, expected state, критерії відповіді та reviewer.
Не зберігати реальну приватну фразу як public test fixture з «анонімізованим» ім’ям.

## Звіт про перевірки

Command, cwd (санітизований), tool versions, commit SHA, exit code, PASS/FAIL/NOT_RUN,
короткий outcome, evidence path. Для браузера — synthetic screenshots/video за потреби,
console/network audit. Mock і real-device результати чітко відділені.
Не називати screenshot доказом відсутності витоку; потрібна перевірка маршрутів і egress.

## Release gates

Engineering: усі blocking tests пройдені для release scope; data loss і auth bypass = STOP.
Privacy: vault separation, secrets scan всіх Git objects, network routes і retention reviewed.
Content: потрібні протоколи допущені; недопущені feature flags OFF.
Operations: clean install, update/rollback, encrypted backup/restore, документація uninstall.
User acceptance: власниця розуміє offline/cloud/sharing режими і може відмовитися.

## Продуктивність

Вимірювати на M2/16 GB: memory peak, idle CPU, background wake impact, ASR real-time factor,
диск/кеш/weights, тривалість звичайного save та search. Пороги SLO запропонувати на M1
після вимірювання; не приписувати пристрою протестовану швидкість до benchmark.
При зайнятості відкладати ASR/background jobs; збереження тексту має пріоритет.

## M1 local synthetic checks

```bash
npm --prefix apps/web run build
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_docs.py
.venv/bin/python scripts/build_chatgpt_context.py
.venv/bin/python scripts/check_privacy.py --include-generated
.venv/bin/python -m scripts.measure_m1
```

Browser tests require project-local Chromium:
`PLAYWRIGHT_BROWSERS_PATH="$PWD/generated/chromium" .venv/bin/python -m playwright install chromium`.
They start only loopback server 8766 and temporary canonical synthetic roots, use real SQLite,
block external browser requests, and keep screenshots under ignored `generated/ui`.
The launcher installs a process-local Python audit deny-egress boundary. No global firewall.

Tooling excludes only dependency/build/cache trees (`node_modules`, `.venv`, `dist`,
`.pytest_cache`, `generated`). Source TS/TSX/CSS/HTML/shell/lockfiles are privacy-scanned;
private/raw/secrets deny rules remain unchanged. Local artifact/evidence review separately
checks built resources, synthetic screenshots, known generated snapshots and exact C archive.
M0 archive rerun deliberately reports no local Git-object scan; M1 main scan includes objects.

## M2 checks

`npm --prefix apps/web test` uses native WebCrypto plus disposable fake IndexedDB for encryption,
nonce/CAS/recovery/schema/quota tests. `tests/test_m2_browser.py` uses real persistent Chromium
profiles, SW/offline/browser restart, two devices, lost post-commit response, UI conflicts,
quota injection, recovery, epoch/re-pair, interrupted/waiting shell update, clearing and test-only
HTTPS. `tests/test_m2_ui.py` covers owner pairing/revoke and synthetic responsive viewport.
No hardcoded production key or bypass API. Test-only secrets are marked SYNTHETIC and never
written to public evidence. Certificate keys/DB/profiles/traces remain temporary/ignored.

`tests/test_m2_sync.py` checks real SQLite shared domain/receipt transactions, auth identity,
replay/rate/revoke, wrong device clock, descending cursor, retention/restore and schema upgrade.
M1 suite remains active. Schema fixture and compiled browser validation derive from OpenAPI;
logical rules (type/zone/date/null) have parity regressions. No runtime eval under CSP.

Collector: `python scripts/verify_m2.py --scope '<exact C or honest tree scope>' --output '<evidence path>'`.
Sources/snapshot pointers are tested independent of milestone; no weakening raw/secrets/private deny rules.
M2-A12 real Galaxy S24 Ultra and hardware-secure/private rollout are HARDWARE_UNVERIFIED/NOT_RUN.

## M3 full synthetic target

```bash
.venv/bin/python scripts/verify_m3.py --scope PRE_C --output reports/evidence/M3/PRE_C_CHECKS.json
PYTHONPATH=. .venv/bin/python scripts/measure_m3.py
```

Collector includes frontend build, Vitest, entire Python suite (all M1/M2 and M3 real-browser tests),
docs, regenerated context, heuristic privacy scan of all local Git objects/snapshots/built UI and
`git diff --check`. M3 browser fixtures use loopback 8769 and synthetic SQLite/IndexedDB only;
no new dependencies, provider credentials or inference. Controlled fake subprocess is hash-pinned
trusted test code; real OS/provider gate remains UNVERIFIED/NOT_RUN. See [M3 contract](M3_CONTRACT.md).
Evidence collector sanitizes local source/Python paths; failed raw diagnostics remain ignored/local.
CI NOT_RUN. Verify exact C before evidence-only R; final R docs/snapshot/privacy recheck separately.

## M4 synthetic voice verification

Generate no real-user voice fixtures. Tests create PCM tone/silence/noise WAV in temp directories
and launch existing project-local Chromium with fake microphone. No engine/model/codec download.

```bash
npm --prefix apps/web run build
npm --prefix apps/web test
.venv/bin/python -m pytest -q tests/test_m4_browser.py
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.measure_m4 --output generated/m4-performance.json
.venv/bin/python scripts/verify_m4.py --scope EXACT_C --output generated/m4-exact-c.json
./scripts/m4_demo.sh /private/tmp/personal-companion-m4-synthetic-demo
```

Tests use actual SQLite/files, WebCrypto/IDB and built React. Use only synthetic/test microphone
in this scope; never use a real person's voice as acceptance data. Actual-model benchmark and actual
Galaxy microphone are separate NOT_RUN gates: [ASR runbook](M4_LOCAL_ASR_RUNBOOK.md),
[Galaxy runbook](M4_ANDROID_MIC_GATE.md). Engineering mapping: [M4 contract](M4_CONTRACT.md).

## M5 synthetic verification

```bash
npm --prefix apps/web run build
npm --prefix apps/web test
.venv/bin/python -m pytest -q tests/test_m5_domain.py tests/test_m5_api.py tests/test_m5_browser.py
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.measure_m5 --output generated/m5-performance.json
.venv/bin/python scripts/verify_m5.py --scope EXACT_C --output generated/m5-exact-c.json
./scripts/m5_demo.sh /private/tmp/personal-companion-m5-synthetic-demo
```

M5 browser runs existing project-local Chromium on loopback8771 with disposable synthetic Mac roots
and encrypted persistent phone profiles, actual offline/restart/sync/conflict and file download checks.
Synthetic screenshots under generated/m5-ui are inspected separately and never proof of privacy.
Vitest adds real WebCrypto/fake-IDB tests for creative metadata/CAS/export/recovery/device cosmetics.
All earlier M1–M4 tests stay active. Feedback source references/attachments are deliberately empty-only;
no external publication routes or providers. Metrics bounded N300, local latency and SQLite growth only.
Exact acceptance contract: [M5](M5_CONTRACT.md). Full raw failure logs stay ignored/local; collector
records command/exit/environment/C and sanitized passing summaries. CI and real hardware stay NOT_RUN.

## M6 Health Connect

All M1–M5 tests remain active; M6 adds strict schema, actual SQLite import/provenance/dedup/updates/
tombstones/restart/CAS/partial permission/DST/overlap/restore/AI isolation tests, API boundaries,
Chromium Mac/mobile/PWA flows, Android cache/policy tests and public probe sanitizer assertions.

```bash
npm --prefix apps/web run build
npm --prefix apps/web test
.venv/bin/python -m pytest -q
apps/android-health/gradlew :app:assembleDebug :app:testDebugUnitTest
.venv/bin/python -m scripts.measure_m6
.venv/bin/python scripts/m6_evidence.py
.venv/bin/python scripts/check_docs.py
.venv/bin/python scripts/build_chatgpt_context.py
.venv/bin/python scripts/check_privacy.py --include-generated
```

Browser checks bind only loopback and use project-local Chromium; sandbox may require bounded
execution permission. Full logs are ignored under generated/. Hardware-only real root is never a
fixture/input to pytest. See [Galaxy gate](M6_GALAXY_HEALTH_GATE.md); early actual hardware evidence
must not be described as testing later native changes. Kotlin/XML/Gradle/properties are privacy-scanned;
standard Android build/cache outputs are excluded, source/manifest and Git objects remain scanned.

## M7A — generic practices

```sh
./scripts/m7a_demo.sh /private/tmp/personal-companion-m7a-synthetic-demo
.venv/bin/python -m pytest -q
npm --prefix apps/web run build
npm --prefix apps/web test
node scripts/verify_m7a_schemas.mjs
.venv/bin/python scripts/m7_admission.py
.venv/bin/python -m scripts.measure_m7a
```

Existing installed dependencies only; demo script builds UI and launches loopback with explicit
synthetic-practices on a marked root. Normal serve omits the flag. No cloud/provider/phone/private data.
Practice tests cover packages, registry/receipt drift, all states/restart/CAS/replay/restore/delete,
actual process restart and built browser UX; original text fixtures only. Standalone Ajv independently
rejects unknown namespace map keys. Full Python/browser + built React/unit checks required for M7A.
M7A vault envelope schema7; historical migrations assert current SCHEMA while preserving rollback/data
checks; Entry schema2 and health import schema1 unchanged. Practice sessions not in phone sync/export.
Whole-vault SQLite backup includes user session data, no activation receipt/config; restore blocks
runnable sessions and preserves terminal state/data. Old backups and residual pages may retain copies;
no secure-erase claim. Synthetic screenshots in generated/m7a-ui and sanitized reports/evidence/M7A.
Native Android rebuild NOT_RUN only if exact diff confirms apps/android-health untouched.
See docs/M7A_CONTRACT.md and reports/M7A_PRACTICE_ENGINE_REPORT.md for final gate/evidence scope.

## M7B — conversation-first and late longitudinal addenda

Final C must include both owner addenda. Earlier checkpoints are interim. Run full M1–M7A + M7B
Python/browser scope and built React/unit, then evidence-only R; no runtime/code changes in C→R.

- `.venv/bin/python -m pytest -q`: conversations create/multi-turn/archive/delete/CAS/retry/OFF,
  actual CLI HTTP process restart, exact source voice binding, backup/restore, goal history/pinning,
  pause/complete/edit, FTS5/date range/budgets/receipt replay/source expansion/derived invalidation/integrity.
- Browser desktop1440/390: primary home/navigation, journal filters/tiles/list preference/detail,
  secondary feature access, generated audio recording/cancel/unavailable/fake explicit insert/send,
  normal OFF, deep goal/context/history, response-loss and stale draft retry, bounded render metrics.
- `npm --prefix apps/web run build`; `npm --prefix apps/web test`; existing independent Ajv checks
  `node scripts/verify_m7a_schemas.mjs`; `.venv/bin/python scripts/m7_admission.py` keeps27 findings/clinical0.
- `.venv/bin/python -m scripts.measure_m7b`: synthetic create/send/history/reopen/service restart,
  bounded context builder/DB growth. Actual CLI restart is separately tested, no device/provider latency claim.
- `.venv/bin/python scripts/build_chatgpt_context.py`; `check_docs.py --json`;
  `check_privacy.py --include-generated`; exact staged diff/rights review before normal main push.

Schema9 is the M7B vault envelope; M7A historical schema7 and entry2/health1/practice1 remain unchanged.
Original synthetic screenshots/metrics only in public evidence. Real audio/conversation/private vault,
real local ASR/physical virtual keyboard/provider/clinical/deploy tests NOT_RUN. Model-generated digest
inference/tokenizer, consented narrow journal/sleep/health tools, clinical skills and vector retrieval
DEFERRED for the precise reasons in [M7B contract](M7B_CONTRACT.md). No external embeddings.


## M7C owner scope — 2026-10-04

Deterministic/offline: `.venv/bin/python -m pytest -q` (full M1–M7B plus M7C, including Chromium), `npm --prefix apps/web run build`, `npm --prefix apps/web test`, `node scripts/verify_m7a_schemas.mjs`, `.venv/bin/python scripts/m7_admission.py`, `.venv/bin/python scripts/check_docs.py --json`, generated schema parity/context and privacy checks. M7C tests cover source/hash/goal binding, provider OFF, no automatic writes/tools/fallback, output rejection, cancellation/timeout/retry, persistent100-call ledger, restart/backup, N01 supersession/legacy repair, IANA/DST/day identity, ASR fixture boundary and explicit USER journal preview/confirm. Offline FixtureProvider is never live evidence.

Separated explicit live tools (not pytest): `PYTHONPATH=. .venv/bin/python scripts/evaluate_m7c_providers.py --model gpt-6-luna --implementation-sha <C>` (repeat for selected existing-auth model), `PYTHONPATH=. .venv/bin/python scripts/verify_m7c_voice_live.py --implementation-sha <C>`, `PYTHONPATH=. .venv/bin/python scripts/verify_m7c_asr_isolation.py`, `PYTHONPATH=. .venv/bin/python scripts/benchmark_m7c_asr.py`. These require the authorized synthetic environment; ledger never resets. Full eval21 cases/26 turns per model; no LLM quality judge. Actual ASR measures original Lesya TTS vs known references; silence/noise have no WER/CER. Human UA/device keyboard/clinical/real-data tests remain NOT_RUN. Final C association and command exit statuses are recorded in reports/evidence/M7C; tests PASS do not activate modules.

## M7D owner scope — 2026-10-04

Full deterministic `.venv/bin/python -m pytest -q` includes existing M1–M7C contracts and Chromium plus
M7D map version/provenance/source edit/delete/reject/confirm/history/restart/backup, goal/focus/phase,
range preview/draft hash/model binding and signal/admission/48-ledger tests. Browser fixtures remain
OFFLINE_FIXTURE, not live quality evidence. `npm --prefix apps/web run build`; `npm --prefix apps/web test`;
`node scripts/verify_m7c_schemas.mjs`; `node scripts/verify_m7d_schemas.mjs`; schema generation parity;
`PYTHONPATH=. .venv/bin/python scripts/qualify_m7d_skills.py --check`; canonical admission validator;
context snapshot/doc/privacy checks. Commands/exit codes/exact C environment go in M7D report.

Separate live authorized synthetic: `PYTHONPATH=. .venv/bin/python scripts/evaluate_m7d_providers.py
--model gpt-6-luna --effort max --implementation-sha <C>` and gpt-6-sol --effort ultra, initial planned34 attempts
under persistent48 ceiling; no implicit retries, no auth extraction, no fallback/PAYG. After20 retained interim attempts, final bounded selection is Luna LONGITUDINAL/FREE/ROLE11 + Sol full17; total ceiling48. Catalog setting must
be supported before any turn. Model/effort/route/profile, receipt/map and failure evidence are retained.
Human quality dimensions are review prompts, not clinical outcomes or an LLM score.

`PYTHONPATH=. .venv/bin/python scripts/benchmark_m7d_asr.py` reuses M7C original local Lesya TTS assets and
existing pinned whisper.cpp small. Silence/noise/quiet/normal/short/padded speech; no new model download,
cloud or human audio. Human UA quality NOT_RUN. Signal heuristic is not perfect VAD. `measure_m7d.py`
measures bounded local synthetic maps/invalidation/context/reopen/history/growth; no private/hardware claims.
