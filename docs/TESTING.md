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
