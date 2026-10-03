# M7A generic practice engine — AWAITING_REVIEW

Реалізовано deterministic admission-enforced finite practice/session engine і реальний український
local catalog/session/history UX. Production clinical active **0**, original synthetic demo **1**.
Жоден OFF research candidate не запускається. Технічний PASS не є content/rights/clinical approval.

## Commit / publication checkpoint

Base `9b3d8c7171920074fb9b755274d5879a0972c4ff`. Final C `a68ca709874a6efeb2ec848ec0e246c7264351b7`. Branch main; R — immediate evidence-only successor,
власний SHA не вбудовується рекурсивно. При створенні R: **PRE_PUSH**; normal fast-forward main
owner-authorized, live exact R/origin equality receipt — у фінальній відповіді. CI **NOT_RUN/no workflow**.

## Implementation / boundaries

Strict package schema1: unique IDs/entry, bounded plain Unicode, deterministic order/next, terminal
completion, supported information/ack/short-text/long-text/single-choice primitives. No workflow
expressions/branch engine/eval/scripts/imports/HTTP/tools. Text/package instructions are data.
Normalized content SHA-256 excludes only content_hash. No copied therapy/questionnaire/article content.

Canonical PREP registry/permissions unchanged, independently validated before admission/transitions;
source/claim/rights/hash drift fails closed. Generated constrained binding maps now key-closed for
standalone validation; Python validator remains strict. Runtime receipts are a separate explicit
boundary with ID/version/package/admission/technical footprint/owner decision/scope/epoch/UTC/expiry.
Current OFF-only preparation authority supplies no ACTIVE production admission; future production
receipt/registry evolution requires a separate authorized goal. Synthetic receipt grants neutral UX only.

Explicit --synthetic-practices + existing marked synthetic root required; normal serve has no runnable
fixture. Valid production-shadow package matching a real OFF ID is denied in both modes. Synthetic
metadata cannot become EVIDENCE/CONTENT/RIGHTS/APPROVED/ACTIVE clinical records. No continue-anyway.

Sessions pin exact package/version/receipt. ACTIVE/PAUSED/COMPLETED/STOPPED/BLOCKED transitions,
revision/CAS, stable operation IDs/replay, response edit history, timestamps/provenance, optional skip,
manual pause/resume/stop/exit and explicit deletion. Duplicate start/action/lost response cannot duplicate
sessions or overwrite stale state; blocked-action receipts survive response loss. Terminal sessions
never silently reactivate. Admission stale preserves user responses; current package is never substituted.

Vault envelope schema7 adds isolated practice tables; journal payload2/health import1 unchanged.
Existing SQLite transactions/backup/restore used. Four-state roundtrips preserve responses, restore
blocks runnable sessions/old receipt bindings and never restores activation config or provider consent.
Explicit delete cascades response/revision rows and redacts fingerprints, keeping only minimal
idempotency/tombstone metadata. Old backups/residual SQLite pages may retain copies; no forensic erase claim.
Selected-entry journal exports exclude sessions; no automatic response export/share/upload.

Practice errors/unavailable registry/storage do not gate journal/creative/voice/health. No automatic
journal/memory/health/tasks/feedback mutation, AI progression/classifier/crisis detection/reminders/
clinical homework/streak/reward/analytics. No live AI/model/provider call. No new sync/crypto/transport/auth/billing.
Responsive primary Mac local web; practice-session phone sync **M7A-deferred** because current M2
shared contract is entry-based and extension would enlarge scope. No cloud/Tailscale/phone prerequisite.
Native Android unchanged, full rebuild **NOT_RUN** with exact diff justification; Python native/source regression included.

## Exact-C verification

[Commands/exit/environment](evidence/M7A/EXACT_C_CHECKS.json), [18 gates](evidence/M7A/ACCEPTANCE_MATRIX.json),
[45-section audit](evidence/M7A/COMPLETION_AUDIT.json), [scope](evidence/M7A/SCOPE_AUDIT.json).
Clean committed C at check start/end; SHA unchanged. All ten checks exit0:

| Check | Result |
|---|---|
| Full Python `.venv/bin/python -m pytest -q` | **510 PASS**, including **34 real Chromium** cases in8 modules |
| Built React `npm --prefix apps/web run build` / `test` | build PASS; **43 PASS** |
| Independent `node scripts/verify_m7a_schemas.mjs` | **7 checks PASS**, unknown source/claim namespace keys denied |
| PREP `.venv/bin/python scripts/m7_admission.py` | structural PASS; content findings27 OPEN; clinical0 |
| Docs + generated context + source/output hashes | PASS |
| Privacy public tree/generated/all local Git objects + diff | PASS, heuristic scope |
| `.venv/bin/python -m scripts.measure_m7a` | measured synthetic25/100 sessions; original fixtures |

