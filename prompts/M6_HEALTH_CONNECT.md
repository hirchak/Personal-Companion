M6 — READ-ONLY HEALTH CONNECT / SAMSUNG BRIDGE + REAL GALAXY HARDWARE GATE

Repository:
https://github.com/hirchak/Personal-Companion.git

Current verified main/base:
2edf0995d6d996200d9502484deb7bb557259b7e

Reviewed M5:
C = 7585005d42ff7211b543fe63e443ece92f92a2ae
R = 2edf0995d6d996200d9502484deb7bb557259b7e

External architect verdict:
M5 = ACCEPT for synthetic engineering scope.

Owner has separately supplied explicit M6 authorization for:
- Galaxy S24 Ultra hardware testing;
- Galaxy Watch7-derived data already available to Health Connect;
- read-only Sleep, Steps, Exercise only;
- user-approved Health Connect permissions;
- local private verification using actual records;
- project-local Android/Gradle/Maven dependencies;
- debug APK installation through ADB;
- USB debugging and temporary adb reverse/forward.

The separate OWNER AUTHORIZATION is binding and narrower than this specification.
If anything here conflicts with it, the narrower owner authorization wins.

==================================================
1. M6 GOAL
==================================================

Build and verify the first real Android health integration:

Galaxy Watch7 / Samsung Health / Health Connect
→ minimal native Android bridge on Galaxy S24 Ultra
→ read-only normalized health records
→ safe local import into Personal Companion
→ provenance/dedup/update/delete/revoke behavior
→ no clinical interpretation.

This milestone has two distinct layers:

A. complete synthetic engineering implementation and regressions;
B. actual Galaxy S24 Ultra hardware/Health Connect gate.

Unlike previous milestones, attempt B now because the owner has the real phone connected and
has explicitly authorized the limited test.

M6 must not become a general Android rewrite of Personal Companion.
The existing PWA remains the primary phone UI.

The native component should be the smallest reasonable bridge needed to access Health Connect.

==================================================
2. RECORD CURRENT REVIEW STATE
==================================================

At start:

- fetch/verify actual origin/main;
- verify clean worktree and ancestry;
- preserve published history;
- record external M5 ACCEPT durably:

  reviewed implementation C:
  7585005d42ff7211b543fe63e443ece92f92a2ae

  reviewed evidence R:
  2edf0995d6d996200d9502484deb7bb557259b7e

  scope:
  synthetic engineering only.

- update STATE/HANDOFF appropriately;
- activate only M6.

Do not self-assign ACCEPT to M6.

==================================================
3. CRITICAL SCOPE — READ ONLY
==================================================

Health integration is READ ONLY.

Authorized data categories:

1. Sleep
2. Steps
3. Exercise / activity sessions

Do NOT request/read:

- heart rate;
- blood pressure;
- SpO2;
- body composition;
- location;
- exercise route/location;
- medical records;
- reproductive data;
- nutrition;
- medications;
- temperature;
- all-health-data wildcard permissions;
- any type not explicitly authorized above.

No Health Connect write permission.

No Samsung Health write.

No deletion or mutation of source health records.

No WRITE permissions “for future use”.

If exact permissions/data-type names differ in the installed/current Health Connect SDK,
resolve them from actual official APIs/installed dependency documentation rather than guessing.

==================================================
4. BACKGROUND / HISTORY BOUNDARY
==================================================

Do NOT request:

- READ_HEALTH_DATA_IN_BACKGROUND;
- READ_HEALTH_DATA_HISTORY;

unless separately authorized later.

M6 foreground/manual import must work without those extended permissions.

If Health Connect imposes a limited historical read window under current permissions:
- detect/document it;
- do not bypass it;
- do not call missing history “zero”.

No background periodic sync in M6.

No WorkManager health polling.

No boot receiver/autostart.

==================================================
5. REAL DEVICE SAFETY
==================================================

Reference hardware is already known:

- Samsung Galaxy S24 Ultra
- Samsung Galaxy Watch7

Do not ask their models again.

Exact following properties remain NOT_VERIFIED until inspected on the actual device:

- Android version;
- One UI version;
- Samsung Health version;
- Health Connect implementation/version;
- Watch firmware;
- actual record fields/data origins;
- Health Connect permissions currently granted;
- presence/absence of Sleep/Steps/Exercise data.

