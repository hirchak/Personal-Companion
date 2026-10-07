# M8E-H01 final JSON-RPC protocol correction

Continue M8E only. Base from current main R: `9e6119707c6a9d4d13bd8bca92df4bd65eb80edd`.

In `CodexConversationProvider.readiness()`, validate the JSON-RPC response envelope and expected result type before
interpreting account or model capabilities. Do not use truthiness fallback to replace null, false, empty, or missing
results with `{}`.

- Malformed/missing `initialize`, `account/read`, or `model/list` result → protocol/route failure.
- A well-formed `account/read` result with `account: null` or a non-ChatGPT account →
  `EXISTING_CHATGPT_AUTH_REQUIRED`.
- A well-formed successful catalog missing a required model/profile → `PRIVATE_PROVIDER_PROFILE_UNVERIFIED`.
- A verified model without the required effort → `PROVIDER_EFFORT_UNSUPPORTED`.
- Never expose raw RPC data or exception messages.
- Add deterministic negative tests for malformed initialize, account/read, and model/list results.

Preserve M8E-H02, one-click AI, independent local microphone/Whisper, exact context bindings, no fallback/PAYG,
and clinical/Health/phone OFF. Zero live inference; no real vault access; do not install the candidate into the owner
pilot.

Run relevant/full tests, exact-C build/Chromium/privacy checks, then implementation C3 and evidence-only R3. Publish
by normal fast-forward, verify `origin/main == R3`, and stop AWAITING_REVIEW. No milestone change, release, deploy,
or force-push.