Python count from exact-C JUnit; browser count includes test_m2_ui plus seven *_browser modules.
Tests include14 malformed package cases, five actual process restart states plus terminated/restarted
HTTP server,11 invalidation causes, concurrency/replay/loss/stale writes, four backup states/revoked
restore, delete/purge, inert package/user script text, normal/demo isolation, migration rollback/data.
Three old latest-version assertions updated to current SCHEMA; their historical rollback/preservation
checks retained. Added explicit6→7 rollback/journal/health preservation test. Low-height sidebar lock
regression caused by the new nav item fixed, M6 affected browser check passed. One upstream Starlette
BlockingPortal deprecation warning; no test failure. Full exact-C regression supplies current evidence.

Environment Darwin arm64/Python3.13.2/Pydantic2.11.3/Node26.8.2; codex-cli0.159.0, actual current-session
model gpt-6.1-sol/high, Default execution (Plan OFF). No global installs/engine or model downloads.

## Local demo / visual review / measurement

```sh
./scripts/m7a_demo.sh /private/tmp/personal-companion-m7a-synthetic-demo
```

Command rebuilds UI with existing dependencies, creates/reuses only marked synthetic root, prints
loopback URL and one-time terminal code; open «Практики». Exact-C fresh-root
[demo command proof](evidence/M7A/DEMO_COMMAND_CHECK.json): start/save/pause/read/resume/stop,
4 seeded journal notes unchanged, clinical0/demo1, external calls NONE, phone NOT_USED.
Checker exit0; long-running demo server intentionally stopped by SIGTERM and owned test roots cleaned.

[UI review](evidence/M7A/UI_REVIEW.json), [design preservation](evidence/M7A/DESIGN_DOCUMENTATION.json),
[synthetic desktop catalog](evidence/M7A/ui/synthetic-catalog-desktop.png),
[mobile text step](evidence/M7A/ui/text-input-mobile.png). All24 named state/viewport captures retained.
Actual built browser proved normal/synthetic catalog, inputs/optional skip/pause/resume/stop/complete/
blocked/history/delete/empty; keyboard/focus,44px controls, wrapping/no document overflow/reduced motion.
Independent full26-capture handoff review valid after premature optional desktop capture recaptured.
Only material finding: browser-blue programmatic heading focus; palette fix scored resolved/ship at
that named-fix scope. Documentation agent rechecked final C, incumbent DESIGN preserved. Existing
narrative-sidecar drift/M5 detector shelf warning disclosed without redesign or unasked repair.

[Measured overhead](evidence/M7A/SYNTHETIC_PERFORMANCE.json): catalog/start/save/transition/history/
service reopen-resume and DB growth. Exact values in JSON; local synthetic service timings only,
not Galaxy/user outcome/provider cost/clinical improvement. Demo command timing includes local build.

## Rights/privacy/durable state and remaining gates

[Exact-C privacy](evidence/M7A/EXACT_C_PRIVACY.json) plus staged/C→R manual material review.
Only own engine/schemas/neutral fixture/tests/sanitized evidence/screenshots and approved external
review metadata in public Git. No RAW R01–R16, manuals/scales/forms/full articles, real sessions/
health/audio/vault/credentials/private endpoints/runtime DB. Scanner heuristics are not exhaustive
rights/security/privacy assurance. Real data/qualified clinical/legal review **NOT_PERFORMED**.

External [PREP ACCEPT](M7_PREP_ARCHITECT_REVIEW.md) only preparation/tooling; all27 research content
findings **OPEN**, originals16 externally received, locally manifest-only, primary checks partial.
Mechanical standalone-schema note closed; no research/content finding resolution claimed.
M6 scoped engineering + early0.6.0 hardware ACCEPT preserved; **M6-N01 OPEN**, final0.6.1 hardware NOT_RUN.
STATE/HANDOFF/roadmap/testing/ADR/devlog updated. Existing generator regenerates four ChatGPT
snapshots; local outputs ignored under unchanged canonical map/ignore. Snapshot evidence pins source/
output hashes with C provenance anchor and pending-R source texts explicitly distinguished.

Clinical/live AI/deploy/general real-data permissions remain OFF. **M7B/M8 NOT_STARTED**.
CI/native rebuild/final Galaxy smoke/live provider/real ASR/private transport/clinical/legal review NOT_RUN.
Result **AWAITING_REVIEW**, no self ACCEPT. Next only independent architect review exact pushed C/R;
no next milestone automatically started.