Record only sanitized version/capability metadata suitable for public engineering evidence.

Do NOT commit:
- real health values;
- record IDs;
- device serials;
- Android ID;
- account/email;
- Health Connect source package IDs if they reveal private/local setup unnecessarily;
- screenshots containing real health data;
- timestamps from private health history;
- ADB device serial.

Public evidence should say things like:

Sleep records present: YES
Steps records present: YES
Exercise records present: NO / YES

not actual sleep times, step counts or workout details.

==================================================
6. NATIVE ANDROID BRIDGE
==================================================

Create the smallest maintainable native Android module/component required to read Health Connect.

Do not rewrite the existing React PWA into a native application.

Preferred conceptual structure:

PWA / Personal Companion
+
small Android Health Bridge

Bridge responsibilities:

- availability/capability check;
- request only authorized read permissions;
- read supported Health Connect record types;
- normalize them into a strict bridge schema;
- maintain sync/change state where available;
- make records available to Personal Companion through a controlled local interface;
- expose revoke/disconnect state clearly.

Choose architecture autonomously.

Possible communication methods may include:
- local app-to-app/deep-link/file handoff;
- bounded local loopback interface;
- explicit export/import;
- another simple secure local bridge.

Do NOT add a public/cloud backend.

Do NOT expose the bridge on LAN/public network.

Do not invent unnecessary native infrastructure.

==================================================
7. ANDROID PROJECT / BUILD
==================================================

Android code must be reproducible and isolated inside the repository.

Allowed under owner authorization:

- Gradle wrapper/project-local Gradle;
- Android/Jetpack/Health Connect dependencies from normal official Maven/Google repositories;
- project-local build caches/dependencies;
- debug APK;
- ADB install to the connected owner device.

Not allowed:

- release signing;
- Play Store publication;
- Firebase;
- analytics SDKs;
- cloud backend;
- global Homebrew/system changes;
- sudo;
- root;
- arbitrary Android tooling installed globally without separate approval.

If an essential Android SDK/system package is absent and cannot be obtained within the explicitly
authorized project-local workflow, STOP at that exact point and report the dependency.

Do not silently install system components.

==================================================
8. PERMISSIONS UX
==================================================

The real user must remain in control of Health Connect permissions.

Provide a clear user-facing permissions screen explaining:

- Sleep: read only;
- Steps: read only;
- Exercise: read only;
- no writes;
- no background health reading;
- no extended historical permission;
- data stays local to Personal Companion in this milestone;
- no AI receives health records.

The owner/user must personally approve Android/Health Connect permission dialogs.

Do not use ADB/UI automation to silently grant health permissions unless the platform test framework
has an explicitly safe test-only permission mechanism and it does not bypass the real hardware gate.

For actual acceptance, manually granted permission is preferred.

Permission denial must be a normal supported state.

==================================================
9. HEALTH CONNECT AVAILABILITY / CAPABILITY SNAPSHOT
==================================================

Before import, inspect the actual device.

Record a sanitized capability result such as:

- Health Connect available/unavailable;
- required update/setup if applicable;
- permission states for three authorized categories;
- whether each authorized category has readable records;
- visible accessible field names/types;
- data-origin count/categories if safely sanitizable;
- current bridge/app version;
- API/SDK level.

Do not assume Watch7 fields from marketing/docs.

Use actual API responses.

If Samsung Health is not currently writing one category into Health Connect:
mark that category AVAILABLE_BUT_NO_RECORDS or NOT_AVAILABLE as appropriate.

Do not fabricate sample data to turn the hardware gate green.

==================================================
10. DATA MODEL — RAW IMPORT LAYER
==================================================

Health records must remain distinct from self-report journal fields.

Create a dedicated imported-health representation.

At minimum each imported normalized record needs logical equivalents of:

- local opaque import ID;
- source system = Health Connect;
- source record identity or stable privacy-safe internal key;
- source data origin;
- record type;
- source revision/last-modified information where supported;
- start/end instant or date as appropriate;
- source timezone/offset when available;
- normalized fields;
- units;
- imported_at;
- first_seen;
- last_seen;
- deleted/upsert status;
- schema version;
- provenance = program/source imported, not USER_REPORTED.

Do not overwrite journal self-report values.

Example:
user says “slept 7h”
and wearable estimates something else
→ keep both separately.

No automatic “correction”.

==================================================
11. MISSING DATA
==================================================

