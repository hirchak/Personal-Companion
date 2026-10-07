# M8E-H01 final account-shape correction — evidence

**Status:** AWAITING_REVIEW

**Base R3:** `df1c151eeca5920d3e2721726fd0ae77f0d09beb`

**Implementation C4:** `c95e49ff92b5e4d42b877e91e5e9464258dc7588`

**Prior protocol implementation C3:** `611d2726e9a69d6e195c677a0a6adb3f46d4daf7`

**Evidence commit:** This report is contained in the evidence-only R4 commit. Its exact SHA is the containing Git commit and is reported by final delivery; it is not embedded here to avoid a self-hash cycle.

The final account/read correction treats an empty account object and missing, null, empty, whitespace-only, or
non-string `account.type` as a protocol/route failure. A well-formed `account: null` and a well-formed non-ChatGPT
string account type remain `EXISTING_CHATGPT_AUTH_REQUIRED`. No account fields other than the allowlisted auth type
are retained; raw RPC data and exception messages never reach UI or logs.

Deterministic local fake-app-server regressions cover each malformed account shape and the valid auth outcomes. They
preserve the C3 envelope/result checks for initialize/account/read/model/list and readiness’s no-thread/no-turn/no-
inference property. H02’s explicit frontend code allowlist is unchanged and remains ACCEPTED.

## Exact-C4 checks

Environment: Darwin arm64, Python 3.13 virtual environment, existing Node/npm dependencies, Chromium; all PRIVATE_LOCAL test data was synthetic and disposable.

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | PASS — 846 passed, one upstream Starlette deprecation warning, exit 0 |
| `.venv/bin/python -m pytest -q tests/test_m8e_readiness.py` | PASS — malformed account/result categories exercised with local fake RPC only |
| `npm test` | PASS — 53 passed, exit 0 |
| `npm run build` | PASS — TypeScript check and Vite build, exit 0 |
| `.venv/bin/python -m apps.core.release prepare --output generated/releases/M8D-c95e49ff92b5e4d42b877e91e5e9464258dc7588` | PASS — exact C4 package, exit 0; manifest hash `a48177bbdc52a0c8d5a1ac3d2643f36aeb4cf31365db14fdb7a532b146eb39c6` |
| `PYTHONPATH=. .venv/bin/python scripts/verify_m8e_browser.py --package generated/releases/M8D-c95e49ff92b5e4d42b877e91e5e9464258dc7588` | PASS — exact package Chromium; 21 checks, 0 page errors, 0 non-loopback requests, exit 0 |
| `.venv/bin/python scripts/check_docs.py` | PASS — local docs/links/schema structure, exit 0 |
| `.venv/bin/python scripts/build_chatgpt_context.py` | PASS — current goal/state snapshots generated from C4 |
| `.venv/bin/python scripts/check_privacy.py --include-generated` | PASS — no findings; worktree, generated snapshots, built UI, tracked paths, and local Git objects scanned, exit 0 |
| `git diff --check` | PASS, exit 0 |

The exact-package Chromium output records `live_provider_calls: 0`, `real_vault_inspected: false`,
`physical_phone: NOT_RUN_NEEDS_TRANSPORT_GATE`, and `human_ua: PARTIAL_OWNER_PILOT_OPEN`. No real owner data,
account settings, or owner microphone was accessed. CI remains NOT_CONFIGURED/NOT_RUN.

## Preserved boundaries

H02 remains ACCEPTED. The C4 owner pilot was not inspected, modified, upgraded, or rechecked, and C4 was not
installed. External settings remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone transport remains
`OFF / NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF. No live inference, release, tag, or deploy occurred.
