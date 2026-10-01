# M6 — bounded Galaxy Health Connect gate

Owner's Galaxy S24 Ultra / Watch7 are reference devices. Source app origin does not prove
Watch7 physical origin. Never inspect Samsung private storage or modify source health records.

## Authorization and owner actions

The owner authorizes ONLY read-only Sleep, Steps, Exercise after personally approving Android
permissions; local private verification; project-local Android/Gradle/Maven/JDK build dependencies;
debug bridge install/update; USB debugging and temporary reverse/forward if needed.
No Health Connect writes, Heart Rate, routes/location, medical or other categories, background/history
permissions, root, system trust changes, global installation, remote rollout, cloud AI/ASR or deployment.
M6 goal separately authorizes sanitized development C/R fast-forward pushes to main.
No private journal migration. This root is health-only, never a real journal vault.

USB: unlock phone → personally allow USB debugging for this Mac.
Bridge: «Дозволити читання трьох типів» → allow only Sleep / Steps / Exercise.
Revoke: «Керувати дозволами Health Connect» → app permissions → Personal Companion Health →
turn off Sleep → return to bridge. Regrant is optional and requires another personal owner action.

## Commands

```bash
.venv/bin/python scripts/bootstrap_android.py
apps/android-health/gradlew :app:assembleDebug :app:testDebugUnitTest
.venv/bin/python scripts/m6_hardware.py connection
.venv/bin/python scripts/m6_hardware.py install
.venv/bin/python scripts/m6_hardware.py open
# Owner personally grants only the three read permissions, then:
.venv/bin/python scripts/m6_hardware.py import
.venv/bin/python scripts/m6_hardware.py capture --root /private/tmp/personal-companion-m6-private-hardware --evidence reports/evidence/M6/EARLY_REAL_IMPORT.json
.venv/bin/python scripts/m6_hardware.py import
.venv/bin/python scripts/m6_hardware.py capture --root /private/tmp/personal-companion-m6-private-hardware --evidence reports/evidence/M6/EARLY_INCREMENTAL_IMPORT.json
.venv/bin/python scripts/m6_probe_permissions.py
# Owner revokes Sleep and returns, then repeat import/capture to EARLY_REVOKE.json.
```

Import is foreground-only. Wait for bridge «Локальна копія готова» before capture. `capture` is an
explicit owner-controlled USB handoff: `run-as` reads only this app's two fixed bridge-produced files.
It does not discover/scrape any app filesystem, database, accounts or settings. Raw payload goes
straight into validation and a fresh private health-only SQLite root outside Git; output is sanitized.
Tokens never leave app-private storage. Final 0.6.1 staging expires after 15 minutes on the next
foreground capability check; no background cleanup service. Explicit bridge-copy deletion is available.
The private verification root is retained only as owner-authorized local test data; it is never used
in synthetic tests/snapshots or added to Git. Remove its owned files after verification when desired. No LAN/INTERNET listener or ADB reverse/forward needed.

Initial read covers at most the last 29 days under normal grant; the SDK's permission-relative
historical limit is not bypassed. Missing older history is UNKNOWN, not zero or deleted.
Per type: maximum 1000 records, paginated 250, at most 40 change pages, one-million-byte staging cap.
Limit/read failure produces READ_FAILED for that scope, never a partial-success checkpoint.
Tokens are reserved before initial read; cumulative private export plus tombstones makes transfer
retry safe even when app checkpoint advances before Mac captures. Newer source changes use per-type
changes tokens. Recovery rereads permitted recent history and marks unseen old cache UNKNOWN.
No source deletion can be inferred outside a complete accessible interval.

## Evidence privacy

Public snapshots contain only OS/app versions, API level, granted/denied states, YES/NO/NOT_READ
availability, sanitized source classes, duration buckets and verification booleans. No values,
private timestamps, IDs, device serial, source package IDs, payload hashes, personal counts,
screenshots or raw logcat. No real records sent to AI. Watch firmware remains NOT_VERIFIED unless
owner independently provides safe metadata; no watch filesystem extraction.

Early native bridge gate precedes full M6 implementation by owner priority. Subsequent changes
must distinguish exact installed early build evidence from final implementation synthetic checks.