Missing != zero.

Examples:

- no steps permission ≠ 0 steps;
- no record for interval ≠ 0 steps;
- missing sleep stage ≠ zero minutes;
- absent exercise list ≠ proof of inactivity;
- unavailable Health Connect field ≠ false/zero value.

Represent explicit states such as:

VALUE
MISSING
NOT_AVAILABLE
PERMISSION_DENIED
NOT_REQUESTED
SOURCE_DELETED
UNKNOWN

or equivalent typed semantics.

Never insert fabricated zero values for missing fields.

==================================================
12. SLEEP IMPORT
==================================================

Read available Health Connect sleep records in authorized scope.

Preserve only fields actually supplied by the API/device.

Possible concepts may include:
- session start/end;
- stages if actually present;
- metadata/data origin;
- update/deletion identity.

Do NOT assume a particular stage taxonomy beyond what the actual SDK/records supply.

Normalize known Health Connect values safely.

Unknown/new stage type:
preserve as unknown/source-specific rather than crash or remap incorrectly.

Do not derive:

- clinical total sleep time claim beyond source semantics;
- insomnia diagnosis;
- sleep efficiency as a clinical statement;
- cortisol;
- depression;
- cause of fatigue.

Source device estimates are consumer-device data.

==================================================
13. STEPS IMPORT
==================================================

Read Health Connect Steps records.

Prevent naive double counting.

Do not automatically sum overlapping steps from different data origins.

Define and document a deterministic provenance/dedup policy.

Possible safe initial behavior:

- preserve source records independently;
- when displaying an aggregate, use an explicit source/priority rule or Health Connect's
  semantics if an official aggregate API provides deduplicated totals;
- never sum overlapping origins blindly.

If correct dedup semantics cannot be proven:
store records but mark aggregate as UNRESOLVED instead of inventing a total.

Test overlap explicitly.

==================================================
14. EXERCISE IMPORT
==================================================

Read only authorized exercise/activity session records.

Do not request exercise route/location permission.

Do not infer route.

Store only available non-location fields.

Unknown exercise type must remain source/unknown rather than cause failure.

No calories/heart-rate enrichment unless that data is already part of the specifically authorized
Exercise record itself and does not require another unauthorized record permission.

If access to a field would require another health permission:
omit it.

==================================================
15. CHANGE TRACKING / INCREMENTAL SYNC
==================================================

Implement a robust incremental import.

Use Health Connect's supported change/update mechanism where appropriate rather than repeatedly
blind-importing the full history forever.

Requirements:

- separate state/checkpoint/token per relevant scope/type if the API semantics warrant it;
- initial read;
- next incremental read;
- upsert;
- source update;
- source deletion;
- invalid/expired checkpoint recovery;
- idempotent retry;
- app restart;
- duplicate delivery;
- permission revoke;
- partial failure.

Persist tokens/checkpoints privately.

Do not publish tokens or source IDs.

If actual installed API behaves differently from assumptions:
adapt implementation to current official API and document the actual semantics.

==================================================
16. DEDUP / IDEMPOTENCY
==================================================

Repeated import must not create duplicate logical records.

Test:

same source record twice
→ one local imported record.

Updated source record
→ update/revision history, not duplicate.

Deleted source record
→ local source-derived record marked/deleted according to the import policy.

Reinstall/reconnect scenario:
must not silently multiply old records.

Use stable source identity + origin + record type + appropriate metadata.

Never use approximate timestamps alone as the sole identity if the source exposes stable IDs.

==================================================
17. SOURCE DELETION
==================================================

When Health Connect reports source deletion/change:

- reflect it in imported-source state;
- invalidate derived cached aggregates based on the removed record;
- do not delete an independent user journal entry;
- do not delete user-confirmed memory that merely references their own statement;
- source-derived future analysis must no longer use deleted data.

Keep minimal audit/tombstone metadata if required for idempotency.

No resurrection from stale device queues/backups without explicit reconciliation.

==================================================
18. PERMISSION REVOCATION
==================================================

Test actual revoke on device where feasible.

When permission is revoked:

- future reads stop;
- UI clearly shows permission revoked;
- no repeated bypass prompts;
- imported existing local data is not silently deleted unless user explicitly chooses;
- no health requests sent to another path/provider;
- journal/creative/voice continue normally.

Provide explicit local imported-data deletion separately.

