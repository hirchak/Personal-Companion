# M8E-H01 final account-shape correction

Continue M8E only. Base from current `origin/main`: `df1c151eeca5920d3e2721726fd0ae77f0d09beb`.

In `CodexConversationProvider.readiness()`, malformed `account/read` results must not be classified as missing
ChatGPT authentication. An empty `account` object or missing/invalid `account.type` returns protocol/route
failure. A well-formed `account: null` and a valid non-ChatGPT account remain `EXISTING_CHATGPT_AUTH_REQUIRED`.

Add deterministic negative regression tests. Preserve the JSON-RPC envelope/result validation, H02 explicit UI
allowlist, one-click AI, independent microphone/local Whisper, exact payload/Deep/journal bindings, no fallback/
PAYG, and clinical/Health/phone OFF.

Zero live inference; no real vault or owner-pilot access/installation. Run relevant/full tests, exact-C build,
Chromium, and privacy checks; create forward C/R, normal fast-forward push, verify `origin/main == R`, then stop
AWAITING_REVIEW. No milestone change, release, deploy, or force push.
