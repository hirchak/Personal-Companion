# M1 — локальний synthetic щоденник

Дата: 2026-10-01 (Europe/Warsaw). Implementation/review: **AWAITING_REVIEW**.
M1 готовий для незалежного engineering review. Це development candidate, не accepted
release, private rollout або клінічне затвердження. M0 ACCEPT походить із зовнішнього ТЗ.

| Ref/status | Значення |
|---|---|
| Repository / branch | `hirchak/Personal-Companion`, `main` |
| Base M1 | `175fc934ad16552759273d2ed6770835b6f28786` |
| Implementation C | `fd056cc4e91b826a032a871381dbf3a64180bd44` |
| Evidence R2 | Наступний evidence-only commit; exact SHA повертається у final handoff без self-hash |
| Correction base / origin before correction push | `56a29e8912b39bdb20687a4f8b6bf23824956607` (попередній R1) |
| Push у цьому R | PRE_PUSH: C/R2 готові до дозволеного normal fast-forward; remote receipt — final handoff |
| CI | NOT_RUN; нових workflows/runners/secrets не створено |
| Permissions | push_main=true; merge/deploy/provider/private-data=false |
| M2+ | NOT_STARTED, не дозволені |

## Реалізація й користувацький результат

Python/FastAPI/Pydantic, SQLite WAL та один Journal service для HTTP/maintenance;
React/TypeScript/Vite same-origin build. Український нейтральний UI: додати через «+»,
inbox/daily/sleep/creative, optional fields, chronological list, literal search, type/tag/date
filters, edit/type-change confirmation, paginated history, delete, selected preview/export.
Labels/focus/keyboard, desktop/mobile layouts; errors/conflicts лишають чернетку для повтору.
Немає AI/chat/mic/watch controls, зовнішніх fonts/images/analytics або browser persistence.

Ревізія містить `recorded_at_utc` в immutable JSON, атомарно з edit; для попередньої
synthetic development history timestamp невідомий і повертається null без вигадування.
Save повертає MAC_SAVED лише після commit. Ідемпотентність і revision checks — одна
transaction із entry/history/index/receipt. Delete purge current/history/index і write
fingerprints; мінімальна operation metadata та tombstone зберігаються проти replay.
Після tombstone старі create/edit дають 410, повтор delete не відновлює текст.

Nullable ratings відрізняють unknown і zero. Offset-aware timestamps нормалізуються в UTC;
IANA zone й event local_date зберігаються явно. Sleep wake визначає event time/date, коли
відомий; інтервал названий оцінкою користувача, не фактичним TST або health metric.

Loopback 127.0.0.1; exact Host/Origin, bounded JSON/body/query, no wildcard CORS.
One-time unlock code 5 min/5 attempts per minute; HttpOnly host-only SameSite=Strict session,
idle 15 min/absolute 8 h, CSRF, revoke/restart. Static navigation може не мати Origin;
private API все одно потребує session, writes/exports — exact Origin та CSRF.
No-store/CSP й neutral error bodies, без request payload/SQL/path echo. Access logging OFF.
Auto-lock unmounts UI text, draft, history, export state; новий код отримується restart.

Explicit SYNTHETIC root поза Git; unknown root/git worktree/symlink/escape refused;
0700 directories, 0600 storage files. Transactional v0→v1 synthetic migration fixture,
consistent pre-upgrade snapshot, rollback, no-op restart, newer schema refusal.
Backup uses SQLite backup API against live WAL, completes atomically with manifest/checksum;
no sessions/auth. Restore validates files, schema, logical domain and SQLite integrity before
new-root activation; metadata UUID/owner/epoch/UTC fields and revision references are validated; restore_epoch increments and reconciliation flag is required.
JSON lossless selected current/history export, Markdown escaped readable text; stale/deleted/
expired/session-mismatched preview refused. No import/merge HTTP endpoint.