No “permission required to use the app”.

==================================================
19. LOCAL PRIVATE IMPORT
==================================================

Real hardware test may read actual authorized health records only for local verification.

Real values stay in a private local runtime/data root.

NEVER:

- commit actual health values to Git;
- paste values into reports;
- include them in screenshots;
- include source IDs;
- include private timestamps;
- include them in ChatGPT context snapshots;
- include them in devlogs;
- use them as test fixtures.

Evidence uses sanitized structural statements only.

If Codex terminal output from a debug command would print real records:
redirect to ignored/private file or sanitize before display.

Avoid echoing full records to terminal.

==================================================
20. BRIDGE → MAC / PERSONAL COMPANION
==================================================

Integrate imported records into the existing local-first system.

Do not silently activate private remote transport/Tailscale.

For the real USB hardware gate, temporary ADB reverse/forward is explicitly allowed by owner.

Use it only as needed for controlled local testing.

No permanent network listener beyond existing loopback boundaries.

If import requires a bridge handoff from phone to Mac, design:

- authenticated or owner-controlled;
- schema validated;
- bounded;
- idempotent;
- no arbitrary paths;
- no client-supplied SQL;
- no shell;
- no provider calls;
- no broad device command API.

Health bridge must not become a generic Android remote-control service.

==================================================
21. PHONE / MAC OWNERSHIP
==================================================

Keep clear where authoritative source lies:

Health Connect source record
→ imported normalized health record
→ optional derived display/cache.

Health Connect is source authority for imported wearable data.

Mac is not allowed to write back.

Phone bridge is not allowed to rewrite Health Connect.

Personal Companion imported copy is a local cache/history with provenance.

==================================================
22. UI
==================================================

Add a neutral health/wearable section.

Do not make it medical.

Suggested Ukrainian language:

«Дані з годинника»
or
«Health Connect»

Show:

- connection status;
- permission status for Sleep / Steps / Activity;
- last import time;
- count/status, without exposing unnecessary private details in diagnostics;
- source availability;
- sync/import button;
- revoke/disconnect instructions;
- imported-data deletion option;
- clear distinction between:
  “Записано вами”
  and
  “Імпортовано з Health Connect”.

Do not show diagnostic warnings or clinical labels.

No red “bad sleep” score.

No judgement.

==================================================
23. HEALTH DATA + M3 AI
==================================================

M3 live provider remains OFF.

Health records must NOT automatically enter AI context.

Do not add health records to existing exact-context selector in M6.

Do not send health data to:
- Codex;
- OpenAI API;
- MiniMax;
- any cloud provider.

Future health-to-AI use requires separate explicit consent/design milestone.

Mock AI must not automatically inspect imported health records either unless a later scope explicitly
adds a reviewed health-context contract.

==================================================
24. HEALTH DATA + MEMORY
==================================================

Imported records are not long-term personal “facts” inferred by AI.

Do not convert:

“steps = X”
or
“sleep session = Y”

into model memory.

No automatic statements such as:
- “user sleeps badly”;
- “user is inactive”;
- “user has sleep disorder”;
- “user is stressed”.

If future summaries exist, they need a separate analytics/research scope.

==================================================
25. ANALYTICS — DEFERRED
==================================================

M6 is data plumbing/import, not health interpretation.

Allowed deterministic displays:
- raw/readable source records;
- explicit simple totals if semantics are verified;
- data availability/missingness;
- source/provenance.

Do not implement:

- causal correlations;
- mental-health predictions;
- readiness score;
- recovery score;
- cortisol model;
- sleep diagnosis;
- exercise prescription;
- medical advice;
- symptom inference.

R12 or equivalent wearable validity research remains a later evidence gate for analytics.

==================================================
26. R12 / RESEARCH BOUNDARY
==================================================

Do NOT open/ingest R01_RAW.docx, R02_RAW.docx or R03_RAW.docx.

Do not start clinical research automatically.

R12 wearable validity/evidence review may be required before later interpretations, but is not
required to prove read-only transport/import correctness.

M6 engineering ACCEPT must not be described as scientific validation of Watch7 measurements.

==================================================
27. ACTUAL DEVICE CAPABILITY PROBE
==================================================

Once bridge is built and debug APK installed:

perform a bounded real-device probe.

Owner may need to tap permission dialogs.

Capture only sanitized results:

