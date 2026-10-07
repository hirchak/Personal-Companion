# M8E-H01/H02 independent-review fixes — evidence

**Status:** AWAITING_REVIEW

**Base R:** `16868ac34f50651b4c04465f6de0921c5f631ce3`

**Implementation C2:** `e0f56b79f305b5bf937487e73dc3f3222b2ec7c8`

**Prior UX implementation C1:** `8d3c528eb3364f01ee60b42c033d1bfe22ef4149`

**Evidence commit:** This report is contained in the evidence-only R commit. Its exact SHA is the containing commit and is reported by final delivery; it is intentionally not embedded here to avoid a self-hash cycle.

M8E-H01 now distinguishes a successful `account/read` response with missing/non-ChatGPT authentication from
readiness infrastructure failure. Account/model JSON-RPC failure, child process exit, transport failure, timeout,
and protocol failure map to `PRIVATE_PROVIDER_ROUTE_UNAVAILABLE`. A successful catalog missing or failing to verify
a required model/profile maps to `PRIVATE_PROVIDER_PROFILE_UNVERIFIED`; a catalog that verifies the model but lacks
the required effort maps to `PROVIDER_EFFORT_UNSUPPORTED`. Account details and raw RPC messages are discarded.
Readiness starts no thread or turn and reserves no inference attempt.

M8E-H02 replaces regex-only frontend error-code acceptance with an explicit allowlist derived from the codes with
approved UI recovery messages. Unknown codes, including uppercase underscore codes and synthetic secret-like
strings, collapse to `LOCAL_SERVICE_UNAVAILABLE`; the unknown code is not displayed.

The existing one-click durable-consent AI toggle, single first-use consent action, nonblocking external-settings
reminder, independent local microphone/Whisper, missing-ASR audio preservation, raw-audio-never-provider, exact
canonical payload/Deep/journal bindings, no fallback/PAYG/new auth, clinical/Health OFF, and phone OFF behavior
remain intact. The accepted C4 owner pilot was not opened, inspected, modified, upgraded, or rechecked. No live
provider inference, owner conversation, or owner microphone capture occurred.

## Exact-C2 checks

Environment: Darwin arm64, Python 3.13 virtual environment, existing Node/npm dependencies, Chromium. All PRIVATE_LOCAL cases used disposable synthetic roots; readiness used a local fake JSON-RPC executable with no network capability.

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | PASS — 825 passed, one upstream Starlette deprecation warning, exit 0 |
| `.venv/bin/python -m pytest -q tests/test_m8e_readiness.py tests/test_m8e_experience.py` | PASS — 22 passed, exit 0 |
| `npm test` | PASS — 53 passed, exit 0 |
| `npm run build` | PASS — TypeScript check and Vite production build, exit 0 |
| `.venv/bin/python -m apps.core.release prepare --output generated/releases/M8D-e0f56b79f305b5bf937487e73dc3f3222b2ec7c8` | PASS — exact C2 package, exit 0; manifest hash `be4499a5300c87617f3175ab5166082a69044de03e13bb4bb4f927e1ecc1eb2a` |
| `PYTHONPATH=. .venv/bin/python scripts/verify_m8e_browser.py --package generated/releases/M8D-e0f56b79f305b5bf937487e73dc3f3222b2ec7c8` | PASS — exact packaged C2 in Chromium; 21 checks, 0 page errors, 0 non-loopback requests, exit 0 |
| `node scripts/verify_m7a_schemas.mjs` | PASS — 7 checks, exit 0 |
| `node scripts/verify_m7c_schemas.mjs` | PASS — 12 checks, exit 0 |
| `node scripts/verify_m7d_schemas.mjs` | PASS — 14 checks, exit 0 |
| `.venv/bin/python scripts/m7_admission.py` | PASS — structural validation; clinical active 0, exit 0; 27 research findings remain open |
| `PYTHONPATH=. .venv/bin/python scripts/qualify_m7d_skills.py --check` | PASS — 5 candidate/off packages, exit 0 |
| `.venv/bin/python scripts/check_docs.py` | PASS — 838 files, 286 JSON, 369 local links, exit 0 |
| `/Users/hirchak/.agents/skills/impeccable/scripts/impeccable detect --json apps/web/src/PrivatePilotControls.tsx apps/web/src/ComposerVoice.tsx apps/web/src/ConversationHome.tsx apps/web/src/private-pilot-errors.ts` | PASS — no findings, exit 0 |
| `python3 -m py_compile apps/core/codex_conversation_provider.py apps/core/local_private_ai.py tests/test_m8e_readiness.py scripts/verify_m8e_browser.py` | PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |

The packaged Chromium result records `live_provider_calls: 0`, `real_vault_inspected: false`,
`physical_phone: NOT_RUN_NEEDS_TRANSPORT_GATE`, and `human_ua: PARTIAL_OWNER_PILOT_OPEN`. The privacy scan includes
the final evidence tree, generated snapshots, built UI, and all local Git objects; its result is recorded after R
in the final delivery. CI remains NOT_CONFIGURED/NOT_RUN.

## Preserved owner boundaries

External controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone transport is
`OFF / NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF. The C2 candidate is not installed into the owner
pilot. No real vault, account settings, credentials, provider inference/message, deploy, tag, or release was used.
