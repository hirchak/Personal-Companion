# ADR-006 — M6 foreground read-only bridge and imported provenance

Status: implementation decision within owner M6 goal; independent review pending.
This realizes baseline ADR-009 in the register with **manual foreground** reading, not automatic polling.

## Boundary and alternatives

Keep the React PWA as primary phone UI. A minimal Kotlin ComponentActivity bridge uses only
Health Connect SleepSessionRecord, StepsRecord and ExerciseSessionRecord READ permissions.
No write/delete-to-source code, INTERNET, routes, background/history permissions or polling.
A loopback server would require INTERNET/network/auth infrastructure; file provider/export would
risk external storage exposure. M6 therefore uses owner-controlled USB handoff of two fixed,
app-private bridge artifacts via ADB `run-as`, not a generic filesystem/command service.
No Samsung private API, cloud backend, Android app rewrite or remote rollout.

## Persistence and source semantics

Mac schema 6 adds health_records, health_revisions and health_state to the existing local SQLite
store, separate from journal/self-report/M3 memory. Private real verification uses a fresh dedicated
M6_PRIVATE_HEALTH_TEST root with only the same health tables, never a personal journal migration.
Opaque local UUID plus exact type/source ID preserve identity; origin is stored privately and
conflicting origin for an existing source ID is rejected. Health Connect deletion reports only ID;
per-type tokens avoid guessing a deletion type. Source metadata is data, never SQL/tools/instructions.
Last-modified guards stale upserts. Updated payload gets local revision history; source deletion
retains minimal tombstone and removes previous source-derived revision payloads. Older backup
copies remain historical private copies; no claim to erase them remotely.

No health aggregate is computed: Steps aggregate stays UNRESOLVED, especially across overlapping
origins. UNKNOWN and denied/missing states are not numeric zero. Source time instants/offsets and
unknown source codes are preserved; journal local_date never shifts.

## Delivery and recovery

Bridge keeps per-type tokens privately, reserves token before initial paginated read, drains changes,
and persists the entire cumulative cache/tombstones plus sequence/epoch. Replayed full cumulative
handoff prevents losing deletions if transport fails after Android checkpoint moves. No tokens in
transfer/backup/public evidence. Partial denial/failure has no records and does not advance that type.
One import job at a time, cancelled when native UI stops. The handoff staging expires after 15 minutes
on the next foreground capability check; explicit cleanup is offered without source mutation. Invalid/expired tokens re-read permitted
recent history; old unseen records become UNKNOWN, not invented deletions or zero. Reconciliation
outside the accessible history window cannot prove deletion. Bounds are strict, surfaced as failures.

Mac transaction atomically applies batch + checkpoint. Sequence conflicts/stale batches, unexpected
epoch without explicit reconnect and generation-stale queued actions are rejected. Local delete
clears records/revisions and receipt state, rotates generation and blocks implicit re-import.
Re-import requires explicit owner action. Permission revocation preserves prior local copies and
stops reads; disconnect is distinct from source permission revocation.

## Backup, restore and rollback

Existing consistent private SQLite snapshot includes normalized health/tombstones. No Health Connect
tokens/permissions are present. Backup invalidates source connection/epoch receipt; restore rotates
generation, blocks automatic import, marks previously VALUE copies UNKNOWN and requires reconnect.
After reconnect, updates/deletions reconcile by stable source identity without duplicates. Corrupt
health metadata/history is rejected before activation. Synthetic previous-schema migrations retained.
Rollback: remove bridge permissions/uninstall debug app, explicitly delete local imported copy;
previous private backups are retained unless owner separately removes them. No source write occurs.

## Evidence

Early 0.6.0-debug actual Galaxy test: granted read/real private import/replay/incremental/Sleep revoke.
Later recovery/cancellation refactoring is synthetic build/unit verified, not claimed as newly tested
on hardware. Any later hardware-only follow-up remains NOT_RUN until a separate short connection.
Official APIs checked against installed connect-client 1.1.0 and successful compile API 36.
References: [official setup](https://developer.android.com/health-and-fitness/health-connect/get-started),
[official changes semantics](https://developer.android.com/health-and-fitness/health-connect/sync-data),
[AndroidX release notes](https://developer.android.com/jetpack/androidx/releases/health-connect).
