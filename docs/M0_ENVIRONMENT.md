# M0 — capability report

Перевірено 2026-09-30 у відкритому system repo (`cwd=repo/`). Результати — локальний
стенд, не доказ сумісності цільового Mac/Android. Dependencies не встановлювалися.

| Probe | Exit | Результат |
|---|---|---|
| `sw_vers` | 0 | macOS 27.0, build 26A428 |
| `uname -m` | 0 | arm64 |
| `git --version` | 0 | 2.50.1 (Apple Git-155) |
| `python3 --version` | 0 | 3.13.2 |
| `node --version` | 0 | v26.8.2 |
| `npm --version` | 0 | 11.19.1 |
| `sqlite3 --version` | 0 | 3.54.0, 64-bit |
| `codex --version` | 0 | codex-cli 0.159.0; PATH alias creation denied warning, command works |
| `codex app-server --help` | 0 | Installed CLI exposes app-server stdio and schema tooling; no server started |
| `sysctl -n hw.memsize` | 1 | `Operation not permitted`; actual RAM NOT_VERIFIED |
| Python `importlib.metadata.version` | 0 | Pydantic 2.12.5; SQLAlchemy 2.0.46 |
| Python dependency discovery | 0 | FastAPI, Uvicorn, pytest, Alembic NOT_INSTALLED in current Python |
| `git status --short --branch` до init | 128 | `fatal: not a git repository (or any of the parent directories): .git` |
| `git ls-remote https://github.com/hirchak/Personal-Companion.git` | 0 | Empty advertised refs; не доводить visibility чи право push |
| `gh repo view hirchak/Personal-Companion --json url,isPrivate,defaultBranchRef` | 1 | `error connecting to api.github.com`; visibility/default branch NOT_VERIFIED |

GitHub connector підтвердив public repo. Після першого push у новий порожній repo actual
default став `review/m0-bootstrap`; owner-intended target був `main`. У цій goal C3 створив
origin/main, потім `gh repo edit --default-branch main` повернув exit 0. `gh repo view` і
GitHub connector після цього підтвердили actual default `main`. Historical review ref
лишився незмінним.

## Codex capability та межі verification

Client tool metadata цієї сесії перелічує `gpt-6.1-sol`, зокрема effort `high`,
та `gpt-6-luna`. Це observed available client catalog, не перевірений live runtime
для акаунта власниці. Actual selected model/reasoning поточного чату — NOT_VERIFIED:
немає безпечного прямого getter у використаному інтерфейсі. Їх не перемикали.
Collaboration Mode=Default (execution, Plan Mode OFF) наданий client context.

OpenAI Docs використано лише для read-only звірки CLI surface:
[official developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
Наявність command/schema/catalog не доводить subscription entitlement, runtime
retention, quota, billing route або sandbox isolation. `codex exec`, model inference,
login/auth probes та private backend calls — NOT_RUN. MiniMax — NOT_VERIFIED/OFF.
Не читались auth.json, токени, особистий config, журнали чатів або home inventory.

## Готовність до M1

Python/Node/Git/SQLite і stdlib unittest придатні для M0 tooling. Python/Node versions
самі по собі не доводять сумісність FastAPI/Vite: M1 має обрати й локально перевірити
dependency versions/lockfiles. Встановлені глобальні Python packages не dependency
contract. Пакет застосунку, venv, package.json і lockfiles — ще відсутні навмисно.

Референс Mac M2/16 GB та Galaxy S24 Ultra походить зі специфікації: hardware/browser,
FileVault, wearable, Android HTTPS, at-rest encryption та install acceptance —
HARDWARE_UNVERIFIED/NOT_RUN. Їх не підтверджує arm64 локального dev-стенда.
Managed workspace-write і локальні Git exceptions не є доведеним runtime sandbox.
Відсутні dependencies та пізні hardware gates не блокують завершення M0.