- device detected by ADB: YES;
- bridge installed: YES;
- Health Connect available: YES/NO;
- Sleep permission: GRANTED/DENIED;
- Steps permission: GRANTED/DENIED;
- Exercise permission: GRANTED/DENIED;
- records structurally readable for each: YES/NO;
- incremental read supported/tested: YES/NO;
- revoke tested: YES/NO;
- no write permissions: VERIFIED;
- unauthorized types inaccessible/not requested: VERIFIED.

No actual values in public evidence.

If a category has no real records:
do not create fake hardware evidence.
Test that category synthetically and mark real-data branch NO_RECORDS.

==================================================
28. SAMSUNG HEALTH / WATCH7 PROVENANCE
==================================================

Do not assume every Health Connect record came from the Watch7.

Use source/data-origin metadata.

If records indicate Samsung Health as origin, record sanitized origin class.

Do not infer physical hardware origin unless Health Connect metadata actually supports it.

Possible status:

SOURCE_APP_SAMSUNG_HEALTH
HARDWARE_ORIGIN_NOT_EXPOSED

rather than inventing “Watch7 record”.

If source metadata clearly identifies device type/model and it is safe to retain privately,
store it privately, but public evidence should remain sanitized.

==================================================
29. ANDROID LOGGING
==================================================

No health record payloads in Logcat.

No record values in exceptions.

No full metadata objects in debug logging.

No permissions tokens in logs.

Use:
record count,
status code,
type,
sanitized failure category.

Example allowed:
Imported Sleep: 3 records locally

But for public evidence prefer:
Sleep import: non-zero record set successfully processed

rather than personal counts if the count itself could expose behavior.

==================================================
30. NATIVE SECURITY
==================================================

Debug bridge must not export broad components unnecessarily.

Review Android manifest:

- only required permissions;
- exported=false where possible;
- no INTERNET permission unless strictly needed by project dependency/build and not runtime;
- no location;
- no health writes;
- no arbitrary file provider exposure;
- no custom scheme accepting arbitrary commands;
- no backup behavior that accidentally exposes health cache without review.

If INTERNET runtime permission is unnecessary, omit it.

No analytics/crash reporting SDK.

No WebView remote pages.

==================================================
31. PRIVATE STORAGE ON ANDROID
==================================================

Health bridge local cache/state must live in app-private storage.

No shared external storage.

Do not save real health JSON under Downloads/DCIM/public files.

If records are staged before local transfer:
- app-private;
- bounded retention;
- explicit cleanup;
- no credentials/health payload in filenames.

No claim of hardware-backed encryption unless actually verified.

==================================================
32. LOCAL IMPORT RETENTION / DELETE
==================================================

Provide explicit choice to remove locally imported health data from Personal Companion.

This does NOT delete Health Connect/Samsung Health originals.

UI must state that clearly.

Delete local imported copy:
- imported records;
- derived import indexes/checkpoints where appropriate;
- cached aggregates;
- queued health import operations.

Do not erase unrelated journal/self-report.

Resetting checkpoint must not make deleted local records silently reappear without a clearly defined
“re-import from source” action.

==================================================
33. BACKUP / RESTORE
==================================================

Decide explicitly whether imported health records belong in Personal Companion backup.

For M6 default:
include normalized imported records if consistent with existing private local backup architecture,
but never Health Connect permission tokens/system permissions.

Requirements:

- schema/version;
- provenance preserved;
- import checkpoint treatment explicit;
- device authorization/Health Connect permission must be re-established after restore;
- restore must not imply source is currently connected;
- stale bridge credentials/tokens invalidated;
- no duplicate import after reconnect.

If safer, restore sets:
SOURCE_RECONNECT_REQUIRED.

Test source update/delete after restore.

==================================================
34. DATA SCHEMA VALIDATION
==================================================

Bridge/import payload is untrusted external structured data.

Strict validation before DB mutations.

Reject:

- unknown schema version;
- malformed timestamps;
- impossible type structure;
- NaN/Infinity;
- invalid units;
- unexpected extra command fields;
- oversized batches;
- duplicate conflicting source IDs;
- arbitrary paths;
- SQL-like/tool-like fields as commands.

Text in source metadata remains data.

No generic Android command execution.

==================================================
35. SYNTHETIC HEALTH FIXTURES
==================================================

Create comprehensive synthetic Health Connect-like fixtures for deterministic tests.

