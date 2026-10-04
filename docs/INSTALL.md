# M8C: локальне встановлення; synthetic compatibility і private core

Це prerequisite-based unsigned source package, не standalone installer і не дозвіл на реальний пілот.
Поточні assumptions: macOS/Darwin arm64, Python3.13 із **точними runtime versions** `requirements.runtime.lock`.
Для build також потрібні наявні Node/npm і project-local `apps/web/node_modules`. Нічого не встановлюється.
M8B не запускає pip/npm ci, Homebrew, trust setup чи system changes. Відсутній prerequisite → INCOMPATIBLE;
його встановлення потребувало б окремої цілі. Після build Node/npm/Git не потрібні для startup.

З чистого точного checkout, із наявним project Python:

```bash
mkdir -p generated/releases
.venv/bin/python -m apps.core.release prepare --output "generated/releases/M8C-$(git rev-parse HEAD)"
```

Ідентичність нового build — `M8C-<full Git SHA>`, а не latest. Manifest у `release-manifest.json` містить exact commit,
schema11, окремі runtime/dev Python lock identities і web lock, contract/defaults і hashes усіх package files. Output ignored; не комітити
runtime roots/backups/архіви. Expected `manifest_hash` візьміть з довіреного результату build/evidence,
передавайте окремо; hash не є цифровим підписом чи notarization.

Приклад із **новими синтетичними** paths поза Git (замініть placeholders; spaces/Unicode підтримуються):

```bash
.venv/bin/python -m apps.core.release preflight --package "$PACKAGE" --manifest-hash "$EXPECTED_HASH" --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT"
.venv/bin/python -m apps.core.release install --package "$PACKAGE" --manifest-hash "$EXPECTED_HASH" --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT"
.venv/bin/python -m apps.core.release start --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT" --port 8765
```

App/data roots повинні бути різними без вкладення один в одного; parents уже існують, roots для install нові.
App root: installation.json / active.json / releases/M8B-SHA. Data: accepted synthetic marker + local SQLite/audio.
Для запуску без checkout: той самий схвалений Python із dependencies + `python /path/to/package/launch.py start`
з app/data arguments. Package source не потребує Git. Не переносіть `.venv` як самодостатній runtime.

Сервер foreground на 127.0.0.1, egress тільки loopback; frontend/fonts/assets локальні. Немає provider process,
cloud sync/telemetry/fallback/download. Розблокування — одноразовий локальний код в операторському terminal;
не копіюйте його в evidence/logs. **Stop: Ctrl+C**; повторіть start для restart/new code. Немає daemon/autostart.
Файл `.m8a-lock` біля root не містить credentials; OS lock звільняється після exit, inode лишається.

ProviderOFF, clinical0, specialistsOFF, health-to-AIOFF, cloudASRNONE, embeddingsOFF. У пакеті немає ASR assets:
LOCAL OPTIONAL_UNAVAILABLE, голос можна зберігати/видаляти вручну; не представляйте FAKE як real ASR.
Phone/private HTTPS/Health optional недоступні в цьому launcher; це не перешкоджає journal/creative.
Якщо збережений job був перерваний, startup позначить його FAILED, не відновить provider inference автоматично.

Суміжні операції: [upgrade/rollback](UPGRADE.md), [recovery + M8B gates](RECOVERY.md), [remove](UNINSTALL.md).
`CLEAN_SYNTHETIC_ROOT` не є clean physical Mac acceptance.


M8B manifest format2/runtime lock містить12 pinned runtime packages. `requirements.lock` залишається повним
build/test input (pytest/Playwright/httpx тощо); вони не потрібні для startup нового пакета. Old M8A format1
зберігає історичний full-lock prerequisite contract, не перетлумачений заднім числом.
Sanitized actual-Mac preflight: `python -m apps.core.release mac-preflight` із тими самими package/hash/app/data/port
arguments. Факти обмежені поточним Mac, не всіма Macs. [Pilot handoff](PILOT_HANDOFF.md) пояснює окремий
private-root runtime gate: M8B synthetic launcher не активує private mode; M8C private gate описано нижче.

## Current PRIVATE_LOCAL release

New builds use **M8C-<exact C> / manifest format3**, retaining the format1/2 synthetic compatibility above.
Use `generated/releases/M8C-<exact C>` as the clean-checkout prepare output; same existing runtime-only prerequisites.
PRIVATE_LOCAL is a separate root/SQLite/install classification, not SYNTHETIC_M1 marker replacement. `install` remains
synthetic-only; private activation is separately named `initialize-private` and requires exact root/data-owner intent.
`start --mode PRIVATE_LOCAL` never creates a vault. Wrong kinds/corrupt markers/permissions/encryption fail closed.
Canonical **post-ACCEPT-only** preflight/empty-root consent/start/first-entry commands: [PILOT_HANDOFF](PILOT_HANDOFF.md).
M8C may test them only on disposable roots with ORIGINAL SYNTHETIC content; actual private root NOT_CREATED.
Current private profile binds MAC_PRIVATE_CORE_PROFILE.json and is enforced by API/factory/runtime, not a toggle.
[ADR-013](adr/ADR-013-M8C-PRIVATE-LOCAL-CORE.md) specifies verified FileVault APFS + owner-only0700/0600/no ACL;
no application-level database/archive encryption, no downloads or OS settings changes. Package assets all local.