Контракт v4 має явний change note дозволених engineering уточнень. Trust boundary не змінено;
архітектурного відхилення немає, ADR не потрібний. Hardware metadata оновлено до Galaxy Watch7,
versions/fields/compatibility NOT_VERIFIED. R01/R02/R03 лише metadata received externally,
unreviewed/not ingested; raw DOCX не відкривалися. Design backlog — знеособлений і deferred.

## Перевірки та gates

[Exact C checks](evidence/M1/EXACT_FINAL_C_CHECKS.json) — чистий detached local clone exact C,
без читання сторонніх даних. Pinned project dependency tree reused explicitly; source checkout
і tracked files не змінювались. Build та **104 тести PASS**, exit 0, Python 3.13.2,
Node 26.8.2, npm 11.19.1, Darwin 27.0.0/arm64, SQLite 3.45.3, Chromium 140.0.7339.16.
Відомий non-failing warning: Starlette TestClient/AnyIO deprecated BlockingPortal alias.
[Pre-C checks](evidence/M1/AUDIT_PRE_C3_CHECKS.json) — окремий чесно позначений worktree run.
Commands/time/duration/environment/exit/output збережені в records, не лише hash manifest.

| Gate | Конкретний доказ | Результат |
|---|---|---|
| M1-A01 | `test_A01_crud_history_purge` ×4, `test_A01_type_change_explicit`, immutable recorded_at_utc/read schemas, API/browser CRUD | PASS |
| M1-A02 | commit retry/restart, abrupt subprocess exit 17 with uncommitted transaction, failed edit/delete rollback, parametrized disk-full/read-only/I/O API, browser draft retry | PASS |
| M1-A03 | receipt reuse/payload conflict/tombstone, concurrent duplicate/stale writes, new-operation repeated delete and global reuse denial; browser second writer | PASS |
| M1-A04 | Unicode/emoji, null/zero, invalid Unicode scalar/patch rejection, strict fields/limits, offset/DST/midnight/IANA, event edits та зміна системного TZ, user-estimated interval | PASS |
| M1-A05 | live-WAL snapshot→restore, checksum/version/attachments/missing/partial/nonempty/DB integrity/logical payload and metadata/owner/epoch/UTC and revision-reference rejection | PASS, attachments themselves absent in M1 |
| M1-A06 | root isolation/0700/0600, repo/worktree/symlink/escape/unknown denied, injected migration rollback/preupgrade snapshot/newer refusal | PASS |
| M1-A07 | API auth/Host/Origin/CSRF/expiry/revoke/cookies/owner/limits/errors; malformed PATCH enum and NaN/Infinity→422; real browser cross-origin denial | PASS |
| M1-A08 | selected lossless JSON validator round-trip, Markdown escape, exact preview/session/expiry/change/delete invalidation | PASS |
| M1-A09 | real React/HTTP/SQLite browser create/edit/search/history/type-change/export/restart/delete/failure/conflict/manual+idle lock; keyboard Tab/Enter/Space, actual demo launcher; inert script, no browser storage, no unexpected JS errors; desktop/mobile | PASS |
| M1-A10 | [staged/Git/generated privacy](evidence/M1/FINAL_R2_PRIVACY.json), [artifact review](evidence/M1/FINAL_C_ARTIFACT_REVIEW.json); separate TCP/UDP/sendmsg/alternative DNS deny-egress and browser external abort negative tests | PASS in stated synthetic/local scope |

Actual files: [domain tests](../tests/test_m1_domain.py), [API/security tests](../tests/test_m1_api.py),
[browser test](../tests/test_m1_browser.py), [OpenAPI](../packages/contracts/openapi.json),
[generated TS contract](../apps/web/src/api-schema.ts). Schema fixture is compared to actual app; read/history/receipt output models are shared with TS.
[Documented setup check](evidence/M1/SETUP_CHECK.json) та `test_A09_documented_demo_start_unlock_restart_stop`
підтверджують саме setup/demo scripts, seeded sections, committed save, restart/no reseed та stop.
[Desktop](evidence/M1/ui/desktop.png), [mobile](evidence/M1/ui/mobile.png) — viewed synthetic
viewport only; no desktop/terminal/unlock codes/private paths. No DB/ZIP/video/auth state in Git.

