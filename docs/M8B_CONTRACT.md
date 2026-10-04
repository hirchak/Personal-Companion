# M8B — real-reference-Mac synthetic dry run

Authority: [owner goal](../prompts/M8B_REAL_HARDWARE_SYNTHETIC_DRY_RUN.md), [ADR-012](adr/ADR-012-M8B-BACKUP-RUNTIME-HANDOFF.md).
Implementation completion = AWAITING_REVIEW. Actual private pilot NOT_STARTED.

| ID | Required contract | Evidence |
|---|---|---|
| M8B-A01 | Exact external M8A ACCEPT/notes durable | reports/M8A_ARCHITECT_REVIEW.md |
| M8B-A02 | Snapshot-bound exact backup producer/source/schema/format/time | release_metadata, Store format3, tamper tests |
| M8B-A03 | Historical backup compatibility explicit, not relabeled | format1/2; explicit legacy gate tests |
| M8B-A04 | New manifest binds pinned runtime-only lock | format2/runtime_input_hash; dependency tests |
| M8B-A05 | Startup without test deps/Git/node_modules | actual package + pip-free copied-runtime driver |
| M8B-A06 | Sanitized actual reference Mac preflight/schema | mac-preflight; MAC_PREFLIGHT.json |
| M8B-A07 | Actual Mac synthetic install/usage/stop/restart | verify_m8b.py real process + Chromium |
| M8B-A08 | Backup/restore/upgrade/failure/rollback/KEEP DATA | disposable roots only; MAC_LIFECYCLE.json |
| M8B-A09 | Phone exact gate, no implicit networking | PHONE_PRIVATE_TRANSPORT_REQUIRED |
| M8B-A10 | PWA offline/encrypted/update code evidence, Galaxy NOT_RUN | existing M2/browser/web regression; phone handoff |
| M8B-A11 | Stable FORMAL_VY; human language OPEN | M8A two-turn regression; no live model/human samples |
| M8B-A12 | Inactive first-pilot profile and operator handoff | packages/pilot/MAC_CORE_PROFILE.json; PILOT_HANDOFF.md |
| M8B-A13 | Independent honest core/phone/optional readiness | PILOT_READINESS.json; synthetic-only core gate |
| M8B-A14 | No private/live/clinical/health/trust/system/deploy activation | defaults/status, scope/public-tree review |
| M8B-A15 | Relevant exact-C regressions/build/Chromium/privacy | EXACT_C_CHECKS.json |
| M8B-A16 | C→evidence-only R→normal main FF→origin equality→STOP | final delivery verification, no self-ACCEPT |

M8A-N01/N02 only close after verified engineering outcomes. Hardware evidence is exact tested Mac/environment,
not clean physical Mac/all-Mac compatibility/Galaxy/Watch/human ASR proof. No provider-budget reuse/new auth.