Include:

Sleep:
- normal session;
- crossing midnight;
- DST change;
- missing optional fields;
- unknown stage;
- update;
- deletion.

Steps:
- one source;
- duplicate record;
- overlapping origins;
- update;
- delete;
- missing interval.

Exercise:
- supported type;
- unknown type;
- no location;
- update/delete;
- missing optional metadata.

Permission:
- deny;
- partial grant;
- revoke;
- unavailable Health Connect.

Never copy real records into fixtures.

==================================================
36. M6 ACCEPTANCE MATRIX
==================================================

Create docs/M6_CONTRACT.md.

At minimum:

M6-A01 — native bridge boundary
Minimal Android bridge builds reproducibly, strict read-only authorized types only.

M6-A02 — permission minimization
Only Sleep/Steps/Exercise read permissions requested; no write/background/history/location permissions.

M6-A03 — normalized provenance
Imported records preserve source/type/revision/time/unit/availability provenance without replacing self-report.

M6-A04 — missing != zero
Absent permission/field/record never becomes fabricated numeric zero.

M6-A05 — idempotent import
Repeated same source data creates one logical local record.

M6-A06 — update/delete
Source update modifies correct imported record; source deletion invalidates/removes source-derived state safely.

M6-A07 — incremental checkpoint
Restart/retry/change-token behavior is deterministic and no duplicate/resurrection occurs.

M6-A08 — revoke
Permission revocation stops future reads; journal/PWA remain functional.

M6-A09 — overlap/dedup safety
Steps from multiple overlapping origins are not blindly double-counted.

M6-A10 — privacy boundary
No health values/source IDs/device IDs in Git/evidence/logs/screenshots.

M6-A11 — no clinical inference
No diagnosis/cortisol/readiness/mental-health inference from imported data.

M6-A12 — AI isolation
No Health data enters M3 provider context; live provider remains OFF.

M6-A13 — backup/restore
Imported data and reconnect state restore coherently without permission-token reuse or duplicates.

M6-A14 — previous milestones
M1–M5 regressions remain green.

M6-A15 — real Galaxy bridge
Debug bridge installs/runs on actual Galaxy S24 Ultra with authorized Health Connect permissions.

M6-A16 — real Health Connect read
At least one authorized category with real available records successfully completes sanitized structural
import verification. Do not require all categories to contain records.

M6-A17 — real permission revoke
Actual revoke/deny path is tested on device where platform interaction permits.

M6-A18 — no source write
Actual/runtime code contains and exercises no write/delete-to-Health-Connect behavior.

==================================================
37. HARDWARE VERDICT SEMANTICS
==================================================

Do not call hardware PASS if only emulator/fake repository tests ran.

Possible final states:

M6-A15 PASS
M6-A16 PASS / NO_RECORDS / BLOCKED
M6-A17 PASS / NOT_RUN with exact reason

If real device cannot complete due to owner interaction:
stop at the permission screen and tell owner exactly what to tap.

Do not downgrade entire synthetic implementation to blocked if only one hardware subgate needs interaction.

==================================================
38. OWNER INTERACTION HARD STOPS
==================================================

Pause and ask owner only when a real user decision is required, such as:

- Android Health Connect permission dialog;
- enable/install/update Health Connect if OS explicitly requires it;
- reconnect USB authorization;
- system component installation outside existing authorization;
- broader permission than Sleep/Steps/Exercise;
- any action that would expose real health values publicly;
- any request for background/history/location permission.

Do NOT ask owner for routine implementation choices/tests.

==================================================
39. ADB RULES
==================================================

Allowed:
- adb devices;
- install/update debug APK for this bridge;
- logcat with strict filtering/sanitization;
- adb reverse/forward for temporary local test;
- start bridge activity;
- inspect package/version/permission state where non-sensitive.

Do NOT:
- dump arbitrary phone filesystem;
- pull Samsung Health databases;
- use root;
- use backup extraction;
- scrape private app data;
- bypass Health Connect permission model;
- retrieve account tokens;
- publish ADB serial.

Use Health Connect public API only.

==================================================
40. SAMSUNG-SPECIFIC RESTRICTION
==================================================

Do not reverse engineer Samsung Health private storage/cloud endpoints.

Do not depend on deprecated/private Samsung APIs.

Health Connect is the primary M6 path.

