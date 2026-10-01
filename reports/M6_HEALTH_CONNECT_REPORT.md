# M6 — AWAITING_REVIEW

Base: `2edf0995d6d996200d9502484deb7bb557259b7e`; main fetched/verified clean before work.
Final C: `1d30db9677f2c7b6f07145e8c0c5263969f39d3e`. R: evidence-only successor; exact R/origin push receipt in final response, no recursive self-hash.
M5 external synthetic ACCEPT recorded in [review](M5_ARCHITECT_REVIEW.md). No M6 self-ACCEPT.

[Contract](../docs/M6_CONTRACT.md), [ADR](../docs/adr/ADR-006-M6-HEALTH-BRIDGE.md),
[hardware runbook](../docs/M6_GALAXY_HEALTH_GATE.md), [owner goal](../prompts/M6_HEALTH_CONNECT.md).

## Implementation

Minimal Kotlin bridge, Health Connect 1.1.0, compile API36, project-local JDK/SDK/Gradle/Maven
caches, no global installation. Exactly three health READ permissions, no INTERNET/network handoff,
write, Heart Rate, routes/location/background/history, WorkManager, cloud or source mutation.
Manual foreground app-private staging, per-type tokens, before-read token reservation,
full cumulative replayable cache/tombstones and bounded incremental/recovery behavior.
Owner-controlled USB handoff only of two fixed bridge-produced files; no other app scraping.

Mac schema6 health tables preserve source/provenance/identity/time/unknown offsets/fields/units,
seen/imported timestamps, local revisions and deletion tombstones separately from journal/AI/memory.
Strict byte/schema/type/version/unit/time/duplicate/permission validation; atomic batch/checkpoint,
origin conflict/stale sequence/epoch and generation guards, explicit re-import after deletion/restore.
Steps totals unresolved, overlapping origins never summed. No clinical interpretation. Backup includes
normalized records, not HC tokens; restore UNKNOWN/reconnect required, previous schemas supported.

Mac Ukrainian health section provides permissions/availability/imported copy/provenance/local file
import/view/disconnect/delete. PWA read-only paired status/help is truthful offline and never claims
native Health Connect access or another health outbox. Journal/voice/creative remain independent.

## Actual early Galaxy gate — sanitized only

Owner-priority early 0.6.0-debug APK installed/opened on authorized Galaxy S24 Ultra.
Android16/API36; One UI build80500; Samsung Health7.00.6.011; HC system version17.
Personal USB grant and Health Connect three-type grant were confirmed by owner in this chat.
Health Connect AVAILABLE. Sleep GRANTED / real records YES; Steps GRANTED / YES;
Exercise GRANTED / NO_RECORDS in permitted recent read window. Samsung Health source class observed;
Watch7 physical origin/firmware NOT_VERIFIED, never inferred.

Private health-only import PASS; same batch replay PASS; actual foreground incremental refresh
OBSERVED; durable checkpoint/restart check PASS. Owner personally disabled Sleep; next read yielded
Sleep PERMISSION_DENIED/NOT_READ while Steps/Exercise remained allowed. Local prior copy retained.
No source writes or real source update/delete mutations. Installed manifest exactly allowlisted,
WRITE/background/history/location/INTERNET NONE. Own bridge PID log check found no payload markers;
raw logs never persisted. All public hardware artifacts passed the structural allowlist sanitizer.

[Early snapshots](evidence/M6/EARLY_REAL_IMPORT.json),
[incremental](evidence/M6/EARLY_INCREMENTAL_IMPORT.json),
[revoke](evidence/M6/EARLY_REVOKE.json),
[manifest](evidence/M6/EARLY_INSTALLED_MANIFEST.json),
[log check](evidence/M6/EARLY_LOG_REDACTION_CHECK.json).
Real payloads were never sent to AI/terminal/public evidence/Git/screenshots or reused as fixtures.
Private verification used a dedicated M6_PRIVATE_HEALTH_TEST root outside repository, not a real journal.
After structural proof, its owned temporary Mac files were removed; source originals were unchanged.
Early Android cache remains app-private with explicit cleanup UI; no post-release phone requirement.
Phone declared disconnectable after actual owner interactions; no subsequent phone requirement imposed.

Final 0.6.1-debug adds tested pure-cache refactoring, invalid-token recovery, stop-cancellation and bounded staging expiry.
Final build/unit verification is synthetic; reinstall/run of 0.6.1 after phone release NOT_RUN.
Real token expiry/recovery/app-background-cancellation/source update/delete remain NOT_RUN;
synthetic coverage does not masquerade as device evidence. No full real-phone PWA/M4/Tailscale gate.
Real launch/query/memory metrics NOT_MEASURED; early import duration bucket LT_1S only.
Exercise with real records, Watch firmware/hardware identity, real source changes not manufactured.

## Checks and next step

Previous local C57d30d64d592c70a4c4b8e8a937ffbb27cabdb82 exact checks passed and remain in
[evidence](evidence/M6/PREVIOUS_C_CHECKS.json). Forward fix C adds identical in-batch normalization
and cancellation before bridge-copy deletion. C803ef003ebfcd9e895a8f2813d1744fecf1e27ed
exact checks also passed ([evidence](evidence/M6/PREVIOUS_FORWARD_C_CHECKS.json)). Final forward
cleanup handles committed and interrupted owned staging files with filesystem tests; final exact-C
evidence supersedes these candidates.

[Exact-C command/environment evidence](evidence/M6/EXACT_C_CHECKS.json): clean committed C, all exit0.
- Python: **380 PASS**, including **29 Chromium** (5 M6), complete M1–M5 regressions retained.
- Web: **35 PASS**; TypeScript/Vite production build PASS.
- Android: **17 PASS**, offline final0.6.1 assembleDebug PASS; real install covered early0.6.0 only.
- Docs, generated context, structural hardware sanitizer, all-local-Git-object/generated/built privacy
  and diff checks PASS. Environment Python3.13.2, Node26.8.2, Darwin arm64; project-local JDK17/Gradle8.13.
- [A01–A18 matrix](evidence/M6/ACCEPTANCE_MATRIX.json), [all53 section audit](evidence/M6/COMPLETION_AUDIT.json).
One upstream Starlette deprecation warning; Gradle deprecation/compileSdk support notices, no build failure.
No hardware NOT_RUN state counted as a tested final-native path. Watch validity/clinical ACCEPT not claimed.

Synthetic 100/1000 records benchmark: [operational metrics](evidence/M6/SYNTHETIC_BENCHMARK.json).
Impeccable review scored both grouping/copy fixes resolved; incumbent design preserved, detector's
old shelf warning left outside M6 scope. No new raster assets/private screenshots.

Publication checkpoint PRE_PUSH at evidence creation. Next: evidence-only R, exact C→R allowed-path
review, final privacy scan, normal fast-forward push main and verify origin/main==R; then stop.
CI NOT_RUN (no repo workflow). M7+ OFF. Private remote/clinical/provider/deploy/releases remain OFF.
Demo `./scripts/m6_demo.sh /private/tmp/personal-companion-m6-synthetic-demo`.
Tests `.venv/bin/python -m pytest -q tests/test_m6_health.py tests/test_m6_api.py tests/test_m6_native.py tests/test_m6_browser.py`.
Hardware command/runbook above; owner interaction only on future explicitly scheduled short reconnection.
