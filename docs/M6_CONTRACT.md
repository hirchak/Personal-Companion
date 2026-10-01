# M6 — read-only Health Connect acceptance contract

Owner goal: [53-section specification](../prompts/M6_HEALTH_CONNECT.md).
Authority: owner scoped authorization overrides broader baseline/private permissions only for
M6 Sleep/Steps/Exercise local health-only hardware verification, after personally granted permissions.
Standing/direct M6 goal allows sanitized C/R normal main push. No deployment/release/runtime publication.
M5 external synthetic ACCEPT is durable in [review](../reports/M5_ARCHITECT_REVIEW.md).

## Acceptance matrix

| ID | Requirement | Authoritative evidence |
|---|---|---|
| M6-A01 | Minimal reproducible native bridge | apps/android-health; final assembleDebug; Android unit tests; no PWA rewrite |
| M6-A02 | Exactly three read types; no broad permissions | AndroidManifest.xml, manifest/static tests, EARLY_INSTALLED_MANIFEST.json |
| M6-A03 | Separate normalized provenance/revisions/time/units | health-bridge.schema.json, health_records; synthetic provenance + journal test |
| M6-A04 | Missing != zero | denied/unavailable/missing/status tests; per-scope availability; no total inference |
| M6-A05 | Idempotent retry and stable source identity | restart/replay/duplicate/upsert tests; EARLY_REAL_IMPORT.json |
| M6-A06 | Source update/delete; minimal tombstone | update/history/delete/atomic-conflict tests; real source mutations NOT_RUN deliberately |
| M6-A07 | Per-type incremental checkpoint/recovery | native cache/recovery tests, synthetic sequence/epoch/restart tests; EARLY_INCREMENTAL_IMPORT.json |
| M6-A08 | Revoke stops reading, independent journal works | partial/deny tests, browser/PWA tests; EARLY_REVOKE.json |
| M6-A09 | Overlap never blindly summed | two-origin overlap test; Steps aggregate UNRESOLVED |
| M6-A10 | No private values/IDs in public tree/evidence/logs | allowlist sanitizer tests + scan; filtered early PID log check; Git-object scan |
| M6-A11 | No clinical inference | health tables/bridge/display only; no diagnostic/clinical/causal calculation |
| M6-A12 | No AI/memory context expansion | imported UUID rejected by journal-only M3 selector; mock execution 0; live OFF |
| M6-A13 | Private backup/reconnect coherent | schema6 validation, corrupted backup refusal, restore UNKNOWN/reconnect/update/delete tests |
| M6-A14 | Complete M1–M5 regression | final exact-C full Python, web and browser checks, unchanged functional scenarios |
| M6-A15 | Actual Galaxy installed/running bridge | early debug install/open receipt; before-grant capability and later granted snapshot |
| M6-A16 | Real category structural import | Sleep YES, Steps YES, Exercise NO in early real import; private replay and checkpoint PASS |
| M6-A17 | Actual owner permission revoke | owner personally switched Sleep OFF; EARLY_REVOKE.json Sleep PERMISSION_DENIED / NOT_READ |
| M6-A18 | No source writes in runtime/code | installed manifest no write, static source no mutations, hardware read only; source mutations never performed |

PASS belongs to the named test/gate, not self-ACCEPT or clinical validation. Early hardware and final
synthetic exact-C evidence are separate. A new source state is never fabricated to green a hardware gate.
Watch firmware and physical Watch7 origin remain NOT_VERIFIED; Samsung Health origin class is observed.
Exercise real record branch NO_RECORDS within authorized recent read window, synthetic import verified.

## Data and controls

Records retain schema/source/import provenance, opaque local ID, exact private source ID/origin,
source lastModifiedTime, source start/end instant and offsets (null = unknown), fields/units, first/last
seen/imported timestamp, local revisions and status. Type/source identity is stable; origin conflicts
fail transactionally. Sleep stages stay source codes, unknown codes preserved. Exercise routes never
accessed. No aggregate Health Connect API or enrichment is used.

Mac auth/session/Host/Origin/CSRF/body limit protects health endpoints; file import requires strict
schema, current generation, explicit reconnect after deletion/restore. Phone paired-device endpoint
returns status only, no new health outbox or raw health selector. Offline PWA reports unknown source
and keeps journal/creative/voice functional. No real health runtime UI/screenshots are used in tests.

[ADR](adr/ADR-006-M6-HEALTH-BRIDGE.md) defines checkpoint, tombstone, restore, USB security and limits.
[Galaxy runbook](M6_GALAXY_HEALTH_GATE.md) defines manual permissions, commands, privacy and cleanup.
Imported values are private local data; no tokens/system grants in backup. Delete copy does not remove
source records/journal. Past backups can retain historical copies; explicit restore is reconciliation.