Runtime deny-egress test is independent of privacy regex scanning: process-local socket audit
rejects non-loopback connect/datagram/sendmsg/DNS, then local SQLite save/search still works. Browser session
blocks external requests, with one deliberate negative attempt. Host OS firewall unchanged.
This does not establish an OS sandbox against arbitrary malicious same-user code.

Agent-browser also verified the real launcher shell (page, labels, no error overlay/errors),
then closed; the test server was stopped. Impeccable mechanical detector returned no findings
on the implemented surface; subsequent changes stabilized labels/localized enum display and
formatted source. React review: clean effect listeners, no persistent browser payload/cache,
in-flight responses cannot remount locked journal, stale search responses are discarded.
Completion audit caught missing recording time, missing system-TZ test and narrow socket coverage
in the first candidate C1 `6695ffd64d56f935ec41a2d11df5cad7fbfa8106` / R1
`56a29e8912b39bdb20687a4f8b6bf23824956607`. C2 fixes recording/read-contract/TZ/network coverage; C3 additionally rejects malformed backup
metadata/owner relations, forbids wildcard socket binds, and fixes malformed PATCH enum errors;
C4 receipts every new delete operation after tombstone, preventing action/ID reuse.
C5 gives non-ASCII auth/CSRF proper 401/403 and rejects malformed Unicode text/tags with 422;
the original C1/R1 and intermediate exact-C evidence is preserved. No R+1 attestation-only change/history rewrite.
[Completion audit](evidence/M1/COMPLETION_AUDIT.json) maps every goal section to current evidence.

Npm audit after Vite patch 6.4.3: zero findings; lockfiles pinned. No global dependencies.

## Вимірювання

[Performance](evidence/M1/FINAL_C_PERFORMANCE.json): exact C, N=200 synthetic entries; 200 committed
saves, 30 literal searches(limit=100), same-process reopen, 0.5s idle CPU sample, own-process
RSS via ps. Actual values are in the linked JSON; this is a bounded repository/service
measurement, not HTTP startup SLO, target M2/16GB benchmark or long stress run. No SLO claimed.

## M0 correction

[M0 architect decision](M0_ARCHITECT_REVIEW.md) зберігає зовнішній ACCEPT C3 й limitations.
Missing C3_CHECKS.json pointer замінено [exact final C rerun](evidence/M0/C3_RERUN_2026-10-01.json),
25 tooling tests/docs/privacy source checks exit 0. Git archive has no local Git-object scan;
цей scope чесно записаний. R5 publication звірено на старті M1. Historical R5 PENDING поля
збережені як попередній evidence, superseded поточним рішенням/report, не підроблені заднім числом.

## Запуск і відновлення

З repository root:

```bash
./scripts/setup_demo.sh
./scripts/demo.sh /private/tmp/personal-companion-m1-synthetic-demo
```

Open `http://127.0.0.1:8765`, unlock одноразовим кодом із термінала, stop Ctrl+C.
Побачите чотири вигадані українські записи й всі M1 journal actions. Repeat start preserves
synthetic data and issues a fresh code. Unknown existing root refuses startup; no reseeding.
Після lock/reload unsaved draft втрачається; при звичайній save failure лишається в unlocked UI.
[Installation/maintenance runbook](../docs/INSTALLATION.md) має backup/restore commands.

## Межі handoff

Немає відкритих implementation blockers у M1 gates. Independent architect review pending.
AI/provider calls, deploy, new CI, real/private data, phone/PWA/sync, health/watch, ASR,
clinical modules, gameplay, autostart, release/tag і M2+ OFF/NOT_RUN. Encryption/key recovery,
FileVault, actual hardware/wake/clean installer/private rollout acceptance NOT_RUN.
Deleted bytes можуть залишатися в SQLite free pages/WAL, exports, old backups/OS snapshots;
forensic erase не обіцяється. License/clinical/content/device gates залишаються окремими.
Після normal C/R push executor зупиняється до незалежного review/нової owner goal.
