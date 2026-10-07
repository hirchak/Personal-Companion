# M8E-H01 final JSON-RPC protocol correction — evidence

**Status:** AWAITING_REVIEW

**Base R:** `9e6119707c6a9d4d13bd8bca92df4bd65eb80edd`

**Implementation C3:** `611d2726e9a69d6e195c677a0a6adb3f46d4daf7`

**Prior C2:** `e0f56b79f305b5bf937487e73dc3f3222b2ec7c8`

**Evidence commit:** This report is in the evidence-only R3 commit. Its exact SHA is the containing Git commit and is reported by final delivery; it is not embedded here to avoid a self-hash cycle.

## Correction

`CodexConversationProvider.readiness()` now validates JSON-RPC response correlation IDs, exactly one of result/error,
and dictionary result types for `initialize`, `account/read`, and `model/list`. Missing, null, list, false, or
otherwise malformed results are classified as protocol/route failures before any account or capability
interpretation. A properly formed `account/read` with `account: null` or a non-ChatGPT account remains
`EXISTING_CHATGPT_AUTH_REQUIRED`. A well-formed model catalog missing a required model/profile remains
`PRIVATE_PROVIDER_PROFILE_UNVERIFIED`; a verified model lacking the required effort remains
`PROVIDER_EFFORT_UNSUPPORTED`. Raw RPC data and exception messages are discarded.

The exact C3 test fixture is a local fake app-server executable with no network capability. Negative tests cover
malformed/missing initialize, account/read, and model/list results, account/model RPC errors, process exits,
protocol errors, bounded timeouts, missing and non-ChatGPT auth, missing/unverifiable models, and unsupported
efforts. A marker verifies readiness starts no thread or turn.

## Exact-C3 checks

Environment: Darwin arm64, Python 3.13 virtual environment, existing Node/npm dependencies, Chromium; all PRIVATE_LOCAL tests used disposable synthetic roots.

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | PASS — 841 passed, one upstream Starlette deprecation warning, exit 0 |
| `.venv/bin/python -m pytest -q tests/test_m8e_readiness.py tests/test_m8e_experience.py` | PASS — 38 passed, exit 0 |
| `npm test` | PASS — 53 passed, exit 0 |
| `npm run build` | PASS — TypeScript check and Vite build, exit 0 |
| `.venv/bin/python -m apps.core.release prepare --output generated/releases/M8D-611d2726e9a69d6e195c677a0a6adb3f46d4daf7` | PASS — exact C3 package, exit 0; manifest hash `f41e88ff5e5b5548371e9d246dfe33d89387eb70db8e0325d69f91c9b3439a9c` |
| `PYTHONPATH=. .venv/bin/python scripts/verify_m8e_browser.py --package generated/releases/M8D-611d2726e9a69d6e195c677a0a6adb3f46d4daf7` | PASS on final official repeat — 21 checks, 0 page errors, 0 non-loopback requests, exit 0 |
| `node scripts/verify_m7a_schemas.mjs` / `verify_m7c_schemas.mjs` / `verify_m7d_schemas.mjs` | PASS — 7 / 12 / 14 checks, exit 0 |
| `.venv/bin/python scripts/check_docs.py` | PASS — 841 files, 286 JSON, 369 local links, exit 0 |
| `.venv/bin/python scripts/build_chatgpt_context.py` | PASS — snapshots generated with source commit C3, exit 0 |
| `.venv/bin/python scripts/m7_admission.py` | PASS — structural status; 27 findings remain open; clinical active 0; exit 0 |
| `PYTHONPATH=. .venv/bin/python scripts/qualify_m7d_skills.py --check` | PASS — 5 candidate/off packages, exit 0 |
| `/Users/hirchak/.agents/skills/impeccable/scripts/impeccable detect --json apps/web/src/PrivatePilotControls.tsx apps/web/src/ComposerVoice.tsx apps/web/src/ConversationHome.tsx apps/web/src/private-pilot-errors.ts` | PASS — no findings, exit 0 |
| `.venv/bin/python scripts/check_privacy.py --include-generated` | PASS — no findings; worktree, generated snapshots, built UI, and all local Git objects scanned, exit 0 |
| `git diff --check` | PASS, exit 0 |

Two earlier exact-package Chromium attempts timed out waiting for an assistant message at different explicit-send
steps; the final official run of the same exact C3 package passed all 21 checks. This timing behavior remains visible
for independent review. The browser run reports `live_provider_calls: 0`, `real_vault_inspected: false`,
`physical_phone: NOT_RUN_NEEDS_TRANSPORT_GATE`, and `human_ua: PARTIAL_OWNER_PILOT_OPEN`. CI remains
NOT_CONFIGURED/NOT_RUN.

## Preserved boundaries

H02 remains ACCEPTED. The C4 owner pilot was not inspected, modified, upgraded, or rechecked; the C3 candidate was
not installed. External controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone remains
`OFF / NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF. No live inference, account-setting inspection, owner
conversation/message, owner microphone recording, deploy, tag, or release occurred.