If actual Samsung Health → Health Connect sync is absent:
document it honestly.

Samsung Health Data SDK can remain an alternative future path only after separate review;
do not expand scope automatically.

==================================================
41. UI HARDWARE STATUS
==================================================

Show truthful integration status, e.g.:

Health Connect
Connected

Sleep — allowed / available
Steps — allowed / available
Activity — allowed / no records

Last import — [local time]

Or:

Permission denied
Nothing was imported

No misleading “Watch connected” just because Health Connect is installed.

==================================================
42. TIME / DST
==================================================

Health records are sensitive to time semantics.

Test:

- UTC;
- local offset;
- Europe/Warsaw DST transitions;
- sleep crossing midnight;
- records with missing zone;
- phone timezone change.

Store raw/source time semantics plus normalized UTC where applicable.

Do not infer timezone if source explicitly says unknown.

Never silently shift user journal local_date from wearable data.

==================================================
43. PERFORMANCE
==================================================

Synthetic benchmark:

- import 100 / 1000 records;
- incremental update batch;
- dedup lookup;
- restart/checkpoint;
- DB growth;
- memory/CPU where useful.

Real phone:
measure only non-sensitive operational data:

- bridge launch time;
- permission/capability query latency;
- import duration bucket or sanitized duration;
- bridge process memory if practical.

Do not publish actual number of personal sleep/workout/step records if avoidable.

No battery-life claim from one test.

==================================================
44. REAL HEALTH DATA EVIDENCE REDACTION
==================================================

Before writing any report/evidence:

explicitly sanitize.

Forbidden public evidence fields include:

- exact steps;
- sleep start/end;
- exercise dates;
- exercise types if personal;
- record IDs;
- package/source identifiers if user-specific;
- device IDs;
- ADB serial;
- account information;
- health payload hashes if they could fingerprint private records.

Evidence can record boolean/structural results and synthetic hashes.

Add automated checks where possible to catch accidental real-data capture.

==================================================
45. PUBLIC GITHUB BOUNDARY
==================================================

Public repository may contain:

- bridge source;
- Gradle config;
- synthetic fixtures;
- schemas;
- docs;
- sanitized hardware evidence;
- generic screenshots without real health data.

Never commit:

- debug APK if binary artifact policy says generated/ignored;
- keystore/private signing material;
- local.properties;
- Android SDK path;
- ADB serial;
- real Health Connect export;
- logcat containing real records;
- DB/runtime data;
- private screenshots.

Update .gitignore if needed.

==================================================
46. NO REAL PRIVATE JOURNAL MIGRATION
==================================================

Owner authorization permits limited real Health Connect verification.

It does NOT authorize migration of the girlfriend/private journal into this development environment.

Use a separate M6 hardware-test private local root.

Do not mix real Health Connect test records with synthetic public demo data.

==================================================
47. CURRENT M4/M5 DEFERRED ITEMS
==================================================

Do not opportunistically solve:

- real Whisper ASR;
- human Ukrainian ASR benchmark;
- full private Tailscale rollout;
- M4 actual microphone gate beyond what M6 requires;
- live AI;
- M5 publication;
- game expansion.

They remain separate gates.

M6 focuses on Health Connect.

==================================================
48. TESTING
==================================================

Keep complete M1–M5 regression suite.

Add:

- Android unit tests;
- bridge schema tests;
- permission manifest tests;
- synthetic health import tests;
- dedup/update/delete tests;
- checkpoint/change tests;
- partial permissions;
- missing-data tests;
- overlap/double-count tests;
- DST/time tests;
- revoke tests;
- backup/reconnect tests;
- malformed batch tests;
- no-write/no-background/no-location static assertions;
- Mac API/import tests;
- browser UI tests where relevant;
- real device test script/runbook;
- public evidence sanitizer tests.

Use deterministic tests.

No LLM judge.

==================================================
49. REAL HARDWARE TEST SEQUENCE
==================================================

Once synthetic checks pass sufficiently:

1. verify adb device connection without publishing serial;
2. build debug bridge;
3. install debug APK;
4. open bridge;
5. inspect Health Connect availability;
6. request only Sleep/Steps/Exercise READ;
7. owner manually approves/denies as instructed;
8. capability probe;
9. perform bounded real import into private ignored test root;
10. repeat import → verify no duplicate;
11. perform incremental refresh;
12. if safely possible, revoke one permission in Health Connect settings;
13. verify bridge reports revoked and stops reading;
14. re-grant only if owner explicitly does so;
15. verify no write/background/history/location permission;
16. inspect logs for absence of health payloads;
17. clean temporary private test output as appropriate;
18. generate sanitized evidence only.

