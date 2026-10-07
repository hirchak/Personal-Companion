# M8E-H01/H02 independent-review corrections

Continue M8E only. Base: `16868ac34f50651b4c04465f6de0921c5f631ce3`.

## M8E-H01 — readiness failure categories

Preserve truthful sanitized categories. A successful `account/read` response with missing/non-ChatGPT auth is
`EXISTING_CHATGPT_AUTH_REQUIRED`. Process, transport, timeout, protocol, and RPC infrastructure failures are
`PRIVATE_PROVIDER_ROUTE_UNAVAILABLE`. A successful catalog without a verifiable required model/profile is
`PRIVATE_PROVIDER_PROFILE_UNVERIFIED`; a required effort absent from the catalog is
`PROVIDER_EFFORT_UNSUPPORTED`. Never return raw RPC/provider exception text. Readiness must not start a thread,
turn, prompt, or inference. Add deterministic account/read and model/list transport/RPC/timeout tests.

## M8E-H02 — explicit frontend code allowlist

Replace regex-only safe-code acceptance with an explicit allowlist of displayable sanitized codes. Unknown backend
codes, including uppercase/underscore codes, collapse to a generic safe code/message and are never displayed
verbatim. Add tests for unknown synthetic codes and secret-like values.

Preserve the accepted M8E behavior: one-click durable-consent AI toggle; one first-use acceptance; external OpenAI
settings nonblocking and `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; local microphone/Whisper independent of AI;
missing ASR preserves local recording; raw audio external `NEVER`; exact canonical payload/Deep/journal bindings;
no fallback/PAYG/new auth; clinical/Health/phone OFF.

Use synthetic fixtures only. Zero live provider inference. Do not inspect or modify the real owner vault and do not
install the hotfix into the owner pilot. Run relevant/full tests, exact-C build/Chromium/privacy checks; publish
forward C and evidence-only R by normal fast-forward; verify `origin/main == R`; update state/handoff/report; stop
AWAITING_REVIEW.