Do not modify/delete actual Samsung Health/Health Connect records to manufacture an update/delete test.
Update/delete source semantics can remain synthetic if safely generating real source changes is not possible.

==================================================
50. M6 REPORTING
==================================================

Create/update:

- reports/M5_ARCHITECT_REVIEW.md

  External M5 ACCEPT
  C 7585005d42ff7211b543fe63e443ece92f92a2ae
  R 2edf0995d6d996200d9502484deb7bb557259b7e
  scope synthetic engineering.

- docs/M6_CONTRACT.md
- relevant ADR for native bridge / imported health provenance
- docs/M6_GALAXY_HEALTH_GATE.md
- reports/M6_HEALTH_CONNECT_REPORT.md
- reports/evidence/M6/*
- STATE.md
- HANDOFF.md
- ROADMAP.md
- TESTING/integration docs
- append-only devlog
- regenerated ChatGPT context.

Hardware report must be sanitized.

No raw health artifact.

==================================================
51. GIT / EVIDENCE WORKFLOW
==================================================

Standing direct-main development push authorization applies.

Because real private Health data may temporarily exist outside Git, be especially strict.

Before commit:

- verify no local private health files are staged;
- privacy scan;
- inspect generated/evidence files;
- verify Android local.properties/keystore/logcat/runtime data ignored;
- inspect `git status --ignored` if useful.

Workflow:

1. implement/fix;
2. synthetic/full regression;
3. real Galaxy hardware gate;
4. sanitize/remove private hardware evidence from public tree;
5. final implementation C;
6. exact-C checks;
7. evidence-only R;
8. verify C→R has no implementation changes;
9. privacy/public-tree scan including Git objects;
10. normal fast-forward push main;
11. verify origin/main == R;
12. stop.

If implementation code changes after C due to hardware findings:
create a new final C and rerun affected + regression checks before R.

No force-push.
No history rewrite.
No M7 auto-start.

==================================================
52. DEFINITION OF DONE
==================================================

M6 is ready for independent review when:

- M5 ACCEPT is durable;
- native bridge exists and builds;
- only three authorized read data categories are requested;
- no Health Connect writes exist;
- import schema/provenance/missing semantics work;
- duplicate/update/delete/checkpoint/revoke logic works synthetically;
- health/self-report remain separate;
- no clinical/AI inference exists;
- previous M1–M5 regressions pass;
- actual Galaxy debug APK successfully runs, or exact hardware blocker is reported;
- actual Health Connect permission flow is attempted;
- at least one real authorized record category is structurally verified if records are available;
- real values never enter public evidence/Git;
- no background/history/location permissions;
- privacy checks PASS;
- final C/R pushed normally;
- origin/main verified;
- M7+ remains OFF.

==================================================
53. FINAL RESPONSE
==================================================

Return concise handoff with:

- Base SHA;
- final C SHA;
- R SHA;
- origin/main SHA;
- M6 status;
- Python/web/Android/browser test counts;
- privacy result;
- Android bridge build/install status;
- connected device status WITHOUT serial;
- Health Connect availability;
- permission states:
  Sleep
  Steps
  Exercise;
- real structural record availability YES/NO per category without values;
- idempotent real re-import result;
- real revoke test result;
- confirmation Health Connect WRITE permissions = NONE;
- confirmation background/history/location permissions = NONE;
- M6-A01…A18 status;
- exact debug/hardware NOT_RUN blockers if any;
- CI status;
- exact synthetic demo/test command;
- exact sanitized hardware verification command/runbook location.

Do not include real health values.

Do not include ADB serial.

Do not start M7.
## Subsequent owner priority update

Perform the minimal early bridge / ADB / personally granted permissions / real bounded import,
replay, incremental and revoke before waiting for full synthetic implementation. Keep all payloads
private and evidence sanitized. After phone actions explicitly report PHONE CAN BE DISCONNECTED.
Complete remaining M6 offline; any later unverified hardware behavior is HARDWARE_PENDING/NOT_RUN,
not a fabricated early PASS. Do not retain owner by phone for ordinary implementation or tests.
